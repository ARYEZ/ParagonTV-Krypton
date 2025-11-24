#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Check Movie Genre Consistency - Compares NFO genre to filename genre
Reports mismatches where NFO doesn't match the filename (filename = source of truth)
Supports both Kodi VFS (NFS/SMB) and standard filesystem paths
"""

import sys
import os
import re
from collections import defaultdict

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
        ADDON_PATH = ADDON.getAddonInfo('path')
        ICON = os.path.join(ADDON_PATH, 'icon.png')
    except Exception as e:
        ADDON = None
        ADDON_ID = "check_movie_genre_consistency"
        ICON = ""
except ImportError:
    KODI_MODE = False
    ADDON = None
    ADDON_ID = "check_movie_genre_consistency"
    ICON = ""

# XML parsing
try:
    import xml.etree.ElementTree as ET
except ImportError:
    import elementtree.ElementTree as ET

def log(msg):
    """Log message to Kodi log or console."""
    if KODI_MODE:
        xbmc.log("[Movie Genre Consistency] {}".format(msg), xbmc.LOGNOTICE)
    else:
        print("[Movie Genre Consistency] {}".format(msg))

def notify(title, message, time=5000):
    """Show notification with Paragon TV icon."""
    if KODI_MODE:
        xbmcgui.Dialog().notification(title, message, ICON, time)
    else:
        print("[NOTIFY] {}: {}".format(title, message))

def scan_movie_folders(base_path, progress_dialog=None):
    """Scan movie folders and find .nfo files."""
    log("Starting scan of: {}".format(base_path))
    
    if progress_dialog:
        progress_dialog.update(0, "Scanning movie library...", "Finding movie folders...", "")
    
    folders_scanned = 0
    nfo_files_found = []
    
    try:
        # Use xbmcvfs to list directories
        if KODI_MODE:
            dirs, files = xbmcvfs.listdir(base_path)
        else:
            dirs = [d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))]
        
        log("Found {} folders in base path".format(len(dirs)))
        total_dirs = len(dirs)
        
        # Scan each movie folder
        for idx, folder_name in enumerate(dirs):
            if progress_dialog:
                percent = int((float(idx) / total_dirs) * 100)
                progress_dialog.update(percent, "Scanning movie library...", "Checking: {}".format(folder_name), "")
                
                if progress_dialog.iscanceled():
                    log("Scan cancelled by user")
                    return None
            
            folders_scanned += 1
            
            # Build full folder path
            if base_path.endswith('/'):
                folder_path = base_path + folder_name
            else:
                folder_path = base_path + '/' + folder_name
            
            # Look for any .nfo file in this folder
            try:
                if KODI_MODE:
                    folder_dirs, folder_files = xbmcvfs.listdir(folder_path)
                else:
                    folder_files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
                
                # Find .nfo files
                nfo_filename = None
                for filename in folder_files:
                    if filename.lower().endswith('.nfo'):
                        nfo_filename = filename
                        break
                
                if nfo_filename:
                    nfo_path = folder_path + '/' + nfo_filename
                    nfo_files_found.append({
                        'path': nfo_path,
                        'folder': folder_name,
                        'folder_path': folder_path,
                        'nfo_filename': nfo_filename
                    })
                        
            except Exception as e:
                log("Error checking folder {}: {}".format(folder_name, str(e)))
                continue
        
        log("Scan complete: {} folders scanned, {} .nfo files found".format(
            folders_scanned, len(nfo_files_found)))
        
        return nfo_files_found
        
    except Exception as e:
        log("Error reading folder {}: {}".format(base_path, str(e)))
        return []

def parse_nfo_genre(filepath):
    """Parse the NFO file and extract the genre."""
    try:
        # Read file using VFS for network paths
        if KODI_MODE and (filepath.startswith('nfs://') or filepath.startswith('smb://') or filepath.startswith('upnp://')):
            nfo_file = xbmcvfs.File(filepath, 'r')
            content = nfo_file.read()
            nfo_file.close()
            root = ET.fromstring(content)
        else:
            tree = ET.parse(filepath)
            root = tree.getroot()
        
        genre_elem = root.find('genre')
        genre = genre_elem.text if genre_elem is not None else None
        
        return genre
    except Exception as e:
        log("Error parsing {}: {}".format(filepath, str(e)))
        return None

def extract_genre_from_filename(filename):
    """
    Extract genre from movie filename format.
    Format: Movie Title - Rating - Genre - Resolution - Audio Channels - Audio Codec - Holiday
    Example: The Matrix - R - Science Fiction - 1080 - 8 - ATMOS - None
    Genre is in position 2 (0-indexed)
    """
    # Remove .nfo extension
    if filename.lower().endswith('.nfo'):
        filename = filename[:-4]
    
    parts = filename.split(' - ')
    
    if len(parts) >= 3:
        genre = parts[2].strip()
        return genre
    
    return None

def write_report(report_path, report_content):
    """Write report to file with proper UTF-8 encoding."""
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
            log("Report written to: {}".format(report_path))
        else:
            with open(report_path, 'w') as f:
                f.write(report_content)
            log("Report written to: {}".format(report_path))
        return True
    except Exception as e:
        log("Error writing report: {}".format(str(e)))
        return False

def check_movie_genre_consistency(base_path):
    """Main function to check movie genre consistency between NFO and filename."""
    log("=" * 60)
    log("Starting Movie Genre Consistency Check")
    log("Base path: {}".format(base_path))
    log("=" * 60)
    
    notify("Check Movie Genres", "Starting scan...")
    
    # Create progress dialog
    if KODI_MODE:
        progress = xbmcgui.DialogProgress()
        progress.create("Check Movie Genre Consistency", "Initializing...")
    else:
        progress = None
    
    # Scan for NFO files
    nfo_files = scan_movie_folders(base_path, progress)
    
    if nfo_files is None:
        if progress:
            progress.close()
        notify("Check Movie Genres", "Scan cancelled", 3000)
        return
    
    if not nfo_files:
        if progress:
            progress.close()
        notify("Check Movie Genres", "No .nfo files found!", 5000)
        return
    
    log("Found {} .nfo files".format(len(nfo_files)))
    
    # Check consistency
    if progress:
        progress.update(0, "Checking consistency...", "Comparing NFO vs filename genres...", "")
    
    matches = []
    mismatches = []
    no_filename_genre = []
    no_nfo_genre = []
    
    total = len(nfo_files)
    for idx, nfo_info in enumerate(nfo_files):
        if progress:
            percent = int((float(idx) / total) * 100)
            progress.update(percent, "Checking consistency...", nfo_info['folder'], "")
            
            if progress.iscanceled():
                progress.close()
                notify("Check Movie Genres", "Check cancelled", 3000)
                return
        
        nfo_path = nfo_info['path']
        folder_name = nfo_info['folder']
        nfo_filename = nfo_info['nfo_filename']
        
        # Get NFO genre
        nfo_genre = parse_nfo_genre(nfo_path)
        
        # Get filename genre
        filename_genre = extract_genre_from_filename(nfo_filename)
        
        # Compare
        if nfo_genre is None:
            no_nfo_genre.append(folder_name)
        elif filename_genre is None:
            no_filename_genre.append(folder_name)
        elif nfo_genre == filename_genre:
            matches.append(folder_name)
        else:
            mismatches.append({
                'movie': folder_name,
                'nfo': nfo_genre,
                'filename': filename_genre
            })
    
    if progress:
        progress.close()
    
    # Generate report
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("MOVIE GENRE CONSISTENCY REPORT")
    report_lines.append("=" * 80)
    report_lines.append("")
    report_lines.append("Total movies scanned: {}".format(len(nfo_files)))
    report_lines.append("Matching: {}".format(len(matches)))
    report_lines.append("MISMATCHES: {}".format(len(mismatches)))
    report_lines.append("No filename genre found: {}".format(len(no_filename_genre)))
    report_lines.append("No NFO genre: {}".format(len(no_nfo_genre)))
    report_lines.append("")
    
    # Mismatches (most important!)
    if mismatches:
        report_lines.append("=" * 80)
        report_lines.append("MISMATCHES (NFO genre doesn't match filename genre):")
        report_lines.append("=" * 80)
        for item in sorted(mismatches, key=lambda x: x['movie']):
            report_lines.append("")
            report_lines.append("Movie: {}".format(item['movie']))
            report_lines.append("  NFO Genre:      {}".format(item['nfo']))
            report_lines.append("  Filename Genre: {} (CORRECT)".format(item['filename']))
        report_lines.append("")
    
    # No filename genre
    if no_filename_genre:
        report_lines.append("=" * 80)
        report_lines.append("NO GENRE IN FILENAME:")
        report_lines.append("=" * 80)
        for movie in sorted(no_filename_genre):
            report_lines.append("  - {}".format(movie))
        report_lines.append("")
    
    # No NFO genre
    if no_nfo_genre:
        report_lines.append("=" * 80)
        report_lines.append("NO GENRE IN NFO:")
        report_lines.append("=" * 80)
        for movie in sorted(no_nfo_genre):
            report_lines.append("  - {}".format(movie))
        report_lines.append("")
    
    report_content = "\n".join(report_lines)
    
    # Write report
    if KODI_MODE:
        report_path = xbmc.translatePath('special://temp/movie_genre_consistency_report.txt')
    else:
        report_path = os.path.join(os.path.expanduser('~'), 'movie_genre_consistency_report.txt')
    
    write_report(report_path, report_content)
    
    # Show report in text viewer
    if KODI_MODE:
        xbmcgui.Dialog().textviewer("Movie Genre Consistency Report", report_content)
    
    notify("Check Movie Genres", "Found {} mismatches!".format(len(mismatches)), 5000)
    
    log("=" * 60)
    log("Consistency check complete!")
    log("Mismatches: {}".format(len(mismatches)))
    log("Report saved to: {}".format(report_path))
    log("=" * 60)

if __name__ == "__main__":
    # Get base path from command line or use default
    if len(sys.argv) > 1:
        base_path = sys.argv[1]
    else:
        # Default path
        if KODI_MODE:
            base_path = "nfs://10.0.0.39/mnt/user/MOVIES/"
        else:
            base_path = "/path/to/movies/"
    
    check_movie_genre_consistency(base_path)