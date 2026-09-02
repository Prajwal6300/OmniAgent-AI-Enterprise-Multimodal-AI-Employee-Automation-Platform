from typing import Dict, Any
from agents.graph.state import AgentGraphState
from agents.supervisor.agent import SupervisorAgent
from agents.vision.agent import VisionAgent
from agents.document.agent import DocumentAgent
from agents.rag.agent import RAGAgent
from agents.database.agent import DatabaseAgent
from agents.reasoning.agent import ReasoningAgent
from agents.action.agent import ActionAgent

supervisor = SupervisorAgent()
vision_agent = VisionAgent()
document_agent = DocumentAgent()
rag_agent = RAGAgent()
database_agent = DatabaseAgent()
reasoning_agent = ReasoningAgent()
action_agent = ActionAgent()

async def supervisor_node(state: AgentGraphState) -> Dict[str, Any]:
    decision = await supervisor.evaluate_step(state)
    return {
        "next_step": decision.next_agent,
        "active_agent": "supervisor",
        "intermediate_steps": [{"agent": "supervisor", "output": decision.dict()}]
    }

async def vision_node(state: AgentGraphState) -> Dict[str, Any]:
    result = await vision_agent.process(state)
    return {
        "intermediate_steps": [{"agent": "vision", "output": result}],
        "next_step": "supervisor"
    }

async def document_node(state: AgentGraphState) -> Dict[str, Any]:
    result = await document_agent.process(state)
    return {
        "intermediate_steps": [{"agent": "document", "output": result}],
        "next_step": "supervisor"
    }

async def rag_node(state: AgentGraphState) -> Dict[str, Any]:
    result = await rag_agent.process(state)
    return {
        "intermediate_steps": [{"agent": "rag", "output": result}],
        "next_step": "supervisor"
    }

async def database_node(state: AgentGraphState) -> Dict[str, Any]:
    result = await database_agent.process(state)
    return {
        "intermediate_steps": [{"agent": "database", "output": result}],
        "next_step": "supervisor"
    }

async def reasoning_node(state: AgentGraphState) -> Dict[str, Any]:
    result = await reasoning_agent.process(state)
    return {
        "intermediate_steps": [{"agent": "reasoning", "output": result}],
        "next_step": "supervisor"
    }

async def action_node(state: AgentGraphState) -> Dict[str, Any]:
    result = await action_agent.process(state)
    return {
        "intermediate_steps": [{"agent": "action", "output": result}],
        "next_step": "supervisor"
    }
