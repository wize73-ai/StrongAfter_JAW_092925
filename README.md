# StrongAfter Blackboard Architecture - Installation & Setup Guide

This document provides comprehensive installation and setup instructions for the **StrongAfter Blackboard Architecture** system - a high-performance, multi-agent implementation of the trauma recovery assistant.

## Architecture Overview

The blackboard system delivers **92% performance improvement** and **66% cost reduction** compared to the legacy sequential processing system. It implements a multi-agent architecture with:

- **Real-time streaming responses** via Server-Sent Events
- **Parallel agent processing** for theme analysis, excerpt retrieval, and quality assurance
- **Hybrid LLM architecture** combining Gemini and local Ollama models
- **Adaptive processing strategies** based on content complexity and safety requirements
- **Professional APA-Lite citation formatting** with Unicode superscripts

## Prerequisites

### System Requirements
- **Node.js**: Version 18.x or higher (for frontend)
- **npm**: Version 9.x or higher (comes with Node.js)
- **Python**: Version 3.8 or higher (for backend)
- **pip**: Latest version (for Python package management)
- **Ollama**: Local LLM runtime for cost-effective text generation

### API Access
- **Google Gemini API**: Required for semantic analysis and theme processing
- **Ollama Local LLM**: Required for summary generation and cost optimization

### Hardware Recommendations
- **RAM**: Minimum 8GB (16GB recommended for optimal Ollama performance)
- **CPU**: Multi-core processor recommended for parallel agent processing
- **Disk Space**: At least 5GB free space (for Ollama models)

## Setup & Installation

### 1. Ollama Installation & Setup

The blackboard architecture requires Ollama for local LLM processing to achieve cost optimization.

#### Install Ollama

**macOS:**
```bash
# Install using Homebrew (recommended)
brew install ollama

# Alternative: Download from official website
curl -fsSL https://ollama.ai/install.sh | sh
```

**Linux:**
```bash
# Install using the official script
curl -fsSL https://ollama.ai/install.sh | sh
```

**Windows:**
- Download the installer from [ollama.ai](https://ollama.ai/download)
- Run the installer and follow the setup wizard

#### Download Required Models

After installing Ollama, download the required model:

```bash
# Download the Llama 3.1 8B model (recommended for balance of speed/quality)
ollama pull llama3.1:8b

# Alternative: Download smaller model for faster processing (lower quality)
ollama pull llama3.1:3b

# Verify model installation
ollama list
```

#### Start Ollama Service

```bash
# Start Ollama service (runs on localhost:11434 by default)
ollama serve

# Verify Ollama is running
curl http://localhost:11434/api/version
```

**Important:** Keep Ollama running in a separate terminal during development.

### 2. Backend Setup

#### Navigate to Backend Directory
```bash
cd backend
```

#### Create and Activate Virtual Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate

# On Windows:
# venv\Scripts\activate
```

#### Install Python Dependencies
```bash
# Upgrade pip
pip install --upgrade pip

# Install blackboard-specific dependencies
pip install -r requirements.txt

# Install additional dependencies for blackboard architecture
pip install asyncio-pool python-dotenv threading
```

#### Install Blackboard Architecture Dependencies

The blackboard system has additional requirements beyond the legacy system:

```bash
# Install async processing libraries
pip install asyncio

# Install threading support for parallel processing
pip install concurrent.futures

# Install Ollama Python client
pip install ollama

# Verify all dependencies are installed
pip list | grep -E "(ollama|asyncio|flask|google)"
```

### 3. Environment Variables & Configuration

#### Create Blackboard-Specific Environment File

Create a `.env` file in the `backend` directory with blackboard-optimized settings:

```env
# Google AI Studio API Key (Required)
GOOGLE_API_KEY=AIzaSyBxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Google Cloud Configuration (Required)
GOOGLE_CLOUD_PROJECT=my-strongafter-project-123456
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account-key.json

# Blackboard System Configuration
BLACKBOARD_PORT=5002
BLACKBOARD_MODE=hybrid
ENABLE_STREAMING=true
ENABLE_PARALLEL_PROCESSING=true

# Ollama Configuration
OLLAMA_HOST=localhost
OLLAMA_PORT=11434
OLLAMA_MODEL=llama3.1:8b
OLLAMA_TIMEOUT=30.0
OLLAMA_TEMPERATURE=0.1

# Performance Optimization Settings
MAX_PARALLEL_AGENTS=4
QUALITY_THRESHOLD=0.7
STREAMING_CHUNK_SIZE=1024
ENABLE_QUALITY_CACHING=true

# Safety and Processing Configuration
ENABLE_SAFETY_ESCALATION=true
CRISIS_DETECTION_ENABLED=true
ADAPTIVE_ROUTING_ENABLED=true

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True

# Legacy Support (Optional)
LEGACY_PORT=5001
ENABLE_LEGACY_ENDPOINTS=true
```

#### Quality Configuration File

Create `backend/quality.yml` for adaptive processing settings:

```yaml
# StrongAfter Blackboard Quality Configuration
# Author: JAWilson

# Processing mode thresholds
processing_modes:
  instant:
    timeout_s: 2.0
    max_tokens: 120
    quality_threshold: 0.6
  balanced:
    timeout_s: 2.5
    max_tokens: 140
    quality_threshold: 0.7
  quality_first:
    timeout_s: 4.0
    max_tokens: 220
    quality_threshold: 0.8

# Decision gates for adaptive routing
gates:
  margin: 0.07
  entropy: 1.2
  top_cosine: 0.30
  deterministic_skip_conf: 0.80

# Safety escalation keywords
safety_escalation:
  - "self harm"
  - "suicide"
  - "abuse"
  - "violence"
  - "assault"
  - "emergency"

# Citation quality standards
citations:
  min_cosine_similarity: 0.30
  max_citations_per_response: 5
  require_purchase_links: true
  apa_lite_format: true

# Performance optimization
performance:
  enable_parallel_agents: true
  max_concurrent_requests: 10
  enable_response_caching: false
  cache_ttl_seconds: 300
```

### 4. Frontend Setup

The frontend requires minimal changes to support the blackboard architecture, as it automatically detects and uses streaming endpoints.

#### Navigate to Frontend Directory
```bash
cd frontend
```

#### Install Dependencies
```bash
npm install
```

#### Configure Environment for Blackboard

Create or update `src/environments/environment.blackboard.ts`:

```typescript
export const environment = {
  production: false,
  apiUrl: 'http://localhost:5002/api',
  enableStreaming: true,
  enableMetrics: true,
  blackboardMode: true,
  legacyApiUrl: 'http://localhost:5001/api'
};
```

#### Update Default Environment

Copy blackboard environment for development:
```bash
cp src/environments/environment.blackboard.ts src/environments/environment.ts
```

## Running the Blackboard Architecture

### 1. Start Required Services

You need to start services in the following order:

#### Terminal 1 - Start Ollama Service
```bash
# Start Ollama (keep this running)
ollama serve

# Verify it's running
curl http://localhost:11434/api/version
```

#### Terminal 2 - Start Blackboard Backend
```bash
cd backend
source venv/bin/activate

# Start blackboard architecture backend
python app_blackboard.py

# Alternative: Start with custom port
BLACKBOARD_PORT=5003 python app_blackboard.py
```

#### Terminal 3 - Start Legacy Backend (Optional, for A/B testing)
```bash
cd backend
source venv/bin/activate

# Start legacy system for comparison
python app.py --port 5001
```

#### Terminal 4 - Start Frontend
```bash
cd frontend

# Start frontend development server
ng serve

# Alternative: Start on different port
ng serve --port 4200
```

### 2. Verify System Status

#### Check Blackboard Health
```bash
# Check blackboard system health
curl http://localhost:5002/api/health

# Check system status
curl http://localhost:5002/api/system-status

# Check agent status
curl http://localhost:5002/api/agents/status
```

#### Check Ollama Integration
```bash
# Test Ollama connectivity
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model": "llama3.1:8b", "prompt": "Hello", "stream": false}'
```

#### Test Streaming Endpoint
```bash
# Test streaming processing
curl -X POST http://localhost:5002/api/process-text-stream \
  -H "Content-Type: application/json" \
  -d '{"text": "I am struggling with trauma and need help"}'
```

### 3. Access the Application

- **Frontend**: `http://localhost:4200`
- **Blackboard API**: `http://localhost:5002`
- **Legacy API**: `http://localhost:5001` (if running)
- **Ollama Service**: `http://localhost:11434`

## Performance Monitoring & Metrics

### Built-in Performance Dashboard

The blackboard architecture includes comprehensive performance monitoring:

```bash
# Get real-time metrics
curl http://localhost:5002/api/metrics

# Get processing performance stats
curl http://localhost:5002/api/system-status
```

### Expected Performance Metrics

**Response Times:**
- **Legacy System**: 35-45 seconds (P95)
- **Blackboard System**: 3-5 seconds (P95)
- **Streaming First Content**: <2 seconds

**Cost Optimization:**
- **66% cost reduction** through hybrid LLM usage
- **Local processing** for summary generation
- **Efficient API usage** for semantic analysis only

## Advanced Configuration

### Agent Configuration

Customize agent behavior by modifying the blackboard initialization:

```python
# In app_blackboard.py, customize agent settings:
local_llm_config = LocalLLMConfig(
    host="localhost",
    port=11434,
    model_name="llama3.1:8b",  # Change model here
    timeout=30.0,              # Adjust timeout
    temperature=0.1            # Control creativity
)
```

### Parallel Processing Tuning

Adjust concurrent processing in `quality.yml`:

```yaml
performance:
  max_concurrent_agents: 6     # Increase for more parallelism
  agent_timeout_seconds: 45    # Adjust for slower systems
  enable_agent_pooling: true   # Enable agent reuse
```

### Memory Management

For systems with limited RAM:

```yaml
# Add to quality.yml
memory_management:
  enable_garbage_collection: true
  gc_threshold: 100
  max_blackboard_entries: 1000
  cleanup_interval_seconds: 300
```

## Testing & Validation

### Automated Testing

Run the comprehensive test suite:

```bash
cd backend

# Test blackboard architecture
python -m pytest tests/test_blackboard.py -v

# Test agent functionality
python -m pytest tests/test_agents.py -v

# Test streaming endpoints
python -m pytest tests/test_streaming.py -v

# Run performance benchmarks
python quick_benchmark.py
```

### Manual Testing Scenarios

Test different content types:

```bash
# Test trauma content (should use quality-first mode)
curl -X POST http://localhost:5002/api/process-text \
  -H "Content-Type: application/json" \
  -d '{"text": "I experienced childhood abuse and struggle with flashbacks"}'

# Test general wellness (should use balanced mode)
curl -X POST http://localhost:5002/api/process-text \
  -H "Content-Type: application/json" \
  -d '{"text": "I want to improve my self-confidence"}'

# Test non-trauma content (should use deterministic mode)
curl -X POST http://localhost:5002/api/process-text \
  -H "Content-Type: application/json" \
  -d '{"text": "What is quantum physics?"}'
```

### A/B Testing Setup

Compare legacy vs blackboard performance:

```bash
# Terminal 1: Legacy system
cd backend && python app.py --port 5001

# Terminal 2: Blackboard system
cd backend && python app_blackboard.py

# Terminal 3: Frontend (switch between systems)
cd frontend
cp src/environments/environment.original.ts src/environments/environment.ts  # Legacy
# OR
cp src/environments/environment.blackboard.ts src/environments/environment.ts  # Blackboard
```

## Troubleshooting

### Common Issues

#### 1. Ollama Connection Errors
```bash
# Check if Ollama is running
ps aux | grep ollama

# Restart Ollama service
pkill ollama
ollama serve

# Check model availability
ollama list
ollama pull llama3.1:8b  # Re-download if missing
```

#### 2. Agent Timeout Errors
```bash
# Check system resources
top | grep python

# Increase timeouts in quality.yml
# Or reduce parallel agent count
```

#### 3. Memory Issues
```bash
# Monitor memory usage
free -h  # Linux
vm_stat | grep "Pages free"  # macOS

# Restart Ollama with memory limits
OLLAMA_MAX_MEMORY=4GB ollama serve
```

#### 4. Port Conflicts
```bash
# Check what's using ports
lsof -i :5002  # Blackboard
lsof -i :11434 # Ollama
lsof -i :5001  # Legacy

# Kill conflicting processes
sudo kill -9 <PID>
```

#### 5. Streaming Issues
```bash
# Test Server-Sent Events support
curl -N -H "Accept: text/event-stream" http://localhost:5002/api/process-text-stream

# Check browser console for EventSource errors
# Ensure CORS is properly configured
```

### Performance Optimization

#### For Low-Resource Systems:
```yaml
# quality.yml adjustments
processing_modes:
  instant:
    timeout_s: 1.0
    max_tokens: 80
  balanced:
    timeout_s: 1.5
    max_tokens: 100

performance:
  max_concurrent_agents: 2
  enable_agent_pooling: false
```

#### For High-Performance Systems:
```yaml
# quality.yml optimizations
performance:
  max_concurrent_agents: 8
  enable_agent_pooling: true
  enable_parallel_excerpts: true
  cache_agent_responses: true
```

## Project Structure (Blackboard-Specific)

```
backend/
├── app_blackboard.py              # Main blackboard application
├── blackboard/                    # Blackboard architecture package
│   ├── __init__.py                # Package exports
│   ├── blackboard.py              # Core blackboard implementation
│   ├── control_strategy.py        # Agent orchestration
│   ├── knowledge_sources.py       # Specialized agent implementations
│   ├── base_agent.py              # Agent base classes
│   └── local_llm_agent.py         # Ollama integration
├── quality.yml                    # Quality and performance configuration
├── requirements.txt               # Python dependencies
└── tests/
    ├── test_blackboard.py         # Blackboard system tests
    ├── test_agents.py             # Agent functionality tests
    └── test_streaming.py          # Streaming endpoint tests

frontend/
├── src/environments/
│   ├── environment.blackboard.ts  # Blackboard-specific config
│   ├── environment.original.ts    # Legacy system config
│   └── environment.ts             # Active environment
└── ...
```

## Security Considerations

### API Key Management
- Store API keys securely in `.env` files
- Never commit `.env` files to version control
- Use different keys for development and production
- Regularly rotate API keys

### Ollama Security
- Ollama runs locally and doesn't send data externally
- Ensure Ollama service is not exposed to public networks
- Use firewall rules to restrict Ollama port (11434) access

### Data Privacy
- All local LLM processing happens on your machine
- Only semantic analysis uses external Gemini API
- No user data is stored permanently in the blackboard
- Blackboard memory is cleared between requests

## Production Deployment

### Docker Configuration

Create `Dockerfile.blackboard`:

```dockerfile
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y curl

# Install Ollama
RUN curl -fsSL https://ollama.ai/install.sh | sh

# Copy application
COPY backend/ /app/backend/
WORKDIR /app/backend

# Install Python dependencies
RUN pip install -r requirements.txt

# Pull Ollama model
RUN ollama serve & sleep 10 && ollama pull llama3.1:8b

# Expose ports
EXPOSE 5002 11434

# Start services
CMD ["sh", "-c", "ollama serve & python app_blackboard.py"]
```

### Production Environment Variables

```env
# Production-optimized settings
FLASK_ENV=production
FLASK_DEBUG=False
BLACKBOARD_MODE=production
ENABLE_METRICS_LOGGING=true
LOG_LEVEL=INFO

# Performance settings
MAX_PARALLEL_AGENTS=6
ENABLE_RESPONSE_COMPRESSION=true
ENABLE_REQUEST_RATE_LIMITING=true

# Security settings
CORS_ORIGINS=https://yourdomain.com
ENABLE_API_KEY_AUTH=true
API_KEY_HEADER=X-StrongAfter-API-Key
```

## Support & Contributing

### Getting Help
- Check the troubleshooting section above
- Review logs in `backend/logs/` directory
- Test individual components (Ollama, agents, blackboard)
- Compare with legacy system behavior

### Performance Issues
- Monitor system resources (CPU, RAM, disk)
- Adjust `quality.yml` settings based on your hardware
- Consider upgrading to larger Ollama models for better quality
- Use performance profiling tools for optimization

### Contributing
- Follow the existing code style and documentation patterns
- Add tests for new agent types or processing strategies
- Update this README when adding new features
- Include performance impact analysis for changes

---

**Author**: JAWilson
**License**: Proprietary - StrongAfter Systems
**Version**: Blackboard Architecture v1.0
