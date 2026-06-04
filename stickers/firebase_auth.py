from __future__ import annotations

import os


def initialize_firebase_app() -> None:
    import firebase_admin
    from firebase_admin import credentials

    if firebase_admin._apps:
        return

    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if credentials_path:
        cred = credentials.Certificate(credentials_path)
    else:
        cred = credentials.ApplicationDefault()

    firebase_admin.initialize_app(cred)


def verify_firebase_token(authorization_header: str) -> str:
    from firebase_admin import auth

    if authorization_header.startswith("Bearer "):
        token = authorization_header.split(" ", 1)[1].strip()
    else:
        token = authorization_header.strip()

    if not token:
        raise ValueError("Missing bearer token")

    decoded = auth.verify_id_token(token)
    return decoded["uid"]
