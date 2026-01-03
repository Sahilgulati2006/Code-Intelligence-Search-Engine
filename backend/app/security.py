# app/security.py
"""Authentication and security utilities."""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status, Header
from jose import JWTError, jwt
import logging

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class APIKeyAuth:
    """API Key authentication handler."""

    @staticmethod
    def verify_api_key(x_api_key: str = Header(None)) -> str:
        """
        Verify API key from X-API-Key header.

        Args:
            x_api_key: API key from request header

        Returns:
            API key if valid

        Raises:
            HTTPException: If API key is invalid or missing
        """
        if not settings.AUTH_ENABLED:
            return None

        if not x_api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key missing. Provide X-API-Key header.",
            )

        # Check if API key exists in configured keys
        if not settings.API_KEYS:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="API keys not configured on server.",
            )

        # Check if the key is valid (format: "key_name:secret")
        # For now, we accept any key that matches the pattern
        if ":" not in x_api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key format. Use 'key_name:secret'.",
            )

        key_name, key_secret = x_api_key.split(":", 1)

        # Verify the API key against configured keys
        if key_name not in settings.API_KEYS or settings.API_KEYS[key_name] != key_secret:
            logger.warning(f"Invalid API key attempted: {key_name}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key.",
            )

        logger.info(f"API key authenticated: {key_name}")
        return key_name


class JWTAuth:
    """JWT token authentication handler."""

    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a JWT access token.

        Args:
            data: Payload data to encode
            expires_delta: Optional expiration time delta

        Returns:
            Encoded JWT token

        Raises:
            ValueError: If JWT_SECRET is not configured
        """
        if not settings.JWT_SECRET:
            raise ValueError("JWT_SECRET must be configured to use JWT authentication")

        to_encode = data.copy()

        # Set expiration
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)

        to_encode.update({"exp": expire})

        # Encode JWT
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM,
        )

        return encoded_jwt

    @staticmethod
    def verify_token(token: str = Header(None, alias="Authorization")) -> Dict[str, Any]:
        """
        Verify and decode JWT token.

        Args:
            token: JWT token from Authorization header (format: "Bearer <token>")

        Returns:
            Decoded token payload

        Raises:
            HTTPException: If token is invalid or expired
        """
        if not settings.AUTH_ENABLED:
            return {}

        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing. Use Authorization: Bearer <token>",
            )

        # Extract token from "Bearer <token>" format
        try:
            scheme, credentials = token.split()
            if scheme.lower() != "bearer":
                raise ValueError("Invalid scheme")
            token_to_decode = credentials
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format. Use 'Bearer <token>'",
            )

        try:
            payload = jwt.decode(
                token_to_decode,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM],
            )
            return payload
        except JWTError as e:
            logger.warning(f"Invalid token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token.",
            )


class SecureIndexing:
    """Security utilities for indexing endpoints."""

    @staticmethod
    def require_auth(
        api_key: Optional[str] = Depends(APIKeyAuth.verify_api_key),
    ) -> str:
        """
        Dependency to enforce authentication on indexing endpoints.

        Args:
            api_key: Verified API key from request

        Returns:
            The API key (for logging/tracking)

        Raises:
            HTTPException: If not authenticated
        """
        if settings.AUTH_ENABLED and not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required for this endpoint.",
            )
        return api_key


def get_authenticated_user(api_key: str = Depends(APIKeyAuth.verify_api_key)) -> Optional[str]:
    """
    Dependency for authenticated endpoints.

    Returns the authenticated user/API key name.
    """
    return api_key
