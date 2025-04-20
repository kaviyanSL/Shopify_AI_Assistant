from src.main.service.agent_service.StateClass import State
from src.main.service.agent_service.ChatBotService import chatbot
from src.main.service.agent_service import AgentToolsService as tool


from langgraph.graph import StateGraph, START
from langgraph.prebuilt import tools_condition, ToolNode

import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)



def graph_builder():
    """Builds and returns an async-compatible LangGraph for the agent"""
    logger.debug("Constructing async graph")

    tools = [tool.query_database_tool]
    graph_builder = StateGraph(State)
    graph_builder.add_node("chatbot", chatbot)
    tool_node = ToolNode(tools=tools)
    graph_builder.add_node("tools", tool_node)
    graph_builder.add_edge(START, "chatbot")
    graph_builder.add_conditional_edges("chatbot", tools_condition)
    graph_builder.add_edge("tools", "chatbot")

    logger.info("Compiling the async LangGraph")
    # Compile as async graph
    graph = graph_builder.compile()
    return graph