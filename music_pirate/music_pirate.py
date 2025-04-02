import asyncio
import sys
import os
import logging

from .enrichment import enrich_mp3_with_shazam
from .downloader import download_song


# Configure logging based on environment variable
log_level = logging.DEBUG if os.environ.get(
    'LOG_LEVEL') == 'debug' else logging.WARNING
logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def run():
    """CLI entry point."""
    if len(sys.argv) < 2:
        logger.warning("Usage: steal <mp3_file_path>")
        return 1

    youtube_url = sys.argv[1]
    loop = asyncio.get_event_loop()
    mp3_path = download_song(youtube_url)
    return 0 if loop.run_until_complete(enrich_mp3_with_shazam(mp3_path)) else 1


if __name__ == "__main__":
    sys.exit(run())
