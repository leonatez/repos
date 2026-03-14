import logging
from fastapi import HTTPException, Header, status
from typing import Optional
from database import supabase, supabase_service

logger = logging.getLogger("auth")


async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        logger.warning("Auth failed: missing or malformed Authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.removeprefix("Bearer ").strip()
    logger.debug(f"Verifying JWT (first 20 chars): {token[:20]}...")

    try:
        response = supabase.auth.get_user(token)
        if not response or not response.user:
            logger.warning("Auth failed: get_user returned no user")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )
        logger.debug(f"JWT verified — user: {response.user.email} ({response.user.id})")
        return {"id": str(response.user.id), "email": response.user.email}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Auth failed — get_user raised: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate token: {str(e)}",
        )


async def get_optional_user(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.removeprefix("Bearer ").strip()
    try:
        response = supabase.auth.get_user(token)
        if response and response.user:
            return {"id": str(response.user.id), "email": response.user.email}
    except Exception as e:
        logger.debug(f"Optional auth — token invalid: {e}")
    return None


async def get_admin_user(authorization: Optional[str] = Header(None)) -> dict:
    user = await get_current_user(authorization)
    logger.debug(f"Checking admin role for user {user['email']} ({user['id']})")

    try:
        result = (
            supabase_service.table("users")
            .select("role")
            .eq("id", user["id"])
            .single()
            .execute()
        )
        logger.debug(f"Role query result: {result.data}")

        if not result.data or result.data.get("role") != "admin":
            logger.warning(
                f"Admin check failed for {user['email']} — "
                f"row={result.data!r}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Admin role check raised: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Could not verify admin role: {str(e)}",
        )

    logger.info(f"Admin verified: {user['email']}")
    return user
