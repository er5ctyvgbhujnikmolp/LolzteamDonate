"""
Console interface for LOLZTEAM DONATE application.
"""

import asyncio
import http.server
import signal
import socketserver
import sys
import urllib.parse
import webbrowser
from datetime import datetime
from threading import Thread

from config.settings import Settings
from core.donation_alerts import DonationAlertsAPI, Scopes
from core.lolzteam import LolzteamAPI
from core.payment_monitor import PaymentMonitor


class ConsoleColors:
    """ANSI color codes for console output."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class AuthServer:
    """Simple HTTP server for handling authentication callbacks."""

    def __init__(self, port=5228, token_param="code", is_fragment=False):
        """Initialize auth server.
        
        Args:
            port: Port to listen on
            token_param: Parameter name containing the token
            is_fragment: Whether the token is in the URL fragment
        """
        self.port = port
        self.token_param = token_param
        self.is_fragment = is_fragment
        self.token = None
        self.server = None
        self.server_thread = None

    def start(self):
        """Start the server."""
        self.server = socketserver.TCPServer(("", self.port), self._create_handler())

        self.server_thread = Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()

        print(f"Authentication server listening on port {self.port}...")

    def stop(self):
        """Stop the server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server_thread.join()
            print("Authentication server stopped.")

    def _create_handler(self):
        """Create a request handler class with access to our variables."""
        token_param = self.token_param
        is_fragment = self.is_fragment
        outer_self = self

        class AuthHandler(http.server.SimpleHTTPRequestHandler):
            def do_GET(self):
                """Handle GET request."""
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()

                if is_fragment:
                    self._handle_fragment()
                else:
                    self._handle_query()

            def _handle_fragment(self):
                """Handle the token extraction from URL fragment."""
                html = f"""
                <html>
                <head><title>Authentication Successful</title></head>
                <body>
                    <script>
                        const params = new URLSearchParams(window.location.hash.substring(1));
                        const token = params.get("{token_param}");
                        
                        if (token) {{
                            window.location.href = "/token?" + "{token_param}=" + encodeURIComponent(token);
                        }} else {{
                            console.error("Token not found");
                        }}
                    </script>
                </body>
                </html>
                """
                self.wfile.write(html.encode())

                # After redirect, handle the query part
                query_params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                self._process_token(query_params)

            def _handle_query(self):
                """Handle the token extraction from URL query parameters."""
                query = urllib.parse.urlparse(self.path).query
                query_params = urllib.parse.parse_qs(query)
                self._process_token(query_params)

            def _process_token(self, query_params):
                """Process the token after extraction."""
                if token_param in query_params:
                    outer_self.token = query_params[token_param][0]
                    self._send_success_response()
                    Thread(target=outer_self.stop).start()
                else:
                    self._send_failure_response()

            def _send_success_response(self):
                """Send a response indicating successful authentication."""
                html = """
                <html>
                <head><title>Authentication Successful</title></head>
                <body>
                    <h1>Authentication Successful</h1>
                    <p>You can close this window now.</p>
                </body>
                </html>
                """
                self.wfile.write(html.encode())

            def _send_failure_response(self):
                """Send a response indicating failed authentication."""
                html = """
                <html>
                <head><title>Authentication Failed</title></head>
                <body>
                    <h1>Authentication Failed</h1>
                    <p>No token found in the request. Please try again.</p>
                </body>
                </html>
                """
                self.wfile.write(html.encode())

            def log_message(self, format, *args):
                """Suppress logging."""
                pass

        return AuthHandler


class ConsoleInterface:
    """Console interface for the application."""

    def __init__(self):
        """Initialize console interface."""
        self.settings = Settings()
        self.donation_alerts_api = None
        self.lolzteam_api = None
        self.payment_monitor = None
        self.running = False
        self.loop = None

        # Initialize API clients
        self._initialize_api_clients()

    def _initialize_api_clients(self):
        """Initialize API clients."""
        # DonationAlerts
        da_credentials = self.settings.get_donation_alerts_credentials()
        self.donation_alerts_api = DonationAlertsAPI(
            da_credentials["client_id"],
            da_credentials["redirect_uri"],
            [Scopes.USER_SHOW, Scopes.CUSTOM_ALERT_STORE]
        )

        # LOLZTEAM
        lzt_credentials = self.settings.get_lolzteam_credentials()
        self.lolzteam_api = LolzteamAPI(
            lzt_credentials["client_id"],
            lzt_credentials["redirect_uri"],
            lzt_credentials["access_token"]
        )

    def print_header(self):
        """Print application header."""
        print(f"{ConsoleColors.BOLD}{ConsoleColors.GREEN}")
        print(
            " ██╗      ██████╗ ██╗     ███████╗████████╗███████╗ █████╗ ███╗   ███╗    ██████╗  ██████╗ ███╗   ██╗ █████╗ ████████╗███████╗")
        print(
            " ██║     ██╔═══██╗██║     ╚══███╔╝╚══██╔══╝██╔════╝██╔══██╗████╗ ████║    ██╔══██╗██╔═══██╗████╗  ██║██╔══██╗╚══██╔══╝██╔════╝")
        print(
            " ██║     ██║   ██║██║       ███╔╝    ██║   █████╗  ███████║██╔████╔██║    ██║  ██║██║   ██║██╔██╗ ██║███████║   ██║   █████╗  ")
        print(
            " ██║     ██║   ██║██║      ███╔╝     ██║   ██╔══╝  ██╔══██║██║╚██╔╝██║    ██║  ██║██║   ██║██║╚██╗██║██╔══██║   ██║   ██╔══╝  ")
        print(
            " ███████╗╚██████╔╝███████╗███████╗   ██║   ███████╗██║  ██║██║ ╚═╝ ██║    ██████╔╝╚██████╔╝██║ ╚████║██║  ██║   ██║   ███████╗")
        print(
            " ╚══════╝ ╚═════╝ ╚══════╝╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝    ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═╝   ╚═╝   ╚══════╝")
        print(f"{ConsoleColors.ENDC}")
        print(f"{ConsoleColors.BLUE}Интеграция с DonationAlerts{ConsoleColors.ENDC}")
        print()

    def print_status(self):
        """Print current status."""
        print(f"{ConsoleColors.BOLD}Текущий статус:{ConsoleColors.ENDC}")

        if da_token := self.settings.get("donation_alerts", "access_token"):
            print(f"  DonationAlerts: {ConsoleColors.GREEN}Настроен{ConsoleColors.ENDC}")

            try:
                user_info = self.donation_alerts_api.user(da_token)
                name = user_info.get("data", {}).get("name", "Неизвестно")
                print(f"  - Вы вошли как: {name}")
            except Exception:
                print(f"  - {ConsoleColors.WARNING}Токен может быть недействительным{ConsoleColors.ENDC}")
        else:
            print(f"  DonationAlerts: {ConsoleColors.FAIL}Не настроен{ConsoleColors.ENDC}")

        if lzt_token := self.settings.get("lolzteam", "access_token"):
            print(f"  LOLZTEAM: {ConsoleColors.GREEN}Настроен{ConsoleColors.ENDC}")

            try:
                self.lolzteam_api.set_access_token(lzt_token)
                user_info = self.lolzteam_api.get_user_info()
                username = user_info.get("user", {}).get("username", "Неизвестно")
                print(f"  - Вы вошли как: {username}")
            except Exception:
                print(f"  - {ConsoleColors.WARNING}Токен может быть недействительным{ConsoleColors.ENDC}")
        else:
            print(f"  LOLZTEAM: {ConsoleColors.FAIL}Не настроен{ConsoleColors.ENDC}")

        # Monitoring settings
        print("\nНастройки мониторинга:")
        print(f"  Минимальная сумма платежа: {self.settings.get('app', 'min_payment_amount')} руб.")
        print(f"  Интервал проверки: {self.settings.get('app', 'check_interval_seconds')} секунд")

        print()

    def authenticate_donation_alerts(self):
        """Authenticate with DonationAlerts."""
        print(f"{ConsoleColors.HEADER}Аутентификация DonationAlerts{ConsoleColors.ENDC}")
        
        # Start auth server
        auth_server = AuthServer(port=5228, token_param="access_token", is_fragment=True)
        auth_server.start()

        # Get auth URL and open browser
        auth_url = self.donation_alerts_api.login()
        print(f"Открытие браузера: {auth_url}")
        webbrowser.open(auth_url)

        try:
            # Wait for token
            while auth_server.token is None and auth_server.server is not None:
                print("Ожидание аутентификации... (Нажмите Ctrl+C для отмены)")
                try:
                    asyncio.get_event_loop().run_until_complete(asyncio.sleep(1))
                except KeyboardInterrupt:
                    print("\nАутентификация отменена.")
                    auth_server.stop()
                    return

            if auth_server.token:
                # Save token
                self.settings.update_donation_alerts_token(auth_server.token)

                # Update API client
                self.donation_alerts_api.set_access_token(auth_server.token)

                # Get user info
                try:
                    user_info = self.donation_alerts_api.user(auth_server.token)
                    name = user_info.get("data", {}).get("name", "Неизвестно")

                    print(f"{ConsoleColors.GREEN}Аутентификация успешна!{ConsoleColors.ENDC}")
                    print(f"Вы вошли как: {name}")
                except Exception as e:
                    print(
                        f"{ConsoleColors.FAIL}Не удалось получить информацию о пользователе: {str(e)}{ConsoleColors.ENDC}")
            else:
                print(f"{ConsoleColors.FAIL}Аутентификация не удалась.{ConsoleColors.ENDC}")
        finally:
            # Ensure server is stopped
            if auth_server.server is not None:
                auth_server.stop()

    def authenticate_lolzteam(self):
        """Authenticate with LOLZTEAM."""
        print(f"{ConsoleColors.HEADER}Аутентификация LOLZTEAM{ConsoleColors.ENDC}")

        # Start auth server
        auth_server = AuthServer(
            port=5228, token_param="access_token", is_fragment=True
        )
        auth_server.start()

        # Get auth URL and open browser
        auth_url = self.lolzteam_api.get_auth_url()
        print(f"Открытие браузера: {auth_url}")
        webbrowser.open(auth_url)

        try:
            # Wait for token
            while auth_server.token is None and auth_server.server is not None:
                print("Ожидание аутентификации... (Нажмите Ctrl+C для отмены)")
                try:
                    asyncio.get_event_loop().run_until_complete(asyncio.sleep(1))
                except KeyboardInterrupt:
                    print("\nАутентификация отменена.")
                    auth_server.stop()
                    return

            if auth_server.token:
                # Save token
                self.settings.update_lolzteam_token(auth_server.token)

                # Update API client
                self.lolzteam_api.set_access_token(auth_server.token)

                # Get user info
                try:
                    user_info = self.lolzteam_api.get_user_info()
                    username = user_info.get("user", {}).get("username", "Неизвестно")

                    print(f"{ConsoleColors.GREEN}Аутентификация успешна!{ConsoleColors.ENDC}")
                    print(f"Вы вошли как: {username}")
                except Exception as e:
                    print(
                        f"{ConsoleColors.FAIL}Не удалось получить информацию о пользователе: {str(e)}{ConsoleColors.ENDC}")
            else:
                print(f"{ConsoleColors.FAIL}Аутентификация не удалась.{ConsoleColors.ENDC}")
        finally:
            # Ensure server is stopped
            if auth_server.server is not None:
                auth_server.stop()

    def configure_settings(self):
        """Configure application settings."""
        print(f"{ConsoleColors.HEADER}Настройка параметров{ConsoleColors.ENDC}")

        print("\nНастройки API DonationAlerts:")
        client_id = input(f"Client ID [{self.settings.get('donation_alerts', 'client_id')}]: ")
        if client_id:
            self.settings.set("donation_alerts", "client_id", client_id)

        redirect_uri = input(f"Redirect URI [{self.settings.get('donation_alerts', 'redirect_uri')}]: ")
        if redirect_uri:
            self.settings.set("donation_alerts", "redirect_uri", redirect_uri)

        print("\nНастройки API LOLZTEAM:")
        client_id = input(f"Client ID [{self.settings.get('lolzteam', 'client_id')}]: ")
        if client_id:
            self.settings.set("lolzteam", "client_id", client_id)

        redirect_uri = input(f"Redirect URI [{self.settings.get('lolzteam', 'redirect_uri')}]: ")
        if redirect_uri:
            self.settings.set("lolzteam", "redirect_uri", redirect_uri)

        print("\nMonitoring Settings:")
        min_amount = input(f"Минимальная сумма платежа [{self.settings.get('app', 'min_payment_amount')}]: ")
        if min_amount:
            try:
                min_amount = int(min_amount)
                self.settings.set("app", "min_payment_amount", min_amount)
            except ValueError:
                print(
                    f"{ConsoleColors.WARNING}Некорректное значение. Используем предыдущие настройки.{ConsoleColors.ENDC}")

        check_interval = input(f"Интервал проверки в секундах[{self.settings.get('app', 'check_interval_seconds')}]: ")
        if check_interval:
            try:
                check_interval = int(check_interval)
                self.settings.set("app", "check_interval_seconds", check_interval)
            except ValueError:
                print(
                    f"{ConsoleColors.WARNING}Некорректное значение. Используем предыдущие настройки.{ConsoleColors.ENDC}")

        print(f"{ConsoleColors.GREEN}Настройки сохранены.{ConsoleColors.ENDC}")

    def show_recent_payments(self):
        """Show recent payments from LOLZTEAM."""
        if not self.settings.is_lolzteam_configured():
            print(f"{ConsoleColors.FAIL}LOLZTEAM не настроен.{ConsoleColors.ENDC}")
            return

        print(f"{ConsoleColors.HEADER}Последние платежи{ConsoleColors.ENDC}")

        try:
            payments = self.lolzteam_api.get_payment_history(
                min_amount=self.settings.get("app", "min_payment_amount")
            )

            if not payments:
                print("Платежи не найдены.")
                return

            print(
                f"\n{ConsoleColors.BOLD}{'Сумма':^10} | {'Пользователь':^20} | {'Дата':^19} | {'Комментарий':^30}{ConsoleColors.ENDC}")
            print("-" * 85)

            for payment in reversed(payments):
                amount = payment.get("amount", 0)
                username = payment.get("username", "Неизвестно")
                timestamp = payment.get("datetime", 0)
                comment = payment.get("comment", "").strip()

                # Format date
                date_str = "Неизвестно"
                if timestamp:
                    date_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")

                # Truncate comment if too long
                if len(comment) > 30:
                    comment = f"{comment[:27]}..."

                print(f"{f'{amount} ₽':^10} | {username:^20} | {date_str:^19} | {comment:^30}")
        except Exception as e:
            print(f"{ConsoleColors.FAIL}Не удалось получить платежи: {str(e)}{ConsoleColors.ENDC}")

    @staticmethod
    def _on_new_payment(payment):
        """Handle new payment event.

        Args:
            payment: Payment data
        """
        amount = payment.get("amount", 0)
        username = payment.get("username", "Неизвестно")
        timestamp = payment.get("datetime", 0)
        comment = payment.get("comment", "").strip()

        # Format date
        date_str = "Неизвестно"
        if timestamp:
            date_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")

        print(f"\n{ConsoleColors.GREEN}[НОВЫЙ ПЛАТЕЖ] {amount} руб. от {username} в {date_str}{ConsoleColors.ENDC}")
        if comment:
            print(f"Комментарий: {comment}")

        print("\nПлатеж будет автоматически переадресован в DonationAlerts.")

    @staticmethod
    def _on_monitor_error(error_message):
        """Handle payment monitor error.
        
        Args:
            error_message: Error message
        """
        print(f"\n{ConsoleColors.FAIL}[ОШИБКА] {error_message}{ConsoleColors.ENDC}")

    async def _start_monitoring(self):
        """Start payment monitoring."""
        if not self.settings.is_donation_alerts_configured():
            print(f"{ConsoleColors.FAIL}DonationAlerts не настроен.{ConsoleColors.ENDC}")
            return

        if not self.settings.is_lolzteam_configured():
            print(f"{ConsoleColors.FAIL}LOLZTEAM не настроен.{ConsoleColors.ENDC}")
            return

        print(f"{ConsoleColors.HEADER}Запуск мониторинга платежей{ConsoleColors.ENDC}")

        # Create payment monitor
        self.payment_monitor = PaymentMonitor(
            self.lolzteam_api,
            self.donation_alerts_api,
            self.settings.get("app", "min_payment_amount"),
            self.settings.get("app", "check_interval_seconds")
        )

        # Set DonationAlerts token
        self.payment_monitor.set_donation_alerts_token(
            self.settings.get("donation_alerts", "access_token")
        )

        # Set callbacks
        self.payment_monitor.set_on_payment_callback(self._on_new_payment)
        self.payment_monitor.set_on_error_callback(self._on_monitor_error)

        # Start monitor
        await self.payment_monitor.start()

        print(f"{ConsoleColors.GREEN}Мониторинг платежей запущен.{ConsoleColors.ENDC}")
        print("Нажмите Ctrl+C для остановки.")

        self.running = True

        # Keep running until interrupted
        while self.running:
            try:
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break

    async def _stop_monitoring(self):
        """Stop payment monitoring."""
        if self.payment_monitor:
            self.running = False
            await self.payment_monitor.stop()
            self.payment_monitor = None

            print(f"{ConsoleColors.GREEN}Мониторинг платежей остановлен.{ConsoleColors.ENDC}")

    def run(self):
        """Run the console interface."""
        signal.signal(signal.SIGINT, lambda s, f: self._handle_sigint())

        self.loop = asyncio.get_event_loop()

        self.print_header()
        self.print_status()

        while True:
            print("\nОпции:")
            print("1. Начать мониторинг платежей")
            print("2. Показать последние платежи")
            print("3. Авторизоваться в DonationAlerts")
            print("4. Авторизоваться в LOLZTEAM")
            print("5. Настроить параметры")
            print("0. Выход")

            choice = input("\nВыберите опцию: ")

            if choice == "1":
                try:
                    self.loop.run_until_complete(self._start_monitoring())
                except KeyboardInterrupt:
                    self.loop.run_until_complete(self._stop_monitoring())
            elif choice == "2":
                self.show_recent_payments()
            elif choice == "3":
                self.authenticate_donation_alerts()
            elif choice == "4":
                self.authenticate_lolzteam()
            elif choice == "5":
                self.configure_settings()
            elif choice == "0":
                if self.payment_monitor:
                    self.loop.run_until_complete(self._stop_monitoring())
                print("Выход...")
                break
            else:
                print(f"{ConsoleColors.WARNING}Неверный выбор. Пожалуйста, попробуйте снова.{ConsoleColors.ENDC}")

    def _handle_sigint(self):
        """Handle SIGINT (Ctrl+C)."""
        if self.running:
            print("\nОстановка мониторинга платежей...")
            if self.loop and self.loop.is_running():
                asyncio.ensure_future(self._stop_monitoring())
            else:
                self.loop.run_until_complete(self._stop_monitoring())
        else:
            print("\nВыход...")
            sys.exit(0)


def main():
    """Entry point for console mode."""
    console = ConsoleInterface()
    console.run()


if __name__ == "__main__":
    main()
