#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Repair Corrupted NFO Files - Fixes XML corruption and extracts genre from filenames
Supports both Kodi VFS (NFS/SMB) and standard filesystem paths
Filename format: SSxEE - Episode Title - Show Title - Genre - Resolution - Audio Channels - Audio Codec - Holiday
"""

import sys
import os
import re

# Detect if running in Kodi
try:
    import xbmc
    import xbmcaddon
    import xbmcgui
    import xbmcvfs
    KODI_MODE = True
    try:
        ADDON = xbmcaddon.Addon('script.paragontv')
        ADDON_ID = 'script.paragontv'
    except Exception as e:
        ADDON = None
        ADDON_ID = "repair_corrupted_nfo"
except ImportError:
    KODI_MODE = False
    ADDON = None
    ADDON_ID = "repair_corrupted_nfo"

# XML parsing
try:
    import xml.etree.ElementTree as ET
except ImportError:
    import elementtree.ElementTree as ET

def log(msg):
    """Log message to Kodi log or console."""
    if KODI_MODE:
        xbmc.log("[Repair NFO] {}".format(msg), xbmc.LOGNOTICE)
    else:
        print("[Repair NFO] {}".format(msg))

# List of 49 corrupted shows
CORRUPTED_SHOWS = [
    "What I Like About You",
    "Warehouse 13",
    "The Twilight Zone",
    "The OA",
    "The Lost Pirate Kingdom",
    "The Librarians - The Next Chapter",
    "The Librarians (2014)",
    "The City & The City",
    "Step by Step",
    "Sense8",
    "Philip K. Dick's Electric Dreams",
    "Maniac (2018)",
    "Girl Meets World",
    "FlashForward",
    "Dinosaurs",
    "Counterpart",
    "Lost",
    "Victorious",
    "The Terror",
    "The Continental (2023)",
    "Tales from the Loop",
    "Alcatraz",
    "The Twilight Zone (2019)",
    "Tosh.0",
    "Devs",
    "Fuller House",
    "Dispatches from Elsewhere",
    "Burn Notice",
    "Dark",
    "Person of Interest",
    "24",
    "Black Sails",
    "From",
    "Black Mirror",
    "Big Time Rush",
    "Alice in Borderland (2020)",
    "Alias",
    "1899",
    "The Institute",
    "Squid Game",
    "Shogun",
    "Robin Hood (2006)",
    "Outer Range",
    "Kaleidoscope (2023)",
    "Haven",
    "Designated Survivor",
    "Severance",
    "Reacher",
    "Fringe"
]

def fix_corrupted_xml(content):
    """Fix corrupted XML by finding the first valid </tvshow> after the FIRST </generator> and cutting there."""
    try:
        log("Original content length: {} bytes".format(len(content)))
        
        # Find ALL occurrences of </generator>
        generator_positions = []
        search_pos = 0
        while True:
            pos = content.find('</generator>', search_pos)
            if pos == -1:
                break
            generator_positions.append(pos)
            search_pos = pos + 1
        
        log("Found {} </generator> tags".format(len(generator_positions)))
        
        # Find ALL occurrences of </tvshow>
        tvshow_positions = []
        search_pos = 0
        while True:
            pos = content.find('</tvshow>', search_pos)
            if pos == -1:
                break
            tvshow_positions.append(pos)
            search_pos = pos + 1
        
        log("Found {} </tvshow> tags".format(len(tvshow_positions)))
        
        if not generator_positions or not tvshow_positions:
            log("Missing expected tags")
            return content
        
        # CORRECT STRATEGY: Find the FIRST </tvshow> that comes AFTER the FIRST </generator>
        # This is the correct closing tag before the corruption
        
        first_generator_pos = generator_positions[0]
        first_generator_end = first_generator_pos + len('</generator>')
        
        log("First </generator> ends at position {}".format(first_generator_end))
        
        # Find the first </tvshow> that comes after the first </generator>
        first_valid_tvshow = None
        for tvshow_pos in tvshow_positions:
            if tvshow_pos >= first_generator_end:
                first_valid_tvshow = tvshow_pos
                break
        
        if first_valid_tvshow is None:
            log("ERROR: No </tvshow> found after first </generator>!")
            return content
        
        # Cut right after this </tvshow>
        cut_position = first_valid_tvshow + len('</tvshow>')
        
        log("First valid </tvshow> is at position {}, cutting at {}".format(first_valid_tvshow, cut_position))
        
        # Get clean content
        fixed_content = content[:cut_position]
        
        # Show what we're removing
        removed_content = content[cut_position:]
        if removed_content.strip():
            log("REMOVING {} bytes of junk".format(len(removed_content)))
            log("Junk preview: {}".format(removed_content[:200]))
        else:
            log("No junk to remove - file already clean")
        
        # Verify the fixed content is valid XML
        try:
            root = ET.fromstring(fixed_content)
            log("XML validation: SUCCESS - file is now valid")
            return fixed_content
        except Exception as parse_error:
            log("XML validation: FAILED - {}".format(str(parse_error)))
            log("Last 300 chars: {}".format(fixed_content[-300:]))
            return fixed_content
            
    except Exception as e:
        log("CRITICAL ERROR in fix_corrupted_xml: {}".format(str(e)))
        import traceback
        log("Traceback: {}".format(traceback.format_exc()))
        return content

def read_nfo_file(filepath):
    """Read NFO file content using VFS-compatible methods."""
    try:
        if KODI_MODE and (filepath.startswith('nfs://') or filepath.startswith('smb://') or filepath.startswith('upnp://')):
            nfo_file = xbmcvfs.File(filepath, 'r')
            content = nfo_file.read()
            nfo_file.close()
        else:
            with open(filepath, 'r') as f:
                content = f.read()
        return content
    except Exception as e:
        log("Error reading {}: {}".format(filepath, str(e)))
        return None

def write_nfo_file(filepath, content):
    """Write NFO file content using VFS-compatible methods."""
    try:
        if KODI_MODE and (filepath.startswith('nfs://') or filepath.startswith('smb://') or filepath.startswith('upnp://')):
            nfo_file = xbmcvfs.File(filepath, 'w')
            nfo_file.write(content)
            nfo_file.close()
        else:
            with open(filepath, 'w') as f:
                f.write(content)
        return True
    except Exception as e:
        log("Error writing {}: {}".format(filepath, str(e)))
        return False

def list_directory_files(folder_path):
    """List files in directory using VFS-compatible methods."""
    try:
        if KODI_MODE:
            dirs, files = xbmcvfs.listdir(folder_path)
            log("Listed directory - Dirs: {}, Files: {}".format(len(dirs), len(files)))
            return dirs, files
        else:
            dirs = [d for d in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, d))]
            files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
            return dirs, files
    except Exception as e:
        log("Error listing directory {}: {}".format(folder_path, str(e)))
        return [], []

def extract_genre_from_filename(filename):
    """
    Extract genre from extended filename format.
    Format: SSxEE - Episode Title - Show Title - Genre - Resolution - Audio Channels - Audio Codec - Holiday
    Example: 01x01 - Good News About Hell - Severance - Mystery - 1080 - 6 - EAC3 ATMOS - None
    """
    log("Parsing filename: {}".format(filename))
    # Split by ' - ' to get segments
    parts = filename.split(' - ')
    log("Split into {} parts".format(len(parts)))
    
    # Genre is in position 3 (0-indexed)
    if len(parts) >= 4:
        genre = parts[3].strip()
        log("Extracted genre: {}".format(genre))
        return genre
    
    log("Not enough parts to extract genre")
    return None

def find_genre_from_folder(folder_path):
    """Find genre by scanning video files in the folder and season subfolders."""
    log("Scanning folder for video files: {}".format(folder_path))
    
    dirs, files = list_directory_files(folder_path)
    
    # Look for video files in main folder
    video_extensions = ['.mkv', '.mp4', '.avi', '.m4v']
    
    log("Found {} files in main folder".format(len(files)))
    for filename in files:
        # Check if it's a video file
        if any(filename.lower().endswith(ext) for ext in video_extensions):
            log("Found video file: {}".format(filename))
            genre = extract_genre_from_filename(filename)
            if genre:
                return genre
    
    # If no video files in main folder, check Season folders
    log("No video files in main folder, checking {} subdirectories".format(len(dirs)))
    for dirname in dirs:
        # Check if it's a season folder
        if dirname.lower().startswith('season'):
            log("Checking season folder: {}".format(dirname))
            
            # Build season folder path
            if folder_path.endswith('/'):
                season_path = folder_path + dirname
            else:
                season_path = folder_path + '/' + dirname
            
            # List files in season folder
            season_dirs, season_files = list_directory_files(season_path)
            log("Found {} files in season folder".format(len(season_files)))
            
            for filename in season_files:
                if any(filename.lower().endswith(ext) for ext in video_extensions):
                    log("Found video file in season: {}".format(filename))
                    genre = extract_genre_from_filename(filename)
                    if genre:
                        return genre
    
    log("No genre found in folder or season subfolders")
    return None

def extract_current_genre(content):
    """Extract current genre from XML content."""
    match = re.search(r'<genre>(.*?)</genre>', content)
    if match:
        return match.group(1)
    return "Unknown"

def update_genre_in_content(content, new_genre):
    """Update genre in XML content string."""
    import re
    # Use regex to replace the genre tag
    content = re.sub(r'<genre>.*?</genre>', '<genre>{}</genre>'.format(new_genre), content)
    return content

def show_progress_dialog():
    """Create progress dialog if in Kodi mode."""
    if KODI_MODE:
        dialog = xbmcgui.DialogProgress()
        dialog.create("Repairing NFO Files", "Initializing...")
        return dialog
    return None

def update_progress_dialog(dialog, percent, line1, line2="", line3=""):
    """Update progress dialog."""
    if dialog and KODI_MODE:
        dialog.update(percent, line1, line2, line3)

def repair_corrupted_shows(base_path):
    """Main repair function."""
    log("=" * 60)
    log("Starting NFO Repair Process")
    log("Base path: {}".format(base_path))
    log("Shows to repair: {}".format(len(CORRUPTED_SHOWS)))
    log("=" * 60)
    
    if KODI_MODE:
        # Show initial dialog
        result = xbmcgui.Dialog().yesno(
            "Repair Corrupted NFO Files",
            "Found {} shows with corrupted NFO files.[CR][CR]"
            "This script will:[CR]"
            "1. Fix corrupted XML[CR]"
            "2. Extract genre from video filenames[CR]"
            "3. Update NFO files automatically[CR][CR]"
            "Continue?".format(len(CORRUPTED_SHOWS))
        )
        if not result:
            log("User cancelled repair")
            return
    
    # Create progress dialog
    progress = show_progress_dialog()
    
    repaired = []
    no_genre_found = []
    errors = []
    
    total = len(CORRUPTED_SHOWS)
    current = 0
    
    for show_name in CORRUPTED_SHOWS:
        current += 1
        percent = int((float(current) / total) * 100)
        
        log("Processing {}/{}: {}".format(current, total, show_name))
        
        if progress:
            update_progress_dialog(
                progress, 
                percent, 
                "Processing show {}/{}".format(current, total),
                show_name,
                ""
            )
        
        # Build paths
        if base_path.endswith('/'):
            folder_path = base_path + show_name
            nfo_path = folder_path + '/tvshow.nfo'
        else:
            folder_path = base_path + '/' + show_name
            nfo_path = folder_path + '/tvshow.nfo'
        
        # Check if NFO exists
        if KODI_MODE:
            if not xbmcvfs.exists(nfo_path):
                log("NFO not found: {}".format(nfo_path))
                errors.append(show_name + " (NFO not found)")
                continue
        else:
            if not os.path.exists(nfo_path):
                log("NFO not found: {}".format(nfo_path))
                errors.append(show_name + " (NFO not found)")
                continue
        
        # Read NFO file
        content = read_nfo_file(nfo_path)
        if content is None:
            errors.append(show_name + " (read error)")
            continue
        
        # Fix XML corruption
        fixed_content = fix_corrupted_xml(content)
        current_genre = extract_current_genre(fixed_content)
        
        # Find genre from video files
        genre = find_genre_from_folder(folder_path)
        
        if genre is None:
            log("Could not find genre in filenames for: {}".format(show_name))
            no_genre_found.append(show_name)
            # Still fix the XML corruption even if no genre found
            if write_nfo_file(nfo_path, fixed_content):
                log("Fixed XML corruption (no genre update): {}".format(show_name))
            continue
        
        # Update genre in content
        fixed_content = update_genre_in_content(fixed_content, genre)
        
        # Write back
        if write_nfo_file(nfo_path, fixed_content):
            log("Repaired: {} -> {} (was: {})".format(show_name, genre, current_genre))
            repaired.append({
                'show': show_name,
                'old_genre': current_genre,
                'new_genre': genre
            })
        else:
            errors.append(show_name + " (write error)")
    
    # Close progress dialog
    if progress:
        progress.close()
    
    # Generate report
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("NFO REPAIR REPORT")
    report_lines.append("=" * 80)
    report_lines.append("")
    report_lines.append("Total shows processed: {}".format(len(CORRUPTED_SHOWS)))
    report_lines.append("Successfully repaired: {}".format(len(repaired)))
    report_lines.append("No genre found: {}".format(len(no_genre_found)))
    report_lines.append("Errors: {}".format(len(errors)))
    report_lines.append("")
    
    if repaired:
        report_lines.append("=" * 80)
        report_lines.append("REPAIRED SHOWS:")
        report_lines.append("=" * 80)
        for item in repaired:
            report_lines.append("{}: {} -> {}".format(
                item['show'], item['old_genre'], item['new_genre']))
        report_lines.append("")
    
    if no_genre_found:
        report_lines.append("=" * 80)
        report_lines.append("NO GENRE FOUND (XML still fixed):")
        report_lines.append("=" * 80)
        for show in no_genre_found:
            report_lines.append(show)
        report_lines.append("")
    
    if errors:
        report_lines.append("=" * 80)
        report_lines.append("ERRORS:")
        report_lines.append("=" * 80)
        for error in errors:
            report_lines.append(error)
        report_lines.append("")
    
    report_content = "\n".join(report_lines)
    
    # Write report
    if KODI_MODE:
        report_path = xbmc.translatePath('special://temp/nfo_repair_report.txt')
    else:
        report_path = os.path.join(os.path.expanduser('~'), 'nfo_repair_report.txt')
    
    try:
        if KODI_MODE:
            report_file = xbmcvfs.File(report_path, 'w')
            if sys.version_info[0] == 2:
                if isinstance(report_content, unicode):
                    report_file.write(report_content.encode('utf-8'))
                else:
                    report_file.write(report_content)
            else:
                report_file.write(report_content.encode('utf-8') if isinstance(report_content, str) else report_content)
            report_file.close()
        else:
            with open(report_path, 'w') as f:
                f.write(report_content)
        log("Report saved to: {}".format(report_path))
    except Exception as e:
        log("Error writing report: {}".format(str(e)))
    
    # Show summary
    summary_lines = [
        "Repair Complete!",
        "",
        "Repaired: {}".format(len(repaired)),
        "No genre found: {}".format(len(no_genre_found)),
        "Errors: {}".format(len(errors)),
        "",
        "Report saved to:",
        report_path
    ]
    
    if KODI_MODE:
        xbmcgui.Dialog().ok("Repair Complete", "[CR]".join(summary_lines))
    else:
        print("\n" + "=" * 60)
        print("\n".join(summary_lines))
        print("=" * 60)
    
    log("=" * 60)
    log("Repair complete!")
    log("Repaired: {}".format(len(repaired)))
    log("Report: {}".format(report_path))
    log("=" * 60)

if __name__ == "__main__":
    # Get base path from command line or use default
    if len(sys.argv) > 1:
        base_path = sys.argv[1]
    else:
        # Default path
        if KODI_MODE:
            base_path = "nfs://10.0.0.39/mnt/user/TELEVISION/"
        else:
            base_path = "/path/to/tv/shows/"
    
    repair_corrupted_shows(base_path)