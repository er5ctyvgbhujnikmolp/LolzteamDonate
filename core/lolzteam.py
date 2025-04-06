import logging
import time
from typing import Dict, Any, List

import httpx

logger = logging.getLogger("LolzteamAPI")

class LolzteamAPI:
    """LOLZTEAM API client."""

    BASE_URL = "https://lolz.live"
    MARKET_URL = "https://prod-api.lzt.market"
    FORUM_URL = "https://prod-api.lolz.live"

    def __init__(self, client_id: str = None, redirect_uri: str = None, access_token: str = None):
        """Initialize LOLZTEAM API client.

        Args:
            client_id: Application client ID
            redirect_uri: Redirect URI for OAuth flow
            access_token: Access token
        """
        self.client_id = client_id
        self.redirect_uri = redirect_uri
        self.access_token = access_token
        self._http_client = None
        self.logger = logging.getLogger("LolzteamAPI")

    def get_auth_url(self) -> str:
        """Get the OAuth authorization URL.

        Returns:
            Authorization URL for user to visit
        """
        # Using a different construction method to avoid HTTP2 protocol errors
        params = {
            "client_id": self.client_id,
            "response_type": "token",
            "scope": "payment basic"
        }

        # Construct the URL manually to avoid URL encoding issues
        query_string = "&".join([f"{key}={value}" for key, value in params.items()])
        auth_url = f"{self.BASE_URL}/account/authorize?{query_string}"
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
                follow_redirects=True,
                http2=False  # Explicitly disable HTTP/2 to avoid protocol errors
            )
        return self._http_client

    async def get_user_info(self) -> Dict[str, Any]:
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
            response = await client.get(f"{self.FORUM_URL}/users/me", headers=headers)
            response.raise_for_status()
            data = response.json()
            username = data.get("user", {}).get("username", "unknown")
            self.logger.info(f"Got user info for {username}")
            return data
        except httpx.HTTPStatusError as e:
            self.logger.error(f"HTTP error getting user info: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Failed to get user info: {e}")
        except Exception as e:
            self.logger.error(f"Error getting user info: {str(e)}")
            raise

    async def get_payment_history(self, min_amount: int = 1) -> List[Dict[str, Any]]:
        """Get payment history.

        Args:
            min_amount: Minimum payment amount

        Returns:
            List of payments

        Raises:
            Exception: If the request fails or token is not set
        """
        if not self.access_token:
            raise ValueError("Access token not set")

        self.logger.info(f"Getting payment history with min_amount={min_amount}")
        client = await self._get_http_client()
        headers = {"Authorization": f"Bearer {self.access_token}"}

        params = {
            "type": "receiving_money",
            "pmin": min_amount,
            "show_payment_stats": "false",
            "is_hold": "false",
        }

        try:
            response = await client.get(
                f"{self.MARKET_URL}/user/payments",
                params=params,
                headers=headers
            )
            response.raise_for_status()
            data = response.json()

            if "payments" not in data:
                self.logger.warning(f"Unexpected API response structure: 'payments' key not found in: {data.keys()}")
                return []

            payments = self._process_payment_data(data)
            self.logger.info(f"Got {len(payments)} payments")
            return payments
        except httpx.HTTPStatusError as e:
            self.logger.error(f"HTTP error getting payment history: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Failed to get payment history: {e}")
        except Exception as e:
            self.logger.error(f"Error getting payment history: {str(e)}")
            raise

    def _process_payment_data(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process payment data from the API response.

        Args:
            data: Raw payment data from API

        Returns:
            Processed list of payments
        """
        payments = []
        payments_data = data.get("payments", {})

        # If payments_data is a dict, convert it to a list
        if isinstance(payments_data, dict):
            for payment_id, payment_data in payments_data.items():
                try:
                    # Process amount to clean format
                    incoming_sum = payment_data.get("incoming_sum", 0)
                    if isinstance(incoming_sum, float) and incoming_sum.is_integer():
                        incoming_sum = str(int(incoming_sum))
                    else:
                        incoming_sum = str(incoming_sum).rstrip('0').rstrip('.')

                    # Extract user data
                    data_section = payment_data.get("data", {})
                    if not isinstance(data_section, dict):
                        data_section = {}

                    payment_info = {
                        "id": payment_id,
                        "amount": incoming_sum,
                        "username": data_section.get("username", "Неизвестно"),
                        "comment": data_section.get("commentPlain", ""),
                        "datetime": payment_data.get("operation_date", int(time.time()))
                    }
                    payments.append(payment_info)
                except Exception as e:
                    self.logger.error(f"Error processing payment {payment_id}: {str(e)}")
        else:
            self.logger.warning(f"Unexpected payments data type: {type(payments_data)}")

        return list(reversed(payments))

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
            response = await client.get(f"{self.FORUM_URL}/users/me", headers=headers)
            valid = response.status_code == 200
            self.logger.info(f"Token is {'valid' if valid else 'invalid'}")
            return valid
        except Exception as e:
            self.logger.error(f"Error verifying token: {str(e)}")
            return False

    async def close(self) -> None:
        """Close the HTTP client and cleanup resources."""
        if self._http_client and not self._http_client.is_closed:
            self.logger.info("Closing HTTP client")
            await self._http_client.aclose()
            self._http_client = None
