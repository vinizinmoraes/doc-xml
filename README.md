# XML Watcher Service

A cross-platform service that monitors a folder for XML files and automatically uploads them to an API endpoint. Works on Windows, macOS, and Linux.

## Features

- 🔍 **Real-time file monitoring** - Detects new XML files as soon as they're created
- 🔄 **Automatic retries** - Configurable retry logic for failed uploads
- 🌐 **Cross-platform** - Works on Windows, macOS, and Linux
- 📁 **Flexible file handling** - Delete or move files after processing
- 🔐 **Multiple auth methods** - Supports Bearer token and Basic authentication
- 📊 **Comprehensive logging** - Detailed logs with rotation and color support
- ⚡ **Concurrent uploads** - Process multiple files simultaneously
- 📦 **Standalone executables** - No Python installation required

## Quick Start (Using Pre-built Executables)

### Download the Latest Release

1. Go to the [Releases](https://github.com/yourusername/xml-watcher/releases) page
2. Download the appropriate file for your platform:
   - **Windows**: `xml-watcher-windows.zip`
   - **macOS**: `xml-watcher-macos.tar.gz`
   - **Linux**: `xml-watcher-linux.tar.gz`

### Extract and Configure

```bash
# macOS/Linux
tar -xzf xml-watcher-[platform].tar.gz
cd xml-watcher

# Windows (use 7-Zip or Windows Explorer)
# Extract xml-watcher-windows.zip
```

### Configure the Service

1. Copy the example configuration:
   ```bash
   cp config/config.yaml.example config/config.yaml
   ```

2. Edit `config/config.yaml` with your settings:
   ```yaml
   watch_folder: "/path/to/watch"
   api:
     endpoint: "https://your-api.com/upload"
     auth:
       type: "bearer"
       token: "your-api-token"
   ```

### Run the Service

```bash
# macOS/Linux
./xml-watcher

# Windows
xml-watcher.exe
```

## Installation as Python Package

You can also install XML Watcher as a Python package:

```bash
pip install xml-watcher
```

Then run it with:
```bash
xml-watcher --config /path/to/config.yaml
```

## Installation from Source

### Requirements

- Python 3.8 or higher
- pip (Python package manager)

### Installation Steps

#### 1. Clone the repository

```bash
git clone https://github.com/vinizinmoraes/doc-xml.git
cd doc-xml
```

#### 2. Create a virtual environment (recommended)

```bash
# On macOS/Linux
python3 -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
venv\Scripts\activate
```

#### 3. Install dependencies

```bash
# For runtime dependencies only
pip install -r requirements.txt

# For development (includes testing, linting, building tools)
pip install -r requirements-dev.txt
```

#### 4. Configure the service

Copy the example configuration file:

```bash
cp config/config.yaml.example config/config.yaml
```

Edit `config/config.yaml` with your settings:

```yaml
# Minimal configuration
watch_folder: "/path/to/watch"
api:
  endpoint: "https://your-api.com/upload"
  auth:
    type: "bearer"
    token: "your-api-token"
```

## Usage

### Using Pre-built Executable

```bash
# Windows
xml-watcher.exe --config path/to/config.yaml

# macOS/Linux
./xml-watcher --config path/to/config.yaml

# Show version
xml-watcher --version
```

### Running from Source

```bash
# Using the Python module
python -m src.main

# Or using the executable script
./src/main.py

# With a custom config file
python -m src.main --config /path/to/config.yaml
```

### Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `watch_folder` | Directory to monitor for XML files | Required |
| `api.endpoint` | API endpoint URL | Required |
| `api.auth.type` | Authentication type: `bearer`, `basic`, or `none` | `none` |
| `api.timeout` | Request timeout in seconds | 30 |
| `api.retry_attempts` | Number of retry attempts | 3 |
| `processing.patterns` | File patterns to watch | `["*.xml", "*.XML"]` |
| `processing.process_existing` | Process existing files on startup | `false` |
| `processing.delete_after_upload` | Delete files after successful upload | `false` |
| `processing.processed_folder` | Move files here after processing | `""` (don't move) |
| `service.recursive` | Watch subdirectories | `true` |
| `service.max_concurrent_uploads` | Maximum parallel uploads | 5 |

### Environment Variables

You can override configuration using environment variables:

- `WATCH_FOLDER` - Override watch folder
- `API_ENDPOINT` - Override API endpoint
- `API_TOKEN` - Override API token
- `LOG_LEVEL` - Override log level
- `CONFIG_FILE` - Specify config file path

Example:
```bash
WATCH_FOLDER=/tmp/xml API_TOKEN=secret python -m src.main
```

## Running as a System Service

### Linux (systemd)

Create a systemd service file:

```bash
sudo nano /etc/systemd/system/xml-watcher.service
```

```ini
[Unit]
Description=XML Watcher Service
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/xml-watcher
Environment="PATH=/path/to/xml-watcher/venv/bin"
ExecStart=/path/to/xml-watcher/xml-watcher
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl enable xml-watcher
sudo systemctl start xml-watcher
sudo systemctl status xml-watcher
```

### macOS (launchd)

Create a plist file:

```bash
nano ~/Library/LaunchAgents/com.yourcompany.xml-watcher.plist
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.yourcompany.xml-watcher</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/xml-watcher/xml-watcher</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/path/to/xml-watcher</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/xml-watcher.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/xml-watcher-error.log</string>
</dict>
</plist>
```

Load the service:
```bash
launchctl load ~/Library/LaunchAgents/com.yourcompany.xml-watcher.plist
```

### Windows

Run as a Windows Service using NSSM (Non-Sucking Service Manager):

1. Download NSSM from https://nssm.cc/
2. Install the service:

```powershell
nssm install XMLWatcher "C:\path\to\xml-watcher\xml-watcher.exe"
nssm set XMLWatcher AppDirectory "C:\path\to\xml-watcher"
nssm start XMLWatcher
```

Or run in a console window:
```powershell
cd C:\path\to\xml-watcher
xml-watcher.exe
```

## Troubleshooting

### macOS: "Cannot verify developer" or Gatekeeper Issues

If you get a security warning on macOS saying the app cannot be verified:

**Method 1: Remove Quarantine Attribute**
```bash
# Navigate to where xml-watcher is located
xattr -d com.apple.quarantine xml-watcher
chmod +x xml-watcher
```

**Method 2: System Preferences**
1. Try to run the app (it will be blocked)
2. Go to **System Preferences** → **Security & Privacy**
3. Click **"Allow Anyway"** next to the xml-watcher entry
4. Try running the app again, then click **"Open"**

**Method 3: Right-click Method**
1. Right-click the executable
2. Select **"Open"** from the context menu
3. Click **"Open"** in the security dialog

### Windows: SmartScreen or Antivirus Warnings

If Windows Defender or your antivirus blocks the executable:
1. Add an exception for the xml-watcher.exe file
2. Or temporarily disable real-time protection during installation

### Linux: Permission Issues

If you get permission denied errors:
```bash
chmod +x xml-watcher
```

## Development

### Running tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_watcher.py
```

### Building Executables

To build standalone executables:

```bash
# Install PyInstaller
pip install pyinstaller

# Build executable
pyinstaller xml-watcher.spec --clean

# The executable will be in the dist/ directory
```

### Code formatting

```bash
# Format code
black src/ tests/

# Check code style
flake8 src/ tests/

# Type checking
mypy src/
```

## Troubleshooting

### Service won't start

1. Check configuration file syntax:
   ```bash
   python -c "import yaml; yaml.safe_load(open('config/config.yaml'))"
   ```

2. Verify watch folder exists and has proper permissions:
   ```bash
   ls -la /path/to/watch/folder
   ```

3. Test API connectivity:
   ```bash
   curl -X POST https://your-api.com/upload
   ```

### Files not being detected

1. Check file patterns in configuration
2. Verify file permissions
3. Check logs for errors:
   ```bash
   tail -f logs/xml-watcher.log
   ```

### Upload failures

1. Check API authentication credentials
2. Verify API endpoint is correct
3. Check network connectivity
4. Review API response in logs

## API Requirements

The service expects the API to accept multipart/form-data POST requests with:

- `file`: The XML file content
- `filename`: Original filename
- `size`: File size in bytes
- `path`: Full file path

Example API implementation (Python/Flask):

```python
@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    metadata = {
        'filename': request.form['filename'],
        'size': request.form['size'],
        'path': request.form['path']
    }
    # Process file...
    return jsonify({'status': 'success'})
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and feature requests, please create an issue on GitHub.
