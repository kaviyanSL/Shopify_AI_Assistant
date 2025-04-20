import os
import json
import logging
import uuid
import asyncio
from redis.asyncio import Redis
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_community.utilities import SQLDatabase
from langchain.agents import create_sql_agent
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain_groq import ChatGroq
from langchain.tools import tool
from langgraph.prebuilt import tools_condition, ToolNode
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolCall
from typing import Annotated, Dict, Any
from typing_extensions import TypedDict

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment
logger.info("Initializing Groq Agent")
load_dotenv()
api_token_groq = os.getenv("grop_db_query_model_api_key") or os.getenv("chat_assistant_api_1")
db_api = os.getenv("db_info")
redis_url = os.getenv("REDIS_URL")

# Connect to Redis async client
redis_client = Redis.from_url(redis_url, decode_responses=True)

# LLM and DB setup
logger.info(f"Using Groq model: llama3-70b-8192")
llm_query = ChatGroq(api_key=api_token_groq, model_name="llama3-70b-8192", temperature=0.1)
llm = ChatGroq(api_key=api_token_groq, model_name="llama3-70b-8192", temperature=0.7)
db = SQLDatabase.from_uri(db_api)
toolkit = SQLDatabaseToolkit(db=db, llm=llm_query)
agent_executor = create_sql_agent(llm=llm_query, toolkit=toolkit, verbose=False)

class State(TypedDict):
    messages: Annotated[list, add_messages]
    final_result: dict

@tool
async def query_database_tool(query: str) -> str:
    """Tool to query a SQL database and return result as a JSON string."""
    logger.info(f"Running SQL query from tool: {query[:50]}...")
    try:
        structured_input = [
            SystemMessage(content=(
                "You are a helpful assistant specialized in generating SQL queries.\n"
                "Given a user input, return a JSON object with the keys: `query`, `result`, and `message`.\n"
                "Always include `id`, `shopify_id`, and `title` in your results if those fields exist in the database.\n"
                "Ensure output is valid JSON that can be parsed safely."
            )),
            HumanMessage(content=query)
        ]
        response = await agent_executor.ainvoke({"input": structured_input})
        output = response.get("output", "")
        logger.debug(f"Tool response: {output[:100]}")
        try:
            json.loads(output)
            return output
        except json.JSONDecodeError:
            logger.warning("Tool output is not valid JSON, wrapping it")
            return json.dumps({
                "query": "",
                "result": [],
                "message": output
            })
    except Exception as e:
        logger.error(f"Tool execution failed: {str(e)}", exc_info=True)
        return json.dumps({
            "query": "",
            "result": [],
            "message": f"Tool error: {str(e)}"
        })


tools = [query_database_tool]
llm_with_tools = llm.bind_tools(tools)

async def chatbot(state: State) -> State:
    logger.info("Supervisor chatbot activated")
    system_prompt = SystemMessage(content=(
                        "You are a high-level assistant for a product-focused shop chatbot.\n"
                        "Responsibilities:\n"
                        "1. Determine whether the user's message is a product-related query (e.g., asking about products, prices, inventory) or a general inquiry (e.g., store hours, policies).\n"
                        "2. Try to find any semantic similarities in the user's message to product-related queries.\n"
                        "3. If the semantic similarities in the user's message is product-related, use the `query_database_tool` to fetch relevant products.\n"
                        "4. If it's product-related, prioritize using the `query_database_tool`.\n"
                        "5. If `query_database_tool` returns no results, just query again for 4 random product`.\n"
                        "6. If the input is a general inquiry, answer it directly, but still return a random product.\n"
                        "7. Always return a JSON object with: `query`, `result`, and `message`.\n"
                        "8. Include `id`, `shopify_id`, and `title` in results if available.\n"
                        "9. Format all replies as clear, friendly messages for customers.\n"
                    ))

    messages = [system_prompt] + state["messages"]
    logger.debug(f"Processing {len(messages)} messages")

    try:
        result = await llm_with_tools.ainvoke(messages)
        if hasattr(result, "tool_calls") and result.tool_calls:
            return {
                "messages": [AIMessage(content=result.content, tool_calls=result.tool_calls)],
                "final_result": state.get("final_result", {})
            }

        output = result.content
        try:
            parsed = json.loads(output)
        except json.JSONDecodeError:
            parsed = {
                "query": "",
                "result": [],
                "message": output
            }

        return {
            "messages": [AIMessage(content=output)],
            "final_result": parsed
        }

    except Exception as e:
        logger.error(f"Supervisor chatbot error: {str(e)}", exc_info=True)
        return {
            "messages": [AIMessage(content=f"Sorry, something went wrong: {str(e)}")],
            "final_result": {
                "query": "",
                "result": [],
                "message": f"Sorry, something went wrong: {str(e)}"
            }
        }

logger.debug("Constructing graph")
graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)
tool_node = ToolNode(tools=tools)
graph_builder.add_node("tools", tool_node)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_conditional_edges("chatbot", tools_condition)
graph_builder.add_edge("tools", "chatbot")

logger.info("Compiling the LangGraph")
graph = graph_builder.compile()

# Entrypoint function with UUID + Redis
async def agent_calling(user_input: str, session_id: str = None) -> Dict[str, Any]:
    if not session_id:
        session_id = str(uuid.uuid4())
        logger.info(f"New session started with UUID: {session_id}")

    logger.info(f"[{session_id}] Received input: {user_input[:50]}")

    # Exit and clean session memory
    if user_input.lower() in ["exit", "quit", "q"]:
        await redis_client.delete(session_id)
        logger.info(f"[{session_id}] Session ended and memory cleared")
        return {
            "session_id": session_id,
            "response": {
                "message": "Session ended. Goodbye!",
                "query": "",
                "result": []
            }
        }

    # Load memory
    history_json = await redis_client.get(session_id)
    history = json.loads(history_json) if history_json else []

    # Append new user message
    history.append(HumanMessage(content=user_input))

    try:
        final_output = {}
        async for event in graph.astream({"messages": history}):
            for value in event.values():
                if "final_result" in value and value["final_result"]:
                    final_output = value["final_result"]
                    history += value["messages"]

        # Save back to Redis
        serialized_history = []
        for msg in history:
            if isinstance(msg, HumanMessage):
                serialized_history.append({"type": "human", "content": msg.content})
            elif isinstance(msg, AIMessage):
                # Handle tool calls if they exist
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    tool_calls_data = [
                        {"name": t.name, "args": t.args, "id": t.id} 
                        for t in msg.tool_calls
                    ]
                    serialized_history.append({
                        "type": "ai",
                        "content": msg.content,
                        "tool_calls": tool_calls_data
                    })
                else:
                    serialized_history.append({"type": "ai", "content": msg.content})
            elif isinstance(msg, SystemMessage):
                serialized_history.append({"type": "system", "content": msg.content})
            elif isinstance(msg, dict) and "type" in msg and "content" in msg:
                # Already in the right format
                serialized_history.append(msg)
            else:
                # Handle other message types
                serialized_history.append({"type": "unknown", "content": str(msg)})

        # Save history to Redis
        await redis_client.set(session_id, json.dumps(serialized_history))

        # Fallback
        if not final_output:
            final_output = {
                "query": "",
                "result": [],
                "message": "No response generated."
            }

        return {
            "session_id": session_id,
            "response": {
                "message": final_output["message"],
                "query": final_output["query"],
                "result": final_output["result"]
            }
        }

    except Exception as e:
        logger.error(f"[{session_id}] Error in graph execution: {str(e)}", exc_info=True)
        return {
            "session_id": session_id,
            "response": {
                "query": "",
                "result": [],
                "message": f"Execution error: {str(e)}"
            }
        }