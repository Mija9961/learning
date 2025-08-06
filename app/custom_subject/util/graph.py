from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage
import os
from typing import TypedDict, Annotated, Sequence
from operator import add as add_messages
from .instructions import get_prompt_interview, get_prompt_learn
from dotenv import load_dotenv
from functools import lru_cache
from bs4 import BeautifulSoup

load_dotenv()

class LLMResponseLangGraph:
    @staticmethod
    def remove_html_tags(text):
        soup = BeautifulSoup(text, 'html.parser')
        return soup.get_text()
    @staticmethod
    @lru_cache(maxsize=10)
    def build_graph(ai_provider: str, ai_model: str, request_type="learn"):
        llm = init_chat_model(model_provider=ai_provider, model=ai_model)

        class AgentState(TypedDict):
            messages: Annotated[Sequence[BaseMessage], add_messages]

        def llm_node_learn(state: AgentState) -> AgentState:
            messages = [SystemMessage(content=get_prompt_learn())] + state["messages"]
            response = llm.invoke(messages)

            return {"messages": [response]}
        
        def llm_node_interview(state: AgentState) -> AgentState:
            messages = [SystemMessage(content=get_prompt_interview())] + state["messages"]
            response = llm.invoke(messages)
            return {"messages": [response]}

        graph = StateGraph(AgentState)
        if request_type == "learn":
            graph.add_node("chat", llm_node_learn)
        else:
            graph.add_node("chat", llm_node_interview)

        graph.set_entry_point("chat")
        graph.add_edge("chat", END)
        return graph.compile()

    @staticmethod
    def get_response(ai_provider: str, ai_model: str, message: list, request_type):
        chat_graph = LLMResponseLangGraph.build_graph(ai_provider=ai_provider, ai_model=ai_model, request_type=request_type)
        state = {"messages": message}

        result = chat_graph.invoke(state)
        return result["messages"][-1]
    