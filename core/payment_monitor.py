"""
Payment monitoring module.
Monitors LOLZTEAM for new payments and sends alerts to DonationAlerts.
"""

import asyncio
import datetime
import time
from typing import Dict, Any, List, Optional, Set, Callable

from core.donation_alerts import DonationAlertsAPI
from core.lolzteam import LolzteamAPI

from . import errors


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
        self.donation_alerts_token = None
        self.on_payment_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        self.on_error_callback: Optional[Callable[[str], None]] = None
        self.on_payments_updated_callback: Optional[Callable[[List[Dict[str, Any]]], None]] = None
        self.last_check_time = 0

        # Debug info
        print(f"PaymentMonitor initialized with min_amount={min_amount}, check_interval={check_interval}")

    def set_on_payments_updated_callback(self, callback: Callable[[List[Dict[str, Any]]], None]) -> None:
        """Set callback to be called when payments are updated in a cycle.

        Args:
            callback: Callback function that will receive the full list of payments
        """
        self.on_payments_updated_callback = callback
        print("Payments updated callback set")

    def set_donation_alerts_token(self, token: str) -> None:
        """Set the DonationAlerts access token.

        Args:
            token: Access token
        """
        self.donation_alerts_token = token
        print(f"DonationAlerts token set: {token[:10]}...")

    def set_min_amount(self, amount: int) -> None:
        """Set the minimum payment amount to monitor.

        Args:
            amount: Minimum amount
        """
        self.min_amount = amount
        print(f"Minimum payment amount set to {amount}")

    def set_check_interval(self, interval: int) -> None:
        """Set the interval between checks.

        Args:
            interval: Interval in seconds
        """
        self.check_interval = interval
        print(f"Check interval set to {interval} seconds")

    def set_on_payment_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Set callback to be called when a new payment is detected.

        Args:
            callback: Callback function
        """
        self.on_payment_callback = callback
        print("Payment callback set")

    def set_on_error_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback to be called when an error occurs.

        Args:
            callback: Callback function
        """
        self.on_error_callback = callback
        print("Error callback set")

    async def start(self) -> None:
        """Start monitoring for payments."""
        if self.running:
            print("Payment monitor already running")
            return

        print("Starting payment monitor...")
        self.running = True

        # Start the DonationAlerts alert processor
        if self.donation_alerts_token:
            print("Starting DonationAlerts alert processor")
            await self.donation_alerts_api.start_alert_processor(self.donation_alerts_token)
        else:
            print("Warning: DonationAlerts token not set, alerts will not be sent")
            if self.on_error_callback:
                self.on_error_callback("DonationAlerts token not set, alerts will not be sent")

        # Initialize known payment IDs on first run
        try:
            print(f"Initializing known payment IDs with min_amount={self.min_amount}")
            payments = self.lolzteam_api.get_payment_history(
                min_amount=self.min_amount
            )
            print(f"Found {len(payments)} existing payments")
            self.known_payment_ids = {payment["id"] for payment in payments}
            print(f"Initialized {len(self.known_payment_ids)} known payment IDs")

            # Запомним текущее время как время последней проверки
            self.last_check_time = time.time()

            # Start the monitoring task
            print("Starting payment monitoring task")
            # Use the current event loop
            loop = asyncio.get_event_loop()
            self.task = loop.create_task(self._monitor_payments())
            print("Payment monitor started")

            # Don't await the task - it will run indefinitely

        except Exception as e:
            error_msg = f"Failed to initialize payment monitor: {str(e)}"
            print(f"ERROR: {error_msg}")
            if self.on_error_callback:
                self.on_error_callback(error_msg)
            self.running = False
            raise errors.InitializeException(f"Failed to initialize payment monitor: {str(e)}") from e # Propagate the exception

    async def stop(self):
        """Stop monitoring for payments."""
        if not self.running:
            print("Payment monitor not running")
            return

        print("Stopping payment monitor...")
        self.running = False

        # Cancel and wait for the task to finish
        if self.task and not self.task.done():
            print("Cancelling monitoring task")
            try:
                self.task.cancel()
                # Give the task a chance to clean up
                try:
                    await asyncio.wait_for(asyncio.shield(self.task), timeout=5.0)
                except asyncio.TimeoutError:
                    print("Timeout waiting for task to cancel, force cancelling")
                except asyncio.CancelledError:
                    print("Task cancelled successfully")
            except Exception as e:
                print(f"Error cancelling task: {e}")

        # Stop the DonationAlerts alert processor
        try:
            print("Stopping DonationAlerts alert processor")
            await self.donation_alerts_api.stop_alert_processor()
        except Exception as e:
            print(f"Error stopping DonationAlerts alert processor: {e}")

        print("Payment monitor stopped")
        return True  # Indicate successful stop

    async def _monitor_payments(self) -> None:
        """Monitor for new payments."""
        print("Payment monitoring loop started")

        try:
            while self.running:
                print("Current loop iteration - monitoring active")
                try:
                    current_time = datetime.datetime.now().strftime("%H:%M:%S")
                    print(f"[{current_time}] Checking for new payments with min_amount={self.min_amount}")
                    current_check_time = time.time()

                    # Track new payments in this cycle
                    new_payments = []

                    # Получаем все платежи без ограничения
                    payments = self.lolzteam_api.get_payment_history(
                        min_amount=self.min_amount
                    )

                    print(f"Retrieved {len(payments)} payments from API")

                    # Обрабатываем каждый платеж
                    for payment in payments:
                        payment_id = payment["id"]
                        payment_time = payment.get("datetime", 0)

                        # Проверяем, является ли платеж новым (не в известных ID и создан после последней проверки)
                        is_new = payment_id not in self.known_payment_ids and payment_time > self.last_check_time - 300  # Добавим 5 минут запаса

                        if is_new:
                            print(f"New payment detected: ID={payment_id}, Amount={payment['amount']}, "
                                  f"User={payment['username']}, Time={payment_time}")
                            self.known_payment_ids.add(payment_id)
                            new_payments.append(payment)  # Add to new payments list

                            # Получаем список банвордов
                            from config.settings import Settings
                            settings = Settings()
                            banwords = settings.get("app", "banwords") or []

                            # Фильтруем комментарий если есть банворды
                            comment = payment.get("comment", "")
                            if banwords and comment:
                                for word in banwords:
                                    if word and len(word) > 0:  # Проверяем, что слово не пустое
                                        # Используем регулярные выражения для поиска без учета регистра
                                        import re
                                        pattern = re.compile(re.escape(word), re.IGNORECASE)
                                        comment = pattern.sub('*' * len(word), comment)
                                payment["comment"] = comment

                            username = payment.get("username", "")
                            if banwords and username:
                                for word in banwords:
                                    if word and len(word) > 0:  # Проверяем, что слово не пустое
                                        # Используем регулярные выражения для поиска без учета регистра
                                        import re
                                        pattern = re.compile(re.escape(word), re.IGNORECASE)
                                        username = pattern.sub('*' * len(word), username)
                                payment["username"] = username

                            # Notify callback for individual new payment
                            if self.on_payment_callback:
                                print("Calling payment callback")
                                self.on_payment_callback(payment)

                            # Queue alert for DonationAlerts
                            if self.donation_alerts_token:
                                print(f"Queuing alert for DonationAlerts: {payment['amount']} RUB from "
                                      f"{payment['username']}")
                                await self.donation_alerts_api.queue_alert(
                                    payment["amount"],
                                    payment["username"],
                                    payment.get("comment", "")
                                )
                            else:
                                print("DonationAlerts token not set, alert not queued")

                    # If we have new payments, send them to be added to the UI
                    # BUT DON'T SEND ALL PAYMENTS - this would cause the list to be replaced
                    if new_payments and self.on_payments_updated_callback:
                        print(f"Sending {len(new_payments)} new payments to be added to the UI")
                        self.on_payments_updated_callback(new_payments)

                    # Обновляем время последней проверки
                    self.last_check_time = current_check_time
                    print(f"Updated last_check_time to {self.last_check_time}")

                except Exception as e:
                    error_msg = f"Error monitoring payments: {str(e)}"
                    print(f"ERROR: {error_msg}")
                    if self.on_error_callback:
                        self.on_error_callback(error_msg)
                    # Добавляем небольшую паузу при ошибке, чтобы не забивать логи
                    await asyncio.sleep(5)
                    continue  # Продолжаем работу после ошибки

                # Wait for next check with interrupt handling
                print(f"Waiting {self.check_interval} seconds until next check")

                # Use smaller sleep intervals to check self.running more frequently
                remaining = self.check_interval
                while remaining > 0 and self.running:
                    sleep_interval = min(1, remaining)  # Sleep at most 1 second at a time
                    await asyncio.sleep(sleep_interval)
                    remaining -= sleep_interval

                if self.running:
                    print("Woke up, checking again...")
                else:
                    print("Monitoring stopped during sleep")
                    break

        except asyncio.CancelledError as e:
            print("Monitoring task was cancelled")
            # Correctly handle cancellation
            raise errors.TaskCanceled("Monitoring task was cancelled") from e
        except Exception as e:
            print(f"Unexpected error in monitor loop: {str(e)}")
            if self.on_error_callback:
                self.on_error_callback(f"Monitoring stopped due to error: {str(e)}")
            raise errors.BasePMException(f"Unexpected error in monitor loop: {str(e)}") from e
        finally:
            print("Monitoring loop ended")
