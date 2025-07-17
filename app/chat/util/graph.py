from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage
import os
from typing import TypedDict, Annotated, Sequence
from operator import add as add_messages
from .instructions import instructions_chat, instructions_chat_anything
from dotenv import load_dotenv
from functools import lru_cache


from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_tavily import TavilySearch


load_dotenv()

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

class LLMResponseLangGraph:
    @staticmethod
    @lru_cache(maxsize=10)
    def build_graph(ai_provider: str, ai_model: str):
        llm = init_chat_model(model_provider=ai_provider, model=ai_model)

        
        def llm_node_chat(state: AgentState) -> AgentState:
            messages = [SystemMessage(content=instructions_chat)] + state["messages"]
            response = llm.invoke(messages)
            return {"messages": [response]}

        graph = StateGraph(AgentState)
        graph.add_node("chat", llm_node_chat)

        graph.set_entry_point("chat")
        graph.add_edge("chat", END)
        return graph.compile()

    @staticmethod
    def get_response(ai_provider: str, ai_model: str, message: list):
        chat_graph = LLMResponseLangGraph.build_graph(ai_provider=ai_provider, ai_model=ai_model)
        state = {"messages": message}

        result = chat_graph.invoke(state)
        return result["messages"][-1]


# Define the tool first, before using it
@tool
def add(a: int, b: int):
    """This is an addition function that adds 2 numbers"""
    return a + b

@tool
def docducgosearch(query: str) -> str:
    """Searches the web using DuckDuckGo for live data and returns a summary of results."""
    try:
        search = DuckDuckGoSearchResults(backend="news")
        results = search.invoke(query)
        print("Result from Duckduckgo::",results)

        if not results:
            return "No results found."
        return results
    except Exception as e:
        print(f"Erro to get data from dockdockgosearch, {e}")
        return "No results found."

@tool
def tavily_search(query: str) -> str:
    """Searches the web using TavilySearch for live data and returns a summary of results."""
    try:
        tool = TavilySearch(max_results=2)
        result = tool.invoke(query)
        print("Result from tavily::",result)
        if not result:
            return "No results found."
        return result
    except Exception as e:
        print(f"Erro to get data from dockdockgosearch, {e}")
        return "No results found." 
    
# List of tools to be used
tools = [add, tavily_search, docducgosearch]

class LLMResponseLangGraphAgent:   
    @staticmethod
    @lru_cache(maxsize=10)
    def build_graph(ai_provider: str, ai_model: str):
        llm = init_chat_model(model_provider=ai_provider, model=ai_model).bind_tools(tools)

        def llm_node_chat(state: AgentState) -> AgentState:
            messages = [SystemMessage(content=instructions_chat_anything)] + state["messages"]
            response = llm.invoke(messages)
            return {"messages": [response]}
        
        
        def should_continue(state: AgentState) -> AgentState:
            messages = state["messages"]
            last_message = messages[-1]

            if not last_message.tool_calls:
                return "end"
            else:
                return "continue"


        graph = StateGraph(AgentState)
        tool_node = ToolNode(tools=tools)
        graph.add_node("chat", llm_node_chat)
        graph.add_node("tools", tool_node)
        graph.set_entry_point("chat")
        graph.add_conditional_edges(
            "chat",
            should_continue,
            {
                "continue": "tools",
                "end": END,
            },
        )
        graph.add_edge("tools", "chat")

        return graph.compile()

    @staticmethod
    def get_response(ai_provider: str, ai_model: str, message: list):
        chat_graph = LLMResponseLangGraphAgent.build_graph(ai_provider=ai_provider, ai_model=ai_model)
        state = {"messages": message}

        result = chat_graph.invoke(state)
        return result["messages"][-1]
     