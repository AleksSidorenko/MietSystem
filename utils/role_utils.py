# utils/role_utils.py


def user_has_role(user, roles: list[str]) -> bool:
    """
    Проверяет, принадлежит ли пользователь одной из заданных ролей.
    Пример: user_has_role(user, ["TENANT", "ADMIN"])
    """
    return hasattr(user, "role") and user.role in roles
