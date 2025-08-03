async def get_user_locale(user_id: int) -> str:
    return "ar"

async def send_feedback(user_id: int, message: str):
    print(f"Feedback from {user_id}: {message}")
