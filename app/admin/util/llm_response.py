from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv
from uuid import uuid4
from flask import session
# Setup model

model_client = OpenAIChatCompletionClient(model="gpt-4.1-mini")

class LLMResponse:
    @staticmethod
    def get_session_id():
        """Generate and retrieve the unique session ID for each user."""
        if "session_id" not in session:
            session["session_id"] = str(uuid4())  # Ensure the session_id is unique per user
        return session["session_id"]
    @staticmethod
    async def get_formatted_response_from_llm(data):
        formatted_answer = await LLMResponse.get_response(data)
         
        return formatted_answer
    

    @staticmethod
    def get_professor(session_id):
        """Create a unique professor instance per session."""
        safe_name = f"professor_{session_id.replace('-', '_')}"
        return AssistantAgent(
            name=safe_name,
            description="Professor who formats text and answers questions.",
            model_client=model_client,
            system_message="You are a helpful assistant.",
        ), safe_name

    @staticmethod
    async def get_response(message):
        """Generate a response asynchronously using the professor (AssistantAgent)."""
        session_id = LLMResponse.get_session_id()

        professor, professor_name = LLMResponse.get_professor(session_id)
        

        last_response = None
        conversation_history_clean_text = message

        async for chunk in professor.run_stream(task=conversation_history_clean_text):
            if hasattr(chunk, "content") and getattr(chunk, "source", "") == professor_name:
                last_response = chunk.content

        return last_response or "Sorry, I couldn't generate a response."