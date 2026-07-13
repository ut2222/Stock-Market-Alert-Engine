from datetime import datetime


class AlertDispatcher:
    """
    Handles fired alerts — prints to console now,
    will send email/webhook in a later phase.
    """

    def __init__(self):
        self.history: list[dict] = []

    def dispatch(self, alerts: list[dict]) -> None:
        for alert in alerts:
            self.history.append({**alert, "dispatched_at": datetime.utcnow().isoformat()})
            self._print_alert(alert)

    def _print_alert(self, alert: dict) -> None:
        border = "=" * 56
        print(f"\n{border}")
        print(f"  ALERT FIRED [{alert['rule_type'].upper()}]")
        print(f"  {alert['message']}")
        print(f"  Rule ID: {alert['rule_id']}  |  Date: {alert['date']}")
        print(f"{border}")

    def summary(self) -> None:
        print(f"\nTotal alerts dispatched: {len(self.history)}")
        for a in self.history:
            print(f"  [{a['rule_type']:16s}] {a['symbol']}  —  {a['message'][:60]}")