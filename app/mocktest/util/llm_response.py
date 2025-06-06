from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv
from uuid import uuid4
from .instructions import instructions
from flask import session
from .shared_state import mock_questions, mock_answers
import asyncio, json
load_dotenv()
# Setup model
system_messages = instructions
model_client = OpenAIChatCompletionClient(model="gpt-4.1-mini")

class LLMResponse:
    @staticmethod
    def get_session_id():
        """Generate and retrieve the unique session ID for each user."""
        if "session_id" not in session:
            session["session_id"] = str(uuid4())  # Ensure the session_id is unique per user
        return session["session_id"]    
    
    @staticmethod
    def get_professor_mocktest(session_id):
        """Create a unique professor instance per session."""
        safe_name = f"professor_{session_id.replace('-', '_')}"
        return AssistantAgent(
            name=safe_name,
            description="Professor who sets mock question paper.",
            model_client=model_client,
            system_message=system_messages,
        ), safe_name

    @staticmethod
    async def get_response_mocktest(topic):
        """Generate a response asynchronously using the professor (AssistantAgent)."""
        session_id = LLMResponse.get_session_id()

        professor, professor_name = LLMResponse.get_professor_mocktest(session_id)
        
        last_response = None

        async for chunk in professor.run_stream(task=topic):
            if hasattr(chunk, "content") and getattr(chunk, "source", "") == professor_name:
                last_response = chunk.content
        # last_response = await professor.run(task=topic)
        print(last_response)
        return last_response or "Sorry, I couldn't generate a response."

    @staticmethod
    def get_question_paper(topic):
        response = asyncio.run(LLMResponse.get_response_mocktest(topic))
        print(f"Question paper type: {type(response)} ")
        print(f"Question paper: {response} ")

        response = json.loads(response)
        
        return response.get('mock_questions', []), response.get('mock_answers', [])
