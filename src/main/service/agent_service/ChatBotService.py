from src.main.service.agent_service.StateClass import State
from src.main.service.agent_service import AgentToolsService as tool
from src.main.service.agent_service.LLMsModelService import LLMsModelService 

import json
import re

from langchain_core.messages import SystemMessage, AIMessage

import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.info("Initializing Groq Agent")

model = LLMsModelService()
# tools = [tool.query_database_tool]
# llm_with_tools = model.llm.bind_tools(tools)

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
                        "7. When responding ONLY include a simple friendly customer message, the exact SQL query used, and the product results.\n"
                        "8. DO NOT include explanations of your process or reasoning.\n"
                        "9. Format your response as follows:\n"
                        "```json\n"
                        "{\n"
                        "  \"message\": \"[friendly customer message only]\",\n"
                        "  \"query\": \"[exact SQL query used]\",\n"
                        "  \"result\": [[id, shopify_id, title], [id, shopify_id, title], ...]\n"
                        "}\n"
                        "```\n"
                    ))

    messages = [system_prompt] + state["messages"]
    logger.debug(f"Processing {len(messages)} messages")

    try:
        result = await model.ainvoke_llm(messages)
        if hasattr(result, "tool_calls") and result.tool_calls:
            return {
                "messages": [AIMessage(content=result.content, tool_calls=result.tool_calls)],
                "final_result": state.get("final_result", {})
            }

        output = result.content
        
        # Try to extract JSON from the response
        try:
            # Check if response contains JSON in code blocks
            json_match = re.search(r'```(?:json)?\s*({[\s\S]*?})\s*```', output)
            if json_match:
                parsed = json.loads(json_match.group(1))
            else:
                # Try direct JSON parsing
                parsed = json.loads(output)
                
            # Ensure result is in the correct format (list of lists)
            if "result" in parsed and parsed["result"]:
                # If result is a list of dicts, convert to list of lists
                if isinstance(parsed["result"], list) and isinstance(parsed["result"][0], dict):
                    parsed["result"] = [
                        [item.get("id", ""), item.get("shopify_id", ""), item.get("title", "")]
                        for item in parsed["result"]
                    ]
            else:
                parsed["result"] = []
                
        except (json.JSONDecodeError, AttributeError):
            logger.warning("Failed to parse JSON from model response")
            parsed = {
                "query": "",
                "result": [],
                "message": "I'm sorry, but I couldn't find any specific products matching your request."
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

