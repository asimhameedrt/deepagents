# Solution Design Document
## Deep Research AI Agent

### 1. System Overview

An autonomous research agent designed for Enhanced Due Diligence (EDD) investigations that conducts comprehensive research on individuals and entities by orchestrating multiple AI models through a graph-based workflow.

**Core Capability**: Consecutive search strategy where each research iteration builds upon previous discoveries to progressively uncover deeper intelligence.

---

### 2. Architecture Pattern

**Workflow Orchestration**: LangGraph state machine with typed state management

**Multi-Agent Pattern**: Specialized agents for different cognitive tasks:
- **OpenAI GPT-4o**: Information retrieval, web search, entity extraction
- **Claude Sonnet 4**: Risk analysis, pattern recognition, report synthesis

**State Management**: Centralized `AgentState` TypedDict maintains all research progress, metrics, and discoveries across workflow nodes.

---

### 3. Core Components

#### 3.1 Workflow Graph (`src/agents/graph.py`)
- **Pattern**: Directed graph with conditional routing
- **Nodes**: 7 specialized processing nodes
- **Edges**: Linear and conditional transitions based on research progress
- **Flow**: Initialize → Generate → Search → Analyze → Route → Connect/Continue → Synthesize

#### 3.2 LLM Services Layer

**OpenAI Service** (`src/services/llm/openai_service.py`)
- Uses OpenAI Agents SDK with WebSearchTool
- Structured output via Pydantic schemas
- Handles: web search execution, query generation
- Returns: `WebSearchOutput` with sources, memory summaries, comprehensive reports

**Claude Service** (`src/services/llm/claude_service.py`)
- Structured extraction using Claude's beta API
- Currently implements: generic structured extraction
- Designed for: risk analysis, connection mapping, report synthesis

#### 3.3 State Models (`src/models/state.py`)

**AgentState**: Core state container
- Session tracking: `session_id`, `subject`, `subject_context`
- Progress: `current_depth`, `max_depth`, `queries_executed`
- Control flow: `should_continue`, `termination_reason`
- Memory: `search_memory` (list of search iteration summaries)
- Audit: `search_iterations` (detailed audit trail)
- Metrics: search count, error count, iteration count

**SearchIterationData**: Audit trail per iteration
- Goal, queries executed, model used
- Entities discovered, sources found
- Error tracking

#### 3.4 Search Strategy (`src/services/search/`)

**QueryGenerator**: Currently simplified
- Initial queries: basic subject + context
- Refinement: designed for depth-based query evolution (not fully implemented)
- Deduplication: tracks generated queries

**SearchExecutor** (`src/services/search/web_search.py`)
- Parallel search execution via asyncio
- Rate limiting and concurrency control
- Source collection and search memory generation

---

### 4. Workflow Execution

#### Node Pipeline

1. **Initialize** (`initialize.py`): Session setup, state initialization
2. **Generate Queries** (`generate_queries.py`): 
   - Depth 0: Simple initial query
   - Depth N: Intended to use search memory for refinement
3. **Execute Search** (`web_search.py`):
   - Parallel searches via OpenAI Agents SDK
   - Collects sources and search summaries
   - Updates audit trail
4. **Analyze and Reflect** (`analyze.py`): Placeholder for analysis and reflection
5. **Map Connections** (`connect.py`): Placeholder for relationship mapping
6. **Synthesize Report** (`synthesize.py`): Final report generation

#### Conditional Routing (`src/agents/edges/routing.py`)

**Decision Points** (placeholder implementations):
- `should_continue_research`: continue_search / analyze / finish
- `has_new_queries`: search_more / synthesize
- `needs_deeper_research`: refine / synthesize

---

### 5. Multi-Model Strategy

**Division of Labor**:

| Task | Model | Rationale |
|------|-------|-----------|
| Web Search & Extraction | OpenAI GPT-4o | Native web search tool, fast structured output |
| Risk Analysis | Claude Sonnet 4 | Superior reasoning for complex pattern recognition |
| Report Synthesis | Claude Sonnet 4 | Comprehensive long-form generation |

**Structured Output**:
- OpenAI: Uses Agents SDK with Pydantic output types
- Claude: Beta structured outputs API (`beta.messages.parse`)

---

### 6. Observability Architecture

**Dual Logging System**:

1. **Audit Logger** (`observability/audit_logger.py`)
   - JSONL format for compliance
   - Session-based file per research run
   - Immutable event trail

2. **Detailed Logger** (`observability/detailed_logger.py`)
   - Rich operational logging
   - Node execution tracking via decorator pattern
   - LLM call instrumentation (tokens, duration, cost estimation)

**Integration**: LangFuse support for distributed tracing (optional)

---

### 7. Current Implementation State

#### ✅ Implemented
- LangGraph workflow structure with 7 nodes
- OpenAI web search integration via Agents SDK
- Search memory collection from searches
- Structured output schemas (WebSearchOutput, SearchQueriesList)
- Session management and state tracking
- Audit logging infrastructure
- Configuration management via Pydantic Settings
- Parallel search execution

#### 🚧 Partial/Placeholder
- Query refinement logic (simplified to basic queries)
- Risk analysis node (empty implementation)
- Connection mapping (empty implementation)
- Report synthesis (basic structure only)
- Conditional routing logic (functions defined but not implemented)

#### ❌ Not Implemented
- Claude-based analysis operations
- Connection graph construction
- Source classification and confidence scoring
- Red flag detection system
- Depth-based search strategies
- Final report generation with EDD sections

---

### 8. Key Technical Decisions

#### 8.1 Stateful Workflow
**Choice**: LangGraph with TypedDict state
**Trade-off**: Type safety and workflow visualization vs. additional framework dependency

#### 8.2 Search Memory
**Choice**: Store LLM-generated summaries per search iteration
**Benefit**: Enables intelligent routing decisions without re-processing all raw data
**Location**: `state["search_memory"]` as list of search summaries

#### 8.3 Search Execution
**Choice**: OpenAI Agents SDK with WebSearchTool
**Benefit**: Native web search, automatic rate limiting, structured outputs
**Limitation**: Dependent on OpenAI's search quality and availability

#### 8.4 Parallel Processing
**Choice**: AsyncIO for concurrent searches
**Configuration**: `max_concurrent_searches` setting (default: 5)

#### 8.5 Observability
**Choice**: File-based JSONL audit logs + optional LangFuse
**Rationale**: Compliance requirements + optional cloud observability

---

### 9. Data Flow

```
Subject Input
    ↓
Initialize State
    ↓
Generate Queries (OpenAI) ──→ ["query1", "query2", ...]
    ↓
Execute Searches (OpenAI WebSearch) ──→ Sources + Search Memory
    ↓
Analyze and Reflect (Claude) [PLACEHOLDER]
    ↓
Decision Point: Continue? Analyze? Finish?
    ↓
    ├──→ Continue: Loop back to Generate Queries
    ├──→ Analyze: Map Connections → Refine → Search More
    └──→ Finish: Synthesize Report
                      ↓
                  Final Report
```

---

### 10. Configuration Architecture

**Environment-based**: `.env` file + Pydantic Settings
**Key Parameters**:
- `max_search_depth`: Iteration limit
- `max_queries_per_depth`: Queries per iteration
- `max_concurrent_searches`: Parallel execution limit
- Model selections: `openai_search_model`, `claude_model`

**Models Used**:
- OpenAI: `gpt-4o` (search and extraction)
- Claude: `claude-sonnet-4-20250514` (analysis)

---

### 11. Extension Points

The architecture is designed for extension:
- **New Nodes**: Add to workflow graph
- **Enhanced Routing**: Implement logic in `routing.py` functions
- **Analysis Logic**: Implement in `analyze.py` and `connect.py`
- **Report Templates**: Customize in `synthesize.py`
- **Additional Models**: Add services in `services/llm/`

---

### 12. Limitations & Considerations

**Current State**:
- Workflow structure exists but key analysis nodes are placeholders
- Query generation is simplified (no true consecutive refinement yet)
- No risk assessment or connection mapping implemented
- Report generation is minimal

**Architectural Readiness**:
- State management supports full implementation
- Search memory collection enables intelligent routing
- Multi-model infrastructure is in place
- Observability supports production deployment

**Technical Debt**:
- Routing logic needs implementation based on search memory
- Claude service needs integration for analysis tasks
- Prompt engineering for analysis and synthesis required

---

### 13. System Dependencies

**Core**:
- `langgraph`: Workflow orchestration
- `agents`: OpenAI Agents SDK for web search
- `anthropic`: Claude API client
- `pydantic`: Data validation and settings

**Supporting**:
- `langfuse`: Optional observability
- `asyncio`: Concurrent execution

---

### 14. File Organization

```
src/
├── agents/
│   ├── graph.py              # Workflow definition
│   ├── nodes/                # Processing nodes
│   │   ├── initialize.py
│   │   ├── generate_queries.py
│   │   ├── web_search.py
│   │   ├── analyze.py        # [PLACEHOLDER]
│   │   ├── connect.py        # [PLACEHOLDER]
│   │   └── synthesize.py     # [PLACEHOLDER]
│   └── edges/
│       └── routing.py        # [PLACEHOLDER]
├── services/
│   ├── llm/
│   │   ├── openai_service.py # Web search + extraction
│   │   └── claude_service.py # Generic structured extraction
│   └── search/
│       ├── query_generator.py
│       └── web_search.py
├── models/
│   ├── state.py              # State definitions
│   └── search_result.py      # Pydantic schemas
├── prompts/
│   └── web_search.py         # Prompt builders
├── observability/
│   ├── audit_logger.py
│   └── detailed_logger.py
├── config/
│   └── settings.py
└── main.py                   # Entry point
```

---

**Document Version**: 1.0  
**Date**: December 2, 2025  
**Status**: Reflects current implementation state (incomplete/in-progress)

