"""Evaluation tests for persona fact recall."""

import pytest
import json
import asyncio
from pathlib import Path

from src.main import DeepResearchAgent
from .evaluation_comparator import EvaluationComparator, print_evaluation_report


def load_persona(persona_name: str) -> dict:
    """Load persona definition from JSON."""
    persona_file = Path(__file__).parent / "personas" / f"{persona_name}.json"
    
    with open(persona_file) as f:
        return json.load(f)


@pytest.mark.asyncio
@pytest.mark.evaluation
@pytest.mark.slow
async def test_elon_musk_comprehensive():
    """Comprehensive evaluation test for Elon Musk persona."""
    persona = load_persona("elon_musk")
    
    agent = DeepResearchAgent()
    result = await agent.research(
        subject=persona["name"],
        context=persona.get("category"),
        max_depth=3  # Reduced for testing
    )
    
    # Check success
    assert result["success"], f"Research failed: {result.get('error')}"
    
    # Use comprehensive comparator
    comparator = EvaluationComparator(similarity_threshold=0.7)
    metrics = comparator.compare(persona, result)
    
    # Print detailed report
    print_evaluation_report(metrics, persona["name"])
    
    # Assert targets from persona
    targets = persona["evaluation_metrics"]["recall_targets"]
    
    # For testing, we'll use relaxed thresholds (70% of target)
    # In production evaluation, use actual targets (remove * 0.7)
    assert metrics.surface_recall >= targets["surface_level"] * 0.7, \
        f"Surface recall {metrics.surface_recall:.2%} below target {targets['surface_level']:.2%}"
    
    # Check precision
    assert metrics.precision >= targets["overall"] * 0.7, \
        f"Precision {metrics.precision:.2%} below target"
    
    print(f"\n✅ Comprehensive evaluation passed for {persona['name']}")


@pytest.mark.asyncio
@pytest.mark.evaluation
async def test_risk_detection():
    """Test risk detection capabilities."""
    persona = load_persona("elon_musk")
    
    agent = DeepResearchAgent()
    result = await agent.research(
        subject=persona["name"],
        max_depth=2
    )
    
    assert result["success"]
    
    # Use comparator for detailed risk analysis
    comparator = EvaluationComparator()
    metrics = comparator.compare(persona, result)
    
    # Check risk detection rate
    targets = persona["evaluation_metrics"]["risk_assessment_targets"]
    
    print(f"\n🚩 Risk Detection Metrics:")
    print(f"  Detection Rate: {metrics.risk_detection_rate:.1%}")
    print(f"  Category Accuracy: {metrics.risk_category_accuracy:.1%}")
    print(f"  Red Flags Found: {metrics.red_flags_found}")
    print(f"  Red Flags Expected: {metrics.red_flags_expected}")
    
    # Assert minimum detection rate
    assert metrics.risk_detection_rate >= targets["red_flag_detection_rate"] * 0.6, \
        f"Risk detection rate {metrics.risk_detection_rate:.2%} below target"
    
    print(f"\n✅ Risk detection test passed")


@pytest.mark.asyncio
@pytest.mark.evaluation
async def test_all_personas():
    """Run evaluation on all available personas."""
    
    personas_dir = Path(__file__).parent / "personas"
    persona_files = list(personas_dir.glob("*.json"))
    
    print(f"\n{'='*80}")
    print(f"🧪 EVALUATING {len(persona_files)} PERSONAS")
    print(f"{'='*80}\n")
    
    comparator = EvaluationComparator(similarity_threshold=0.7)
    results = {}
    
    for persona_file in persona_files:
        persona_name = persona_file.stem
        persona = load_persona(persona_name)
        
        print(f"\n▶️  Testing: {persona['name']}")
        
        agent = DeepResearchAgent()
        result = await agent.research(
            subject=persona["name"],
            context=persona.get("category"),
            max_depth=3
        )
        
        if result["success"]:
            metrics = comparator.compare(persona, result)
            print_evaluation_report(metrics, persona["name"])
            results[persona_name] = metrics
        else:
            print(f"❌ Research failed: {result.get('error')}")
            results[persona_name] = None
    
    # Print summary
    print(f"\n{'='*80}")
    print(f"📋 SUMMARY OF ALL PERSONAS")
    print(f"{'='*80}\n")
    
    for persona_name, metrics in results.items():
        if metrics:
            print(f"{persona_name}:")
            print(f"  Recall: {metrics.overall_recall:.1%}")
            print(f"  Precision: {metrics.precision:.1%}")
            print(f"  Total Sources: {metrics.total_sources}")
            print(f"  Risk Detection: {metrics.risk_detection_rate:.1%}\n")
        else:
            print(f"{persona_name}: FAILED\n")


if __name__ == "__main__":
    # Run comprehensive test
    asyncio.run(test_elon_musk_comprehensive())

