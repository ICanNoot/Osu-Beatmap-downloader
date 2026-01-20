# osu! Beatmap Downloader

A Python desktop application for downloading osu! beatmaps with PP (Performance Points) filtering.

## Features

- **Multi-mode support**: osu! Standard, Taiko, Catch, and Mania (4K/7K)
- **Star rating filter**: Filter by minimum and maximum star rating with decimal precision
- **PP filter**: Calculate max PP (100% SS) using rosu-pp-py and filter by PP range
- **Additional filters**: Length and BPM range filtering
- **Batch downloads**: Download multiple beatmaps with progress tracking
- **Local caching**: .osu files are cached locally for faster repeated searches
- **Dark theme UI**: Modern dark theme with osu! pink/purple accents

## Requirements

- Python 3.10+
- PyQt6
- ossapi
- rosu-pp-py
- aiohttp
- aiofiles

## Installation

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

## Configuration

Before using the application, you need to configure your osu! OAuth credentials:

1. Go to https://osu.ppy.sh/home/account/edit#oauth
2. Create a new OAuth application
3. Copy the Client ID and Client Secret
4. Click "Configure API" in the application and enter your credentials

## Usage

Run the application:
```bash
python main.py
```

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

## Project Structure

```
Osu-Beatmap-downloader/
├── main.py              # Entry point
├── requirements.txt     # Dependencies
├── README.md           # This file
├── src/
│   ├── __init__.py
│   ├── app.py          # Main application logic
│   ├── config.py       # Configuration management
│   ├── api_client.py   # osu! API wrapper
│   ├── pp_calculator.py # PP calculation
│   ├── downloader.py   # Download manager
│   └── gui.py          # PyQt6 GUI
├── cache/              # Cached .osu files (auto-created)
└── downloads/          # Downloaded .osz files (auto-created)
```

## Mirrors

The application uses beatmap mirrors to download .osu and .osz files:

- **catboy.best** (default)
- **nerinyan.moe** (alternative)

## License

MIT License
