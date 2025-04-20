import os
import logging
from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase
from langchain.agents import create_sql_agent
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain_groq import ChatGroq
from src.main.service.agent_service import AgentToolsService as tool

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.info("Initializing Groq Agent")
load_dotenv()
api_token_groq = os.getenv("chat_assistant_api_1")
db_api = os.getenv("db_info")

logger.info(f"Using Groq model: llama3-70b-8192")


class LLMsModelService:
    def __init__(self):
        self.llm_query = ChatGroq(api_key=api_token_groq, model_name="llama3-70b-8192", temperature=0.4)
        self.llm = ChatGroq(api_key=api_token_groq, model_name="llama3-70b-8192", temperature=0.7)
        self.db = SQLDatabase.from_uri(db_api)
        self.toolkit = SQLDatabaseToolkit(db=self.db, llm=self.llm_query)
        self.agent_executor = create_sql_agent(llm=self.llm_query, toolkit=self.toolkit, verbose=False)
        
    # Add async methods
    async def ainvoke_llm(self, messages):
        """Invoke the LLM asynchronously"""
        tools = [tool.query_database_tool]
        llm_with_tools = self.llm.bind_tools(tools)
        return await llm_with_tools.ainvoke(messages)
    
    async def ainvoke_llm_query(self, messages):
        """Invoke the query LLM asynchronously"""
        return await self.llm_query.ainvoke(messages)
    
    async def ainvoke_agent(self, input_data):
        """Invoke the agent executor asynchronously"""
        return await self.agent_executor.ainvoke(input_data)