from dataclasses import dataclass, field
from typing import Optional
import uuid


@dataclass
class AlertRule:
    """
    Represents a user-defined alert rule.

    Examples:
      - "Alert me when AAPL drops more than 3% in 5 days"
      - "Alert me when TSLA 14-day range exceeds $80"
      - "Alert me when GOOGL closes above $410"
    """
    symbol:     str
    rule_type:  str        # 'price_above', 'price_below', 'drop_pct', 'range_exceeds'
    threshold:  float      # the value to compare against
    window:     int = 14   # how many days to look back (for range/drop rules)
    id:         str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    triggered:  bool = False
    description: str = ""

    def __post_init__(self):
        valid_types = {'price_above', 'price_below', 'drop_pct', 'range_exceeds'}
        if self.rule_type not in valid_types:
            raise ValueError(f"rule_type must be one of {valid_types}")


class RuleStore:
    """In-memory store for alert rules. Phase 4 will persist these to a DB."""

    def __init__(self):
        self._rules: dict[str, AlertRule] = {}

    def add(self, rule: AlertRule) -> AlertRule:
        self._rules[rule.id] = rule
        print(f"  [RuleStore] Added rule {rule.id}: {rule.description}")
        return rule

    def get_for_symbol(self, symbol: str) -> list[AlertRule]:
        return [r for r in self._rules.values() if r.symbol == symbol]

    def get_all(self) -> list[AlertRule]:
        return list(self._rules.values())

    def mark_triggered(self, rule_id: str):
        if rule_id in self._rules:
            self._rules[rule_id].triggered = True