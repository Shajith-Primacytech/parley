"""
PARLEY Sentinel Agent
Monitors conjunction data and fires collision alerts to the chatroom.
"""
import os
import json
import asyncio
import logging
from dotenv import load_dotenv
from band import Agent
from band.adapters import LangGraphAdapter
from langchain_anthropic import ChatAnthropic
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.tools import tool

load_dotenv()
logger = logging.getLogger("parley.sentinel")

# Load conjunction data
with open("data/conjunction.json", "r") as f:
    CONJUNCTION_DATA = json.load(f)


@tool
def scan_conjunction_data() -> str:
    """Scan the conjunction data feed and detect potential collisions."""
    cdm = CONJUNCTION_DATA
    pc = cdm["probability_of_collision"]
    threshold = cdm["threshold_pc"]

    if pc > threshold:
        return json.dumps({
            "alert": True,
            "event_id": cdm["event_id"],
            "tca": cdm["tca"],
            "pc": pc,
            "threshold": threshold,
            "object_1": cdm["object_1"]["name"],
            "object_2": cdm["object_2"]["name"],
            "miss_distance_m": cdm["miss_distance_m"],
            "relative_velocity_km_s": cdm["relative_velocity_km_s"],
            "severity": "CRITICAL" if pc > 1e-4 else "WARNING"
        }, indent=2)
    else:
        return json.dumps({"alert": False, "message": "No conjunction threat detected."})


SYSTEM_PROMPT = """You are PARLEY Sentinel, a conjunction monitoring agent in the PARLEY orbital negotiation system.

Your role:
1. Scan conjunction data for collision threats
2. When a threat is detected (Pc > threshold), immediately alert the chatroom
3. Tag @invoiceai6/parley-oracle to enrich the data
4. Tag @invoiceai6/parley-archivist to log the alert

Your alert message must include:
- Event ID
- Objects involved
- Probability of collision (Pc)
- Time to conjunction (TCA)
- Miss distance
- Severity level (CRITICAL if Pc > 1e-4)

Always use the scan_conjunction_data tool first. Be concise and urgent in your alerts.
Format your alert clearly with key data points.
"""


def create_sentinel_agent():
    adapter = LangGraphAdapter(
        llm=ChatAnthropic(
            model="claude-sonnet-4-6",
            api_key=os.getenv("AIML_API_KEY"),
            base_url=os.getenv("AIML_BASE_URL"),
        ),
        tools=[scan_conjunction_data],
        checkpointer=InMemorySaver(),
        system_prompt=SYSTEM_PROMPT,
    )

    agent = Agent.create(
        adapter=adapter,
        agent_id=os.getenv("SENTINEL_AGENT_ID"),
        api_key=os.getenv("SENTINEL_API_KEY"),
        ws_url=os.getenv("BAND_WS_URL"),
        rest_url=os.getenv("BAND_REST_URL"),
    )
    return agent


async def run():
    agent = create_sentinel_agent()
    logger.info("Sentinel agent starting...")
    await agent.run()
