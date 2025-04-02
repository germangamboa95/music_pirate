import asyncio
import json
import sys
import os
import re
import eyed3
from shazamio import Serialize, Shazam
import yt_dlp
from typing import Optional, Dict, Any
import requests
from io import BytesIO
import logging

# Configure logging based on environment variable
log_level = logging.DEBUG if os.environ.get(
    'LOG_LEVEL') == 'debug' else logging.WARNING
logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class DownloadError(Exception):
    """Raised when video download fails."""
    pass


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename by removing invalid characters.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    if not filename:
        return "untitled"

    # Remove file extension if present
    filename = os.path.splitext(filename)[0]

    # Replace invalid characters with underscores
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)

    # Replace spaces with underscores
    filename = filename.replace(' ', '_')

    # Replace non-ASCII characters
    filename = re.sub(r'[^\x00-\x7F]+', '_', filename)

    # Remove leading/trailing spaces and dots
    filename = filename.strip('. ')

    # Use 'untitled' if filename is empty after sanitization
    if not filename:
        return "untitled"

    # Truncate to maximum length (100 characters)
    return filename[:100]


def download_song(song_url: str):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': '~/Songs/current_download',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192'
        }],
    }
    os.makedirs('~/Songs', exist_ok=True)
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:

            info = ydl.extract_info(song_url, download=True)

            # Get video details
            video_id = info.get('id')
            if not video_id:
                raise DownloadError("Failed to get video ID")

            video_title = info.get('title', 'untitled')
            sanitized_title = sanitize_filename(video_title)
            os.rename(os.path.expanduser(f"~/Songs/current_download.mp3"),
                      os.path.expanduser(f'~/Songs/{sanitized_title}_{video_id}.mp3'))
            # Construct file paths

            downloaded_file = f'~/Songs/{
                sanitized_title}_{video_id}.mp3'

            return os.path.expanduser(downloaded_file)

        except yt_dlp.utils.DownloadError as e:
            raise DownloadError(f"Failed to download audio: {str(e)}")
        except Exception as e:
            raise DownloadError(
                f"Unexpected error during download: {str(e)}")


async def main(song_location: str):
    shazam = Shazam()

    out = await shazam.recognize(song_location)

    song = eyed3.load(song_location)
    artist_id = out["track"]["artists"][0]["adamid"]
    about_artist = await shazam.artist_about(artist_id)

    song.tag.title = out["track"]["title"]
    song.tag.artist = about_artist["data"][0]["attributes"]["name"]
    song.tag.save()


def run():
    """CLI entry point."""
    if len(sys.argv) < 2:
        logger.warning("Usage: steal <mp3_file_path>")
        return 1

    mp3_path = sys.argv[1]
    loop = asyncio.get_event_loop()
    return 0 if loop.run_until_complete(enrich_mp3_with_shazam(mp3_path)) else 1


async def get_track_info(audio_file_path: str) -> Optional[Dict[str, Any]]:
    """Recognize a song using ShazamIO and return enriched track information."""
    try:
        shazam = Shazam()
        recognition = await shazam.recognize(audio_file_path)

        if not recognition or 'track' not in recognition:
            logger.debug("No track recognized")
            return None

        track_key = recognition['track']['key']
        logger.debug(f"Track key found: {track_key}")
        return await shazam.track_about(track_key)
    except Exception as e:
        logger.debug(f"Recognition error: {e}")
        return None


def download_image(url: str) -> Optional[bytes]:
    """Download image from URL and return as bytes."""
    try:
        response = requests.get(url)
        return response.content if response.status_code == 200 else None
    except Exception as e:
        logger.debug(f"Image download error: {e}")
        return None


def apply_metadata_to_mp3(mp3_file_path: str, track_data: Dict[str, Any]) -> bool:
    """Apply ShazamIO track data to MP3 file using EyeD3."""
    try:
        audiofile = eyed3.load(mp3_file_path)
        if audiofile.tag is None:
            audiofile.initTag()

        # Basic metadata
        if title := track_data.get('title'):
            audiofile.tag.title = str(title)
            logger.debug(f"Set title: {title}")

        # Artist information
        artist = track_data.get('subtitle') or track_data.get('artistName')
        if artist:
            audiofile.tag.artist = str(artist)
            logger.debug(f"Set artist: {artist}")

        # Process sections for metadata
        if sections := track_data.get('sections'):
            # Extract metadata from sections
            for section in sections:
                # Handle lyrics
                if section.get('type') == 'LYRICS' and 'text' in section:
                    lyrics_text = '\n'.join(str(line)
                                            for line in section['text'])
                    audiofile.tag.lyrics.set(lyrics_text)
                    logger.debug("Set lyrics")

                # Handle other metadata
                if metadata_list := section.get('metadata'):
                    for metadata in metadata_list:
                        title, text = metadata.get(
                            'title'), metadata.get('text')
                        if not (title and text):
                            continue

                        if title == 'Album':
                            audiofile.tag.album = str(text)
                            logger.debug(f"Set album: {text}")
                        elif title == 'Released':
                            try:
                                year = int(str(text)[:4])
                                audiofile.tag.release_date = eyed3.core.Date(
                                    year)
                                logger.debug(f"Set release year: {year}")
                            except (ValueError, TypeError):
                                logger.debug(
                                    f"Could not parse release date: {text}")
                        elif title == 'Label':
                            audiofile.tag.publisher = str(text)
                            logger.debug(f"Set publisher: {text}")
                        elif title == 'Genre':
                            audiofile.tag.genre = str(text)
                            logger.debug(f"Set genre: {text}")

        # Cover artwork
        if images := track_data.get('images'):
            image_url = images.get('coverarthq') or images.get('coverart')
            if image_url and (image_data := download_image(image_url)):
                audiofile.tag.images.set(3, image_data, "image/jpeg", "Cover")
                logger.debug("Set cover artwork")

        # Add Shazam ID
        if key := track_data.get('key'):
            audiofile.tag.user_text_frames.set("SHAZAM_ID", str(key))
            logger.debug(f"Set Shazam ID: {key}")

        audiofile.tag.save()
        logger.debug(f"Successfully applied metadata to {mp3_file_path}")
        return True
    except Exception as e:
        logger.debug(f"Metadata application error: {e}")
        return False


async def enrich_mp3_with_shazam(mp3_file_path: str) -> bool:
    """Recognize and enrich an MP3 file with metadata from Shazam."""
    logger.debug(f"Processing file: {mp3_file_path}")
    if track_data := await get_track_info(mp3_file_path):
        return apply_metadata_to_mp3(mp3_file_path, track_data)
    logger.debug("No track data found")
    return False


if __name__ == "__main__":
    sys.exit(run())
