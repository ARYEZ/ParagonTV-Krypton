#!/usr/bin/env python3
"""
Audio File Metadata Renamer

This script reads audio file metadata and renames files to an extended format:
Artist - Title - Album - Genre - Year - Audio Codec - Bitrate.ext

It preserves the original file content but renames based on metadata tags.
Supports MP3, FLAC, M4A, OGG, WAV, and WMA files.

Features:
- Extracts metadata from audio files using mutagen
- Sanitizes filenames for Windows compatibility
- Skips files already in the correct format
- Optional cover art extraction
- Dry-run mode for preview
"""

import argparse
import logging
import os
import re
import shutil
import sys

# Audio processing requires mutagen
try:
    import mutagen
    from mutagen.easyid3 import EasyID3
    from mutagen.id3 import APIC, ID3
    from mutagen.mp3 import MP3

    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False
    print("ERROR: This script requires the mutagen library.")
    print("Please install it with: pip install mutagen")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("audio_renamer.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Audio file extensions to process
AUDIO_EXTENSIONS = [".mp3", ".flac", ".m4a", ".ogg", ".wav", ".wma"]

# Common audio codec mappings
AUDIO_CODEC_MAP = {
    "mp3": "MP3",
    "flac": "FLAC",
    "aac": "AAC",
    "m4a": "AAC",
    "ogg": "Vorbis",
    "wav": "PCM",
    "wma": "WMA",
    "opus": "OPUS",
    "alac": "ALAC",
}

# Invalid characters for Windows filenames
INVALID_FILENAME_CHARS = ["<", ">", ":", '"', "/", "\\", "|", "?", "*"]

# Pattern to detect if a file is already in the extended audio format
# Format: Artist - Title - Album - Genre - Year - Audio Codec - Bitrate.ext
EXTENDED_AUDIO_FORMAT_PATTERN = re.compile(
    r"^.+ - .+ - .+ - .+ - \d{4} - [A-Za-z0-9-]+ - \d+$"
)


def sanitize_filename(filename):
    """
    Remove or replace characters that are invalid in Windows filenames
    """
    # Replace colons with periods
    sanitized = filename.replace(":", ".")

    # Replace other invalid characters with underscores
    for char in INVALID_FILENAME_CHARS:
        sanitized = sanitized.replace(char, "_")

    # Replace multiple periods with a single period
    sanitized = re.sub(r"\.+", ".", sanitized)

    # Remove leading/trailing spaces and periods
    sanitized = sanitized.strip(". ")

    if sanitized != filename:
        logger.debug(f"Sanitized: '{filename}' -> '{sanitized}'")

    return sanitized


def is_already_extended_format(filename):
    """
    Check if the filename is already in the extended audio format
    """
    # Strip extension
    base_name = os.path.splitext(filename)[0]

    # Quick pattern match first
    if EXTENDED_AUDIO_FORMAT_PATTERN.match(base_name):
        return True

    # Detailed analysis
    parts = base_name.split(" - ")

    # Need exactly 7 parts
    if len(parts) != 7:
        return False

    # Check year (5th part) - should be 4 digits
    if not re.match(r"^\d{4}$", parts[4]):
        return False

    # Check bitrate (7th part) - should be numeric
    if not parts[6].isdigit():
        return False

    return True


def parse_audio_file(audio_path):
    """
    Parse audio file to extract metadata using mutagen
    Returns a dictionary with artist, title, album, genre, etc.
    """
    try:
        # Initialize metadata with defaults
        metadata = {
            "artist": "Unknown Artist",
            "title": "Unknown Title",
            "album": "Unknown Album",
            "genre": "Unknown Genre",
            "year": "0000",
            "audio_codec": "Unknown",
            "bitrate": "0",  # in kbps
        }

        # Load the audio file
        audio = mutagen.File(audio_path)

        if audio is None:
            logger.error(f"Could not parse audio file: {audio_path}")
            return None

        # Determine audio codec from file type
        file_ext = os.path.splitext(audio_path)[1].lower()[1:]  # Remove the dot
        if isinstance(audio, MP3):
            metadata["audio_codec"] = "MP3"
        else:
            metadata["audio_codec"] = AUDIO_CODEC_MAP.get(file_ext, file_ext.upper())

        # Get bitrate (convert to kbps)
        if hasattr(audio.info, "bitrate") and audio.info.bitrate:
            metadata["bitrate"] = str(audio.info.bitrate // 1000)

        # Try EasyID3 for common tags (works for MP3)
        try:
            if file_ext == "mp3":
                tags = EasyID3(audio_path)
            else:
                tags = audio

            # Extract common tags
            if "artist" in tags and tags["artist"]:
                metadata["artist"] = (
                    str(tags["artist"][0])
                    if isinstance(tags["artist"], list)
                    else str(tags["artist"])
                )

            if "title" in tags and tags["title"]:
                metadata["title"] = (
                    str(tags["title"][0])
                    if isinstance(tags["title"], list)
                    else str(tags["title"])
                )

            if "album" in tags and tags["album"]:
                metadata["album"] = (
                    str(tags["album"][0])
                    if isinstance(tags["album"], list)
                    else str(tags["album"])
                )

            if "genre" in tags and tags["genre"]:
                metadata["genre"] = (
                    str(tags["genre"][0])
                    if isinstance(tags["genre"], list)
                    else str(tags["genre"])
                )

            # Get year from date tag
            if "date" in tags and tags["date"]:
                date_str = (
                    str(tags["date"][0])
                    if isinstance(tags["date"], list)
                    else str(tags["date"])
                )
                year_match = re.search(r"\d{4}", date_str)
                if year_match:
                    metadata["year"] = year_match.group(0)

        except Exception as e:
            logger.warning(f"Could not extract tags using EasyID3: {e}")

            # Fallback: try to extract tags directly
            if hasattr(audio, "tags") and audio.tags:
                for tag_name, tag_value in audio.tags.items():
                    tag_lower = str(tag_name).lower()

                    if "artist" in tag_lower and not metadata["artist"].startswith(
                        "Unknown"
                    ):
                        metadata["artist"] = str(
                            tag_value[0] if isinstance(tag_value, list) else tag_value
                        )
                    elif "title" in tag_lower and not metadata["title"].startswith(
                        "Unknown"
                    ):
                        metadata["title"] = str(
                            tag_value[0] if isinstance(tag_value, list) else tag_value
                        )
                    elif "album" in tag_lower and not metadata["album"].startswith(
                        "Unknown"
                    ):
                        metadata["album"] = str(
                            tag_value[0] if isinstance(tag_value, list) else tag_value
                        )
                    elif "genre" in tag_lower and not metadata["genre"].startswith(
                        "Unknown"
                    ):
                        metadata["genre"] = str(
                            tag_value[0] if isinstance(tag_value, list) else tag_value
                        )
                    elif "date" in tag_lower or "year" in tag_lower:
                        date_str = str(
                            tag_value[0] if isinstance(tag_value, list) else tag_value
                        )
                        year_match = re.search(r"\d{4}", date_str)
                        if year_match:
                            metadata["year"] = year_match.group(0)

        # Sanitize all metadata values
        for key in metadata:
            if isinstance(metadata[key], str):
                metadata[key] = sanitize_filename(metadata[key])

        return metadata

    except Exception as e:
        logger.error(f"Error processing audio file {audio_path}: {e}")
        return None


def extract_cover_art(audio_path, output_dir):
    """
    Extract cover art from audio file and save as album.jpg
    """
    try:
        audio = mutagen.File(audio_path)

        if audio is None:
            return None

        # For MP3 files, look for APIC frames
        if isinstance(audio, MP3):
            for tag in audio.tags.values():
                if isinstance(tag, APIC):
                    output_path = os.path.join(output_dir, "album.jpg")
                    with open(output_path, "wb") as img_file:
                        img_file.write(tag.data)
                    logger.info(f"Extracted cover art to {output_path}")
                    return output_path

        # For other formats, look for picture tags
        elif hasattr(audio, "pictures") and audio.pictures:
            output_path = os.path.join(output_dir, "album.jpg")
            with open(output_path, "wb") as img_file:
                img_file.write(audio.pictures[0].data)
            logger.info(f"Extracted cover art to {output_path}")
            return output_path

        # FLAC-specific
        elif hasattr(audio, "pics") and audio.pics:
            output_path = os.path.join(output_dir, "album.jpg")
            with open(output_path, "wb") as img_file:
                img_file.write(audio.pics[0].data)
            logger.info(f"Extracted cover art to {output_path}")
            return output_path

        return None

    except Exception as e:
        logger.error(f"Error extracting cover art from {audio_path}: {e}")
        return None


def create_extended_filename(metadata, original_ext):
    """
    Create new filename based on metadata
    Format: Artist - Title - Album - Genre - Year - Audio Codec - Bitrate.ext
    """
    artist = metadata.get("artist", "Unknown Artist")
    title = metadata.get("title", "Unknown Title")
    album = metadata.get("album", "Unknown Album")
    genre = metadata.get("genre", "Unknown Genre")
    year = metadata.get("year", "0000")
    audio_codec = metadata.get("audio_codec", "Unknown")
    bitrate = metadata.get("bitrate", "0")

    # Format the new filename
    filename = f"{artist} - {title} - {album} - {genre} - {year} - {audio_codec} - {bitrate}{original_ext}"

    # Final sanitization
    return sanitize_filename(filename)


def rename_audio_files(directory, dry_run=False, recursive=False, extract_covers=False):
    """
    Process directory and rename audio files according to extended format
    """
    if not os.path.isdir(directory):
        logger.error(f"Directory not found: {directory}")
        return None

    # Statistics
    stats = {
        "processed": 0,
        "renamed": 0,
        "errors": 0,
        "skipped": 0,
        "already_extended": 0,
        "covers_extracted": 0,
    }

    # Get list of files to process
    if recursive:
        files_to_process = []
        for root, dirs, files in os.walk(directory):
            for filename in files:
                if os.path.splitext(filename)[1].lower() in AUDIO_EXTENSIONS:
                    files_to_process.append(os.path.join(root, filename))
    else:
        files_to_process = [
            os.path.join(directory, f)
            for f in os.listdir(directory)
            if os.path.isfile(os.path.join(directory, f))
            and os.path.splitext(f)[1].lower() in AUDIO_EXTENSIONS
        ]

    # Process each audio file
    for file_path in files_to_process:
        stats["processed"] += 1
        filename = os.path.basename(file_path)
        file_dir = os.path.dirname(file_path)

        logger.info(f"Processing: {filename}")

        # Check if already in extended format
        if is_already_extended_format(filename):
            logger.info(f"Already in extended format: {filename}")
            stats["already_extended"] += 1
            stats["skipped"] += 1
            continue

        # Parse audio metadata
        metadata = parse_audio_file(file_path)
        if not metadata:
            logger.error(f"Failed to parse: {filename}")
            stats["errors"] += 1
            continue

        # Extract cover art if requested
        if extract_covers and not os.path.exists(os.path.join(file_dir, "album.jpg")):
            if extract_cover_art(file_path, file_dir):
                stats["covers_extracted"] += 1

        # Create new filename
        file_ext = os.path.splitext(filename)[1]
        new_filename = create_extended_filename(metadata, file_ext)

        # Check if rename is needed
        if new_filename == filename:
            logger.info(f"Already has correct naming: {filename}")
            stats["skipped"] += 1
            continue

        # Log the rename operation
        logger.info(f"Renaming:\n  From: {filename}\n  To:   {new_filename}")

        if not dry_run:
            try:
                src_path = file_path
                dst_path = os.path.join(file_dir, new_filename)

                # Check if destination already exists
                if os.path.exists(dst_path):
                    logger.error(f"Destination already exists: {new_filename}")
                    stats["errors"] += 1
                    continue

                # Rename the file
                shutil.move(src_path, dst_path)
                stats["renamed"] += 1

            except Exception as e:
                logger.error(f"Error renaming file: {e}")
                stats["errors"] += 1
        else:
            stats["renamed"] += 1  # Count as renamed in dry-run

    # Log summary
    logger.info(f"\nSummary for {directory}:")
    logger.info(f"  Processed: {stats['processed']}")
    logger.info(f"  Renamed: {stats['renamed']}")
    logger.info(f"  Skipped: {stats['skipped']}")
    logger.info(f"  Already Extended: {stats['already_extended']}")
    logger.info(f"  Errors: {stats['errors']}")
    logger.info(f"  Covers Extracted: {stats['covers_extracted']}")

    return stats


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Rename audio files to extended format based on metadata"
    )

    parser.add_argument("directory", help="Directory containing audio files to process")

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

    parser.add_argument(
        "--extract-covers",
        "-c",
        action="store_true",
        help="Extract cover art as album.jpg",
    )

    args = parser.parse_args()

    print("Audio File Metadata Renamer")
    print(f"Processing directory: {args.directory}")
    print(f"Recursive: {'Yes' if args.recursive else 'No'}")
    print(f"Dry run: {'Yes' if args.dry_run else 'No'}")
    print(f"Extract covers: {'Yes' if args.extract_covers else 'No'}")
    print("")

    if args.dry_run:
        print("*** DRY RUN MODE - NO FILES WILL BE MODIFIED ***")
        print("")

    try:
        stats = rename_audio_files(
            args.directory,
            dry_run=args.dry_run,
            recursive=args.recursive,
            extract_covers=args.extract_covers,
        )

        if stats:
            print("\nOperation completed successfully!")
            print(f"Files processed: {stats['processed']}")
            print(f"Files renamed: {stats['renamed']}")
            print(f"Files skipped: {stats['skipped']}")
            print(f"Already in format: {stats['already_extended']}")
            print(f"Errors: {stats['errors']}")
            if args.extract_covers:
                print(f"Cover art extracted: {stats['covers_extracted']}")

            return 0 if stats["errors"] == 0 else 1
        else:
            return 1

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"\nOperation failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
