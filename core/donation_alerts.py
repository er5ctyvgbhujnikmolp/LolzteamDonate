"""
DonationAlerts API integration module.
Handles authentication and sending custom alerts to DonationAlerts.
"""

import asyncio
from enum import Enum
from typing import Dict, Any, List, Optional
from urllib.parse import urlencode

import aiohttp
import requests

from . import types as api_types
from . import errors


class Scopes(Enum):
    """DonationAlerts API scopes."""
    USER_SHOW = "oauth-user-show"
    CUSTOM_ALERT_STORE = "oauth-custom_alert-store"


class DonationAlertsAPI:
    """DonationAlerts API client."""

    BASE_URL = "https://www.donationalerts.com"
    API_URL = f"{BASE_URL}/api/v1"

    def __init__(
            self,
            client_id: Optional[str] = None,
            redirect_uri: Optional[str] = None,
            scopes: Optional[List[Scopes]] = None
    ):
        """Initialize DonationAlerts API client.

        Args:
            client_id: Application client ID
            redirect_uri: Redirect URI for OAuth flow
            scopes: List of API scopes to request
        """
        self.client_id = client_id
        self.redirect_uri = redirect_uri
        self.scopes = scopes or [Scopes.USER_SHOW, Scopes.CUSTOM_ALERT_STORE]
        self.session = None
        self._queue: asyncio.Queue[api_types.AlertInfo] = asyncio.Queue()
        self._queue_task: Optional[asyncio.Task[None]] = None

    def login(self) -> str:
        """Get the OAuth authorization URL.

        Returns:
            Authorization URL for user to visit
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "token",
            "scope": " ".join([scope.value for scope in self.scopes])
        }
        return f"{self.BASE_URL}/oauth/authorize?{urlencode(params)}"

    def user(self, access_token: str) -> Dict[str, Any]:
        """Get user information.

        Args:
            access_token: Access token

        Returns:
            User information
        """
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(f"{self.API_URL}/user/oauth", headers=headers)
        response.raise_for_status()

        return response.json()

    async def verify_token(self, access_token: str) -> bool:
        """Verify if the access token is valid.
        
        Args:
            access_token: Access token to verify
            
        Returns:
            True if token is valid, False otherwise
        """
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.API_URL}/user/oauth", headers=headers) as response:
                    return response.status == 200
        except Exception:
            return False

    async def send_custom_alert(
            self, access_token: str, header: str, message: str
    ) -> Dict[str, Any]:
        """Send a custom alert to DonationAlerts.
        
        Args:
            access_token: Access token
            header: Alert header
            message: Alert message
            
        Returns:
            Response JSON
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "header": header,
        }

        if message:
            data["message"] = message

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                        f"{self.API_URL}/custom_alert",
                        headers=headers,
                        data=data
                ) as response:
                    if response.status == 201:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        raise Exception(f"Error sending alert: {response.status} - {error_text}")
        except Exception as e:
            raise errors.SendAlertException(f"Failed to send alert: {str(e)}") from e

    async def start_alert_processor(self, access_token: str) -> None:
        """Start the alert processing queue.
        
        Args:
            access_token: Access token for DonationAlerts API
        """
        if self._queue_task is not None:
            return

        self._queue_task = asyncio.create_task(self._process_alerts(access_token))

    async def stop_alert_processor(self) -> None:
        """Stop the alert processing queue."""
        if self._queue_task is not None:
            self._queue_task.cancel()
            try:
                await self._queue_task
            except asyncio.CancelledError:
                pass
            self._queue_task = None

    async def _process_alerts(self, access_token: str) -> None:
        """Process alerts from the queue.
        
        Args:
            access_token: Access token for DonationAlerts API
        """
        while True:
            try:
                alert = await self._queue.get()
                await self.send_custom_alert(
                    access_token,
                    f"{alert.username} — {alert.amount} RUB",
                    alert.message
                )
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error processing alert: {str(e)}")
            finally:
                self._queue.task_done()

    async def queue_alert(self, amount: float, username: str, message: str) -> None:
        """Queue an alert to be sent.
        
        Args:
            amount: Donation amount
            username: Username of donor
            message: Donation message
        """
        await self._queue.put(
            api_types.AlertInfo(
                amount=amount,
                username=username,
                message=message
            )
        )
