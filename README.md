# LOLZTEAM DONATE

<p align="center">
  <img src="https://via.placeholder.com/200x200.png?text=LOLZTEAM+DONATE" alt="LOLZTEAM DONATE Logo"/>
</p>

A Python application that integrates LOLZTEAM with DonationAlerts, allowing you to automatically forward donations from
LOLZTEAM to DonationAlerts for showing alerts during your streams.

## Features

- **Dual Mode Operation**: Run as a GUI application or in console mode
- **Payment Monitoring**: Automatically monitor LOLZTEAM for new payments
- **DonationAlerts Integration**: Forward payments to DonationAlerts as custom alerts
- **Real-time Notifications**: Get notified when new payments are received
- **Payment History**: View recent payments directly in the application
- **Customizable Settings**: Configure API credentials, minimum payment amount, check interval, and more
- **System Tray Support**: Runs in the background with system tray notifications

## Installation

### Prerequisites

- Python 3.8 or higher
- PyQt5 (for GUI mode)
- Required Python packages (see `requirements.txt`)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/lolzteam-donate.git
   cd lolzteam-donate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   # GUI mode
   python main.py
   
   # Console mode
   python main.py --console
   ```

## Configuration

The application requires authentication with both DonationAlerts and LOLZTEAM:

### DonationAlerts Setup

1. Create a new application at [DonationAlerts](https://www.donationalerts.com/application/clients)
2. Set the redirect URI to `http://127.0.0.1:5228/login`
3. Note your Client ID and Client Secret
4. Enter these credentials in the application settings

### LOLZTEAM Setup

1. Create a new application at [LOLZTEAM](https://lolz.live/account/api)
2. Set the redirect URI to your application's callback URL
3. Note your Client ID
4. Enter this information in the application settings

## Usage

### GUI Mode

1. Launch the application: `python main.py`
2. Click "Authenticate with DonationAlerts" and "Authenticate with LOLZTEAM" to connect your accounts
3. Once authenticated, the application will automatically start monitoring for new payments
4. View recent payments in the "Recent Payments" section
5. Configure settings by clicking the "Settings" button

### Console Mode

1. Launch the application in console mode: `python main.py --console`
2. Follow the on-screen prompts to authenticate and configure the application
3. Select "Start monitoring payments" to begin monitoring

## Advanced Settings

### Minimum Payment Amount

Set the minimum payment amount to monitor. Payments below this amount will be ignored.

### Check Interval

Configure how frequently the application checks for new payments (in seconds).

### Application Settings

- **Start Minimized**: Start the application minimized to the system tray
- **Start with System**: Launch the application automatically when your system starts

## Troubleshooting

### Authentication Issues

- Ensure your Client ID and Client Secret are correct
- Check that your redirect URIs match exactly
- Try re-authenticating if your tokens have expired

### Payment Monitoring Issues

- Verify that both DonationAlerts and LOLZTEAM are properly authenticated
- Check your internet connection
- Ensure the LOLZTEAM API is accessible

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [DonationAlerts API](https://www.donationalerts.com/apidoc)
- [LOLZTEAM API](https://lolz.live/account/api)
- [PyQt5](https://riverbankcomputing.com/software/pyqt/intro)
