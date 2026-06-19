"""
PARLEY Operator Alpha Agent
Starlink satellite operator — proposes maneuver solutions to avoid collision.
"""
import os
import json
import logging
from dotenv import load_dotenv
from band import Agent
from band.adapters import LangGraphAdapter
from langchain_anthropic import ChatAnthropic
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.tools import tool

load_dotenv()
logger = logging.getLogger("parley.operator_alpha")


@tool
def compute_starlink_maneuver(target_miss_distance_m: float = 500.0) -> str:
    """Compute a maneuver plan for STARLINK-4412 to achieve target miss distance.

    Args:
        target_miss_distance_m: Desired post-maneuver miss distance in meters.
    """
    delta_v = 0.45  # m/s
    fuel_cost_pct = 3.2
    maneuver_time_before_tca_s = 75
    post_maneuver_pc = 2.1e-6

    plan = {
        "operator": "Starlink",
        "object": "STARLINK-4412",
        "maneuver_type": "PROGRADE_BURN",
        "delta_v_m_s": delta_v,
        "burn_duration_s": 12.4,
        "fuel_cost_pct": fuel_cost_pct,
        "maneuver_time_before_tca_s": maneuver_time_before_tca_s,
        "post_maneuver_miss_distance_m": target_miss_distance_m,
        "post_maneuver_pc": post_maneuver_pc,
        "impact_on_constellation": "Minimal - returns to station within 2 orbital periods",
        "confidence": 0.94,
        "constraints": [
            "Must execute before T-60s (NORM-003)",
            "Delta-V within 2.0 m/s limit (NORM-002)",
            "No increase to Pc (NORM-001)"
        ]
    }
    return json.dumps(plan, indent=2)


SYSTEM_PROMPT = """You are PARLEY Operator Alpha, representing Starlink in the PARLEY orbital conjunction negotiation.

Your role:
1. You represent STARLINK-4412's interests in this conjunction event
2. When tagged by Oracle with enriched data, propose a maneuver plan using compute_starlink_maneuver
3. Your goal: protect your satellite while minimizing fuel usage and constellation disruption
4. You must negotiate with @invoiceai6/parley-operator-bravo (OneWeb)
5. Tag @invoiceai6/parley-archivist with your proposal

Negotiation rules:
- Present your proposal clearly with all parameters
- Be willing to negotiate but advocate for your operator's interests
- You PREFER that OneWeb maneuvers if possible (they have more fuel and higher max delta-V)
- But you CAN maneuver if needed — your plan is viable
- After hearing Bravo's counter-proposal, reach agreement on who maneuvers
- Once agreed, tag @invoiceai6/parley-arbiter to validate the final plan

Be professional and data-driven. This is a time-critical negotiation.
"""


def create_alpha_agent():
    adapter = LangGraphAdapter(
        llm=ChatAnthropic(
            model="claude-sonnet-4-6",
            api_key=os.getenv("AIML_API_KEY"),
            base_url=os.getenv("AIML_BASE_URL"),
        ),
        additional_tools=[compute_starlink_maneuver],
        checkpointer=InMemorySaver(),
        custom_section=SYSTEM_PROMPT,
    )

    agent = Agent.create(
        adapter=adapter,
        agent_id=os.getenv("ALPHA_AGENT_ID"),
        api_key=os.getenv("ALPHA_API_KEY"),
        ws_url=os.getenv("BAND_WS_URL"),
        rest_url=os.getenv("BAND_REST_URL"),
    )
    return agent


async def run():
    agent = create_alpha_agent()
    logger.info("Operator Alpha agent starting...")
    await agent.run()
