from app.modules.users.models import User


def get_role_value(user: User) -> str:
    """Get role value as string from user."""
    if hasattr(user.role, "value"):
        return user.role.value
    return str(user.role)
