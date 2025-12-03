# Quick Start Guide: Enhanced Deep Research Agent (Optimized ⚡)

## 🚀 Get Started in 3 Steps

### 1. Configure Environment

Copy and edit `.env` file:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

Required variables:
```bash
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
```

### 2. Run Research

```bash
# Basic usage
python -m src.main "Sam Bankman-Fried"

# With context
python -m src.main "Elizabeth Holmes" --context "Former CEO of Theranos"

# Custom depth
python -m src.main "Elon Musk" --max-depth 3
```

### 3. Review Results

**Report Location:** `reports/{session_id}_report.json`

**Audit Log:** `logs/{session_id}.jsonl`

---

## 📊 What You'll Get

### Comprehensive Report Includes:
- ✅ Executive summary & overall risk level
- ✅ Biographical overview
- ✅ Professional history
- ✅ Financial analysis
- ✅ Legal & regulatory issues
- ✅ Behavioral patterns
- ✅ **Red flags with severity levels**
- ✅ Entity relationship graph
- ✅ Source credibility assessment
- ✅ Research gaps & limitations
- ✅ Actionable recommendations

---

## ⚙️ Key Configuration Options

Edit `.env` to customize:

```bash
# Research depth
MAX_SEARCH_DEPTH=5                    # How many iterations?
MAX_QUERIES_PER_DEPTH=10              # Queries per iteration?

# Stagnation detection (switch to connection mapping)
STAGNATION_CHECK_ITERATIONS=2         # If no progress in N iterations

# Termination
# - Max depth reached
# - Reflection recommends stop
# - No new queries generated
```

**Simplified:** No confidence calculation (faster Claude processing)

---

## 🔍 Understanding the Workflow

### Iteration Cycle (Optimized ⚡):

```
1. GENERATE QUERIES (Claude - Fast)
   ↓ Textual strategy from reflection
   
2. EXECUTE SEARCHES (OpenAI)
   ↓ Parallel web searches with sources
   
3. ANALYZE & REFLECT (Claude - Simple Schema)
   ↓ Structured text analysis (fast processing)
   
4. MERGE ENTITIES (OpenAI - Structured)
   ↓ Extract from text + deduplicate
   
5. DECISION POINT
   ├─ Continue? → Back to step 1
   ├─ Stagnation? → Map connections
   └─ Done? → Synthesize report
```

### Stopping Conditions:
- ✋ Max depth reached
- ✋ Reflection recommends stop
- ✋ No new queries generated

**Removed:** Confidence threshold (simplified for speed)

---

## ⚡ Performance Optimizations

**Simplified Schemas:**
- Claude uses **text-based outputs** (fast processing)
- OpenAI handles **structured data** (entity/graph operations)
- No complex nested structures in Claude (no API failures)

**Entity Extraction:**
- Claude mentions entities in analysis text
- OpenAI extracts and merges them (fast, reliable)

**Query Strategy:**
- Natural language priorities (flexible)
- Parsed by Claude for refinement

---

## 🎯 Use Cases

### Due Diligence Investigation
```bash
python -m src.main "Company CEO Name" \
  --context "CEO of XYZ Corp, considering investment" \
  --max-depth 5
```

### Background Check
```bash
python -m src.main "Person Name" \
  --context "Potential executive hire" \
  --max-depth 3
```

### Risk Assessment
```bash
python -m src.main "Organization Name" \
  --context "Vendor due diligence" \
  --max-depth 4
```

---

## 🛠️ Troubleshooting

### Issue: "No module named agents"
**Solution:** Install dependencies
```bash
pip install -r requirements.txt
```

### Issue: "API key not found"
**Solution:** Check `.env` file has correct keys
```bash
cat .env | grep API_KEY
```

### Issue: Research stops too early
**Solution:** Increase max depth or adjust stagnation iterations
```bash
# In .env
MAX_SEARCH_DEPTH=7
STAGNATION_CHECK_ITERATIONS=3
```

### Issue: Too many queries per iteration
**Solution:** Reduce queries per depth
```bash
# In .env
MAX_QUERIES_PER_DEPTH=5
```

---

## 📖 Advanced Features

### 1. Stagnation Control
Control when to switch from search to analysis:

```bash
# More aggressive (stop searching sooner)
STAGNATION_CHECK_ITERATIONS=1

# More patient (keep searching longer)
STAGNATION_CHECK_ITERATIONS=3
```

### 2. Enable Model Cross-Validation
Use both Claude and OpenAI for critical decisions:

```bash
ENABLE_MODEL_CROSS_VALIDATION=true
```

---

## 📊 Sample Output

### Console Output
```
================================================================================
🔍 Deep Research AI Agent
================================================================================
Subject: Sam Bankman-Fried
Session ID: sess_20251203_120000
Max depth: 5
================================================================================

[Iteration 0] Generating initial queries...
[Iteration 0] Executing 7 searches...
[Iteration 0] Analyzing and reflecting...
  → Found 15 entities, 8 red flags
  → Confidence: 0.45

[Iteration 1] Generating refined queries (priority: red flags)...
[Iteration 1] Executing 10 searches...
[Iteration 1] Analyzing and reflecting...
  → Found 12 new entities, 5 new red flags
  → Confidence: 0.68

[Iteration 2] Generating refined queries...
[Iteration 2] Executing 8 searches...
[Iteration 2] Analyzing and reflecting...
  → Found 3 new entities, 2 new red flags
  → Confidence: 0.87

================================================================================
✅ Research Complete
================================================================================
Duration: 5m 23s
Total Queries: 25
Total Sources: 142
Total Entities: 28
Risk Level: CRITICAL
Red Flags: 15
Report saved: reports/sess_20251203_120000_report.json
================================================================================
```

### Report Structure (JSON)
```json
{
  "metadata": {
    "subject": "Sam Bankman-Fried",
    "research_depth": 3,
    "risk_level": "CRITICAL"
  },
  "executive_summary": "...",
  "key_findings": [...],
  "biographical_overview": "...",
  "professional_history": "...",
  "financial_analysis": "...",
  "legal_regulatory": "...",
  "red_flags": [
    {
      "finding": "$8B customer funds missing",
      "severity": "critical",
      "confidence": 0.95,
      "sources": ["Bloomberg", "WSJ", "SEC"]
    }
  ],
  "entity_graph": {
    "nodes": [...],
    "edges": [...]
  },
  "recommendations": [...]
}
```

---

## 🎓 Next Steps

1. **Read full implementation:** See `IMPLEMENTATION_SUMMARY.md`
2. **Review architecture:** See `SOLUTION_DESIGN.md`
3. **Customize config:** Edit `.env` for your use case
4. **Run test research:** Start with a well-known person
5. **Review output:** Check generated reports and logs

---

## 💡 Tips

- **Start with low depth** (2-3) for testing
- **Review reflection reasoning** in audit logs
- **Adjust confidence weights** based on your priorities
- **Monitor API costs** (LLM calls add up)
- **Use context parameter** for better initial queries

---

**Need Help?** Check `IMPLEMENTATION_SUMMARY.md` for detailed documentation.

