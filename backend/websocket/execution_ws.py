import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from services.execution_service import ExecutionService

router = APIRouter()
service = ExecutionService()


@router.websocket("/ws/execute")
async def execution_websocket(websocket: WebSocket):
    await websocket.accept()
    try:
        data = await websocket.receive_text()
        payload = json.loads(data)

        async def send(msg: dict):
            await websocket.send_text(json.dumps(msg))

        await service.stream_steps(
            transaction_type=payload.get("transaction_type", "trade_in_upgrade"),
            customer_id=payload.get("customer_id", ""),
            params=payload.get("params", {}),
            send_fn=send,
        )
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_text(json.dumps({"type": "error", "message": str(e)}))
        except Exception:
            pass
