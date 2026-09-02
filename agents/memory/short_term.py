from typing import List, Dict, Any

class ShortTermMemory:
    def __init__(self):
        self._history: List[Dict[str, Any]] = []

    def append(self, item: Dict[str, Any]):
        self._history.append(item)

    def get_context(self) -> List[Dict[str, Any]]:
        return self._history[-10:]
