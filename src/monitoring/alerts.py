from __future__ import annotations

import json
import os
from collections.abc import Iterable
from datetime import datetime
from types import ModuleType

try:
    import urllib.request as urlreq
except Exception:  # pragma: no cover
    urlreq = None  # type: ignore[assignment]


def _now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")


def format_issues(issues: Iterable[tuple[str, float, float]]) -> str:
    lines = ["Monitoring threshold breaches:"]
    for key, val, th in issues:
        lines.append(f"- {key}: value={val:.6f}, threshold={th}")
    return "\n".join(lines)


def to_console(message: str) -> None:
    print(f"[ALERT {_now()}] {message}")


def to_file(message: str, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"[ALERT {_now()}]\n{message}\n\n")


def to_slack(message: str, webhook_url: str) -> None:
    if not urlreq or not webhook_url:
        return
    data = json.dumps({"text": message}).encode("utf-8")
    req = urlreq.Request(webhook_url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urlreq.urlopen(req, timeout=10) as _:
            pass
    except Exception:
        # Fail silently to avoid crashing monitoring
        return
