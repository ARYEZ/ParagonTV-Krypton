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

import os

import xbmc
import xbmcaddon
import xbmcgui

from Globals import *

# Constants
ADDON = xbmcaddon.Addon("script.paragontv")
ADDON_PATH = ADDON.getAddonInfo("path")
FLAGS_PATH = os.path.join(ADDON_PATH, "resources", "skins", "default", "media", "ptv_flags")

ACTION_PREVIOUS_MENU = [9, 10, 92, 216, 247, 257, 275, 61467, 61448]


class VideoInfoWindow(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        xbmcgui.WindowXMLDialog.__init__(self, *args, **kwargs)
        self.log("__init__")

    def onInit(self):
        self.log("onInit")
        self.populateVideoInfo()

    def populateVideoInfo(self):
        """Fetch video info and set window properties with icon paths"""

        # Get video resolution
        width = xbmc.getInfoLabel("VideoPlayer.VideoWidth")
        height = xbmc.getInfoLabel("VideoPlayer.VideoHeight")
        resolutionIcon = self.getResolutionIcon(height)

        if resolutionIcon:
            self.setProperty("VideoInfo.Resolution.Icon", resolutionIcon)
        self.setProperty("VideoInfo.Resolution.Text", self.getResolutionText(height))

        if width and height:
            self.setProperty("VideoInfo.Dimensions", "%s x %s" % (width, height))

        # Get video codec
        videoCodec = xbmc.getInfoLabel("VideoPlayer.VideoCodec")
        videoCodecIcon = self.getVideoCodecIcon(videoCodec)

        if videoCodecIcon:
            self.setProperty("VideoInfo.VideoCodec.Icon", videoCodecIcon)
        self.setProperty("VideoInfo.VideoCodec.Text", videoCodec.upper() if videoCodec else "Unknown")

        # Video details (bitrate, fps)
        videoBitrate = xbmc.getInfoLabel("VideoPlayer.VideoBitrate")
        fps = xbmc.getInfoLabel("VideoPlayer.VideoFPS")
        videoDetails = []
        if videoBitrate:
            videoDetails.append("%s kbps" % videoBitrate)
        if fps:
            videoDetails.append("%s fps" % fps)
        self.setProperty("VideoInfo.VideoDetails", " | ".join(videoDetails))

        # Get audio codec
        audioCodec = xbmc.getInfoLabel("VideoPlayer.AudioCodec")
        audioCodecIcon = self.getAudioCodecIcon(audioCodec)

        if audioCodecIcon:
            self.setProperty("VideoInfo.AudioCodec.Icon", audioCodecIcon)
        self.setProperty("VideoInfo.AudioCodec.Text", audioCodec.upper() if audioCodec else "Unknown")

        # Audio details
        audioBitrate = xbmc.getInfoLabel("VideoPlayer.AudioBitrate")
        sampleRate = xbmc.getInfoLabel("VideoPlayer.AudioSamplerate")
        audioDetails = []
        if audioBitrate:
            audioDetails.append("%s kbps" % audioBitrate)
        if sampleRate:
            audioDetails.append("%s Hz" % sampleRate)
        self.setProperty("VideoInfo.AudioDetails", " | ".join(audioDetails))

        # Get audio channels
        audioChannels = xbmc.getInfoLabel("VideoPlayer.AudioChannels")
        audioChannelsIcon = self.getAudioChannelsIcon(audioChannels)

        if audioChannelsIcon:
            self.setProperty("VideoInfo.AudioChannels.Icon", audioChannelsIcon)
        self.setProperty("VideoInfo.AudioChannels.Text", self.getChannelsText(audioChannels))
        self.setProperty("VideoInfo.ChannelLayout", self.getChannelLayout(audioChannels))

        # File info
        filename = xbmc.getInfoLabel("Player.Filename")
        self.setProperty("VideoInfo.Filename", filename if filename else "Unknown")

        # Duration
        duration = xbmc.getInfoLabel("VideoPlayer.Duration")
        self.setProperty("VideoInfo.Duration", duration if duration else "--:--")

        # Aspect ratio
        aspect = xbmc.getInfoLabel("VideoPlayer.VideoAspect")
        self.setProperty("VideoInfo.AspectRatio", aspect if aspect else "Unknown")

    def getResolutionIcon(self, height):
        """Map video height to resolution icon"""
        if not height:
            return None

        try:
            h = int(height)
        except:
            return None

        # Map height ranges to resolution icons
        if h >= 2160:
            res = "4k"
        elif h >= 1080:
            res = "1080"
        elif h >= 720:
            res = "720"
        elif h >= 576:
            res = "576"
        elif h >= 540:
            res = "540"
        elif h >= 480:
            res = "480"
        else:
            return None

        iconPath = os.path.join(FLAGS_PATH, "videoresolution", "%s.png" % res)
        if os.path.exists(iconPath):
            return iconPath
        return None

    def getResolutionText(self, height):
        """Get resolution text label"""
        if not height:
            return "Unknown"

        try:
            h = int(height)
        except:
            return height

        if h >= 2160:
            return "4K UHD"
        elif h >= 1080:
            return "1080p HD"
        elif h >= 720:
            return "720p HD"
        elif h >= 576:
            return "576p SD"
        elif h >= 540:
            return "540p"
        elif h >= 480:
            return "480p SD"
        else:
            return "%sp" % h

    def getVideoCodecIcon(self, codec):
        """Map video codec to icon"""
        if not codec:
            return None

        codec = codec.lower()

        # Try direct match first
        iconPath = os.path.join(FLAGS_PATH, "videocodec", "%s.png" % codec)
        if os.path.exists(iconPath):
            return iconPath

        # Try common aliases
        aliases = {
            "h264": ["avc1", "avc", "x264"],
            "hevc": ["h265", "x265", "hev1", "hvc1"],
            "mpeg2video": ["mpeg2"],
            "mpeg1video": ["mpeg1"],
            "vc1": ["vc-1", "wvc1"],
            "vp9": ["vp09"],
            "vp8": ["vp08"],
        }

        for canonical, names in aliases.items():
            if codec in names:
                iconPath = os.path.join(FLAGS_PATH, "videocodec", "%s.png" % canonical)
                if os.path.exists(iconPath):
                    return iconPath

        # Try reverse lookup
        for canonical, names in aliases.items():
            if codec == canonical:
                for name in names:
                    iconPath = os.path.join(FLAGS_PATH, "videocodec", "%s.png" % name)
                    if os.path.exists(iconPath):
                        return iconPath

        return None

    def getAudioCodecIcon(self, codec):
        """Map audio codec to icon"""
        if not codec:
            return None

        codec = codec.lower()

        # Try direct match first
        iconPath = os.path.join(FLAGS_PATH, "audiocodec", "%s.png" % codec)
        if os.path.exists(iconPath):
            return iconPath

        # Try common aliases
        aliases = {
            "ac3": ["dolbydigital", "a52"],
            "eac3": ["dolbydigitalplus", "ec3"],
            "dts": ["dca"],
            "truehd": ["mlp"],
            "aac": ["aac_latm"],
            "flac": ["fla"],
            "vorbis": ["ogg"],
            "pcm": ["lpcm", "pcm_s16le", "pcm_s24le", "pcm_bluray"],
        }

        for canonical, names in aliases.items():
            if codec in names:
                iconPath = os.path.join(FLAGS_PATH, "audiocodec", "%s.png" % canonical)
                if os.path.exists(iconPath):
                    return iconPath

        return None

    def getAudioChannelsIcon(self, channels):
        """Map audio channel count to icon"""
        if not channels:
            return None

        try:
            ch = int(channels)
        except:
            return None

        iconPath = os.path.join(FLAGS_PATH, "audiochannel", "%d.png" % ch)
        if os.path.exists(iconPath):
            return iconPath

        return None

    def getChannelsText(self, channels):
        """Get channel count text"""
        if not channels:
            return "Unknown"

        try:
            ch = int(channels)
        except:
            return channels

        layouts = {
            1: "Mono",
            2: "Stereo",
            3: "2.1",
            4: "Quad",
            5: "4.1",
            6: "5.1",
            7: "6.1",
            8: "7.1",
            10: "9.1",
        }

        return layouts.get(ch, "%d ch" % ch)

    def getChannelLayout(self, channels):
        """Get detailed channel layout description"""
        if not channels:
            return ""

        try:
            ch = int(channels)
        except:
            return ""

        layouts = {
            1: "Center",
            2: "Left, Right",
            6: "Front L/R, Center, LFE, Surround L/R",
            8: "Front L/R, Center, LFE, Side L/R, Rear L/R",
        }

        return layouts.get(ch, "")

    def setProperty(self, key, value):
        """Set a window property"""
        self.getWindow().setProperty(key, str(value) if value else "")

    def getWindow(self):
        """Get the window to set properties on"""
        return self

    def onClick(self, controlId):
        self.log("onClick " + str(controlId))
        self.close()

    def onAction(self, act):
        action = act.getId()
        self.log("onAction " + str(action))

        # Close on back/escape or any click
        if action in ACTION_PREVIOUS_MENU or action == 7:  # ACTION_SELECT_ITEM
            self.close()

    def log(self, msg, level=xbmc.LOGDEBUG):
        log("VideoInfoWindow: " + msg, level)
