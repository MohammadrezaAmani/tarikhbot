from typing import Dict, List, Optional, Union, Any
import logging
import datetime
from tortoise.exceptions import DoesNotExist

from apps.users.models import (
    get_user_by_telegram_id,
    get_or_create_user,
    update_user_preferences,
    store_google_auth,
    get_google_auth,
    update_google_sync_settings
)
from database.models import User, GoogleAuth

logger = logging.getLogger("users")

class UserService:
    """Service for user management."""
    
    @staticmethod
    async def get_user(telegram_id: int) -> Optional[User]:
        """Get a user by Telegram ID."""
        return await get_user_by_telegram_id(telegram_id)
    
    @staticmethod
    async def register_user(
        telegram_id: int,
        first_name: str,
        last_name: Optional[str] = None,
        username: Optional[str] = None,
        language_code: str = "en",
    ) -> tuple[User, bool]:
        """Register a new user or update existing one."""
        logger.info(f"Registering user: {telegram_id}, {first_name} {last_name}")
        return await get_or_create_user(
            telegram_id=telegram_id,
            first_name=first_name,
            last_name=last_name,
            username=username,
            language_code=language_code,
        )
    
    @staticmethod
    async def update_preferences(user_id: int, preferences: Dict) -> Optional[User]:
        """Update user preferences."""
        user = await get_user_by_telegram_id(user_id)
        if not user:
            logger.warning(f"Tried to update preferences for non-existent user: {user_id}")
            return None
        
        logger.info(f"Updating preferences for user {user_id}: {preferences}")
        return await update_user_preferences(user, preferences)
    
    @staticmethod
    async def set_timezone(user_id: int, timezone: str) -> Optional[User]:
        """Set user's timezone."""
        user = await get_user_by_telegram_id(user_id)
        if not user:
            logger.warning(f"Tried to set timezone for non-existent user: {user_id}")
            return None
        
        logger.info(f"Setting timezone for user {user_id}: {timezone}")
        user.timezone = timezone
        await user.save()
        return user
    
    @staticmethod
    async def set_language(user_id: int, language_code: str) -> Optional[User]:
        """Set user's language."""
        user = await get_user_by_telegram_id(user_id)
        if not user:
            logger.warning(f"Tried to set language for non-existent user: {user_id}")
            return None
        
        logger.info(f"Setting language for user {user_id}: {language_code}")
        user.language_code = language_code
        await user.save()
        return user
    
    @staticmethod
    async def toggle_premium(user_id: int, is_premium: bool) -> Optional[User]:
        """Toggle premium status for a user."""
        user = await get_user_by_telegram_id(user_id)
        if not user:
            logger.warning(f"Tried to toggle premium for non-existent user: {user_id}")
            return None
        
        logger.info(f"Setting premium status for user {user_id}: {is_premium}")
        user.is_premium = is_premium
        await user.save()
        return user
    
    @staticmethod
    async def get_user_profile(user_id: int) -> Optional[Dict[str, Any]]:
        """Get user profile information."""
        user = await get_user_by_telegram_id(user_id)
        if not user:
            logger.warning(f"Tried to get profile for non-existent user: {user_id}")
            return None
        
        # Get Google auth status
        google_auth = await get_google_auth(user)
        
        # Count user's tasks
        task_count = await user.tasks.all().count()
        
        # Get additional stats as needed
        
        return {
            "id": user.id,
            "telegram_id": user.telegram_id,
            "name": f"{user.first_name} {user.last_name or ''}".strip(),
            "username": user.username,
            "language": user.language_code,
            "timezone": user.timezone,
            "is_premium": user.is_premium,
            "preferences": user.preferences,
            "google_connected": google_auth is not None,
            "google_email": google_auth.email if google_auth else None,
            "joined_at": user.created_at.isoformat(),
            "stats": {
                "task_count": task_count,
                # Add more stats as needed
            }
        }


class GoogleAuthService:
    """Service for Google OAuth authentication and API integration."""
    
    @staticmethod
    async def get_google_auth(user_id: int) -> Optional[Dict[str, Any]]:
        """Get Google OAuth info for a user."""
        google_auth = await GoogleAuthService.get_credentials(user_id)
        if not google_auth:
            return None
            
        return {
            "email": google_auth.email,
            "calendar_sync_enabled": google_auth.calendar_sync_enabled,
            "gmail_sync_enabled": google_auth.gmail_sync_enabled,
            "token_expiry": google_auth.token_expiry
        }
    
    @staticmethod
    async def store_credentials(
        user_id: int,
        access_token: str,
        refresh_token: Optional[str],
        token_expiry: datetime.datetime,
        email: Optional[str] = None,
    ) -> Optional[GoogleAuth]:
        """Store Google OAuth credentials for a user."""
        user = await get_user_by_telegram_id(user_id)
        if not user:
            logger.warning(f"Tried to store Google credentials for non-existent user: {user_id}")
            return None
        
        logger.info(f"Storing Google credentials for user {user_id}")
        return await store_google_auth(
            user=user,
            access_token=access_token,
            refresh_token=refresh_token,
            token_expiry=token_expiry,
            email=email,
        )
    
    @staticmethod
    async def get_credentials(user_id: int) -> Optional[GoogleAuth]:
        """Get Google OAuth credentials for a user."""
        user = await get_user_by_telegram_id(user_id)
        if not user:
            logger.warning(f"Tried to get Google credentials for non-existent user: {user_id}")
            return None
        
        return await get_google_auth(user)
    
    @staticmethod
    async def update_sync_settings(
        user_id: int,
        calendar_sync: Optional[bool] = None,
        gmail_sync: Optional[bool] = None,
    ) -> bool:
        """Update Google sync settings for a user."""
        user = await get_user_by_telegram_id(user_id)
        if not user:
            logger.warning(f"Tried to update Google sync settings for non-existent user: {user_id}")
            return False
        
        logger.info(f"Updating Google sync settings for user {user_id}: calendar={calendar_sync}, gmail={gmail_sync}")
        result = await update_google_sync_settings(user, calendar_sync, gmail_sync)
        return result is not None
    
    @staticmethod
    async def is_google_connected(user_id: int) -> bool:
        """Check if the user has connected Google account."""
        user = await get_user_by_telegram_id(user_id)
        if not user:
            return False
        
        google_auth = await get_google_auth(user)
        return google_auth is not None
    
    @staticmethod
    async def is_token_valid(user_id: int) -> bool:
        """Check if the user's Google token is valid and not expired."""
        user = await get_user_by_telegram_id(user_id)
        if not user:
            return False
        
        google_auth = await get_google_auth(user)
        if not google_auth:
            return False
            
        # Check if token is expired
        now = datetime.datetime.now(datetime.timezone.utc)
        return now < google_auth.token_expiry
    
    @staticmethod
    async def google_disconnect(user_id: int) -> bool:
        """Disconnect Google account from user."""
        user = await get_user_by_telegram_id(user_id)
        if not user:
            logger.warning(f"Tried to disconnect Google for non-existent user: {user_id}")
            return False
        
        try:
            google_auth = await GoogleAuth.get(user=user)
            await google_auth.delete()
            logger.info(f"Disconnected Google account for user {user_id}")
            return True
        except DoesNotExist:
            logger.warning(f"Tried to disconnect non-existent Google auth for user: {user_id}")
            return False