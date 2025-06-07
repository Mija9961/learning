from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv
from uuid import uuid4
from .instructions import instructions
from flask import session
from .shared_state import mocktest_sessions
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
        
        # Fetch all previous chat history for the session
        chat_history = mocktest_sessions.get(session_id, [])
        task = str({'history': chat_history, 'topic': topic})
        last_response = None

        async for chunk in professor.run_stream(task=task):
            if hasattr(chunk, "content") and getattr(chunk, "source", "") == professor_name:
                last_response = chunk.content
        return last_response or "Sorry, I couldn't generate a response."

    @staticmethod
    def get_question_paper(topic):
        response = asyncio.run(LLMResponse.get_response_mocktest(topic))

        response = json.loads(response)
        print(f"Response: {response}")
        # 🟠 Correctly extract questions
        questions_dict = response.get('mock_questions', {})
        questions = questions_dict.get(topic, [])

        session_id = LLMResponse.get_session_id()

        if session_id not in mocktest_sessions:
            mocktest_sessions[session_id] = {}
        if topic not in mocktest_sessions[session_id]:
            mocktest_sessions[session_id][topic] = []

        mocktest_sessions[session_id][topic].extend(questions)

        return response.get('mock_questions', []), response.get('mock_answers', [])
