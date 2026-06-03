API_KEYS = {
    "admin-key-123": "admin",
    "dev-key-123": "developer",
    "viewer-key-123": "viewer"
}

def require_role(key: str, allowed):
    role = API_KEYS.get(key)
    if not role:
        return None
    if role == "admin":
        return "admin"
    if role in allowed:
        return role
    return None
