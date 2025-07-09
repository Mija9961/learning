from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage
import os
from typing import TypedDict, Annotated, Sequence
from operator import add as add_messages
from .instructions import instructions_chat
from dotenv import load_dotenv
from functools import lru_cache


load_dotenv()

class LLMResponseLangGraph:
    @staticmethod
    @lru_cache(maxsize=10)
    def build_graph(ai_provider: str, ai_model: str):
        llm = init_chat_model(model_provider=ai_provider, model=ai_model)

        class AgentState(TypedDict):
            messages: Annotated[Sequence[BaseMessage], add_messages]

        
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
    