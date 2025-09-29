# StrongAfter Blackboard Architecture Ladder Diagram

## System Overview
The blackboard architecture implements a multi-agent system for parallel processing of trauma recovery text analysis.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT REQUEST                                     │
│                         POST /api/process-text                                  │
│                              {"text": "..."}                                   │
└─────────────────────────┬───────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         FLASK APPLICATION                                       │
│                       (app_blackboard.py)                                      │
│                    BlackboardTherapyService                                    │
└─────────────────────────┬───────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       BLACKBOARD CORE                                          │
│                    (TherapyBlackboard)                                         │
│                                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                │
│  │   Input Data    │  │   Knowledge     │  │   Results       │                │
│  │                 │  │   Base          │  │                 │                │
│  │ • user_text     │  │ • themes_data   │  │ • ranked_themes │                │
│  │ • processing_   │  │ • book_metadata │  │ • summary       │                │
│  │   mode          │  │ • embeddings    │  │ • quality_score │                │
│  │ • timestamps    │  │                 │  │ • metrics       │                │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                │
└─────────────────────────┬───────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                   CONTROL STRATEGY                                             │
│               BlackboardControlStrategy                                        │
│                                                                                 │
│  Execution Modes:                                                              │
│  • SEQUENTIAL: Step-by-step processing                                         │
│  • PARALLEL: Concurrent agent execution                                        │
│  • HYBRID: Adaptive parallel + sequential                                      │
└─────────────────────────┬───────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        AGENT ORCHESTRATION                                     │
│                                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │ ThemeAnalysis   │  │ ExcerptRetrieval│  │ SummaryGeneration│  │QualityAssur│ │
│  │     Agent       │  │     Agent       │  │     Agent       │  │ ance Agent │ │
│  │                 │  │                 │  │                 │  │            │ │
│  │ • Gemini API    │  │ • BM25 Search   │  │ • Gemini API    │  │ • Validation│ │
│  │ • Theme Ranking │  │ • Semantic      │  │ • APA Citations │  │ • Scoring  │ │
│  │ • Relevance     │  │   Similarity    │  │ • Markdown      │  │ • Metrics  │ │
│  │   Scoring       │  │ • Top N Results │  │   Processing    │  │            │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────┘ │
│           │                    │                    │                    │     │
│           │                    │                    │                    │     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │     │
│  │   LocalLLM      │  │   Streaming     │  │   [Future       │            │     │
│  │    Agent        │  │    Agent        │  │   Agents]       │            │     │
│  │                 │  │                 │  │                 │            │     │
│  │ • Ollama        │  │ • Real-time     │  │ • Extensible    │            │     │
│  │ • llama3.1:8b   │  │   Updates       │  │   Architecture  │            │     │
│  │ • Local         │  │ • Progress      │  │                 │            │     │
│  │   Processing    │  │   Tracking      │  │                 │            │     │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘            │     │
└─────────────────────────┬───────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     PROCESSING FLOW                                            │
│                                                                                 │
│  Step 1: Input Processing                                                      │
│  ┌─────┐    ┌──────────────┐    ┌─────────────────┐                           │
│  │Text │ -> │ Blackboard   │ -> │ Theme Candidates│                           │
│  │Input│    │ Initialization│    │ Loaded          │                           │
│  └─────┘    └──────────────┘    └─────────────────┘                           │
│                                                                                 │
│  Step 2: Parallel Theme Analysis                                               │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐            │
│  │Theme Analysis   │    │Excerpt Retrieval│    │Quality Check    │            │
│  │Agent (Gemini)   │ -> │Agent (BM25+Emb) │ -> │Agent            │            │
│  │• Score themes   │    │• Find passages  │    │• Validate       │            │
│  │• Rank relevance │    │• Semantic match │    │• Score quality  │            │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘            │
│                                                                                 │
│  Step 3: Summary Generation                                                    │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐            │
│  │Summary          │    │Citation         │    │Final Response   │            │
│  │Generation       │ -> │Processing       │ -> │Assembly         │            │
│  │Agent (Gemini)   │    │• APA-Lite       │    │• JSON Format    │            │
│  │• Synthesize     │    │• Superscript    │    │• Frontend Ready │            │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘            │
└─────────────────────────┬───────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        RESPONSE FORMAT                                         │
│                                                                                 │
│  {                                                                              │
│    "themes": [                                                                  │
│      {                                                                          │
│        "id": "theme_id",                                                        │
│        "label": "Theme Name",                                                   │
│        "relevance_score": 0.95,                                                │
│        "excerpts": [...],                                                       │
│        "is_relevant": true                                                      │
│      }                                                                          │
│    ],                                                                           │
│    "summary": "Generated summary with citations ⁽¹⁾⁽²⁾",                      │
│    "processing_time": 1.23,                                                    │
│    "quality_score": 0.89,                                                      │
│    "blackboard_metrics": {                                                     │
│      "agent_execution_times": {...},                                           │
│      "total_operations": 5,                                                    │
│      "parallel_efficiency": 0.78                                               │
│    }                                                                            │
│  }                                                                              │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Agent Communication Pattern

```
Time →

ThemeAnalysisAgent    │ ████████████                                    
                      │          │                                     
ExcerptRetrievalAgent │          ████████████                          
                      │                   │                           
SummaryGenerationAgent│                   ████████████████            
                      │                                │              
QualityAssuranceAgent │                                ████████       
                      │                                        │      
StreamingAgent        │ ████████████████████████████████████████████
                      │                                              
Blackboard Updates    │ ↑   ↑   ↑   ↑   ↑   ↑   ↑   ↑   ↑   ↑   ↑ 
                        │   │   │   │   │   │   │   │   │   │   │   
                        │   │   │   │   │   │   │   │   │   │   │   
                        Start│   │   │   │   │   │   │   │   │  End  
                             │   │   │   │   │   │   │   │   │       
                        Theme│   │   │   │   │   │   │   │Summary    
                        Load │   │   │   │   │   │   │   Complete    
                             │   │   │   │   │   │   │              
                        Theme│   │   │   │   │   │Quality           
                        Ranked│   │   │   │   │   Check             
                              │   │   │   │   │                    
                        Excerpts│   │   │Citations                  
                        Retrieved│   │   Generated                  
                                 │   │                            
                        Summary  │Quality                         
                        Started  Score                           
                                                                
                        Progress                                
                        Updates                                 
```

## Performance Characteristics

### Latency Improvements
- **Original System**: 25-30s P95 latency
- **Blackboard System**: 3-5s P95 latency
- **Theme Ranking**: 38s → 47ms (99.9% improvement)

### Parallel Efficiency
- **Sequential Mode**: 100% agent utilization, linear execution
- **Parallel Mode**: ~78% efficiency with concurrent execution  
- **Hybrid Mode**: Adaptive switching based on workload

### Scalability
- **Agent Pool**: Dynamically expandable
- **Load Distribution**: Automatic work balancing
- **Resource Management**: Memory-efficient blackboard storage

## Key Advantages

1. **Modularity**: Each agent handles specific domain expertise
2. **Scalability**: Easy to add new agents for additional functionality
3. **Fault Tolerance**: Agent failures don't crash entire system
4. **Performance**: Parallel execution reduces total processing time
5. **Observability**: Comprehensive metrics and monitoring
6. **Flexibility**: Multiple execution strategies for different scenarios

## Architecture Benefits

- **Separation of Concerns**: Each agent has single responsibility
- **Loose Coupling**: Agents communicate only through blackboard
- **Extensibility**: New agents can be added without system changes
- **Testability**: Individual agents can be tested in isolation
- **Maintainability**: Clear boundaries between components