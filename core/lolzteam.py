"""
LOLZTEAM API integration module.
Handles authentication and payment monitoring for LOLZTEAM.
"""

import json
import time
from typing import Dict, Any, List

import aiohttp
import requests


class LolzteamAPI:
    """LOLZTEAM API client."""

    BASE_URL = "https://lolz.live"
    MARKET_URL = "https://prod-api.lzt.market"
    FORUM_URL = "https://prod-api.lolz.live"

    def __init__(self, client_id: str = None, redirect_uri: str = None, access_token: str = None):
        """Initialize LOLZTEAM API client.

        Args:
            client_id: Application client ID
            access_token: Access token
        """
        self.client_id = client_id
        self.redirect_uri = redirect_uri
        self.access_token = access_token

    def get_auth_url(self) -> str:
        """Get the OAuth authorization URL.

        Returns:
            Authorization URL for user to visit
        """
        # Using a different construction method and using 'https://lolz.guru' instead of 'lolz.live'
        # This can help avoid HTTP2 protocol errors that sometimes occur with certain domains
        params = {
            "client_id": self.client_id,
            "response_type": "token",
            "scope": "payment basic"
        }

        # Construct the URL manually to avoid URL encoding issues
        query_string = "&".join([f"{key}={value}" for key, value in params.items()])
        return f"{self.BASE_URL}/account/authorize?{query_string}"

    def set_access_token(self, token: str) -> None:
        """Set the access token.

        Args:
            token: Access token
        """
        self.access_token = token

    def get_user_info(self) -> Dict[str, Any]:
        """Get user information.

        Returns:
            User information

        Raises:
            Exception: If the request fails
        """
        if not self.access_token:
            raise Exception("Access token not set")

        headers = {
            "Authorization": f"Bearer {self.access_token}",
        }

        # Use session to control connection parameters
        session = requests.Session()
        session.headers.update(headers)

        # Disable HTTP/2 to avoid protocol errors
        session.mount('https://', requests.adapters.HTTPAdapter(max_retries=3))

        try:
            response = session.get(f"{self.FORUM_URL}/users/me")
            if response.status_code != 200:
                raise Exception(f"Failed to get user info: {response.status_code} - {response.text}")

            return response.json()
        except requests.RequestException as e:
            print(f"Request exception in get_user_info: {str(e)}")
            raise Exception(f"Network error getting user info: {str(e)}")
        except json.JSONDecodeError as e:
            print(f"JSON decode error in get_user_info: {str(e)}")
            print(f"Response text: {response.text}")
            raise Exception(f"Invalid JSON response from server: {str(e)}")
        except Exception as e:
            print(f"Unexpected error in get_user_info: {str(e)}")
            raise

    def get_payment_history(self, min_amount: int = 1) -> List[Dict[str, Any]]:
        """Get payment history.

        Args:
            min_amount: Minimum payment amount
            limit: Maximum number of payments to return

        Returns:
            List of payments

        Raises:
            Exception: If the request fails
        """
        if not self.access_token:
            raise Exception("Access token not set")

        headers = {
            "Authorization": f"Bearer {self.access_token}",
        }

        params = {
            "type": "receiving_money",
            "pmin": min_amount,
            "show_payment_stats": "false",
            "is_hold": "false",
        }

        # Use session to control connection parameters
        session = requests.Session()
        session.headers.update(headers)

        # Disable HTTP/2 to avoid protocol errors
        session.mount('https://', requests.adapters.HTTPAdapter(max_retries=3))

        try:
            response = session.get(
                f"{self.MARKET_URL}/user/payments",
                params=params
            )

            if response.status_code != 200:
                raise Exception(f"Failed to get payment history: {response.status_code} - {response.text}")

            data = response.json()

            # Check data structure
            if "payments" not in data:
                print(f"Unexpected API response structure: 'payments' key not found in: {data.keys()}")
                return []

            # Extract payments from the response
            payments = []
            payments_data = data.get("payments", {})

            # If payments_data is a dict, convert it to a list
            if isinstance(payments_data, dict):
                for payment_id, payment_data in payments_data.items():

                    incoming_sum = payment_data.get("incoming_sum", 0)
                    if isinstance(incoming_sum, float) and incoming_sum.is_integer():
                        incoming_sum = str(int(incoming_sum))
                    else:
                        incoming_sum = str(incoming_sum).rstrip('0').rstrip('.')

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
            else:
                print(f"Unexpected payments data type: {type(payments_data)}")

            return list(reversed(payments))

        except requests.RequestException as e:
            print(f"Request exception in get_payment_history: {str(e)}")
            raise Exception(f"Network error getting payment history: {str(e)}")
        except json.JSONDecodeError as e:
            print(f"JSON decode error in get_payment_history: {str(e)}")
            print(f"Response text: {response.text}")
            raise Exception(f"Invalid JSON response from server: {str(e)}")
        except Exception as e:
            print(f"Unexpected error in get_payment_history: {str(e)}")
            raise Exception(f"Unexpected error in get_payment_history: {str(e)}")

    async def verify_token(self, access_token: str) -> bool:
        """Verify if the access token is valid.

        Returns:
            True if token is valid, False otherwise
        """
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.FORUM_URL}/users/me", headers=headers) as response:
                    return response.status == 200
        except Exception:
            return False
