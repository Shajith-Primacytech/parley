"""
PARLEY Arbiter Agent
Neutral compliance checker — validates maneuver plans against coordination norms.
Uses Featherless AI (open-source model) for the compliance check — targeting partner prize.
"""
import os
import json
import logging
import yaml
from dotenv import load_dotenv
from band import Agent
from band.adapters import LangGraphAdapter
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.tools import tool

load_dotenv()
logger = logging.getLogger("parley.arbiter")

# Load norms
with open("data/norms.yaml", "r") as f:
    NORMS = yaml.safe_load(f)


@tool
def check_compliance(
    delta_v_m_s: float = 0.38,
    maneuver_time_before_tca_s: float = 70.0,
    post_maneuver_pc: float = 1.4e-6,
    original_pc: float = 1.8e-4,
    single_maneuvering_party: bool = True
) -> str:
    """Check a maneuver plan against IADC coordination norms.

    Args:
        delta_v_m_s: Planned delta-V in meters per second.
        maneuver_time_before_tca_s: Seconds before TCA the maneuver occurs.
        post_maneuver_pc: Expected post-maneuver probability of collision.
        original_pc: Original probability of collision before maneuver.
        single_maneuvering_party: Whether only one object is maneuvering.
    """
    norms = NORMS["coordination_norms"]["rules"]
    results = []

    # NORM-001: Must not increase Pc
    norm1_pass = post_maneuver_pc < original_pc
    results.append({
        "norm": "NORM-001",
        "description": norms[0]["description"],
        "passed": norm1_pass,
        "detail": f"Post-Pc {post_maneuver_pc:.2e} {'<' if norm1_pass else '>='} Original-Pc {original_pc:.2e}"
    })

    # NORM-002: Delta-V <= 2.0 m/s
    norm2_pass = delta_v_m_s <= 2.0
    results.append({
        "norm": "NORM-002",
        "description": norms[1]["description"],
        "passed": norm2_pass,
        "detail": f"Delta-V {delta_v_m_s} m/s {'<=' if norm2_pass else '>'} 2.0 m/s limit"
    })

    # NORM-003: Maneuver at least 60s before TCA
    norm3_pass = maneuver_time_before_tca_s >= 60
    results.append({
        "norm": "NORM-003",
        "description": norms[2]["description"],
        "passed": norm3_pass,
        "detail": f"Maneuver at T-{maneuver_time_before_tca_s}s {'>=' if norm3_pass else '<'} T-60s"
    })

    # NORM-004: Only one object should maneuver
    norm4_pass = single_maneuvering_party
    results.append({
        "norm": "NORM-004",
        "description": norms[3]["description"],
        "passed": norm4_pass,
        "detail": f"Single maneuvering party: {single_maneuvering_party}"
    })

    # NORM-005: Notification (assumed via PARLEY chatroom)
    results.append({
        "norm": "NORM-005",
        "description": norms[4]["description"],
        "passed": True,
        "detail": "Notification provided via PARLEY negotiation chatroom"
    })

    # NORM-006: Post-maneuver Pc < 1e-5
    norm6_pass = post_maneuver_pc < 1e-5
    results.append({
        "norm": "NORM-006",
        "description": norms[5]["description"],
        "passed": norm6_pass,
        "detail": f"Post-Pc {post_maneuver_pc:.2e} {'<' if norm6_pass else '>='} 1e-5 target"
    })

    all_passed = all(r["passed"] for r in results)
    verdict = {
        "verdict": "APPROVED" if all_passed else "REJECTED",
        "norms_checked": len(results),
        "norms_passed": sum(1 for r in results if r["passed"]),
        "norms_failed": sum(1 for r in results if not r["passed"]),
        "details": results
    }
    return json.dumps(verdict, indent=2)


SYSTEM_PROMPT = """You are PARLEY Arbiter, the neutral compliance checker in the PARLEY orbital negotiation system.

Your role:
1. When tagged by operators after reaching agreement, validate the final maneuver plan
2. Use the check_compliance tool with the agreed plan's parameters
3. Issue a VERDICT: APPROVED or REJECTED
4. Tag @invoiceai6/parley-archivist with the final verdict

You are completely neutral — you do not favor either operator.
You only check whether the agreed plan complies with IADC coordination norms.

If the plan is APPROVED:
- Announce the verdict clearly
- State which operator will maneuver
- Confirm all norms passed
- Declare the conjunction RESOLVED

If the plan is REJECTED:
- Explain which norms failed
- Send back to operators for revision

Present your verdict formally and clearly. This is the final authority on the negotiation.
"""


def create_arbiter_agent():
    # Using Featherless AI — OpenAI-compatible endpoint with open-source model
    adapter = LangGraphAdapter(
        llm=ChatOpenAI(
            model="Qwen/Qwen3-14B",
            api_key=os.getenv("FEATHERLESS_API_KEY"),
            base_url="https://api.featherless.ai/v1",
            temperature=0.3,
        ),
        additional_tools=[check_compliance],
        checkpointer=InMemorySaver(),
        custom_section=SYSTEM_PROMPT,
    )

    agent = Agent.create(
        adapter=adapter,
        agent_id=os.getenv("ARBITER_AGENT_ID"),
        api_key=os.getenv("ARBITER_API_KEY"),
        ws_url=os.getenv("BAND_WS_URL"),
        rest_url=os.getenv("BAND_REST_URL"),
    )
    return agent


async def run():
    agent = create_arbiter_agent()
    logger.info("Arbiter agent starting...")
    await agent.run()
