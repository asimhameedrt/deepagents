"""Comprehensive evaluation comparator for persona testing."""

import re
from typing import Dict, List, Tuple, Set
from dataclasses import dataclass
from difflib import SequenceMatcher


@dataclass
class EvaluationMetrics:
    """Detailed evaluation metrics."""
    
    # Recall metrics
    surface_recall: float
    medium_recall: float
    deep_recall: float
    overall_recall: float
    
    # Precision metrics
    precision: float
    false_positive_rate: float
    
    # Source quality metrics
    total_sources: int
    
    # Confidence metrics
    avg_confidence: float
    confidence_by_depth: Dict[str, float]
    
    # Risk assessment
    risk_detection_rate: float
    risk_category_accuracy: float
    red_flags_found: int
    red_flags_expected: int
    
    # Connection mapping
    connections_found: int
    connections_expected: int
    connection_recall: float
    
    # Detailed counts
    facts_found: Dict[str, int]  # by depth
    facts_expected: Dict[str, int]  # by depth
    
    # Performance
    processing_time: float
    search_count: int


class EvaluationComparator:
    """Compares agent output with evaluation persona expectations."""
    
    def __init__(self, similarity_threshold: float = 0.7):
        """Initialize comparator.
        
        Args:
            similarity_threshold: Minimum similarity score for fact matching (0.0-1.0)
        """
        self.similarity_threshold = similarity_threshold
    
    def compare(
        self,
        persona: dict,
        agent_result: dict
    ) -> EvaluationMetrics:
        """
        Comprehensive comparison of agent output vs persona expectations.
        
        Args:
            persona: Evaluation persona JSON
            agent_result: Agent research result (with 'report' key)
            
        Returns:
            EvaluationMetrics with detailed comparison results
        """
        if not agent_result.get("success"):
            return self._create_failed_metrics()
        
        report = agent_result["report"]
        
        # Extract all discovered facts
        discovered_facts = self._extract_all_facts(report)
        
        # 1. Fact Recall Analysis
        recall_metrics = self._compare_facts(
            persona["facts_by_depth"],
            discovered_facts
        )
        
        # 2. Source Quality Analysis
        source_metrics = self._count_sources(report)
        
        # 3. Risk Assessment Analysis
        risk_metrics = self._compare_risk_assessment(
            persona["expected_risk_findings"],
            report["risk_assessment"]
        )
        
        # 4. Connection Analysis
        connection_metrics = self._compare_connections(
            persona.get("connection_map", {}),
            report
        )
        
        # 5. Precision Analysis
        precision = self._calculate_precision(
            persona["facts_by_depth"],
            discovered_facts
        )
        
        # Combine all metrics
        return EvaluationMetrics(
            # Recall
            surface_recall=recall_metrics["surface"],
            medium_recall=recall_metrics["medium"],
            deep_recall=recall_metrics["deep"],
            overall_recall=recall_metrics["overall"],
            
            # Precision
            precision=precision,
            false_positive_rate=1.0 - precision,
            
            # Source quality
            total_sources=source_metrics["total"],
            
            # Confidence
            avg_confidence=report["overall_confidence"],
            confidence_by_depth=self._calculate_confidence_by_depth(
                persona["facts_by_depth"],
                discovered_facts
            ),
            
            # Risk
            risk_detection_rate=risk_metrics["detection_rate"],
            risk_category_accuracy=risk_metrics["category_accuracy"],
            red_flags_found=risk_metrics["flags_found"],
            red_flags_expected=risk_metrics["flags_expected"],
            
            # Connections
            connections_found=connection_metrics["found"],
            connections_expected=connection_metrics["expected"],
            connection_recall=connection_metrics["recall"],
            
            # Counts
            facts_found=recall_metrics["found_counts"],
            facts_expected=recall_metrics["expected_counts"],
            
            # Performance
            processing_time=report.get("processing_time_seconds", 0),
            search_count=report.get("search_queries_count", 0)
        )
    
    def _extract_all_facts(self, report: dict) -> List[dict]:
        """Extract all facts from all report sections."""
        all_facts = []
        
        sections = [
            "identification", "professional_profile", "corporate_affiliations",
            "political_exposure", "financial_profile", "regulatory_legal",
            "adverse_media", "relationship_mapping", "geographic_risk"
        ]
        
        for section_name in sections:
            section = report.get(section_name, {})
            if section and "facts" in section:
                facts = section["facts"]
                # Add section context to each fact
                for fact in facts:
                    if isinstance(fact, dict):
                        fact["section"] = section_name
                        all_facts.append(fact)
        
        return all_facts
    
    def _compare_facts(
        self,
        expected_facts_by_depth: dict,
        discovered_facts: List[dict]
    ) -> dict:
        """Compare expected vs discovered facts by depth."""
        
        surface_expected = expected_facts_by_depth["surface_level_facts"]
        medium_expected = expected_facts_by_depth["medium_depth_facts"]
        deep_expected = expected_facts_by_depth["deep_hidden_facts"]
        
        # Match facts using semantic similarity
        surface_found = self._match_facts(surface_expected, discovered_facts)
        medium_found = self._match_facts(medium_expected, discovered_facts)
        deep_found = self._match_facts(deep_expected, discovered_facts)
        
        total_expected = len(surface_expected) + len(medium_expected) + len(deep_expected)
        total_found = surface_found + medium_found + deep_found
        
        return {
            "surface": surface_found / len(surface_expected) if surface_expected else 0,
            "medium": medium_found / len(medium_expected) if medium_expected else 0,
            "deep": deep_found / len(deep_expected) if deep_expected else 0,
            "overall": total_found / total_expected if total_expected else 0,
            "found_counts": {
                "surface": surface_found,
                "medium": medium_found,
                "deep": deep_found,
                "total": total_found
            },
            "expected_counts": {
                "surface": len(surface_expected),
                "medium": len(medium_expected),
                "deep": len(deep_expected),
                "total": total_expected
            }
        }
    
    def _match_facts(
        self,
        expected_facts: List[dict],
        discovered_facts: List[dict]
    ) -> int:
        """Match expected facts against discovered facts using similarity."""
        matched = 0
        
        for expected in expected_facts:
            expected_statement = expected["statement"].lower()
            
            for discovered in discovered_facts:
                discovered_statement = discovered.get("statement", "").lower()
                
                # Calculate similarity
                similarity = self._calculate_similarity(
                    expected_statement,
                    discovered_statement
                )
                
                if similarity >= self.similarity_threshold:
                    matched += 1
                    break  # Found a match, move to next expected fact
        
        return matched
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts."""
        # Use SequenceMatcher for basic similarity
        # In production, you might use sentence transformers or embeddings
        
        # Normalize texts
        text1 = self._normalize_text(text1)
        text2 = self._normalize_text(text2)
        
        # Check for key phrase overlap
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        # Remove common words
        common_words = {'the', 'a', 'an', 'in', 'on', 'at', 'of', 'for', 'to', 'is', 'was', 'are', 'were'}
        words1 = words1 - common_words
        words2 = words2 - common_words
        
        if not words1 or not words2:
            return 0.0
        
        # Jaccard similarity
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        jaccard = intersection / union if union > 0 else 0
        
        # Sequence similarity
        sequence = SequenceMatcher(None, text1, text2).ratio()
        
        # Weighted combination
        return 0.6 * jaccard + 0.4 * sequence
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison."""
        # Lowercase
        text = text.lower()
        # Remove punctuation
        text = re.sub(r'[^\w\s]', ' ', text)
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text
    
    def _count_sources(self, report: dict) -> dict:
        """Count total sources used."""
        total = report.get("total_sources_consulted", 0)
        
        return {
            "total": total
        }
    
    def _compare_risk_assessment(
        self,
        expected_risks: dict,
        actual_risk_assessment: dict
    ) -> dict:
        """Compare risk assessment results."""
        
        # Count expected red flags across all categories
        expected_flags = 0
        for category_data in expected_risks.values():
            expected_flags += len(category_data.get("red_flags", []))
        
        # Count actual red flags
        actual_flags = len(actual_risk_assessment.get("red_flags", []))
        
        # Get actual risk categories
        actual_categories = set(
            score["category"] for score in actual_risk_assessment.get("category_scores", [])
        )
        
        # Check expected high-risk categories
        expected_high_risk = set(
            category for category, data in expected_risks.items()
            if data.get("risk_level") in ["high", "critical", "medium"]
        )
        
        # Calculate category accuracy
        if expected_high_risk:
            correctly_identified = len(actual_categories & expected_high_risk)
            category_accuracy = correctly_identified / len(expected_high_risk)
        else:
            category_accuracy = 1.0
        
        # Detection rate
        detection_rate = min(actual_flags / expected_flags, 1.0) if expected_flags > 0 else 1.0
        
        return {
            "detection_rate": detection_rate,
            "category_accuracy": category_accuracy,
            "flags_found": actual_flags,
            "flags_expected": expected_flags
        }
    
    def _compare_connections(
        self,
        expected_connections: dict,
        report: dict
    ) -> dict:
        """Compare connection mapping results."""
        
        # Count expected connections
        expected_count = 0
        for conn_type in ["family_connections", "business_connections", "political_connections", "organizational_connections"]:
            expected_count += len(expected_connections.get(conn_type, []))
        
        # Extract actual connections (would need to parse relationship_mapping section)
        # For now, estimate from entities found
        entities_found = len(report.get("subject", {}).get("facts", []))
        
        # This is a simplified estimation
        # In production, you'd parse the relationship_mapping section content
        found_count = min(entities_found // 2, expected_count)
        
        recall = found_count / expected_count if expected_count > 0 else 1.0
        
        return {
            "found": found_count,
            "expected": expected_count,
            "recall": recall
        }
    
    def _calculate_precision(
        self,
        expected_facts_by_depth: dict,
        discovered_facts: List[dict]
    ) -> float:
        """Calculate precision (1 - false positive rate)."""
        
        # Get all expected statements
        all_expected = []
        for depth_key in ["surface_level_facts", "medium_depth_facts", "deep_hidden_facts"]:
            all_expected.extend([
                fact["statement"].lower()
                for fact in expected_facts_by_depth[depth_key]
            ])
        
        if not discovered_facts:
            return 1.0  # No facts = no false positives
        
        # Count how many discovered facts match expected ones
        true_positives = 0
        for discovered in discovered_facts:
            statement = discovered.get("statement", "").lower()
            
            for expected in all_expected:
                if self._calculate_similarity(statement, expected) >= self.similarity_threshold:
                    true_positives += 1
                    break
        
        # Precision = TP / (TP + FP) = TP / Total Discovered
        precision = true_positives / len(discovered_facts) if discovered_facts else 1.0
        
        return precision
    
    def _calculate_confidence_by_depth(
        self,
        expected_facts_by_depth: dict,
        discovered_facts: List[dict]
    ) -> Dict[str, float]:
        """Calculate average confidence for facts at each depth."""
        
        confidence_by_depth = {
            "surface": 0.0,
            "medium": 0.0,
            "deep": 0.0
        }
        
        # This is simplified - in production, you'd match discovered facts
        # to their expected depth level
        if discovered_facts:
            avg_confidence = sum(
                fact.get("confidence", 0.5)
                for fact in discovered_facts
            ) / len(discovered_facts)
            
            # Distribute evenly for now
            for key in confidence_by_depth:
                confidence_by_depth[key] = avg_confidence
        
        return confidence_by_depth
    
    def _create_failed_metrics(self) -> EvaluationMetrics:
        """Create metrics for failed research."""
        return EvaluationMetrics(
            surface_recall=0.0,
            medium_recall=0.0,
            deep_recall=0.0,
            overall_recall=0.0,
            precision=0.0,
            false_positive_rate=1.0,
            total_sources=0,
            avg_confidence=0.0,
            confidence_by_depth={"surface": 0.0, "medium": 0.0, "deep": 0.0},
            risk_detection_rate=0.0,
            risk_category_accuracy=0.0,
            red_flags_found=0,
            red_flags_expected=0,
            connections_found=0,
            connections_expected=0,
            connection_recall=0.0,
            facts_found={"surface": 0, "medium": 0, "deep": 0, "total": 0},
            facts_expected={"surface": 0, "medium": 0, "deep": 0, "total": 0},
            processing_time=0.0,
            search_count=0
        )


def print_evaluation_report(metrics: EvaluationMetrics, persona_name: str):
    """Print a detailed evaluation report."""
    
    print("\n" + "=" * 80)
    print(f"📊 EVALUATION REPORT: {persona_name}")
    print("=" * 80)
    
    print("\n🎯 RECALL METRICS")
    print(f"  Surface Level: {metrics.surface_recall:.1%} ({metrics.facts_found['surface']}/{metrics.facts_expected['surface']})")
    print(f"  Medium Depth:  {metrics.medium_recall:.1%} ({metrics.facts_found['medium']}/{metrics.facts_expected['medium']})")
    print(f"  Deep/Hidden:   {metrics.deep_recall:.1%} ({metrics.facts_found['deep']}/{metrics.facts_expected['deep']})")
    print(f"  Overall:       {metrics.overall_recall:.1%} ({metrics.facts_found['total']}/{metrics.facts_expected['total']})")
    
    print("\n✅ PRECISION METRICS")
    print(f"  Precision:         {metrics.precision:.1%}")
    print(f"  False Positive:    {metrics.false_positive_rate:.1%}")
    
    print("\n📚 SOURCE QUALITY")
    print(f"  Total Sources:     {metrics.total_sources}")
    
    print("\n🔒 CONFIDENCE")
    print(f"  Overall:    {metrics.avg_confidence:.1%}")
    print(f"  By Depth:")
    print(f"    Surface: {metrics.confidence_by_depth.get('surface', 0):.1%}")
    print(f"    Medium:  {metrics.confidence_by_depth.get('medium', 0):.1%}")
    print(f"    Deep:    {metrics.confidence_by_depth.get('deep', 0):.1%}")
    
    print("\n🚩 RISK ASSESSMENT")
    print(f"  Detection Rate:      {metrics.risk_detection_rate:.1%}")
    print(f"  Category Accuracy:   {metrics.risk_category_accuracy:.1%}")
    print(f"  Red Flags Found:     {metrics.red_flags_found}")
    print(f"  Red Flags Expected:  {metrics.red_flags_expected}")
    
    print("\n🔗 CONNECTIONS")
    print(f"  Connection Recall:   {metrics.connection_recall:.1%}")
    print(f"  Connections Found:   {metrics.connections_found}")
    print(f"  Connections Expected: {metrics.connections_expected}")
    
    print("\n⏱️  PERFORMANCE")
    print(f"  Processing Time:  {metrics.processing_time:.1f}s")
    print(f"  Search Count:     {metrics.search_count}")
    
    print("\n" + "=" * 80 + "\n")

