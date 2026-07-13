from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from alert_engine.rule_store import RuleStore, AlertRule
from alert_engine.evaluator import AlertEvaluator
from alert_engine.dispatcher import AlertDispatcher
import json
import os

router = APIRouter()
CACHE_FILE = "historical_cache.json"

# In-memory store for this session
# Phase 5 will replace this with a database
_store = RuleStore()


class CreateRuleRequest(BaseModel):
    """Shape of the JSON body when creating a new alert rule."""
    symbol:     str
    rule_type:  str
    threshold:  float
    window:     int = 14
    description: str = ""


@router.get("/alerts")
def get_all_rules():
    """Return all registered alert rules."""
    rules = _store.get_all()
    return {
        "count": len(rules),
        "rules": [
            {
                "id":          r.id,
                "symbol":      r.symbol,
                "rule_type":   r.rule_type,
                "threshold":   r.threshold,
                "window":      r.window,
                "triggered":   r.triggered,
                "description": r.description
            }
            for r in rules
        ]
    }


@router.post("/alerts")
def create_rule(body: CreateRuleRequest):
    """
    Create a new alert rule.
    Example body:
    {
        "symbol": "AAPL",
        "rule_type": "price_above",
        "threshold": 320.0,
        "description": "AAPL breaks $320"
    }
    """
    try:
        rule = AlertRule(
            symbol=      body.symbol.upper(),
            rule_type=   body.rule_type,
            threshold=   body.threshold,
            window=      body.window,
            description= body.description
        )
        _store.add(rule)
        return {"message": "Rule created", "rule_id": rule.id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/alerts/evaluate")
def evaluate_rules():
    """
    Evaluate all rules against the latest cached data.
    Returns any alerts that fired.
    """
    if not os.path.exists(CACHE_FILE):
        raise HTTPException(status_code=400, detail="No cached data found. Run main.py first.")

    with open(CACHE_FILE, "r") as f:
        historical = json.load(f)

    evaluator  = AlertEvaluator(_store)
    dispatcher = AlertDispatcher()
    all_fired  = []

    for symbol, bars in historical.items():
        bars_oldest_first = list(reversed(bars))
        fired = evaluator.evaluate(symbol, bars_oldest_first)
        dispatcher.dispatch(fired)
        all_fired.extend(fired)

    return {
        "alerts_fired": len(all_fired),
        "alerts": all_fired
    }


@router.delete("/alerts/{rule_id}")
def delete_rule(rule_id: str):
    """Delete an alert rule by ID."""
    rules = _store.get_all()
    ids   = [r.id for r in rules]

    if rule_id not in ids:
        raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found.")

    del _store._rules[rule_id]
    return {"message": f"Rule {rule_id} deleted."}