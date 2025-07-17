
# Multi-tenant storage
chat_sessions = {}  # Dict: session_id -> list of {user, bot}
subjects_storage = []
current_subject_dict = {}