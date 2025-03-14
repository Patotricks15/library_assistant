from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langgraph.prebuilt import create_react_agent
from langchain.agents import Tool, initialize_agent
from dotenv import load_dotenv
import sqlite3
import re


load_dotenv()



conn = sqlite3.connect("/home/patrick/library_assistant/bookstore.db")
cursor = conn.cursor()



class State(TypedDict):
    question: str
    sql_output: str

db = SQLDatabase.from_uri("sqlite:////home/patrick/library_assistant/bookstore.db")

model_3_5 = ChatOpenAI(model="gpt-3.5-turbo-1106", temperature=0)
toolkit = SQLDatabaseToolkit(db=db, llm=model_3_5)
sql_tools = toolkit.get_tools()

sql_prefix = (
    "You are a SQLAgent specialized in interacting with a SQLite database. "
    "Given a user's request, generate a syntactically correct SQLite query or extract purchase information "
    "(book title and quantity) clearly. The tables are:\n"
    "books (id, title, author, description, price, stock), customers, orders."
)
sql_system_message = SystemMessage(content=sql_prefix)
sql_agent = create_react_agent(model_3_5, sql_tools)

def parse_order(response):
    match = re.search(r'(?i)buy(?:ing)?\s(\d+)\s(?:unit|copy|copies|units)?\sof\s[\"\']?(.*?)[\"\']?$', response)
    if match:
        quantity = int(match.group(1))
        book_title = match.group(2).strip()
        return book_title, quantity
    return None, None

def process_purchase(customer_name, book_title, quantity=1):
    cursor.execute("SELECT id, stock FROM books WHERE title = ?", (book_title,))
    book = cursor.fetchone()

    if not book:
        return "Book not found."

    book_id, stock = book

    if stock < quantity:
        return f"Insufficient stock. Only {stock} units available."

    # Get or create customer
    cursor.execute("SELECT id FROM customers WHERE name = ?", (customer_name,))
    customer = cursor.fetchone()

    if customer is None:
        cursor.execute("INSERT INTO customers (name) VALUES (?)", (customer_name,))
        customer_id = cursor.lastrowid
    else:
        customer_id = customer[0]

    # Insert order and update stock
    cursor.execute("INSERT INTO orders (customer_id, book_id, quantity) VALUES (?, ?, ?)",
                   (customer_id, book_id, quantity))

    cursor.execute("UPDATE books SET stock = stock - ? WHERE id = ?", (quantity, book_id))
    conn.commit()

    return "Order successfully placed."

# LangGraph Workflow
workflow = StateGraph(State)

def agent_node(state):
    """
    Node in the LangGraph workflow that takes a question and returns a response from the SQLAgent.
    If the question is a purchase request, it processes the purchase and returns the result.
    """
    question = state["question"]
    response = sql_agent.invoke({"messages": [HumanMessage(content=question)]})['messages'][-1].content
    """
    Node in the LangGraph workflow that takes a question and returns a response from the SQLAgent.
    If the question is a purchase request, it processes the purchase and returns the result.
    """

    book_title, quantity = parse_order(question)

    if book_title and quantity:
        purchase_response = process_purchase("Patrick", book_title, quantity)
        final_response = purchase_response
    else:
        final_response = response

    return {"sql_output": final_response}

workflow.add_node("agent_node", agent_node)
workflow.add_edge(START, "agent_node")
workflow.add_edge("agent_node", END)
graph = workflow.compile()

answer = graph.invoke({"question": "I want to buy 2 units of 'Clean Code'"})
print(answer["sql_output"])