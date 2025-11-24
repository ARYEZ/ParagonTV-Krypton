#   Copyright (C) 2025 Aryez
#
# This file is part of Paragon TV.
#
# Paragon TV is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Paragon TV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Paragon TV.  If not, see <http://www.gnu.org/licenses/>.

import json
import os

import xbmc
import xbmcaddon
import xbmcgui

# Constants
ADDON = xbmcaddon.Addon("script.paragontv")
ADDON_NAME = ADDON.getAddonInfo("name")
CWD = ADDON.getAddonInfo("path")

ACTION_PREVIOUS_MENU = [9, 10, 92, 216, 247, 257, 275, 61467, 61448]
ACTION_MOVE_LEFT = 1
ACTION_MOVE_RIGHT = 2
ACTION_MOVE_UP = 3
ACTION_MOVE_DOWN = 4
ACTION_SELECT_ITEM = 7


class SeasonBrowserWindow(xbmcgui.WindowXMLDialog):
    """First window - displays seasons only"""

    def __init__(self, *args, **kwargs):
        xbmcgui.WindowXMLDialog.__init__(self, *args, **kwargs)
        self.showInfo = kwargs.get("showInfo", {})
        self.overlay = kwargs.get("overlay", None)
        self.selectedSeason = None
        self.seasons = []

    def onInit(self):
        self.log("SeasonBrowserWindow onInit")

        # Set window properties
        self.setProperty("ShowTitle", self.showInfo.get("title", "Unknown Show"))

        # Get show landscape artwork for right side
        showLandscape = self.getShowLandscape()
        if showLandscape:
            self.setProperty("ShowLandscape", showLandscape)

        # Load seasons
        self.loadSeasons()

        # Populate season list
        self.populateSeasonList()

    def loadSeasons(self):
        """Load seasons for the show"""
        try:
            showPath = self.showInfo.get("path", "")

            if "videodb://" in showPath:
                # Extract show ID from path
                showId = int(showPath.split("/")[-2])

                # Get seasons using JSON-RPC
                json_query = {
                    "jsonrpc": "2.0",
                    "method": "VideoLibrary.GetSeasons",
                    "params": {
                        "tvshowid": showId,
                        "properties": [
                            "season",
                            "episode",
                            "watchedepisodes",
                            "thumbnail",
                        ],
                    },
                    "id": 1,
                }

                result = xbmc.executeJSONRPC(json.dumps(json_query))
                result = json.loads(result)

                if "result" in result and "seasons" in result["result"]:
                    self.seasons = result["result"]["seasons"]
                    self.log("Loaded {} seasons".format(len)(self.seasons))

        except Exception as e:
            self.log("Error loading seasons: " + str(e))

    def populateSeasonList(self):
        """Populate the season list control"""
        try:
            seasonList = self.getControl(8000)
            seasonList.reset()

            for season in self.seasons:
                seasonNum = season.get("season", 0)
                episodeCount = season.get("episode", 0)

                # Format season label (left aligned)
                if seasonNum == 0:
                    label = "Specials"
                else:
                    label = "Season {}".format(seasonNum)

                # Format episode count (will be right aligned)
                label2 = "({} episodes)".format(episodeCount)

                # Create list item
                item = xbmcgui.ListItem(label)
                item.setLabel2(label2)
                item.setProperty("season_number", str(seasonNum))

                # Add thumbnail if available
                if "thumbnail" in season:
                    item.setArt({"thumb": season["thumbnail"]})

                seasonList.addItem(item)

        except Exception as e:
            self.log("Error populating season list: " + str(e))

    def getShowLandscape(self):
        """Get show landscape artwork"""
        try:
            showTitle = self.showInfo.get("title", "")

            # First try to find landscape image in the show's folder if we have a path
            showPath = self.showInfo.get("path", "")
            if showPath and os.path.exists(showPath):
                landscapePath = os.path.join(showPath, "landscape.jpg")
                if os.path.exists(landscapePath):
                    return landscapePath

            # Try JSON-RPC to get show artwork
            json_query = {
                "jsonrpc": "2.0",
                "method": "VideoLibrary.GetTVShows",
                "params": {
                    "filter": {"field": "title", "operator": "is", "value": showTitle},
                    "properties": ["art"],
                },
                "id": 1,
            }

            result = xbmc.executeJSONRPC(json.dumps(json_query))
            result = json.loads(result)

            if (
                "result" in result
                and "tvshows" in result["result"]
                and result["result"]["tvshows"]
            ):
                show = result["result"]["tvshows"][0]
                if "art" in show:
                    # Priority: landscape > fanart
                    if "landscape" in show["art"]:
                        return show["art"]["landscape"]
                    elif "fanart" in show["art"]:
                        return show["art"]["fanart"]

        except Exception as e:
            self.log("Error getting show landscape: " + str(e))

        return None

    def onClick(self, controlId):
        """Handle clicks"""
        if controlId == 8000:  # Season list
            try:
                seasonList = self.getControl(8000)
                selectedItem = seasonList.getSelectedItem()

                if selectedItem:
                    seasonNum = int(selectedItem.getProperty("season_number"))

                    # Find the selected season data
                    for season in self.seasons:
                        if season.get("season", -1) == seasonNum:
                            self.selectedSeason = season
                            break

                    # Open episode window
                    self.openEpisodeWindow(seasonNum)

            except Exception as e:
                self.log("Error in onClick: " + str(e))

    def openEpisodeWindow(self, seasonNum):
        """Open the episode browser for the selected season"""
        self.log("Opening episode window for season {}".format(seasonNum))

        # Create episode window
        episodeWindow = EpisodeListWindow(
            "script.paragontv.EpisodeListWindow.xml",
            CWD,
            "default",
            showInfo=self.showInfo,
            seasonNum=seasonNum,
            overlay=self.overlay,
        )

        # Show the episode window
        episodeWindow.doModal()

        # Check if an episode was selected
        if episodeWindow.selectedEpisode:
            # Pass the selected episode back to the original window
            self.selectedEpisode = episodeWindow.selectedEpisode
            # Close this window to return to overlay
            self.close()

        del episodeWindow

    def onAction(self, action):
        """Handle actions"""
        actionId = action.getId()

        if actionId in ACTION_PREVIOUS_MENU:
            self.close()

    def log(self, msg, level=xbmc.LOGDEBUG):
        """Log messages"""
        xbmc.log(ADDON_NAME + " SeasonBrowserWindow: " + msg, level)


class EpisodeListWindow(xbmcgui.WindowXMLDialog):
    """Second window - displays episodes for selected season"""

    def __init__(self, *args, **kwargs):
        xbmcgui.WindowXMLDialog.__init__(self, *args, **kwargs)
        self.showInfo = kwargs.get("showInfo", {})
        self.seasonNum = kwargs.get("seasonNum", 1)
        self.overlay = kwargs.get("overlay", None)
        self.selectedEpisode = None
        self.episodes = []

    def onInit(self):
        self.log("EpisodeListWindow onInit")

        # Set window properties
        showTitle = self.showInfo.get("title", "Unknown Show")
        if self.seasonNum == 0:
            seasonLabel = "Specials"
        else:
            seasonLabel = "Season {}".format(self.seasonNum)

        self.setProperty("ShowTitle", showTitle)
        self.setProperty("SeasonLabel", seasonLabel)

        # Get show logo/banner
        showLogo = self.getShowArtwork()
        if showLogo:
            self.setProperty("ShowLogo", showLogo)

        # Load episodes
        self.loadEpisodes()

        # Populate episode list
        self.populateEpisodeList()

    def loadEpisodes(self):
        """Load episodes for the selected season"""
        try:
            showPath = self.showInfo.get("path", "")

            if "videodb://" in showPath:
                # Extract show ID
                showId = int(showPath.split("/")[-2])

                # Get episodes using JSON-RPC
                json_query = {
                    "jsonrpc": "2.0",
                    "method": "VideoLibrary.GetEpisodes",
                    "params": {
                        "tvshowid": showId,
                        "season": self.seasonNum,
                        "properties": [
                            "title",
                            "episode",
                            "plot",
                            "thumbnail",
                            "file",
                            "runtime",
                            "firstaired",
                        ],
                        "sort": {"order": "ascending", "method": "episode"},
                    },
                    "id": 1,
                }

                result = xbmc.executeJSONRPC(json.dumps(json_query))
                result = json.loads(result)

                if "result" in result and "episodes" in result["result"]:
                    self.episodes = result["result"]["episodes"]
                    self.log("Loaded {} episodes".format(len)(self.episodes))

        except Exception as e:
            self.log("Error loading episodes: " + str(e))

    def populateEpisodeList(self):
        """Populate the episode list control"""
        try:
            episodeList = self.getControl(8001)
            episodeList.reset()

            for episode in self.episodes:
                episodeNum = episode.get("episode", 0)
                episodeTitle = episode.get("title", "Unknown Episode")
                plot = episode.get("plot", "")
                thumbnail = episode.get("thumbnail", "")
                runtime = episode.get("runtime", 0)
                firstaired = episode.get("firstaired", "")

                # Extract year from firstaired date
                year = ""
                if firstaired:
                    try:
                        year = firstaired.split("-")[0]
                    except Exception as e:
                        year = "2005"  # Default year if parsing fails

                # Format label for list display
                if episodeNum > 0:
                    if self.seasonNum == 0:
                        label = "%02d. %s" % (episodeNum, episodeTitle.upper())
                    else:
                        label = "%02d. %s" % (episodeNum, episodeTitle.upper())
                else:
                    label = episodeTitle.upper()

                # Create list item
                item = xbmcgui.ListItem(label)
                item.setProperty("episode_file", episode.get("file", ""))
                item.setProperty("year", year)
                item.setInfo("video", {"plot": plot})

                # Set quality icon (you can customize this logic)
                # For now, using Blu-ray icon as placeholder
                item.setProperty(
                    "quality_icon", "special://skin/media/logos/bluray.png"
                )

                # Set thumbnail
                if thumbnail:
                    item.setArt({"thumb": thumbnail})

                episodeList.addItem(item)

        except Exception as e:
            self.log("Error populating episode list: " + str(e))

    def getShowArtwork(self):
        """Get show logo/banner artwork"""
        try:
            showTitle = self.showInfo.get("title", "")

            json_query = {
                "jsonrpc": "2.0",
                "method": "VideoLibrary.GetTVShows",
                "params": {
                    "filter": {"field": "title", "operator": "is", "value": showTitle},
                    "properties": ["art"],
                },
                "id": 1,
            }

            result = xbmc.executeJSONRPC(json.dumps(json_query))
            result = json.loads(result)

            if (
                "result" in result
                and "tvshows" in result["result"]
                and result["result"]["tvshows"]
            ):
                show = result["result"]["tvshows"][0]
                if "art" in show:
                    if "clearlogo" in show["art"]:
                        return show["art"]["clearlogo"]
                    elif "banner" in show["art"]:
                        return show["art"]["banner"]
                    elif "landscape" in show["art"]:
                        return show["art"]["landscape"]

        except Exception as e:
            self.log("Error getting show artwork: " + str(e))

        return None

    def onClick(self, controlId):
        """Handle clicks"""
        if controlId == 8001:  # Episode list
            try:
                episodeList = self.getControl(8001)
                selectedItem = episodeList.getSelectedItem()

                if selectedItem:
                    episodeFile = selectedItem.getProperty("episode_file")
                    if episodeFile:
                        self.selectedEpisode = episodeFile
                        self.close()

            except Exception as e:
                self.log("Error in onClick: " + str(e))

    def onAction(self, action):
        """Handle actions"""
        actionId = action.getId()

        if actionId in ACTION_PREVIOUS_MENU:
            self.close()

    def log(self, msg, level=xbmc.LOGDEBUG):
        """Log messages"""
        xbmc.log(ADDON_NAME + " EpisodeListWindow: " + msg, level)


class EpisodeBrowserWindow(xbmcgui.WindowXMLDialog):
    """Main entry point - opens season browser"""

    def __init__(self, *args, **kwargs):
        xbmcgui.WindowXMLDialog.__init__(self, *args, **kwargs)
        self.showInfo = kwargs.get("showInfo", {})
        self.overlay = kwargs.get("overlay", None)
        self.selectedEpisode = None

    def onInit(self):
        # Immediately close and open season browser
        self.close()
        self.openSeasonBrowser()

    def openSeasonBrowser(self):
        """Open the season browser window"""
        seasonWindow = SeasonBrowserWindow(
            "script.paragontv.SeasonBrowserWindow.xml",
            CWD,
            "default",
            showInfo=self.showInfo,
            overlay=self.overlay,
        )

        seasonWindow.doModal()

        # Check if an episode was selected
        if hasattr(seasonWindow, "selectedEpisode"):
            self.selectedEpisode = seasonWindow.selectedEpisode

        del seasonWindow

    def log(self, msg, level=xbmc.LOGDEBUG):
        """Log messages"""
        xbmc.log(ADDON_NAME + " EpisodeBrowserWindow: " + msg, level)
