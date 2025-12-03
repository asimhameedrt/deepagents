# Deep Research AI Agent

An autonomous AI agent capable of conducting comprehensive Enhanced Due Diligence (EDD) investigations on individuals and entities. The system leverages multi-model AI architecture to gather intelligence, map relationships, identify risks, and generate compliance-ready reports.

## Features

- **Multi-Model AI Architecture**: Uses OpenAI GPT-4.1 for search and Claude Sonnet 4 for analysis
- **Consecutive Search Strategy**: Each search builds upon previous findings
- **Dynamic Query Refinement**: Adapts search strategies based on discovered information
- **Risk Pattern Recognition**: Identifies red flags across 10 risk categories
- **Connection Mapping**: Traces relationships between entities and organizations
- **Source Validation**: Implements tier-based source classification and confidence scoring
- **Compliance-Ready Reports**: Generates comprehensive EDD reports with full audit trails

## Quick Start

### Prerequisites

- Python 3.11+
- OpenAI API key
- Anthropic API key

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd 00-deepresearch-agents/workspace
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

### Basic Usage

```bash
# Run research on a subject
python -m src.main "Elon Musk"

# With additional context
python -m src.main "Elizabeth Holmes" --context "Former CEO of Theranos" --max-depth 1

# Set custom search depth
python -m src.main "Bill Hwang" --max-depth 7
```

### Python API Usage

```python
from src.main import DeepResearchAgent
import asyncio

async def run_research():
    agent = DeepResearchAgent()
    
    result = await agent.research(
        subject="Isabel dos Santos",
        context="Angolan businesswoman",
        max_depth=5
    )
    
    print(f"Report saved to: {result['report_path']}")

asyncio.run(run_research())
```

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                           USER INTERFACE                             │
│                    CLI / API Endpoint / Python SDK                   │
├─────────────────────────────────────────────────────────────────────┤
│                        ORCHESTRATION LAYER                           │
│                            LangGraph                                 │
│       START → Search → Extract → Analyze → Synthesize → END         │
│         ↑                                       │                    │
│         └────────── Refine Loop ←──────────────┘                    │
├────────────────────┬────────────────────┬──────────────────────────┤
│  OPENAI SERVICES   │  CLAUDE SERVICES   │    DATA SERVICES         │
│  • Web Search      │  • Risk Analysis   │  • Pydantic Models       │
│  • Query Gen       │  • Pattern Recog   │  • Source Tier DB        │
│  • Entity Extract  │  • Red Flag Detect │  • Connection Graph      │
│  • Structured Out  │  • EDD Synthesis   │  • Search Cache          │
└────────────────────┴────────────────────┴──────────────────────────┘
```

### Key Components

- **LangGraph Workflow**: Orchestrates the consecutive search and analysis process
- **OpenAI Service**: Handles web search, entity extraction, and structured output
- **Claude Service**: Performs risk analysis and report synthesis
- **Connection Mapper**: Builds relationship graphs using NetworkX
- **Source Validator**: Classifies sources into 5 tiers and calculates confidence scores
- **EDD Report Generator**: Synthesizes comprehensive compliance-ready reports

## Workflow

The agent follows a systematic research process:

1. **Initialize**: Set up research session with parameters
2. **Generate Queries**: Create initial search queries
3. **Execute Search**: Perform web searches in parallel
4. **Extract Entities**: Identify persons, organizations, and facts
5. **Classify Sources**: Tier sources and calculate confidence
6. **Decision Point**: Continue searching, analyze, or finish
7. **Risk Analysis**: Identify red flags and assess risks
8. **Connection Mapping**: Map relationships between entities
9. **Refine Queries**: Generate deeper queries based on findings
10. **Synthesize Report**: Generate comprehensive EDD report

## Evaluation

The system includes a comprehensive evaluation framework with test personas:

- **Elon Musk**: High-profile tech entrepreneur (connection mapping)
- **Elizabeth Holmes**: Convicted fraudster (red flag detection)
- **Isabel dos Santos**: African billionaire (PEP, international complexity)

### Running Evaluations

```bash
# Run evaluation tests
pytest tests/evaluation/test_persona_recall.py -v

# Evaluate specific persona
python tests/evaluation/run_evaluation.py --persona elon_musk
```

### Success Criteria

| Metric | Target |
|--------|--------|
| Surface-level fact recall | > 95% |
| Medium-depth fact recall | > 70% |
| Deep/hidden fact recall | > 40% |
| Fact precision (verified) | > 90% |
| Red flag detection rate | > 80% |
| Average source tier quality | < 2.5 |
| Report generation time | < 10 minutes |

## Configuration

Edit `.env` to configure:

```env
# API Keys
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here

# Agent Configuration
MAX_SEARCH_DEPTH=5
MAX_QUERIES_PER_DEPTH=10
MIN_CONFIDENCE_THRESHOLD=0.6
MAX_CONCURRENT_SEARCHES=5

# Models
OPENAI_SEARCH_MODEL=gpt-4o
CLAUDE_MODEL=claude-sonnet-4-20250514
```

## Output

The agent generates:

1. **JSON Report**: Complete EDD report with all findings (`reports/sess_*_report.json`)
2. **Audit Logs**: Full audit trail for compliance (`logs/sess_*.jsonl`)
3. **Console Output**: Real-time progress and summary

### Report Sections

- Executive Summary
- Identification & Background
- Professional Profile
- Corporate Affiliations
- Political Exposure
- Financial Profile
- Regulatory & Legal History
- Adverse Media
- Relationship Mapping
- Geographic Risk Assessment
- Risk Assessment (with red flags)

## Risk Categories

The system evaluates 10 risk categories:

1. **Financial Crime**: Money laundering, fraud, embezzlement
2. **Fraud**: Fraudulent activities and schemes
3. **Corruption**: Bribery, kickbacks, corrupt practices
4. **Sanctions**: OFAC, UN, EU sanctions exposure
5. **PEP Exposure**: Politically Exposed Persons
6. **Regulatory**: Enforcement actions, violations
7. **Reputational**: Adverse media, controversies
8. **Litigation**: Lawsuits, legal proceedings
9. **Geographic**: High-risk jurisdictions
10. **Industry**: High-risk sectors

## Development

### Project Structure

```
src/
├── config/           # Configuration and settings
├── models/           # Pydantic data models
├── agents/           # LangGraph workflow and nodes
├── services/         # Core services (LLM, search, analysis)
├── reporting/        # Report generation
├── observability/    # Logging and monitoring
└── utils/            # Helper utilities

tests/
├── unit/             # Unit tests
├── integration/      # Integration tests
└── evaluation/       # Evaluation tests with personas
```

### Running Tests

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit -v

# Integration tests
pytest tests/integration -v

# With coverage
pytest --cov=src tests/
```

## Observability

The system includes comprehensive observability:

- **Audit Logging**: Structured logs for compliance (JSON Lines format)
- **Session Tracking**: Complete trail of all operations
- **Performance Metrics**: Search counts, processing time, costs
- **Error Tracking**: Detailed error logging and recovery

## Security & Compliance

- API keys stored in environment variables
- Sensitive data encrypted at rest
- Full audit trail for regulatory compliance
- Source attribution for all facts
- Confidence scoring for risk assessment
- Human review flags for critical findings

## Limitations

- Relies on publicly available information
- Search quality depends on OpenAI's web search capability
- May not access paywalled or restricted sources
- False positives/negatives possible in risk detection
- Processing time increases with search depth

## Contributing

See `SOLUTION_DESIGN.md` for detailed architectural information.

## License

[Your License Here]

## Support

For issues or questions, please open an issue on GitHub.

