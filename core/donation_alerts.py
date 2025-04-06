import asyncio
import logging
from enum import Enum
from typing import Dict, Any, List
from urllib.parse import urlencode

import httpx

logger = logging.getLogger("DonationAlertsAPI")


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
            client_id: str = None,
            redirect_uri: str = None,
            scopes: List[Scopes] = None,
            access_token: str = None
    ):
        """Initialize DonationAlerts API client.

        Args:
            client_id: Application client ID
            redirect_uri: Redirect URI for OAuth flow
            scopes: List of API scopes to request
            access_token: Access token for authentication
        """
        self.client_id = client_id
        self.redirect_uri = redirect_uri
        self.scopes = scopes or [Scopes.USER_SHOW, Scopes.CUSTOM_ALERT_STORE]
        self.access_token = access_token
        self._http_client = None
        self._queue = asyncio.Queue()
        self._queue_task = None
        self.logger = logging.getLogger("DonationAlertsAPI")

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
        auth_url = f"{self.BASE_URL}/oauth/authorize?{urlencode(params)}"
        self.logger.info(f"Generated auth URL: {auth_url}")
        return auth_url

    def set_access_token(self, token: str) -> None:
        """Set the access token.
        
        Args:
            token: Access token
        """
        self.access_token = token
        self.logger.info("Access token updated")

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client.
        
        Returns:
            Async HTTP client
        """
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=30.0,
                follow_redirects=True
            )
        return self._http_client

    async def user(self) -> Dict[str, Any]:
        """Get user information.

        Returns:
            User information

        Raises:
            Exception: If the request fails or token is not set
        """
        if not self.access_token:
            raise ValueError("Access token not set")

        self.logger.info("Getting user information")
        client = await self._get_http_client()
        headers = {"Authorization": f"Bearer {self.access_token}"}

        try:
            response = await client.get(f"{self.API_URL}/user/oauth", headers=headers)
            response.raise_for_status()
            data = response.json()
            self.logger.info(f"Got user info for {data.get('data', {}).get('name', 'unknown')}")
            return data
        except httpx.HTTPStatusError as e:
            self.logger.error(f"HTTP error getting user info: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Failed to get user info: {e}")
        except Exception as e:
            self.logger.error(f"Error getting user info: {str(e)}")
            raise

    async def verify_token(self) -> bool:
        """Verify if the access token is valid.
            
        Returns:
            True if token is valid, False otherwise
        """
        if not self.access_token:
            self.logger.warning("Cannot verify token: no token set")
            return False

        try:
            self.logger.info("Verifying access token")
            client = await self._get_http_client()
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = await client.get(f"{self.API_URL}/user/oauth", headers=headers)
            valid = response.status_code == 200
            self.logger.info(f"Token is {'valid' if valid else 'invalid'}")
            return valid
        except Exception as e:
            self.logger.error(f"Error verifying token: {str(e)}")
            return False

    async def send_custom_alert(self, header: str, message: str) -> Dict[str, Any]:
        """Send a custom alert to DonationAlerts.
        
        Args:
            header: Alert header
            message: Alert message
            
        Returns:
            Response JSON

        Raises:
            Exception: If the request fails or token is not set
        """
        if not self.access_token:
            raise ValueError("Access token not set")

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "header": header,
        }

        if message:
            data["message"] = message

        try:
            self.logger.info(f"Sending custom alert: {header}")
            client = await self._get_http_client()
            response = await client.post(
                f"{self.API_URL}/custom_alert",
                headers=headers,
                data=data
            )

            if response.status_code == 201:
                self.logger.info("Custom alert sent successfully")
                return response.json()
            else:
                self.logger.error(f"Error sending alert: {response.status_code} - {response.text}")
                raise Exception(f"Error sending alert: {response.status_code} - {response.text}")
        except Exception as e:
            self.logger.error(f"Failed to send alert: {str(e)}")
            raise Exception(f"Failed to send alert: {str(e)}")

    async def start_alert_processor(self) -> None:
        """Start the alert processing queue."""
        if not self.access_token:
            self.logger.error("Cannot start alert processor: no access token")
            return

        if self._queue_task is not None:
            self.logger.info("Alert processor already started")
            return

        self.logger.info("Starting alert processor")
        self._queue_task = asyncio.create_task(self._process_alerts())

    async def stop_alert_processor(self) -> None:
        """Stop the alert processing queue."""
        if self._queue_task is not None:
            self.logger.info("Stopping alert processor")
            self._queue_task.cancel()
            try:
                await self._queue_task
            except asyncio.CancelledError:
                pass
            self._queue_task = None
            self.logger.info("Alert processor stopped")

    async def _process_alerts(self) -> None:
        """Process alerts from the queue."""
        self.logger.info("Alert processor running")
        while True:
            try:
                alert = await self._queue.get()
                self.logger.info(f"Processing alert from {alert['username']} - {alert['amount']} RUB")
                await self.send_custom_alert(
                    f"{alert['username']} — {alert['amount']} RUB",
                    alert['message']
                )
            except asyncio.CancelledError:
                self.logger.info("Alert processor task cancelled")
                break
            except Exception as e:
                self.logger.error(f"Error processing alert: {str(e)}")
            finally:
                self._queue.task_done()

    async def queue_alert(self, amount: float, username: str, message: str) -> None:
        """Queue an alert to be sent.
        
        Args:
            amount: Donation amount
            username: Username of donor
            message: Donation message
        """
        self.logger.info(f"Queueing alert: {username} - {amount} RUB")
        await self._queue.put({
            "amount": amount,
            "username": username,
            "message": message
        })

    async def close(self) -> None:
        """Close the HTTP client and cleanup resources."""
        if self._http_client and not self._http_client.is_closed:
            self.logger.info("Closing HTTP client")
            await self._http_client.aclose()
            self._http_client = None

        # Ensure alert processor is stopped
        await self.stop_alert_processor()
