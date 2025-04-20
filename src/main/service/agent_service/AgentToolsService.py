import json
import logging
from langchain.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
from src.main.service.agent_service.LLMsModelService import LLMsModelService


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
models = LLMsModelService()

logger.info("Initializing Tools")


logger.info(f"Using Groq model: llama3-70b-8192")
llm_query = models.llm_query
db = models.db
toolkit = models.toolkit
agent_executor = models.agent_executor


@tool
async def query_database_tool(query: str) -> str:
    """Tool to query a SQL database and return result as a JSON string."""
    logger.info(f"Running SQL query from tool: {query[:50]}...")
    try:
        structured_input = [
            SystemMessage(content=(
                "You are a helpful assistant specialized in generating SQL queries.\n"
                "IMPORTANT : FIND AS MANY AS SIMILAR KEYWORD FOR WHERE CLAUSE BECAUSE YOU MUST RETURN THE CUSTOMER QUERY-RELEVENT ITEMS"
                "Given a user input, return a JSON object with the keys: `query`, `result`, and `message`.\n"
                "Always include `id`, `shopify_id`, and `title` in your results if those fields exist in the database.\n"
                "Format the `result` as a list of lists, where each inner list contains [id, shopify_id, title] from products table.\n"
                "Example format: {\"query\": \"SELECT...\", \"result\": [[1, 123, \"Product A\"], [2, 456, \"Product B\"]], \"message\": \"...\"}\n"
                "IMPORTANT: MUST RETURN THE EXACT ID AND SHOPIFY_ID from the PRODUCT TABLE. THEY SHOULD THE REAL MATCH FOR THE PRODUCT YOU RETURN.\n"
                "Ensure output is valid JSON that can be parsed safely."
                "IMPORTANT: DO NOT use LIMIT in your SQL queries. Return ALL products that match the criteria.\n"
                "IMPORTANT: YOU MUST RETURN SOMTHING AT LEAST"
            )),
            HumanMessage(content=query)
        ]
        response = await models.ainvoke_agent({"input": structured_input})
        output = response.get("output", "")
        logger.debug(f"Tool response: {output[:100]}")
        
        # Try to parse the JSON response and ensure correct format
        try:
            parsed = json.loads(output)
            
            # Convert result to list of lists if it's a list of dicts
            if "result" in parsed and isinstance(parsed["result"], list):
                if parsed["result"] and isinstance(parsed["result"][0], dict):
                    parsed["result"] = [
                        [item.get("id", ""), item.get("shopify_id", ""), item.get("title", "")]
                        for item in parsed["result"]
                    ]
            
            return json.dumps(parsed)
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

@tool
async def get_random_product(query: str = "") -> dict:
    """Fetch a random product from the database."""
    try:
        query = """
                    SELECT id, shopify_id, TITLE 
                    FROM products 
                    ORDER BY RAND() 
                    LIMIT 4 
                """

        result = db.run(query)
        rows = result if result else []
        
        # Format the result as a list of lists [id, shopify_id, title]
        formatted_results = []
        for row in rows:
            if isinstance(row, dict):
                formatted_results.append([
                    row.get("id", ""), 
                    row.get("shopify_id", ""), 
                    row.get("title", "")
                ])
            elif isinstance(row, (list, tuple)):
                formatted_results.append(list(row))
        
        return {
            "query": query,
            "result": formatted_results,
            "message": "No specific results found, here are some random products you might be interested in!"
        }
    except Exception as e:
        logger.error(f"Random product query failed: {str(e)}")
        return {
            "query": query,
            "result": [],
            "message": f"Error fetching random product: {str(e)}"
        }