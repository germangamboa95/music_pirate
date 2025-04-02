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

## Debug Mode

To enable debug logging, set the `LOG_LEVEL` environment variable to `debug`:

```bash
LOG_LEVEL=debug poetry run steal https://www.youtube.com/watch?v=-zHm77FkW3U
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
