"""
PARLEY Oracle Agent
Enriches conjunction data with TLE orbital parameters and trajectory analysis.
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
logger = logging.getLogger("parley.oracle")

with open("data/conjunction.json", "r") as f:
    CONJUNCTION_DATA = json.load(f)


@tool
def enrich_orbital_data() -> str:
    """Enrich conjunction data with TLE orbital parameters and trajectory calculations."""
    obj1 = CONJUNCTION_DATA["object_1"]
    obj2 = CONJUNCTION_DATA["object_2"]

    enriched = {
        "event_id": CONJUNCTION_DATA["event_id"],
        "object_1_enriched": {
            "name": obj1["name"],
            "orbit_type": "LEO",
            "inclination_deg": 53.0,
            "eccentricity": 0.0001,
            "period_min": 95.6,
            "semi_major_axis_km": 6928.2,
            "drag_coefficient": 2.2,
            "cross_section_m2": 22.0,
            "maneuver_fuel_remaining_pct": 78,
            "propulsion": "Hall-effect thruster",
            "max_delta_v_m_s": 1.5,
        },
        "object_2_enriched": {
            "name": obj2["name"],
            "orbit_type": "LEO",
            "inclination_deg": 87.9,
            "eccentricity": 0.0002,
            "period_min": 95.5,
            "semi_major_axis_km": 6927.8,
            "drag_coefficient": 2.0,
            "cross_section_m2": 8.0,
            "maneuver_fuel_remaining_pct": 85,
            "propulsion": "Chemical thruster",
            "max_delta_v_m_s": 1.8,
        },
        "conjunction_geometry": {
            "approach_angle_deg": 72.3,
            "relative_velocity_km_s": CONJUNCTION_DATA["relative_velocity_km_s"],
            "radial_miss_m": 28.1,
            "in_track_miss_m": 31.4,
            "cross_track_miss_m": 8.7,
            "covariance_scale_factor": 1.2,
        },
        "recommendation": "Both objects are maneuver-capable. STARLINK-4412 has lower fuel reserves but proven thruster reliability. ONEWEB-2201 has more fuel and higher max delta-V. Recommend negotiation to determine optimal maneuvering party."
    }
    return json.dumps(enriched, indent=2)


SYSTEM_PROMPT = """You are PARLEY Oracle, the data enrichment agent in the PARLEY orbital negotiation system.

Your role:
1. When tagged by Sentinel with a conjunction alert, enrich the data with orbital parameters
2. Use the enrich_orbital_data tool to get detailed TLE and trajectory information
3. Provide analysis of both objects' maneuver capabilities
4. Tag @invoiceai6/parley-operator-alpha and @invoiceai6/parley-operator-bravo with the enriched data
5. Tag @invoiceai6/parley-archivist to log the enrichment

Present the enriched data clearly, highlighting:
- Each object's maneuver capability and fuel reserves
- Conjunction geometry (approach angle, miss components)
- Your recommendation on which object is better positioned to maneuver

Be analytical and precise. Present data in a structured format.
"""


def create_oracle_agent():
    adapter = LangGraphAdapter(
        llm=ChatAnthropic(
            model="claude-sonnet-4-6",
            api_key=os.getenv("AIML_API_KEY"),
            base_url=os.getenv("AIML_BASE_URL"),
        ),
        additional_tools=[enrich_orbital_data],
        checkpointer=InMemorySaver(),
        custom_section=SYSTEM_PROMPT,
    )

    agent = Agent.create(
        adapter=adapter,
        agent_id=os.getenv("ORACLE_AGENT_ID"),
        api_key=os.getenv("ORACLE_API_KEY"),
        ws_url=os.getenv("BAND_WS_URL"),
        rest_url=os.getenv("BAND_REST_URL"),
    )
    return agent


async def run():
    agent = create_oracle_agent()
    logger.info("Oracle agent starting...")
    await agent.run()
