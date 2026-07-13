import asyncio
import json
import random
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from datetime import datetime

router = APIRouter()


class ConnectionManager:
    """
    Manages all active WebSocket connections.

    Why a manager class? When multiple browser tabs connect,
    we need to track all of them and broadcast to every one.
    This is the fan-out pattern used in chat systems too.
    """

    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)
        print(f"[WS] Client connected. Total: {len(self.active)}")

    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)
        print(f"[WS] Client disconnected. Total: {len(self.active)}")

    async def broadcast(self, message: dict):
        """Send a message to every connected client."""
        dead = []
        for ws in self.active:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        # Clean up dead connections
        for ws in dead:
            self.active.remove(ws)


manager = ConnectionManager()


def get_simulated_tick(symbol: str, base_price: float) -> dict:
    """
    Simulate a price tick by adding small random movement.
    We use this because the free API tier doesn't support
    real-time streaming — in production this would be replaced
    by a Kafka consumer reading real ticks.

    The movement is normally distributed around 0 —
    equally likely to go up or down, small steps.
    """
    change_pct = random.gauss(0, 0.001)   # 0.1% std deviation
    new_price  = round(base_price * (1 + change_pct), 2)
    return {
        "symbol":    symbol,
        "price":     new_price,
        "change":    round(new_price - base_price, 2),
        "change_pct": round(change_pct * 100, 4),
        "timestamp": datetime.utcnow().isoformat(),
    }


# Base prices loaded from cache — updated as ticks come in
_last_prices: dict[str, float] = {}


def load_base_prices():
    """Load the latest closing prices from cache as starting points."""
    try:
        with open("historical_cache.json", "r") as f:
            cache = json.load(f)
        for symbol, bars in cache.items():
            _last_prices[symbol] = bars[0]["close"]  # newest first
        print(f"[WS] Loaded base prices: {_last_prices}")
    except Exception as e:
        print(f"[WS] Could not load base prices: {e}")
        _last_prices.update({"AAPL": 308.82, "TSLA": 426.01, "GOOGL": 382.97})


load_base_prices()


@router.websocket("/ws/live")
async def websocket_live(websocket: WebSocket):
    """
    WebSocket endpoint — connects a client and streams
    simulated price ticks every second until disconnected.

    Connect from browser with:
    new WebSocket("ws://localhost:8000/ws/live")
    """
    await manager.connect(websocket)
    try:
        while True:
            # Generate a tick for each symbol
            ticks = []
            for symbol, base in _last_prices.items():
                tick = get_simulated_tick(symbol, base)
                _last_prices[symbol] = tick["price"]  # update base for next tick
                ticks.append(tick)

            # Broadcast to ALL connected clients simultaneously
            await manager.broadcast({
                "type":      "price_update",
                "ticks":     ticks,
                "timestamp": datetime.utcnow().isoformat()
            })

            await asyncio.sleep(1)  # push update every second

    except WebSocketDisconnect:
        manager.disconnect(websocket)