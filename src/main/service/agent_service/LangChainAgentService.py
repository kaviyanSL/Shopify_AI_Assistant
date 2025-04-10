import re
import logging
from langchain.agents import Tool, initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from langchain.schema.messages import SystemMessage
from src.main.service.agent_service.AgentToolsService import get_product_types, find_products_flexible
from src.main.service.agent_service.QwenChatModelWrapperService import QwenChatModel
from src.main.service.TextPreprocessingService import TextPreprocessingService

class LangChainAgentService:
    def __init__(self):
        llm = QwenChatModel()

        tools = [
            Tool.from_function(
                get_product_types,
                name="GetProductTypes",
                description="Fetches the available product types."
            ),
            Tool.from_function(
                find_products_flexible,
                name="FindProductsFlexible",
                description="Finds products based on flexible search criteria. If no exact matches are found, it will return the closest matches."
            )
        ]

        memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

        self.agent = initialize_agent(
            tools=tools,
            llm=llm,
            memory=memory,
            agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
            verbose=True,
            handle_parsing_errors=True
        )

        self.agent.agent.llm_chain.prompt.messages.insert(0, SystemMessage(
            content="""You are a helpful shopping assistant. If a user provides a vague query like 
            'I need a gift' or 'something for a birthday', suggest some suitable products, 
            then ask a follow-up question to gather more details like price range or product type. 
            Always return at least one product, even if the match is not exact."""
        ))

        self.text_preprocessor = TextPreprocessingService()

    def run(self, user_prompt: str):
        # Correct spelling in the user query
        corrected_prompt = str(self.text_preprocessor.prompt_spell_correction(user_prompt))
        logging.info(f"Corrected user prompt: {corrected_prompt}")

        # Pass the corrected prompt to the agent
        agent_output = self.agent.run(corrected_prompt)
        return self.process_agent_response(agent_output)

    def process_agent_response(self, agent_output) -> dict:
        if isinstance(agent_output, str):
            action_input = agent_output
            agent_output = {"action": "Final Answer", "action_input": action_input}
        else:
            action_input = agent_output.get("action_input", "")

        # Extract Shopify IDs from the agent's response
        ids = re.findall(r'ID[:\s]*\(?(\d+)\)?', action_input, re.IGNORECASE)

        # Ensure at least one product is returned
        if not ids:
            agent_output["action_input"] += "\nNo exact matches found. Suggesting the closest products."
            fallback_products = find_products_flexible(action_input)  # Pass the corrected query as input

            # Ensure fallback_products are dictionaries
            fallback_products = [
                {
                    "shopify_id": str(product["shopify_id"]),
                    "title": product["title"],
                    "product_type": product["product_type"],
                    "price": str(product["price"]),
                    "status": product["status"]
                }
                for product in fallback_products
            ]

            # Update action_input with fallback product details
            ids = [product["shopify_id"] for product in fallback_products]
            agent_output["action_input"] += "\nSuggested products: " + ", ".join(
                [f"{p['title']} (ID: {p['shopify_id']})" for p in fallback_products]
            )

        # Ensure shopify_id is included in the response
        agent_output["shopify_id"] = ids if ids else []

        return agent_output