import pytest
from agents.graph.routing import route_next_node

def test_agent_routing_logic():
    state = {"next_step": "vision"}
    assert route_next_node(state) == "vision"
    
    state_end = {"next_step": "unknown"}
    assert route_next_node(state_end) == "end"
