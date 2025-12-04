# Solution Design Document
## Deep Research AI Agent

**Status:** ✅ Fully Implemented  
**Last Updated:** December 4, 2025

### 1. System Overview

A production-ready autonomous research agent designed for Enhanced Due Diligence (EDD) investigations that conducts comprehensive research on individuals and entities by orchestrating multiple AI models through a graph-based workflow.

**Core Capabilities**:
- **Reflection-Based Strategy**: Each iteration analyzes findings and guides next steps
- **Entity Tracking**: Discovers and deduplicates entities with LLM-based reasoning
- **Connection Mapping**: Builds relationship graphs and identifies patterns
- **Intelligent Routing**: Three termination criteria (max depth, reflection, stagnation)
- **Comprehensive Reporting**: 18-section due diligence reports with risk assessment

---

### 2. Architecture Pattern

**Workflow Orchestration**: LangGraph state machine with typed state management

**Multi-Agent Pattern**: Specialized agents for different cognitive tasks:
- **Claude Sonnet 4**: Reflection analysis (simple schemas for speed), query generation
- **OpenAI GPT-4o**: Web search, entity extraction/merging (structured output), connection mapping, report synthesis

**State Management**: Centralized `AgentState` TypedDict maintains all research progress, metrics, and discoveries across workflow nodes.

---

### 3. Core Components

#### 3.1 Workflow Graph (`src/agents/graph.py`)
- **Pattern**: Directed graph with conditional routing
- **Nodes**: 6 specialized processing nodes (all fully implemented)
- **Edges**: Linear and conditional transitions based on research progress
- **Flow**: Initialize → Generate → Search → Analyze → Route → (Continue OR Finalize → Connect → Synthesize)

#### 3.2 LLM Services Layer

**OpenAI Service** (`src/services/llm/openai_service.py`)
- Uses OpenAI Agents SDK with WebSearchTool
- Structured output via Pydantic schemas
- Handles: web search execution, entity merging, connection mapping, report synthesis
- Returns: `WebSearchOutput`, `ConnectionMappingOutput`, `DueDiligenceReport`
- Fast and reliable for complex structured outputs

**Claude Service** (`src/services/llm/claude_service.py`)
- Structured extraction using Claude's Messages API with response_format
- Optimized for structured outputs with Pydantic models
- Handles: reflection analysis, query generation
- Returns: `ReflectionOutput`, `SearchQueriesList`
- Excellent for strategic thinking and analysis

#### 3.2.1 Prompt Modules

**Analysis Prompts** (`src/prompts/analysis.py`)
- System prompt for reflection and analysis
- Prompt builder for structured analysis summaries
- Includes sections for: findings, entities, relationships, risk assessment, gaps

**Synthesis Prompts** (`src/prompts/synthesis.py`)
- Instructions for report generation
- Prompt builder aggregating all research findings
- Formats data for comprehensive due diligence report

**Query Generation Prompts** (`src/prompts/query_generation.py`)
- Initial query system prompt (broad coverage)
- Refined query system prompt (strategy-driven)
- Prompt builders for both initial and refined queries

#### 3.3 State Models (`src/models/state.py`)

**AgentState**: Core state container
- Session tracking: `session_id`, `subject`, `subject_context`
- Progress: `current_depth`, `max_depth`, `queries_executed`
- Control flow: `should_continue`, `termination_reason`
- Memory: `search_memory` (list of search iteration summaries), `reflection_memory` (reflection outputs)
- Entity tracking: `discovered_entities` (merged entities), `entity_graph` (nodes + edges)
- Risk assessment: `risk_indicators` (red_flags, neutral, positive)
- Audit: `search_iterations` (detailed audit trail)
- Metrics: search count, error count, iteration count

**SearchIterationData**: Audit trail per iteration
- Goal, queries executed, model used
- Entities discovered, sources found
- Error tracking

#### 3.4 Search Strategy (`src/services/search/`)

**QueryGenerator**: Claude-based strategy
- Initial queries: Broad biographical, professional, financial, legal coverage
- Refinement: Uses textual `query_strategy` from reflection
- Parses natural language priorities to generate targeted queries
- Deduplication: avoids queries in `queries_executed`

**SearchExecutor** (`src/services/search/web_search.py`)
- Parallel search execution via asyncio
- Rate limiting and concurrency control
- Source collection and search memory generation

---

### 4. Workflow Execution

#### Node Pipeline

1. **Initialize** (`initialize.py`) - ✅ Fully Implemented
   - Session setup with unique session_id
   - State initialization with defaults
   - Timestamp and metric initialization

2. **Generate Queries** (`generate_queries.py`) - ✅ Fully Implemented - **Claude**
   - Depth 0: Broad queries (biographical, professional, financial, legal)
   - Depth 1+: Uses `query_strategy` from latest reflection for refinement
   - Prioritizes red flags and critical gaps
   - Deduplicates against `queries_executed`
   - Returns list of targeted queries

3. **Execute Search** (`web_search.py`) - ✅ Fully Implemented - **OpenAI**
   - Parallel searches via OpenAI Agents SDK with WebSearchTool
   - Structured extraction of search results
   - Source tracking (URLs + titles)
   - Updates `search_memory` with full results

4. **Analyze and Reflect** (`analyze.py`) - ✅ Fully Implemented - **Claude**
   - Structured analysis using `ReflectionOutput` Pydantic model
   - Outputs: `analysis_summary` (multi-section structured text)
   - Decision: `should_continue` (bool) + `reasoning`
   - Strategy: `query_strategy` for next iteration
   - Increments depth after analysis

5. **Entity Merging** (utility in analyze node) - ✅ Fully Implemented - **OpenAI**
   - Extracts entities from `analysis_summary` text
   - Merges with existing entities via LLM reasoning
   - Handles variations and aliases
   - Updates `discovered_entities`

6. **Map Connections** (`connect.py`) - ✅ Fully Implemented - **OpenAI**
   - Builds/updates entity graph (nodes + edges)
   - Pattern detection (recurring connections)
   - Flags suspicious patterns
   - Assesses entity importance with reasoning
   - Returns `ConnectionMappingOutput`

7. **Synthesize Report** (`synthesize.py`) - ✅ Fully Implemented - **OpenAI**
   - Comprehensive due diligence report using `DueDiligenceReport` model
   - 18 sections: executive summary, risk assessment, detailed findings, recommendations
   - Adds metadata (models used, statistics, timing)
   - Saves to `reports/{session_id}_report.json`

#### Conditional Routing (`src/agents/edges/routing.py`)

**Primary Decision Point** - ✅ Fully Implemented:

`should_continue_research()`:
- **Decision Criteria** (checked in order):
  1. Max depth reached? → **finalize** (map connections → synthesize)
  2. Reflection recommends stop? → **finalize** (map connections → synthesize)
  3. Stagnation detected (no new entities in N iterations)? → **finalize**
  4. Otherwise → **continue_search** (generate more queries)

**Key Implementation Details**:
- Depth is incremented in `analyze_and_reflect` node BEFORE routing
- All finalization routes through `map_connections` before synthesis
- Termination reason is logged in state
- Example: max_depth=3 runs iterations at depths 0, 1, 2 (total 3)

---

### 5. Multi-Model Strategy (Optimized)

**Division of Labor**:

| Task | Model | Schema Type | Rationale |
|------|-------|-------------|-----------|
| Query Generation | Claude Sonnet 4 | Simple (list) | Strategic reasoning, natural language |
| Web Search | OpenAI GPT-4o | Structured | Native web search tool |
| Reflection Analysis | Claude Sonnet 4 | **Simple (text-heavy)** | **Fast processing with minimal structure** |
| Entity Merging | OpenAI GPT-4o | Structured | Reliable extraction + deduplication |
| Graph Merging | OpenAI GPT-4o | Structured | Fast graph operations |
| Connection Mapping | OpenAI GPT-4o | Structured | Pattern detection, graph building |
| Report Synthesis | OpenAI GPT-4o | Structured | Comprehensive long-form generation |

**Optimization Strategy**:
- **Claude**: Simple schemas (mostly text) → Fast, reliable
- **OpenAI**: Complex structured outputs → No failures, good performance
- **Key Insight**: Claude excels with simple schemas, OpenAI handles complex structures better

**Structured Output**:
- OpenAI: Uses Agents SDK with Pydantic output types (complex schemas)
- Claude: Beta structured outputs API with simplified schemas (text-heavy)

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

#### ✅ Fully Implemented (Production-Ready)

**Core Workflow**:
- [x] LangGraph workflow with 6 nodes (all implemented)
- [x] Complete state management with AgentState
- [x] Session initialization and tracking
- [x] Intelligent routing with 3 termination criteria

**Query Generation**:
- [x] Initial query generation (broad coverage)
- [x] Refined query generation (strategy-driven)
- [x] Query deduplication
- [x] Red flag prioritization

**Search & Analysis**:
- [x] OpenAI web search with Agents SDK
- [x] Parallel async search execution
- [x] Claude reflection with ReflectionOutput model
- [x] Entity extraction and LLM-based merging
- [x] Multi-section analysis summaries
- [x] Gap analysis tracking

**Entity & Connection Management**:
- [x] Entity discovery and deduplication
- [x] Entity graph construction (nodes + edges)
- [x] Pattern detection
- [x] Suspicious connection flagging
- [x] Entity importance assessment

**Report Generation**:
- [x] Comprehensive 18-section due diligence report
- [x] Risk assessment with severity levels
- [x] Evidence strength evaluation
- [x] Recommendations and next steps
- [x] Metadata with statistics and timing

**Observability & Configuration**:
- [x] Dual logging system (audit + detailed)
- [x] JSONL audit trail per session
- [x] Pydantic-based configuration with validation
- [x] Environment variable management

**Prompt Architecture**:
- [x] Modular prompt modules (analysis, synthesis, query generation)
- [x] System prompts + prompt builders
- [x] Structured instructions for each task

#### ⚡ Performance & Design Optimizations
- Multi-model approach (Claude for strategy, OpenAI for structure)
- Pydantic models for type safety and validation
- Async parallel search execution
- Depth increment after analysis (before routing)
- All finalization routes through connection mapping
- Stagnation detection prevents wasted iterations

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
Subject Input + Context
    ↓
┌─────────────────────────────────────────────────┐
│ Initialize Session                              │
│ - Generate session_id                           │
│ - Initialize state with defaults                │
│ - Set start_time, depth=0                       │
└─────────────────┬───────────────────────────────┘
                  ↓
┌──────────────────────────────────────────────────────────────┐
│  ITERATION LOOP                                              │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │ Generate Queries (Claude)                          │    │
│  │ • Depth 0: Initial broad coverage                  │    │
│  │ • Depth 1+: Refined based on query_strategy        │    │
│  │ • Output: List[str] queries                        │    │
│  └──────────────────────┬─────────────────────────────┘    │
│                         ↓                                    │
│  ┌────────────────────────────────────────────────────┐    │
│  │ Execute Searches (OpenAI)                          │    │
│  │ • Parallel web searches (async)                    │    │
│  │ • WebSearchOutput per query                        │    │
│  │ • Updates search_memory                            │    │
│  └──────────────────────┬─────────────────────────────┘    │
│                         ↓                                    │
│  ┌────────────────────────────────────────────────────┐    │
│  │ Analyze & Reflect (Claude)                         │    │
│  │ • ReflectionOutput with analysis_summary           │    │
│  │ • Entity extraction + merging (OpenAI)             │    │
│  │ • Decision: should_continue?                       │    │
│  │ • Query strategy for next iteration                │    │
│  │ • Increments depth++                               │    │
│  └──────────────────────┬─────────────────────────────┘    │
│                         ↓                                    │
│              ┌──────────────────┐                           │
│              │ Routing Decision │                           │
│              └────────┬─────────┘                           │
│                       │                                      │
│         ┌─────────────┼─────────────┐                       │
│         │             │             │                        │
│    Max depth?    Reflection?   Stagnation?                  │
│         │             │             │                        │
│         No            No            No                       │
│         │             │             │                        │
│         └─────────────┴─────────────┘                       │
│                       │                                      │
│                  CONTINUE_SEARCH                             │
│                       │                                      │
│                       └──────────────────────┐               │
│                                              │               │
└──────────────────────────────────────────────┼───────────────┘
                                               │
                                          Loop Back
                                               │
                    ┌──────────────────────────┘
                    │
                    │ (Any condition true)
                    ↓
              FINALIZE PATH
                    ↓
       ┌────────────────────────┐
       │ Map Connections (OpenAI)│
       │ • Build entity graph    │
       │ • Identify patterns     │
       │ • Flag suspicious       │
       └────────┬───────────────┘
                ↓
       ┌────────────────────────┐
       │ Synthesize Report (OpenAI)│
       │ • 18-section report     │
       │ • Add metadata          │
       │ • Save JSON file        │
       └────────┬───────────────┘
                ↓
        Final Report JSON
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

**Known Limitations**:

1. **Web Search Dependency**
   - Relies on OpenAI's WebSearchTool
   - Limited to publicly accessible information
   - No access to paywalled content or databases

2. **LLM Costs**
   - Multiple LLM calls per iteration (Claude + OpenAI)
   - Cost scales with search depth and queries per iteration
   - Mitigation: Configurable limits via settings

3. **Context Window Limits**
   - Long reflection histories may approach context limits
   - Entity graphs can grow large with many iterations
   - Mitigation: Summary compression for older iterations (future enhancement)

4. **Entity Extraction Accuracy**
   - LLM-based extraction depends on model quality
   - May miss subtle relationships or aliases
   - Mitigation: Iterative refinement across multiple searches

5. **Stagnation Detection**
   - Based on entity count (may not detect quality stagnation)
   - Could stop prematurely if entity discovery slows
   - Mitigation: Configurable threshold via settings

**Production Considerations**:
- Rate limiting: Respect API rate limits via `max_concurrent_searches`
- Error handling: All nodes have try-catch with error logging
- Audit compliance: JSONL logs provide immutable trail
- Cost monitoring: Track token usage via detailed logger
- Testing: Evaluation framework with test personas

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
│   ├── graph.py                    # ✅ LangGraph workflow definition
│   ├── nodes/                      # Processing nodes (all implemented)
│   │   ├── initialize.py           # ✅ Session setup
│   │   ├── generate_queries.py     # ✅ Claude query generation
│   │   ├── web_search.py           # ✅ OpenAI parallel web search
│   │   ├── analyze.py              # ✅ Claude reflection + entity merge
│   │   ├── connect.py              # ✅ OpenAI connection mapping
│   │   └── synthesize.py           # ✅ OpenAI report synthesis
│   └── edges/
│       └── routing.py              # ✅ Conditional routing logic
├── services/
│   ├── llm/
│   │   ├── openai_service.py       # ✅ Agents SDK + structured output
│   │   └── claude_service.py       # ✅ Messages API + structured extraction
│   └── search/
│       ├── query_generator.py      # ✅ Query generation service
│       └── web_search.py           # ✅ Search execution service
├── models/
│   ├── state.py                    # ✅ AgentState + SearchIterationData
│   └── search_result.py            # ✅ Pydantic schemas (6 models)
├── prompts/                        # ✅ Modular prompt architecture
│   ├── analysis.py                 # ✅ Reflection prompts
│   ├── synthesis.py                # ✅ Report synthesis prompts
│   ├── query_generation.py         # ✅ Query generation prompts
│   └── web_search.py               # ✅ Web search prompts
├── utils/
│   ├── research_utils.py           # ✅ Entity merge, stagnation check
│   └── helpers.py                  # ✅ Utility functions
├── observability/
│   ├── audit_logger.py             # ✅ JSONL audit trail
│   └── detailed_logger.py          # ✅ Detailed operational logs
├── config/
│   └── settings.py                 # ✅ Pydantic Settings with validation
└── main.py                         # ✅ CLI entry point

tests/
├── evaluation/
│   ├── EVALUATION_GUIDE.md         # ✅ Evaluation framework
│   ├── evaluation_comparator.py   # ✅ Result comparison tools
│   ├── test_persona_recall.py     # ✅ Persona testing
│   └── personas/                   # ✅ Test subjects (3 personas)
│       ├── sam_bankman_fried.json
│       ├── elon_musk.json
│       └── isabel_dos_santos.json
├── test_anthropic.py
├── test_openai_agents.py
└── conftest.py

docs/
├── IMPLEMENTATION_COMPLETE.md      # ✅ Implementation summary
├── IMPLEMENTATION_SUMMARY.md       # ✅ Technical details
├── SOLUTION_DESIGN.md              # ✅ This file - architecture
├── OPTIMIZATION_CHANGES.md         # ✅ Performance optimizations
├── QUICK_START.md                  # ✅ Quick start guide
└── problem_statement.md            # ✅ Original requirements
```

**Total Files**: 22 implementation files + documentation + tests

---

### 15. Testing & Validation

**Evaluation Framework**:
- Test personas for validation (Sam Bankman-Fried, Elon Musk, Isabel dos Santos)
- Evaluation comparator for result analysis
- Persona recall testing

**Manual Testing**:
```bash
# Quick test (2-3 iterations)
python -m src.main "Test Subject" --context "Context" --max-depth 2

# Full investigation (5+ iterations)
python -m src.main "Subject Name" --context "Info" --max-depth 5
```

**Validation Points**:
- ✅ Pydantic models validate all LLM outputs
- ✅ Type hints throughout codebase
- ✅ Error handling in all nodes
- ✅ Audit trail for compliance
- ✅ Configuration validation on startup

---

### 16. Future Enhancements

**Potential Improvements**:
- [ ] PDF/HTML report generation (currently JSON only)
- [ ] Semantic search for better query deduplication
- [ ] Vector database for search result caching
- [ ] Multi-language support for international subjects
- [ ] Real-time streaming output to UI
- [ ] Web UI dashboard for interactive research
- [ ] Advanced graph visualization
- [ ] Report comparison across multiple subjects
- [ ] Automated fact verification with multiple sources
- [ ] Integration with specialized databases (legal, financial, etc.)

---

**Document Version**: 2.0  
**Date**: December 4, 2025  
**Status**: ✅ Reflects fully implemented production-ready system

