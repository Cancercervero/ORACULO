# Scenario Tree Engine — Design Spec

**Date:** 2026-05-03  
**Status:** Approved  
**Sub-project:** 1 of 8 (Warren Wayne integration series)

---

## Overview

Warren Wayne has three isolated systems — ShadowBroker (OSINT), WIN_System (geopolitical council), MiroFish (social simulation) — that currently share no state and cannot react to each other. This spec defines **warren-core**, a new central service that connects them via a live scenario tree: a per-incident probabilistic model of possible outcomes that updates in real time as OSINT signals arrive.

**Core concept:** Information (OSINT events) flows into a tree of scenarios per active incident. Each signal has a direction (escalatory or de-escalatory) and a severity. Warren-core updates branch probabilities as signals arrive. WIN_System and MiroFish subscribe to these updates and react automatically.

---

## Decisions Made

| Question | Decision | Rationale |
|---|---|---|
| Transport | Redis pub/sub | Minimal new infra, async-native, trivial Docker Compose addition |
| Event flows | ShadowBroker→WIN, WIN→MiroFish | MVP loop: real event → intelligence → social simulation |
| Tree model | Template scenarios + dynamic probability weights | Controlled, predictable cost, proven geopolitical framing |
| Tree granularity | Per incident | Natural unit; lifecycle (open/archive); no cross-contamination |
| Implementation | Redis (hot state) + PostgreSQL (history) | Backtesting requires history; Redis alone too fragile |

---

## Architecture

```
ShadowBroker (FastAPI :8000)
    │
    │  PUBLISH osint.alert
    ▼
Redis :6379  ◄──────────────────────────────────────────┐
    │                                                    │
    │  SUBSCRIBE all channels                            │ PUBLISH council.briefing
    ▼                                                    │
warren-core (FastAPI :9000)                        WIN_System
    │  IncidentClassifier                               (subscribes scenario.updated)
    │  ProbabilityEngine                                     │
    │  ScenarioTemplates                                     │ PUBLISH council.briefing
    │                                                        ▼
    ├── SET incident:{id} ──────► Redis (hot)          MiroFish (Flask :5001)
    ├── INSERT ─────────────────► PostgreSQL :5432      (subscribes council.briefing)
    │                                                        │
    └── PUBLISH scenario.updated ──► Redis ◄───────────────── PUBLISH sim.result
```

**Event channels and payload schemas:**

| Channel | Publisher | Subscribers | Trigger |
|---|---|---|---|
| `osint.alert` | ShadowBroker | warren-core | GPS jamming, carrier move, GDELT spike, conflict event, Ukraine alert |
| `scenario.updated` | warren-core | WIN_System, MiroFish | Any node probability shifts ≥ 0.01 |
| `council.briefing` | WIN_System | warren-core, MiroFish | Council finishes briefing for an incident |
| `sim.result` | MiroFish | warren-core | Simulation completes — sentiment + narratives |

**Payload schemas (all JSON over Redis):**

```json
// osint.alert
{ "type": "gps_jamming", "severity": 0.85, "region": "Baltic",
  "source": "shadowbroker", "payload": { ...raw feed data... } }

// scenario.updated
{ "incident_id": "uuid", "incident_title": "Baltic GPS Crisis",
  "nodes": [{ "id": "uuid", "label": "Escalacion", "probability": 0.52, "direction": "right" }, ...],
  "triggered_by": { "event_type": "gps_jamming", "severity": 0.85 } }

// council.briefing
{ "incident_id": "uuid", "personas": ["putin", "biden", "dalio"],
  "briefing_text": "...", "consensus_node": "Escalacion militar",
  "confidence": 0.72, "generated_at": "2026-05-03T14:22:01Z" }

// sim.result
{ "incident_id": "uuid", "sentiment_score": -0.34,
  "top_narratives": ["NATO expansion rhetoric", "Economic pressure narrative", ...],
  "platform_breakdown": { "twitter": { "sentiment": -0.41, "agent_count": 100 },
                          "reddit": { "sentiment": -0.27, "agent_count": 80 } },
  "completed_at": "2026-05-03T14:35:00Z" }
```

---

## Data Model

### PostgreSQL

```sql
-- Active and archived incidents
incidents (
  id                UUID PRIMARY KEY,
  title             TEXT,                       -- "Baltic GPS Jamming Crisis"
  region            TEXT,                       -- "Baltic", "Taiwan", "MidEast"
  status            ENUM('active','archived'),
  scenario_template TEXT,                       -- "military_conflict" | "economic_crisis" | "diplomatic" | "cyber_incident"
  created_at        TIMESTAMPTZ,
  resolved_at       TIMESTAMPTZ                 -- NULL while active
)

-- Scenario tree nodes (branches)
scenario_nodes (
  id          UUID PRIMARY KEY,
  incident_id UUID REFERENCES incidents(id),
  parent_id   UUID REFERENCES scenario_nodes(id),  -- NULL = root
  label       TEXT,                                 -- "Escalacion militar"
  probability FLOAT,                                -- 0.0–1.0, all siblings sum to 1.0
  direction   ENUM('left','right')                  -- left=de-escalatory, right=escalatory
)

-- Full history of probability changes
probability_history (
  node_id          UUID REFERENCES scenario_nodes(id),
  probability      FLOAT,
  recorded_at      TIMESTAMPTZ,
  trigger_event_id UUID REFERENCES osint_events(id)
)

-- All OSINT events received, classified to incident
osint_events (
  id          UUID PRIMARY KEY,
  incident_id UUID REFERENCES incidents(id),
  source      TEXT,       -- "flights" | "geo" | "sigint" | "news" | ...
  event_type  TEXT,       -- "gps_jamming" | "carrier_movement" | "gdelt_spike" | ...
  severity    FLOAT,      -- 0.0–1.0 (scored by SeverityScorer rules)
  payload     JSONB,      -- raw feed data
  received_at TIMESTAMPTZ
)
```

### Redis Hot State

```
incident:{uuid}        → JSON  (full tree with current probabilities)
active_incidents       → SET   (all active incident UUIDs)
```

**Consistency rule:** Redis = source of truth for active state. PostgreSQL = source of truth for history. Warren-core writes to both on every update. On startup, warren-core reloads active incidents from PostgreSQL into Redis.

### Scenario Templates (JSON, editable without code)

```json
{
  "military_conflict": ["Escalacion militar", "Tension diplomatica", "Stalemate", "De-escalacion"],
  "economic_crisis":   ["Recesion profunda", "Contraccion", "Estabilidad", "Rebote"],
  "diplomatic":        ["Ruptura total", "Negociacion", "Acuerdo", "Status-quo"],
  "cyber_incident":    ["Ataque masivo", "Espionaje", "Probe", "Ruido de fondo"]
}
```

Initial probabilities: uniform distribution (0.25 each node).

---

## warren-core Service

**Stack:** FastAPI, asyncio, redis-py (async), asyncpg, SQLAlchemy 2.0, Alembic  
**Port:** 9000  
**LLM usage:** Single cheap call per event for `direction_score` (classify escalatory/de-escalatory). Model: `gpt-4o-mini` or `claude-haiku-4-5`.

### Modules

**`IncidentClassifier`** — maps incoming `osint.alert` to an incident:
```
input: { type, region, severity, payload }
match = active incident where: region == event.region AND created_at > now-24h
if match found → assign to existing incident
elif severity > 0.6 → create new incident (auto-title via LLM cheap call, same model as direction_score)
else → discard (noise, severity ≤ 0.6 with no active incident)
```
Region matching is exact string match (e.g. "Baltic", "Taiwan"). One active incident per region at a time for MVP.

**`ProbabilityEngine`** — updates node weights:
```
direction_score = LLM classify(event) → float 0.0–1.0 (0=de-escal, 1=escal)
event_weight = severity × direction_score
for each escalatory node (direction=right): prob += event_weight × 0.15
for each de-escalatory node (direction=left): prob -= event_weight × 0.15
re-normalize: all siblings sum to 1.0
if max delta < 0.01: skip publish (no meaningful change)
```

The `0.15` dampening factor prevents single events from dominating. Configurable via env var `PROB_DAMPENING` (default 0.15).

**`ScenarioTemplates`** — loads `data/scenario_templates.json`, creates initial node set for new incidents.

**`RedisSubscriber`** — async background loop, listens on all 4 channels:
- `council.briefing` → persist to PostgreSQL only (does not affect probabilities)
- `sim.result` → persist sentiment data (future: feed back into probability weights)

### REST API

| Method | Path | Description | Consumer |
|---|---|---|---|
| GET | `/incidents` | All active incidents with current trees | ShadowBroker frontend, WIN_System |
| GET | `/incidents/{id}` | Full tree: nodes, probabilities, recent events | WIN_System (pre-briefing) |
| GET | `/incidents/{id}/history` | Probability timeline (for backtesting, charts) | Dashboard, analytics |
| POST | `/incidents` | Manually create incident `{ title, region, template }` | WIN_System, operator |
| POST | `/incidents/{id}/resolve` | Archive incident (active → archived) | WIN_System, operator |
| WS | `/ws/incidents` | Real-time probability updates stream | ShadowBroker frontend map, future meta-dashboard |

### File Structure

```
warren-core/
├── app/
│   ├── main.py                      # FastAPI app + lifespan (Redis + DB init)
│   ├── config.py
│   ├── services/
│   │   ├── incident_classifier.py
│   │   ├── probability_engine.py
│   │   ├── redis_subscriber.py
│   │   └── scenario_templates.py
│   ├── api/
│   │   ├── incidents.py             # REST routes
│   │   └── websocket.py
│   └── models/
│       └── db.py                    # SQLAlchemy models
├── data/
│   └── scenario_templates.json      # editable without code changes
├── migrations/                      # Alembic
└── pyproject.toml
```

---

## Integration Changes (Existing Systems)

### ShadowBroker — ~60 lines added

**`backend/services/data_fetcher.py`** (modify):
- After each significant feed fetch, call `_maybe_publish_alert(event_type, data)`
- Publishes to `osint.alert` only if `severity > 0.4` (noise filter)

**`backend/services/fetchers/severity_scorer.py`** (new):
- Rule-based severity per event type (no LLM cost here)
- `gps_jamming`: `min(count / 500, 1.0)`
- `carrier_movement`: `0.75 if underway else 0.3`
- `gdelt_spike`: `min(sigma / 4.0, 1.0)`
- `ukraine_alert`: `0.9` (always high)

### WIN_System — ~120 lines added

**`council_orchestrator.py`** (modify):
- Remove hardcoded event list and mock responses
- Add `listen_for_scenarios()` async loop subscribing to `scenario.updated`
- On each update: call `GET /incidents/{id}` on warren-core, select personas by region, run council with real LLM calls, publish `council.briefing`

**`agents/persona_selector.py`** (new):
- Maps `region + template` → subset of the 109 persona files
- Example: `Baltic + military_conflict` → `[putin, nato_sec, biden, dalio]`

### MiroFish — ~80 lines added

**`backend/app/services/simulation_manager.py`** (modify):
- Add `listen_for_briefings()` async loop subscribing to `council.briefing`
- On each briefing: call existing `simulation_config_generator.py` to auto-build config, run simulation, publish `sim.result` with `{ incident_id, sentiment_score, top_narratives, platform_breakdown }`

---

## Docker Compose Changes

Each sub-project currently has its own `docker-compose.yml`. This work requires creating a **new root-level `docker-compose.yml`** at `Warren Wayne/docker-compose.yml` that orchestrates all services together. The per-project files remain for standalone dev.

New services in root compose:
- `redis:7-alpine` — AOF persistence enabled, port 6379
- `postgres:16-alpine` — DB `warren_core`, credentials via env vars
- `warren-core` — depends on redis + postgres, port 9000
- `shadowbroker` — extended from `shadowbroker_analysis/docker-compose.yml`, adds `REDIS_URL` env
- `mirofish` — extended from `mirofish_analysis/docker-compose.yml`, adds `REDIS_URL` env
- `win-system` — new container for WIN_System (no existing compose), adds `REDIS_URL` + `WARREN_CORE_URL`

New volumes: `redis-data`, `pg-data`

New env vars required: `PG_PASSWORD`, `OPENAI_API_KEY` (already present in sub-project envs), `WARREN_CORE_URL=http://warren-core:9000`

---

## Error Handling

| Scenario | Behavior |
|---|---|
| Redis unavailable | warren-core retries with exponential backoff (max 30s); ShadowBroker buffers last 10 events in memory |
| PostgreSQL unavailable | warren-core continues with Redis-only state; queues DB writes for retry |
| LLM call fails (direction_score) | Default to `direction_score = 0.5` (neutral); log and continue |
| No active incident matches signal | Discard if severity < 0.6; create new if ≥ 0.6 |
| Probability sum drift | Re-normalize on every write (floating point safety) |

---

## Out of Scope (This Sub-project)

- Hybrid tree model (C) — dynamic branches created by WIN_System (sub-project 2)
- `sim.result` feeding back into probability weights (sub-project 2)
- Meta-dashboard / unified frontend (sub-project 5)
- Auth layer (sub-project 6)
- Backtesting pipeline (sub-project 5)
- council.watchlist flow (WIN→ShadowBroker priority targeting)

---

## Testing Approach

- Unit: `ProbabilityEngine` normalization, `IncidentClassifier` match logic, `SeverityScorer` rules
- Integration: Publish mock `osint.alert` to Redis → verify `scenario.updated` emitted with correct probability deltas
- End-to-end: Docker Compose up all services → inject GPS jamming event → verify full loop completes (ShadowBroker → warren-core → WIN_System council → MiroFish simulation)

---

## Expected Effort

| Component | Estimate |
|---|---|
| warren-core service (full) | 3–4 days |
| ShadowBroker integration | 0.5 days |
| WIN_System integration | 1–2 days |
| MiroFish integration | 1 day |
| Docker Compose + infra | 0.5 days |
| Tests | 1 day |
| **Total** | **~7–9 days** |
