from fastapi import Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.security import OAuth2PasswordBearer

from app.core.security import decode_access_token
from app.db.session import SessionDep
from app.modules.users.models import Role, User
from app.modules.users.repo import get_user_by_id

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    session: SessionDep,
    token: str = Depends(oauth2_scheme),
) -> User:
    user_id = decode_access_token(token)
    user = await get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    return user


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != Role.ADMIN.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return current_user


async def require_driver(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != Role.DRIVER.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return current_user


async def get_current_user_websocket(
    websocket: WebSocket, session: SessionDep
) -> User:
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise WebSocketDisconnect("Missing token")
    
    try:
        user_id = decode_access_token(token)
    except HTTPException:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise WebSocketDisconnect("Invalid token")
    
    user = await get_user_by_id(session, user_id)
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise WebSocketDisconnect("Invalid credentials")
    
    return user 