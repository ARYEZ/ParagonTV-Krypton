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

import datetime
import os
import subprocess
import threading
import time
import traceback
import xml.etree.ElementTree as ET

import xbmc
import xbmcaddon
import xbmcgui
from Channel import Channel
from FileAccess import FileAccess
from Globals import *
from Playlist import Playlist

ADDON_SETTINGS = xbmcaddon.Addon(id="script.paragontv")


class EPGWindow(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        self.focusRow = 0
        self.focusIndex = 0
        self.focusTime = 0
        self.focusEndTime = 0
        self.shownTime = 0
        self.centerChannel = 0
        self.rowCount = 5
        self.channelButtons = [None] * self.rowCount
        self.buttonCache = []
        self.actionSemaphore = threading.BoundedSemaphore()
        self.lastActionTime = time.time()
        self.channelLogos = ""
        self.textcolor = "FFFFFFFF"
        self.shadowcolor = "00000000"
        self.focusedcolor = "FF7d7d7d"
        self.clockMode = 0
        self.textfont = "fontsize_22"

        # Artwork caching
        self.artworkCache = {}  # Format: {(channel, position): artwork_path}
        self.maxCacheSize = 100  # Maximum number of cached artwork paths

        # Set media path.
        if os.path.exists(
            xbmc.translatePath(
                os.path.join(CWD, "resources", "skins", xbmc.getSkinDir(), "media")
            )
        ):
            self.mediaPath = xbmc.translatePath(
                os.path.join(
                    CWD, "resources", "skins", xbmc.getSkinDir(), "media" + "/"
                )
            )
        else:
            self.mediaPath = xbmc.translatePath(
                os.path.join(CWD, "resources", "skins", "default", "media" + "/")
            )

        self.log("Media Path is " + self.mediaPath)

        # Use the given focus and non-focus textures if they exist.  Otherwise use the defaults.
        if xbmc.skinHasImage(self.mediaPath + BUTTON_FOCUS):
            self.textureButtonFocus = self.mediaPath + BUTTON_FOCUS
        else:
            self.textureButtonFocus = "button-focus.png"

        if xbmc.skinHasImage(self.mediaPath + BUTTON_NO_FOCUS):
            self.textureButtonNoFocus = self.mediaPath + BUTTON_NO_FOCUS
        else:
            self.textureButtonNoFocus = "button-nofocus.png"

        for i in range(self.rowCount):
            self.channelButtons[i] = []

        self.clockMode = ADDON_SETTINGS.getSetting("ClockMode")
        self.toRemove = []

    def onFocus(self, controlid):
        pass

    # set the time labels
    def setTimeLabels(self, thetime):
        self.log("setTimeLabels")
        now = datetime.datetime.fromtimestamp(thetime)
        self.getControl(104).setLabel(
            now.strftime("%A, %d %B %Y").lstrip("0").replace(" 0", " ")
        )
        delta = datetime.timedelta(minutes=30)

        for i in range(3):
            if self.clockMode == "0":
                self.getControl(101 + i).setLabel(
                    now.strftime("%I:%M %p").lstrip("0").replace(" 0", " ")
                )
            else:
                self.getControl(101 + i).setLabel(now.strftime("%H:%M"))

            now = now + delta

        self.log("setTimeLabels return")

    def log(self, msg, level=xbmc.LOGDEBUG):
        log("EPGWindow: " + msg, level)

    def onInit(self):
        self.log("onInit")
        timex, timey = self.getControl(120).getPosition()
        timew = self.getControl(120).getWidth()
        timeh = self.getControl(120).getHeight()
        self.currentTimeBar = xbmcgui.ControlImage(
            timex, timey, timew, timeh, self.mediaPath + TIME_BAR
        )

        self.addControl(self.currentTimeBar)

        try:
            textcolor = int(self.getControl(100).getLabel(), 16)
            focusedcolor = int(self.getControl(100).getLabel2(), 16)
            self.textfont = self.getControl(105).getLabel()

            if textcolor > 0:
                self.textcolor = hex(textcolor)[2:]

            if focusedcolor > 0:
                self.focusedcolor = hex(focusedcolor)[2:]
        except:
            pass

        try:
            if (
                self.setChannelButtons(time.time(), self.MyOverlayWindow.currentChannel)
                == False
            ):
                self.log("Unable to add channel buttons")
                return

            curtime = time.time()
            self.focusIndex = -1
            basex, basey = self.getControl(113).getPosition()
            baseh = self.getControl(113).getHeight()
            basew = self.getControl(113).getWidth()

            # set the button that corresponds to the currently playing show
            for i in range(len(self.channelButtons[2])):
                left, top = self.channelButtons[2][i].getPosition()
                width = self.channelButtons[2][i].getWidth()
                left = left - basex
                starttime = self.shownTime + (left / (basew / 5400.0))
                endtime = starttime + (width / (basew / 5400.0))

                if curtime >= starttime and curtime <= endtime:
                    self.focusIndex = i
                    self.setFocus(self.channelButtons[2][i])
                    self.focusTime = int(time.time())
                    self.focusEndTime = endtime
                    break

            # If nothing was highlighted, just select the first button
            if self.focusIndex == -1:
                self.focusIndex = 0
                self.setFocus(self.channelButtons[2][0])
                left, top = self.channelButtons[2][0].getPosition()
                width = self.channelButtons[2][0].getWidth()
                left = left - basex
                starttime = self.shownTime + (left / (basew / 5400.0))
                endtime = starttime + (width / (basew / 5400.0))
                self.focusTime = int(starttime + 30)
                self.focusEndTime = endtime

            self.focusRow = 2
            self.setShowInfo()
        except:
            self.log("Unknown EPG Initialization Exception", xbmc.LOGERROR)
            self.log(traceback.format_exc(), xbmc.LOGERROR)

            try:
                self.close()
            except:
                self.log("Error closing", xbmc.LOGERROR)

            self.MyOverlayWindow.sleepTimeValue = 1
            self.MyOverlayWindow.startSleepTimer()
            return

        self.log("onInit return")

    # setup all channel buttons for a given time
    def setChannelButtons(self, starttime, curchannel, singlerow=-1):
        self.log("setChannelButtons " + str(starttime) + ", " + str(curchannel))
        self.centerChannel = self.MyOverlayWindow.fixChannel(curchannel)
        # This is done twice to guarantee we go back 2 channels.  If the previous 2 channels
        # aren't valid, then doing a fix on curchannel - 2 may result in going back only
        # a single valid channel.
        curchannel = self.MyOverlayWindow.fixChannel(curchannel - 1, False)
        curchannel = self.MyOverlayWindow.fixChannel(curchannel - 1, False)
        starttime = self.roundToHalfHour(int(starttime))
        self.setTimeLabels(starttime)
        self.shownTime = starttime
        basex, basey = self.getControl(111).getPosition()
        basew = self.getControl(111).getWidth()
        tmpx, tmpy = self.getControl(110 + self.rowCount).getPosition()
        timex, timey = self.getControl(120).getPosition()
        timew = self.getControl(120).getWidth()
        timeh = self.getControl(120).getHeight()
        basecur = curchannel
        self.toRemove.append(self.currentTimeBar)
        EpgLogo = ADDON.getSetting("ShowEpgLogo")
        myadds = []

        for i in range(self.rowCount):
            if singlerow == -1 or singlerow == i:
                self.setButtons(starttime, basecur, i)
                myadds.extend(self.channelButtons[i])

            basecur = self.MyOverlayWindow.fixChannel(basecur + 1)

        basecur = curchannel

        for i in range(self.rowCount):
            self.getControl(301 + i).setLabel(
                self.MyOverlayWindow.channels[basecur - 1].name
            )
            basecur = self.MyOverlayWindow.fixChannel(basecur + 1)

        for i in range(self.rowCount):
            try:
                self.getControl(311 + i).setLabel(str(curchannel))
            except:
                pass

            try:
                if EpgLogo == "true":
                    self.getControl(321 + i).setImage(
                        self.channelLogos
                        + ascii(self.MyOverlayWindow.channels[curchannel - 1].name)
                        + "_c.png"
                    )
                    if not FileAccess.exists(
                        self.channelLogos
                        + ascii(self.MyOverlayWindow.channels[curchannel - 1].name)
                        + "_c.png"
                    ):
                        self.getControl(321 + i).setImage(IMAGES_LOC + "Default.png")
            except:
                pass

            curchannel = self.MyOverlayWindow.fixChannel(curchannel + 1)

        if time.time() >= starttime and time.time() < starttime + 5400:
            dif = int((starttime + 5400 - time.time()))
            self.currentTimeBar.setPosition(
                int((basex + basew - (timew / 2)) - (dif * (basew / 5400.0))), timey
            )
        else:
            if time.time() < starttime:
                self.currentTimeBar.setPosition(basex, timey)
            else:
                self.currentTimeBar.setPosition(basex + basew - timew, timey)

        myadds.append(self.currentTimeBar)

        try:
            self.removeControls(self.toRemove)
        except:
            for cntrl in self.toRemove:
                try:
                    self.removeControl(cntrl)
                except:
                    pass

        self.addControls(myadds)
        self.toRemove = []

        # Clean up old cache entries when changing time/channels
        self.cleanupArtworkCache()

        self.log("setChannelButtons return")

    def cleanupArtworkCache(self):
        """Remove old entries from artwork cache to prevent memory growth"""
        if len(self.artworkCache) > self.maxCacheSize:
            # Remove oldest entries (simple FIFO approach)
            # In a more sophisticated implementation, you might use LRU
            items_to_remove = len(self.artworkCache) - self.maxCacheSize
            for key in list(self.artworkCache.keys())[:items_to_remove]:
                del self.artworkCache[key]
            self.log(
                "Cleaned up artwork cache, removed " + str(items_to_remove) + " entries"
            )

    # round the given time down to the nearest half hour
    def roundToHalfHour(self, thetime):
        n = datetime.datetime.fromtimestamp(thetime)
        delta = datetime.timedelta(minutes=30)

        if n.minute > 29:
            n = n.replace(minute=30, second=0, microsecond=0)
        else:
            n = n.replace(minute=0, second=0, microsecond=0)

        return time.mktime(n.timetuple())

    # create the buttons for the specified channel in the given row
    def setButtons(self, starttime, curchannel, row):
        self.log(
            "setButtons " + str(starttime) + ", " + str(curchannel) + ", " + str(row)
        )

        try:
            curchannel = self.MyOverlayWindow.fixChannel(curchannel)
            basex, basey = self.getControl(111 + row).getPosition()
            baseh = self.getControl(111 + row).getHeight()
            basew = self.getControl(111 + row).getWidth()

            if xbmc.Player().isPlaying() == False:
                self.log("No video is playing, not adding buttons")
                self.closeEPG()
                return False

            # Backup all of the buttons to an array
            self.toRemove.extend(self.channelButtons[row])
            del self.channelButtons[row][:]

            # if the channel is paused, then only 1 button needed
            if self.MyOverlayWindow.channels[curchannel - 1].isPaused:
                self.channelButtons[row].append(
                    xbmcgui.ControlButton(
                        basex,
                        basey,
                        basew,
                        baseh,
                        self.MyOverlayWindow.channels[curchannel - 1].getCurrentTitle()
                        + " (paused)",
                        focusTexture=self.textureButtonFocus,
                        noFocusTexture=self.textureButtonNoFocus,
                        alignment=4,
                        font=self.textfont,
                        textColor=self.textcolor,
                        shadowColor="0xAA000000",
                        focusedColor=self.focusedcolor,
                    )
                )
            else:
                # Find the show that was running at the given time
                # Use the current time and show offset to calculate it
                # At timedif time, channelShowPosition was playing at channelTimes
                # The only way this isn't true is if the current channel is curchannel since
                # it could have been fast forwarded or rewinded (rewound)?
                if curchannel == self.MyOverlayWindow.currentChannel:
                    playlistpos = int(xbmc.PlayList(xbmc.PLAYLIST_VIDEO).getposition())
                    videotime = xbmc.Player().getTime()
                    reftime = time.time()
                else:
                    playlistpos = self.MyOverlayWindow.channels[
                        curchannel - 1
                    ].playlistPosition
                    videotime = self.MyOverlayWindow.channels[
                        curchannel - 1
                    ].showTimeOffset
                    reftime = self.MyOverlayWindow.channels[
                        curchannel - 1
                    ].lastAccessTime

                # normalize reftime to the beginning of the video
                reftime -= videotime

                while reftime > starttime:
                    playlistpos -= 1
                    # No need to check bounds on the playlistpos, the duration function makes sure it is correct
                    reftime -= self.MyOverlayWindow.channels[
                        curchannel - 1
                    ].getItemDuration(playlistpos)

                while (
                    reftime
                    + self.MyOverlayWindow.channels[curchannel - 1].getItemDuration(
                        playlistpos
                    )
                    < starttime
                ):
                    reftime += self.MyOverlayWindow.channels[
                        curchannel - 1
                    ].getItemDuration(playlistpos)
                    playlistpos += 1

                # create a button for each show that runs in the next hour and a half
                endtime = starttime + 5400
                totaltime = 0
                totalloops = 0

                while reftime < endtime and totalloops < 1000:
                    xpos = int(basex + (totaltime * (basew / 5400.0)))
                    tmpdur = self.MyOverlayWindow.channels[
                        curchannel - 1
                    ].getItemDuration(playlistpos)
                    shouldskip = False

                    # this should only happen the first time through this loop
                    # it shows the small portion of the show before the current one
                    if reftime < starttime:
                        tmpdur -= starttime - reftime
                        reftime = starttime

                        if tmpdur < 60 * 3:
                            shouldskip = True

                    # Don't show very short videos
                    if self.MyOverlayWindow.hideShortItems and shouldskip == False:
                        if (
                            self.MyOverlayWindow.channels[
                                curchannel - 1
                            ].getItemDuration(playlistpos)
                            < self.MyOverlayWindow.shortItemLength
                        ):
                            shouldskip = True
                            tmpdur = 0
                        else:
                            nextlen = self.MyOverlayWindow.channels[
                                curchannel - 1
                            ].getItemDuration(playlistpos + 1)
                            prevlen = self.MyOverlayWindow.channels[
                                curchannel - 1
                            ].getItemDuration(playlistpos - 1)

                            if nextlen < 60:
                                tmpdur += nextlen / 2

                            if prevlen < 60:
                                tmpdur += prevlen / 2

                    width = int((basew / 5400.0) * tmpdur)

                    if width < 30 and shouldskip == False:
                        width = 30
                        tmpdur = int(30.0 / (basew / 5400.0))

                    if width + xpos > basex + basew:
                        width = basex + basew - xpos

                    if shouldskip == False and width >= 30:
                        mylabel = self.MyOverlayWindow.channels[
                            curchannel - 1
                        ].getItemTitle(playlistpos)

                        # Check if this is a music channel and format the label accordingly
                        channelName = self.MyOverlayWindow.channels[curchannel - 1].name
                        if channelName:
                            channelLower = channelName.lower()

                            # Keywords that indicate video content, not audio music
                            videoExcludeKeywords = [
                                "documentary",
                                "performance",
                                "concert",
                                "tv",
                                "video",
                                "visual",
                                "show",
                                "series",
                                "movie",
                                "movies",
                                "film",
                                "films",
                                "cinema",
                            ]

                            # Skip if any exclude keywords are found
                            hasVideoKeyword = any(
                                keyword in channelLower
                                for keyword in videoExcludeKeywords
                            )

                            isMusicChannel = False
                            if not hasVideoKeyword:
                                musicKeywords = [
                                    "music",
                                    "radio",
                                    "genre",
                                    "eighties",
                                    "nineties",
                                    "seventies",
                                    "rock",
                                    "pop",
                                    "jazz",
                                    "blues",
                                    "metal",
                                    "country",
                                    "classical",
                                    "dance",
                                    "electronic",
                                    "hip hop",
                                    "r&b",
                                    "soul",
                                    "disco",
                                ]

                                isMusicChannel = any(
                                    keyword in channelLower for keyword in musicKeywords
                                )

                            # Also check channel type (12 = music genre)
                            try:
                                chtype = int(
                                    ADDON_SETTINGS.getSetting(
                                        "Channel_" + str(curchannel) + "_type"
                                    )
                                )
                                if chtype == 12 and not hasVideoKeyword:
                                    isMusicChannel = True
                            except:
                                pass

                            if isMusicChannel and " - " in mylabel:
                                # For music files, show only the song title in the EPG grid
                                parts = mylabel.split(" - ")
                                if len(parts) >= 2:
                                    mylabel = parts[
                                        1
                                    ].strip()  # Just show the song title

                        self.channelButtons[row].append(
                            xbmcgui.ControlButton(
                                xpos,
                                basey,
                                width,
                                baseh,
                                mylabel,
                                focusTexture=self.textureButtonFocus,
                                noFocusTexture=self.textureButtonNoFocus,
                                alignment=4,
                                font=self.textfont,
                                shadowColor="0xAA000000",
                                textColor=self.textcolor,
                                focusedColor=self.focusedcolor,
                            )
                        )

                    totaltime += tmpdur
                    reftime += tmpdur
                    playlistpos += 1
                    totalloops += 1

                if totalloops >= 1000:
                    self.log(
                        "Broken big loop, too many loops, reftime is "
                        + str(reftime)
                        + ", endtime is "
                        + str(endtime)
                    )

                # If there were no buttons added, show some default button
                if len(self.channelButtons[row]) == 0:
                    self.channelButtons[row].append(
                        xbmcgui.ControlButton(
                            basex,
                            basey,
                            basew,
                            baseh,
                            self.MyOverlayWindow.channels[curchannel - 1].name,
                            focusTexture=self.textureButtonFocus,
                            noFocusTexture=self.textureButtonNoFocus,
                            alignment=4,
                            font=self.textfont,
                            textColor=self.textcolor,
                            shadowColor="0xFF000000",
                            focusedColor=self.focusedcolor,
                        )
                    )
        except:
            self.log("Exception in setButtons", xbmc.LOGERROR)
            self.log(traceback.format_exc(), xbmc.LOGERROR)

        self.log("setButtons return")
        return True

    def onAction(self, act):
        self.log("onAction " + str(act.getId()))

        if self.actionSemaphore.acquire(False) == False:
            self.log("Unable to get semaphore")
            return

        action = act.getId()

        try:
            if action in ACTION_PREVIOUS_MENU:
                self.closeEPG()
            elif action == ACTION_MOVE_DOWN:
                self.GoDown()
            elif action == ACTION_MOVE_UP:
                self.GoUp()
            elif action == ACTION_MOVE_LEFT:
                self.GoLeft()
            elif action == ACTION_MOVE_RIGHT:
                self.GoRight()
            elif action == ACTION_STOP:
                self.closeEPG()
            elif action == ACTION_SELECT_ITEM:
                lastaction = time.time() - self.lastActionTime

                if lastaction >= 2:
                    self.selectShow()
                    self.closeEPG()
                    self.lastActionTime = time.time()
        except:
            self.log("Unknown EPG Exception", xbmc.LOGERROR)
            self.log(traceback.format_exc(), xbmc.LOGERROR)

            try:
                self.close()
            except:
                self.log("Error closing", xbmc.LOGERROR)

            self.MyOverlayWindow.sleepTimeValue = 1
            self.MyOverlayWindow.startSleepTimer()
            return

        self.actionSemaphore.release()
        self.log("onAction return")

    def closeEPG(self):
        self.log("closeEPG")

        try:
            self.removeControl(self.currentTimeBar)
            self.MyOverlayWindow.startSleepTimer()
        except:
            pass

        self.close()

    def onControl(self, control):
        self.log("onControl")

    # Run when a show is selected, so close the epg and run the show
    def onClick(self, controlid):
        self.log("onClick")

        if self.actionSemaphore.acquire(False) == False:
            self.log("Unable to get semaphore")
            return

        lastaction = time.time() - self.lastActionTime

        if lastaction >= 2:
            try:
                selectedbutton = self.getControl(controlid)
            except:
                self.actionSemaphore.release()
                self.log("onClick unknown controlid " + str(controlid))
                return

            for i in range(self.rowCount):
                for x in range(len(self.channelButtons[i])):
                    mycontrol = 0
                    mycontrol = self.channelButtons[i][x]

                    if selectedbutton == mycontrol:
                        self.focusRow = i
                        self.focusIndex = x
                        self.selectShow()
                        self.closeEPG()
                        self.lastActionTime = time.time()
                        self.actionSemaphore.release()
                        self.log("onClick found button return")
                        return

            self.lastActionTime = time.time()
            self.closeEPG()

        self.actionSemaphore.release()
        self.log("onClick return")

    def GoDown(self):
        self.log("goDown")

        # change controls to display the proper junks
        if self.focusRow == self.rowCount - 1:
            self.setChannelButtons(
                self.shownTime, self.MyOverlayWindow.fixChannel(self.centerChannel + 1)
            )
            self.focusRow = self.rowCount - 2

        self.setProperButton(self.focusRow + 1)
        self.log("goDown return")

    def GoUp(self):
        self.log("goUp")

        # same as godown
        # change controls to display the proper junks
        if self.focusRow == 0:
            self.setChannelButtons(
                self.shownTime,
                self.MyOverlayWindow.fixChannel(self.centerChannel - 1, False),
            )
            self.focusRow = 1

        self.setProperButton(self.focusRow - 1)
        self.log("goUp return")

    def GoLeft(self):
        self.log("goLeft")
        basex, basey = self.getControl(111 + self.focusRow).getPosition()
        basew = self.getControl(111 + self.focusRow).getWidth()

        # change controls to display the proper junks
        if self.focusIndex == 0:
            left, top = self.channelButtons[self.focusRow][
                self.focusIndex
            ].getPosition()
            width = self.channelButtons[self.focusRow][self.focusIndex].getWidth()
            left = left - basex
            starttime = self.shownTime + (left / (basew / 5400.0))
            self.setChannelButtons(self.shownTime - 1800, self.centerChannel)
            curbutidx = self.findButtonAtTime(self.focusRow, starttime + 30)

            if (curbutidx - 1) >= 0:
                self.focusIndex = curbutidx - 1
            else:
                self.focusIndex = 0
        else:
            self.focusIndex -= 1

        left, top = self.channelButtons[self.focusRow][self.focusIndex].getPosition()
        width = self.channelButtons[self.focusRow][self.focusIndex].getWidth()
        left = left - basex
        starttime = self.shownTime + (left / (basew / 5400.0))
        endtime = starttime + (width / (basew / 5400.0))
        self.setFocus(self.channelButtons[self.focusRow][self.focusIndex])
        self.setShowInfo()
        self.focusEndTime = endtime
        self.focusTime = starttime + 30
        self.log("goLeft return")

    def GoRight(self):
        self.log("goRight")
        basex, basey = self.getControl(111 + self.focusRow).getPosition()
        basew = self.getControl(111 + self.focusRow).getWidth()

        # change controls to display the proper junks
        if self.focusIndex == len(self.channelButtons[self.focusRow]) - 1:
            left, top = self.channelButtons[self.focusRow][
                self.focusIndex
            ].getPosition()
            width = self.channelButtons[self.focusRow][self.focusIndex].getWidth()
            left = left - basex
            starttime = self.shownTime + (left / (basew / 5400.0))
            self.setChannelButtons(self.shownTime + 1800, self.centerChannel)
            curbutidx = self.findButtonAtTime(self.focusRow, starttime + 30)

            if (curbutidx + 1) < len(self.channelButtons[self.focusRow]):
                self.focusIndex = curbutidx + 1
            else:
                self.focusIndex = len(self.channelButtons[self.focusRow]) - 1
        else:
            self.focusIndex += 1

        left, top = self.channelButtons[self.focusRow][self.focusIndex].getPosition()
        width = self.channelButtons[self.focusRow][self.focusIndex].getWidth()
        left = left - basex
        starttime = self.shownTime + (left / (basew / 5400.0))
        endtime = starttime + (width / (basew / 5400.0))
        self.setFocus(self.channelButtons[self.focusRow][self.focusIndex])
        self.setShowInfo()
        self.focusEndTime = endtime
        self.focusTime = starttime + 30
        self.log("goRight return")

    def findButtonAtTime(self, row, selectedtime):
        self.log("findButtonAtTime " + str(row))
        basex, basey = self.getControl(111 + row).getPosition()
        baseh = self.getControl(111 + row).getHeight()
        basew = self.getControl(111 + row).getWidth()

        for i in range(len(self.channelButtons[row])):
            left, top = self.channelButtons[row][i].getPosition()
            width = self.channelButtons[row][i].getWidth()
            left = left - basex
            starttime = self.shownTime + (left / (basew / 5400.0))
            endtime = starttime + (width / (basew / 5400.0))

            if selectedtime >= starttime and selectedtime <= endtime:
                return i

        return -1

    # based on the current focus row and index, find the appropriate button in
    # the new row to set focus to
    def setProperButton(self, newrow, resetfocustime=False):
        self.log("setProperButton " + str(newrow))
        self.focusRow = newrow
        basex, basey = self.getControl(111 + newrow).getPosition()
        baseh = self.getControl(111 + newrow).getHeight()
        basew = self.getControl(111 + newrow).getWidth()

        for i in range(len(self.channelButtons[newrow])):
            left, top = self.channelButtons[newrow][i].getPosition()
            width = self.channelButtons[newrow][i].getWidth()
            left = left - basex
            starttime = self.shownTime + (left / (basew / 5400.0))
            endtime = starttime + (width / (basew / 5400.0))

            if self.focusTime >= starttime and self.focusTime <= endtime:
                self.focusIndex = i
                self.setFocus(self.channelButtons[newrow][i])
                self.setShowInfo()
                self.focusEndTime = endtime

                if resetfocustime:
                    self.focusTime = starttime + 30

                self.log("setProperButton found button return")
                return

        self.focusIndex = 0
        self.setFocus(self.channelButtons[newrow][0])
        left, top = self.channelButtons[newrow][0].getPosition()
        width = self.channelButtons[newrow][0].getWidth()
        left = left - basex
        starttime = self.shownTime + (left / (basew / 5400.0))
        endtime = starttime + (width / (basew / 5400.0))
        self.focusEndTime = endtime

        if resetfocustime:
            self.focusTime = starttime + 30

        self.setShowInfo()
        self.log("setProperButton return")

    def setShowInfo(self):
        self.log("setShowInfo")
        basex, basey = self.getControl(111 + self.focusRow).getPosition()
        baseh = self.getControl(111 + self.focusRow).getHeight()
        basew = self.getControl(111 + self.focusRow).getWidth()
        # use the selected time to set the video
        left, top = self.channelButtons[self.focusRow][self.focusIndex].getPosition()
        width = self.channelButtons[self.focusRow][self.focusIndex].getWidth()
        left = left - basex + (width / 2)
        starttime = self.shownTime + (left / (basew / 5400.0))
        chnoffset = self.focusRow - 2
        newchan = self.centerChannel

        while chnoffset != 0:
            if chnoffset > 0:
                newchan = self.MyOverlayWindow.fixChannel(newchan + 1, True)
                chnoffset -= 1
            else:
                newchan = self.MyOverlayWindow.fixChannel(newchan - 1, False)
                chnoffset += 1

        plpos = self.determinePlaylistPosAtTime(starttime, newchan)

        if plpos == -1:
            self.log("Unable to find the proper playlist to set from EPG")
            return

        # Get the title
        title = self.MyOverlayWindow.channels[newchan - 1].getItemTitle(plpos)
        self.getControl(500).setLabel(title)

        # Check if this is a music channel
        channelName = self.MyOverlayWindow.channels[newchan - 1].name
        isMusicChannel = False

        if channelName:
            channelLower = channelName.lower()

            # Keywords that indicate video content, not audio music
            videoExcludeKeywords = [
                "documentary",
                "performance",
                "concert",
                "tv",
                "video",
                "visual",
                "show",
                "series",
                "movie",
                "movies",
                "film",
                "films",
                "cinema",
            ]

            # Skip if any exclude keywords are found
            hasVideoKeyword = any(
                keyword in channelLower for keyword in videoExcludeKeywords
            )

            if not hasVideoKeyword:
                musicKeywords = [
                    "music",
                    "radio",
                    "genre",
                    "eighties",
                    "nineties",
                    "seventies",
                    "rock",
                    "pop",
                    "jazz",
                    "blues",
                    "metal",
                    "country",
                    "classical",
                    "dance",
                    "electronic",
                    "hip hop",
                    "r&b",
                    "soul",
                    "disco",
                ]

                isMusicChannel = any(
                    keyword in channelLower for keyword in musicKeywords
                )

        # Also check channel type (12 = music genre)
        try:
            chtype = int(ADDON_SETTINGS.getSetting("Channel_" + str(newchan) + "_type"))
            if chtype == 12:
                # Double-check it's not a video channel even if type is 12
                if channelName and not any(
                    keyword in channelName.lower() for keyword in videoExcludeKeywords
                ):
                    isMusicChannel = True
        except:
            pass

        if isMusicChannel:  # Music channels
            # Try to parse artist from the filename
            filename = self.MyOverlayWindow.channels[newchan - 1].getItemFilename(plpos)

            if filename:
                # Extract just the filename without path
                filename = os.path.basename(filename)

                # Remove file extension
                filename = os.path.splitext(filename)[0]

                # Parse the filename pattern: Artist - Song - Album - Genre - Year - Format - Bitrate
                parts = filename.split(" - ")

                if len(parts) >= 2:
                    artist = parts[0].strip()
                    song = parts[1].strip()

                    # Set the second line to artist
                    self.getControl(501).setLabel(artist)

                    # Build description from available parts
                    desc_parts = []
                    if len(parts) > 2 and parts[2].strip():
                        desc_parts.append("Album: " + parts[2].strip())
                    if len(parts) > 3 and parts[3].strip():
                        desc_parts.append("Genre: " + parts[3].strip())
                    if len(parts) > 4 and parts[4].strip():
                        desc_parts.append("Year: " + parts[4].strip())

                    description = " | ".join(desc_parts) if desc_parts else "Music"
                    self.getControl(502).setText(description)
                else:
                    # Fallback if pattern doesn't match - try parsing from title
                    artist = ""
                    if title and " - " in title:
                        parts = title.split(" - ", 1)
                        if len(parts[0]) < 50:  # Artist names are usually shorter
                            artist = parts[0].strip()

                    if artist:
                        self.getControl(501).setLabel(artist)
                    else:
                        # Show cleaned channel name
                        displayName = channelName
                        for prefix in ["Music Genre - ", "Music - ", "Genre - "]:
                            if displayName.startswith(prefix):
                                displayName = displayName[len(prefix) :]
                                break
                        self.getControl(501).setLabel(displayName)

                    self.getControl(502).setText("Music Channel")
            else:
                # No filename available, use title parsing
                artist = ""
                if title and " - " in title:
                    parts = title.split(" - ", 1)
                    if len(parts[0]) < 50:
                        artist = parts[0].strip()

                if artist:
                    self.getControl(501).setLabel(artist)
                else:
                    displayName = channelName
                    for prefix in ["Music Genre - ", "Music - ", "Genre - "]:
                        if displayName.startswith(prefix):
                            displayName = displayName[len(prefix) :]
                            break
                    self.getControl(501).setLabel(displayName)

                self.getControl(502).setText("Music Channel")
        else:
            # For video channels
            episodeTitle = self.MyOverlayWindow.channels[
                newchan - 1
            ].getItemEpisodeTitle(plpos)

            # Check if this is a movie (no episode title means it's likely a movie)
            if not episodeTitle or episodeTitle.strip() == "":
                # This is likely a movie - try to get tagline from NFO
                itemPath = self.MyOverlayWindow.channels[newchan - 1].getItemFilename(
                    plpos
                )
                tagline = self.getMovieTagline(itemPath)

                if tagline:
                    self.getControl(501).setLabel(tagline)
                else:
                    # No tagline found, use default text or channel name
                    self.getControl(501).setLabel("Movie")
            else:
                # TV show - show episode title as before
                self.getControl(501).setLabel(episodeTitle)

            self.getControl(502).setText(
                self.MyOverlayWindow.channels[newchan - 1].getItemDescription(plpos)
            )

        # Get show/movie artwork with caching
        showArtwork = self.getShowArtwork(newchan - 1, plpos)
        if isinstance(showArtwork, unicode):
            showArtwork = showArtwork.encode("utf-8")
        self.getControl(503).setImage(showArtwork)

        self.log("setShowInfo return")

    def getShowArtwork(self, channelIndex, playlistPosition):
        """Get artwork for the show/movie at the specified position with caching"""
        cache_key = (channelIndex, playlistPosition)

        # Check cache first
        if cache_key in self.artworkCache:
            self.log(
                "Using cached artwork for channel "
                + str(channelIndex + 1)
                + ", position "
                + str(playlistPosition)
            )
            return self.artworkCache[cache_key]

        self.log(
            "getShowArtwork channel: "
            + str(channelIndex + 1)
            + ", position: "
            + str(playlistPosition)
        )

        showArtwork = None

        try:
            # Try to get the file path for the current item
            itemPath = self.MyOverlayWindow.channels[channelIndex].getItemFilename(
                playlistPosition
            )

            if itemPath and FileAccess.exists(itemPath):
                # Extract the directory path
                itemDir = os.path.dirname(itemPath)

                # For TV shows, check if we're in a season folder and go up one level
                dirName = os.path.basename(itemDir).lower()
                if (
                    dirName.startswith("season")
                    or dirName.startswith("s0")
                    or dirName.startswith("s1")
                ):
                    itemDir = os.path.dirname(itemDir)

                # List of possible artwork filenames in order of preference
                artworkNames = [
                    "landscape.jpg",
                    "landscape.png",
                    "fanart.jpg",
                    "fanart.png",
                    "backdrop.jpg",
                    "backdrop.png",
                    "background.jpg",
                    "background.png",
                    "art.jpg",
                    "art.png",
                ]

                # Check each possible artwork file
                for artName in artworkNames:
                    artFile = os.path.join(itemDir, artName)
                    if FileAccess.exists(artFile):
                        showArtwork = artFile
                        self.log("Found artwork: " + artFile)
                        break

                # If no artwork found in show folder, try to get from Kodi's cache
                if not showArtwork:
                    try:
                        # Try to get artwork from the playlist item metadata
                        item = xbmc.PlayList(xbmc.PLAYLIST_MUSIC).getitem(
                            playlistPosition
                        )
                        if item:
                            # Try different artwork types
                            for artType in ["landscape", "fanart", "thumb", "poster"]:
                                art = item.getArt(artType)
                                if art:
                                    showArtwork = art
                                    self.log("Found artwork from metadata: " + artType)
                                    break
                    except:
                        pass

        except Exception as e:
            self.log("Error getting show artwork: " + str(e), xbmc.LOGERROR)

        # Fall back to channel logo if no show artwork found
        if not showArtwork or not FileAccess.exists(showArtwork):
            showArtwork = (
                self.channelLogos
                + ascii(self.MyOverlayWindow.channels[channelIndex].name)
                + ".png"
            )
            if not FileAccess.exists(showArtwork):
                showArtwork = IMAGES_LOC + "Default.png"
            self.log("Falling back to channel logo or default")

        # Cache the result
        self.artworkCache[cache_key] = showArtwork

        return showArtwork

    def getMovieTagline(self, itemPath):
        """Get tagline from movie NFO file"""
        self.log("getMovieTagline: " + itemPath)

        try:
            # Get the directory and base filename
            itemDir = os.path.dirname(itemPath)
            itemBase = os.path.basename(itemPath)
            itemName = os.path.splitext(itemBase)[0]

            # Try different NFO filename patterns
            nfoPatterns = [
                os.path.join(itemDir, itemName + ".nfo"),  # Same name as video file
                os.path.join(itemDir, "movie.nfo"),  # Generic movie.nfo
            ]

            for nfoPath in nfoPatterns:
                if FileAccess.exists(nfoPath):
                    self.log("Found NFO file: " + nfoPath)

                    try:
                        # Read the NFO file
                        nfoFile = FileAccess.open(nfoPath, "r")
                        # Read the entire file - FileAccess.read() needs a size parameter
                        # Use a large size to read the whole file
                        nfoContent = nfoFile.read(1024 * 1024)  # Read up to 1MB
                        nfoFile.close()

                        # Parse XML
                        root = ET.fromstring(nfoContent)

                        # Look for tagline in different possible tags
                        tagline = None

                        # Check for 'tagline' tag first (preferred)
                        taglineTag = root.find("tagline")
                        if taglineTag is not None and taglineTag.text:
                            tagline = taglineTag.text.strip()
                            self.log("Found tagline in tagline tag: " + tagline)
                            return tagline

                        # Check for 'outline' tag as fallback
                        outline = root.find("outline")
                        if outline is not None and outline.text:
                            tagline = outline.text.strip()
                            # Truncate long outlines to fit on one line
                            if len(tagline) > 100:
                                tagline = tagline[:97] + "..."
                            self.log("Found tagline in outline tag: " + tagline)
                            return tagline

                    except Exception as e:
                        self.log(
                            "Error parsing NFO file " + nfoPath + ": " + str(e),
                            xbmc.LOGERROR,
                        )
                else:
                    self.log("NFO file not found: " + nfoPath)

        except Exception as e:
            self.log("Error getting movie tagline: " + str(e), xbmc.LOGERROR)

        self.log("No tagline found, returning None")
        return None

    # using the currently selected button, play the proper shows
    def selectShow(self):
        self.log("selectShow")
        basex, basey = self.getControl(111 + self.focusRow).getPosition()
        baseh = self.getControl(111 + self.focusRow).getHeight()
        basew = self.getControl(111 + self.focusRow).getWidth()
        # use the selected time to set the video
        left, top = self.channelButtons[self.focusRow][self.focusIndex].getPosition()
        width = self.channelButtons[self.focusRow][self.focusIndex].getWidth()
        left = left - basex + (width / 2)
        starttime = self.shownTime + (left / (basew / 5400.0))
        chnoffset = self.focusRow - 2
        newchan = self.centerChannel

        while chnoffset != 0:
            if chnoffset > 0:
                newchan = self.MyOverlayWindow.fixChannel(newchan + 1, True)
                chnoffset -= 1
            else:
                newchan = self.MyOverlayWindow.fixChannel(newchan - 1, False)
                chnoffset += 1

        plpos = self.determinePlaylistPosAtTime(starttime, newchan)

        if plpos == -1:
            self.log(
                "Unable to find the proper playlist to set from EPG", xbmc.LOGERROR
            )
            return

        timedif = (
            time.time() - self.MyOverlayWindow.channels[newchan - 1].lastAccessTime
        )
        pos = self.MyOverlayWindow.channels[newchan - 1].playlistPosition
        showoffset = self.MyOverlayWindow.channels[newchan - 1].showTimeOffset

        # adjust the show and time offsets to properly position inside the playlist
        while showoffset + timedif > self.MyOverlayWindow.channels[
            newchan - 1
        ].getItemDuration(pos):
            timedif -= (
                self.MyOverlayWindow.channels[newchan - 1].getItemDuration(pos)
                - showoffset
            )
            pos = self.MyOverlayWindow.channels[newchan - 1].fixPlaylistIndex(pos + 1)
            showoffset = 0

        if self.MyOverlayWindow.currentChannel == newchan:
            if plpos == xbmc.PlayList(xbmc.PLAYLIST_MUSIC).getposition():
                self.log("selectShow return current show")
                return

        if pos != plpos:
            self.MyOverlayWindow.channels[newchan - 1].setShowPosition(plpos)
            self.MyOverlayWindow.channels[newchan - 1].setShowTime(0)
            self.MyOverlayWindow.channels[newchan - 1].setAccessTime(time.time())

        self.MyOverlayWindow.newChannel = newchan
        self.log("selectShow return")

    def determinePlaylistPosAtTime(self, starttime, channel):
        self.log("determinePlaylistPosAtTime " + str(starttime) + ", " + str(channel))
        channel = self.MyOverlayWindow.fixChannel(channel)

        # if the channel is paused, then it's just the current item
        if self.MyOverlayWindow.channels[channel - 1].isPaused:
            self.log("determinePlaylistPosAtTime paused return")
            return self.MyOverlayWindow.channels[channel - 1].playlistPosition
        else:
            # Find the show that was running at the given time
            # Use the current time and show offset to calculate it
            # At timedif time, channelShowPosition was playing at channelTimes
            # The only way this isn't true is if the current channel is curchannel since
            # it could have been fast forwarded or rewinded (rewound)?
            if channel == self.MyOverlayWindow.currentChannel:
                playlistpos = xbmc.PlayList(xbmc.PLAYLIST_MUSIC).getposition()
                videotime = xbmc.Player().getTime()
                reftime = time.time()
            else:
                playlistpos = self.MyOverlayWindow.channels[
                    channel - 1
                ].playlistPosition
                videotime = self.MyOverlayWindow.channels[channel - 1].showTimeOffset
                reftime = self.MyOverlayWindow.channels[channel - 1].lastAccessTime

            # normalize reftime to the beginning of the video
            reftime -= videotime

            while reftime > starttime:
                playlistpos -= 1
                reftime -= self.MyOverlayWindow.channels[channel - 1].getItemDuration(
                    playlistpos
                )

            while (
                reftime
                + self.MyOverlayWindow.channels[channel - 1].getItemDuration(
                    playlistpos
                )
                < starttime
            ):
                reftime += self.MyOverlayWindow.channels[channel - 1].getItemDuration(
                    playlistpos
                )
                playlistpos += 1

            self.log(
                "determinePlaylistPosAtTime return"
                + str(
                    self.MyOverlayWindow.channels[channel - 1].fixPlaylistIndex(
                        playlistpos
                    )
                )
            )
            return self.MyOverlayWindow.channels[channel - 1].fixPlaylistIndex(
                playlistpos
            )
