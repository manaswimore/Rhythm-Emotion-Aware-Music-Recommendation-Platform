import re


EMAIL_PATTERN = re.compile(
    r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
)


def validate_register_data(data):
    if not isinstance(data, dict):
        return "Request body must be a JSON object."

    name = data.get("name", "")
    email = data.get("email", "")
    password = data.get("password", "")

    if not isinstance(name, str) or not name.strip():
        return "Name is required."

    if len(name.strip()) < 2:
        return "Name must contain at least 2 characters."

    if len(name.strip()) > 100:
        return "Name cannot exceed 100 characters."

    if not isinstance(email, str) or not email.strip():
        return "Email is required."

    email = email.strip().lower()

    if not EMAIL_PATTERN.match(email):
        return "Please enter a valid email address."

    if not isinstance(password, str) or not password:
        return "Password is required."

    if len(password) < 8:
        return "Password must contain at least 8 characters."

    if len(password) > 128:
        return "Password cannot exceed 128 characters."

    return None


def validate_login_data(data):
    if not isinstance(data, dict):
        return "Request body must be a JSON object."

    email = data.get("email", "")
    password = data.get("password", "")

    if not isinstance(email, str) or not email.strip():
        return "Email is required."

    if not isinstance(password, str) or not password:
        return "Password is required."

    return None