# Self-Hosted Model for Theme Ranking - Performance Optimization

## Current Bottleneck Analysis

**Current Theme Ranking Process:**
```python
# 15-20 second bottleneck
def rank_themes(text, themes):
    # Large prompt with all 20+ themes
    prompt = build_massive_prompt(text, all_themes)
    response = MODEL.generate_content(prompt)  # Gemini API call
    return parse_theme_rankings(response)
```

**Performance Issues:**
- **Network latency**: Round-trip to Google's servers
- **API queue time**: Waiting in Google's processing queue
- **Large context**: Processing 20+ themes with descriptions
- **Complex scoring**: Detailed analysis and explanation generation

## Self-Hosted Model Strategy

### Hybrid Architecture Approach

```
┌─────────────────┐    Fast     ┌─────────────────┐    Detailed    ┌─────────────────┐
│   User Input    │────────────▶│  Self-Hosted    │───────────────▶│   Gemini API    │
│                 │   <1s       │  Theme Ranking  │     3-5s       │  Summary Gen    │
└─────────────────┘             └─────────────────┘                └─────────────────┘
                                        │
                                   Local Model
                                 - Llama 3.1 8B
                                 - Mistral 7B
                                 - Phi-3 Medium
```

**Process Flow:**
1. **Self-hosted model**: Fast theme ranking and filtering (< 1s)
2. **Gemini API**: Detailed summary generation for top themes (3-5s)
3. **Total time**: 4-6s instead of 25+s

## Self-Hosted Model Options

### 1. **Llama 3.1 8B (Recommended)**

**Pros:**
- Excellent reasoning capabilities
- Good for classification tasks
- Optimized quantized versions available
- Strong open-source ecosystem

**Hardware Requirements:**
- **GPU**: RTX 4090 (24GB) or RTX 3090 (24GB)
- **RAM**: 16GB+ system RAM
- **Storage**: 8-16GB model files

**Implementation:**
```python
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

class LlamaThemeRanker:
    def __init__(self):
        self.model_name = "meta-llama/Meta-Llama-3.1-8B-Instruct"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float16,
            device_map="auto",
            load_in_4bit=True  # Quantization for speed
        )

    def rank_themes_fast(self, user_text, themes):
        # Simplified prompt for fast ranking
        prompt = self.build_ranking_prompt(user_text, themes)

        inputs = self.tokenizer(prompt, return_tensors="pt").to("cuda")

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=200,
                temperature=0.1,
                do_sample=False
            )

        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return self.parse_rankings(response)
```

### 2. **Mistral 7B**

**Pros:**
- Faster inference than Llama
- Good multilingual support
- Smaller memory footprint

**Implementation:**
```python
from transformers import AutoTokenizer, AutoModelForCausalLM

class MistralThemeRanker:
    def __init__(self):
        self.model_name = "mistralai/Mistral-7B-Instruct-v0.3"
        # Similar setup to Llama but faster
```

### 3. **Phi-3 Medium (14B)**

**Pros:**
- Microsoft's efficient architecture
- Good reasoning for size
- Optimized for local deployment

**Hardware Requirements:**
- **GPU**: RTX 4090 recommended
- **RAM**: 32GB+ for full precision

## Implementation Architecture

### Hybrid Service Design

```python
# services/theme_ranking_service.py
class HybridThemeService:
    def __init__(self):
        # Local model for fast ranking
        self.local_ranker = LlamaThemeRanker()

        # Gemini for detailed summaries
        self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')

    async def process_themes_hybrid(self, user_text, all_themes):
        # Stage 1: Fast local ranking (< 1s)
        start_time = time.time()

        theme_scores = await self.local_ranker.rank_themes_fast(
            user_text, all_themes
        )

        local_time = time.time() - start_time
        logger.info(f"Local ranking completed in {local_time:.2f}s")

        # Filter to top 3-5 themes
        top_themes = self.select_top_themes(theme_scores, limit=5)

        # Stage 2: Detailed analysis with Gemini (3-5s)
        detailed_summary = await self.gemini_model.generate_content(
            self.build_summary_prompt(user_text, top_themes)
        )

        total_time = time.time() - start_time
        logger.info(f"Total processing time: {total_time:.2f}s")

        return {
            'themes': top_themes,
            'summary': detailed_summary.text,
            'processing_time': total_time
        }
```

### Optimized Prompts for Local Model

```python
def build_ranking_prompt(self, user_text, themes):
    """Simplified prompt optimized for fast local processing"""

    # Reduce complexity for local model
    theme_list = "\n".join([
        f"{i+1}. {theme['label']}"
        for i, theme in enumerate(themes)
    ])

    prompt = f"""Rate how relevant each theme is to the user's text on a scale of 0-100.
    Return only the numbers, one per line.

User text: "{user_text}"

Themes:
{theme_list}

Relevance scores (0-100, one per line):"""

    return prompt

def parse_rankings(self, response):
    """Simple parsing for numeric scores"""
    lines = response.strip().split('\n')
    scores = []

    for line in lines:
        try:
            score = int(line.strip())
            scores.append(min(100, max(0, score)))  # Clamp 0-100
        except ValueError:
            scores.append(0)

    return scores
```

## Performance Comparison

| Approach | Theme Ranking Time | Summary Generation | Total Time | Cost |
|----------|-------------------|-------------------|------------|------|
| **Current (All Gemini)** | 15-20s | 8-12s | 25-30s | $0.10/request |
| **Hybrid (Local + Gemini)** | 0.5-1s | 3-5s | 4-6s | $0.03/request |
| **All Local** | 0.5-1s | 2-3s | 3-4s | $0.00/request |

## Deployment Options

### Option 1: Docker Container
```dockerfile
# Dockerfile.llama-service
FROM pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime

RUN pip install transformers accelerate bitsandbytes

COPY theme_ranking_service.py /app/
COPY requirements.txt /app/

WORKDIR /app
EXPOSE 5002

CMD ["python", "theme_ranking_service.py"]
```

### Option 2: Separate GPU Server
```python
# gpu_server/theme_service.py
from flask import Flask, request, jsonify

app = Flask(__name__)
ranker = LlamaThemeRanker()

@app.route('/rank-themes', methods=['POST'])
def rank_themes():
    data = request.json
    user_text = data['text']
    themes = data['themes']

    scores = ranker.rank_themes_fast(user_text, themes)

    return jsonify({
        'scores': scores,
        'processing_time': ranker.last_processing_time
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
```

### Option 3: Ollama Integration (Easiest)
```python
import requests

class OllamaThemeRanker:
    def __init__(self):
        self.ollama_url = "http://localhost:11434"

    def rank_themes_fast(self, user_text, themes):
        prompt = self.build_ranking_prompt(user_text, themes)

        response = requests.post(f"{self.ollama_url}/api/generate", json={
            "model": "llama3.1:8b",
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 200
            }
        })

        return self.parse_rankings(response.json()['response'])
```

## Implementation Steps

### Phase 1: Proof of Concept (1 week)
1. **Setup Ollama** with Llama 3.1 8B
2. **Create simple ranking service**
3. **Test performance** vs current Gemini approach
4. **Measure accuracy** of theme rankings

### Phase 2: Production Integration (2 weeks)
1. **Containerize** the local model service
2. **Update main Flask app** to use hybrid approach
3. **Add fallback logic** (use Gemini if local model fails)
4. **Implement monitoring** and logging

### Phase 3: Optimization (1 week)
1. **Fine-tune prompts** for local model
2. **Optimize GPU memory usage**
3. **Add caching layer**
4. **Performance monitoring**

## Expected Performance Gains

```python
# Before: Single Gemini approach
def process_text_current(text):
    start = time.time()
    themes = rank_themes_gemini(text, all_themes)     # 15-20s
    summary = generate_summary_gemini(themes)         # 8-12s
    return time.time() - start  # 25-30s total

# After: Hybrid approach
def process_text_hybrid(text):
    start = time.time()
    themes = rank_themes_local(text, all_themes)      # 0.5-1s
    summary = generate_summary_gemini(themes[:5])     # 3-5s
    return time.time() - start  # 4-6s total
```

**Performance Improvement: 80-85% reduction in response time**

## Hardware Requirements Summary

### Minimum Setup:
- **GPU**: RTX 3090 (24GB) or RTX 4080 (16GB)
- **RAM**: 32GB system RAM
- **Storage**: 50GB SSD for models and cache

### Recommended Setup:
- **GPU**: RTX 4090 (24GB)
- **RAM**: 64GB system RAM
- **Storage**: 100GB NVMe SSD

### Cloud Options:
- **AWS**: g5.xlarge instance ($1.20/hour)
- **Google Cloud**: n1-standard-4 with T4 GPU ($0.80/hour)
- **Local**: One-time hardware investment ($2000-3000)

This hybrid approach gives you the best of both worlds: **fast local ranking** with **high-quality Gemini summaries**, reducing total response time by 80%+ while maintaining output quality.