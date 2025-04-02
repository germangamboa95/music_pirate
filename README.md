# Music Pirate

Music Pirate is a Python tool that helps you download songs from YouTube and automatically enrich them with metadata using Shazam's audio recognition service.

## Features

- Download songs from YouTube URLs
- Convert videos to MP3 format
- Automatically recognize songs using Shazam
- Enrich MP3 files with metadata including:
  - Title and artist
  - Album information
  - Release date
  - Genre
  - Publisher/label
  - Cover artwork
  - Lyrics (when available)

## Installation

```bash
# Clone the repository
git clone https://github.com/username/music-pirate.git
cd music-pirate

# Install dependencies with Poetry
poetry install

```

## Usage

### Command Line Interface

To enrich an existing MP3 file with metadata:

```bash
poetry run steal <youtube-url>
```

### Python API

#### Download a song from YouTube

```python
from music_pirate import download_song

# Download a song from YouTube
mp3_path = download_song("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
print(f"Downloaded to: {mp3_path}")
```

#### Enrich an MP3 file with metadata

```python
import asyncio
from music_pirate import enrich_mp3_with_shazam

# Enrich an MP3 file with metadata from Shazam
async def process_file(file_path):
    result = await enrich_mp3_with_shazam(file_path)
    if result:
        print("Successfully enriched MP3 with metadata!")
    else:
        print("Failed to enrich MP3 file.")

# Run the async function
asyncio.run(process_file("/path/to/your/song.mp3"))
```

#### Complete workflow: Download and enrich

```python
import asyncio
from music_pirate import download_song, enrich_mp3_with_shazam

async def download_and_enrich(youtube_url):
    # Download the song
    mp3_path = download_song(youtube_url)
    print(f"Downloaded to: {mp3_path}")

    # Enrich with metadata
    result = await enrich_mp3_with_shazam(mp3_path)
    if result:
        print("Successfully enriched MP3 with metadata!")
    else:
        print("Failed to enrich MP3 file.")

    return mp3_path

# Run the async function
youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
asyncio.run(download_and_enrich(youtube_url))
```

## Debug Mode

To enable debug logging, set the `LOG_LEVEL` environment variable to `debug`:

```bash
LOG_LEVEL=debug poetry run steal /path/to/your/song.mp3
```

## Dependencies

All dependencies are managed through Poetry and specified in the `pyproject.toml` file:

- Python 3.7+
- yt-dlp
- eyed3
- shazamio
- requests

## License

[MIT License](LICENSE)
