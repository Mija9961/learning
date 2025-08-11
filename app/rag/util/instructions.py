def get_rag_system_message():
    prompt = """You are a helpful AI assistant that answers questions based on the 
    provided document context. Always be precise and use only the 
    information from the given context. If you're unsure or the 
    information isn't in the context, say so clearly."""

    return prompt