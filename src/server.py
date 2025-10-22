import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

# Add the parent directory to sys.path to import vortex_sdk
parent_dir = Path(__file__).parent.parent.parent / "packages" / "vortex-python-sdk" / "src"
sys.path.insert(0, str(parent_dir))

from fastapi import FastAPI, Request, Response, HTTPException, Depends, Cookie
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import our simplified auth system
from auth import (
    DemoUser,
    authenticate_user,
    create_session_jwt,
    verify_session_jwt,
    get_demo_users
)

# Import Vortex SDK
try:
    from vortex_sdk import Vortex, JwtPayload, InvitationTarget, VortexApiError
    vortex_import_ok = True
except ImportError as e:
    print(f"⚠️  Vortex SDK import failed: {e}")
    vortex_import_ok = False

app = FastAPI(
    title="Vortex Python Demo (Working)",
    description="Demo FastAPI app with working routes (no python-jose dependency)",
    version="0.0.1"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Vortex client if available
if vortex_import_ok:
    vortex_api_key = os.getenv("VORTEX_API_KEY", "demo-api-key")
    vortex_client = Vortex(api_key=vortex_api_key)
else:
    vortex_client = None


# Pydantic models
class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    success: bool
    user: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class LogoutResponse(BaseModel):
    success: bool


class JwtRequest(BaseModel):
    user_id: Optional[str] = None
    identifiers: Optional[Dict[str, str]] = None
    groups: Optional[list] = None
    role: Optional[str] = None


class AcceptInvitationsRequest(BaseModel):
    invitationIds: list
    target: Dict[str, str]


# Helper functions
def get_current_user(session: Optional[str] = Cookie(None)) -> Optional[DemoUser]:
    """Get current user from session cookie"""
    if not session:
        return None
    return verify_session_jwt(session)


def demo_user_to_vortex_format(user: DemoUser) -> Dict[str, Any]:
    """Convert DemoUser to Vortex authenticated user format"""
    return {
        "userId": user.id,
        "identifiers": {"email": user.email},
        "groups": [f"{group.type}:{group.id}" for group in user.groups],
        "role": user.role
    }


# Serve the demo frontend at root
@app.get("/")
async def serve_index():
    """Serve the demo frontend"""
    try:
        with open("public/index.html", "r") as f:
            content = f.read()
            # Fix the title to say Python instead of Express
            content = content.replace("Vortex Express SDK Demo", "Vortex Python SDK Demo")
            content = content.replace("Express SDK", "Python SDK")
            return HTMLResponse(content)
    except FileNotFoundError:
        return HTMLResponse("<h1>Demo frontend not found</h1><p>Make sure public/index.html exists</p>")


# Auth routes
@app.post("/api/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest, response: Response):
    """Login endpoint"""
    if not request.email or not request.password:
        raise HTTPException(status_code=400, detail="Email and password required")

    user = authenticate_user(request.email, request.password)
    if not user:
        return LoginResponse(success=False, error="Invalid credentials")

    session_token = create_session_jwt(user)
    response.set_cookie(
        "session",
        session_token,
        httponly=True,
        secure=os.getenv("NODE_ENV") == "production",
        samesite="lax",
        max_age=24 * 60 * 60
    )

    return LoginResponse(
        success=True,
        user={
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "groups": [group.model_dump() for group in user.groups]
        }
    )


@app.post("/api/auth/logout", response_model=LogoutResponse)
async def logout(response: Response):
    """Logout endpoint"""
    response.delete_cookie("session")
    return LogoutResponse(success=True)


@app.get("/api/auth/me")
async def get_me(current_user: Optional[DemoUser] = Depends(get_current_user)):
    """Get current user info"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    return {
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "role": current_user.role,
            "groups": [group.model_dump() for group in current_user.groups]
        }
    }


# Demo data endpoints
@app.get("/api/demo/users")
async def get_demo_users_endpoint():
    """Get demo users"""
    return {"users": get_demo_users()}


@app.get("/api/demo/protected")
async def protected_route(current_user: DemoUser = Depends(get_current_user)):
    """Protected demo route"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    return {
        "message": "This is a protected route!",
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "role": current_user.role,
            "groups": [group.model_dump() for group in current_user.groups]
        },
        "timestamp": datetime.utcnow().isoformat()
    }


# Vortex API routes - ORDERED CORRECTLY!
@app.post("/api/vortex/jwt")
async def generate_jwt(
    request: Optional[JwtRequest] = None,
    current_user: Optional[DemoUser] = Depends(get_current_user)
):
    """Generate Vortex JWT"""
    if not vortex_client:
        raise HTTPException(status_code=503, detail="Vortex SDK not available")

    try:
        if request and request.user_id and request.identifiers:
            payload = JwtPayload(
                user_id=request.user_id,
                identifiers=request.identifiers,
                groups=request.groups,
                role=request.role
            )
        elif current_user:
            vortex_user = demo_user_to_vortex_format(current_user)
            payload = JwtPayload(
                user_id=vortex_user["userId"],
                identifiers=vortex_user["identifiers"],
                groups=vortex_user["groups"],
                role=vortex_user["role"]
            )
        else:
            raise HTTPException(status_code=401, detail="Authentication required")

        jwt_token = vortex_client.generate_jwt(payload)
        return {"jwt": jwt_token}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate JWT: {str(e)}")


# IMPORTANT: Specific routes BEFORE generic ones!
@app.get("/api/vortex/invitations/by-target")
async def get_invitations_by_target_standard(
    targetType: str,
    targetValue: str,
    current_user: Optional[DemoUser] = Depends(get_current_user)
):
    """Get invitations by target (standard route)"""
    if not vortex_client:
        return {"invitations": [{"id": "demo-1", "message": "Vortex SDK not available - this is a demo response"}]}

    try:
        invitations = vortex_client.get_invitations_by_target_sync(targetType, targetValue)
        return {"invitations": [inv.model_dump() for inv in invitations]}
    except Exception as e:
        return {"invitations": [], "error": f"Demo mode: {str(e)}"}


@app.get("/api/vortex/invitations/by-group/{group_type}/{group_id}")
async def get_invitations_by_group(
    group_type: str,
    group_id: str,
    current_user: Optional[DemoUser] = Depends(get_current_user)
):
    """Get invitations by group - THIS SHOULD WORK NOW!"""
    if not vortex_client:
        return {
            "invitations": [
                {
                    "id": f"demo-group-{group_type}-{group_id}",
                    "message": f"Demo response for group {group_type}/{group_id}",
                    "note": "Vortex SDK not fully available - this is a demo response"
                }
            ]
        }

    try:
        invitations = vortex_client.get_invitations_by_group_sync(group_type, group_id)
        return {"invitations": [inv.model_dump() for inv in invitations]}
    except Exception as e:
        return {"invitations": [], "error": f"Demo mode: {str(e)}"}


@app.get("/api/vortex/invitations")
async def get_invitations_by_target_legacy(
    targetType: str,
    targetValue: str,
    current_user: Optional[DemoUser] = Depends(get_current_user)
):
    """Get invitations by target (legacy route for frontend compatibility)"""
    if not vortex_client:
        return {"invitations": [{"id": "demo-legacy", "message": f"Demo response for {targetType}={targetValue}"}]}

    try:
        invitations = vortex_client.get_invitations_by_target_sync(targetType, targetValue)
        return {"invitations": [inv.model_dump() for inv in invitations]}
    except Exception as e:
        return {"invitations": [], "error": f"Demo mode: {str(e)}"}


@app.post("/api/vortex/invitations/accept")
async def accept_invitations(
    request: AcceptInvitationsRequest,
    current_user: Optional[DemoUser] = Depends(get_current_user)
):
    """Accept invitations"""
    if not vortex_client:
        return {"message": "Demo mode - invitations would be accepted", "invitationIds": request.invitationIds}

    try:
        target = InvitationTarget(**request.target)
        result = vortex_client.accept_invitations_sync(request.invitationIds, target)
        return result
    except Exception as e:
        return {"error": f"Demo mode: {str(e)}"}


@app.post("/api/vortex/invitations/{invitation_id}/reinvite")
async def reinvite(
    invitation_id: str,
    current_user: Optional[DemoUser] = Depends(get_current_user)
):
    """Reinvite for a specific invitation"""
    if not vortex_client:
        return {"id": invitation_id, "message": "Demo mode - reinvite would be sent"}

    try:
        invitation = vortex_client.reinvite_sync(invitation_id)
        return invitation.model_dump()
    except Exception as e:
        return {"error": f"Demo mode: {str(e)}"}


@app.get("/api/vortex/invitations/{invitation_id}")
async def get_invitation(
    invitation_id: str,
    current_user: Optional[DemoUser] = Depends(get_current_user)
):
    """Get specific invitation"""
    if not vortex_client:
        return {"id": invitation_id, "message": "Demo mode - invitation details"}

    try:
        invitation = vortex_client.get_invitation_sync(invitation_id)
        return invitation.model_dump()
    except Exception as e:
        return {"error": f"Demo mode: {str(e)}"}


@app.delete("/api/vortex/invitations/{invitation_id}")
async def revoke_invitation(
    invitation_id: str,
    current_user: Optional[DemoUser] = Depends(get_current_user)
):
    """Revoke invitation"""
    if not vortex_client:
        return {"message": f"Demo mode - invitation {invitation_id} would be revoked"}

    try:
        result = vortex_client.revoke_invitation_sync(invitation_id)
        return result
    except Exception as e:
        return {"error": f"Demo mode: {str(e)}"}


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "vortex_sdk": "available" if vortex_import_ok else "not available (demo mode)",
        "auth": "minimal (SHA256 + simple JWT)",
        "routes": [
            "POST /api/vortex/jwt",
            "GET /api/vortex/invitations/by-target",
            "GET /api/vortex/invitations/by-group/{type}/{id}",
            "GET /api/vortex/invitations",
            "POST /api/vortex/invitations/accept",
            "GET /api/vortex/invitations/{id}",
            "POST /api/vortex/invitations/{id}/reinvite",
            "DELETE /api/vortex/invitations/{id}"
        ]
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))

    print(f"🚀 Vortex Python Demo (Working Version)")
    print(f"📱 Visit http://localhost:{port} to try the demo")
    print(f"📖 API docs: http://localhost:{port}/docs")
    print(f"📊 Health: http://localhost:{port}/health")
    print("")
    print("✅ No python-jose dependency required")
    print("✅ Routes properly ordered")
    print("✅ Graceful fallbacks if Vortex SDK unavailable")
    print("")
    print("Demo users:")
    print("  - admin@example.com / password123")
    print("  - user@example.com / userpass")
    print("")

    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        reload_dirs=["src"]
    )