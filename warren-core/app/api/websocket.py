# warren-core/app/api/websocket.py
import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()
_connections: list[WebSocket] = []


@router.websocket("/ws/incidents")
async def ws_incidents(websocket: WebSocket):
    await websocket.accept()
    _connections.append(websocket)
    try:
        while True:
            await asyncio.sleep(30)
            await websocket.send_text(json.dumps({"type": "ping"}))
    except WebSocketDisconnect:
        if websocket in _connections:
            _connections.remove(websocket)


async def broadcast(data: dict) -> None:
    dead = []
    msg = json.dumps(data)
    for ws in list(_connections):
        try:
            await ws.send_text(msg)
        except Exception:
            dead.append(ws)
    for ws in dead:
        if ws in _connections:
            _connections.remove(ws)
