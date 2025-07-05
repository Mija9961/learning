from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv
from uuid import uuid4
from .instructions import instructions_chat
from flask import session
from flask_login import current_user

from .shared_state import global_chat_sessions

load_dotenv()
# Setup model
system_messages_chat = instructions_chat

from langchain_core.messages import HumanMessage, AIMessage

from .graph import LLMResponseLangGraph

class LLMResponse:
    @staticmethod
    def get_model_client():
        model_client = OpenAIChatCompletionClient(model="gpt-4.1-nano")
        try:
            if current_user.is_authenticated:
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
    def get_professor_chat(session_id):
        """Create a unique professor instance per session."""
        safe_name = f"professor_{session_id.replace('-', '_')}"
        return AssistantAgent(
            name=safe_name,
            description="Assistant who helps the user",
            model_client=LLMResponse.get_model_client(),
            system_message=system_messages_chat,
        ), safe_name

    async def get_response_chat(message: str):
        """Generate a response asynchronously using the professor (AssistantAgent)."""
        session_id = LLMResponse.get_session_id()

        if 'ai_model' in session and 'ai_provider' in session and session['ai_provider'].lower() != 'openai':
            # Fetch all previous chat history for the session
            chat_history = global_chat_sessions.get(session_id, [])

            conversation_history = []
            for entry in chat_history:
                human_messsage = HumanMessage(content=entry['user'])
                ai_messsage = AIMessage(content=entry['bot'])
                conversation_history.append(human_messsage)
                conversation_history.append(ai_messsage)

            human_messsage = HumanMessage(content=message)

            conversation_history.append(human_messsage)

            last_response = LLMResponseLangGraph.get_response(
                ai_provider=session['ai_provider'],
                ai_model= session['ai_model'],
                message = conversation_history
            )

            return last_response.content or "Sorry, I couldn't generate a response."
        
        professor, professor_name = LLMResponse.get_professor_chat(session_id)
        
        # Fetch all previous chat history for the session
        chat_history = global_chat_sessions.get(session_id, [])

        conversation_history = "\n".join([f"User: {entry['user']}\nBot: {entry['bot']}" for entry in chat_history[-25:]]) # Send last 25 messages
        
        # Now append the current user message to maintain the conversation flow
        conversation_history += f"\nUser: {message}\nBot:"

        # Generate the bot's response based on the entire conversation context
        last_response = None

        async for chunk in professor.run_stream(task=conversation_history):
            if hasattr(chunk, "content") and getattr(chunk, "source", "") == professor_name:
                last_response = chunk.content

        return last_response or "Sorry, I couldn't generate a response."
    