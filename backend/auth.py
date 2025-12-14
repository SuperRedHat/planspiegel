from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Depends, Request, Response, status
from jose import jwt, JWTError, ExpiredSignatureError
from passlib.context import CryptContext
from pydantic import BaseModel, ValidationError, Field
from starlette.responses import RedirectResponse

from constants import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY, CLIENT_ID, CLIENT_SECRET, FRONTEND_URL
from lib.postgres_db import yield_db
from lib.redis_db import revoke_token, check_token_revoked, redis_for_session
from lib.utils import extract_hostname, is_running_in_docker
from models import db_user_by_email
from models.user import db_save_user, db_save_user_via_provider, User, db_user_by_id

# ROUTE PROTECTION: "_: dict = Depends(verify_jwt)"


# region PASSWORD
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


# endregion

# region TOKEN
class TokenData(BaseModel):
    sub: str  # standard name for user_id
    email: str


class TokenDataFulfilled(BaseModel):
    sub: int  # standard name for user_id
    exp: int
    email: str


def create_access_token(data: TokenData) -> str:
    to_encode = data.model_dump()
    utc_now = datetime.now(timezone.utc)
    expire = utc_now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


AUTHORIZATION_COOKIE = "access_token"


def set_token_to_cookie(response: Response, token: str, domain: str | None = None):
    response.set_cookie(
        key=AUTHORIZATION_COOKIE,
        value=token,
        httponly=True,
        domain=domain,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        secure=True,
        samesite="None"
    )


def get_token_from_cookie(request: Request) -> str:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token not found in cookies",
        )
    return token


async def verify_jwt(token: str = Depends(get_token_from_cookie)) -> TokenDataFulfilled:
    if await check_token_revoked(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return TokenDataFulfilled(**payload)
    except (ExpiredSignatureError, JWTError, ValidationError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


# endregion

# region ROUTES
class UserCreate(BaseModel):
    email: str = Field(default="example@gmail.com")
    password: str = Field(default="qwerty")


class UserLogin(BaseModel):
    email: str = Field(default="example@gmail.com")
    password: str = Field(default="qwerty")


class Token(BaseModel):
    access_token: str
    token_type: str


class ClaimsResponse(BaseModel):  # Define the response model
    message: str
    user: TokenDataFulfilled



router = APIRouter()


@router.get("/claims", response_model=ClaimsResponse)
async def claims(user: TokenDataFulfilled = Depends(verify_jwt)):
    return ClaimsResponse(message="You have access", user=user)


@router.get("/user", response_model=User)
async def get_user(user: TokenDataFulfilled = Depends(verify_jwt), db=Depends(yield_db)):
    return await db_user_by_id(user_id=user.sub, db=db)


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register_user(response: Response, user: UserCreate, db=Depends(yield_db)):
    hashed_password = get_password_hash(user.password)
    saved_user = await db_save_user(User(email=user.email, hashed_password=hashed_password), db)

    token = create_access_token(TokenData(sub=str(saved_user.user_id), email=user.email))
    set_token_to_cookie(response, token)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/login", response_model=Token)
async def login(response: Response, user: UserLogin, db=Depends(yield_db)):
    db_user = await db_user_by_email(user.email, db)
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect email or password")

    token = create_access_token(TokenData(sub=str(db_user.user_id), email=db_user.email))
    set_token_to_cookie(response, token)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/logout")
async def logout(request: Request, response: Response, _: dict = Depends(verify_jwt)):
    token = get_token_from_cookie(request)
    await revoke_token(token)
    response.delete_cookie(key="access_token", httponly=True, samesite="None")
    request.session.clear()
    return {"msg": "Token revoked"}
# endregion

# region GOOGLE AUTH
import time
import secrets
from authlib.integrations.starlette_client import OAuth


async def generate_state():
    state = secrets.token_urlsafe(16)
    expires_in = ACCESS_TOKEN_EXPIRE_MINUTES * 60
    await redis_for_session.setex(f"oauth-state:{state}", expires_in, time.time())
    return state


async def verify_state(state):
    key = f"oauth-state:{state}"
    exists = await redis_for_session.exists(key)
    if not exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired state")
    await redis_for_session.delete(key)


oauth = OAuth()
oauth.register(
    name="google",
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


# URL for auth start
@router.get("/google-login")
async def google_login(request: Request):
    redirect_uri = request.url_for("google_callback")
    print("is_running_in_docker()", is_running_in_docker())
    if is_running_in_docker():
        redirect_uri = redirect_uri.replace(path="/api/auth/google-callback")
    print("redirect_url: ", redirect_uri)
    state = await generate_state()
    return await oauth.google.authorize_redirect(request, redirect_uri, state=state)


# Callback URL for handle response from Google
@router.get("/google-callback", name="google_callback", include_in_schema=False)
async def google_callback(request: Request, db=Depends(yield_db)):
    # verify state
    state = request.query_params.get("state")
    if not state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="State is missing")
    await verify_state(state)

    # Get email
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get("userinfo")
    if not user_info or "email" not in user_info:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to fetch user info")

    saved_user = await db_save_user_via_provider(email=user_info.email, db=db)
    token = create_access_token(TokenData(sub=str(saved_user.user_id), email=user_info.email))
    redirect_url = f"{FRONTEND_URL}?token={token}"
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)


class SetCookieRequest(BaseModel):
    token: str


@router.post("/google-set-cookie")
async def set_cookie(request: SetCookieRequest, response: Response):
    token = request.token
    await verify_jwt(token)
    host = extract_hostname(FRONTEND_URL)
    set_token_to_cookie(response, token, host)
    return {"message": "Cookie set successfully"}
# endregion
