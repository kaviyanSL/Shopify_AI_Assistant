import re
from langchain.agents import Tool, initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from langchain.schema.messages import SystemMessage
from src.main.service.agent_service.AgentToolsService import get_product_types, find_products_flexible
from src.main.service.agent_service.QwenChatModelWrapperService import QwenChatModel  

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
                description="Finds products based on flexible search criteria."
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
            then ask a follow-up question to gather more details like price range or product type."""
        ))

    def run(self, user_prompt: str):
        return self.agent.run(user_prompt)



    def process_agent_response(self, agent_output) -> dict:
        if isinstance(agent_output, str):
            action_input = agent_output
            agent_output = {"action": "Final Answer", "action_input": action_input}
        else:
            action_input = agent_output.get("action_input", "")

        ids = re.findall(r'shopify_id[:\s]*\(?(\d+)\)?', action_input, re.IGNORECASE)

        agent_output["shopify_id"] = ids if ids else []

        return agent_output