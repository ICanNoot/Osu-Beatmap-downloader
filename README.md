# osu! Beatmap Downloader

A Python desktop application for downloading osu! beatmaps with PP (Performance Points) filtering.

## Download

### Pre-built Executables (Recommended)

Download the latest release for your operating system from the [Releases](../../releases) page:

- **Windows**: `OsuBeatmapDownloader.exe`
- **Linux**: `OsuBeatmapDownloader`
- **macOS**: `OsuBeatmapDownloader`

Just download and run - no installation required!

## Features

- **Multi-mode support**: osu! Standard, Taiko, Catch, and Mania (4K/7K)
- **Star rating filter**: Filter by minimum and maximum star rating with decimal precision
- **PP filter**: Calculate max PP (100% SS) using rosu-pp-py and filter by PP range
- **Additional filters**: Length and BPM range filtering
- **Batch downloads**: Download multiple beatmaps with progress tracking
- **Local caching**: .osu files are cached locally for faster repeated searches
- **Dark theme UI**: Modern dark theme with osu! pink/purple accents

## Configuration

Before using the application, you need to configure your osu! OAuth credentials:

1. Go to https://osu.ppy.sh/home/account/edit#oauth
2. Click "New OAuth Application"
3. Fill in:
   - **Application Name**: `Beatmap Downloader` (or anything you like)
   - **Application Callback URL**: `http://localhost`
4. Click "Register application"
5. Copy the **Client ID** and **Client Secret**
6. In the app, click "Configure API" and enter your credentials

## Usage

### Search Workflow

1. Select the game mode (Standard, Taiko, Catch, or Mania)
2. Set your desired filters:
   - Star rating range
   - PP range (100% SS)
   - Length range
   - BPM range
3. Set the maximum number of results
4. Click "Search Beatmaps"
5. Select the beatmaps you want to download
6. Click "Download Selected"

### PP Calculation

The application uses `rosu-pp-py` to calculate the maximum PP for each beatmap:

1. Beatmaps matching your basic filters are fetched from the osu! API
2. The .osu file for each beatmap is downloaded from a mirror (catboy.best)
3. PP is calculated for 100% accuracy (SS)
4. Results are filtered by your PP range

---

## Building from Source

If you want to build the application yourself or contribute to development:

### Requirements

- Python 3.10+
- pip

### Development Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Osu-Beatmap-downloader.git
cd Osu-Beatmap-downloader
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python main.py
```

### Building Executables

To create a standalone executable that anyone can run without Python:

#### Windows
```batch
build.bat
```
Or manually:
```batch
pip install pyinstaller
pyinstaller osu_downloader.spec --clean
```

#### Linux / macOS
```bash
./build.sh
```
Or manually:
```bash
pip install pyinstaller
pyinstaller osu_downloader.spec --clean
```

The executable will be created in the `dist/` folder:
- Windows: `dist/OsuBeatmapDownloader.exe`
- Linux/macOS: `dist/OsuBeatmapDownloader`

## Project Structure

```
Osu-Beatmap-downloader/
├── main.py               # Entry point
├── requirements.txt      # Dependencies
├── osu_downloader.spec   # PyInstaller configuration
├── build.bat             # Windows build script
├── build.sh              # Linux/macOS build script
├── README.md             # This file
├── src/
│   ├── __init__.py
│   ├── app.py            # Main application logic
│   ├── config.py         # Configuration management
│   ├── api_client.py     # osu! API wrapper
│   ├── pp_calculator.py  # PP calculation
│   ├── downloader.py     # Download manager
│   └── gui.py            # PyQt6 GUI
├── cache/                # Cached .osu files (auto-created)
└── downloads/            # Downloaded .osz files (auto-created)
```

## Mirrors

The application uses beatmap mirrors to download .osu and .osz files:

- **catboy.best** (default)
- **nerinyan.moe** (alternative)

## Troubleshooting

### "API not configured" error
Make sure you've entered your osu! OAuth credentials. Click "Configure API" and enter your Client ID and Client Secret.

### Search returns no results
- Check your filter settings - they might be too restrictive
- Make sure your API credentials are correct
- Try increasing the star rating range or PP range

### Downloads fail
- Check your internet connection
- The mirror might be temporarily down - try again later
- Make sure you have write permissions in the downloads folder

## License

MIT License
