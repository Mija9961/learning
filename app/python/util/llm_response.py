from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv
from uuid import uuid4
from .instructions import instructions1, instructions_learn
from flask import session
from .shared_state import chat_sessions

# Setup model
system_messages = instructions1
system_messages_learn = instructions_learn
model_client = OpenAIChatCompletionClient(model="gpt-4.1-mini")


class LLMResponse:
    @staticmethod
    def get_session_id():
        """Generate and retrieve the unique session ID for each user."""
        if "session_id" not in session:
            session["session_id"] = str(uuid4())  # Ensure the session_id is unique per user
        return session["session_id"]
    
    
    @staticmethod
    def get_professor_interview(session_id):
        """Create a unique professor instance per session."""
        safe_name = f"professor_{session_id.replace('-', '_')}"
        return AssistantAgent(
            name=safe_name,
            description="Professor who asks interview questions.",
            model_client=model_client,
            system_message=system_messages,
        ), safe_name

    async def get_response(message):
        """Generate a response asynchronously using the professor (AssistantAgent)."""
        session_id = LLMResponse.get_session_id()

        professor, professor_name = LLMResponse.get_professor_interview(session_id)
        
        # Fetch all previous chat history for the session
        chat_history = chat_sessions.get(session_id, [])

        conversation_history = "\n".join([f"User: {entry['user']}\nBot: {entry['bot']}" for entry in chat_history])
        
        # Now append the current user message to maintain the conversation flow
        conversation_history += f"\nUser: {message}\nBot:"

        # Generate the bot's response based on the entire conversation context
        last_response = None

        async for chunk in professor.run_stream(task=conversation_history):
            if hasattr(chunk, "content") and getattr(chunk, "source", "") == professor_name:
                last_response = chunk.content

        return last_response or "Sorry, I couldn't generate a response."
    
    @staticmethod
    def get_professor_learn(session_id):
        """Create a unique professor instance per session."""
        safe_name = f"professor_{session_id.replace('-', '_')}"
        return AssistantAgent(
            name=safe_name,
            description="Professor who teaches Python",
            model_client=model_client,
            system_message=system_messages_learn,
        ), safe_name

    async def get_response_learn(message):
        """Generate a response asynchronously using the professor (AssistantAgent)."""
        session_id = LLMResponse.get_session_id()

        professor, professor_name = LLMResponse.get_professor_learn(session_id)
        

        # Fetch all previous chat history for the session
        chat_history = chat_sessions.get(session_id, [])

        conversation_history = "\n".join([f"User: {entry['user']}\nBot: {entry['bot']}" for entry in chat_history])
        
        # Now append the current user message to maintain the conversation flow
        conversation_history += f"\nUser: {message}\nBot:"
        # Generate the bot's response based on the entire conversation context
        last_response = None

        async for chunk in professor.run_stream(task=conversation_history):
            if hasattr(chunk, "content") and getattr(chunk, "source", "") == professor_name:
                last_response = chunk.content

        return last_response or "Sorry, I couldn't generate a response."
            