#   Copyright (C) 2025 Aryez
#
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

import base64
import datetime
import os
import random
import re
import subprocess
import sys
import threading
import time
from xml.dom.minidom import parse, parseString

import httplib
import xbmc
import xbmcaddon
import xbmcgui
from Channel import Channel
from FileAccess import FileAccess, FileLock
from GlobalRulesHandler import GlobalRulesHandler
from Globals import *
from Playlist import Playlist
from VideoParser import VideoParser


class ChannelList:
    def __init__(self):
        self.showGenreList = []
        self.movieGenreList = []
        self.musicGenreList = []
        self.channels = []
        self.videoParser = VideoParser()
        self.sleepTime = 0
        self.threadPaused = False
        self.runningActionChannel = 0
        self.runningActionId = 0
        self.enteredChannelCount = 0
        self.background = True
        random.seed()

    def readConfig(self):
        self.channelResetSetting = int(ADDON.getSetting("ChannelResetSetting"))
        self.log("Channel Reset Setting is " + str(self.channelResetSetting))
        self.forceReset = ADDON.getSetting("ForceChannelReset") == "true"
        self.log("Force Reset is " + str(self.forceReset))
        self.updateDialog = xbmcgui.DialogProgress()
        self.startMode = int(ADDON.getSetting("StartMode"))
        self.log("Start Mode is " + str(self.startMode))
        self.backgroundUpdating = int(ADDON.getSetting("ThreadMode"))
        self.mediaLimit = MEDIA_LIMIT[int(ADDON.getSetting("MediaLimit"))]
        self.showSeasonEpisode = ADDON.getSetting("ShowSeEp") == "true"
        self.findMaxChannels()

        if self.forceReset:
            ADDON.setSetting("ForceChannelReset", "False")
            self.forceReset = False

        try:
            self.lastResetTime = int(ADDON_SETTINGS.getSetting("LastResetTime"))
        except:
            self.lastResetTime = 0

        try:
            self.lastExitTime = int(ADDON_SETTINGS.getSetting("LastExitTime"))
        except:
            self.lastExitTime = int(time.time())

    def setupList(self):
        self.readConfig()
        self.updateDialog.create(ADDON_NAME, "Updating channel list")
        self.updateDialog.update(0, "Updating channel list")
        self.updateDialogProgress = 0
        foundvalid = False
        makenewlists = False
        self.background = False

        if self.backgroundUpdating > 0 and self.myOverlay.isMaster == True:
            makenewlists = True

        # Go through all channels, create their arrays, and setup the new playlist
        for i in range(self.maxChannels):
            self.updateDialogProgress = i * 100 // self.enteredChannelCount
            self.updateDialog.update(
                self.updateDialogProgress,
                "Loading channel " + str(i + 1),
                "waiting for file lock",
            )
            self.channels.append(Channel())

            # If the user pressed cancel, stop everything and exit
            if self.updateDialog.iscanceled():
                self.log("Update channels cancelled")
                self.updateDialog.close()
                return None

            self.setupChannel(i + 1, False, makenewlists, False)

            if self.channels[i].isValid:
                foundvalid = True

        if makenewlists == True:
            ADDON.setSetting("ForceChannelReset", "false")

        if foundvalid == False and makenewlists == False:
            for i in range(self.maxChannels):
                self.updateDialogProgress = i * 100 // self.enteredChannelCount
                self.updateDialog.update(
                    self.updateDialogProgress,
                    "Updating channel " + str(i + 1),
                    "waiting for file lock",
                    "",
                )
                self.setupChannel(i + 1, False, True, False)

                if self.channels[i].isValid:
                    foundvalid = True
                    break

        self.updateDialog.update(100, "Update complete")
        self.updateDialog.close()

        return self.channels

    def log(self, msg, level=xbmc.LOGDEBUG):
        log("ChannelList: " + msg, level)

    # Determine the maximum number of channels by opening consecutive
    # playlists until we don't find one
    def findMaxChannels(self):
        self.log("findMaxChannels")
        self.maxChannels = 0
        self.enteredChannelCount = 0

        for i in range(999):
            chtype = 9999
            chsetting1 = ""
            chsetting2 = ""

            try:
                chtype = int(
                    ADDON_SETTINGS.getSetting("Channel_" + str(i + 1) + "_type")
                )
                chsetting1 = ADDON_SETTINGS.getSetting("Channel_" + str(i + 1) + "_1")
                chsetting2 = ADDON_SETTINGS.getSetting("Channel_" + str(i + 1) + "_2")
            except:
                pass

            if chtype == 0:
                if FileAccess.exists(xbmc.translatePath(chsetting1)):
                    self.maxChannels = i + 1
                    self.enteredChannelCount += 1
            elif chtype < 8 or chtype == 12:  # Added check for type 12
                if len(chsetting1) > 0:
                    self.maxChannels = i + 1
                    self.enteredChannelCount += 1

            if self.forceReset and (chtype != 9999):
                ADDON_SETTINGS.setSetting("Channel_" + str(i + 1) + "_changed", "True")

        self.log("findMaxChannels return " + str(self.maxChannels))

    def sendJSON(self, command):
        data = xbmc.executeJSONRPC(command)
        return unicode(data, "utf-8", errors="ignore")

    def setupChannel(self, channel, background=False, makenewlist=False, append=False):
        self.log("setupChannel " + str(channel))
        returnval = False
        createlist = makenewlist
        chtype = 9999
        chsetting1 = ""
        chsetting2 = ""
        needsreset = False
        self.background = background
        self.settingChannel = channel

        try:
            chtype = int(ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_type"))
            chsetting1 = ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_1")
            chsetting2 = ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_2")
        except:
            pass

        while len(self.channels) < channel:
            self.channels.append(Channel())

        if chtype == 9999:
            self.channels[channel - 1].isValid = False
            return False

        self.channels[channel - 1].isSetup = True

        # Load channel-specific rules
        self.channels[channel - 1].loadRules(channel)

        # NEW: Apply global rules if enabled
        try:
            from GlobalRulesHandler import GlobalRulesHandler

            globalHandler = GlobalRulesHandler()

            # Apply global rules based on channel type
            if globalHandler.isChannelTypeEnabled(chtype):
                self.log(
                    "Applying global rules to channel "
                    + str(channel)
                    + " (type "
                    + str(chtype)
                    + ")"
                )
                globalHandler.applyGlobalRules(self.channels[channel - 1], chtype)
        except Exception as e:
            self.log("Error applying global rules: " + str(e))

        # Run start actions after all rules are loaded
        self.runActions(RULES_ACTION_START, channel, self.channels[channel - 1])

        try:
            needsreset = (
                ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_changed")
                == "True"
            )

            if needsreset:
                self.channels[channel - 1].isSetup = False
        except:
            pass

        # If possible, use an existing playlist
        # Don't do this if we're appending an existing channel
        # Don't load if we need to reset anyway
        if (
            FileAccess.exists(CHANNELS_LOC + "channel_" + str(channel) + ".m3u")
            and append == False
            and needsreset == False
        ):
            try:
                self.channels[channel - 1].totalTimePlayed = int(
                    ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_time", True)
                )
                createlist = True

                if self.background == False:
                    self.updateDialog.update(
                        self.updateDialogProgress,
                        "Loading channel " + str(channel),
                        "reading playlist",
                        "",
                    )

                if (
                    self.channels[channel - 1].setPlaylist(
                        CHANNELS_LOC + "channel_" + str(channel) + ".m3u"
                    )
                    == True
                ):
                    self.channels[channel - 1].isValid = True
                    self.channels[channel - 1].fileName = (
                        CHANNELS_LOC + "channel_" + str(channel) + ".m3u"
                    )
                    returnval = True

                    # If this channel has been watched for longer than it lasts, reset the channel
                    if (
                        self.channelResetSetting == 0
                        and self.channels[channel - 1].totalTimePlayed
                        < self.channels[channel - 1].getTotalDuration()
                    ):
                        createlist = False

                    if self.channelResetSetting > 0 and self.channelResetSetting < 4:
                        timedif = time.time() - self.lastResetTime

                        if self.channelResetSetting == 1 and timedif < (60 * 60 * 24):
                            createlist = False

                        if self.channelResetSetting == 2 and timedif < (
                            60 * 60 * 24 * 7
                        ):
                            createlist = False

                        if self.channelResetSetting == 3 and timedif < (
                            60 * 60 * 24 * 30
                        ):
                            createlist = False

                        if timedif < 0:
                            createlist = False

                    if self.channelResetSetting == 4:
                        createlist = False
            except:
                pass

        if createlist or needsreset:
            self.channels[channel - 1].isValid = False

            if makenewlist:
                try:
                    os.remove(CHANNELS_LOC + "channel_" + str(channel) + ".m3u")
                except:
                    pass

                append = False

                if createlist:
                    ADDON_SETTINGS.setSetting("LastResetTime", str(int(time.time())))

        if append == False:
            # if there is no start mode in the channel mode flags, set it to the default
            if self.channels[channel - 1].mode & MODE_STARTMODES == 0:
                if self.startMode == 0:
                    self.channels[channel - 1].mode |= MODE_RESUME
                elif self.startMode == 1:
                    self.channels[channel - 1].mode |= MODE_REALTIME
                elif self.startMode == 2:
                    self.channels[channel - 1].mode |= MODE_RANDOM

        if ((createlist or needsreset) and makenewlist) or append:
            if self.background == False:
                self.updateDialogProgress = (
                    (channel - 1) * 100 // self.enteredChannelCount
                )
                self.updateDialog.update(
                    self.updateDialogProgress,
                    "Updating channel " + str(channel),
                    "adding videos",
                    "",
                )

            if (
                self.makeChannelList(channel, chtype, chsetting1, chsetting2, append)
                == True
            ):
                if (
                    self.channels[channel - 1].setPlaylist(
                        CHANNELS_LOC + "channel_" + str(channel) + ".m3u"
                    )
                    == True
                ):
                    returnval = True
                    self.channels[channel - 1].fileName = (
                        CHANNELS_LOC + "channel_" + str(channel) + ".m3u"
                    )
                    self.channels[channel - 1].isValid = True

                    # Don't reset variables on an appending channel
                    if append == False:
                        self.channels[channel - 1].totalTimePlayed = 0
                        ADDON_SETTINGS.setSetting(
                            "Channel_" + str(channel) + "_time", "0"
                        )

                        if needsreset:
                            ADDON_SETTINGS.setSetting(
                                "Channel_" + str(channel) + "_changed", "False"
                            )
                            self.channels[channel - 1].isSetup = True

        self.runActions(RULES_ACTION_BEFORE_CLEAR, channel, self.channels[channel - 1])

        # Don't clear history when appending channels
        if self.background == False and append == False and self.myOverlay.isMaster:
            self.updateDialogProgress = (channel - 1) * 100 // self.enteredChannelCount
            self.updateDialog.update(
                self.updateDialogProgress,
                "Loading channel " + str(channel),
                "clearing history",
                "",
            )
            self.clearPlaylistHistory(channel)

        if append == False:
            self.runActions(
                RULES_ACTION_BEFORE_TIME, channel, self.channels[channel - 1]
            )

            if self.channels[channel - 1].mode & MODE_ALWAYSPAUSE > 0:
                self.channels[channel - 1].isPaused = True

            if self.channels[channel - 1].mode & MODE_RANDOM > 0:
                self.channels[channel - 1].showTimeOffset = random.randint(
                    0, self.channels[channel - 1].getTotalDuration()
                )

            if self.channels[channel - 1].mode & MODE_REALTIME > 0:
                timedif = int(self.myOverlay.timeStarted) - self.lastExitTime
                self.channels[channel - 1].totalTimePlayed += timedif

            if self.channels[channel - 1].mode & MODE_RESUME > 0:
                self.channels[channel - 1].showTimeOffset = self.channels[
                    channel - 1
                ].totalTimePlayed
                self.channels[channel - 1].totalTimePlayed = 0

            while (
                self.channels[channel - 1].showTimeOffset
                > self.channels[channel - 1].getCurrentDuration()
            ):
                self.channels[channel - 1].showTimeOffset -= self.channels[
                    channel - 1
                ].getCurrentDuration()
                self.channels[channel - 1].addShowPosition(1)

        self.channels[channel - 1].name = self.getChannelName(chtype, chsetting1)

        if ((createlist or needsreset) and makenewlist) and returnval:
            self.runActions(
                RULES_ACTION_FINAL_MADE, channel, self.channels[channel - 1]
            )
        else:
            self.runActions(
                RULES_ACTION_FINAL_LOADED, channel, self.channels[channel - 1]
            )

        return returnval

    def clearPlaylistHistory(self, channel):
        self.log("clearPlaylistHistory")

        if self.channels[channel - 1].isValid == False:
            self.log("channel not valid, ignoring")
            return

        # if we actually need to clear anything
        if self.channels[channel - 1].totalTimePlayed > (60 * 60 * 24 * 2):
            try:
                fle = FileAccess.open(
                    CHANNELS_LOC + "channel_" + str(channel) + ".m3u", "w"
                )
            except:
                self.log(
                    "clearPlaylistHistory Unable to open the smart playlist",
                    xbmc.LOGERROR,
                )
                return

            flewrite = uni("#EXTM3U\n")
            tottime = 0
            timeremoved = 0

            for i in range(self.channels[channel - 1].Playlist.size()):
                tottime += self.channels[channel - 1].getItemDuration(i)

                if tottime > (
                    self.channels[channel - 1].totalTimePlayed - (60 * 60 * 12)
                ):
                    tmpstr = str(self.channels[channel - 1].getItemDuration(i)) + ","
                    tmpstr += (
                        self.channels[channel - 1].getItemTitle(i)
                        + "//"
                        + self.channels[channel - 1].getItemEpisodeTitle(i)
                        + "//"
                        + self.channels[channel - 1].getItemDescription(i)
                    )
                    tmpstr = uni(tmpstr[:2036])
                    tmpstr = (
                        tmpstr.replace("\\n", " ")
                        .replace("\\r", " ")
                        .replace('\\"', '"')
                    )
                    tmpstr = (
                        uni(tmpstr)
                        + uni("\n")
                        + uni(self.channels[channel - 1].getItemFilename(i))
                    )
                    flewrite += uni("#EXTINF:") + uni(tmpstr) + uni("\n")
                else:
                    timeremoved = tottime

            fle.write(flewrite)
            fle.close()

            if timeremoved > 0:
                if (
                    self.channels[channel - 1].setPlaylist(
                        CHANNELS_LOC + "channel_" + str(channel) + ".m3u"
                    )
                    == False
                ):
                    self.channels[channel - 1].isValid = False
                else:
                    self.channels[channel - 1].totalTimePlayed -= timeremoved
                    # Write this now so anything sharing the playlists will get the proper info
                    ADDON_SETTINGS.setSetting(
                        "Channel_" + str(channel) + "_time",
                        str(self.channels[channel - 1].totalTimePlayed),
                    )

    def getChannelName(self, chtype, setting1):
        self.log("getChannelName " + str(chtype))

        if len(setting1) == 0:
            return ""

        if chtype == 0:
            return self.getSmartPlaylistName(setting1)
        elif chtype == 3:
            return setting1 + " TV"
        elif chtype == 4:
            return setting1 + " Movies"
        elif chtype == 12:
            return "Music Genre - " + setting1

        return ""

    def getSmartPlaylistName(self, fle):
        self.log("getSmartPlaylistName")
        fle = xbmc.translatePath(fle)

        try:
            xml = FileAccess.open(fle, "r")
        except:
            self.log("getSmartPlaylistName Unable to open " + fle)
            return ""

        try:
            dom = parse(xml)
        except:
            self.log("getSmartPlaylistName Unable to parse " + fle)
            xml.close()
            return ""

        xml.close()

        try:
            plname = dom.getElementsByTagName("name")
            self.log("getSmartPlaylistName return " + plname[0].childNodes[0].nodeValue)
            return plname[0].childNodes[0].nodeValue
        except:
            self.log("getSmartPlaylistName return")
            return ""

    # Open the smart playlist and read the name out of it...this is the channel name
    # Smart Distribution Methods - WORKING VERSION WITHOUT EPISODE TRACKING
    def weighted_choice(self, options, weights):
        """
        Select an option based on weighted probabilities.

        Args:
            options: List of options to choose from
            weights: List of weights corresponding to each option

        Returns:
            Selected option
        """
        total = sum(weights)
        if total == 0:
            return random.choice(options)

        r = random.uniform(0, total)
        upto = 0
        for i, w in enumerate(weights):
            if upto + w >= r:
                return options[i]
            upto += w

        return options[-1]

    def applySmartDistribution(self, fileList, limit, channel):
        """
        Applies smart distribution WITHOUT episode tracking.

        Features:
        - Every show gets at least 1 episode
        - Hard cap of 5% (max 5 episodes per 100 total)
        - Exception: channels with <10 shows get no hard cap
        - Weighted selection favors smaller shows

        Args:
            fileList: List of all available episodes (episode strings)
            limit: Maximum number of episodes to return
            channel: Channel number being processed

        Returns:
            List of distributed episodes
        """
        self.log(
            "applySmartDistribution: Starting for channel %d with %d episodes, limit %d"
            % (channel, len(fileList), limit)
        )

        if len(fileList) == 0:
            return []

        # Parse fileList to group episodes by show
        episodes_by_show = {}

        for episode_str in fileList:
            try:
                # Parse the episode string (format: duration,show//episode//description\nfilepath)
                parts = episode_str.split("\n")
                if len(parts) >= 2:
                    info_parts = parts[0].split(",", 1)
                    if len(info_parts) >= 2:
                        # Extract show name
                        show_info = info_parts[1].split("//")
                        show_name = show_info[0] if show_info else "Unknown"

                        if show_name not in episodes_by_show:
                            episodes_by_show[show_name] = []
                        episodes_by_show[show_name].append(episode_str)
            except:
                self.log(
                    "applySmartDistribution: Error parsing episode string",
                    xbmc.LOGWARNING,
                )
                continue

        # Count unique shows
        num_shows = len(episodes_by_show)
        self.log("applySmartDistribution: Found %d unique shows" % num_shows)

        # Log show breakdown
        for show, episodes in episodes_by_show.items():
            self.log("  %s: %d episodes" % (show, len(episodes)))

        # Determine if we should apply hard cap
        apply_hard_cap = num_shows >= 10

        if apply_hard_cap:
            hard_cap_per_show = max(1, int(limit * 0.05))  # 5% cap, minimum 1
            self.log(
                "applySmartDistribution: Hard cap ENABLED - %d episodes max per show"
                % hard_cap_per_show
            )
        else:
            hard_cap_per_show = limit  # No limit for small channels
            self.log(
                "applySmartDistribution: Hard cap DISABLED - only %d shows" % num_shows
            )

        # Randomize episodes within each show
        for show in episodes_by_show:
            random.shuffle(episodes_by_show[show])

        # First pass: Give every show at least 1 episode
        distributed_list = []
        episodes_taken = {}

        for show in episodes_by_show:
            if len(distributed_list) >= limit:
                break
            if len(episodes_by_show[show]) > 0:
                selected_episode = episodes_by_show[show][0]
                distributed_list.append(selected_episode)
                episodes_taken[show] = 1
                # Extract filename for logging
                try:
                    filename = os.path.basename(selected_episode.split("\n")[1])
                    self.log("  Guaranteed episode for %s: %s" % (show, filename))
                except:
                    self.log("  Guaranteed episode for %s" % show)
            else:
                episodes_taken[show] = 0

        # Second pass: Distribute remaining slots using weighted selection
        remaining_slots = limit - len(distributed_list)
        self.log(
            "applySmartDistribution: %d guaranteed episodes, %d remaining slots"
            % (len(distributed_list), remaining_slots)
        )

        for slot in range(remaining_slots):
            # Calculate weights for each show
            weights_dict = {}

            for show in episodes_by_show:
                current_taken = episodes_taken.get(show, 0)
                available_episodes = len(episodes_by_show[show])

                # Skip if show is at hard cap or has no more episodes
                if (
                    current_taken >= hard_cap_per_show
                    or current_taken >= available_episodes
                ):
                    continue

                # Weight calculation: smaller libraries get higher weights
                # Base weight of 100, then divide by library size
                base_weight = 100.0
                size_factor = max(1, available_episodes)
                weight = base_weight / size_factor

                # Bonus for shows with fewer episodes taken so far
                taken_penalty = current_taken * 10
                weight = max(1, weight - taken_penalty)

                weights_dict[show] = weight

            # If no eligible shows, break
            if not weights_dict:
                break

            # Select show using weighted choice
            shows = list(weights_dict.keys())
            weights = list(weights_dict.values())
            selected_show = self.weighted_choice(shows, weights)

            # Add next episode from selected show
            ep_index = episodes_taken[selected_show]
            if ep_index < len(episodes_by_show[selected_show]):
                selected_episode = episodes_by_show[selected_show][ep_index]
                distributed_list.append(selected_episode)
                episodes_taken[selected_show] += 1

        # Apply episode spacing
        distributed_list = self.spaceEpisodes(distributed_list, minimum_spacing=3)

        # Log final distribution
        self.log("applySmartDistribution: Final distribution:")
        show_counts = {}
        for episode_str in distributed_list:
            try:
                parts = episode_str.split("\n")[0].split(",", 1)
                if len(parts) >= 2:
                    show_name = parts[1].split("//")[0]
                    show_counts[show_name] = show_counts.get(show_name, 0) + 1
            except:
                pass

        for show, count in sorted(show_counts.items()):
            self.log("  %s: %d episodes" % (show, count))

        self.log(
            "applySmartDistribution: Completed - returning %d episodes"
            % len(distributed_list)
        )
        return distributed_list

    def spaceEpisodes(self, episode_list, minimum_spacing=3):
        """
        Rearranges episodes to ensure episodes from the same show don't appear too close together.

        Args:
            episode_list: List of episode strings
            minimum_spacing: Minimum number of other episodes between episodes of the same show

        Returns:
            Rearranged episode list
        """
        self.log(
            "spaceEpisodes: Spacing episodes with minimum gap of %d" % minimum_spacing
        )

        if len(episode_list) <= 1:
            return episode_list

        # Extract show names from episodes
        show_episodes = {}
        for i, episode in enumerate(episode_list):
            try:
                parts = episode.split("\n")[0].split(",", 1)
                if len(parts) >= 2:
                    show_name = parts[1].split("//")[0]
                    if show_name not in show_episodes:
                        show_episodes[show_name] = []
                    show_episodes[show_name].append((i, episode))
            except:
                continue

        # If we only have one show, just return the original list
        if len(show_episodes) <= 1:
            return episode_list

        # Build spaced list
        spaced_list = []
        last_show_positions = {}
        remaining_episodes = {}

        # Initialize remaining episodes
        for show, eps in show_episodes.items():
            remaining_episodes[show] = [ep for ep in eps]

        while any(remaining_episodes.values()):
            best_show = None
            best_score = -1

            # Find the best show to place next
            for show, eps in remaining_episodes.items():
                if not eps:
                    continue

                # Calculate score based on spacing and remaining episodes
                if show in last_show_positions:
                    spacing = len(spaced_list) - last_show_positions[show]
                else:
                    spacing = len(spaced_list)  # Never placed before

                # Prioritize shows that haven't been placed recently
                score = spacing

                # Bonus for shows with more remaining episodes
                score += len(eps) * 0.1

                if score > best_score:
                    best_score = score
                    best_show = show

            if best_show is None:
                break

            # Add episode from best show
            episode = remaining_episodes[best_show].pop(0)
            spaced_list.append(episode[1])
            last_show_positions[best_show] = len(spaced_list) - 1

            # Remove empty shows
            if not remaining_episodes[best_show]:
                del remaining_episodes[best_show]

        return spaced_list

    def makeChannelList(self, channel, chtype, setting1, setting2, append=False):
        self.log("makeChannelList " + str(channel))
        israndom = False
        fileList = []

        if chtype == 0:
            if (
                FileAccess.copy(setting1, MADE_CHAN_LOC + os.path.split(setting1)[1])
                == False
            ):
                if (
                    FileAccess.exists(MADE_CHAN_LOC + os.path.split(setting1)[1])
                    == False
                ):
                    self.log("Unable to copy or find playlist " + setting1)
                    return False
            fle = MADE_CHAN_LOC + os.path.split(setting1)[1]
        else:
            fle = self.makeTypePlaylist(chtype, setting1, setting2)

        if len(fle) == 0:
            self.log(
                "Unable to locate the playlist for channel " + str(channel),
                xbmc.LOGERROR,
            )
            return False

        try:
            xml = FileAccess.open(fle, "r")
        except:
            self.log(
                "makeChannelList Unable to open the smart playlist " + fle,
                xbmc.LOGERROR,
            )
            return False

        try:
            dom = parse(xml)
        except:
            self.log("makeChannelList Problem parsing playlist " + fle, xbmc.LOGERROR)
            xml.close()
            return False

        xml.close()

        if self.getSmartPlaylistType(dom) == "mixed":
            fileList = self.buildMixedFileList(dom, channel)
        else:
            fileList = self.buildFileList(fle, channel)

            # Apply smart distribution for TV Genre channels only
            if chtype == 3:  # TV Genre channel
                use_smart_dist = True
                try:
                    use_smart_dist = (
                        ADDON_SETTINGS.getSetting(
                            "Channel_" + str(channel) + "_smartdist"
                        )
                        != "false"
                    )
                except:
                    use_smart_dist = True

                if use_smart_dist and len(fileList) > 0:
                    limit = min(len(fileList), 16384)
                    fileList = self.applySmartDistribution(fileList, limit, channel)
                    self.log("Applied smart distribution to channel %d" % channel)

        try:
            order = dom.getElementsByTagName("order")

            if order[0].childNodes[0].nodeValue.lower() == "random":
                israndom = True
        except:
            pass

        try:
            if append == True:
                channelplaylist = FileAccess.open(
                    CHANNELS_LOC + "channel_" + str(channel) + ".m3u", "r"
                )
                channelplaylist.seek(0, 2)
                channelplaylist.close()
            else:
                channelplaylist = FileAccess.open(
                    CHANNELS_LOC + "channel_" + str(channel) + ".m3u", "w"
                )
        except:
            self.log(
                "Unable to open the cache file "
                + CHANNELS_LOC
                + "channel_"
                + str(channel)
                + ".m3u",
                xbmc.LOGERROR,
            )
            return False

        if append == False:
            channelplaylist.write(uni("#EXTM3U\n"))

        # Only randomize if not using smart distribution
        if israndom and chtype != 3:
            random.shuffle(fileList)

        if len(fileList) > 16384:
            fileList = fileList[:16384]

        fileList = self.runActions(RULES_ACTION_LIST, channel, fileList)
        self.channels[channel - 1].isRandom = israndom

        if append:
            if len(fileList) + self.channels[channel - 1].Playlist.size() > 16384:
                fileList = fileList[
                    : (16384 - self.channels[channel - 1].Playlist.size())
                ]
        else:
            if len(fileList) > 16384:
                fileList = fileList[:16384]

        # Write each entry into the new playlist
        for string in fileList:
            channelplaylist.write(uni("#EXTINF:") + uni(string) + uni("\n"))

        channelplaylist.close()
        self.log("makeChannelList return")
        return True

    def makeTypePlaylist(self, chtype, setting1, setting2):
        if chtype == 3:
            if len(self.showGenreList) == 0:
                self.fillTVInfo()
            return self.createGenrePlaylist("episodes", chtype, setting1)
        elif chtype == 4:
            if len(self.movieGenreList) == 0:
                self.fillMovieInfo()
            return self.createGenrePlaylist("movies", chtype, setting1)
        elif chtype == 12:
            if len(self.musicGenreList) == 0:
                self.fillMusicInfo()
            return self.createGenrePlaylist("songs", chtype, setting1)

        self.log("makeTypePlaylists invalid channel type: " + str(chtype))
        return ""

    def createGenrePlaylist(self, pltype, chtype, genre):
        flename = xbmc.makeLegalFilename(GEN_CHAN_LOC + pltype + "_" + genre + ".xsp")

        try:
            fle = FileAccess.open(flename, "w")
        except:
            self.Error(LANGUAGE(30034) + " " + flename, xbmc.LOGERROR)
            return ""

        self.writeXSPHeader(fle, pltype, self.getChannelName(chtype, genre))
        genre = self.cleanString(genre)
        fle.write('    <rule field="genre" operator="is">\n')
        fle.write("        <value>" + genre + "</value>\n")
        fle.write("    </rule>\n")
        self.writeXSPFooter(fle, 0, "random")
        fle.close()
        return flename

    def writeXSPHeader(self, fle, pltype, plname):
        fle.write('<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>\n')
        fle.write('<smartplaylist type="' + pltype + '">\n')
        plname = self.cleanString(plname)
        fle.write("    <name>" + plname + "</name>\n")
        fle.write("    <match>one</match>\n")

    def writeXSPFooter(self, fle, limit, order):
        if self.mediaLimit > 0:
            fle.write("    <limit>" + str(self.mediaLimit) + "</limit>\n")

        fle.write('    <order direction="ascending">' + order + "</order>\n")
        fle.write("</smartplaylist>\n")

    def cleanString(self, string):
        newstr = uni(string)
        newstr = newstr.replace("&", "&amp;")
        newstr = newstr.replace(">", "&gt;")
        newstr = newstr.replace("<", "&lt;")
        return uni(newstr)

    def fillTVInfo(self, sortbycount=False):
        self.log("fillTVInfo")
        json_query = '{"jsonrpc": "2.0", "method": "VideoLibrary.GetTVShows", "params": {"properties":["studio", "genre"]}, "id": 1}'

        if self.background == False:
            self.updateDialog.update(
                self.updateDialogProgress,
                "Updating channel " + str(self.settingChannel),
                "adding videos",
                "reading TV data",
            )

        json_folder_detail = self.sendJSON(json_query)
        detail = re.compile("{(.*?)}", re.DOTALL).findall(json_folder_detail)

        for f in detail:
            if self.threadPause() == False:
                del self.showGenreList[:]
                return

            match = re.search('"genre" *: *\[(.*?)\]', f)

            if match:
                genres = match.group(1).split(",")

                for genre in genres:
                    found = False
                    curgenre = genre.lower().strip('"').strip()

                    for g in range(len(self.showGenreList)):
                        if self.threadPause() == False:
                            del self.showGenreList[:]
                            return

                        itm = self.showGenreList[g]

                        if sortbycount:
                            itm = itm[0]

                        if curgenre == itm.lower():
                            found = True

                            if sortbycount:
                                self.showGenreList[g][1] += 1

                            break

                    if found == False:
                        if sortbycount:
                            self.showGenreList.append([genre.strip('"').strip(), 1])
                        else:
                            self.showGenreList.append(genre.strip('"').strip())

        if sortbycount:
            self.showGenreList.sort(key=lambda x: x[1], reverse=True)
        else:
            self.showGenreList.sort(key=lambda x: x.lower())

        if len(self.showGenreList) == 0:
            self.log(json_folder_detail)

        self.log("found genres " + str(self.showGenreList))

    def fillMovieInfo(self, sortbycount=False):
        self.log("fillMovieInfo")
        json_query = '{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": {"properties":["studio", "genre"]}, "id": 1}'

        if self.background == False:
            self.updateDialog.update(
                self.updateDialogProgress,
                "Updating channel " + str(self.settingChannel),
                "adding videos",
                "reading movie data",
            )

        json_folder_detail = self.sendJSON(json_query)
        detail = re.compile("{(.*?)}", re.DOTALL).findall(json_folder_detail)

        for f in detail:
            if self.threadPause() == False:
                del self.movieGenreList[:]
                break

            match = re.search('"genre" *: *\[(.*?)\]', f)

            if match:
                genres = match.group(1).split(",")

                for genre in genres:
                    found = False
                    curgenre = genre.lower().strip('"').strip()

                    for g in range(len(self.movieGenreList)):
                        itm = self.movieGenreList[g]

                        if sortbycount:
                            itm = itm[0]

                        if curgenre == itm.lower():
                            found = True

                            if sortbycount:
                                self.movieGenreList[g][1] += 1

                            break

                    if found == False:
                        if sortbycount:
                            self.movieGenreList.append([genre.strip('"').strip(), 1])
                        else:
                            self.movieGenreList.append(genre.strip('"').strip())

        if sortbycount:
            self.movieGenreList.sort(key=lambda x: x[1], reverse=True)
        else:
            self.movieGenreList.sort(key=lambda x: x.lower())

        if len(self.movieGenreList) == 0:
            self.log(json_folder_detail)

        self.log("found genres " + str(self.movieGenreList))

    def fillMusicInfo(self, sortbycount=False):
        self.log("fillMusicInfo")
        self.musicGenreList = []
        json_query = '{"jsonrpc": "2.0", "method": "AudioLibrary.GetAlbums", "params": {"properties":["genre"]}, "id": 1}'

        if self.background == False:
            self.updateDialog.update(
                self.updateDialogProgress,
                "Updating channel " + str(self.settingChannel),
                "adding music",
                "reading music data",
            )

        json_folder_detail = self.sendJSON(json_query)
        self.log("fillMusicInfo response length: " + str(len(json_folder_detail)))

        # Log first 500 chars of response to see what we're getting
        self.log("fillMusicInfo response preview: " + json_folder_detail[:500])

        # Parse the response
        detail = re.compile("{(.*?)}", re.DOTALL).findall(json_folder_detail)

        for f in detail:
            if self.threadPause() == False:
                del self.musicGenreList[:]
                return

            match = re.search('"genre" *: *\[(.*?)\]', f)

            if match:
                genres = match.group(1).split(",")

                for genre in genres:
                    found = False
                    curgenre = genre.lower().strip('"').strip()

                    for g in range(len(self.musicGenreList)):
                        if self.threadPause() == False:
                            del self.musicGenreList[:]
                            return

                        itm = self.musicGenreList[g]
                        if sortbycount:
                            itm = itm[0]

                        if curgenre == itm.lower():
                            found = True
                            if sortbycount:
                                self.musicGenreList[g][1] += 1
                            break

                    if found == False:
                        if sortbycount:
                            self.musicGenreList.append([genre.strip('"').strip(), 1])
                        else:
                            self.musicGenreList.append(genre.strip('"').strip())

        # Sort the genre list
        if sortbycount:
            self.musicGenreList.sort(key=lambda x: x[1], reverse=True)
        else:
            self.musicGenreList.sort(key=lambda x: x.lower())

        # Log the final list
        self.log("fillMusicInfo final list: " + str(self.musicGenreList))

    def makeMixedList(self, list1, list2):
        self.log("makeMixedList")
        newlist = []

        for item in list1:
            curitem = item.lower()

            for a in list2:
                if curitem == a.lower():
                    newlist.append(item)
                    break

        self.log("makeMixedList return " + str(newlist))
        return newlist

    def buildFileList(self, dir_name, channel):
        self.log("buildFileList")
        fileList = []
        seasoneplist = []
        filecount = 0

        # Determine media type based on channel type
        media_type = "video"
        if self.channels[channel - 1].isValid:
            chtype = int(ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_type"))
            if chtype == 12:  # Music genre
                media_type = "music"

        json_query = (
            '{"jsonrpc": "2.0", "method": "Files.GetDirectory", "params": {"directory": "%s", "media": "%s", "properties":["season","episode","playcount","duration","runtime","showtitle","album","artist","plot","track"]}, "id": 1}'
            % (self.escapeDirJSON(dir_name), media_type)
        )

        if self.background == False:
            self.updateDialog.update(
                self.updateDialogProgress,
                "Updating channel " + str(self.settingChannel),
                "adding items",
                "querying database",
            )

        json_folder_detail = self.sendJSON(json_query)
        file_detail = re.compile("{(.*?)}", re.DOTALL).findall(json_folder_detail)

        for f in file_detail:
            if self.threadPause() == False:
                del fileList[:]
                break

            f = uni(f)
            match = re.search('"file" *: *"(.*?)",', f)
            istvshow = False

            if match:
                if match.group(1).endswith("/") or match.group(1).endswith("\\"):
                    fileList.extend(self.buildFileList(match.group(1), channel))
                else:
                    f = self.runActions(RULES_ACTION_JSON, channel, f)
                    duration = re.search('"duration" *: *([0-9]*?),', f)

                    try:
                        dur = int(duration.group(1))
                    except:
                        dur = 0

                    if dur == 0:
                        duration = re.search('"runtime" *: *([0-9]*?),', f)
                        try:
                            dur = int(duration.group(1))
                        except:
                            dur = 0

                    if dur == 0:
                        try:
                            dur = self.videoParser.getVideoLength(
                                uni(match.group(1)).replace("\\\\", "\\")
                            )
                        except:
                            dur = 0

                    try:
                        if dur > 0:
                            filecount += 1
                            seasonval = -1
                            epval = -1

                            if self.background == False:
                                if filecount == 1:
                                    self.updateDialog.update(
                                        self.updateDialogProgress,
                                        "Updating channel " + str(self.settingChannel),
                                        "adding items",
                                        "added " + str(filecount) + " entry",
                                    )
                                else:
                                    self.updateDialog.update(
                                        self.updateDialogProgress,
                                        "Updating channel " + str(self.settingChannel),
                                        "adding items",
                                        "added " + str(filecount) + " entries",
                                    )

                            title = re.search('"label" *: *"(.*?)"', f)
                            tmpstr = str(dur) + ","

                            # Check if this is music content
                            album = re.search('"album" *: *"(.*?)"', f)
                            artist = re.search('"artist" *: *"(.*?)"', f)

                            if artist and album and artist.group(1) and album.group(1):
                                # This is a music file
                                track = re.search('"track" *: *(.*?),', f)
                                tracknum = ""
                                try:
                                    tracknum = str(int(track.group(1))) + ". "
                                except:
                                    pass

                                tmpstr += (
                                    artist.group(1)
                                    + "//"
                                    + tracknum
                                    + title.group(1)
                                    + "//"
                                    + album.group(1)
                                )
                            else:
                                # Video content handling (unchanged)
                                showtitle = re.search('"showtitle" *: *"(.*?)"', f)
                                plot = re.search('"plot" *: *"(.*?)",', f)

                                if plot == None:
                                    theplot = ""
                                else:
                                    theplot = plot.group(1)

                                # This is a TV show
                                if showtitle != None and len(showtitle.group(1)) > 0:
                                    season = re.search('"season" *: *(.*?),', f)
                                    episode = re.search('"episode" *: *(.*?),', f)
                                    swtitle = title.group(1)

                                    try:
                                        seasonval = int(season.group(1))
                                        epval = int(episode.group(1))

                                        if self.showSeasonEpisode:
                                            swtitle = (
                                                swtitle
                                                + " (S"
                                                + ("0" if seasonval < 10 else "")
                                                + str(seasonval)
                                                + "E"
                                                + ("0" if epval < 10 else "")
                                                + str(epval)
                                                + ")"
                                            )
                                    except:
                                        seasonval = -1
                                        epval = -1

                                    tmpstr += (
                                        showtitle.group(1)
                                        + "//"
                                        + swtitle
                                        + "//"
                                        + theplot
                                    )
                                    istvshow = True
                                else:
                                    tmpstr += title.group(1) + "//" + "//" + theplot

                            tmpstr = tmpstr[:2036]
                            tmpstr = (
                                tmpstr.replace("\\n", " ")
                                .replace("\\r", " ")
                                .replace('\\"', '"')
                            )
                            tmpstr = (
                                tmpstr + "\n" + match.group(1).replace("\\\\", "\\")
                            )

                            if self.channels[channel - 1].mode & MODE_ORDERAIRDATE > 0:
                                seasoneplist.append([seasonval, epval, tmpstr])
                            else:
                                fileList.append(tmpstr)
                    except:
                        pass
            else:
                continue

        if self.channels[channel - 1].mode & MODE_ORDERAIRDATE > 0:
            seasoneplist.sort(key=lambda seep: seep[1])
            seasoneplist.sort(key=lambda seep: seep[0])

            for seepitem in seasoneplist:
                fileList.append(seepitem[2])

        if filecount == 0:
            self.log(json_folder_detail)

        self.log("buildFileList return")
        return fileList

    def buildMixedFileList(self, dom1, channel):
        fileList = []
        self.log("buildMixedFileList")

        try:
            rules = dom1.getElementsByTagName("rule")
            order = dom1.getElementsByTagName("order")
        except:
            self.log("buildMixedFileList Problem parsing playlist", xbmc.LOGERROR)
            return fileList

        for rule in rules:
            rulename = rule.childNodes[0].nodeValue

            if FileAccess.exists(
                xbmc.translatePath("special://profile/playlists/video/") + rulename
            ):
                FileAccess.copy(
                    xbmc.translatePath("special://profile/playlists/video/") + rulename,
                    MADE_CHAN_LOC + rulename,
                )
                fileList.extend(self.buildFileList(MADE_CHAN_LOC + rulename, channel))
            else:
                fileList.extend(self.buildFileList(GEN_CHAN_LOC + rulename, channel))

        self.log("buildMixedFileList returning")
        return fileList

    # Run rules for a channel
    def runActions(self, action, channel, parameter):
        self.log("runActions " + str(action) + " on channel " + str(channel))
        if channel < 1:
            return parameter

        self.runningActionChannel = channel
        index = 0

        for rule in self.channels[channel - 1].ruleList:
            if rule.actions & action > 0:
                self.runningActionId = index

                if self.background == False:
                    self.updateDialog.update(
                        self.updateDialogProgress,
                        "Updating channel " + str(self.settingChannel),
                        "processing rule " + str(index + 1),
                        "",
                    )

                parameter = rule.runAction(action, self, parameter)

            index += 1

        self.runningActionChannel = 0
        self.runningActionId = 0
        return parameter

    def threadPause(self):
        if threading.activeCount() > 1:
            while self.threadPaused == True and self.myOverlay.isExiting == False:
                time.sleep(self.sleepTime)

            # This will fail when using config.py
            try:
                if self.myOverlay.isExiting == True:
                    self.log("IsExiting")
                    return False
            except:
                pass

        return True

    def escapeDirJSON(self, dir_name):
        mydir = uni(dir_name)

        if mydir.find(":"):
            mydir = mydir.replace("\\", "\\\\")

        return mydir

    def getSmartPlaylistType(self, dom):
        self.log("getSmartPlaylistType")

        try:
            pltype = dom.getElementsByTagName("smartplaylist")
            return pltype[0].attributes["type"].value
        except:
            self.log("Unable to get the playlist type.", xbmc.LOGERROR)
            return ""

    def clearAllPlaylists(self):
        self.log("clearAllPlaylists")
        for i in range(999):
            try:
                FileAccess.delete(CHANNELS_LOC + "channel_" + str(i + 1) + ".m3u")
            except:
                pass

    def Error(self, msg, severity=xbmc.LOGWARNING):
        self.log(msg, severity)
        xbmc.executebuiltin("Notification(Paragon TV," + msg + ", 3000)")
        return
