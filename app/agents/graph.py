from langgraph.graph import END, StateGraph

from app.agents.nodes import AgentNodes, choose_next_node
from app.agents.state import AgentState
from app.core.config import Settings


def build_agent_graph(settings: Settings, nodes: AgentNodes | None = None):
    agent_nodes = nodes or AgentNodes(settings)

    workflow = StateGraph(AgentState)
    workflow.add_node("Validator(input)", agent_nodes.validate_input)
    workflow.add_node("Planner", agent_nodes.plan)
    workflow.add_node("Retriever", agent_nodes.retrieve)
    workflow.add_node("Reasoner", agent_nodes.reason)
    workflow.add_node("Responder", agent_nodes.respond)
    workflow.add_node("Validator(output)", agent_nodes.validate_output)

    workflow.set_entry_point("Validator(input)")
    workflow.add_edge("Validator(input)", "Planner")
    workflow.add_conditional_edges(
        "Planner",
        choose_next_node,
        {
            "retrieve": "Retriever",
            "reason": "Reasoner",
        },
    )
    workflow.add_edge("Retriever", "Reasoner")
    workflow.add_edge("Reasoner", "Responder")
    workflow.add_edge("Responder", "Validator(output)")
    workflow.add_edge("Validator(output)", END)

    return workflow.compile()
