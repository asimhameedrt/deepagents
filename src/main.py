"""Main entry point for the Deep Research Agent."""

import asyncio
import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from .config.settings import settings
from .models.state import AgentState
from .agents.graph import research_graph
from .utils.helpers import generate_session_id, format_duration
from .observability.audit_logger import AuditLogger
from langfuse import Langfuse, get_client
from langfuse.langchain import CallbackHandler

class DeepResearchAgent:
    """Main agent class for conducting deep research."""
    
    def __init__(self):
        """Initialize the agent."""
        self.graph = research_graph
        self.audit_logger = AuditLogger()
        
        # Initialize LangFuse callback handler if available (only import if keys configured)
        self.langfuse_handler = None
        if settings.langfuse_public_key and settings.langfuse_secret_key:
            try:
                # --- Langfuse init (optional explicit init instead of env-only) ---
                langfuse_client = get_client(
                    public_key=settings.langfuse_public_key,
                    secret_key=settings.langfuse_secret_key,
                )
                self.langfuse_handler = CallbackHandler()
            except Exception:
                self.langfuse_handler = None
    
    async def research(
        self,
        subject: str,
        context: Optional[str] = None,
        max_depth: Optional[int] = None
    ) -> dict:
        """
        Conduct deep research on a subject.
        
        Args:
            subject: Name of person or entity to research
            context: Additional context about the subject
            max_depth: Maximum search depth (defaults to config)
            
        Returns:
            Dict with research report and metadata
        """
        # Generate session ID
        session_id = generate_session_id()
        
        # Initialize state
        initial_state: AgentState = {
            "session_id": session_id,
            "subject": subject,
            "subject_context": context,
            "current_depth": 0,
            "max_depth": max_depth or settings.max_search_depth,
            "queries_executed": [],
            "pending_queries": [],
            "should_continue": True,
            "termination_reason": None,
            "start_time": datetime.utcnow(),
            "search_count": 0,
            "extraction_count": 0,
            "error_count": 0,
            "iteration_count": 0,
            "search_iterations": [],  # For audit trail
            "messages": []
        }
        
        # Log session start
        self.audit_logger.log_session_start(
            session_id=session_id,
            subject=subject,
            config={
                "max_depth": initial_state["max_depth"],
                "max_queries_per_depth": settings.max_queries_per_depth,
            }
        )
        
        # Log to console
        print(f"\n{'='*80}")
        print(f"🔍 Deep Research AI Agent")
        print(f"{'='*80}")
        print(f"Subject: {subject}")
        print(f"Session ID: {session_id}")
        print(f"Max depth: {initial_state['max_depth']}")
        print(f"{'='*80}\n")
        
        # Execute the graph
        try:
            config = {
                "recursion_limit": 100,  # Allow up to 100 node executions
                "max_concurrency": 10
            }
            
            # Add LangFuse callback if available
            if self.langfuse_handler:
                config["callbacks"] = [self.langfuse_handler]
            
            final_state = await self.graph.ainvoke(initial_state, config=config)
            
            # # Extract report
            # report = final_state.get("report")
                
        except Exception as e:
            error_msg = f"Error during research: {e}"
            print(f"❌ {error_msg}")
            self.audit_logger.log("error", {
                "session_id": session_id,
                "subject": subject,
                "error": str(e)
            })
            return {
                "session_id": session_id,
                "success": False,
                "error": str(e)
            }
    
    def _save_report(self, report, session_id: str) -> Path:
        """Save report to file."""
        reports_dir = settings.reports_dir
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Save as JSON
        report_file = reports_dir / f"{session_id}_report.json"
        
        with open(report_file, 'w') as f:
            json.dump(report.model_dump(), f, indent=2, default=str)
        
        return report_file


async def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Deep Research AI Agent for Enhanced Due Diligence"
    )
    parser.add_argument(
        "subject",
        help="Name of person or entity to research"
    )
    parser.add_argument(
        "-c", "--context",
        help="Additional context about the subject",
        default=None
    )
    parser.add_argument(
        "-d", "--max-depth",
        help="Maximum search depth",
        type=int,
        default=None
    )
    
    args = parser.parse_args()
    
    # Create agent
    agent = DeepResearchAgent()
    
    # Run research
    result = await agent.research(
        subject=args.subject,
        context=args.context,
        max_depth=args.max_depth
    )
    
    # Return appropriate exit code
    return 0 if result["success"] else 1


if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

