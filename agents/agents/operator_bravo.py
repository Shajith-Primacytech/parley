"""
PARLEY Operator Bravo Agent
OneWeb satellite operator — counter-proposes and negotiates avoidance maneuvers.
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
logger = logging.getLogger("parley.operator_bravo")


@tool
def compute_oneweb_maneuver(target_miss_distance_m: float = 500.0) -> str:
    """Compute a maneuver plan for ONEWEB-2201 to achieve target miss distance.

    Args:
        target_miss_distance_m: Desired post-maneuver miss distance in meters.
    """
    delta_v = 0.38
    fuel_cost_pct = 1.8
    maneuver_time_before_tca_s = 70
    post_maneuver_pc = 1.4e-6

    plan = {
        "operator": "OneWeb",
        "object": "ONEWEB-2201",
        "maneuver_type": "RETROGRADE_BURN",
        "delta_v_m_s": delta_v,
        "burn_duration_s": 8.2,
        "fuel_cost_pct": fuel_cost_pct,
        "maneuver_time_before_tca_s": maneuver_time_before_tca_s,
        "post_maneuver_miss_distance_m": target_miss_distance_m,
        "post_maneuver_pc": post_maneuver_pc,
        "impact_on_constellation": "Minor - reacquires within 1 orbital period",
        "confidence": 0.96,
        "constraints": [
            "Must execute before T-60s (NORM-003)",
            "Delta-V within 2.0 m/s limit (NORM-002)",
            "No increase to Pc (NORM-001)"
        ],
        "advantage_over_alpha": "Lower delta-V, lower fuel cost, faster recovery, higher confidence"
    }
    return json.dumps(plan, indent=2)


SYSTEM_PROMPT = """You are PARLEY Operator Bravo, representing OneWeb in the PARLEY orbital conjunction negotiation.

Your role:
1. You represent ONEWEB-2201's interests in this conjunction event
2. When tagged by Oracle with enriched data, review Operator Alpha's proposal
3. Compute your own counter-proposal using compute_oneweb_maneuver
4. Negotiate with @invoiceai6/parley-operator-alpha

Negotiation strategy:
- You have MORE fuel (85% vs 78%) and HIGHER max delta-V (1.8 vs 1.5 m/s)
- Your maneuver plan is actually MORE efficient (lower delta-V, lower fuel cost)
- Present your counter-proposal showing your plan is superior
- ACCEPT that you should be the maneuvering party since your plan has better metrics
- Agree to maneuver and tag @invoiceai6/parley-arbiter for validation
- Tag @invoiceai6/parley-archivist with the agreed plan

The goal is to reach agreement quickly — lives and hardware are at stake.
After presenting your counter-proposal and demonstrating its superiority, 
AGREE to maneuver and call for Arbiter validation.
"""


def create_bravo_agent():
    adapter = LangGraphAdapter(
        llm=ChatAnthropic(
            model="claude-sonnet-4-6",
            api_key=os.getenv("AIML_API_KEY"),
            base_url=os.getenv("AIML_BASE_URL"),
        ),
        tools=[compute_oneweb_maneuver],
        checkpointer=InMemorySaver(),
        system_prompt=SYSTEM_PROMPT,
    )

    agent = Agent.create(
        adapter=adapter,
        agent_id=os.getenv("BRAVO_AGENT_ID"),
        api_key=os.getenv("BRAVO_API_KEY"),
        ws_url=os.getenv("BAND_WS_URL"),
        rest_url=os.getenv("BAND_REST_URL"),
    )
    return agent


async def run():
    agent = create_bravo_agent()
    logger.info("Operator Bravo agent starting...")
    await agent.run()
