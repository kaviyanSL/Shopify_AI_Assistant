import json
import logging
import uuid
import asyncio
import re
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from src.main.service.agent_service.RedisService import RediceService
from src.main.service.agent_service.GraphService import graph_builder


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
redis = RediceService()


async def agent_calling_service(user_input: str, session_id: str = None):
    """Asynchronous agent service that processes user input and maintains session state"""
    graph = graph_builder()
    if not session_id:
        session_id = str(uuid.uuid4())
        logger.info(f"New session started with UUID: {session_id}")

    logger.info(f"[{session_id}] Received input: {user_input[:50]}")

    # Exit and clean session memory
    if user_input.lower() in ["exit", "quit", "q"]:
        await redis.delete(session_id)
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
    history_json = await redis.get(session_id)
    history = json.loads(history_json) if history_json else []

    # Append new user message
    history.append(HumanMessage(content=user_input))

    try:
        final_output = {}
        async for event in graph.astream({"messages": history}):
            for value in event.values():
                if "final_result" in value:
                    final_output = value["final_result"]
                    history += value["messages"]

        # Save back to Redis
        serialized_history = []
        for msg in history:
            if isinstance(msg, HumanMessage):
                serialized_history.append({"type": "human", "content": msg.content})
            elif isinstance(msg, AIMessage):
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
                serialized_history.append(msg)
            else:
                serialized_history.append({"type": "unknown", "content": str(msg)})

        # Save history to Redis
        await redis.set(session_id, json.dumps(serialized_history))

        # Ensure the final output is properly formatted
        if not final_output:
            final_output = {
                "query": "",
                "result": [],
                "message": "No response generated."
            }
        
        # Process result to ensure correct format
        if "result" in final_output and final_output["result"]:
            # Convert dict format to list format if needed
            if isinstance(final_output["result"], list):
                if isinstance(final_output["result"][0], dict):
                    final_output["result"] = [
                        [item.get("id", ""), item.get("shopify_id", ""), item.get("title", "")]
                        for item in final_output["result"]
                    ]
        
        # Extract actual user message if embedded in complex response
        if "message" in final_output and isinstance(final_output["message"], str):
            # If message appears to contain a JSON structure explanation, try to extract the actual message
            message = final_output["message"]
            json_match = re.search(r'```(?:json)?\s*({[\s\S]*?})\s*```', message)
            if json_match:
                try:
                    json_part = json.loads(json_match.group(1))
                    if "message" in json_part:
                        final_output["message"] = json_part["message"]
                except json.JSONDecodeError:
                    # Keep original message if parsing fails
                    pass

        return {
            "session_id": session_id,
            "response": {
                "message": final_output.get("message", ""),
                "query": final_output.get("query", ""),
                "result": final_output.get("result", [])
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
