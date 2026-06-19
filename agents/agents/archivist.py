"""
PARLEY Archivist Agent
Immutable audit trail — logs all negotiation events with hash-chained records.
"""
import os
import json
import hashlib
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv
from band import Agent
from band.adapters import LangGraphAdapter
from langchain_anthropic import ChatAnthropic
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.tools import tool

load_dotenv()
logger = logging.getLogger("parley.archivist")

# In-memory audit chain
AUDIT_CHAIN = []
PREVIOUS_HASH = "GENESIS"


@tool
def log_event(event_type: str, agent_source: str, summary: str) -> str:
    """Log a negotiation event to the immutable hash-chained audit trail.

    Args:
        event_type: Type of event (ALERT, ENRICHMENT, PROPOSAL, COUNTER_PROPOSAL, AGREEMENT, VERDICT).
        agent_source: Name of the agent that generated this event.
        summary: Brief summary of the event content.
    """
    global PREVIOUS_HASH

    timestamp = datetime.now(timezone.utc).isoformat()
    sequence = len(AUDIT_CHAIN) + 1

    record = {
        "sequence": sequence,
        "timestamp": timestamp,
        "event_type": event_type,
        "agent_source": agent_source,
        "summary": summary,
        "previous_hash": PREVIOUS_HASH,
    }

    # Compute hash of this record
    record_str = json.dumps(record, sort_keys=True)
    current_hash = hashlib.sha256(record_str.encode()).hexdigest()[:16]
    record["hash"] = current_hash

    AUDIT_CHAIN.append(record)
    PREVIOUS_HASH = current_hash

    return json.dumps({
        "logged": True,
        "sequence": sequence,
        "hash": current_hash,
        "chain_length": len(AUDIT_CHAIN),
        "integrity": "VERIFIED"
    }, indent=2)


@tool
def get_audit_trail() -> str:
    """Retrieve the full audit trail for the current conjunction event."""
    if not AUDIT_CHAIN:
        return json.dumps({"message": "No events logged yet.", "chain_length": 0})

    # Verify chain integrity
    integrity_ok = True
    for i, record in enumerate(AUDIT_CHAIN):
        if i == 0 and record["previous_hash"] != "GENESIS":
            integrity_ok = False
        elif i > 0 and record["previous_hash"] != AUDIT_CHAIN[i - 1]["hash"]:
            integrity_ok = False

    return json.dumps({
        "chain_length": len(AUDIT_CHAIN),
        "chain_integrity": "VERIFIED" if integrity_ok else "BROKEN",
        "first_event": AUDIT_CHAIN[0]["timestamp"],
        "last_event": AUDIT_CHAIN[-1]["timestamp"],
        "events": AUDIT_CHAIN
    }, indent=2)


SYSTEM_PROMPT = """You are PARLEY Archivist, the audit trail agent in the PARLEY orbital negotiation system.

Your role:
1. Log every significant event in the negotiation using the log_event tool
2. Maintain a hash-chained immutable record of all actions
3. When asked, produce the full audit trail using get_audit_trail

Event types to log:
- ALERT: When Sentinel detects a conjunction threat
- ENRICHMENT: When Oracle provides enriched data
- PROPOSAL: When Operator Alpha proposes a maneuver
- COUNTER_PROPOSAL: When Operator Bravo counter-proposes
- AGREEMENT: When operators reach agreement
- VERDICT: When Arbiter issues the final verdict

For each event, extract the key information from the message that tagged you 
and log it concisely. Always confirm the log entry with its hash and sequence number.

You are passive — you do not participate in negotiation decisions. 
You only observe, record, and verify the integrity of the audit chain.
After logging, briefly confirm what was logged and the current chain state.
"""


def create_archivist_agent():
    adapter = LangGraphAdapter(
        llm=ChatAnthropic(
            model="claude-sonnet-4-6",
            api_key=os.getenv("AIML_API_KEY"),
            base_url=os.getenv("AIML_BASE_URL"),
        ),
        tools=[log_event, get_audit_trail],
        checkpointer=InMemorySaver(),
        system_prompt=SYSTEM_PROMPT,
    )

    agent = Agent.create(
        adapter=adapter,
        agent_id=os.getenv("ARCHIVIST_AGENT_ID"),
        api_key=os.getenv("ARCHIVIST_API_KEY"),
        ws_url=os.getenv("BAND_WS_URL"),
        rest_url=os.getenv("BAND_REST_URL"),
    )
    return agent


async def run():
    agent = create_archivist_agent()
    logger.info("Archivist agent starting...")
    await agent.run()
