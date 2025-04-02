

from asyncio.log import logger
from typing import Optional, Dict, Any
from shazamio import Shazam
import eyed3
import requests


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


async def enrich_mp3_with_shazam(mp3_file_path: str) -> bool:
    """Recognize and enrich an MP3 file with metadata from Shazam."""
    logger.debug(f"Processing file: {mp3_file_path}")
    if track_data := await get_track_info(mp3_file_path):
        return apply_metadata_to_mp3(mp3_file_path, track_data)
    logger.debug("No track data found")
    return False
