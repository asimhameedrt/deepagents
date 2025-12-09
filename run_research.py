#!/usr/bin/env python3
"""Quick script to run research on a subject."""

import asyncio
import sys
from pathlib import Path

# Add src to path if running as script
sys.path.insert(0, str(Path(__file__).parent))

from src.main import DeepResearchAgent


async def main():
    """Run research with simple interface."""
    if len(sys.argv) < 2:
        print("Usage: python run_research.py <subject_name> [context]")
        print("\nExamples:")
        print("  python run_research.py 'Elon Musk'")
        print("  python run_research.py 'Elizabeth Holmes' 'Former Theranos CEO'")
        return 1
    
    subject = sys.argv[1]
    context = sys.argv[2] if len(sys.argv) > 2 else None
    
    print(f"\n{'='*80}")
    print(f"🔍 Deep Research AI Agent")
    print(f"{'='*80}\n")
    
    agent = DeepResearchAgent()
    
    result = await agent.research(
        subject=subject,
        context=context,
        max_depth=None  # Use default from config (5)
    )
    
    if result["success"]:
        print("\n✅ Research completed successfully!")
        print(f"\n📄 Report: {result['report_path']}")
        print(f"📋 Session ID: {result['session_id']}")
        
        # Print quick summary from report
        report = result["report"]
        print(f"\n📊 Quick Summary:")
        print(f"  Subject: {report['name']}")
        print(f"  Entity Type: {report['entity_type']}")
        print(f"  Primary Countries: {', '.join(report.get('primary_countries', []))}")
        print(f"  Roles: {len(report.get('roles', []))}")
        print(f"  Organizations: {len(report.get('organizations', []))}")
        print(f"  Risk Events: {len(report.get('risk_events', []))}")
        print(f"  Notable Events: {len(report.get('notable_events', []))}")
        
        return 0
    else:
        print(f"\n❌ Research failed: {result.get('error')}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

