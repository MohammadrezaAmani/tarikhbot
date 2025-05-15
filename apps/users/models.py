from typing import Dict, List, Optional, Union
from database.models import User, GoogleAuth
from tortoise.exceptions import DoesNotExist
from datetime import datetime, timezone

# These are just model functions that leverage the tortoise-orm models
# They provide a higher-level interface for working with user data

async def get_user_by_telegram_id(telegram_id: int) -> Optional[User]:
    """Get a user by Telegram ID."""
    try:
        return await User.get(telegram_id=telegram_id)
    except DoesNotExist:
        return None

async def create_user(
    telegram_id: int,
    first_name: str,
    last_name: Optional[str] = None,
    username: Optional[str] = None,
    language_code: str = "en",
) -> User:
    """Create a new user."""
    return await User.create(
        telegram_id=telegram_id,
        first_name=first_name,
        last_name=last_name,
        username=username,
        language_code=language_code,
        preferences={}
    )

async def get_or_create_user(
    telegram_id: int,
    first_name: str,
    last_name: Optional[str] = None,
    username: Optional[str] = None,
    language_code: str = "en",
) -> Union[User, bool]:
    """Get a user by Telegram ID or create it if it doesn't exist.
    
    Returns:
        Tuple with (user, created) where created is a boolean indicating
        if the user was created.
    """
    user = await get_user_by_telegram_id(telegram_id)
    
    if user:
        # Update user info in case it changed
        if (user.first_name != first_name or 
            user.last_name != last_name or 
            user.username != username or
            user.language_code != language_code):
            
            user.first_name = first_name
            user.last_name = last_name
            user.username = username
            user.language_code = language_code
            await user.save()
        
        return user, False
    
    user = await create_user(
        telegram_id=telegram_id,
        first_name=first_name,
        last_name=last_name,
        username=username,
        language_code=language_code,
    )
    
    return user, True

async def update_user_preferences(user: User, preferences: Dict) -> User:
    """Update user preferences."""
    if not user.preferences:
        user.preferences = {}
        
    # Merge new preferences with existing ones
    user.preferences.update(preferences)
    await user.save()
    return user

async def store_google_auth(
    user: User,
    access_token: str,
    refresh_token: Optional[str],
    token_expiry: datetime,
    email: Optional[str] = None,
) -> GoogleAuth:
    """Store Google OAuth credentials for a user."""
    try:
        # Try to update existing auth
        google_auth = await GoogleAuth.get(user=user)
        google_auth.access_token = access_token
        
        if refresh_token:  # Only update refresh_token if provided
            google_auth.refresh_token = refresh_token
            
        google_auth.token_expiry = token_expiry
        
        if email:
            google_auth.email = email
            
        await google_auth.save()
        return google_auth
    except DoesNotExist:
        # Create new auth
        return await GoogleAuth.create(
            user=user,
            access_token=access_token,
            refresh_token=refresh_token,
            token_expiry=token_expiry,
            email=email,
        )

async def get_google_auth(user: User) -> Optional[GoogleAuth]:
    """Get Google OAuth credentials for a user."""
    try:
        return await GoogleAuth.get(user=user)
    except DoesNotExist:
        return None

async def update_google_sync_settings(
    user: User, 
    calendar_sync: Optional[bool] = None,
    gmail_sync: Optional[bool] = None
) -> Optional[GoogleAuth]:
    """Update Google sync settings for a user."""
    try:
        google_auth = await GoogleAuth.get(user=user)
        
        if calendar_sync is not None:
            google_auth.calendar_sync_enabled = calendar_sync
            
        if gmail_sync is not None:
            google_auth.gmail_sync_enabled = gmail_sync
            
        await google_auth.save()
        return google_auth
    except DoesNotExist:
        return None