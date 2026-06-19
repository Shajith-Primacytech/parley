# PARLEY

**A multi-agent orbital conjunction negotiation system**

Built for the **Band of Agents Hackathon 2026** using [Band.ai's](https://band.ai) SDK, with Claude Sonnet (via AI/ML API) powering the negotiating agents and Featherless AI serving the Arbiter.

---

## What it does

When two satellites are on a collision course (an "orbital conjunction"), operators traditionally negotiate maneuvers manually — slow, error-prone, and not built for the scale of modern satellite constellations. PARLEY automates this negotiation with a council of AI agents that simulate the operators, evaluate risk, and arrive at a fair, physically valid resolution — without a human in the loop.

## The Agents

PARLEY is built around six specialized agents, each with a distinct role in the negotiation:

| Agent | Role |
|---|---|
| **Arbiter** | Adjudicates the negotiation and issues the final ruling. Powered by Featherless AI to keep the decision-maker model-independent from the negotiating parties. |
| **Archivist** | Maintains the historical record of past conjunctions and precedent, informing the Arbiter's decisions. |
| **Operator Alpha** | Represents satellite operator A — negotiates on behalf of its asset's interests (fuel cost, mission priority, maneuverability). |
| **Operator Bravo** | Represents satellite operator B — same role as Alpha, for the opposing asset. |
| **Oracle** | Provides orbital mechanics and collision-probability calculations to ground the negotiation in physical reality. |
| **Sentinel** | Monitors the negotiation for fairness and safety violations, flagging any proposed resolution that breaches collision-avoidance norms. |

## Architecture

- **Orchestration:** Band.ai SDK coordinates agent communication and turn-taking.
- **Negotiating agents:** Claude Sonnet via the AI/ML API.
- **Arbiter:** Featherless AI — deliberately separate from the negotiating agents' model provider to reduce bias in the final ruling.
- **Data:** Conjunction scenarios and negotiation norms are defined in `data/conjunction.json` and `data/norms.yaml`.
- **Config:** Agent roles, models, and behavior are defined in `agent_config.yaml`.

## Project Structure

```
parley/
├── agents/              # Agent implementations
│   ├── arbiter.py
│   ├── archivist.py
│   ├── operator_alpha.py
│   ├── operator_bravo.py
│   ├── oracle.py
│   └── sentinel.py
├── data/
│   ├── conjunction.json # Sample conjunction scenario
│   └── norms.yaml       # Collision-avoidance norms used by Sentinel
├── agent_config.yaml    # Agent + model configuration
├── main.py              # Entry point
├── pyproject.toml
└── uv.lock
```

## Running PARLEY

This project uses [`uv`](https://docs.astral.sh/uv/) for dependency management.

```bash
# Install dependencies
uv sync

# Run the negotiation
uv run python main.py
```

You'll need API keys for the AI/ML API and Featherless AI — set these as environment variables (see `.env.example` if present, or check `agent_config.yaml` for the expected variable names). **Never commit your `.env` file.**

## Why "PARLEY"?

A parley is a negotiation between adversaries to avoid further conflict — fitting for a system where two satellite operators (often competitors) need to agree on who moves, by how much, and when, to avoid a costly or catastrophic collision.

## Built for

[Band of Agents Hackathon 2026](https://band.ai) — submitted by [@buildwithshaji](https://twitter.com/buildwithshaji) / www.linkedin.com/in/mohamedshajith52

## License

No license specified yet — all rights reserved by default. Add a `LICENSE` file if you'd like to open this up.
