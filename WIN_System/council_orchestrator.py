import asyncio
import datetime
import json
import logging
import os
from pathlib import Path
from typing import Optional

import redis.asyncio as aioredis
from openai import AsyncOpenAI

from agents.persona_selector import select_personas

logger = logging.getLogger(__name__)


class CouncilOrchestrator:
    def __init__(self, agents_path, reports_path):
        self.agents_path = agents_path
        self.reports_path = reports_path

    def run_simulation(self, event_description):
        print(f"\n[!] INITIATING COUNCIL MEETING: '{event_description}'\n")

        agents = ["trump", "putin", "dalio"]
        discussion = []

        for agent_name in agents:
            with open(os.path.join(self.agents_path, f"{agent_name}_persona.json"), 'r') as f:
                persona = json.load(f)

            if agent_name == "trump":
                response = f"[{persona['name']}]: This DeepSeek thing... it's a huge disruption. China is playing dirty, but it shows our tech companies were overvalued. I'll bring the chip manufacturing back to Ohio. We don't need their software if we control the hardware. America First!"
            elif agent_name == "putin":
                response = f"[{persona['name']}]: The West's technological monopoly is breaking. DeepSeek proves that intelligence is not a Western privilege. We will partner with Beijing to integrate these models into our sovereign infrastructure. Sanctions are becoming irrelevant."
            elif agent_name == "dalio":
                response = f"[{persona['name']}]: This is a classic 'Changing World Order' move. A new power (China) disrupts the dominant power's (US) core advantage (AI). This accelerates the External Disorder cycle. NVDA's 12% drop is a symptom of a massive shift in productivity expectations. Rebalance now."

            discussion.append(response)
            print(response)

        with open(os.path.join(self.reports_path, "council_discussion_current.txt"), 'w', encoding='utf-8') as f:
            f.write("\n".join(discussion))


async def _run_council_for_scenario(
    llm: AsyncOpenAI,
    scenario: dict,
    personas: list[str],
    personas_dir: Path,
) -> dict:
    """Run LLM council and return briefing dict."""
    incident_title = scenario.get("incident_title", "Unknown Incident")
    nodes_summary = ", ".join(
        f"{n['label']} ({n['probability']:.0%})"
        for n in scenario.get("nodes", [])
    )
    persona_responses = []
    for persona_name in personas[:4]:  # cap at 4 to control cost
        persona_file = personas_dir / f"{persona_name}.json"
        if not persona_file.exists():
            continue
        with open(persona_file) as f:
            persona = json.load(f)
        name = persona.get("name", persona_name)
        role = persona.get("role", "")
        style = persona.get("communication_style", "analytical")
        prompt = (
            f"You are {name}, {role}. Respond in a {style} style. "
            f"Current geopolitical situation: '{incident_title}'. "
            f"Scenario probabilities: {nodes_summary}. "
            "In 2-3 sentences: what is your assessment and recommended action?"
        )
        try:
            resp = await llm.chat.completions.create(
                model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024,
                temperature=0.7,
            )
            import re as _re
            raw = resp.choices[0].message.content or ""
            text = _re.sub(r"<think>.*?</think>", "", raw, flags=_re.DOTALL).strip() or raw.strip()
            persona_responses.append({
                "persona": name,
                "response": text,
            })
        except Exception as e:
            logger.warning("LLM call failed for persona %s: %s", name, e)

    top_node = max(scenario.get("nodes", []), key=lambda n: n["probability"], default={})
    return {
        "incident_id": scenario.get("incident_id"),
        "incident_title": incident_title,
        "personas": [p["persona"] for p in persona_responses],
        "council_responses": persona_responses,
        "consensus_node": top_node.get("label", "Unknown"),
        "confidence": top_node.get("probability", 0.0),
        "briefing_text": "\n\n".join(
            f"**{r['persona']}**: {r['response']}" for r in persona_responses
        ),
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
    }


async def listen_and_brief(personas_dir: Optional[Path] = None) -> None:
    """Subscribe to scenario.updated and publish council.briefing for each update."""
    if personas_dir is None:
        personas_dir = Path(__file__).parent / "agents" / "personas"

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    llm_api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY", "")
    llm_base_url = os.getenv("LLM_BASE_URL")

    llm = AsyncOpenAI(api_key=llm_api_key, base_url=llm_base_url)

    while True:
        redis_client = aioredis.from_url(redis_url, decode_responses=True)
        try:
            pubsub = redis_client.pubsub()
            await pubsub.subscribe("scenario.updated")
            logger.info("WIN_System listening on scenario.updated")

            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue
                try:
                    scenario = json.loads(message["data"])
                    region = scenario.get("incident_title", "").split()[0]
                    template = "military_conflict"
                    personas = select_personas(region, template)
                    if not personas:
                        logger.warning("No personas found for region=%s", region)
                        continue
                    briefing = await _run_council_for_scenario(llm, scenario, personas, personas_dir)
                    if not briefing["council_responses"]:
                        logger.warning("All LLM calls failed for incident=%s, skipping publish", scenario.get("incident_id"))
                        continue
                    await redis_client.publish("council.briefing", json.dumps(briefing))
                    logger.info("Published council.briefing for incident=%s", scenario.get("incident_id"))
                except Exception:
                    logger.exception("Error processing council message")
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Redis connection lost, reconnecting in 5s")
            await asyncio.sleep(5)
        finally:
            await redis_client.aclose()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(listen_and_brief())
