from typing import Dict, Any

class WorkingMemory:
    def __init__(self):
        self._state: Dict[str, Any] = {}

    def set(self, key: str, value: Any):
        self._state[key] = value

    def get(self, key: str) -> Any:
        return self._state.get(key)
