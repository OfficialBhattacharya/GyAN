# UPSC News Aggregator

A PyQt5-based desktop application that automatically scrapes, filters, and delivers UPSC-relevant news to your inbox daily.

## Features

- **Desktop Application**: Clean, user-friendly desktop interface with real-time status monitoring
- **Multi-Source News Scraping**: Fetches news from The Hindu, PIB, and Indian Express
- **Smart Filtering**: Uses UPSC-relevant keywords to filter important news
- **Automated Email Delivery**: Sends beautifully formatted daily digest emails
- **Configurable Scheduling**: Set your preferred delivery time
- **Live Activity Monitoring**: View real-time logs and news items in the application
- **Error Handling**: Robust network error handling and retry mechanisms

## Quick Start

### Option 1: Run from Source (Recommended)

1. **Easy Start (Windows)**:
   - Double-click `start_app.bat` for automatic setup and launch
   
   **Or manually:**

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application**:
   ```bash
   python run_app.py
   ```
   *Or alternatively:* `python main.py`

4. **Configure Settings**: Use the Settings button or File menu to configure the application

### Option 2: Build Executable

1. **Clean Previous Builds**:
   ```bash
   # Remove old build files if they exist
   rmdir /s dist build (Windows)
   rm -rf dist build (Linux/Mac)
   ```

2. **Install PyInstaller**:
   ```bash
   pip install pyinstaller
   ```

3. **Build Executable**:
   ```bash
   python build.py
   ```

4. **Run**: Execute the generated file in the `dist/` folder

### If Executable Fails to Start

If you get a "ModuleNotFoundError" when running the executable:

1. **Use Source Version Instead** (Recommended):
   ```bash
   python run_app.py
   ```

2. **Or Rebuild with Clean Environment**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   python build.py
   ```

3. **Check Dependencies**:
   ```bash
   python -c "import apscheduler; import PyQt5; import bs4; print('All modules OK')"
   ```

## Configuration

### Email Settings

For Gmail users:
1. Enable 2-Factor Authentication
2. Generate an App Password: [Google Account Settings](https://myaccount.google.com/apppasswords)
3. Use your email and the app password in the settings

**SMTP Settings**:
- **Gmail**: `smtp.gmail.com:587`
- **Outlook**: `smtp-mail.outlook.com:587`
- **Yahoo**: `smtp.mail.yahoo.com:587`

### News Sources

The application scrapes from:
- **The Hindu**: National section for government and policy news
- **PIB**: Press Information Bureau for official government releases
- **Indian Express**: India section for current affairs

### Keywords

Default UPSC-relevant keywords include:
- Civil Services, Government, Policy, Governance
- Economy, GDP, Budget, Finance, Banking
- Environment, Climate, Conservation
- International Relations, Diplomacy
- Science, Technology, Innovation
- Security, Defence, Military
- Education, Health, Social Welfare
- Constitution, Supreme Court, Parliament

You can customize these in the settings dialog.

## Usage

### First-Time Setup

1. **Start the Application**: The app will open as a desktop window
2. **Open Settings**: Click the ⚙️ Settings button or use File → Settings menu
3. **Configure Email**:
   - Enter recipient email address
   - Set SMTP server details
   - Enter credentials
   - Test the connection using the "Test Email" button
4. **Set Schedule**: Choose your preferred daily delivery time
5. **Select Sources**: Enable desired news sources
6. **Customize Keywords**: Add or modify filtering keywords
7. **Save Settings**: Click Save to apply changes

### Daily Operation

- The application runs automatically in the background
- At the scheduled time, it will:
  1. Fetch news from configured sources
  2. Filter articles using your keywords
  3. Generate a formatted email digest
  4. Send it to your configured email address

### Manual Testing

- **Test News Fetch**: Click the 📰 "Test News Fetch" button or use Tools menu
- **Test Email**: Click the 📧 "Test Email" button or use Tools menu
- **Monitor Activity**: View real-time logs and status in the main window
- **View Latest News**: See fetched news items in the "Latest News Items" section

## File Structure

```
UPSC-News-Aggregator/
├── main.py                 # Application entry point
├── config.py               # Configuration management
├── scheduler.py            # Background job scheduling  
├── email_manager.py        # Email sending functionality
├── news_scraper.py         # Web scraping logic
├── ui/
│   ├── main_window.py      # Main application window
│   └── settings_dialog.py  # Configuration dialog
├── config.json             # User settings (auto-generated)
├── requirements.txt        # Python dependencies
├── build.py               # PyInstaller build script
└── README.md              # This file
```

## Troubleshooting

### Common Issues

**Application won't start**:
- Ensure Python 3.7+ is installed
- Install all dependencies: `pip install -r requirements.txt`
- Check console output for error messages

**Email sending fails**:
- Verify SMTP settings are correct
- For Gmail, use App Password instead of account password
- Check your internet connection
- Try the "Test Email" feature in settings

**No news items found**:
- Check if the news websites are accessible
- Try broadening your keyword list
- Test individual sources using "Test News Fetch"

**Window doesn't appear**:
- Check if the application is already running
- Try running from command line to see error messages
- Ensure PyQt5 is properly installed

### Log Files

The application creates log files for debugging:
- Check console output when running from source
- Windows: Logs are displayed in the command prompt
- Enable debug logging for detailed information

### Getting Help

1. Check this README for common solutions
2. Review the error messages in the application
3. Test individual components (email, news fetch) separately
4. Verify your configuration settings

## Technical Requirements

### System Requirements
- Windows 10/11, macOS 10.14+, or Linux
- Python 3.7 or higher
- Internet connection
- Desktop environment with GUI support

### Dependencies
- PyQt5: GUI framework
- BeautifulSoup4: HTML parsing
- Requests: HTTP requests
- APScheduler: Job scheduling
- PyInstaller: Executable building (optional)

## Development

### Setting up Development Environment

1. **Clone/Download** the project files
2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Run in development mode**:
   ```bash
   python main.py
   ```

### Customizing News Sources

To add new news sources, modify `news_scraper.py`:

```python
SOURCES = {
    "new_source": {
        "url": "https://example.com/news",
        "parser": lambda soup: soup.select('.article-title'),
        "processor": lambda item: item.text.strip(),
        "link_extractor": lambda item, base_url: urljoin(base_url, item.get('href', ''))
    }
}
```

### Building for Distribution

Use the included build script:
```bash
python build.py
```

This creates a standalone executable in the `dist/` folder.

## License

This project is open source. See LICENSE file for details.

## Support

For issues and feature requests, please check the troubleshooting section first. The application is designed to be self-contained and user-friendly.

---

**Note**: This application is for educational and personal use. Please respect the terms of service of the news websites being scraped.