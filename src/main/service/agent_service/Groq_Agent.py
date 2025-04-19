import os
import json
import time
import logging
import random
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_community.utilities import SQLDatabase
from langchain.agents import create_sql_agent
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain_groq import ChatGroq
from langchain.tools import tool
from langgraph.prebuilt import tools_condition, ToolNode
from langchain_core.messages import SystemMessage, HumanMessage
from typing import Annotated
from typing_extensions import TypedDict

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment
logger.info("Initializing Groq Agent")
load_dotenv()
api_token_groq = os.getenv("grop_db_query_model_api_key") or os.getenv("chat_assistant_api_1")
db_api = os.getenv("db_info")

# LLM and DB setup
logger.info(f"Using Groq model: llama3-70b-8192")
llm = ChatGroq(api_key=api_token_groq, model_name="llama3-70b-8192", temperature=0.7)
db = SQLDatabase.from_uri(db_api)
toolkit = SQLDatabaseToolkit(db=db, llm=llm)
agent_executor = create_sql_agent(llm=llm, toolkit=toolkit, verbose=False)

# Define the state schema
class State(TypedDict):
    messages: Annotated[list, add_messages]
    final_result: dict

# Tool function: wraps the good chatbot's query logic
@tool
def query_database_tool(query: str) -> str:
    """Tool to query a SQL database and return result as a JSON string."""
    logger.info(f"Running SQL query from tool: {query[:50]}...")
    try:
        structured_input = [
            SystemMessage(content=(
                "You are a helpful assistant specialized in SQL queries. "
                "Generate an SQL query based on user input. Return JSON with keys: 'query', 'result', and 'message'. "
                "Always include 'id' and 'shopify_id' in your results if they exist."
            )),
            HumanMessage(content=query)
        ]
        response = agent_executor.invoke({"input": structured_input})
        output = response.get("output", "")
        logger.debug(f"Tool response: {output[:100]}")
        try:
            json.loads(output)  # Validate JSON
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

# Random product fallback
def get_random_product():
    """Fetch a random product from the database."""
    try:
        query = "SELECT id, shopify_id FROM products ORDER BY RANDOM() LIMIT 1"
        result = db.run(query)
        rows = json.loads(result) if result else []
        if rows:
            return {
                "query": query,
                "result": rows,
                "message": "No specific results found, here's a random product for you!"
            }
        return {
            "query": query,
            "result": [],
            "message": "No products available in the database."
        }
    except Exception as e:
        logger.error(f"Random product query failed: {str(e)}")
        return {
            "query": query,
            "result": [],
            "message": f"Error fetching random product: {str(e)}"
        }

tools = [query_database_tool]
llm_with_tools = llm.bind_tools(tools)

# Supervisor chatbot
def chatbot(state: State) -> State:
    logger.info("Supervisor chatbot activated")
    system_prompt = SystemMessage(content=(
        "You are a high-level assistant managing a shop's product search.\n"
        "Your tasks:\n"
        "1. Analyze the user's input to determine if it requires a product search (e.g., asking about products, prices, or inventory) or is a general question (e.g., store hours, policies).\n"
        "2. For product searches, use the query_database_tool.\n"
        "3. For general questions, answer directly without the tool.\n"
        "4. If no results are found from a product search, return a random product.\n"
        "5. Always return a dict with keys: 'query', 'result', 'message'.\n"
        "6. Include 'id' and 'shopify_id' in results if available.\n"
        "7. Format responses as friendly, customer-facing messages."
    ))

    messages = [system_prompt] + state["messages"]
    logger.debug(f"Processing {len(messages)} messages")

    try:
        last_user_message = messages[-1].content  # Access content attribute
        # Use LLM to classify the query
        classification_prompt = [
            SystemMessage(content=(
                "Analyze the following user input and determine if it is a product search (related to products, prices, inventory, etc.) or a general question (e.g., store hours, policies). "
                "Return a JSON object with a single key 'is_product_search' set to true or false."
            )),
            HumanMessage(content=last_user_message)
        ]
        classification_result = llm.invoke(classification_prompt)
        try:
            classification = json.loads(classification_result.content)
            needs_db_query = classification.get("is_product_search", False)
        except json.JSONDecodeError:
            logger.warning("Failed to parse classification result, defaulting to non-database query")
            needs_db_query = False

        if not needs_db_query:
            logger.info("Handling non-database query")
            response = llm.invoke(messages)
            output = response.content
            return {
                "messages": [response],  # Store as AIMessage
                "final_result": {
                    "query": "",
                    "result": [],
                    "message": output
                }
            }

        # Database query needed, rely on tool call
        result = llm_with_tools.invoke(messages)
        if hasattr(result, "tool_calls") and result.tool_calls:
            logger.debug("Tool call detected")
            return {
                "messages": [result],  # Store as AIMessage with tool_calls
                "final_result": state.get("final_result", {})
            }

        # Fallback if no tool call but database query was expected
        output = result.content
        try:
            parsed = json.loads(output)
        except json.JSONDecodeError:
            parsed = {
                "query": "",
                "result": [],
                "message": output
            }

        # Check if results are empty and fetch random product if needed
        if not parsed.get("result"):
            logger.info("No results found, fetching random product")
            parsed = get_random_product()

        return {
            "messages": [result],  # Store as AIMessage
            "final_result": parsed
        }

    except Exception as e:
        logger.error(f"Supervisor chatbot error: {str(e)}", exc_info=True)
        error_message = f"Sorry, something went wrong: {str(e)}"
        return {
            "messages": [HumanMessage(content=error_message)],  # Store as HumanMessage
            "final_result": {
                "query": "",
                "result": [],
                "message": error_message
            }
        }

# Build the graph
logger.debug("Constructing graph")
graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)
tool_node = ToolNode(tools=tools)
graph_builder.add_node("tools", tool_node)

graph_builder.add_edge(START, "chatbot")
graph_builder.add_conditional_edges("chatbot", tools_condition)
graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge("chatbot", END)

logger.info("Compiling the LangGraph")
graph = graph_builder.compile()

# Entrypoint function
def agent_calling(user_input: str):
    logger.info(f"Agent received input: {user_input[:50]}...")
    
    if user_input.lower() in ["exit", "quit", "q"]:
        logger.info("Exiting session")
        return "Goodbye!"

    try:
        logger.debug("Starting graph stream")
        final_output = {}
        for event in graph.stream({"messages": [HumanMessage(content=user_input)]}):
            for value in event.values():
                if "final_result" in value and value["final_result"]:
                    final_output = value["final_result"]
                    logger.debug(f"Captured final result: {str(final_output)[:100]}")
            time.sleep(0.1)  # Reduced throttle for smoother execution

        # Ensure consistent output format
        if not final_output:
            logger.warning("No valid output from graph, returning error")
            final_output = {
                "query": "",
                "result": [],
                "message": "No response generated."
            }

        # Validate output format
        required_keys = ["query", "result", "message"]
        for key in required_keys:
            if key not in final_output:
                final_output[key] = "" if key == "query" else [] if key == "result" else "Missing data"

        # Wrap the final output in the 'response' key
        response = {
            "response": {
                "message": final_output["message"],
                "query": final_output["query"],
                "result": final_output["result"]
            }
        }

        logger.debug(f"Returning data: {str(response)[:100]}")
        return response

    except Exception as e:
        logger.error(f"Error during graph execution: {str(e)}", exc_info=True)
        error_response = {
            "response": {
                "query": "",
                "result": [],
                "message": f"Execution error: {str(e)}"
            }
        }
        return error_response