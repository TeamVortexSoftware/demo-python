import os
import hashlib
import hmac
import json
import base64
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pydantic import BaseModel

# JWT settings
JWT_SECRET = os.getenv("JWT_SECRET", "demo-secret-key")


class Group(BaseModel):
    type: str
    id: str
    name: str


class DemoUser(BaseModel):
    id: str
    email: str
    role: str
    groups: List[Group]


class UserInDB(BaseModel):
    id: str
    email: str
    password: str
    role: str
    groups: List[Group]


def simple_hash(password: str) -> str:
    """Simple SHA256 hashing for demo purposes (not for production!)"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_simple_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password using simple SHA256 (demo only!)"""
    return simple_hash(plain_password) == hashed_password


# Demo users database
demo_users_db = [
    UserInDB(
        id="user-1",
        email="admin@example.com",
        password=simple_hash("password123"),
        role="admin",
        groups=[
            Group(type="team", id="team-1", name="Engineering"),
            Group(type="organization", id="org-1", name="Acme Corp")
        ]
    ),
    UserInDB(
        id="user-2",
        email="user@example.com",
        password=simple_hash("userpass"),
        role="user",
        groups=[
            Group(type="team", id="team-1", name="Engineering")
        ]
    )
]


def get_user_by_email(email: str) -> Optional[UserInDB]:
    """Get user by email from the demo database"""
    for user in demo_users_db:
        if user.email == email:
            return user
    return None


def authenticate_user(email: str, password: str) -> Optional[DemoUser]:
    """Authenticate user by email and password"""
    user_db = get_user_by_email(email)
    if not user_db or not verify_simple_password(password, user_db.password):
        return None

    return DemoUser(
        id=user_db.id,
        email=user_db.email,
        role=user_db.role,
        groups=user_db.groups
    )


def create_simple_jwt(user: DemoUser) -> str:
    """Create a simple JWT-like token (demo only - not real JWT!)"""
    expire = (datetime.utcnow() + timedelta(hours=24)).timestamp()

    payload = {
        "sub": user.email,
        "userId": user.id,
        "email": user.email,
        "role": user.role,
        "groups": [group.model_dump() for group in user.groups],
        "exp": expire
    }

    # Simple token: base64(payload) + "." + hmac_signature
    payload_str = json.dumps(payload)
    payload_b64 = base64.urlsafe_b64encode(payload_str.encode()).decode()

    signature = hmac.new(
        JWT_SECRET.encode(),
        payload_b64.encode(),
        hashlib.sha256
    ).hexdigest()

    return f"{payload_b64}.{signature}"


def verify_simple_jwt(token: str) -> Optional[DemoUser]:
    """Verify simple JWT-like token"""
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None

        payload_b64, signature = parts

        # Verify signature
        expected_signature = hmac.new(
            JWT_SECRET.encode(),
            payload_b64.encode(),
            hashlib.sha256
        ).hexdigest()

        if signature != expected_signature:
            return None

        # Decode payload
        payload_str = base64.urlsafe_b64decode(payload_b64).decode()
        payload = json.loads(payload_str)

        # Check expiration
        if payload.get("exp", 0) < datetime.utcnow().timestamp():
            return None

        return DemoUser(
            id=payload["userId"],
            email=payload["email"],
            role=payload["role"],
            groups=[Group(**group) for group in payload["groups"]]
        )
    except:
        return None


def get_demo_users() -> List[Dict[str, Any]]:
    """Get demo users (for testing)"""
    return [
        {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "groups": [group.model_dump() for group in user.groups]
        }
        for user in demo_users_db
    ]


# Aliases for compatibility
create_session_jwt = create_simple_jwt
verify_session_jwt = verify_simple_jwt