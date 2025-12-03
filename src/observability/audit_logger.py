"""Custom audit logger for compliance requirements."""

import json
import logging
import structlog
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from ..config.settings import settings


class AuditLogger:
    """
    Custom audit logger for compliance requirements.
    
    Creates detailed, queryable logs of all operations.
    """
    
    def __init__(self, log_dir: Optional[Path] = None):
        """Initialize the audit logger.
        
        Args:
            log_dir: Directory for log files (defaults to settings)
        """
        self.log_dir = log_dir or settings.log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure structlog
        structlog.configure(
            processors=[
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.dict_tracebacks,
                structlog.processors.JSONRenderer()
            ],
            wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )
        
        self.logger = structlog.get_logger()
    
    def log_session_start(
        self,
        session_id: str,
        subject: str,
        config: dict
    ) -> None:
        """Log research session initiation."""
        self.logger.info(
            "session_started",
            session_id=session_id,
            subject=subject,
            config=config,
            timestamp=datetime.utcnow().isoformat()
        )
        
        # Also write to session-specific file
        self._write_session_log(session_id, {
            "event": "session_started",
            "subject": subject,
            "config": config,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def log_search(
        self,
        session_id: str,
        query: str,
        model: str,
        results_count: int,
        sources: List[dict],
        duration_ms: int,
        tokens: Optional[dict] = None,
        cost_usd: Optional[float] = None
    ) -> None:
        """Log a search operation with full details."""
        self.logger.info(
            "search_executed",
            session_id=session_id,
            query=query,
            model=model,
            results_count=results_count,
            sources_count=len(sources),
            sources_sample=[{
                "url": s.get("url", ""),
                "domain": s.get("domain", "")
            } for s in sources[:3]],  # Log sample of sources
            duration_ms=duration_ms,
            tokens=tokens or {},
            cost_usd=cost_usd or 0.0
        )
        
        self._write_session_log(session_id, {
            "event": "search_executed",
            "query": query,
            "results_count": results_count,
            "duration_ms": duration_ms
        })
    
    def log_extraction(
        self,
        session_id: str,
        entities_found: int,
        facts_extracted: int,
        model: str,
        duration_ms: int
    ) -> None:
        """Log entity extraction."""
        self.logger.info(
            "extraction_completed",
            session_id=session_id,
            entities_found=entities_found,
            facts_extracted=facts_extracted,
            model=model,
            duration_ms=duration_ms
        )
        
        self._write_session_log(session_id, {
            "event": "extraction_completed",
            "entities_found": entities_found,
            "facts_extracted": facts_extracted
        })
    
    def log_risk_finding(
        self,
        session_id: str,
        red_flag: dict,
        evidence: List[dict]
    ) -> None:
        """Log a risk finding with evidence."""
        self.logger.warning(
            "risk_finding",
            session_id=session_id,
            red_flag=red_flag,
            evidence_count=len(evidence)
        )
        
        self._write_session_log(session_id, {
            "event": "risk_finding",
            "red_flag": red_flag,
            "severity": red_flag.get("severity", "unknown")
        })
    
    def log_report_generated(
        self,
        session_id: str,
        subject: str,
        risk_level: str,
        confidence: float,
        total_searches: int,
        total_sources: int,
        duration_seconds: float
    ) -> None:
        """Log report generation."""
        self.logger.info(
            "report_generated",
            session_id=session_id,
            subject=subject,
            risk_level=risk_level,
            confidence=confidence,
            total_searches=total_searches,
            total_sources=total_sources,
            duration_seconds=duration_seconds
        )
        
        self._write_session_log(session_id, {
            "event": "report_generated",
            "risk_level": risk_level,
            "confidence": confidence,
            "duration_seconds": duration_seconds
        })
    
    def log(self, event: str, data: Dict[str, Any]) -> None:
        """
        Generic log method for flexible logging.
        
        Args:
            event: Event type/name
            data: Event data dictionary
        """
        # Extract session_id if present, otherwise use 'unknown'
        session_id = data.get("session_id", "unknown")
        
        # Log using structlog
        self.logger.info(event, **data)
        
        # Also write to session-specific file if session_id exists
        if session_id != "unknown":
            self._write_session_log(session_id, {
                "event": event,
                **data
            })
    
    def _write_session_log(self, session_id: str, data: Dict[str, Any]) -> None:
        """Write to session-specific log file."""
        log_file = self.log_dir / f"{session_id}.jsonl"
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(data) + '\n')


# Configure basic logging for structlog compatibility
logging.basicConfig(
    format="%(message)s",
    stream=None,
    level=logging.INFO,
)

