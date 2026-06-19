"""
PARLEY — Multi-Agent Orbital Conjunction Negotiation System
Band of Agents Hackathon | June 2026

Runs all 6 agents concurrently. They coordinate via Band.ai chatroom
using @mention routing to negotiate satellite collision avoidance.

Agents:
  1. Sentinel   — detects conjunction threat
  2. Oracle     — enriches with orbital data
  3. Op Alpha   — Starlink negotiator
  4. Op Bravo   — OneWeb negotiator
  5. Arbiter    — compliance checker (Featherless AI)
  6. Archivist  — hash-chained audit trail

Usage:
  uv run python main.py
"""
import asyncio
import logging
import signal
import sys
from dotenv import load_dotenv

from agents.sentinel import create_sentinel_agent
from agents.oracle import create_oracle_agent
from agents.operator_alpha import create_alpha_agent
from agents.operator_bravo import create_bravo_agent
from agents.arbiter import create_arbiter_agent
from agents.archivist import create_archivist_agent

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("parley.main")

# Suppress noisy loggers
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("websockets").setLevel(logging.WARNING)
logging.getLogger("langchain").setLevel(logging.WARNING)


async def run_agent(name: str, agent):
    """Run a single agent with error handling."""
    try:
        logger.info(f"Starting {name}...")
        await agent.run()
    except Exception as e:
        logger.error(f"{name} crashed: {e}")
        raise


async def main():
    logger.info("=" * 60)
    logger.info("PARLEY — Orbital Conjunction Negotiation System")
    logger.info("=" * 60)
    logger.info("Initializing 6 agents...")

    # Create all agents
    agents = {
        "Sentinel": create_sentinel_agent(),
        "Oracle": create_oracle_agent(),
        "Operator Alpha": create_alpha_agent(),
        "Operator Bravo": create_bravo_agent(),
        "Arbiter": create_arbiter_agent(),
        "Archivist": create_archivist_agent(),
    }

    logger.info(f"All {len(agents)} agents created. Connecting to Band.ai...")
    logger.info("")
    logger.info("Agents will coordinate in the Band.ai chatroom.")
    logger.info("To start the negotiation, go to app.band.ai,")
    logger.info("open the chatroom, and send:")
    logger.info('  "@invoiceai6/parley-sentinel scan for conjunction threats"')
    logger.info("")
    logger.info("Press Ctrl+C to stop all agents.")
    logger.info("=" * 60)

    # Run all agents concurrently
    tasks = [
        asyncio.create_task(run_agent(name, agent))
        for name, agent in agents.items()
    ]

    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        logger.info("Shutting down all agents...")
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("All agents stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("PARLEY shutdown complete.")
        sys.exit(0)
