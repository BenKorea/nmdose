import os

def get_keycloak_settings():
    mode = os.getenv("NMDOSE_AUTH_MODE", "dev")
    return {
        "enabled": mode == "keycloak",
        "realm": "nmdose",
        "client_id": "nmdose-web",
        "auth_server_url": "http://localhost:8080",
        "admin_user": "admin",
        "admin_password": "admin",
    }
