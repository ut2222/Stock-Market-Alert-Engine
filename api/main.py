from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import tickers, alerts, ws

app = FastAPI(
    title="Stock Alert Engine",
    description="Real-time stock analysis with DSA-powered indicators and alerts",
    version="1.0.0"
)

# CORS — allows the React dashboard (running on port 3000)
# to talk to this API (running on port 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route groups
app.include_router(tickers.router, prefix="/api")
app.include_router(alerts.router,  prefix="/api")
app.include_router(ws.router)

@app.get("/")
def root():
    return {
        "message": "Stock Alert Engine API",
        "docs":    "http://localhost:8000/docs",
        "endpoints": [
            "GET  /api/tickers",
            "GET  /api/tickers/{symbol}/history",
            "GET  /api/tickers/{symbol}/latest",
            "GET  /api/tickers/{symbol}/stats",
            "GET  /api/alerts",
            "POST /api/alerts",
            "POST /api/alerts/evaluate",
            "DELETE /api/alerts/{rule_id}"
        ]
    }




