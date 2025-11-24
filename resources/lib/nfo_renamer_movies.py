#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import sys

# Python 2/3 compatibility for Unicode handling
if sys.version_info[0] == 2:
    # Python 2: Set default encoding to UTF-8
    if sys.getdefaultencoding() != 'utf-8':
        reload(sys)
        sys.setdefaultencoding('utf-8')

# Try to import Kodi modules, but provide fallbacks for CLI usage
try:
    import xbmc
    import xbmcgui
    import xbmcaddon
    IN_KODI = True
except ImportError:
    IN_KODI = False

"""
NFO Renamer Movies

This script reads TV show and movie NFO files and renames associated video files to the extended format:

TV Show format:
SSxEE - Episode Title - Show Title - Genre - Resolution - Audio Channels - Audio Codec - Holiday.ext

Movie format:
Title - Mpaa Rating - Genre - Resolution - Audio Channels - Audio Codec - Holiday.ext

It preserves the original NFO file content but renames both the NFO and video files.
Genre, show title, and other information are obtained from parent folder NFO files if not available in episode NFO.
Holiday detection (Christmas/Thanksgiving/Halloween/None) is based on plot text analysis.

IMPROVED: 
- Now handles both TV shows and movies
- Auto-detects content type (movie or TV show)
- Skips files that are already in the correct format
- Sanitizes filenames to remove invalid Windows characters
- Handles colons and other special characters in filenames
- Scans for poster.jpg files and creates folder.jpg copies for Kodi compatibility
"""

import argparse
import logging
import os
import re
import shutil
import xml.etree.ElementTree as ET

import xbmcvfs

# Configure logging - console only
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Video file extensions to process
VIDEO_EXTENSIONS = [".mkv", ".mp4", ".avi", ".m4v", ".ts", ".mov"]
# Resolution mapping
RESOLUTION_MAP = {
    "2160p": "2160",
    "4k": "2160",
    "4K": "2160",
    "1080p": "1080",
    "1080P": "1080",
    "720p": "720",
    "720P": "720",
    "480p": "480",
    "480P": "480",
    "SD": "480",
}

# Common audio codec mappings (abbreviations to standardized forms)
AUDIO_CODEC_MAP = {
    "ac3": "AC3",
    "eac3": "EAC3",
    "dts": "DTS",
    "dtshd": "DTS-HD",
    "dtshd_ma": "DTS-HD",  # Added for DTS-HD Master Audio
    "truehd": "TrueHD",
    "aac": "AAC",
    "mp3": "MP3",
    "flac": "FLAC",
    "pcm": "PCM",
    "dca": "DTS",  # DCA is often used for DTS
    "opus": "OPUS",
}

# Holiday keywords to search for in plot text
HOLIDAY_KEYWORDS = {
    "Christmas": ["christmas", "xmas", "santa", "december 25", "noel", "yule"],
    "Thanksgiving": ["thanksgiving", "turkey day", "pilgrim"],
    "Halloween": [
        "halloween",
        "trick or treat",
        "trick-or-treat",
        "spooky",
        "october 31",
        "all hallows",
    ],
}

# Invalid characters for Windows filenames
INVALID_FILENAME_CHARS = ["<", ">", ":", '"', "/", "\\", "|", "?", "*"]

# Cache for tvshow.nfo metadata to avoid re-parsing the same file multiple times
tvshow_metadata_cache = {}

# Pattern to detect if a file is already in the extended TV format
# Format: SSxEE - Episode Title - Show Title - Genre - Resolution - Audio Channels - Audio Codec - Holiday.ext
EXTENDED_TV_FORMAT_PATTERN = re.compile(
    r"^\d+x\d+ - .+ - .+ - .+ - \d+ - \d+ - [A-Za-z0-9-]+ - [A-Za-z]+"
)

# Pattern to detect if a file is already in the extended movie format
# Format: Title - Mpaa Rating - Genre - Resolution - Audio Channels - Audio Codec - Holiday.ext
EXTENDED_MOVIE_FORMAT_PATTERN = re.compile(
    r"^.+ - [A-Za-z0-9-]+ - .+ - \d+ - \d+ - [A-Za-z0-9-]+ - [A-Za-z]+"
)


# Function to sanitize filenames for Windows compatibility
def sanitize_filename(filename):
    """
    Remove or replace characters that are invalid in Windows filenames
    """
    # Ensure filename is unicode
    if isinstance(filename, str):
        filename = filename.decode("utf-8")

    # Replace colons with a safe alternative
    sanitized = filename.replace(":", ".")

    # Replace other invalid characters
    for char in INVALID_FILENAME_CHARS:
        if char in sanitized:
            sanitized = sanitized.replace(char, "_")

    # Replace multiple periods with a single period
    sanitized = re.sub(r"\.+", ".", sanitized)

    # Check if the filename is valid after sanitization
    if sanitized != filename:
        logger.info("Sanitized filename: '{}' -> '{}'".format(filename, sanitized))

    return sanitized


# Function to check if a file is already in the extended format
def is_already_extended_format(filename, content_type="tvshow"):
    """
    Check if the filename is already in the extended format
    Returns True if it matches the pattern, False otherwise

    Args:
        filename: The filename to check
        content_type: Either 'tvshow' or 'movie'
    """
    # Strip extension
    base_name = os.path.splitext(filename)[0]

    if content_type == "tvshow":
        # Check if it matches the TV show pattern
        if EXTENDED_TV_FORMAT_PATTERN.match(base_name):
            return True

        # More detailed analysis: check format parts
        parts = base_name.split(" - ")

        # Check if we have at least 7 hyphens (for 8 parts)
        if len(parts) < 8:
            return False

        # Check if first part matches SSxEE format
        if not re.match(r"^\d+x\d+$", parts[0]):
            return False

        # If resolution part exists and is numeric
        if not parts[4].isdigit():
            return False

        # If audio channels part exists and is numeric
        if not parts[5].isdigit():
            return False

        # If holiday part exists and is valid
        if parts[7] not in ["Christmas", "Thanksgiving", "Halloween", "None"]:
            return False

        # If we got here, it's likely already in the extended format
        return True

    elif content_type == "movie":
        # Check if it matches the movie pattern
        if EXTENDED_MOVIE_FORMAT_PATTERN.match(base_name):
            return True

        # More detailed analysis: check format parts
        parts = base_name.split(" - ")

        # Check if we have at least 6 hyphens (for 7 parts)
        if len(parts) < 7:
            return False

        # Check if MPAA rating looks valid (second part)
        valid_ratings = [
            "G",
            "PG",
            "PG-13",
            "R",
            "NC-17",
            "NR",
            "TV-Y",
            "TV-Y7",
            "TV-G",
            "TV-PG",
            "TV-14",
            "TV-MA",
        ]
        if parts[1] not in valid_ratings:
            return False

        # If resolution part exists and is numeric
        if not parts[3].isdigit():
            return False

        # If audio channels part exists and is numeric
        if not parts[4].isdigit():
            return False

        # If holiday part exists and is valid
        if parts[6] not in ["Christmas", "Thanksgiving", "Halloween", "None"]:
            return False

        # If we got here, it's likely already in the extended format
        return True

    # Unrecognized content type
    return False


def detect_holiday(plot_text):
    """
    Detect holiday references in the plot text
    Returns 'Christmas', 'Thanksgiving', 'Halloween', or 'None' based on keywords found
    """
    if not plot_text:
        return "None"

    # Convert to lowercase for case-insensitive matching
    plot_lower = plot_text.lower()

    # Check for each holiday's keywords
    for holiday, keywords in HOLIDAY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in plot_lower:
                logger.info(
                    "Detected {} episode/movie based on keyword '{}'".format(
                        holiday, keyword
                    )
                )
                return holiday

    # No holiday keywords found
    return "None"


def process_poster_to_folder(directory, dry_run=False):
    """
    Look for poster.jpg in the directory and copy it as folder.jpg if folder.jpg doesn't exist.
    This ensures media folders have the proper artwork for Kodi.

    Args:
        directory: Directory to process
        dry_run: If True, only log what would happen without copying

    Returns:
        Boolean indicating if a copy was made (or would be made in dry_run mode)
    """
    poster_path = os.path.join(directory, "poster.jpg")
    folder_path = os.path.join(directory, "folder.jpg")

    # Check if poster.jpg exists and folder.jpg doesn't
    if xbmcvfs.exists(poster_path) and not xbmcvfs.exists(folder_path):
        logger.info("Found poster.jpg in: {}".format(directory))

        if dry_run:
            logger.info(
                "[DRY RUN] Would copy poster.jpg to folder.jpg in: {}".format(directory)
            )
            return True
        else:
            try:
                # Copy poster.jpg to folder.jpg
                success = xbmcvfs.copy(poster_path, folder_path)
                if success:
                    logger.info(
                        "Successfully copied poster.jpg to folder.jpg in: {}".format(
                            directory
                        )
                    )
                    return True
                else:
                    logger.error(
                        "Failed to copy poster.jpg to folder.jpg in: {}".format(
                            directory
                        )
                    )
                    return False
            except Exception as e:
                logger.error(
                    "Error copying poster.jpg to folder.jpg in {}: {}".format(
                        directory, e
                    )
                )
                return False

    return False


def scan_for_posters(root_directory, dry_run=False, recursive=True):
    """
    Scan directory tree for poster.jpg files and create folder.jpg copies where needed.

    Args:
        root_directory: Starting directory for scan
        dry_run: If True, only log what would happen
        recursive: If True, scan subdirectories

    Returns:
        Dictionary with statistics
    """
    stats = {
        "directories_scanned": 0,
        "posters_found": 0,
        "folders_created": 0,
        "errors": 0,
    }

    logger.info("Starting poster scan in: {}".format(root_directory))

    # Process the root directory first
    stats["directories_scanned"] += 1
    if process_poster_to_folder(root_directory, dry_run):
        stats["posters_found"] += 1
        stats["folders_created"] += 1

    # If recursive, process subdirectories
    if recursive:
        try:
            dirs, files = xbmcvfs.listdir(root_directory)

            for dirname in dirs:
                dir_path = os.path.join(root_directory, dirname)
                stats["directories_scanned"] += 1

                # Check this directory for poster.jpg
                if process_poster_to_folder(dir_path, dry_run):
                    stats["posters_found"] += 1
                    stats["folders_created"] += 1

                # Recursively scan subdirectories
                if recursive:
                    sub_stats = scan_for_posters(dir_path, dry_run, recursive)
                    # Merge statistics
                    stats["directories_scanned"] += sub_stats["directories_scanned"]
                    stats["posters_found"] += sub_stats["posters_found"]
                    stats["folders_created"] += sub_stats["folders_created"]
                    stats["errors"] += sub_stats["errors"]

        except Exception as e:
            logger.error("Error scanning directory {}: {}".format(root_directory, e))
            stats["errors"] += 1

    return stats


def detect_content_type(nfo_path):
    """
    Detect if the NFO file is for a TV show or movie
    Returns 'tvshow', 'movie', or None if unable to determine
    """
    try:
        # Read the file content using xbmcvfs
        f = xbmcvfs.File(nfo_path, "r")
        content = f.read()
        f.close()

        # Decode content if it's a string (not unicode)
        if isinstance(content, str):
            content = content.decode("utf-8")

        # Parse XML from string content
        root = ET.fromstring(content.encode("utf-8"))

        # Check for TV show specific elements
        season_elem = root.find(".//season")
        episode_elem = root.find(".//episode")
        showtitle_elem = root.find(".//showtitle")

        # Check for movie specific elements
        mpaa_elem = root.find(".//mpaa")
        movie_set_elem = root.find(".//set")

        # Logic to determine content type
        if (
            season_elem is not None
            or episode_elem is not None
            or showtitle_elem is not None
        ):
            return "tvshow"
        elif mpaa_elem is not None or movie_set_elem is not None:
            return "movie"

        # Check file and directory name patterns
        filename = os.path.basename(nfo_path)
        if "movie" in filename.lower():
            return "movie"

        # Check if in a season folder
        parent_dir = os.path.basename(os.path.dirname(nfo_path))
        if re.match(r"[Ss]eason\s*\d+", parent_dir, re.IGNORECASE):
            return "tvshow"

        # Check if there's a tvshow.nfo in the parent directory
        parent_dir_path = os.path.dirname(nfo_path)
        tvshow_nfo_path = os.path.join(parent_dir_path, "tvshow.nfo")
        if xbmcvfs.exists(tvshow_nfo_path):
            return "tvshow"

        # If no clear indicators, check for season/episode in filename
        base_name = os.path.splitext(filename)[0]
        if re.search(
            r"[sS]\d+[eE]\d+|[sS]eason\s*\d+|[eE]pisode\s*\d+|\d+x\d+", base_name
        ):
            return "tvshow"

        # If all else fails, assume it's a movie
        return "movie"

    except Exception as e:
        logger.error("Error detecting content type for {}: {}".format(nfo_path, e))
        return None


def parse_tv_nfo_file(nfo_path):
    """
    Parse TV show NFO file to extract metadata
    Returns a dictionary with season, episode, title, show name, genre, etc.
    """
    try:
        # Read the file content using xbmcvfs
        f = xbmcvfs.File(nfo_path, "r")
        content = f.read()
        f.close()

        # Decode content if it's a string (not unicode)
        if isinstance(content, str):
            content = content.decode("utf-8")

        # Parse XML from string content
        root = ET.fromstring(content.encode("utf-8"))

        # Initialize metadata with defaults
        metadata = {
            "content_type": "tvshow",
            "season": None,
            "episode": None,
            "title": None,
            "showtitle": None,
            "genre": None,
            "resolution": None,
            "audio_channels": None,
            "audio_codec": None,
            "holiday": "None",  # Default to 'None' for holiday
        }

        # Extract season and episode
        season_elem = root.find(".//season")
        episode_elem = root.find(".//episode")

        if season_elem is not None and season_elem.text:
            metadata["season"] = int(season_elem.text)
        if episode_elem is not None and episode_elem.text:
            metadata["episode"] = int(episode_elem.text)

        # Extract title
        title_elem = root.find(".//title")
        if title_elem is not None and title_elem.text:
            metadata["title"] = title_elem.text.strip()

        # Extract show title
        showtitle_elem = root.find(".//showtitle")
        if showtitle_elem is not None and showtitle_elem.text:
            metadata["showtitle"] = showtitle_elem.text.strip()

        # Extract genre - take the first one if multiple are present
        genre_elem = root.find(".//genre")
        if genre_elem is not None and genre_elem.text:
            metadata["genre"] = genre_elem.text.strip()

        # Extract plot for holiday detection
        plot_elem = root.find(".//plot")
        if plot_elem is not None and plot_elem.text:
            plot_text = plot_elem.text.strip()
            # Detect holiday based on plot text
            metadata["holiday"] = detect_holiday(plot_text)

        # Try to determine resolution from various sources
        # First check if there's a videoinfo/resolution element
        resolution_elem = root.find(".//videoinfo/resolution") or root.find(
            ".//resolution"
        )
        if resolution_elem is not None and resolution_elem.text:
            res_text = resolution_elem.text.strip()
            # Map resolution text to our format
            for key, value in RESOLUTION_MAP.items():
                if key in res_text:
                    metadata["resolution"] = value
                    break

        # Extract audio information
        # First try the standard location
        audio_elem = root.findall(".//streamdetails/audio")
        if audio_elem:
            # Use the first audio stream for channels and codec
            channels_elem = audio_elem[0].find("./channels")
            if channels_elem is not None and channels_elem.text:
                metadata["audio_channels"] = channels_elem.text.strip()

            codec_elem = audio_elem[0].find("./codec")
            if codec_elem is not None and codec_elem.text:
                codec = codec_elem.text.strip().lower()
                # Map to standardized codec name if possible
                metadata["audio_codec"] = AUDIO_CODEC_MAP.get(codec, codec.upper())

        # Alternative locations for older NFO formats
        if metadata["audio_channels"] is None:
            channels_elem = root.find(".//channels") or root.find(".//audiochannels")
            if channels_elem is not None and channels_elem.text:
                metadata["audio_channels"] = channels_elem.text.strip()

        if metadata["audio_codec"] is None:
            codec_elem = root.find(".//audiocodec") or root.find(".//codec")
            if codec_elem is not None and codec_elem.text:
                codec = codec_elem.text.strip().lower()
                metadata["audio_codec"] = AUDIO_CODEC_MAP.get(codec, codec.upper())

        return metadata

    except ET.ParseError as e:
        logger.error("Error parsing XML in {}: {}".format(nfo_path, e))
        return None
    except Exception as e:
        logger.error("Error processing {}: {}".format(nfo_path, e))
        return None


def parse_movie_nfo_file(nfo_path):
    """
    Parse movie NFO file to extract metadata
    Returns a dictionary with title, mpaa rating, genre, etc.
    """
    try:
        # Read the file content using xbmcvfs
        f = xbmcvfs.File(nfo_path, "r")
        content = f.read()
        f.close()

        # Decode content if it's a string (not unicode)
        if isinstance(content, str):
            content = content.decode("utf-8")

        # Parse XML from string content
        root = ET.fromstring(content.encode("utf-8"))

        # Initialize metadata with defaults
        metadata = {
            "content_type": "movie",
            "title": None,
            "mpaa": "NR",  # Default to Not Rated
            "genre": None,
            "resolution": None,
            "audio_channels": None,
            "audio_codec": None,
            "holiday": "None",  # Default to 'None' for holiday
        }

        # Extract title
        title_elem = root.find(".//title")
        if title_elem is not None and title_elem.text:
            metadata["title"] = title_elem.text.strip()

        # Extract MPAA rating
        mpaa_elem = root.find(".//mpaa")
        if mpaa_elem is not None and mpaa_elem.text:
            mpaa_text = mpaa_elem.text.strip()
            # Extract just the rating part (e.g. "Rated R" -> "R")
            rating_match = re.search(r"(?:Rated\s+)?([A-Za-z0-9-]+)", mpaa_text)
            if rating_match:
                metadata["mpaa"] = rating_match.group(1)
            else:
                metadata["mpaa"] = mpaa_text

        # Extract genre - take the first one if multiple are present
        genre_elem = root.find(".//genre")
        if genre_elem is not None and genre_elem.text:
            metadata["genre"] = genre_elem.text.strip()

        # Extract plot for holiday detection
        plot_elem = root.find(".//plot")
        if plot_elem is not None and plot_elem.text:
            plot_text = plot_elem.text.strip()
            # Detect holiday based on plot text
            metadata["holiday"] = detect_holiday(plot_text)

        # Try to determine resolution from various sources
        # First check if there's a videoinfo/resolution element
        resolution_elem = root.find(".//videoinfo/resolution") or root.find(
            ".//resolution"
        )
        if resolution_elem is not None and resolution_elem.text:
            res_text = resolution_elem.text.strip()
            # Map resolution text to our format
            for key, value in RESOLUTION_MAP.items():
                if key in res_text:
                    metadata["resolution"] = value
                    break

        # Extract audio information
        # First try the standard location
        audio_elem = root.findall(".//streamdetails/audio")
        if audio_elem:
            # Use the first audio stream for channels and codec
            channels_elem = audio_elem[0].find("./channels")
            if channels_elem is not None and channels_elem.text:
                metadata["audio_channels"] = channels_elem.text.strip()

            codec_elem = audio_elem[0].find("./codec")
            if codec_elem is not None and codec_elem.text:
                codec = codec_elem.text.strip().lower()
                # Map to standardized codec name if possible
                metadata["audio_codec"] = AUDIO_CODEC_MAP.get(codec, codec.upper())

        # Alternative locations for older NFO formats
        if metadata["audio_channels"] is None:
            channels_elem = root.find(".//channels") or root.find(".//audiochannels")
            if channels_elem is not None and channels_elem.text:
                metadata["audio_channels"] = channels_elem.text.strip()

        if metadata["audio_codec"] is None:
            codec_elem = root.find(".//audiocodec") or root.find(".//codec")
            if codec_elem is not None and codec_elem.text:
                codec = codec_elem.text.strip().lower()
                metadata["audio_codec"] = AUDIO_CODEC_MAP.get(codec, codec.upper())

        return metadata

    except ET.ParseError as e:
        logger.error("Error parsing XML in {}: {}".format(nfo_path, e))
        return None
    except Exception as e:
        logger.error("Error processing {}: {}".format(nfo_path, e))
        return None


def get_tvshow_metadata(episode_nfo_path):
    """
    Get show metadata from tvshow.nfo in the parent directory
    Returns dictionary with genre and show title information
    """
    # Get parent directory
    parent_dir = os.path.dirname(episode_nfo_path)

    # Check cache first
    if parent_dir in tvshow_metadata_cache:
        logger.debug("Using cached tvshow metadata for {}".format(parent_dir))
        return tvshow_metadata_cache[parent_dir]

    # Path to tvshow.nfo
    tvshow_nfo_path = os.path.join(parent_dir, "tvshow.nfo")

    # If we're already in a season subfolder, go up one level
    if not xbmcvfs.exists(tvshow_nfo_path):
        # Check if current folder name matches season pattern (Season X, season X, etc.)
        current_folder = os.path.basename(parent_dir)
        if re.match(r"[Ss]eason\s*\d+", current_folder, re.IGNORECASE):
            # Go up one level
            show_dir = os.path.dirname(parent_dir)
            tvshow_nfo_path = os.path.join(show_dir, "tvshow.nfo")

    # Check if tvshow.nfo exists
    if not xbmcvfs.exists(tvshow_nfo_path):
        logger.warning("tvshow.nfo not found for {}".format(episode_nfo_path))
        return {"genre": None, "showtitle": None}

    # Initialize metadata with defaults
    tvshow_metadata = {"genre": None, "showtitle": None}

    # Parse tvshow.nfo
    try:
        # Read the file content using xbmcvfs
        f = xbmcvfs.File(tvshow_nfo_path, "r")
        content = f.read()
        f.close()

        # Decode content if it's a string (not unicode)
        if isinstance(content, str):
            content = content.decode("utf-8")

        # Parse XML from string content
        root = ET.fromstring(content.encode("utf-8"))

        # Extract genre
        genre_elem = root.find(".//genre")
        if genre_elem is not None and genre_elem.text:
            tvshow_metadata["genre"] = genre_elem.text.strip()
            logger.info(
                "Found genre '{}' in tvshow.nfo for {}".format(
                    tvshow_metadata["genre"], parent_dir
                )
            )

        # Extract show title - check multiple possible tags
        # First check originaltitle (as in the American Dad! example)
        originaltitle_elem = root.find(".//originaltitle")
        if originaltitle_elem is not None and originaltitle_elem.text:
            tvshow_metadata["showtitle"] = originaltitle_elem.text.strip()
            logger.info(
                "Found show title '{}' from originaltitle tag in tvshow.nfo".format(
                    tvshow_metadata["showtitle"]
                )
            )
        else:
            # If not found, try title tag
            title_elem = root.find(".//title")
            if title_elem is not None and title_elem.text:
                tvshow_metadata["showtitle"] = title_elem.text.strip()
                logger.info(
                    "Found show title '{}' from title tag in tvshow.nfo".format(
                        tvshow_metadata["showtitle"]
                    )
                )

        # Cache the result
        tvshow_metadata_cache[parent_dir] = tvshow_metadata

        return tvshow_metadata

    except ET.ParseError as e:
        logger.error("Error parsing XML in tvshow.nfo: {}".format(e))
        return {"genre": None, "showtitle": None}
    except Exception as e:
        logger.error("Error processing tvshow.nfo: {}".format(e))
        return {"genre": None, "showtitle": None}


def get_resolution_from_filename(filename):
    """Extract resolution from filename if present"""
    for key in RESOLUTION_MAP:
        if key in filename:
            return RESOLUTION_MAP[key]
    return "1080"  # Default to 1080p if not found


def create_extended_tv_filename(metadata, original_ext):
    """
    Create new TV show filename based on metadata and original extension
    Sanitizes the filename to ensure Windows compatibility
    """
    # Use detected metadata, setting defaults if items are missing
    season = metadata.get("season", 1)
    episode = metadata.get("episode", 1)
    title = metadata.get("title", "Unknown Title")
    showtitle = metadata.get("showtitle", "Unknown Show")
    genre = metadata.get("genre", "Unknown")
    resolution = metadata.get("resolution", "1080")
    audio_channels = metadata.get("audio_channels", "2")  # Default to stereo
    audio_codec = metadata.get("audio_codec", "AAC")  # Default to AAC
    holiday = metadata.get("holiday", "None")  # Default to 'None'

    # Format the new filename
    filename = "{:02d}x{:02d} - {} - {} - {} - {} - {} - {} - {}{}".format(
        season,
        episode,
        title,
        showtitle,
        genre,
        resolution,
        audio_channels,
        audio_codec,
        holiday,
        original_ext,
    )

    # Sanitize the filename for Windows compatibility
    return sanitize_filename(filename)


def create_extended_movie_filename(metadata, original_ext):
    """
    Create new movie filename based on metadata and original extension
    Sanitizes the filename to ensure Windows compatibility
    """
    # Use detected metadata, setting defaults if items are missing
    title = metadata.get("title", "Unknown Title")
    mpaa = metadata.get("mpaa", "NR")  # Default to Not Rated
    genre = metadata.get("genre", "Unknown")
    resolution = metadata.get("resolution", "1080")
    audio_channels = metadata.get("audio_channels", "2")  # Default to stereo
    audio_codec = metadata.get("audio_codec", "AAC")  # Default to AAC
    holiday = metadata.get("holiday", "None")  # Default to 'None'

    # Format the new filename
    filename = "{} - {} - {} - {} - {} - {} - {}{}".format(
        title,
        mpaa,
        genre,
        resolution,
        audio_channels,
        audio_codec,
        holiday,
        original_ext,
    )

    # Sanitize the filename for Windows compatibility
    return sanitize_filename(filename)


def rename_files(directory, dry_run=False, recursive=False, progress_callback=None, depth=0, progress_state=None):
    """
    Process directory and rename files according to extended format for both TV shows and movies

    Args:
        directory: The directory to process
        dry_run: If True, don't actually rename files, just show what would happen
        recursive: If True, process subdirectories recursively
        progress_callback: Optional callback function(current, total, message) for progress updates
        depth: Current recursion depth (for tracking subdirectories)
        progress_state: Shared dict for tracking progress across recursive calls
    """
    print("Starting rename_files with directory: {}".format(directory))
    logger.info("Starting rename_files with directory: {}".format(directory))

    # First scan for poster.jpg files and create folder.jpg copies
    print("\nScanning for poster.jpg files to copy as folder.jpg...")
    poster_stats = scan_for_posters(directory, dry_run, recursive)
    print(
        "Poster scan complete: {} directories scanned, {} posters found, {} folders created".format(
            poster_stats["directories_scanned"],
            poster_stats["posters_found"],
            poster_stats["folders_created"],
        )
    )
    if poster_stats["errors"] > 0:
        print(
            "  Errors encountered during poster scan: {}".format(poster_stats["errors"])
        )
    print("")  # Blank line for readability

    # Check if directory exists using xbmcvfs
    if not xbmcvfs.exists(directory):
        logger.error("Directory not found: {}".format(directory))
        print("ERROR: Directory not found: {}".format(directory))
        return

    # List directory contents using xbmcvfs
    try:
        dirs, files = xbmcvfs.listdir(directory)
        all_items = dirs + files
        logger.info("Directory contents: {} files/folders found".format(len(all_items)))
        print("Directory contents: {} files/folders found".format(len(all_items)))
    except Exception as e:
        logger.error("Failed to list directory contents: {}".format(e))
        print("ERROR: Failed to list directory contents: {}".format(e))
        return

    # Track statistics
    stats = {
        "processed": 0,
        "renamed": 0,
        "errors": 0,
        "skipped": 0,
        "already_extended": 0,
        "genre_from_tvshow": 0,
        "showtitle_from_tvshow": 0,
        "christmas_episodes": 0,
        "thanksgiving_episodes": 0,
        "halloween_episodes": 0,
        "tv_shows": 0,
        "movies": 0,
    }

    # Initialize progress state at root level (depth 0)
    if depth == 0 and progress_callback and progress_state is None:
        progress_state = {"total_nfos": 0, "current_nfo": 0}
        # Count total NFO files recursively
        def count_nfos(dir_path):
            count = 0
            try:
                subdirs, subfiles = xbmcvfs.listdir(dir_path)
                for f in subfiles:
                    if f.lower().endswith(".nfo") and f.lower() != "tvshow.nfo":
                        count += 1
                if recursive:
                    for d in subdirs:
                        count += count_nfos(os.path.join(dir_path, d))
            except Exception as e:
                pass
            return count
        progress_state["total_nfos"] = count_nfos(directory)

    # Process directories first if recursive
    if recursive:
        for dirname in dirs:
            dir_path = os.path.join(directory, dirname)
            sub_stats = rename_files(dir_path, dry_run, recursive, progress_callback, depth + 1, progress_state)
            if sub_stats:
                for key in stats:
                    if key in sub_stats:
                        stats[key] += sub_stats[key]

    # Process files in the current directory
    for filename in files:
        file_path = os.path.join(directory, filename)

        # Check if this is an NFO file (not tvshow.nfo)
        if filename.lower().endswith(".nfo") and filename.lower() != "tvshow.nfo":
            stats["processed"] += 1

            # Update progress if callback provided (use shared progress_state)
            if progress_callback and progress_state:
                progress_state["current_nfo"] += 1
                percent = int((progress_state["current_nfo"] * 100) / progress_state["total_nfos"]) if progress_state["total_nfos"] > 0 else 0
                # Get shortened filename for display
                display_name = filename if len(filename) <= 40 else filename[:37] + "..."
                progress_callback(percent, "Processing: {} ({}/{})".format(
                    display_name, progress_state["current_nfo"], progress_state["total_nfos"]
                ))

            # Get base name without extension
            base_name = os.path.splitext(filename)[0]

            # Look for associated video file with matching base name
            video_file = None
            video_ext = None

            for ext in VIDEO_EXTENSIONS:
                potential_video = base_name + ext
                potential_path = os.path.join(directory, potential_video)
                if xbmcvfs.exists(potential_path):
                    video_file = potential_video
                    video_ext = ext
                    break

            if not video_file:
                logger.warning(
                    "No matching video file found for NFO: {}".format(filename)
                )
                stats["skipped"] += 1
                continue

            # Detect content type (tv show or movie)
            full_nfo_path = os.path.join(directory, filename)
            content_type = detect_content_type(full_nfo_path)

            if content_type is None:
                logger.error("Could not determine content type for {}".format(filename))
                stats["errors"] += 1
                continue

            # Check if video file is already in extended format
            if is_already_extended_format(video_file, content_type):
                logger.info("File already in extended format: {}".format(video_file))
                stats["already_extended"] += 1
                stats["skipped"] += 1
                continue

            # Parse NFO file based on content type
            if content_type == "tvshow":
                metadata = parse_tv_nfo_file(full_nfo_path)
                stats["tv_shows"] += 1
            else:  # movie
                metadata = parse_movie_nfo_file(full_nfo_path)
                stats["movies"] += 1

            if not metadata:
                logger.error("Failed to parse NFO: {}".format(filename))
                stats["errors"] += 1
                continue

            # TV Show specific processing
            if content_type == "tvshow":
                # If we're missing critical metadata, try to extract from filename
                if metadata["season"] is None or metadata["episode"] is None:
                    # Try to extract season and episode from filename
                    season_ep_match = re.search(r"[sS](\d+)[eE](\d+)", base_name)
                    if season_ep_match:
                        metadata["season"] = int(season_ep_match.group(1))
                        metadata["episode"] = int(season_ep_match.group(2))
                    else:
                        # Try NxNN format
                        season_ep_match = re.search(r"(\d+)x(\d+)", base_name)
                        if season_ep_match:
                            metadata["season"] = int(season_ep_match.group(1))
                            metadata["episode"] = int(season_ep_match.group(2))

                # Get missing TV show metadata from tvshow.nfo
                need_tvshow_metadata = False
                if not metadata["genre"] or not metadata["showtitle"]:
                    need_tvshow_metadata = True

                if need_tvshow_metadata:
                    tvshow_metadata = get_tvshow_metadata(full_nfo_path)

                    # If genre is missing, get it from tvshow.nfo
                    if not metadata["genre"] and tvshow_metadata["genre"]:
                        metadata["genre"] = tvshow_metadata["genre"]
                        stats["genre_from_tvshow"] += 1
                        logger.info(
                            "Using genre from tvshow.nfo: {}".format(
                                tvshow_metadata["genre"]
                            )
                        )

                    # If show title is missing, get it from tvshow.nfo
                    if not metadata["showtitle"] and tvshow_metadata["showtitle"]:
                        metadata["showtitle"] = tvshow_metadata["showtitle"]
                        stats["showtitle_from_tvshow"] += 1
                        logger.info(
                            "Using show title from tvshow.nfo: {}".format(
                                tvshow_metadata["showtitle"]
                            )
                        )

            # Common processing for both TV shows and movies

            # Update holiday statistics
            if metadata["holiday"] == "Christmas":
                stats["christmas_episodes"] += 1
            elif metadata["holiday"] == "Thanksgiving":
                stats["thanksgiving_episodes"] += 1
            elif metadata["holiday"] == "Halloween":
                stats["halloween_episodes"] += 1

            # If resolution not in NFO, try to get from filename
            if not metadata["resolution"]:
                metadata["resolution"] = get_resolution_from_filename(base_name)

            # Try to extract audio information from filename if not in NFO
            if not metadata["audio_channels"] or not metadata["audio_codec"]:
                # Look for patterns like "5.1" or "7.1" for channels
                channels_match = re.search(
                    r"(\d+\.\d+)ch|(\d+)ch|(\d+\.\d+)|(\d+)channels", base_name.lower()
                )
                if channels_match:
                    # Use the first non-None group
                    for group in channels_match.groups():
                        if group:
                            metadata["audio_channels"] = group
                            break

                # Look for audio codec indicators
                for codec, standardized in AUDIO_CODEC_MAP.items():
                    if codec.lower() in base_name.lower():
                        metadata["audio_codec"] = standardized
                        break

            # Create new filenames based on content type
            if content_type == "tvshow":
                new_base_name = create_extended_tv_filename(metadata, "")
            else:  # movie
                new_base_name = create_extended_movie_filename(metadata, "")

            new_video_name = new_base_name + video_ext
            new_nfo_name = new_base_name + ".nfo"

            # Check if rename is actually needed (names might already match)
            if new_video_name == video_file and new_nfo_name == filename:
                logger.info("Files already have correct naming: {}".format(filename))
                stats["skipped"] += 1
                continue

            # Log the rename operation
            logger.info(
                "Renaming ({}):\n  {} -> {}\n  {} -> {}".format(
                    content_type, filename, new_nfo_name, video_file, new_video_name
                )
            )

            if not dry_run:
                try:
                    # Rename video file
                    video_src = os.path.join(directory, video_file)
                    video_dst = os.path.join(directory, new_video_name)
                    xbmcvfs.rename(video_src, video_dst)

                    # Rename NFO file
                    nfo_src = os.path.join(directory, filename)
                    nfo_dst = os.path.join(directory, new_nfo_name)
                    xbmcvfs.rename(nfo_src, nfo_dst)

                    stats["renamed"] += 1
                except Exception as e:
                    logger.error("Error renaming files: {}".format(e))
                    stats["errors"] += 1

    # Log summary for this directory
    logger.info(
        "Directory {} - Processed: {}, Renamed: {}, Errors: {}, Skipped: {}, "
        "Already Extended: {}, TV Shows: {}, Movies: {}, "
        "Genre from tvshow.nfo: {}, Show title from tvshow.nfo: {}, "
        "Holiday episodes/movies - Christmas: {}, Thanksgiving: {}, "
        "Halloween: {}".format(
            directory,
            stats["processed"],
            stats["renamed"],
            stats["errors"],
            stats["skipped"],
            stats["already_extended"],
            stats["tv_shows"],
            stats["movies"],
            stats["genre_from_tvshow"],
            stats["showtitle_from_tvshow"],
            stats["christmas_episodes"],
            stats["thanksgiving_episodes"],
            stats["halloween_episodes"],
        )
    )

    return stats


def run_renamer(directory, dry_run=False, recursive=False, progress_callback=None):
    """Run the renamer with specified parameters"""
    print("NFO Renamer Movies")
    print("Processing directory: {}".format(directory))
    print("Recursive mode: {}".format("Yes" if recursive else "No"))
    print("Dry run mode: {}".format("Yes" if dry_run else "No"))
    print("")

    if dry_run:
        print("*** DRY RUN MODE - NO FILES WILL BE MODIFIED ***")

    try:
        stats = rename_files(directory, dry_run, recursive, progress_callback)
        if stats:
            print("\nOperation completed successfully.")
            print("Files processed: {}".format(stats["processed"]))
            print("Files renamed: {}".format(stats["renamed"]))
            print("Files skipped: {}".format(stats["skipped"]))
            print(
                "Files already in extended format: {}".format(stats["already_extended"])
            )
            print("Errors encountered: {}".format(stats["errors"]))
            print("TV Shows processed: {}".format(stats["tv_shows"]))
            print("Movies processed: {}".format(stats["movies"]))
            print("Genre from tvshow.nfo: {}".format(stats["genre_from_tvshow"]))
            print(
                "Show title from tvshow.nfo: {}".format(stats["showtitle_from_tvshow"])
            )
            print("\nHoliday content found:")
            print("  Christmas: {}".format(stats["christmas_episodes"]))
            print("  Thanksgiving: {}".format(stats["thanksgiving_episodes"]))
            print("  Halloween: {}".format(stats["halloween_episodes"]))
            return 0
    except Exception as e:
        logger.error("An error occurred: {}".format(e))
        print("\nOperation failed with error: {}".format(e))
        return 1


def main():
    """Main function to parse arguments and initiate renaming"""
    # Check if running in Kodi
    if IN_KODI:
        # Running from Kodi settings - use configured directory from settings
        dialog = xbmcgui.Dialog()
        addon = xbmcaddon.Addon(id="script.paragontv")

        # Get the configured Movies directory from settings
        directory = addon.getSetting("NFOMoviesPath")

        # Translate Kodi special:// paths and handle Unicode properly
        if directory:
            directory = xbmc.translatePath(directory)

        if not directory:
            dialog.ok(
                "NFO Renamer - Movies",
                "Movies Directory is not configured.",
                "Please configure the 'Movies Directory' setting",
                "in Paragon TV Settings > Preset Refresh Configuration."
            )
            return 1

        # Always process recursively (standard behavior)
        recursive = True

        # Always run in live mode (no dry-run)
        dry_run = False

        # Show progress dialog
        progress = xbmcgui.DialogProgress()
        progress.create("NFO Renamer - Movies", "Scanning files...")

        # Create progress callback that updates the dialog
        def progress_callback(percent, message):
            progress.update(percent, message)

        try:
            result = run_renamer(directory, dry_run, recursive, progress_callback)
            progress.update(100, "Complete!")
            xbmc.sleep(500)  # Brief pause to show completion
            progress.close()

            if result == 0:
                dialog.ok(
                    "NFO Renamer Complete",
                    "Movie files have been processed successfully!",
                    "Check the Kodi log for details."
                )
            else:
                dialog.ok(
                    "NFO Renamer Error",
                    "An error occurred while processing files.",
                    "Check the Kodi log for details."
                )
            return result
        except Exception as e:
            progress.close()
            dialog.ok("Error", "Failed to process files:", str(e))
            return 1
    else:
        # Running from command line - use argparse
        parser = argparse.ArgumentParser(
            description="Rename video files to extended format based on NFO metadata"
        )

        parser.add_argument(
            "directory", help="Directory containing NFO and video files to process"
        )

        parser.add_argument(
            "--recursive",
            "-r",
            action="store_true",
            help="Process subdirectories recursively",
        )

        parser.add_argument(
            "--dry-run",
            "-d",
            action="store_true",
            help="Show what would be renamed without making changes",
        )

        args = parser.parse_args()
        return run_renamer(args.directory, args.dry_run, args.recursive)


if __name__ == "__main__":
    sys.exit(main())
