from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_ollama import OllamaLLM  # Replace deprecated Ollama import



import pymysql
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sqlalchemy as sa
from sqlalchemy import Table, MetaData
from sqlalchemy.exc import SQLAlchemyError
import logging
import pandas as pd




class DBConnection:
    _instance = None
    _engine = None
    _Session = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DBConnection, cls).__new__(cls)
            cls._engine = create_engine("mysql+pymysql://root:root@localhost:3306/shopify_search_assistant",
                                        pool_size=200,          
                                        max_overflow=20,       
                                        pool_timeout=30,       
                                        pool_recycle=1800 )
            cls._Session = sessionmaker(bind=cls._engine)
        return cls._instance

    def get_session(self):
        return self._Session()

    def get_engine(self):
        return self._engine
    



logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class ProductRepository:
    def __init__(self):
        self.db_connection = DBConnection()
        self.engine = self.db_connection.get_engine()
        self.metadata = MetaData()
        self.metadata.reflect(bind=self.engine)

    def call_all_products_with_variants(self):
        try:
            with self.engine.connect() as conn:
                products = Table('products_synonym', self.metadata, autoload_with=self.engine)
                variants = Table('variants_synonym', self.metadata, autoload_with=self.engine)
                query = (
                    sa.select(products, variants)
                    .join(variants, products.c.id == variants.c.product_id)
                )
                result = conn.execute(query)
                return result.mappings()  # Return a Result object with mappings
        except SQLAlchemyError as e:
            logging.error(f"Error fetching products with variants: {e}")
            return []

    def call_distinct_product_type(self):
        try:
            products = Table("products_synonym", self.metadata, autoload_with=self.engine)
            query = sa.select(products.c.product_type).distinct()
            with self.engine.connect() as conn:
                result = conn.execute(query)
                return result.fetchall()
        except SQLAlchemyError as e:
            logging.error(f"Error fetching distinct product types: {e}")
            return []



# Shared state structure
class State(TypedDict):
    messages: Annotated[list, add_messages]
    product_types: str
    next_node: str


# LLM Setup
general_llm = OllamaLLM(model="qwen2.5-coder", temperature=0.7)
precise_llm = OllamaLLM(model="qwen2.5-coder", temperature=0.5)


# Route user message to either product-related or general assistant
def route_user(state: State) -> State:
    user_input = state["messages"][-1].content
    prompt = f"""
You are an intent classifier.

Classify the following user message into one of the following categories by replying ONLY with the keyword (no explanation):
- get_product_types → if the user is asking what products are available, what kind of items you sell, product types, product suggestions, categories, or anything related to shopping or browsing products.
- chatbot → for anything else (like general questions, casual talk, etc).

User message: "{user_input}"

Just reply with: get_product_types OR chatbot
    """
    decision = general_llm.invoke([{"role": "user", "content": prompt}]).strip().lower()
    print("ROUTER DECISION:", decision)
    if decision not in ["get_product_types", "chatbot"]:
        decision = "chatbot"

    return {**state, "next_node": decision}



# Choose next node from router
def next_step(state: State) -> str:
    return state.get("next_node", "chatbot")


# Fetch product types from database
def fetch_product_types(state: State) -> State:
    db = ProductRepository()
    types = [row[0] for row in db.call_distinct_product_type()]
    return {**state, "product_types": types}


# Convert raw product types into structured format
def structure_product_list(state: State) -> State:
    prompt = f"Generate a short, structured list from these product types: {state['product_types']}"
    response = precise_llm.invoke([
        {"role": "system", "content": "You generate structured product category lists."},
        {"role": "user", "content": prompt}
    ])
    return {**state, "product_types": response}


# Main chatbot logic
def assistant_response(state: State) -> State:
    product_info = (
        f"The following product categories are available in our store:\n{state['product_types']}\n\n"
        if state['product_types']
        else ""
    )
    user_msg = state["messages"][-1].content
    print("Structured Product Types:", state["product_types"])

    reply = general_llm.invoke([
        {
            "role": "system",
            "content": (
                "You are a helpful assistant for a shopping assistant app. "
                "If the user is asking about available products, and product categories have been provided, "
                "include them in your answer."
            )
        },
        {"role": "user", "content": product_info + user_msg}
    ])

    updated_messages = state["messages"] + [{"role": "assistant", "content": reply}]
    return {**state, "messages": updated_messages, "next_node": ""}


# Build the graph
builder = StateGraph(State)
builder.add_node("router", route_user)
builder.add_node("get_product_types", fetch_product_types)
builder.add_node("generate_product_list", structure_product_list)
builder.add_node("chatbot", assistant_response)

builder.add_edge(START, "router")
builder.add_conditional_edges("router", next_step, {
    "get_product_types": "get_product_types",
    "chatbot": "chatbot"
})
builder.add_edge("get_product_types", "generate_product_list")
builder.add_edge("generate_product_list", "chatbot")
builder.add_edge("chatbot", END)

graph = builder.compile()


# Run and stream outputs
def stream_graph_updates(user_input: str):
    initial_state = {
        "messages": [{"role": "user", "content": user_input}],
        "product_types": "",
        "next_node": ""
    }

    for event in graph.stream(initial_state):
        for value in event.values():
            for message in value["messages"]:
                if isinstance(message, dict) and message.get("role") == "assistant":
                    print(f"Assistant: {message.get('content')}")
                elif hasattr(message, "role") and getattr(message, "role") == "assistant":
                    print(f"Assistant: {getattr(message, 'content')}")
                elif isinstance(message, str):
                    print(f"Assistant: {message}")


# Interactive loop
if __name__ == "__main__":
    while True:
        try:
            user_input = input("User: ")
            if user_input.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break
            stream_graph_updates(user_input)
        except Exception as e:
            print("Error:", e)
            break