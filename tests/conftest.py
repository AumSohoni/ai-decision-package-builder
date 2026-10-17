import json
from pathlib import Path

CHECKLIST_PATH = Path(__file__).parent.parent / "data" / "checklist.json"
PAST_PATH = Path(__file__).parent.parent / "data" / "past_decisions.json"


def pytest_sessionstart(session):
    Path("out").mkdir(exist_ok=True)
