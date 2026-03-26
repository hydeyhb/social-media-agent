from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from app.config import get_settings
from app.services.auth_service import create_access_token, decode_access_token, verify_password

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/admin/login")


async def get_current_admin(token: str = Depends(oauth2_scheme)) -> str:
    username = decode_access_token(token)
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return username


@router.post("/login")
async def admin_login(form_data: OAuth2PasswordRequestForm = Depends()):
    settings = get_settings()
    if (
        form_data.username != settings.admin_username
        or not verify_password(form_data.password, settings.admin_password)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="帳號或密碼錯誤",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(form_data.username)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me")
async def admin_me(current_user: str = Depends(get_current_admin)):
    return {"username": current_user}
