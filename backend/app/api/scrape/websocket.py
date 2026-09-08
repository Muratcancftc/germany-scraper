from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(prefix="/ws", tags=["websocket"])

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, job_id: int):
        await websocket.accept()
        if job_id not in self.active_connections:
            self.active_connections[job_id] = []
        self.active_connections[job_id].append(websocket)

    def disconnect(self, websocket: WebSocket, job_id: int):
        self.active_connections.get(job_id, []).remove(websocket)
        if not self.active_connections.get(job_id):
            del self.active_connections[job_id]

    async def send_personal(self, message: dict, job_id: int):
        for connection in self.active_connections.get(job_id, []):
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()

@router.websocket("/jobs/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: int):
    await manager.connect(websocket, job_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, job_id)

async def broadcast_event(job_id: int, event: dict):
    await manager.send_personal(event, job_id)
