"""
Authentication service for handling authentication with external services through browser and local server.
"""

import re
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse


class AuthSuccessful(Exception):
    """Exception raised when authentication is successful."""

    def __init__(self, token):
        self.token = token
        super().__init__(f"Авторизация с помощью токена прошла успешно: {token[:10]}...")


class AuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP request handler for auth callbacks."""

    def __init__(self, *args, token_pattern=None, is_fragment=False, **kwargs):
        self.token_pattern = token_pattern
        self.is_fragment = is_fragment
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """Handle GET request."""
        # Отправляем ответ
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()

        # Проверяем URL на наличие токена
        url_path = self.path
        token = None

        # Если токен в URL параметрах
        if not self.is_fragment and self.token_pattern:
            if match := re.search(self.token_pattern, url_path):
                token = match[1]
                auth_server = self.server
                auth_server.token = token
                auth_server.stop_requested = True

        # Возвращаем HTML страницу
        if self.is_fragment:
            # Для фрагментов (LOLZTEAM) нужен JavaScript для извлечения токена
            html = """
            <html>
            <head>
                <title>Успешная авторизация</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 0; padding: 20px; text-align: center; }
                    .container { max-width: 600px; margin: 50px auto; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                    h1 { color: #2BAD72; }
                    p { color: #333; line-height: 1.6; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>LOLZTEAM DONATE</h1>
                    <div id="message">
                        <h2>Процесс авторизации...</h2>
                        <p>Пожалуйста, подождите, пока мы обработаем вашу авторизацию...</p>
                    </div>
                </div>
                
                <script>
                    // Извлекаем токен из фрагмента URL
                    if (window.location.hash) {
                        const fragment = window.location.hash.substring(1);
                        const params = new URLSearchParams(fragment);
                        const token = params.get("access_token");
                        
                        if (token) {
                            // Отправляем токен на сервер
                            fetch("/token?token=" + encodeURIComponent(token))
                                .then(() => {
                                    document.getElementById("message").innerHTML = `
                                        <h2>Успешная авторизация!</h2>
                                        <p>Теперь вы можете закрыть это окно и вернуться к работе с приложением.</p>
                                    `;
                                })
                                .catch(err => {
                                    console.error("Error sending token:", err);
                                    document.getElementById("message").innerHTML = `
                                        <h2>Ошибка авторизации</h2>
                                        <p>Произошла ошибка при обработке вашей авторизации. Пожалуйста, попробуйте еще раз.</p>
                                    `;
                                });
                        } else {
                            document.getElementById("message").innerHTML = `
                                <h2>Ошибка авторизации</h2>
                                <p>Не найден токен авторизации. Пожалуйста, попробуйте еще раз.</p>
                            `;
                        }
                    } else {
                        document.getElementById("message").innerHTML = `
                            <h2>Ошибка авторизации</h2>
                            <p>Данные для авторизации не найдены. Пожалуйста, попробуйте еще раз.</p>
                        `;
                    }
                </script>
            </body>
            </html>
            """
        else:
            # Для обычных URL (DonationAlerts)
            if token:
                html = """
                <html>
                <head>
                    <title>Успешная авторизация/title>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; text-align: center; }
                        .container { max-width: 600px; margin: 50px auto; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                        h1 { color: #2BAD72; }
                        p { color: #333; line-height: 1.6; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>LOLZTEAM DONATE</h1>
                        <h2>Успешная авторизация!</h2>
                        <p>Теперь вы можете закрыть это окно и вернуться к работе с приложением.</p>
                    </div>
                </body>
                </html>
                """
            else:
                html = """
                <html>
                <head>
                    <title>Ошибка авторизации</title>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; text-align: center; }
                        .container { max-width: 600px; margin: 50px auto; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                        h1 { color: #2BAD72; }
                        h2 { color: #884444; }
                        p { color: #333; line-height: 1.6; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>LOLZTEAM DONATE</h1>
                        <h2>Ошибка авторизации</h2>
                        <p>Не найден токен авторизации. Пожалуйста, попробуйте еще раз.</p>
                    </div>
                </body>
                </html>
                """

        self.wfile.write(html.encode())

    def do_POST(self):
        """Handle POST request."""
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        """Override to suppress logging."""
        return

    def handle_token_fragment(self):
        """Handle token in URL fragment."""
        if self.path.startswith("/token"):
            query = urlparse(self.path).query
            params = parse_qs(query)
            if "token" in params:
                token = params["token"][0]
                auth_server = self.server
                auth_server.token = token
                auth_server.stop_requested = True
                return True
        return False


class AuthServer(HTTPServer):
    """HTTP server for handling auth callbacks."""

    def __init__(self, server_address, handler_class, token_pattern=None, is_fragment=False):
        """Initialize auth server.

        Args:
            server_address: Server address (host, port)
            handler_class: Handler class
            token_pattern: Pattern for extracting token from URL
            is_fragment: Whether token is in URL fragment
        """

        class CustomHandler(handler_class):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, token_pattern=token_pattern, is_fragment=is_fragment, **kwargs)

            def do_GET(self):
                # Обрабатываем запрос получения токена из фрагмента
                if is_fragment and self.path.startswith("/token"):
                    query = urlparse(self.path).query
                    params = parse_qs(query)
                    if "token" in params:
                        token = params["token"][0]
                        auth_server = self.server
                        auth_server.token = token
                        auth_server.stop_requested = True

                        # Отправляем ответ
                        self.send_response(200)
                        self.send_header("Content-type", "text/html; charset=utf-8")
                        self.end_headers()
                        self.wfile.write(b"OK")
                        return

                # Стандартная обработка
                super().do_GET()

        super().__init__(server_address, CustomHandler)
        self.token = None
        self.stop_requested = False

    def serve_forever(self, poll_interval=0.5):
        """Serve until stopped."""
        while not self.stop_requested:
            self.handle_request()
            time.sleep(0.1)


class AuthenticationService:
    """Service for handling authentication with external services."""

    def __init__(self, host="localhost", port=5228):
        """Initialize authentication service.

        Args:
            host: Host to bind server to
            port: Port to bind server to
        """
        self.host = host
        self.port = port
        self.server = None
        self.server_thread = None

    def authenticate_process(self, auth_url, on_success=None, on_error=None):
        """Authenticate with DonationAlerts.

        Args:
            auth_url: Authorization URL
            on_success: Callback for successful authentication
            on_error: Callback for authentication error
        """
        return self._authenticate(
            auth_url,
            token_pattern=r"access_token=([^&]+)",
            is_fragment=True,
            on_success=on_success,
            on_error=on_error
        )

    def _authenticate(self, auth_url, token_pattern=None, is_fragment=False,
                      on_success=None, on_error=None):
        """Authenticate with a service.

        Args:
            auth_url: Authorization URL
            token_pattern: Pattern for extracting token from URL
            is_fragment: Whether token is in URL fragment
            on_success: Callback for successful authentication
            on_error: Callback for authentication error

        Returns:
            True if authentication started successfully, False otherwise
        """
        # Проверяем, не запущен ли уже сервер
        if self.server is not None:
            if on_error:
                on_error("Авторизация уже выполняется")
            return False

        try:
            # Запускаем сервер для получения колбэка
            self.server = AuthServer(
                (self.host, self.port),
                AuthCallbackHandler,
                token_pattern=token_pattern,
                is_fragment=is_fragment
            )

            # Запускаем сервер в отдельном потоке
            self.server_thread = threading.Thread(
                target=self._run_server,
                args=(on_success, on_error)
            )
            self.server_thread.daemon = True
            self.server_thread.start()

            # Открываем браузер с URL авторизации
            webbrowser.open(auth_url)

            return True
        except Exception as e:
            if on_error:
                on_error(f"Не удалось запустить авторизацию: {str(e)}")
            return False

    def _run_server(self, on_success=None, on_error=None):
        """Run the server and handle callbacks.

        Args:
            on_success: Callback for successful authentication
            on_error: Callback for authentication error
        """
        try:
            self.server.serve_forever()

            # Если сервер остановлен и есть токен, вызываем колбэк успешной авторизации
            if self.server.token and on_success:
                on_success(self.server.token)
        except Exception as e:
            if on_error:
                on_error(f"Ошибка при авторизации: {str(e)}")
        finally:
            self.server = None
            self.server_thread = None

    def cancel(self):
        """Cancel the authentication process."""
        if self.server:
            self.server.stop_requested = True
