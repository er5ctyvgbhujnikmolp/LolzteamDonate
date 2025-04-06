import asyncio
import datetime
import logging
import time
from typing import Dict, Any, List, Optional, Set, Callable

from core.donation_alerts import DonationAlertsAPI
from core.lolzteam import LolzteamAPI
from core.text_filtering import filter_text_with_banwords, filter_urls_from_text

logger = logging.getLogger("PaymentMonitor")


class PaymentMonitor:
    """Monitors LOLZTEAM for new payments and sends alerts to DonationAlerts."""

    def __init__(
            self,
            lolzteam_api: LolzteamAPI,
            donation_alerts_api: DonationAlertsAPI,
            min_amount: int = 1,
            check_interval: int = 60
    ):
        """Initialize payment monitor.

        Args:
            lolzteam_api: LOLZTEAM API client
            donation_alerts_api: DonationAlerts API client
            min_amount: Minimum payment amount to monitor
            check_interval: Interval in seconds between checks
        """
        self.lolzteam_api = lolzteam_api
        self.donation_alerts_api = donation_alerts_api
        self.min_amount = min_amount
        self.check_interval = check_interval
        self.running = False
        self.task = None
        self.known_payment_ids: Set[str] = set()
        self.on_payment_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        self.on_error_callback: Optional[Callable[[str], None]] = None
        self.on_payments_updated_callback: Optional[Callable[[List[Dict[str, Any]]], None]] = None
        self.last_check_time = 0
        self.filter_urls = False  # New setting to control URL filtering
        self.logger = logging.getLogger("PaymentMonitor")

        # Debug info
        self.logger.info(f"PaymentMonitor initialized with min_amount={min_amount}, check_interval={check_interval}")

    def set_on_payments_updated_callback(self, callback: Callable[[List[Dict[str, Any]]], None]) -> None:
        """Set callback to be called when payments are updated in a cycle.

        Args:
            callback: Callback function that will receive the full list of payments
        """
        self.on_payments_updated_callback = callback
        self.logger.info("Payments updated callback set")

    def set_min_amount(self, amount: int) -> None:
        """Set the minimum payment amount to monitor.

        Args:
            amount: Minimum amount
        """
        self.min_amount = amount
        self.logger.info(f"Minimum payment amount set to {amount}")

    def set_check_interval(self, interval: int) -> None:
        """Set the interval between checks.

        Args:
            interval: Interval in seconds
        """
        self.check_interval = interval
        self.logger.info(f"Check interval set to {interval} seconds")

    def set_filter_urls(self, should_filter: bool) -> None:
        """Set whether to filter URLs from payment comments.

        Args:
            should_filter: Whether to filter URLs
        """
        self.filter_urls = should_filter
        self.logger.info(f"URL filtering set to {should_filter}")

    def set_on_payment_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Set callback to be called when a new payment is detected.

        Args:
            callback: Callback function
        """
        self.on_payment_callback = callback
        self.logger.info("Payment callback set")

    def set_on_error_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback to be called when an error occurs.

        Args:
            callback: Callback function
        """
        self.on_error_callback = callback
        self.logger.info("Error callback set")

    async def start(self) -> None:
        """Start monitoring for payments."""
        if self.running:
            self.logger.info("Payment monitor already running")
            return

        self.logger.info("Starting payment monitor...")
        self.running = True

        # Start the DonationAlerts alert processor
        try:
            self.logger.info("Starting DonationAlerts alert processor")
            await self.donation_alerts_api.start_alert_processor()
        except Exception as e:
            error_msg = f"Failed to start DonationAlerts alert processor: {str(e)}"
            self.logger.error(error_msg)
            if self.on_error_callback:
                self.on_error_callback(error_msg)

        # Initialize known payment IDs on first run
        try:
            self.logger.info(f"Initializing known payment IDs with min_amount={self.min_amount}")
            payments = await self.lolzteam_api.get_payment_history(min_amount=self.min_amount)
            self.logger.info(f"Found {len(payments)} existing payments")
            self.known_payment_ids = {payment["id"] for payment in payments}
            self.logger.info(f"Initialized {len(self.known_payment_ids)} known payment IDs")

            # Set the last check time
            self.last_check_time = time.time()

            # Start the monitoring task
            self.logger.info("Starting payment monitoring task")
            # Use the current event loop
            loop = asyncio.get_event_loop()
            self.task = loop.create_task(self._monitor_payments())
            self.logger.info("Payment monitor started")

        except Exception as e:
            error_msg = f"Failed to initialize payment monitor: {str(e)}"
            self.logger.error(error_msg)
            if self.on_error_callback:
                self.on_error_callback(error_msg)
            self.running = False
            raise  # Propagate the exception

    async def stop(self):
        """Stop monitoring for payments."""
        if not self.running:
            self.logger.info("Payment monitor not running")
            return

        self.logger.info("Stopping payment monitor...")
        self.running = False

        # Cancel and wait for the task to finish
        if self.task and not self.task.done():
            self.logger.info("Cancelling monitoring task")
            try:
                self.task.cancel()
                # Give the task a chance to clean up
                try:
                    await asyncio.wait_for(asyncio.shield(self.task), timeout=5.0)
                except asyncio.TimeoutError:
                    self.logger.warning("Timeout waiting for task to cancel, force cancelling")
                except asyncio.CancelledError:
                    self.logger.info("Task cancelled successfully")
            except Exception as e:
                self.logger.error(f"Error cancelling task: {e}")

        # Stop the DonationAlerts alert processor
        try:
            self.logger.info("Stopping DonationAlerts alert processor")
            await self.donation_alerts_api.stop_alert_processor()
        except Exception as e:
            self.logger.error(f"Error stopping DonationAlerts alert processor: {e}")

        self.logger.info("Payment monitor stopped")
        return True  # Indicate successful stop

    async def _monitor_payments(self) -> None:
        """Monitor for new payments."""
        self.logger.info("Payment monitoring loop started")

        try:
            while self.running:
                self.logger.info("Current loop iteration - monitoring active")
                try:
                    current_time = datetime.datetime.now().strftime("%H:%M:%S")
                    self.logger.info(f"[{current_time}] Checking for new payments with min_amount={self.min_amount}")
                    current_check_time = time.time()

                    # Track new payments in this cycle
                    new_payments = []

                    # Get all payments without limits
                    payments = await self.lolzteam_api.get_payment_history(min_amount=self.min_amount)
                    self.logger.info(f"Retrieved {len(payments)} payments from API")

                    # Get filter settings from config
                    from config.settings import Settings
                    settings = Settings()
                    banwords = settings.get("app", "banwords") or []
                    filter_urls = settings.get("app", "filter_urls", False)

                    # Process each payment
                    for payment in payments:
                        payment_id = payment["id"]
                        payment_time = payment.get("datetime", 0)

                        # Check if payment is new (not in known IDs and created after last check)
                        is_new = payment_id not in self.known_payment_ids and payment_time > self.last_check_time - 300  # Add 5 minutes buffer

                        if is_new:
                            self.logger.info(f"New payment detected: ID={payment_id}, Amount={payment['amount']}, "
                                  f"User={payment['username']}, Time={payment_time}")
                            self.known_payment_ids.add(payment_id)

                            # Apply text filtering
                            payment = self._filter_payment_content(payment, banwords, filter_urls or self.filter_urls)
                            new_payments.append(payment)  # Add to new payments list

                            # Notify callback for individual new payment
                            if self.on_payment_callback:
                                self.logger.info("Calling payment callback")
                                self.on_payment_callback(payment)

                            # Queue alert for DonationAlerts
                            self.logger.info(f"Queuing alert for DonationAlerts: {payment['amount']} RUB from "
                                             f"{payment['username']}")
                            await self.donation_alerts_api.queue_alert(
                                payment["amount"],
                                payment["username"],
                                payment.get("comment", "")
                            )

                    # If we have new payments, send them to be added to the UI
                    # DON'T SEND ALL PAYMENTS - this would cause the list to be replaced
                    if new_payments and self.on_payments_updated_callback:
                        self.logger.info(f"Sending {len(new_payments)} new payments to be added to the UI")
                        self.on_payments_updated_callback(new_payments)

                    # Update the last check time
                    self.last_check_time = current_check_time
                    self.logger.info(f"Updated last_check_time to {self.last_check_time}")

                except Exception as e:
                    error_msg = f"Error monitoring payments: {str(e)}"
                    self.logger.error(error_msg)
                    if self.on_error_callback:
                        self.on_error_callback(error_msg)
                    # Add a small pause on error to avoid spamming logs
                    await asyncio.sleep(5)
                    continue  # Continue after error

                # Wait for next check with interrupt handling
                self.logger.info(f"Waiting {self.check_interval} seconds until next check")

                # Use smaller sleep intervals to check self.running more frequently
                remaining = self.check_interval
                while remaining > 0 and self.running:
                    sleep_interval = min(1, remaining)  # Sleep at most 1 second at a time
                    await asyncio.sleep(sleep_interval)
                    remaining -= sleep_interval

                if self.running:
                    self.logger.info("Woke up, checking again...")
                else:
                    self.logger.info("Monitoring stopped during sleep")
                    break

        except asyncio.CancelledError:
            self.logger.info("Monitoring task was cancelled")
            # Correctly handle cancellation
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in monitor loop: {str(e)}")
            if self.on_error_callback:
                self.on_error_callback(f"Monitoring stopped due to error: {str(e)}")
            raise
        finally:
            self.logger.info("Monitoring loop ended")

    def _filter_payment_content(self, payment: Dict[str, Any], banwords: List[str], filter_urls: bool) -> Dict[
        str, Any]:
        """Filter payment content using banwords and URL filtering.

        Args:
            payment: Payment data
            banwords: List of banned words
            filter_urls: Whether to filter URLs

        Returns:
            Filtered payment data
        """
        # Make a copy to avoid modifying the original
        filtered_payment = payment.copy()

        # Filter comment if present
        if comment := filtered_payment.get("comment", ""):
            # First filter banned words
            filtered_comment = filter_text_with_banwords(comment, banwords)

            # Then filter URLs if enabled
            if filter_urls:
                filtered_comment = filter_urls_from_text(filtered_comment)

            filtered_payment["comment"] = filtered_comment

        # Filter username
        if username := filtered_payment.get("username", ""):
            filtered_username = filter_text_with_banwords(username, banwords)
            filtered_payment["username"] = filtered_username

        return filtered_payment
