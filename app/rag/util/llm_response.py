from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv
from uuid import uuid4
from flask import session
from .shared_state import chat_sessions
from bs4 import BeautifulSoup

# Setup model

model_client = OpenAIChatCompletionClient(model="gpt-4.1-mini")

from langchain_core.messages import HumanMessage, AIMessage

from .graph import LLMResponseLangGraph

class LLMResponse:
    @staticmethod
    def get_model_client():
        try:
            model = session['ai_model']
            model_client = OpenAIChatCompletionClient(model=model)
            return model_client
        except Exception as e:
            print("Something went wrong to get model client: ",e)
            return model_client
        
    @staticmethod
    def get_session_id():
        """Generate and retrieve the unique session ID for each user."""
        if "session_id" not in session:
            session["session_id"] = str(uuid4())  # Ensure the session_id is unique per user
        return session["session_id"]
    
    

    @staticmethod
    def remove_html_tags(text):
        soup = BeautifulSoup(text, 'html.parser')
        return soup.get_text()
    
    @staticmethod
    async def get_formatted_response_from_llm(prompt):
        """
        Get formatted response from LLM for RAG-based Q&A.
        
        Args:
            prompt (str): The formatted prompt with context
            
        Returns:
            str: Formatted response from the LLM
        """
        try:
            session_id = LLMResponse.get_session_id()
            
            # Use different LLM providers based on session settings
            if 'ai_model' in session and 'ai_provider' in session and session['ai_provider'].lower() != 'openai':
                response = LLMResponseLangGraph.get_response(
                    ai_provider=session['ai_provider'],
                    ai_model=session['ai_model'],
                    message=[HumanMessage(content=prompt)],
                    request_type="rag"
                )
                return response.content

            # Create valid Python identifier for agent name
            safe_name = f"rag_assistant_{session_id.replace('-', '_')}"
            
            # Default to OpenAI
            professor = AssistantAgent(
                name=safe_name,
                description="AI assistant that answers questions based on document context",
                model_client=LLMResponse.get_model_client(),
                system_message=(
                    "You are a helpful AI assistant that answers questions based on the "
                    "provided document context. Always be precise and use only the "
                    "information from the given context. If you're unsure or the "
                    "information isn't in the context, say so clearly."
                )
            )

            last_response = None
            clean_prompt = LLMResponse.remove_html_tags(prompt)

            async for chunk in professor.run_stream(task=clean_prompt):
                if hasattr(chunk, "content"):
                    last_response = chunk.content

            return last_response or "Sorry, I couldn't generate a response based on the provided context."

        except Exception as e:
            current_app.logger.error(f"Error in get_formatted_response_from_llm: {str(e)}")
            return "An error occurred while processing your question. Please try again."
