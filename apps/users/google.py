import logging
import aiohttp
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta

from aiogoogle.client import Aiogoogle
from aiogoogle.auth.creds import UserCreds

from config.settings import SETTINGS
from apps.users.services import GoogleAuthService

logger = logging.getLogger("google")


class GoogleAPIClient:
    """Client for interacting with Google APIs."""

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.client_id = SETTINGS["google"]["client_id"]
        self.client_secret = SETTINGS["google"]["client_secret"]
        self.redirect_uri = SETTINGS["google"]["redirect_uri"]
        self.scopes = SETTINGS["google"]["scopes"]

    async def _get_credentials(self) -> Optional[UserCreds]:
        """Get user credentials for Google API."""
        auth = await GoogleAuthService.get_credentials(self.user_id)
        if not auth:
            logger.warning(f"No Google credentials found for user {self.user_id}")
            return None

        # Check if token is expired and needs refresh
        if auth.is_expired():
            logger.info(f"Token expired for user {self.user_id}, refreshing...")
            if not auth.refresh_token:
                logger.error(f"No refresh token available for user {self.user_id}")
                return None

            # Refresh token
            try:
                new_creds = await self._refresh_token(auth.refresh_token)
                if new_creds:
                    # Update stored credentials
                    await GoogleAuthService.store_credentials(
                        self.user_id,
                        new_creds["access_token"],
                        auth.refresh_token,  # Keep existing refresh token
                        datetime.now() + timedelta(seconds=new_creds["expires_in"]),
                        auth.email,
                    )

                    # Return refreshed credentials
                    return UserCreds(
                        access_token=new_creds["access_token"],
                        refresh_token=auth.refresh_token,
                        id_token=new_creds.get("id_token"),
                        token_uri="https://oauth2.googleapis.com/token",
                        client_id=self.client_id,
                        client_secret=self.client_secret,
                        scopes=self.scopes,
                        expiry=datetime.now()
                        + timedelta(seconds=new_creds["expires_in"]),
                    )
                else:
                    logger.error(f"Failed to refresh token for user {self.user_id}")
                    return None
            except Exception as e:
                logger.exception(f"Error refreshing token for user {self.user_id}: {e}")
                return None

        # Return valid credentials
        return UserCreds(
            access_token=auth.access_token,
            refresh_token=auth.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=self.scopes,
            expiry=auth.token_expiry,
        )

    async def _refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh OAuth token."""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "refresh_token": refresh_token,
                        "grant_type": "refresh_token",
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(
                            f"Token refresh failed: {response.status}, {error_text}"
                        )
                        return None
            except Exception as e:
                logger.exception(f"Exception during token refresh: {e}")
                return None

    async def get_user_info(self) -> Optional[Dict[str, Any]]:
        """Get Google user info."""
        creds = await self._get_credentials()
        if not creds:
            return None

        async with Aiogoogle(user_creds=creds) as aiogoogle:
            oauth2 = await aiogoogle.discover("oauth2", "v2")
            try:
                return await aiogoogle.as_user(oauth2.userinfo.v2.me.get())
            except Exception as e:
                logger.exception(f"Error getting user info: {e}")
                return None

    async def list_calendars(self) -> List[Dict[str, Any]]:
        """List available Google Calendars."""
        creds = await self._get_credentials()
        if not creds:
            return []

        async with Aiogoogle(user_creds=creds) as aiogoogle:
            calendar = await aiogoogle.discover("calendar", "v3")
            try:
                response = await aiogoogle.as_user(calendar.calendarList.list())
                return response.get("items", [])
            except Exception as e:
                logger.exception(f"Error listing calendars: {e}")
                return []

    async def get_calendar_events(
        self,
        calendar_id: str = "primary",
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None,
        max_results: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get events from a Google Calendar."""
        creds = await self._get_credentials()
        if not creds:
            return []

        # Default time range to today and next 7 days if not specified
        if time_min is None:
            time_min = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        if time_max is None:
            time_max = time_min + timedelta(days=7)

        # Format times for API
        time_min_str = time_min.isoformat() + "Z"  # UTC format
        time_max_str = time_max.isoformat() + "Z"  # UTC format

        async with Aiogoogle(user_creds=creds) as aiogoogle:
            calendar = await aiogoogle.discover("calendar", "v3")
            try:
                response = await aiogoogle.as_user(
                    calendar.events.list(
                        calendarId=calendar_id,
                        timeMin=time_min_str,
                        timeMax=time_max_str,
                        maxResults=max_results,
                        singleEvents=True,
                        orderBy="startTime",
                    )
                )
                return response.get("items", [])
            except Exception as e:
                logger.exception(f"Error getting calendar events: {e}")
                return []

    async def create_calendar_event(
        self,
        summary: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        calendar_id: str = "primary",
    ) -> Optional[Dict[str, Any]]:
        """Create a new calendar event."""
        creds = await self._get_credentials()
        if not creds:
            return None

        # If end_time not provided, make it 1 hour after start_time
        if end_time is None:
            end_time = start_time + timedelta(hours=1)

        # Format the event
        event = {
            "summary": summary,
            "start": {"dateTime": start_time.isoformat(), "timeZone": "UTC"},
            "end": {"dateTime": end_time.isoformat(), "timeZone": "UTC"},
        }

        if description:
            event["description"] = description

        if location:
            event["location"] = location

        async with Aiogoogle(user_creds=creds) as aiogoogle:
            calendar = await aiogoogle.discover("calendar", "v3")
            try:
                return await aiogoogle.as_user(
                    calendar.events.insert(calendarId=calendar_id, json=event)
                )
            except Exception as e:
                logger.exception(f"Error creating calendar event: {e}")
                return None

    async def update_calendar_event(
        self,
        event_id: str,
        summary: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        calendar_id: str = "primary",
    ) -> Optional[Dict[str, Any]]:
        """Update an existing calendar event."""
        creds = await self._get_credentials()
        if not creds:
            return None

        # First get the existing event
        async with Aiogoogle(user_creds=creds) as aiogoogle:
            calendar = await aiogoogle.discover("calendar", "v3")
            try:
                event = await aiogoogle.as_user(
                    calendar.events.get(calendarId=calendar_id, eventId=event_id)
                )
            except Exception as e:
                logger.exception(f"Error getting calendar event {event_id}: {e}")
                return None

        # Update fields that were provided
        if summary:
            event["summary"] = summary

        if start_time:
            event["start"] = {"dateTime": start_time.isoformat(), "timeZone": "UTC"}

        if end_time:
            event["end"] = {"dateTime": end_time.isoformat(), "timeZone": "UTC"}

        if description:
            event["description"] = description

        if location:
            event["location"] = location

        # Send the update
        async with Aiogoogle(user_creds=creds) as aiogoogle:
            calendar = await aiogoogle.discover("calendar", "v3")
            try:
                return await aiogoogle.as_user(
                    calendar.events.update(
                        calendarId=calendar_id, eventId=event_id, json=event
                    )
                )
            except Exception as e:
                logger.exception(f"Error updating calendar event {event_id}: {e}")
                return None

    async def delete_calendar_event(
        self, event_id: str, calendar_id: str = "primary"
    ) -> bool:
        """Delete a calendar event."""
        creds = await self._get_credentials()
        if not creds:
            return False

        async with Aiogoogle(user_creds=creds) as aiogoogle:
            calendar = await aiogoogle.discover("calendar", "v3")
            try:
                await aiogoogle.as_user(
                    calendar.events.delete(calendarId=calendar_id, eventId=event_id)
                )
                return True
            except Exception as e:
                logger.exception(f"Error deleting calendar event {event_id}: {e}")
                return False

    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[
            List[Tuple[str, bytes, str]]
        ] = None,  # [(filename, data, mimetype), ...]
    ) -> bool:
        """Send an email using Gmail API."""
        creds = await self._get_credentials()
        if not creds:
            return False

        import base64
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.application import MIMEApplication

        # Create message
        message = MIMEMultipart("alternative")
        message["to"] = to
        message["subject"] = subject

        if cc:
            message["cc"] = ",".join(cc)

        if bcc:
            message["bcc"] = ",".join(bcc)

        # Add plain text and HTML parts
        message.attach(MIMEText(body, "plain"))
        if html_body:
            message.attach(MIMEText(html_body, "html"))

        # Add attachments
        if attachments:
            for filename, data, mimetype in attachments:
                attachment = MIMEApplication(data)
                attachment.add_header(
                    "Content-Disposition", f"attachment; filename={filename}"
                )
                message.attach(attachment)

        # Encode message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        async with Aiogoogle(user_creds=creds) as aiogoogle:
            gmail = await aiogoogle.discover("gmail", "v1")
            try:
                await aiogoogle.as_user(
                    gmail.users.messages.send(
                        userId="me", json={"raw": encoded_message}
                    )
                )
                return True
            except Exception as e:
                logger.exception(f"Error sending email: {e}")
                return False


def get_oauth_url() -> str:
    """Generate Google OAuth URL."""
    from aiogoogle.auth.oauth2 import AuthorizationCodeFlow

    flow = AuthorizationCodeFlow(
        client_id=SETTINGS["google"]["client_id"],
        client_secret=SETTINGS["google"]["client_secret"],
        scopes=SETTINGS["google"]["scopes"],
        redirect_uri=SETTINGS["google"]["redirect_uri"],
    )

    auth_uri = flow.authorization_url(
        access_type="offline", include_granted_scopes="true", prompt="consent"
    )

    return auth_uri


async def process_oauth_callback(code: str, user_id: int) -> bool:
    """Process OAuth callback and store credentials."""
    from aiogoogle.auth.oauth2 import AuthorizationCodeFlow

    flow = AuthorizationCodeFlow(
        client_id=SETTINGS["google"]["client_id"],
        client_secret=SETTINGS["google"]["client_secret"],
        scopes=SETTINGS["google"]["scopes"],
        redirect_uri=SETTINGS["google"]["redirect_uri"],
    )

    try:
        # Exchange code for credentials
        credentials = await flow.exchange_code(code)

        # Get user info to get email
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://www.googleapis.com/oauth2/v1/userinfo",
                headers={"Authorization": f"Bearer {credentials.access_token}"},
            ) as response:
                if response.status == 200:
                    user_info = await response.json()
                    email = user_info.get("email")
                else:
                    email = None

        # Calculate expiry time
        expiry = datetime.now() + timedelta(seconds=credentials.expires_in)

        # Store credentials
        await GoogleAuthService.store_credentials(
            user_id=user_id,
            access_token=credentials.access_token,
            refresh_token=credentials.refresh_token,
            token_expiry=expiry,
            email=email,
        )

        return True
    except Exception as e:
        logger.exception(f"Error processing OAuth callback: {e}")
        return False
