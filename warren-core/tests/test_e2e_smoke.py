"""
Requires: docker compose up redis postgres warren-core
Run with: pytest tests/test_e2e_smoke.py -v -m e2e
"""
import json
import time

import httpx
import pytest
import redis


@pytest.mark.e2e
def test_warren_core_health():
    resp = httpx.get("http://localhost:9000/health", timeout=5)
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.e2e
def test_osint_alert_creates_incident():
    r = redis.Redis(host="localhost", port=6379, decode_responses=True)
    r.publish("osint.alert", json.dumps({
        "type": "gps_jamming",
        "severity": 0.85,
        "region": "TestRegionSmoke",
        "source": "test",
        "payload": {"count": 450},
    }))
    time.sleep(2)  # allow warren-core to process

    resp = httpx.get("http://localhost:9000/incidents", timeout=5)
    assert resp.status_code == 200
    incidents = resp.json()
    assert any("TestRegionSmoke" in str(inc) for inc in incidents)
