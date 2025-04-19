import os
import json
import time
import logging
import ast
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_community.utilities import SQLDatabase
from langchain.agents import create_sql_agent
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain_groq import ChatGroq
from typing import Annotated
from typing_extensions import TypedDict

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.info("Initializing Groq Query Agent")
load_dotenv()
api_token_groq = os.getenv("grop_db_query_model_api_key")
db_api = os.getenv("db_info")

logger.info("Connecting to database")
db = SQLDatabase.from_uri(db_api)
logger.info(f"Using Groq model: llama3-70b-8192")
llm = ChatGroq(api_key=api_token_groq, model_name="llama3-70b-8192", temperature=0.7)
# llm = ChatGroq(api_key=api_token_groq, model_name="llama3-8b-8192", temperature=0.)

logger.debug("Setting up SQL toolkit and agent")
toolkit = SQLDatabaseToolkit(db=db, llm=llm)
agent_executor = create_sql_agent(llm=llm, toolkit=toolkit, verbose=False)


class State(TypedDict):
    messages: Annotated[list, add_messages]
    final_result: dict

logger.debug("Initializing StateGraph")
graph_builder = StateGraph(State)

def chatbot(state: State) -> State:
    logger.info("Processing SQL query request")
    system_prompt = {
        "role": "system",
        "content": (
            "You are a helpful assistant specialized in SQL database queries. "
            "Your task:\n"
            "1. Generate a valid SQL query from the user's request.\n"
            "2. Execute the query using the database.\n"
            "3. Return a dictionary with keys: 'query', 'result', and 'message'."
            "4. remmember that you must return the id and shopify_id for each result"
        )
    }

    messages = [system_prompt] + state["messages"]
    logger.debug(f"Processing messages count: {len(messages)}")

    try:
        logger.debug("Invoking agent executor")
        result = agent_executor.invoke({"input": messages})
        output = result.get("output", "")
        logger.info("Agent execution completed successfully")

        try:
            parsed = json.loads(output)
            logger.debug("Successfully parsed JSON output")
        except Exception as e:
            logger.warning(f"Failed to parse JSON output: {str(e)}")
            parsed = {
                "query": "",
                "result": [],
                "message": output
            }

        return {
            "messages": [{"role": "assistant", "content": output}],  # Format as proper message
            "final_result": parsed
        }

    except Exception as e:
        logger.error(f"Error in chatbot processing: {str(e)}", exc_info=True)
        return {
            "messages": [{"role": "assistant", "content": f"Agent error: {str(e)}"}],  # Format as proper message
            "final_result": {
                "query": "",
                "result": [],
                "message": f"Agent error: {str(e)}"
            }
        }

logger.debug("Adding nodes and edges to graph")
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)
logger.info("Compiling agent graph")
graph = graph_builder.compile()


def agent_calling_query(user_input: str):
    logger.info(f"Query agent called with input: {user_input[:50]}...")
    
    if user_input.lower() in ["exit", "quit", "q"]:
        logger.info("User requested exit")
        return "Goodbye!"

    try:
        logger.debug("Streaming graph execution")
        final_output = {}
        for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
            for value in event.values():
                if "final_result" in value:
                    final_output = value["final_result"]
                    logger.debug(f"Received final result: {str(final_output)[:100]}...")
            time.sleep(1)  # Throttle each 

        logger.info("Processing final output")
        data_dict = ast.literal_eval(final_output['message'])
        logger.debug(f"Returning data dictionary with {len(data_dict) if isinstance(data_dict, dict) else 'non-dict'} entries")
        return data_dict

    except Exception as e:
        logger.error(f"Error in agent execution: {str(e)}", exc_info=True)
        return json.dumps({
            "query": "",
            "result": [],
            "message": f"Error: {str(e)}"
        }, indent=2)


