# Evaluation Guide

## Overview

This guide explains how the Deep Research Agent output aligns with evaluation persona JSONs for comprehensive testing.

---

## ✅ Output Alignment

### Persona JSON Structure → Agent Output Mapping

| Persona JSON Field | Agent Output Field | Comparison Method |
|-------------------|-------------------|-------------------|
| `facts_by_depth.surface_level_facts[]` | All `EDDSection.facts[]` | Semantic similarity matching |
| `facts_by_depth.medium_depth_facts[]` | All `EDDSection.facts[]` | Semantic similarity matching |
| `facts_by_depth.deep_hidden_facts[]` | All `EDDSection.facts[]` | Semantic similarity matching |
| `expected_risk_findings` | `EDDReport.risk_assessment` | Category & severity matching |
| `connection_map` | `EDDSection.relationship_mapping` | Entity relationship matching |
| `source_tier_expectations` | `EDDReport.sources_summary` | Tier distribution comparison |
| `evaluation_metrics.recall_targets` | Calculated from found/expected | Percentage calculation |

---

## 📊 Comprehensive Metrics

The `EvaluationComparator` calculates:

### 1. **Recall Metrics** (How much we found)
- **Surface-level recall**: % of basic facts found (target: >95%)
- **Medium-depth recall**: % of deeper facts found (target: >70%)
- **Deep/hidden recall**: % of obscure facts found (target: >40%)
- **Overall recall**: Weighted average across all depths

### 2. **Precision Metrics** (How accurate we are)
- **Precision**: % of discovered facts that match expected facts
- **False positive rate**: % of discovered facts that are incorrect
- **Target**: >90% precision

### 3. **Source Quality** (Source reliability)
- **Average source tier**: Mean tier of all sources (target: <2.5)
- **Tier distribution**: Count of sources at each tier (1-5)
- **Comparison with expected distribution**

### 4. **Confidence Scoring** (How certain we are)
- **Overall confidence**: Mean confidence across all facts
- **Confidence by depth**: Separate confidence for surface/medium/deep
- **Target**: >0.7 average confidence

### 5. **Risk Assessment** (Red flag detection)
- **Risk detection rate**: % of expected red flags found
- **Category accuracy**: % of risk categories correctly identified
- **Red flags count**: Actual vs expected
- **Target**: >80% detection rate

### 6. **Connection Mapping** (Relationship discovery)
- **Connection recall**: % of expected connections found
- **Connections count**: Actual vs expected
- **Relationship types identified**

---

## 🔍 How Comparison Works

### Fact Matching Algorithm

```python
def match_facts(expected_fact, discovered_facts):
    for discovered in discovered_facts:
        # 1. Normalize both texts
        expected_normalized = normalize(expected_fact.statement)
        discovered_normalized = normalize(discovered.statement)
        
        # 2. Calculate Jaccard similarity (word overlap)
        jaccard = len(words_expected ∩ words_discovered) / len(words_expected ∪ words_discovered)
        
        # 3. Calculate sequence similarity
        sequence = SequenceMatcher(expected_normalized, discovered_normalized).ratio()
        
        # 4. Weighted combination
        similarity = 0.6 * jaccard + 0.4 * sequence
        
        # 5. Match if above threshold (default: 0.7)
        if similarity >= 0.7:
            return True
    return False
```

### Example Matches

**Expected Fact:**
```json
{
  "statement": "CEO and product architect of Tesla, Inc.",
  "category": "professional"
}
```

**Discovered Fact:**
```json
{
  "statement": "Elon Musk serves as CEO and product architect at Tesla, Inc.",
  "category": "professional",
  "confidence": 0.95
}
```

**Match Result:** ✅ Similarity: 0.85 (above 0.7 threshold)

---

## 🎯 Evaluation Metrics Structure

### Input: Persona JSON

```json
{
  "name": "Elon Musk",
  "facts_by_depth": {
    "surface_level_facts": [
      {"statement": "Born June 28, 1971", "expected_confidence": 0.99},
      ...
    ],
    "medium_depth_facts": [...],
    "deep_hidden_facts": [...]
  },
  "expected_risk_findings": {
    "regulatory": {
      "risk_level": "high",
      "red_flags": [...]
    }
  },
  "evaluation_metrics": {
    "recall_targets": {
      "surface_level": 0.95,
      "medium_depth": 0.70,
      "deep_hidden": 0.40
    }
  }
}
```

### Output: EvaluationMetrics

```python
@dataclass
class EvaluationMetrics:
    # Recall
    surface_recall: 0.92         # 92% of surface facts found
    medium_recall: 0.68          # 68% of medium facts found
    deep_recall: 0.35            # 35% of deep facts found
    overall_recall: 0.75         # 75% overall recall
    
    # Precision
    precision: 0.88              # 88% of found facts are correct
    false_positive_rate: 0.12    # 12% false positives
    
    # Source Quality
    avg_source_tier: 2.3         # Average tier 2.3 (good)
    tier_distribution: {1: 15, 2: 25, 3: 10}
    
    # Confidence
    avg_confidence: 0.82         # 82% average confidence
    
    # Risk
    risk_detection_rate: 0.85    # Found 85% of expected red flags
    red_flags_found: 12
    red_flags_expected: 14
    
    # Performance
    processing_time: 287.5       # 4.8 minutes
    search_count: 18
```

---

## 🧪 Running Evaluations

### Individual Persona Test

```bash
# Test specific persona with detailed output
pytest tests/evaluation/test_persona_recall.py::test_elon_musk_comprehensive -v -s

# Expected output:
# ============================================================
# 📊 EVALUATION REPORT: Elon Musk
# ============================================================
#
# 🎯 RECALL METRICS
#   Surface Level: 92.0% (23/25)
#   Medium Depth:  68.0% (17/25)
#   Deep/Hidden:   35.0% (7/20)
#   Overall:       67.1% (47/70)
# ...
```

### All Personas Test

```bash
# Run evaluation on all personas
pytest tests/evaluation/test_persona_recall.py::test_all_personas -v -s

# This will:
# 1. Load all persona JSONs from tests/evaluation/personas/
# 2. Run research on each
# 3. Compare outputs with expectations
# 4. Generate detailed reports
```

### Specific Metrics Test

```bash
# Test only risk detection
pytest tests/evaluation/test_persona_recall.py::test_risk_detection -v

# Test only recall
pytest tests/evaluation/test_persona_recall.py -k "recall" -v
```

---

## 📝 Adding New Personas

### 1. Create Persona JSON

```json
{
  "persona_id": "persona_004",
  "name": "Your Subject",
  "category": "Category",
  "facts_by_depth": {
    "surface_level_facts": [
      {
        "id": "surf_001",
        "statement": "Basic fact about subject",
        "category": "biographical",
        "expected_confidence": 0.95,
        "expected_source_tier": 1,
        "verification_difficulty": "easy"
      }
    ],
    "medium_depth_facts": [...],
    "deep_hidden_facts": [...]
  },
  "expected_risk_findings": {...},
  "connection_map": {...},
  "source_tier_expectations": {
    "expected_average_tier": 2.5
  },
  "evaluation_metrics": {
    "recall_targets": {
      "surface_level": 0.95,
      "medium_depth": 0.70,
      "deep_hidden": 0.40
    },
    "precision_targets": {
      "overall": 0.90
    },
    "risk_assessment_targets": {
      "red_flag_detection_rate": 0.80
    }
  }
}
```

### 2. Save to Personas Directory

```bash
# Save as: tests/evaluation/personas/your_subject.json
```

### 3. Run Evaluation

```bash
pytest tests/evaluation/test_persona_recall.py::test_all_personas -v
```

---

## 🎨 Customizing Comparison

### Adjust Similarity Threshold

```python
# Default: 0.7 (70% similarity required)
comparator = EvaluationComparator(similarity_threshold=0.7)

# More strict (fewer false positives, may miss valid matches)
comparator = EvaluationComparator(similarity_threshold=0.85)

# More lenient (more matches, may include false positives)
comparator = EvaluationComparator(similarity_threshold=0.6)
```

### Custom Metrics

```python
from tests.evaluation.evaluation_comparator import EvaluationComparator

comparator = EvaluationComparator()
metrics = comparator.compare(persona, agent_result)

# Access specific metrics
print(f"Surface recall: {metrics.surface_recall:.2%}")
print(f"Avg source tier: {metrics.avg_source_tier:.2f}")
print(f"Risk detection: {metrics.risk_detection_rate:.2%}")
```

---

## ✅ Success Criteria

### Minimum Thresholds (from problem statement)

| Metric | Target | Pass Condition |
|--------|--------|---------------|
| Surface-level recall | >95% | `metrics.surface_recall >= 0.95` |
| Medium-depth recall | >70% | `metrics.medium_recall >= 0.70` |
| Deep/hidden recall | >40% | `metrics.deep_recall >= 0.40` |
| Fact precision | >90% | `metrics.precision >= 0.90` |
| Red flag detection | >80% | `metrics.risk_detection_rate >= 0.80` |
| Source tier quality | <2.5 | `metrics.avg_source_tier <= 2.5` |
| Processing time | <10 min | `metrics.processing_time <= 600` |

### Running with Assertions

```python
# Tests will fail if thresholds not met
pytest tests/evaluation/test_persona_recall.py -v

# Run with relaxed thresholds for development
# (multiply targets by 0.7 in test code)
```

---

## 📈 Interpreting Results

### Good Results

```
📊 EVALUATION REPORT: Test Subject
========================================
🎯 RECALL METRICS
  Surface Level: 96.0% (24/25)  ✅
  Medium Depth:  72.0% (18/25)  ✅
  Deep/Hidden:   42.0% (8/20)   ✅
  
✅ PRECISION METRICS
  Precision:      91.5%         ✅
  
📚 SOURCE QUALITY
  Average Tier:   2.2           ✅
```

### Areas for Improvement

```
📊 EVALUATION REPORT: Test Subject
========================================
🎯 RECALL METRICS
  Surface Level: 88.0% (22/25)  ⚠️  Below target
  Deep/Hidden:   32.0% (6/20)   ⚠️  Below target
  
📚 SOURCE QUALITY
  Average Tier:   2.8           ⚠️  Above target
```

**Actions:**
- Increase search depth for deep facts
- Improve query generation
- Adjust source tier classification

---

## 🔧 Troubleshooting

### Low Recall
**Issue:** `metrics.surface_recall < 0.90`

**Solutions:**
1. Increase `MAX_SEARCH_DEPTH` in `.env`
2. Add more specific queries in query generator
3. Improve entity extraction prompt

### Low Precision
**Issue:** `metrics.precision < 0.85`

**Solutions:**
1. Increase confidence threshold filtering
2. Improve source validation
3. Add fact verification step

### Poor Source Quality
**Issue:** `metrics.avg_source_tier > 2.5`

**Solutions:**
1. Review source tier classification rules
2. Add more tier-1 domains to mapping
3. Filter out low-tier sources

---

## 📚 API Reference

### EvaluationComparator

```python
class EvaluationComparator:
    def __init__(self, similarity_threshold: float = 0.7):
        """Initialize comparator with similarity threshold."""
        
    def compare(
        self,
        persona: dict,
        agent_result: dict
    ) -> EvaluationMetrics:
        """Compare agent output with persona expectations."""
```

### Helper Functions

```python
def print_evaluation_report(
    metrics: EvaluationMetrics,
    persona_name: str
):
    """Print formatted evaluation report."""

def load_persona(persona_name: str) -> dict:
    """Load persona JSON from file."""
```

---

## 🎓 Best Practices

1. **Use realistic personas** with verifiable facts
2. **Include facts at all depth levels** for comprehensive testing
3. **Set achievable targets** based on information availability
4. **Run multiple times** to account for search variance
5. **Review false positives** manually to improve matching
6. **Update personas** as new information emerges
7. **Document edge cases** in persona notes

---

**Last Updated:** November 25, 2025
**Version:** 1.0

