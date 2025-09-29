# StrongAfter A/B Testing Guide
## System Architecture Comparison & Performance Analysis

### Overview
This document outlines the A/B testing setup for comparing the **Legacy System (A)** with the **Blackboard Architecture System (B)** for the StrongAfter trauma recovery assistant.

---

## System Configurations

### System A: Legacy Architecture
- **Backend**: `app.py` on port 5001
- **Frontend**: Angular app on port 4200 (environment.original.ts)
- **Architecture**: Monolithic Flask application
- **AI Integration**: Direct Gemini API calls
- **Response Format**: Traditional JSON with APA-lite citations

**Key Features**:
- ✅ APA-lite citation system with ⁽¹⁾⁽²⁾ format
- ✅ Reference cards generation
- ✅ Book metadata integration
- ✅ Theme ranking and analysis
- ✅ Extended timeout handling (120s)

### System B: Blackboard Architecture
- **Backend**: `app_blackboard.py` on port 5002  
- **Frontend**: Angular app on port 4200 (environment.optimized.ts)
- **Architecture**: Multi-agent blackboard system
- **AI Integration**: Hybrid Gemini + Local LLM (Ollama)
- **Response Format**: Enhanced JSON with streaming capabilities

**Key Features**:
- ✅ Real-time streaming responses (`/api/process-text-stream`)
- ✅ Multi-agent processing (ThemeAnalysisAgent, ExcerptRetrievalAgent, SummaryGenerationAgent)
- ✅ Advanced blackboard coordination
- ✅ System health monitoring (`/api/system-status`)
- ✅ Performance metrics and quality scoring
- ✅ Fallback mechanisms for AI services

---

## Testing Endpoints

### Health Checks
```bash
# System A (Legacy)
curl http://localhost:5001/api/health

# System B (Blackboard)
curl http://localhost:5002/api/health
```

### Text Processing
```bash
# System A - Standard Processing
curl -X POST http://localhost:5001/api/process-text \
  -H "Content-Type: application/json" \
  -d '{"text": "I am struggling with trauma and need help"}'

# System B - Standard Processing
curl -X POST http://localhost:5002/api/process-text \
  -H "Content-Type: application/json" \
  -d '{"text": "I am struggling with trauma and need help"}'

# System B - Streaming Processing
curl -X POST http://localhost:5002/api/process-text-stream \
  -H "Content-Type: application/json" \
  -d '{"text": "I am struggling with trauma and need help"}'
```

---

## Performance Dashboard

### Dashboard Server
- **URL**: http://localhost:8080
- **Backend**: `dashboard_server.py` on port 8080
- **Features**: 
  - Real-time performance comparison
  - P50/P95 latency tracking
  - Success rate monitoring
  - Token rate analysis
  - Live charting

### Automated Testing
```bash
# Run performance comparison
cd backend
python dashboard_server.py

# Access dashboard
open http://localhost:8080
```

---

## Key Metrics to Monitor

### Response Time
- **System A**: Typically 35-45 seconds
- **System B**: Target <10 seconds with streaming updates
- **Measurement**: End-to-end response latency

### Quality Metrics
- **Citation Accuracy**: Proper ⁽¹⁾⁽²⁾ format generation
- **Reference Completeness**: All sources properly attributed
- **Theme Relevance**: Accuracy of theme selection and scoring
- **Resource Card Generation**: Appropriate book recommendations

### User Experience
- **Time to First Content**: How quickly users see initial response
- **Progressive Loading**: Streaming vs. all-at-once delivery
- **Error Handling**: Graceful degradation and fallback behavior
- **Visual Consistency**: Citation rendering and card display

### Technical Performance
- **Memory Usage**: Backend resource consumption
- **CPU Utilization**: Processing efficiency
- **API Response Codes**: Success/failure rates
- **Concurrent User Handling**: System stability under load

---

## Testing Scenarios

### Standard Test Cases
1. **Short Query**: "I feel stressed"
2. **Medium Query**: "I'm dealing with childhood trauma and having trouble with relationships"
3. **Complex Query**: "I experienced abuse as a child and now I'm struggling with depression, anxiety, and trust issues in my marriage"
4. **Edge Cases**: Empty input, very long text, special characters

### Citation System Tests
1. **Single Source**: Query that should generate 1-2 citations
2. **Multiple Sources**: Query requiring 5+ different citations
3. **Duplicate Sources**: Ensure proper deduplication of references
4. **No Sources**: Graceful handling when no citations available

### Performance Load Tests
1. **Single User**: Sequential requests to measure baseline performance
2. **Concurrent Users**: 5-10 simultaneous requests
3. **Stress Test**: Maximum concurrent load until failure
4. **Recovery Test**: System behavior after overload

---

## Environment Switching

### Quick Environment Changes
```bash
# Switch to Legacy System (A)
cp src/environments/environment.original.ts src/environments/environment.ts

# Switch to Blackboard System (B)  
cp src/environments/environment.optimized.ts src/environments/environment.ts

# Restart frontend to apply changes
npm start
```

### Automated Switching Script
```bash
# Create switching utility
echo '#!/bin/bash
if [ "$1" = "legacy" ]; then
    cp src/environments/environment.original.ts src/environments/environment.ts
    echo "Switched to Legacy System (port 5001)"
elif [ "$1" = "blackboard" ]; then
    cp src/environments/environment.optimized.ts src/environments/environment.ts
    echo "Switched to Blackboard System (port 5002)"
else
    echo "Usage: $0 [legacy|blackboard]"
fi' > switch-system.sh
chmod +x switch-system.sh
```

---

## Expected Results

### System A (Legacy) Strengths
- **Proven Stability**: Battle-tested monolithic architecture
- **Complete Citations**: Fully implemented APA-lite system
- **Predictable Performance**: Consistent response times
- **Simple Debugging**: Single-process architecture

### System B (Blackboard) Advantages
- **Faster Response**: Streaming provides immediate feedback
- **Better Scalability**: Multi-agent architecture handles load better
- **Enhanced Monitoring**: Detailed system health and metrics
- **Future-Proof**: Modular design enables easy feature additions

### Key Comparison Points
1. **Time to First Response**: B should be significantly faster
2. **Total Processing Time**: B should show overall improvement
3. **Citation Quality**: Both should be equivalent
4. **User Satisfaction**: B should provide better perceived performance
5. **System Reliability**: A may have advantage in stability

---

## Success Criteria

### Performance Targets
- **System B Response Time**: <15 seconds for 95% of requests
- **System B Streaming**: First content within 3 seconds
- **Error Rate**: <5% for both systems
- **Citation Accuracy**: >95% proper formatting

### User Experience Goals
- **Perceived Speed**: System B should feel 2x faster than A
- **Citation Usability**: Click-through rate >20% on reference links
- **Resource Discovery**: Card engagement >30%
- **Return Usage**: Users prefer System B in 70%+ of comparisons

---

## Data Collection

### Automated Metrics
- Response times (P50, P95, P99)
- Error rates and types
- Citation counts and accuracy
- Resource card generation rates

### Manual Evaluation
- Citation quality assessment
- Theme relevance scoring
- User experience testing
- Comparative usability studies

### Dashboard Integration
All metrics automatically collected and visualized at http://localhost:8080 with real-time updates and historical trending.

---

## Troubleshooting

### Common Issues
1. **Port Conflicts**: Ensure only one backend runs per port
2. **Citation Rendering**: Check frontend citation processing logic
3. **Environment Confusion**: Verify correct environment.ts is active
4. **Timeout Errors**: Confirm 120s timeout is configured

### Debug Commands
```bash
# Check running services
lsof -i :5001,5002,4200,8080

# View backend logs
tail -f backend/logs/app.log

# Test citations directly
curl -s http://localhost:5001/api/process-text -d '{"text":"test"}' | jq '.summary'
```

This A/B testing framework enables comprehensive comparison of both systems to determine the optimal architecture for StrongAfter's trauma recovery assistant.