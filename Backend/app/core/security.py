from datetime import datetime, timedelta, timezone
from typing import Optional
from authlib.jose import jwt, JoseError
from authlib.jose.errors import ExpiredTokenError
from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher
from fastapi import HTTPException, status
from app.core.config import settings

# pwdlib replaces passlib — bcrypt is slow by design to resist brute-force
pwd_hasher = PasswordHash([BcryptHasher()])


def hash_password(password: str) -> str:
    return pwd_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_hasher.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a signed JWT. 'sub' = subject = customer ID.
    Authlib replaces python-jose — same concept, modern maintained library.
    """
    header = {"alg": settings.algorithm}
    payload = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload.update({"exp": expire})
    token = jwt.encode(header, payload, settings.secret_key)
    # Authlib returns bytes — decode to str for JSON serialization
    return token.decode("utf-8") if isinstance(token, bytes) else token


def decode_access_token(token: str) -> dict:
    """
    Decodes and validates JWT. Raises 401 if expired or tampered.
    """
    try:
        claims = jwt.decode(token, settings.secret_key)
        claims.validate()
        return dict(claims)
    except ExpiredTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JoseError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
# from datetime import datetime, timedelta, timezone
# from typing import Optional

# from authlib.jose import JoseError, jwt
# from pwdlib import PasswordHash

# from fastapi import HTTPException, status
# from app.core.config import settings

# # bcrypt is the hashing algorithm — slow by design to resist brute-force
# # pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# pwd_context = PasswordHash.recommended()

# def hash_password(password: str) -> str:
#     return pwd_context.hash(password)


# def verify_password(plain_password: str, hashed_password: str) -> bool:
#     return pwd_context.verify(plain_password, hashed_password)


# def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
#     """
#     Creates a signed JWT. 'sub' = subject = customer ID.
#     Token is signed with SECRET_KEY → server can verify it wasn't tampered with.
#     """
#     expire = datetime.now(timezone.utc) + (
#         expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
#     )

#     payload = data.copy()
#     payload["exp"] = expire

#     header = {"alg": settings.algorithm}

#     token = jwt.encode(
#         header,
#         payload,
#         settings.secret_key
#     )

#     return token.decode("utf-8")

# def decode_access_token(token: str) -> dict:
#     """
#     Decode and validate JWT.
#     Raises HTTP 401 if invalid or expired.
#     """
#     try:

#         claims = jwt.decode(
#             token,
#             settings.secret_key
#         )

#         claims.validate()

#         return dict(claims)

#     except JoseError:

#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid or expired token",
#             headers={"WWW-Authenticate": "Bearer"},
#         )