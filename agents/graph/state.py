from typing import Annotated, Sequence, TypedDict, Optional, Dict, Any, List
import operator

try:
    from langchain_core.messages import BaseMessage
except ImportError:
    class BaseMessage:  # type: ignore
        content: str = ""
        type: str = "message"

class AgentGraphState(TypedDict):
    messages: Annotated[Sequence[Any], operator.add]
    next_step: Optional[str]
    active_agent: Optional[str]
    task_goal: str
    intermediate_steps: Annotated[List[Dict[str, Any]], operator.add]
    approval_required: bool
    approval_payload: Optional[Dict[str, Any]]
    final_response: Optional[str]
