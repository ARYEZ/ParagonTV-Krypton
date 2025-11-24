#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Organize Movie Genres - SAFE VERSION
Scans movie library, previews changes, asks for confirmation, creates backups
Supports both Kodi VFS (NFS/SMB) and standard filesystem paths
"""

import sys
import os
import re
from datetime import datetime

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
    except:
        ADDON = None
        ADDON_ID = "organize_movie_genres"
        ICON = ""
except ImportError:
    KODI_MODE = False
    ADDON = None
    ADDON_ID = "organize_movie_genres"
    ICON = ""

# XML parsing
try:
    import xml.etree.ElementTree as ET
except ImportError:
    import elementtree.ElementTree as ET

def log(msg):
    """Log message to Kodi log or console."""
    if KODI_MODE:
        xbmc.log("[Organize Movie Genres] {}".format(msg), xbmc.LOGNOTICE)
    else:
        print("[Organize Movie Genres] {}".format(msg))

def notify(title, message, time=5000):
    """Show notification with Paragon TV icon."""
    if KODI_MODE:
        xbmcgui.Dialog().notification(title, message, ICON, time)
    else:
        print("[NOTIFY] {}: {}".format(title, message))

# Genre mappings and organization rules
GENRE_MAPPINGS = {
    # Animation
    'Animation': 'Animation',
    'Anime': 'Animation',
    'Animated': 'Animation',
    
    # Comedy
    'Comedy': 'Comedy',
    'Romantic Comedy': 'Comedy',
    'Rom-Com': 'Comedy',
    
    # Drama
    'Drama': 'Drama',
    'Period Drama': 'Drama',
    'Historical Drama': 'Drama',
    
    # Science Fiction
    'Science Fiction': 'Science Fiction',
    'Science-Fiction': 'Science Fiction',
    'Sci-Fi': 'Science Fiction',
    'SciFi': 'Science Fiction',
    
    # Documentary
    'Documentary': 'Documentary',
    'Docudrama': 'Documentary',
    
    # Crime & Mystery - keep separate
    'Crime': 'Crime',
    'Mystery': 'Mystery',
    
    # Action & Adventure - DO NOT MAP, keep them separate
    'Action': 'Action',
    'Adventure': 'Adventure',
    
    # Horror & Thriller - keep separate
    'Horror': 'Horror',
    'Thriller': 'Thriller',
    
    # Music
    'Music': 'Music',
    'Musical': 'Music',
    
    # Family & Kids - keep separate
    'Family': 'Family',
    'Kids': 'Family',
    
    # War
    'War': 'War',
    'War & Politics': 'War',
    
    # Western
    'Western': 'Western',
    
    # Fantasy
    'Fantasy': 'Fantasy',
    
    # News
    'News': 'News',
}

def normalize_genre(genre):
    """Normalize genre name to standard format."""
    if not genre:
        return None
    
    genre = genre.strip()
    
    # Check if it's in our mapping
    if genre in GENRE_MAPPINGS:
        return GENRE_MAPPINGS[genre]
    
    # If not in mapping, return original (don't change it)
    return genre

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
                for filename in folder_files:
                    if filename.lower().endswith('.nfo'):
                        nfo_path = folder_path + '/' + filename
                        nfo_files_found.append({
                            'path': nfo_path,
                            'folder': folder_name,
                            'folder_path': folder_path
                        })
                        log("Found NFO: {}".format(nfo_path))
                        break  # Only take first .nfo file found
                        
            except Exception as e:
                log("Error checking folder {}: {}".format(folder_name, str(e)))
                continue
        
        log("Scan complete: {} folders scanned, {} .nfo files found".format(
            folders_scanned, len(nfo_files_found)))
        
        return nfo_files_found
        
    except Exception as e:
        log("Error reading folder {}: {}".format(base_path, str(e)))
        return []

def parse_nfo_file(filepath):
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
            with open(filepath, 'r') as f:
                content = f.read()
        
        genre_elem = root.find('genre')
        genre = genre_elem.text if genre_elem is not None else None
        
        return genre, root, content
    except Exception as e:
        log("Error parsing {}: {}".format(filepath, str(e)))
        return None, None, None

def create_backup(filepath, content):
    """Create a timestamped backup of the NFO file."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = "{}.backup_{}".format(filepath, timestamp)
        
        if KODI_MODE and (filepath.startswith('nfs://') or filepath.startswith('smb://')):
            backup_file = xbmcvfs.File(backup_path, 'w')
            backup_file.write(content)
            backup_file.close()
        else:
            with open(backup_path, 'w') as f:
                f.write(content)
        
        log("Created backup: {}".format(backup_path))
        return True
    except Exception as e:
        log("Error creating backup for {}: {}".format(filepath, str(e)))
        return False

def update_nfo_genre(filepath, root, content, new_genre):
    """Update the genre in the NFO file using simple string replacement."""
    try:
        # Create backup first
        if not create_backup(filepath, content):
            log("Failed to create backup, skipping update for: {}".format(filepath))
            return False
        
        # Use simple regex to replace ONLY the genre tag content
        import re
        updated_content = re.sub(
            r'<genre>.*?</genre>',
            '<genre>{}</genre>'.format(new_genre),
            content,
            count=1  # Only replace the first occurrence
        )
        
        log("Original genre tag: {}".format(re.search(r'<genre>.*?</genre>', content).group()))
        log("New genre tag: <genre>{}</genre>".format(new_genre))
        
        # Write back to file
        if KODI_MODE and (filepath.startswith('nfs://') or filepath.startswith('smb://')):
            nfo_file = xbmcvfs.File(filepath, 'w')
            nfo_file.write(updated_content)
            nfo_file.close()
        else:
            with open(filepath, 'w') as f:
                f.write(updated_content)
        
        return True
    except Exception as e:
        log("Error updating {}: {}".format(filepath, str(e)))
        return False

def show_preview_and_confirm(proposed_changes):
    """Show preview of changes and ask for confirmation."""
    if not KODI_MODE:
        print("\n" + "=" * 60)
        print("PROPOSED CHANGES:")
        print("=" * 60)
        for change in proposed_changes[:20]:
            print("{}: {} -> {}".format(change['movie'], change['old'], change['new']))
        if len(proposed_changes) > 20:
            print("... and {} more".format(len(proposed_changes) - 20))
        response = raw_input("\nApply these changes? (y/n): ")
        return response.lower() == 'y'
    
    # Kodi mode - show text viewer
    preview_text = "PROPOSED CHANGES:\n"
    preview_text += "=" * 60 + "\n\n"
    preview_text += "Total changes: {}\n\n".format(len(proposed_changes))
    
    for change in proposed_changes:
        preview_text += "{}\n".format(change['movie'])
        preview_text += "  Current: {}\n".format(change['old'])
        preview_text += "  New: {}\n\n".format(change['new'])
    
    # Show in text viewer
    xbmcgui.Dialog().textviewer("Preview Changes", preview_text)
    
    # Ask for confirmation
    result = xbmcgui.Dialog().yesno(
        "Confirm Changes",
        "Apply {} genre changes?[CR][CR]"
        "Backups will be created before modifying files.".format(len(proposed_changes)),
        nolabel="Cancel",
        yeslabel="Apply Changes"
    )
    
    return result

def organize_movie_genres(base_path):
    """Main function to organize movie genres."""
    log("=" * 60)
    log("Starting Movie Genre Organization")
    log("Base path: {}".format(base_path))
    log("=" * 60)
    
    notify("Organize Movie Genres", "Starting scan...")
    
    # Create progress dialog
    if KODI_MODE:
        progress = xbmcgui.DialogProgress()
        progress.create("Organize Movie Genres", "Initializing...")
    else:
        progress = None
    
    # Scan for NFO files
    nfo_files = scan_movie_folders(base_path, progress)
    
    if progress:
        progress.close()
    
    if nfo_files is None:
        notify("Organize Movie Genres", "Scan cancelled", 3000)
        return
    
    if not nfo_files:
        notify("Organize Movie Genres", "No movie.nfo files found!", 5000)
        return
    
    log("Found {} movie.nfo files".format(len(nfo_files)))
    notify("Organize Movie Genres", "Found {} movies. Analyzing...".format(len(nfo_files)), 3000)
    
    # Analyze changes
    if KODI_MODE:
        progress = xbmcgui.DialogProgress()
        progress.create("Analyze Changes", "Checking genres...")
    
    proposed_changes = []
    unchanged = []
    errors = []
    
    total = len(nfo_files)
    for idx, nfo_info in enumerate(nfo_files):
        if progress:
            percent = int((float(idx) / total) * 100)
            progress.update(percent, "Analyzing changes...", nfo_info['folder'], "")
            
            if progress.iscanceled():
                progress.close()
                notify("Organize Movie Genres", "Analysis cancelled", 3000)
                return
        
        nfo_path = nfo_info['path']
        folder_name = nfo_info['folder']
        
        # Parse NFO
        current_genre, root, content = parse_nfo_file(nfo_path)
        
        if root is None:
            errors.append("Error parsing: {}".format(folder_name))
            continue
        
        # Normalize genre
        normalized_genre = normalize_genre(current_genre)
        
        # Check if change needed
        if normalized_genre and current_genre != normalized_genre:
            proposed_changes.append({
                'movie': folder_name,
                'old': current_genre or 'None',
                'new': normalized_genre,
                'nfo_path': nfo_path,
                'root': root,
                'content': content
            })
        else:
            unchanged.append(folder_name)
    
    if progress:
        progress.close()
    
    # Show results
    if not proposed_changes:
        notify("Organize Movie Genres", "No changes needed! All genres are already correct.", 5000)
        log("No changes needed")
        return
    
    log("Found {} proposed changes".format(len(proposed_changes)))
    
    # Show preview and get confirmation
    if not show_preview_and_confirm(proposed_changes):
        notify("Organize Movie Genres", "Changes cancelled", 3000)
        log("User cancelled changes")
        return
    
    # Apply changes
    if KODI_MODE:
        progress = xbmcgui.DialogProgress()
        progress.create("Applying Changes", "Updating NFO files...")
    
    changes_made = []
    change_errors = []
    
    total = len(proposed_changes)
    for idx, change in enumerate(proposed_changes):
        if progress:
            percent = int((float(idx) / total) * 100)
            progress.update(percent, "Updating files...", change['movie'], "")
            
            if progress.iscanceled():
                progress.close()
                notify("Organize Movie Genres", "Update cancelled - {} of {} applied".format(len(changes_made), total), 5000)
                return
        
        # Update NFO
        if update_nfo_genre(change['nfo_path'], change['root'], change['content'], change['new']):
            changes_made.append(change)
            log("Updated {}: {} -> {}".format(change['movie'], change['old'], change['new']))
        else:
            change_errors.append("Error updating: {}".format(change['movie']))
    
    if progress:
        progress.close()
    
    # Show completion notification
    notify("Organize Movie Genres", "Complete! Updated {} movies".format(len(changes_made)), 5000)
    
    log("=" * 60)
    log("Organization complete!")
    log("Changes made: {}".format(len(changes_made)))
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
    
    organize_movie_genres(base_path)