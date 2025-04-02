import os
import re
import yt_dlp


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
