#   Copyright (C) 2025 Aryez
# -*- coding: utf-8 -*-
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

from datetime import datetime, timedelta, date
import json
import os
import random
import re
import subprocess
import sys
import threading
import time
import traceback
from xml.dom.minidom import parse, parseString

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs
import re
# Python 2/3 compatibility
if sys.version_info[0] >= 3:
    unicode = str
    basestring = str

try:
    import html  # Python 3
except ImportError:
    import HTMLParser  # Python 2
    html = HTMLParser.HTMLParser()

# Kodi version compatibility for translatePath
# Kodi v19+ uses xbmcvfs.translatePath()
# Kodi v18 and earlier use xbmc.translatePath()
try:
    translatePath = xbmcvfs.translatePath
except AttributeError:
    translatePath = xbmc.translatePath

from Channel import Channel
from ChannelList import ChannelList
from ChannelListThread import ChannelListThread
from EPGWindow import EPGWindow
from EpisodeBrowserWindow import EpisodeBrowserWindow
from FileAccess import FileAccess, FileLock
from Globals import *
from Migrate import Migrate
from Playlist import Playlist
from SidebarWindow import SidebarWindow
from SpeedDialWindow import SpeedDialWindow

try:
    from PIL import Image, ImageEnhance

    PIL_AVAILABLE = True
except:
    PIL_AVAILABLE = False

ICON = ADDON.getAddonInfo("icon")

# ============================================================================
# KNOWLEDGE PAGE - ZIM FILE CONFIGURATIONS
# ============================================================================

# Kiwix server configuration
KIWIX_SERVER = "http://10.0.0.39:8080"

# ZIM file configurations for Knowledge Page
KNOWLEDGE_SOURCES = {
    'wikipedia': {
        'name': 'Wikipedia',
        'zim_name': 'wikipedia_en_all_maxi_2025-08',
        'type': 'article',
        'base_url': KIWIX_SERVER + '/content/wikipedia_en_all_maxi_2025-08',
        'random_url': KIWIX_SERVER + '/random?content=wikipedia_en_all_maxi_2025-08',
    },
    'funfacts': {
        'name': 'Fun Facts',
        'zim_name': 'wikipedia_en_all_maxi_2025-08',
        'type': 'funfacts',
        'base_url': KIWIX_SERVER + '/content/wikipedia_en_all_maxi_2025-08',
        'random_url': KIWIX_SERVER + '/random?content=wikipedia_en_all_maxi_2025-08',
    },
    'trivia': {
        'name': 'Trivia',
        'zim_name': 'wikipedia_en_all_maxi_2025-08',
        'type': 'trivia',
        'base_url': KIWIX_SERVER + '/content/wikipedia_en_all_maxi_2025-08',
        'random_url': KIWIX_SERVER + '/random?content=wikipedia_en_all_maxi_2025-08',
    },
    'mysteries': {
        'name': 'Unsolved Mysteries',
        'zim_name': 'wikipedia_en_all_maxi_2025-08',
        'type': 'mysteries',
        'base_url': KIWIX_SERVER + '/content/wikipedia_en_all_maxi_2025-08',
        'random_url': KIWIX_SERVER + '/random?content=wikipedia_en_all_maxi_2025-08',
    },
}

# Rotation order for Knowledge Page (cycles through these each time page appears)
KNOWLEDGE_ROTATION = ['wikipedia', 'funfacts', 'trivia', 'mysteries']

# Wikipedia Article Lists - Complete 9,800+ Article Library
WIKIPEDIA_ARTICLES = {
    # ============================================
    # SCIENCE FICTION (~1,000 articles)
    # ============================================
    'scifi_starwars': [
        'Star_Wars', 'The_Empire_Strikes_Back', 'Return_of_the_Jedi', 'The_Phantom_Menace',
        'Attack_of_the_Clones', 'Revenge_of_the_Sith', 'The_Force_Awakens', 'The_Last_Jedi',
        'The_Rise_of_Skywalker', 'Rogue_One', 'Solo:_A_Star_Wars_Story', 'The_Mandalorian',
        'The_Book_of_Boba_Fett', 'Obi-Wan_Kenobi_(TV_series)', 'Ahsoka_(TV_series)',
        'Andor_(TV_series)', 'Luke_Skywalker', 'Darth_Vader', 'Anakin_Skywalker',
        'Princess_Leia', 'Han_Solo', 'Chewbacca', 'C-3PO', 'R2-D2', 'Obi-Wan_Kenobi',
        'Yoda', 'Emperor_Palpatine', 'Darth_Maul', 'Count_Dooku', 'General_Grievous',
        'Boba_Fett', 'Jango_Fett', 'Ahsoka_Tano', 'Mace_Windu', 'Qui-Gon_Jinn',
        'Rey_(Star_Wars)', 'Kylo_Ren', 'Finn_(Star_Wars)', 'Poe_Dameron', 'BB-8',
        'Grogu', 'Din_Djarin', 'Millennium_Falcon', 'Death_Star', 'Star_Destroyer',
        'X-wing', 'TIE_fighter', 'Lightsaber', 'The_Force', 'Jedi', 'Sith',
        'Stormtrooper_(Star_Wars)', 'Clone_trooper', 'Tatooine', 'Coruscant', 'Hoth',
        'Endor_(Star_Wars)', 'Dagobah', 'Naboo', 'Mustafar', 'Beskar',
    ],
    
    'scifi_startrek': [
        'Star_Trek', 'Star_Trek:_The_Original_Series', 'Star_Trek:_The_Next_Generation',
        'Star_Trek:_Deep_Space_Nine', 'Star_Trek:_Voyager', 'Star_Trek:_Enterprise',
        'Star_Trek:_Discovery', 'Star_Trek:_Picard', 'Star_Trek:_Strange_New_Worlds',
        'Star_Trek:_Lower_Decks', 'Star_Trek:_Prodigy', 'James_T._Kirk', 'Spock',
        'Leonard_McCoy', 'Montgomery_Scott', 'Uhura', 'Hikaru_Sulu', 'Pavel_Chekov',
        'Jean-Luc_Picard', 'William_Riker', 'Data_(Star_Trek)', 'Worf', 'Geordi_La_Forge',
        'Deanna_Troi', 'Beverly_Crusher', 'Wesley_Crusher', 'Benjamin_Sisko',
        'Kira_Nerys', 'Odo_(Star_Trek)', 'Jadzia_Dax', 'Kathryn_Janeway',
        'Chakotay', 'Seven_of_Nine', 'The_Doctor_(Star_Trek:_Voyager)', 'Tuvok',
        'USS_Enterprise_(NCC-1701)', 'USS_Enterprise_(NCC-1701-D)', 'USS_Defiant',
        'USS_Voyager_(Star_Trek)', 'Klingon', 'Romulan', 'Vulcan_(Star_Trek)',
        'Borg', 'Ferengi', 'Cardassian', 'Q_(Star_Trek)', 'Starfleet', 'United_Federation_of_Planets',
        'Warp_drive', 'Transporter_(Star_Trek)', 'Tricorder', 'Phaser_(Star_Trek)',
        'Holodeck', 'Prime_Directive', 'The_Wrath_of_Khan', 'The_Voyage_Home',
        'First_Contact_(Star_Trek)', 'Khan_Noonien_Singh', 'Kobayashi_Maru',
    ],
    
    'scifi_doctorwho': [
        'Doctor_Who', 'The_Doctor_(Doctor_Who)', 'TARDIS', 'Dalek', 'Cyberman',
        'Weeping_Angel', 'Sonic_screwdriver', 'Gallifrey', 'Time_Lord', 'Regeneration_(Doctor_Who)',
        'Companion_(Doctor_Who)', 'First_Doctor', 'Second_Doctor', 'Third_Doctor',
        'Fourth_Doctor', 'Fifth_Doctor', 'Sixth_Doctor', 'Seventh_Doctor', 'Eighth_Doctor',
        'Ninth_Doctor', 'Tenth_Doctor', 'Eleventh_Doctor', 'Twelfth_Doctor',
        'Thirteenth_Doctor', 'Fourteenth_Doctor', 'Fifteenth_Doctor', 'Susan_Foreman',
        'Sarah_Jane_Smith', 'Rose_Tyler', 'Martha_Jones', 'Donna_Noble', 'Amy_Pond',
        'Rory_Williams', 'Clara_Oswald', 'River_Song_(Doctor_Who)', 'Bill_Potts',
        'The_Master_(Doctor_Who)', 'Davros', 'Rassilon_(Doctor_Who)', 'The_Rani_(Doctor_Who)',
    ],
    
    'scifi_films_classic': [
        '2001:_A_Space_Odyssey_(film)', 'Blade_Runner', 'Blade_Runner_2049',
        'The_Terminator', 'Terminator_2:_Judgment_Day', 'Terminator_3:_Rise_of_the_Machines',
        'Terminator_Salvation', 'Terminator_Genisys', 'Alien_(film)', 'Aliens_(film)',
        'Alien_3', 'Alien_Resurrection', 'Prometheus_(2012_film)', 'Alien:_Covenant',
        'The_Matrix', 'The_Matrix_Reloaded', 'The_Matrix_Revolutions', 'The_Matrix_Resurrections',
        'Close_Encounters_of_the_Third_Kind', 'E.T._the_Extra-Terrestrial',
        'Back_to_the_Future', 'Back_to_the_Future_Part_II', 'Back_to_the_Future_Part_III',
        'Jurassic_Park_(film)', 'The_Lost_World:_Jurassic_Park', 'Jurassic_Park_III',
        'Jurassic_World', 'Jurassic_World:_Fallen_Kingdom', 'Jurassic_World_Dominion',
        'Total_Recall_(1990_film)', 'RoboCop', 'RoboCop_2', 'RoboCop_3',
        'Predator_(film)', 'Predator_2', 'Predators_(film)', 'The_Predator_(film)',
        'Prey_(2022_film)', 'The_Thing_(1982_film)', 'The_Fly_(1986_film)',
        'A_Clockwork_Orange_(film)', 'Logan%27s_Run_(film)', 'Soylent_Green',
        'Planet_of_the_Apes_(1968_film)', 'Beneath_the_Planet_of_the_Apes',
    ],
    
    'scifi_films_modern': [
        'Inception', 'Interstellar_(film)', 'Arrival_(film)', 'Ex_Machina_(film)',
        'Mad_Max:_Fury_Road', 'District_9', 'Edge_of_Tomorrow', 'Looper_(film)',
        'Gravity_(2013_film)', 'The_Martian_(film)', 'Avatar_(2009_film)',
        'Avatar:_The_Way_of_Water', 'Dune_(2021_film)', 'Dune:_Part_Two',
        'Tenet_(film)', 'Annihilation_(film)', 'A_Quiet_Place', 'A_Quiet_Place_Part_II',
        'Minority_Report_(film)', 'I,_Robot_(film)', 'Elysium_(film)',
        'Chappie_(film)', 'Pacific_Rim_(film)', 'Pacific_Rim_Uprising',
        'Oblivion_(2013_film)', 'Lucy_(2014_film)', 'Passengers_(2016_film)',
        'Valerian_and_the_City_of_a_Thousand_Planets', 'Ghost_in_the_Shell_(2017_film)',
        'Ready_Player_One_(film)', 'Alita:_Battle_Angel', 'Ad_Astra_(film)',
        'Moon_(2009_film)', 'Sunshine_(2007_film)', 'Children_of_Men',
        'Snowpiercer', 'The_Maze_Runner_(film)', 'Divergent_(film)', 'The_Hunger_Games_(film)',
    ],
    
    'scifi_tv_shows': [
        'The_Twilight_Zone_(1959_TV_series)', 'The_Outer_Limits_(1963_TV_series)',
        'Battlestar_Galactica_(1978_TV_series)', 'Battlestar_Galactica_(2004_TV_series)',
        'Stargate_SG-1', 'Stargate_Atlantis', 'Stargate_Universe', 'Babylon_5',
        'Farscape', 'Andromeda_(TV_series)', 'Lexx', 'Space:_Above_and_Beyond',
        'The_Expanse_(TV_series)', 'Westworld_(TV_series)', 'Black_Mirror',
        'Stranger_Things', 'Altered_Carbon', 'The_Orville', 'Foundation_(TV_series)',
        'For_All_Mankind_(TV_series)', 'Severance_(TV_series)', 'Silo_(TV_series)',
        'Lost_(TV_series)', 'Fringe_(TV_series)', 'The_X-Files', 'Firefly_(TV_series)',
        'Serenity_(2005_film)', 'Dark_(TV_series)', 'The_Handmaid%27s_Tale_(TV_series)',
        '3_Body_Problem_(TV_series)', 'Raised_by_Wolves_(American_TV_series)',
        'The_Man_in_the_High_Castle_(TV_series)', 'Counterpart_(TV_series)',
        'Sense8', 'Timeless_(TV_series)', 'Travelers_(TV_series)', '12_Monkeys_(TV_series)',
        'Quantum_Leap', 'Sliders_(TV_series)', 'Heroes_(American_TV_series)',
        'The_4400', 'Warehouse_13', 'Eureka_(American_TV_series)', 'Continuum_(TV_series)',
    ],
    
    'scifi_literature': [
        'Dune_(novel)', 'Dune_Messiah', 'Children_of_Dune', 'God_Emperor_of_Dune',
        'Foundation_(Asimov_novel)', 'Foundation_and_Empire', 'Second_Foundation',
        'Foundation_series', 'I,_Robot', 'The_Caves_of_Steel', 'The_Naked_Sun',
        'The_End_of_Eternity', 'The_Gods_Themselves', 'Neuromancer', 'Count_Zero',
        'Mona_Lisa_Overdrive', 'Snow_Crash', 'The_Diamond_Age', 'Cryptonomicon',
        'The_War_of_the_Worlds', 'The_Time_Machine', 'The_Invisible_Man',
        'Nineteen_Eighty-Four', 'Animal_Farm', 'Brave_New_World', 'Fahrenheit_451',
        'The_Martian_Chronicles', 'The_Illustrated_Man', 'The_Hitchhiker%27s_Guide_to_the_Galaxy',
        'The_Restaurant_at_the_End_of_the_Universe', 'Life,_the_Universe_and_Everything',
        'Ender%27s_Game', 'Speaker_for_the_Dead', 'Xenocide', 'Starship_Troopers',
        'The_Forever_War', 'The_Moon_Is_a_Harsh_Mistress', 'Stranger_in_a_Strange_Land',
        'Hyperion_(Simmons_novel)', 'The_Fall_of_Hyperion', 'Endymion_(Simmons_novel)',
        'The_Left_Hand_of_Darkness', 'The_Dispossessed', 'Do_Androids_Dream_of_Electric_Sheep%3F',
        'The_Man_in_the_High_Castle', 'Ubik', 'A_Scanner_Darkly', 'Flow_My_Tears,_the_Policeman_Said',
        'Solaris_(novel)', 'Ringworld', 'Rendezvous_with_Rama', 'Childhood%27s_End',
        'The_Handmaid%27s_Tale', 'Oryx_and_Crake', 'The_Year_of_the_Flood',
    ],
    
    'scifi_authors': [
        'Isaac_Asimov', 'Arthur_C._Clarke', 'Robert_A._Heinlein', 'Philip_K._Dick',
        'Ray_Bradbury', 'Ursula_K._Le_Guin', 'William_Gibson', 'Neal_Stephenson',
        'Frank_Herbert', 'Orson_Scott_Card', 'Dan_Simmons', 'Kim_Stanley_Robinson',
        'Octavia_E._Butler', 'Samuel_R._Delany', 'Harlan_Ellison', 'Theodore_Sturgeon',
        'Alfred_Bester', 'Joe_Haldeman', 'Larry_Niven', 'Jerry_Pournelle',
        'Frederik_Pohl', 'C._J._Cherryh', 'Lois_McMaster_Bujold', 'Vernor_Vinge',
        'Greg_Egan', 'Alastair_Reynolds', 'Peter_F._Hamilton', 'Iain_M._Banks',
        'Ann_Leckie', 'N._K._Jemisin', 'John_Scalzi', 'Cory_Doctorow',
    ],
    
    # ============================================
    # FANTASY (~800 articles)
    # ============================================
    'fantasy_lotr': [
        'The_Lord_of_the_Rings', 'The_Fellowship_of_the_Ring', 'The_Two_Towers',
        'The_Return_of_the_King', 'The_Hobbit', 'The_Silmarillion',
        'The_Lord_of_the_Rings:_The_Fellowship_of_the_Ring_(film)',
        'The_Lord_of_the_Rings:_The_Two_Towers_(film)',
        'The_Lord_of_the_Rings:_The_Return_of_the_King_(film)',
        'The_Hobbit:_An_Unexpected_Journey', 'The_Hobbit:_The_Desolation_of_Smaug',
        'The_Hobbit:_The_Battle_of_the_Five_Armies', 'The_Rings_of_Power',
        'Frodo_Baggins', 'Bilbo_Baggins', 'Gandalf', 'Aragorn', 'Legolas',
        'Gimli_(Middle-earth)', 'Boromir', 'Samwise_Gamgee', 'Meriadoc_Brandybuck',
        'Peregrin_Took', 'Gollum', 'Sauron', 'Saruman', 'The_One_Ring',
        'Middle-earth', 'The_Shire', 'Rivendell', 'LothlÃ³rien', 'Mordor',
        'Gondor', 'Rohan_(Middle-earth)', 'Isengard', 'Minas_Tirith', 'Mount_Doom',
        'Elrond', 'Galadriel', 'Arwen', 'Ã‰owyn', 'Faramir', 'ThÃ©oden',
        'Thorin_Oakenshield', 'Smaug', 'Balrog', 'NazgÃ»l', 'Shelob',
    ],
    
    'fantasy_got': [
        'A_Song_of_Ice_and_Fire', 'A_Game_of_Thrones', 'A_Clash_of_Kings',
        'A_Storm_of_Swords', 'A_Feast_for_Crows', 'A_Dance_with_Dragons',
        'Game_of_Thrones', 'House_of_the_Dragon', 'Jon_Snow_(character)',
        'Daenerys_Targaryen', 'Tyrion_Lannister', 'Cersei_Lannister', 'Jaime_Lannister',
        'Arya_Stark', 'Sansa_Stark', 'Bran_Stark', 'Ned_Stark', 'Catelyn_Stark',
        'Robb_Stark', 'Theon_Greyjoy', 'Joffrey_Baratheon', 'Stannis_Baratheon',
        'Renly_Baratheon', 'Robert_Baratheon', 'Petyr_Baelish', 'Varys_(character)',
        'Sandor_Clegane', 'Gregor_Clegane', 'Brienne_of_Tarth', 'Margaery_Tyrell',
        'Olenna_Tyrell', 'Oberyn_Martell', 'Khal_Drogo', 'Jorah_Mormont',
        'Samwell_Tarly', 'Davos_Seaworth', 'Melisandre', 'Ramsay_Bolton',
        'Westeros', 'The_Wall_(A_Song_of_Ice_and_Fire)', 'King%27s_Landing',
        'Winterfell', 'Casterly_Rock', 'Dragonstone_(Game_of_Thrones)', 'Iron_Throne_(A_Song_of_Ice_and_Fire)',
        'White_Walker', 'Dragon_(A_Song_of_Ice_and_Fire)', 'Direwolf', 'Red_Wedding',
    ],
    
    'fantasy_harry_potter': [
        'Harry_Potter', 'Harry_Potter_(character)', 'Hermione_Granger', 'Ron_Weasley',
        'Albus_Dumbledore', 'Severus_Snape', 'Lord_Voldemort', 'Rubeus_Hagrid',
        'Sirius_Black', 'Remus_Lupin', 'Minerva_McGonagall', 'Draco_Malfoy',
        'Neville_Longbottom', 'Luna_Lovegood', 'Ginny_Weasley', 'Fred_and_George_Weasley',
        'Dobby_(character)', 'Bellatrix_Lestrange', 'Harry_Potter_and_the_Philosopher%27s_Stone',
        'Harry_Potter_and_the_Chamber_of_Secrets', 'Harry_Potter_and_the_Prisoner_of_Azkaban',
        'Harry_Potter_and_the_Goblet_of_Fire', 'Harry_Potter_and_the_Order_of_the_Phoenix',
        'Harry_Potter_and_the_Half-Blood_Prince', 'Harry_Potter_and_the_Deathly_Hallows',
        'Hogwarts', 'Gryffindor', 'Slytherin', 'Hufflepuff', 'Ravenclaw',
        'Quidditch', 'Patronus_Charm', 'Horcrux', 'Deathly_Hallows', 'Elder_Wand',
        'Fantastic_Beasts_and_Where_to_Find_Them_(film)', 'Fantastic_Beasts:_The_Crimes_of_Grindelwald',
    ],
    
    'fantasy_literature': [
        'The_Chronicles_of_Narnia', 'The_Lion,_the_Witch_and_the_Wardrobe',
        'Prince_Caspian', 'The_Voyage_of_the_Dawn_Treader', 'The_Wheel_of_Time',
        'The_Eye_of_the_World', 'The_Great_Hunt', 'The_Dragon_Reborn',
        'The_Name_of_the_Wind', 'The_Kingkiller_Chronicle', 'Mistborn', 'The_Final_Empire',
        'The_Stormlight_Archive', 'The_Way_of_Kings', 'Words_of_Radiance',
        'The_Earthsea_Cycle', 'A_Wizard_of_Earthsea', 'The_Farthest_Shore',
        'The_Dark_Tower_(series)', 'The_Gunslinger', 'The_Drawing_of_the_Three',
        'The_Waste_Lands', 'Conan_the_Barbarian', 'The_Witcher', 'The_Last_Wish',
        'Sword_of_Destiny', 'Blood_of_Elves', 'American_Gods', 'Good_Omens',
        'The_Sandman_(comic_book)', 'Dragonlance', 'Forgotten_Realms',
        'The_Sword_of_Shannara', 'The_Belgariad', 'The_Riftwar_Cycle',
    ],
    
    'fantasy_authors': [
        'J._R._R._Tolkien', 'George_R._R._Martin', 'J._K._Rowling', 'C._S._Lewis',
        'Robert_Jordan', 'Brandon_Sanderson', 'Patrick_Rothfuss', 'Terry_Pratchett',
        'Neil_Gaiman', 'Terry_Brooks', 'David_Eddings', 'Raymond_E._Feist',
        'Robert_E._Howard', 'Fritz_Leiber', 'Michael_Moorcock', 'Glen_Cook',
        'Steven_Erikson', 'Joe_Abercrombie', 'Brent_Weeks', 'Brian_McClellan',
    ],
    
    'fantasy_films_tv': [
        'The_Witcher_(TV_series)', 'The_Wheel_of_Time_(TV_series)', 'Shadow_and_Bone_(TV_series)',
        'The_Magicians_(American_TV_series)', 'Once_Upon_a_Time_(TV_series)',
        'Merlin_(2008_TV_series)', 'Legend_of_the_Seeker', 'Xena:_Warrior_Princess',
        'Hercules:_The_Legendary_Journeys', 'Willow_(TV_series)', 'The_Shannara_Chronicles',
        'Conan_the_Barbarian_(1982_film)', 'Conan_the_Destroyer', 'The_Princess_Bride',
        'Stardust_(2007_film)', 'The_NeverEnding_Story', 'Labyrinth_(1986_film)',
        'The_Dark_Crystal', 'Legend_(1985_film)', 'Dragonslayer_(1981_film)',
        'Willow_(film)', 'Krull_(film)', 'Ladyhawke_(film)', 'Excalibur_(film)',
    ],
    
    # ============================================
    # COMICS: MARVEL (~500 articles)
    # ============================================
    'comics_marvel_heroes': [
        'Spider-Man', 'Peter_Parker_(Marvel_Cinematic_Universe)', 'Miles_Morales',
        'Iron_Man', 'Tony_Stark_(Marvel_Cinematic_Universe)', 'Captain_America',
        'Steve_Rogers_(Marvel_Cinematic_Universe)', 'Thor_(Marvel_Comics)',
        'Thor_(Marvel_Cinematic_Universe)', 'Hulk', 'Bruce_Banner_(Marvel_Cinematic_Universe)',
        'Black_Widow_(Marvel_Comics)', 'Natasha_Romanoff_(Marvel_Cinematic_Universe)',
        'Hawkeye_(Clint_Barton)', 'Clint_Barton_(Marvel_Cinematic_Universe)',
        'Black_Panther_(character)', 'T%27Challa_(Marvel_Cinematic_Universe)',
        'Doctor_Strange', 'Stephen_Strange_(Marvel_Cinematic_Universe)',
        'Scarlet_Witch', 'Wanda_Maximoff_(Marvel_Cinematic_Universe)',
        'Vision_(Marvel_Comics)', 'Vision_(Marvel_Cinematic_Universe)',
        'Ant-Man_(Scott_Lang)', 'Scott_Lang_(Marvel_Cinematic_Universe)',
        'Wasp_(character)', 'Captain_Marvel_(Marvel_Comics)', 'Carol_Danvers',
        'Star-Lord', 'Gamora', 'Drax_the_Destroyer', 'Rocket_Raccoon', 'Groot',
        'Wolverine_(character)', 'Cyclops_(Marvel_Comics)', 'Jean_Grey',
        'Storm_(Marvel_Comics)', 'Magneto', 'Professor_X', 'Deadpool',
        'Daredevil', 'Jessica_Jones', 'Luke_Cage', 'Iron_Fist_(character)',
        'Punisher', 'Ghost_Rider', 'Moon_Knight', 'She-Hulk', 'Ms._Marvel',
    ],
    
    'comics_marvel_villains': [
        'Thanos', 'Loki_(Marvel_Comics)', 'Ultron', 'Red_Skull', 'Green_Goblin',
        'Doctor_Doom', 'Magneto', 'Venom_(character)', 'Carnage_(character)',
        'Kingpin_(character)', 'Bullseye_(character)', 'Mysterio', 'Doctor_Octopus',
        'Sandman_(Marvel_Comics)', 'Electro_(Marvel_Comics)', 'Lizard_(character)',
        'Vulture_(Marvel_Comics)', 'Galactus', 'Apocalypse_(character)',
        'Kang_the_Conqueror', 'Dormammu', 'Hela_(character)', 'Killmonger_(character)',
        'Ronan_the_Accuser', 'Ego_the_Living_Planet', 'Abomination_(character)',
    ],
    
    'comics_marvel_teams': [
        'Avengers_(comics)', 'The_Avengers_(2012_film)', 'Avengers:_Age_of_Ultron',
        'Avengers:_Infinity_War', 'Avengers:_Endgame', 'X-Men', 'X-Men_(film_series)',
        'Fantastic_Four', 'Guardians_of_the_Galaxy_(film)', 'Guardians_of_the_Galaxy_Vol._2',
        'Guardians_of_the_Galaxy_Vol._3', 'Defenders_(comics)', 'Inhumans',
        'Eternals', 'Eternals_(film)', 'Thunderbolts', 'Young_Avengers',
        'West_Coast_Avengers', 'New_Avengers_(comics)', 'Dark_Avengers',
    ],
    
    'comics_marvel_films': [
        'Marvel_Cinematic_Universe', 'Iron_Man_(2008_film)', 'Iron_Man_2', 'Iron_Man_3',
        'Captain_America:_The_First_Avenger', 'Captain_America:_The_Winter_Soldier',
        'Captain_America:_Civil_War', 'Thor_(film)', 'Thor:_The_Dark_World',
        'Thor:_Ragnarok', 'Thor:_Love_and_Thunder', 'The_Incredible_Hulk_(film)',
        'Black_Widow_(film)', 'Black_Panther_(film)', 'Black_Panther:_Wakanda_Forever',
        'Doctor_Strange_(2016_film)', 'Doctor_Strange_in_the_Multiverse_of_Madness',
        'Spider-Man:_Homecoming', 'Spider-Man:_Far_From_Home', 'Spider-Man:_No_Way_Home',
        'Ant-Man_(film)', 'Ant-Man_and_the_Wasp', 'Ant-Man_and_the_Wasp:_Quantumania',
        'Captain_Marvel_(film)', 'The_Marvels', 'Shang-Chi_and_the_Legend_of_the_Ten_Rings',
        'Spider-Man:_Into_the_Spider-Verse', 'Spider-Man:_Across_the_Spider-Verse',
    ],
    
    'comics_marvel_tv': [
        'WandaVision', 'The_Falcon_and_the_Winter_Soldier', 'Loki_(TV_series)',
        'What_If...%3F_(TV_series)', 'Hawkeye_(2021_TV_series)', 'Moon_Knight_(miniseries)',
        'Ms._Marvel_(miniseries)', 'She-Hulk:_Attorney_at_Law', 'Secret_Invasion_(miniseries)',
        'Echo_(miniseries)', 'Agatha:_Darkhold_Diaries', 'Daredevil_(TV_series)',
        'Jessica_Jones_(TV_series)', 'Luke_Cage_(TV_series)', 'Iron_Fist_(TV_series)',
        'The_Defenders_(miniseries)', 'The_Punisher_(TV_series)', 'Agents_of_S.H.I.E.L.D.',
    ],
    
    # ============================================
    # COMICS: DC (~500 articles)
    # ============================================
    'comics_dc_heroes': [
        'Batman', 'Superman', 'Wonder_Woman', 'The_Flash_(comic_book)', 'Barry_Allen',
        'Wally_West', 'Green_Lantern', 'Hal_Jordan', 'John_Stewart_(character)',
        'Aquaman', 'Cyborg_(DC_Comics)', 'Shazam_(wizard)', 'Green_Arrow',
        'Martian_Manhunter', 'Hawkman', 'Hawkgirl', 'Zatanna', 'Constantine_(character)',
        'Nightwing', 'Robin_(character)', 'Dick_Grayson', 'Jason_Todd', 'Tim_Drake',
        'Damian_Wayne', 'Batgirl', 'Barbara_Gordon', 'Supergirl', 'Batwoman',
        'Blue_Beetle', 'Booster_Gold', 'Static_(DC_Comics)', 'Vixen_(character)',
    ],
    
    'comics_dc_villains': [
        'Joker_(character)', 'Lex_Luthor', 'Harley_Quinn', 'The_Riddler', 'Two-Face',
        'Penguin_(character)', 'Catwoman', 'Bane_(DC_Comics)', 'Ra%27s_al_Ghul',
        'Scarecrow_(DC_Comics)', 'Poison_Ivy_(character)', 'Mr._Freeze',
        'Darkseid', 'Doomsday_(DC_Comics)', 'General_Zod', 'Brainiac_(character)',
        'Reverse-Flash', 'Sinestro', 'Black_Manta', 'Cheetah_(character)',
        'Deathstroke', 'Black_Adam', 'Amanda_Waller', 'Steppenwolf_(comics)',
    ],
    
    'comics_dc_teams': [
        'Justice_League', 'Justice_League_(film)', 'Zack_Snyder%27s_Justice_League',
        'Justice_Society_of_America', 'Teen_Titans', 'Titans_(2018_TV_series)',
        'Young_Justice', 'Doom_Patrol', 'Doom_Patrol_(TV_series)', 'Suicide_Squad',
        'Suicide_Squad_(film)', 'The_Suicide_Squad_(film)', 'Birds_of_Prey_(team)',
        'Birds_of_Prey_(2020_film)', 'Legion_of_Super-Heroes', 'Justice_League_Dark',
    ],
    
    'comics_dc_films': [
        'DC_Extended_Universe', 'Man_of_Steel_(film)', 'Batman_v_Superman:_Dawn_of_Justice',
        'Wonder_Woman_(2017_film)', 'Wonder_Woman_1984', 'Aquaman_(film)',
        'Aquaman_and_the_Lost_Kingdom', 'Shazam!_(film)', 'Shazam!_Fury_of_the_Gods',
        'Black_Adam_(film)', 'The_Flash_(film)', 'Blue_Beetle_(film)',
        'The_Dark_Knight_Trilogy', 'Batman_Begins', 'The_Dark_Knight',
        'The_Dark_Knight_Rises', 'The_Batman_(film)', 'Joker_(2019_film)',
        'Joker:_Folie_Ã _Deux', 'Superman_(1978_film)', 'Superman_II',
        'Batman_(1989_film)', 'Batman_Returns', 'Batman_Forever', 'Batman_&_Robin',
    ],
    
    'comics_dc_tv': [
        'Arrow_(TV_series)', 'The_Flash_(2014_TV_series)', 'Supergirl_(American_TV_series)',
        'Legends_of_Tomorrow', 'Batwoman_(TV_series)', 'Black_Lightning_(TV_series)',
        'Superman_&_Lois', 'Stargirl_(TV_series)', 'Peacemaker_(TV_series)',
        'Smallville', 'Gotham_(TV_series)', 'Pennyworth_(TV_series)',
    ],
    
    # ============================================
    # COMICS: OTHER (~500 articles)
    # ============================================
    'comics_image': [
        'Spawn_(comics)', 'Spawn_(film)', 'The_Walking_Dead_(comic_book)',
        'The_Walking_Dead_(TV_series)', 'Fear_the_Walking_Dead', 'The_Walking_Dead:_World_Beyond',
        'Invincible_(comics)', 'Invincible_(TV_series)', 'Saga_(comic_book)',
        'The_Wicked_+_The_Divine', 'Paper_Girls', 'Monstress_(comics)',
        'Radiant_Black', 'Deadly_Class', 'Chew_(comics)', 'Haunt_(comics)',
    ],
    
    'comics_valiant': [
        'Valiant_Comics', 'X-O_Manowar', 'Bloodshot_(character)', 'Bloodshot_(film)',
        'Harbinger_(comics)', 'Ninjak', 'Rai_(comics)', 'Archer_&_Armstrong',
        'Faith_(character)', 'Shadowman_(comics)', 'Eternal_Warrior',
    ],
    
    'comics_indie': [
        'Hellboy', 'Hellboy_(2004_film)', 'Hellboy_II:_The_Golden_Army',
        'Hellboy_(2019_film)', 'Teenage_Mutant_Ninja_Turtles', 'Leonardo_(Teenage_Mutant_Ninja_Turtles)',
        'Donatello_(Teenage_Mutant_Ninja_Turtles)', 'Raphael_(Teenage_Mutant_Ninja_Turtles)',
        'Michelangelo_(Teenage_Mutant_Ninja_Turtles)', 'The_Mask_(comics)',
        'Sin_City', 'Sin_City_(film)', '300_(comics)', '300_(film)',
        'The_Boys_(comics)', 'The_Boys_(TV_series)', 'Watchmen', 'Watchmen_(film)',
        'Watchmen_(TV_series)', 'V_for_Vendetta', 'V_for_Vendetta_(film)',
        'Kick-Ass_(comic_book)', 'Kick-Ass_(film)', 'Scott_Pilgrim', 'Bone_(comics)',
    ],
    
    # ============================================
    # HISTORY (~1,200 articles)
    # ============================================
    'history_ancient_rome': [
        'Ancient_Rome', 'Roman_Empire', 'Roman_Republic', 'Julius_Caesar',
        'Augustus', 'Nero', 'Caligula', 'Marcus_Aurelius', 'Constantine_the_Great',
        'Cleopatra', 'Mark_Antony', 'Cicero', 'Pompey', 'Spartacus',
        'Roman_Senate', 'Roman_legion', 'Colosseum', 'Roman_Forum', 'Pantheon,_Rome',
        'Pompeii', 'Hadrian%27s_Wall', 'Roman_aqueduct', 'Gladiator', 'Praetorian_Guard',
        'Fall_of_the_Western_Roman_Empire', 'Byzantine_Empire', 'Punic_Wars',
        'Battle_of_Cannae', 'Siege_of_Alesia', 'Battle_of_Actium',
    ],
    
    'history_ancient_greece': [
        'Ancient_Greece', 'Classical_Athens', 'Sparta', 'Alexander_the_Great',
        'Pericles', 'Socrates', 'Plato', 'Aristotle', 'Pythagoras', 'Archimedes',
        'Herodotus', 'Thucydides', 'Homer', 'Hippocrates', 'Leonidas_I',
        'Battle_of_Thermopylae', 'Battle_of_Marathon', 'Battle_of_Salamis',
        'Peloponnesian_War', 'Trojan_War', 'Parthenon', 'Acropolis_of_Athens',
        'Oracle_of_Delphi', 'Olympic_Games', 'Greek_philosophy', 'Greek_mythology',
    ],
    
    'history_ancient_egypt': [
        'Ancient_Egypt', 'Pharaoh', 'Tutankhamun', 'Cleopatra', 'Ramesses_II',
        'Akhenaten', 'Nefertiti', 'Hatshepsut', 'Khufu', 'Great_Pyramid_of_Giza',
        'Sphinx', 'Valley_of_the_Kings', 'Egyptian_pyramids', 'Rosetta_Stone',
        'Egyptian_hieroglyphs', 'Mummy', 'Book_of_the_Dead', 'Egyptian_temple',
        'Battle_of_Kadesh', 'New_Kingdom_of_Egypt', 'Old_Kingdom_of_Egypt',
    ],
    
    'history_medieval': [
        'Middle_Ages', 'Medieval_warfare', 'Knight', 'Castle', 'Crusades',
        'First_Crusade', 'Third_Crusade', 'Richard_I_of_England', 'Saladin',
        'Charlemagne', 'William_the_Conqueror', 'Battle_of_Hastings',
        'Norman_conquest_of_England', 'Magna_Carta', 'Hundred_Years%27_War',
        'Battle_of_Agincourt', 'Joan_of_Arc', 'Black_Death', 'Feudalism',
        'Holy_Roman_Empire', 'Byzantine_Empire', 'Vikings', 'Viking_Age',
    ],
    
    'history_renaissance': [
        'Renaissance', 'Italian_Renaissance', 'Leonardo_da_Vinci', 'Michelangelo',
        'Raphael', 'Mona_Lisa', 'The_Last_Supper_(Leonardo)', 'David_(Michelangelo)',
        'Sistine_Chapel_ceiling', 'NiccolÃ²_Machiavelli', 'The_Prince',
        'Galileo_Galilei', 'Johannes_Gutenberg', 'Printing_press',
        'Age_of_Discovery', 'Christopher_Columbus', 'Ferdinand_Magellan',
        'Vasco_da_Gama', 'Protestant_Reformation', 'Martin_Luther',
    ],
    
    'history_world_war_1': [
        'World_War_I', 'Trench_warfare', 'Battle_of_the_Somme', 'Battle_of_Verdun',
        'Battle_of_Passchendaele', 'Western_Front_(World_War_I)', 'Eastern_Front_(World_War_I)',
        'Treaty_of_Versailles', 'Assassination_of_Archduke_Franz_Ferdinand',
        'Russian_Revolution', 'Vladimir_Lenin', 'Bolsheviks', 'Russian_Civil_War',
        'Woodrow_Wilson', 'League_of_Nations', 'Armistice_of_11_November_1918',
    ],
    
    'history_world_war_2': [
        'World_War_II', 'Adolf_Hitler', 'Nazi_Germany', 'Winston_Churchill',
        'Franklin_D._Roosevelt', 'Joseph_Stalin', 'Benito_Mussolini',
        'Dwight_D._Eisenhower', 'George_S._Patton', 'Bernard_Montgomery',
        'Erwin_Rommel', 'Operation_Barbarossa', 'Battle_of_Stalingrad',
        'Battle_of_Britain', 'The_Blitz', 'D-Day', 'Operation_Overlord',
        'Battle_of_the_Bulge', 'Battle_of_Midway', 'Attack_on_Pearl_Harbor',
        'Atomic_bombings_of_Hiroshima_and_Nagasaki', 'Manhattan_Project',
        'Holocaust', 'Nazi_concentration_camps', 'Anne_Frank', 'Normandy_landings',
        'Battle_of_Iwo_Jima', 'Battle_of_Okinawa', 'Eastern_Front_(World_War_II)',
        'Western_Front_(World_War_II)', 'Pacific_War', 'Battle_of_Berlin',
    ],
    
    'history_cold_war': [
        'Cold_War', 'Space_Race', 'Cuban_Missile_Crisis', 'Berlin_Wall',
        'Fall_of_the_Berlin_Wall', 'Iron_Curtain', 'Korean_War', 'Vietnam_War',
        'Bay_of_Pigs_Invasion', 'Soviet_Union', 'Joseph_Stalin', 'Nikita_Khrushchev',
        'Leonid_Brezhnev', 'Mikhail_Gorbachev', 'Glasnost', 'Perestroika',
        'Dissolution_of_the_Soviet_Union', 'John_F._Kennedy', 'Ronald_Reagan',
        'NATO', 'Warsaw_Pact', 'Marshall_Plan', 'Truman_Doctrine',
    ],
    
    'history_american': [
        'American_Revolution', 'Declaration_of_Independence', 'George_Washington',
        'Thomas_Jefferson', 'Benjamin_Franklin', 'American_Civil_War',
        'Abraham_Lincoln', 'Emancipation_Proclamation', 'Battle_of_Gettysburg',
        'Ulysses_S._Grant', 'Robert_E._Lee', 'Reconstruction_era', 'Wild_West',
        'Great_Depression', 'Dust_Bowl', 'New_Deal', 'Civil_rights_movement',
        'Martin_Luther_King_Jr.', 'Rosa_Parks', 'Malcolm_X', 'Watergate_scandal',
        'September_11_attacks', 'War_on_Terror', 'Iraq_War', 'Afghanistan_War',
    ],
    
    'history_explorers': [
        'Age_of_Discovery', 'Christopher_Columbus', 'Vasco_da_Gama',
        'Ferdinand_Magellan', 'HernÃ¡n_CortÃ©s', 'Francisco_Pizarro',
        'Marco_Polo', 'Lewis_and_Clark_Expedition', 'Ernest_Shackleton',
        'Robert_Falcon_Scott', 'Roald_Amundsen', 'Edmund_Hillary',
        'Neil_Armstrong', 'Yuri_Gagarin', 'Apollo_11', 'Space_Shuttle',
    ],
    
    'history_figures': [
        'Napoleon', 'Genghis_Khan', 'Attila', 'Hannibal', 'Sun_Tzu',
        'Confucius', 'Buddha', 'Muhammad', 'Jesus', 'Moses',
        'Elizabeth_I', 'Queen_Victoria', 'Catherine_the_Great', 'Marie_Antoinette',
        'Cleopatra', 'Helen_of_Troy', 'Boudica', 'Frederick_the_Great',
        'Peter_the_Great', 'Ivan_the_Terrible', 'Vlad_the_Impaler',
    ],
    
    # ============================================
    # RELIGION & MYTHOLOGY (~800 articles)
    # ============================================
    'religion_christianity': [
        'Christianity', 'Jesus', 'Bible', 'New_Testament', 'Old_Testament',
        'Gospel', 'Apostle', 'Paul_the_Apostle', 'Saint_Peter', 'Mary,_mother_of_Jesus',
        'Crucifixion_of_Jesus', 'Resurrection_of_Jesus', 'Easter', 'Christmas',
        'Catholic_Church', 'Pope', 'Vatican_City', 'Protestantism',
        'Martin_Luther', 'Reformation', 'Eastern_Orthodox_Church', 'Anglican_Communion',
        'Ten_Commandments', 'Lord%27s_Prayer', 'Sermon_on_the_Mount',
    ],
    
    'religion_islam': [
        'Islam', 'Muhammad', 'Quran', 'Allah', 'Five_Pillars_of_Islam',
        'Hajj', 'Ramadan', 'Mecca', 'Medina', 'Kaaba', 'Mosque',
        'Sunni_Islam', 'Shia_Islam', 'Caliphate', 'Islamic_Golden_Age',
        'Saladin', 'Ottoman_Empire', 'Sufism', 'Islamic_calendar',
    ],
    
    'religion_judaism': [
        'Judaism', 'Torah', 'Hebrew_Bible', 'Talmud', 'Rabbi',
        'Synagogue', 'Moses', 'Abraham', 'David', 'Solomon',
        'Temple_in_Jerusalem', 'Western_Wall', 'Passover', 'Hanukkah',
        'Yom_Kippur', 'Bar_and_bat_mitzvah', 'Hasidic_Judaism',
    ],
    
    'religion_eastern': [
        'Buddhism', 'Gautama_Buddha', 'Dharma', 'Karma', 'Nirvana',
        'Four_Noble_Truths', 'Noble_Eightfold_Path', 'Dalai_Lama',
        'Zen', 'Tibetan_Buddhism', 'Hinduism', 'Brahma', 'Vishnu',
        'Shiva', 'Vedas', 'Bhagavad_Gita', 'Yoga', 'Reincarnation',
        'Diwali', 'Holi', 'Sikhism', 'Guru_Nanak', 'Golden_Temple',
    ],
    
    'mythology_greek': [
        'Greek_mythology', 'Zeus', 'Hera', 'Poseidon', 'Hades',
        'Athena', 'Apollo', 'Artemis', 'Ares', 'Aphrodite',
        'Hephaestus', 'Hermes', 'Demeter', 'Dionysus', 'Hestia',
        'Persephone', 'Hades_(place)', 'Mount_Olympus', 'Titan_(mythology)',
        'Prometheus', 'Atlas_(mythology)', 'Hercules', 'Perseus',
        'Theseus', 'Jason', 'Medusa', 'Minotaur', 'Centaur',
        'Cyclops', 'Pegasus', 'Chimera_(mythology)', 'Hydra_(mythology)',
        'Cerberus', 'Pandora', 'Achilles', 'Odysseus', 'Trojan_Horse',
    ],
    
    'mythology_norse': [
        'Norse_mythology', 'Odin', 'Thor', 'Loki', 'Freya',
        'Frigg', 'Baldur', 'TÃ½r', 'Heimdallr', 'Hel_(being)',
        'Valkyrie', 'Asgard', 'Midgard', 'JÃ¶tunheimr', 'Valhalla',
        'Yggdrasil', 'RagnarÃ¶k', 'MjÃ¶lnir', 'Fenrir', 'JÃ¶rmungandr',
        'Sleipnir', 'BifrÃ¶st', 'Einherjar', 'Norns', 'Skald',
    ],
    
    'mythology_egyptian': [
        'Egyptian_mythology', 'Ra', 'Osiris', 'Isis', 'Horus',
        'Set_(deity)', 'Anubis', 'Thoth', 'Bastet', 'Sekhmet',
        'Ptah', 'Atum', 'Nut_(goddess)', 'Geb_(god)', 'Amun',
        'Sobek', 'Egyptian_soul', 'Duat', 'Weighing_of_the_Heart',
    ],
    
    'mythology_other': [
        'Celtic_mythology', 'Mesopotamian_mythology', 'Chinese_mythology',
        'Japanese_mythology', 'Hindu_mythology', 'Aztec_mythology',
        'Maya_mythology', 'Inca_mythology', 'Slavic_mythology',
    ],
    
    # ============================================
    # TECHNOLOGY (~1,000 articles)
    # ============================================
    'tech_computers': [
        'Computer', 'Personal_computer', 'Laptop', 'Smartphone', 'Tablet_computer',
        'Central_processing_unit', 'Graphics_processing_unit', 'Random-access_memory',
        'Hard_disk_drive', 'Solid-state_drive', 'Motherboard', 'Operating_system',
        'Microsoft_Windows', 'MacOS', 'Linux', 'Unix', 'Android_(operating_system)',
        'IOS', 'Programming_language', 'Python_(programming_language)',
        'Java_(programming_language)', 'C++', 'JavaScript', 'C_(programming_language)',
        'HTML', 'CSS', 'SQL', 'Compiler', 'Algorithm', 'Data_structure',
        'Binary_number', 'Hexadecimal', 'Assembly_language', 'Machine_code',
    ],
    
    'tech_internet': [
        'Internet', 'World_Wide_Web', 'Web_browser', 'Email', 'Social_media',
        'Search_engine', 'Cloud_computing', 'Server_(computing)', 'Clientâ€“server_model',
        'HTTP', 'HTTPS', 'TCP/IP', 'Domain_Name_System', 'IP_address',
        'Router', 'Wi-Fi', '5G', 'Ethernet', 'Fiber-optic_communication',
        'Encryption', 'Cryptography', 'Cybersecurity', 'Firewall_(computing)',
        'Computer_virus', 'Malware', 'Ransomware', 'Phishing', 'VPN',
    ],
    
    'tech_companies': [
        'Apple_Inc.', 'Microsoft', 'Google', 'Amazon_(company)', 'Meta_Platforms',
        'Facebook', 'Instagram', 'WhatsApp', 'Twitter', 'X_(social_media)',
        'Tesla,_Inc.', 'SpaceX', 'IBM', 'Intel', 'AMD', 'Nvidia',
        'Samsung', 'Sony', 'Dell', 'HP_Inc.', 'Lenovo', 'Cisco_Systems',
        'Oracle_Corporation', 'Netflix', 'Adobe_Inc.', 'Salesforce',
        'PayPal', 'eBay', 'Alibaba_Group', 'Tencent', 'Baidu',
    ],
    
    'tech_ai': [
        'Artificial_intelligence', 'Machine_learning', 'Deep_learning',
        'Neural_network_(machine_learning)', 'Natural_language_processing',
        'Computer_vision', 'Robotics', 'Chatbot', 'GPT-3', 'ChatGPT',
        'DALL-E', 'Midjourney', 'Stable_Diffusion', 'Large_language_model',
        'Turing_test', 'AI_alignment', 'Artificial_general_intelligence',
    ],
    
    'tech_space': [
        'Space_exploration', 'NASA', 'International_Space_Station', 'Apollo_program',
        'Apollo_11', 'Neil_Armstrong', 'Buzz_Aldrin', 'Moon_landing',
        'Mars_rover', 'Curiosity_(rover)', 'Perseverance_(rover)', 'Opportunity_(rover)',
        'Hubble_Space_Telescope', 'James_Webb_Space_Telescope', 'Voyager_1',
        'Voyager_2', 'SpaceX', 'Elon_Musk', 'Falcon_9', 'Starship_(spacecraft)',
        'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto',
        'Sun', 'Moon', 'Milky_Way', 'Solar_System', 'Exoplanet',
    ],
    
    'tech_inventions': [
        'Telephone', 'Telegraph', 'Radio', 'Television', 'Light_bulb',
        'Electric_motor', 'Internal_combustion_engine', 'Steam_engine',
        'Printing_press', 'Camera', 'Microscope', 'Telescope', 'X-ray',
        'Transistor', 'Integrated_circuit', 'Microprocessor', 'Laser',
        'Nuclear_reactor', 'Nuclear_weapon', 'Atomic_bomb', 'Hydrogen_bomb',
    ],
    
    # ============================================
    # VIDEO GAMES (~1,500 articles)
    # ============================================
    'games_nintendo': [
        'Nintendo', 'Super_Mario', 'Mario', 'Luigi', 'Princess_Peach',
        'Bowser', 'Yoshi', 'Donkey_Kong', 'Super_Mario_Bros.', 'Super_Mario_64',
        'Super_Mario_Galaxy', 'Super_Mario_Odyssey', 'The_Legend_of_Zelda',
        'Link_(The_Legend_of_Zelda)', 'Princess_Zelda', 'Ganon',
        'The_Legend_of_Zelda:_Ocarina_of_Time', 'The_Legend_of_Zelda:_Breath_of_the_Wild',
        'The_Legend_of_Zelda:_Tears_of_the_Kingdom', 'PokÃ©mon', 'Pikachu',
        'PokÃ©mon_Red,_Blue,_and_Yellow', 'PokÃ©mon_Gold_and_Silver',
        'PokÃ©mon_Sword_and_Shield', 'Metroid', 'Samus_Aran', 'Kirby_(character)',
        'Star_Fox', 'Animal_Crossing', 'Splatoon', 'Fire_Emblem',
    ],
    
    'games_playstation': [
        'PlayStation', 'PlayStation_2', 'PlayStation_3', 'PlayStation_4',
        'PlayStation_5', 'God_of_War_(2018_video_game)', 'Kratos_(God_of_War)',
        'The_Last_of_Us', 'The_Last_of_Us_Part_II', 'Uncharted', 'Nathan_Drake_(character)',
        'Horizon_Zero_Dawn', 'Horizon_Forbidden_West', 'Spider-Man_(2018_video_game)',
        'Ghost_of_Tsushima', 'Bloodborne', 'Demon%27s_Souls', 'Gran_Turismo_(series)',
        'Final_Fantasy_VII', 'Final_Fantasy_VII_Remake', 'Ratchet_&_Clank',
    ],
    
    'games_xbox': [
        'Xbox', 'Xbox_360', 'Xbox_One', 'Xbox_Series_X_and_Series_S',
        'Halo_(franchise)', 'Master_Chief_(Halo)', 'Halo:_Combat_Evolved',
        'Halo_2', 'Halo_3', 'Halo_Infinite', 'Gears_of_War', 'Forza_(series)',
        'Fable_(video_game_series)', 'Sea_of_Thieves', 'Starfield_(video_game)',
    ],
    
    'games_franchises': [
        'Call_of_Duty', 'Call_of_Duty:_Modern_Warfare', 'Call_of_Duty:_Black_Ops',
        'Call_of_Duty:_Warzone', 'Grand_Theft_Auto', 'Grand_Theft_Auto_V',
        'Red_Dead_Redemption', 'Red_Dead_Redemption_2', 'Minecraft',
        'Fortnite', 'Roblox', 'The_Elder_Scrolls', 'The_Elder_Scrolls_V:_Skyrim',
        'Fallout_(series)', 'Fallout_3', 'Fallout_4', 'Fallout:_New_Vegas',
        'The_Witcher_(video_game_series)', 'The_Witcher_3:_Wild_Hunt',
        'Assassin%27s_Creed', 'Assassin%27s_Creed_II', 'Assassin%27s_Creed_Valhalla',
        'Dark_Souls', 'Dark_Souls_III', 'Elden_Ring', 'Sekiro:_Shadows_Die_Twice',
        'Resident_Evil', 'Resident_Evil_4', 'Resident_Evil_Village',
        'Silent_Hill', 'Metal_Gear', 'Metal_Gear_Solid', 'Death_Stranding',
    ],
    
    'games_classic': [
        'Pac-Man', 'Space_Invaders', 'Donkey_Kong_(video_game)', 'Tetris',
        'Super_Mario_Bros.', 'Sonic_the_Hedgehog', 'Street_Fighter_II',
        'Mortal_Kombat', 'Doom_(1993_video_game)', 'Quake_(video_game)',
        'Half-Life_(video_game)', 'Counter-Strike', 'Portal_(video_game)',
        'BioShock', 'System_Shock_2', 'Deus_Ex_(video_game)', 'Thief:_The_Dark_Project',
    ],
    
    'games_modern': [
        'Overwatch', 'League_of_Legends', 'Dota_2', 'Valorant',
        'Apex_Legends', 'Destiny_2', 'Tom_Clancy%27s_Rainbow_Six_Siege',
        'Battlefield_(video_game_series)', 'Battlefield_2042', 'Titanfall_2',
        'Warframe', 'Monster_Hunter:_World', 'Baldur%27s_Gate_3',
        'Cyberpunk_2077', 'Hogwarts_Legacy', 'Final_Fantasy_XVI',
    ],
    
    # ============================================
    # THEME PARKS (~500 articles)
    # ============================================
    'parks_disney_world': [
        'Walt_Disney_World', 'Magic_Kingdom', 'Epcot', 'Disney%27s_Hollywood_Studios',
        'Disney%27s_Animal_Kingdom', 'Cinderella_Castle', 'Spaceship_Earth_(Epcot)',
        'The_Haunted_Mansion', 'Pirates_of_the_Caribbean_(attraction)',
        'Big_Thunder_Mountain_Railroad', 'Space_Mountain', 'Splash_Mountain',
        'Avatar_Flight_of_Passage', 'Star_Wars:_Galaxy%27s_Edge',
        'Star_Wars:_Rise_of_the_Resistance', 'Millennium_Falcon:_Smugglers_Run',
        'Guardians_of_the_Galaxy:_Cosmic_Rewind', 'TRON_Lightcycle_/_Run',
        'Seven_Dwarfs_Mine_Train', 'Expedition_Everest', 'Kilimanjaro_Safaris',
    ],
    
    'parks_disneyland': [
        'Disneyland', 'Disney_California_Adventure', 'Sleeping_Beauty_Castle',
        'Matterhorn_Bobsleds', 'Indiana_Jones_Adventure', 'Star_Tours',
        'Radiator_Springs_Racers', 'Guardians_of_the_Galaxy_â€“_Mission:_Breakout!',
        'Incredicoaster', 'Soarin%27', 'Toy_Story_Midway_Mania!',
    ],
    
    'parks_universal': [
        'Universal_Studios_Hollywood', 'Universal_Orlando_Resort',
        'Universal_Studios_Florida', 'Islands_of_Adventure', 'Universal%27s_Volcano_Bay',
        'The_Wizarding_World_of_Harry_Potter', 'Harry_Potter_and_the_Forbidden_Journey',
        'Hagrid%27s_Magical_Creatures_Motorbike_Adventure', 'The_Amazing_Adventures_of_Spider-Man',
        'Jurassic_World_VelociCoaster', 'Jurassic_Park_River_Adventure',
        'Revenge_of_the_Mummy_(roller_coaster)', 'Transformers:_The_Ride_3D',
        'Harry_Potter_and_the_Escape_from_Gringotts', 'Hollywood_Rip_Ride_Rockit',
        'The_Incredible_Hulk_Coaster', 'Doctor_Doom%27s_Fearfall',
        'Skull_Island:_Reign_of_Kong', 'King_Kong_(Universal_Studios_Hollywood)',
    ],
    
    'parks_other': [
        'Six_Flags', 'Cedar_Point', 'Busch_Gardens', 'SeaWorld', 'Knott%27s_Berry_Farm',
        'Dollywood', 'Hersheypark', 'Kings_Island', 'Carowinds', 'Silver_Dollar_City',
        'Europa-Park', 'Alton_Towers', 'Legoland', 'Tokyo_Disneyland', 'Disneyland_Paris',
    ],
    
    'parks_attractions': [
        'Roller_coaster', 'Steel_Vengeance', 'Fury_325', 'Millennium_Force',
        'Top_Thrill_Dragster', 'Kingda_Ka', 'Formula_Rossa', 'The_Smiler',
        'X2_(roller_coaster)', 'Twisted_Colossus', 'Steel_Dragon_2000',
        'Log_flume_(ride)', 'Drop_tower', 'Ferris_wheel', 'Carousel',
    ],
    
    'parks_imagineers': [
        'Walt_Disney', 'Walt_Disney_Imagineering', 'Disneyland_Railroad',
        'Disney_Monorail_System', 'PeopleMover', 'Skyway_(Disney)', 'Audio-Animatronics',
    ],
    
    # ============================================
    # POP CULTURE & ENTERTAINMENT (~700 articles)
    # ============================================
    'popculture_films': [
        'The_Shawshank_Redemption', 'The_Godfather', 'The_Godfather_Part_II',
        'Pulp_Fiction', 'The_Dark_Knight', 'Fight_Club', 'Forrest_Gump',
        'Goodfellas', 'The_Matrix', 'Inception', 'Interstellar_(film)',
        'Parasite_(2019_film)', 'Schindler%27s_List', 'The_Silence_of_the_Lambs_(film)',
        'Saving_Private_Ryan', 'The_Green_Mile_(film)', 'Se7en', 'The_Usual_Suspects',
        'Memento_(film)', 'The_Prestige_(film)', 'Gladiator_(2000_film)',
        'Braveheart', 'The_Departed', 'No_Country_for_Old_Men', 'There_Will_Be_Blood',
    ],
    
    'popculture_tv': [
        'Breaking_Bad', 'The_Sopranos', 'The_Wire', 'Mad_Men', 'True_Detective',
        'Better_Call_Saul', 'Fargo_(TV_series)', 'Sherlock_(TV_series)',
        'Westworld_(TV_series)', 'Succession_(TV_series)', 'The_Boys_(TV_series)',
        'The_Mandalorian', 'Yellowstone_(American_TV_series)', 'House_of_the_Dragon',
        'The_Last_of_Us_(TV_series)', 'Andor_(TV_series)', 'Wednesday_(TV_series)',
        'Stranger_Things', 'The_Crown_(TV_series)', 'Bridgerton', 'Squid_Game',
    ],
    
    'popculture_directors': [
        'Steven_Spielberg', 'Martin_Scorsese', 'Quentin_Tarantino', 'Christopher_Nolan',
        'Stanley_Kubrick', 'Alfred_Hitchcock', 'Francis_Ford_Coppola',
        'Ridley_Scott', 'James_Cameron', 'George_Lucas', 'Peter_Jackson',
        'Denis_Villeneuve', 'Guillermo_del_Toro', 'Wes_Anderson', 'Paul_Thomas_Anderson',
        'David_Fincher', 'Darren_Aronofsky', 'The_Coen_Brothers', 'Bong_Joon-ho',
    ],
    
    'popculture_animation': [
        'Pixar', 'Toy_Story', 'Finding_Nemo', 'The_Incredibles', 'Up_(2009_film)',
        'WALL-E', 'Inside_Out_(2015_film)', 'Coco_(2017_film)', 'Soul_(2020_film)',
        'Disney_Animation', 'The_Lion_King', 'Beauty_and_the_Beast_(1991_film)',
        'Aladdin_(1992_Disney_film)', 'Frozen_(2013_film)', 'Moana_(2016_film)',
        'Encanto', 'Zootopia', 'Big_Hero_6_(film)', 'Wreck-It_Ralph',
        'Studio_Ghibli', 'Spirited_Away', 'My_Neighbor_Totoro', 'Princess_Mononoke',
        'Howl%27s_Moving_Castle_(film)', 'Hayao_Miyazaki', 'DreamWorks_Animation',
        'Shrek', 'Kung_Fu_Panda', 'How_to_Train_Your_Dragon_(film)',
    ],
    
    'popculture_music': [
        'The_Beatles', 'Led_Zeppelin', 'Pink_Floyd', 'Queen_(band)',
        'The_Rolling_Stones', 'David_Bowie', 'Michael_Jackson', 'Prince_(musician)',
        'Madonna', 'Elvis_Presley', 'Bob_Dylan', 'Jimi_Hendrix',
        'Nirvana_(band)', 'Radiohead', 'Metallica', 'AC/DC', 'Iron_Maiden',
        'Black_Sabbath', 'Guns_N%27_Roses', 'U2', 'Coldplay', 'Linkin_Park',
    ],
    
    # ============================================
    # PRO WRESTLING (~800 articles)
    # ============================================
    'wrestling_wwe_legends': [
        'WWE', 'World_Wrestling_Entertainment', 'Hulk_Hogan', 'The_Undertaker',
        'Stone_Cold_Steve_Austin', 'The_Rock_(Dwayne_Johnson)', 'Shawn_Michaels',
        'Bret_Hart', 'Ric_Flair', 'Macho_Man_Randy_Savage', 'Ultimate_Warrior',
        'Andre_the_Giant', 'Jake_Roberts', 'Roddy_Piper', 'Big_Van_Vader',
        'Yokozuna_(wrestler)', 'Lex_Luger', 'Sting_(wrestler)', 'Goldberg_(wrestler)',
        'Eddie_Guerrero', 'Chris_Benoit', 'Kurt_Angle', 'Brock_Lesnar',
        'John_Cena', 'Batista_(wrestler)', 'Rey_Mysterio', 'Edge_(wrestler)',
        'Christian_(wrestler)', 'Chris_Jericho', 'CM_Punk', 'Daniel_Bryan',
    ],
    
    'wrestling_wwe_current': [
        'Roman_Reigns', 'Seth_Rollins', 'Cody_Rhodes', 'Drew_McIntyre',
        'Bobby_Lashley', 'Randy_Orton', 'AJ_Styles', 'Kevin_Owens',
        'Sami_Zayn', 'Finn_BÃ¡lor', 'Damian_Priest', 'Rhea_Ripley',
        'Becky_Lynch', 'Charlotte_Flair', 'Bianca_Belair', 'Bayley_(wrestler)',
        'Asuka_(wrestler)', 'Sasha_Banks', 'Alexa_Bliss', 'Liv_Morgan',
        'LA_Knight', 'Gunther_(wrestler)', 'Sheamus', 'Riddle_(wrestler)',
    ],
    
    'wrestling_wcw': [
        'World_Championship_Wrestling', 'WCW', 'Monday_Night_Wars', 'Eric_Bischoff',
        'New_World_Order_(professional_wrestling)', 'Hollywood_Hogan', 'Kevin_Nash',
        'Scott_Hall', 'Diamond_Dallas_Page', 'Booker_T_(wrestler)', 'Scott_Steiner',
        'Rick_Steiner', 'Lex_Luger', 'Sid_Vicious_(wrestler)', 'Big_Show',
        'Chris_Benoit', 'Eddie_Guerrero', 'Dean_Malenko', 'Perry_Saturn',
        'Rey_Mysterio', 'Juventud_Guerrera', 'Psychosis_(wrestler)', 'Ãšltimo_DragÃ³n',
    ],
    
    'wrestling_ecw': [
        'Extreme_Championship_Wrestling', 'ECW', 'Paul_Heyman', 'Tommy_Dreamer',
        'The_Sandman_(wrestler)', 'Raven_(wrestler)', 'Sabu_(wrestler)',
        'Rob_Van_Dam', 'Taz_(wrestler)', 'The_Dudley_Boyz', 'Bubba_Ray_Dudley',
        'D-Von_Dudley', 'Rhyno', 'Spike_Dudley', 'Shane_Douglas',
    ],
    
    'wrestling_aew': [
        'All_Elite_Wrestling', 'AEW', 'Tony_Khan', 'Cody_Rhodes', 'The_Young_Bucks',
        'Kenny_Omega', 'Jon_Moxley', 'Chris_Jericho', 'CM_Punk', 'Bryan_Danielson',
        'Adam_Cole', 'MJF_(wrestler)', 'Jade_Cargill', 'Britt_Baker',
        'Thunder_Rosa', 'Hangman_Adam_Page', 'Orange_Cassidy', 'Darby_Allin',
        'Sting_(wrestler)', 'Samoa_Joe', 'Will_Ospreay', 'Mercedes_MonÃ©',
    ],
    
    'wrestling_international': [
        'New_Japan_Pro-Wrestling', 'NJPW', 'Kazuchika_Okada', 'Hiroshi_Tanahashi',
        'Shinsuke_Nakamura', 'Tomohiro_Ishii', 'Tetsuya_Naito', 'Will_Ospreay',
        'Zack_Sabre_Jr.', 'AAA_(wrestling_promotion)', 'Lucha_Libre_AAA_Worldwide',
        'Lucha_libre', 'Rey_Mysterio', 'Psicosis_(wrestler)', 'Impact_Wrestling',
        'TNA_(wrestling_promotion)', 'Kurt_Angle', 'AJ_Styles', 'Samoa_Joe',
    ],
    
    'wrestling_families': [
        'The_Hart_Family', 'Bret_Hart', 'Owen_Hart', 'British_Bulldog',
        'Jim_Neidhart', 'Natalya_Neidhart', 'Tyson_Kidd', 'The_McMahon_Family',
        'Vince_McMahon', 'Shane_McMahon', 'Stephanie_McMahon', 'Triple_H',
        'The_Rock_(Dwayne_Johnson)', 'Roman_Reigns', 'The_Usos', 'Rikishi',
        'Yokozuna_(wrestler)', 'Umaga_(wrestler)', 'The_Guerrero_Family',
        'Eddie_Guerrero', 'Chavo_Guerrero_Jr.', 'Vickie_Guerrero',
        'The_Von_Erich_Family', 'Fritz_Von_Erich', 'Kerry_Von_Erich',
    ],
    
    'wrestling_stables': [
        'D-Generation_X', 'Triple_H', 'Shawn_Michaels', 'New_World_Order_(professional_wrestling)',
        'The_Four_Horsemen_(professional_wrestling)', 'Ric_Flair', 'Arn_Anderson',
        'Evolution_(professional_wrestling)', 'The_Shield_(professional_wrestling)',
        'Roman_Reigns', 'Seth_Rollins', 'Dean_Ambrose', 'The_Wyatt_Family',
        'Bray_Wyatt', 'Erick_Rowan', 'Luke_Harper', 'Braun_Strowman',
        'The_Bloodline_(professional_wrestling)', 'The_Bullet_Club', 'Judgment_Day_(professional_wrestling)',
    ],

    'wrestling_terms': [
        'Professional_wrestling', 'Kayfabe', 'Heel_(professional_wrestling)',
        'Face_(professional_wrestling)', 'Finishing_move', 'Suplex', 'Powerbomb',
        'Piledriver_(professional_wrestling)', 'DDT_(professional_wrestling)',
        'Stone_Cold_Stunner', 'Rock_Bottom', 'People%27s_Elbow', 'Tombstone_Piledriver',
        'Spear_(professional_wrestling)', 'Sweet_Chin_Music', 'Figure-four_leglock',
        '619_(wrestling_move)', 'RKO_(wrestling_move)', 'F-5_(wrestling_move)',
    ],
}
# Fun Facts Article Lists - ~200 Fascinating Articles
FUNFACTS_ARTICLES = {
    'funfacts_weird_history': [
        'The_Great_Emu_War', 'Dancing_Plague_of_1518', 'London_Beer_Flood',
        'War_of_the_Bucket', 'Cadaver_Synod', 'Defenestrations_of_Prague',
        'Great_Molasses_Flood', 'Night_of_the_Big_Wind', 'Year_Without_a_Summer',
        'Tunguska_event', 'Dyatlov_Pass_incident', 'Mary_Celeste',
        'Kentucky_meat_shower', 'Valentich_disappearance', 'Mad_Honey_Disease',
    ],

    'funfacts_unusual_animals': [
        'Tardigrade', 'Mantis_shrimp', 'Turritopsis_dohrnii', 'Axolotl',
        'Platypus', 'Blobfish', 'Aye-aye', 'Narwhal', 'Pangolin',
        'Okapi', 'Star-nosed_mole', 'Naked_mole-rat', 'Goblin_shark',
        'Vampire_squid', 'Giant_isopod', 'Pistol_shrimp', 'Mimic_octopus',
        'Glass_frog', 'Purple_frog', 'Hercules_beetle', 'Pink_fairy_armadillo',
        'Leafy_seadragon', 'Honey_badger', 'Shoebill', 'Kakapo',
    ],

    'funfacts_strange_science': [
        'Quantum_entanglement', 'Schrödinger%27s_cat', 'Double-slit_experiment',
        'Fermi_paradox', 'Hawking_radiation', 'Antimatter', 'Dark_matter',
        'Graphene', 'Aerogel', 'Superfluid', 'Bose–Einstein_condensate',
        'Ferrofluid', 'Leidenfrost_effect', 'Mpemba_effect',
        'Sonoluminescence', 'Ball_lightning', 'Perpetual_motion',
    ],

    'funfacts_bizarre_phenomena': [
        'Raining_animals', 'Red_rain_in_Kerala', 'Star_jelly',
        'Earthquake_light', 'Will-o%27-the-wisp', 'St._Elmo%27s_fire',
        'Sun_dog', 'Light_pillar', 'Fata_Morgana_(mirage)', 'Green_flash',
        'Moonbow', 'Noctilucent_cloud', 'Fallstreak_hole', 'Morning_Glory_cloud',
    ],

    'funfacts_world_records': [
        'Mount_Everest', 'Mariana_Trench', 'Blue_whale', 'Peregrine_falcon',
        'Cheetah', 'General_Sherman_(tree)', 'Burj_Khalifa', 'Great_Wall_of_China',
        'Three_Gorges_Dam', 'Golden_Gate_Bridge', 'Channel_Tunnel',
    ],

    'funfacts_extinct_creatures': [
        'Dodo', 'Thylacine', 'Woolly_mammoth', 'Smilodon', 'Irish_elk',
        'Tyrannosaurus', 'Velociraptor', 'Triceratops', 'Pteranodon',
        'Megalodon', 'Anomalocaris', 'Trilobite',
    ],

    'funfacts_weird_food': [
        'Hákarl', 'Surströmming', 'Casu_martzu', 'Century_egg', 'Balut',
        'Fugu', 'Durian', 'Ghost_pepper', 'Carolina_Reaper', 'Miracle_fruit',
    ],

    'funfacts_human_oddities': [
        'Synesthesia', 'Photographic_memory', 'Savant_syndrome', 'Tetrachromacy',
        'Absolute_pitch', 'ASMR', 'Phantom_limb', 'Heterochromia',
        'Hypertrichosis', 'Dermatographia',
    ],
}

# Trivia Article Lists - ~500 Fun Trivia Topics
TRIVIA_ARTICLES = {
    'trivia_movies': [
        'Citizen_Kane', 'The_Godfather', 'Casablanca', 'Gone_with_the_Wind',
        'The_Wizard_of_Oz', 'Star_Wars', 'Jaws_(film)', 'E.T._the_Extra-Terrestrial',
        'Jurassic_Park_(film)', 'Titanic_(1997_film)', 'Avatar_(2009_film)',
        'The_Lord_of_the_Rings', 'Harry_Potter', 'Marvel_Cinematic_Universe',
        'James_Bond', 'Indiana_Jones', 'Pirates_of_the_Caribbean',
        'Toy_Story', 'Finding_Nemo', 'The_Lion_King', 'Frozen_(2013_film)',
    ],
    
    'trivia_music': [
        'The_Beatles', 'Elvis_Presley', 'Michael_Jackson', 'Madonna',
        'Queen_(band)', 'Led_Zeppelin', 'Pink_Floyd', 'The_Rolling_Stones',
        'AC/DC', 'Metallica', 'Nirvana_(band)', 'Bob_Dylan', 'David_Bowie',
        'Prince_(musician)', 'Whitney_Houston', 'Beyoncé', 'Taylor_Swift',
        'Ed_Sheeran', 'BTS', 'Gangnam_Style',
    ],
    
    'trivia_tv_shows': [
        'Friends', 'Seinfeld', 'The_Simpsons', 'Game_of_Thrones',
        'Breaking_Bad', 'The_Sopranos', 'The_Wire', 'Mad_Men',
        'Stranger_Things', 'The_Office_(American_TV_series)', 'Parks_and_Recreation',
        'Saturday_Night_Live', 'The_Tonight_Show', 'Sesame_Street',
        'Mister_Rogers%27_Neighborhood', 'Doctor_Who', 'Monty_Python',
    ],
    
    'trivia_sports': [
        'Olympic_Games', 'FIFA_World_Cup', 'Super_Bowl', 'World_Series',
        'Stanley_Cup', 'Wimbledon', 'Tour_de_France', 'Boston_Marathon',
        'Muhammad_Ali', 'Michael_Jordan', 'Babe_Ruth', 'Pelé',
        'Usain_Bolt', 'Michael_Phelps', 'Serena_Williams', 'Tiger_Woods',
        'Lionel_Messi', 'Cristiano_Ronaldo', 'Tom_Brady',
    ],
    
    'trivia_video_games': [
        'Super_Mario', 'The_Legend_of_Zelda', 'Pokémon', 'Minecraft',
        'Tetris', 'Pac-Man', 'Space_Invaders', 'Donkey_Kong',
        'Sonic_the_Hedgehog', 'Street_Fighter', 'Final_Fantasy',
        'Grand_Theft_Auto', 'Call_of_Duty', 'Fortnite', 'World_of_Warcraft',
        'The_Sims', 'Angry_Birds', 'Candy_Crush_Saga',
    ],
    
    'trivia_food_drinks': [
        'Pizza', 'Hamburger', 'Hot_dog', 'Sandwich', 'Sushi', 'Taco',
        'French_fries', 'Ice_cream', 'Chocolate', 'Coffee', 'Tea',
        'Coca-Cola', 'Pepsi', 'McDonald%27s', 'Starbucks', 'KFC',
        'Champagne', 'Whisky', 'Beer', 'Wine', 'Vodka',
    ],
    
    'trivia_landmarks': [
        'Eiffel_Tower', 'Statue_of_Liberty', 'Big_Ben', 'Colosseum',
        'Taj_Mahal', 'Great_Pyramid_of_Giza', 'Machu_Picchu', 'Christ_the_Redeemer',
        'Sydney_Opera_House', 'Leaning_Tower_of_Pisa', 'Mount_Rushmore',
        'Space_Needle', 'CN_Tower', 'Empire_State_Building',
    ],
    
    'trivia_technology': [
        'iPhone', 'Google', 'Facebook', 'Amazon_(company)', 'Microsoft',
        'Apple_Inc.', 'Tesla,_Inc.', 'SpaceX', 'Twitter', 'YouTube',
        'Wikipedia', 'Internet', 'World_Wide_Web', 'Email', 'Smartphone',
        'Personal_computer', 'Laptop', 'Tablet_computer', 'Video_game_console',
    ],
    
    'trivia_countries': [
        'United_States', 'China', 'Russia', 'United_Kingdom', 'France',
        'Germany', 'Japan', 'India', 'Brazil', 'Canada', 'Australia',
        'Mexico', 'Italy', 'Spain', 'South_Korea', 'Netherlands',
        'Switzerland', 'Sweden', 'Norway', 'Denmark', 'Finland',
    ],
    
    'trivia_famous_people': [
        'Abraham_Lincoln', 'George_Washington', 'Winston_Churchill',
        'Mahatma_Gandhi', 'Martin_Luther_King_Jr.', 'Nelson_Mandela',
        'Albert_Einstein', 'Isaac_Newton', 'Leonardo_da_Vinci',
        'William_Shakespeare', 'Charles_Darwin', 'Marie_Curie',
        'Steve_Jobs', 'Bill_Gates', 'Elon_Musk', 'Mark_Zuckerberg',
    ],
}

# Unsolved Mysteries Article Lists - Conspiracy Theories & Fringe Ideas (~400 articles)
MYSTERIES_ARTICLES = {
    'mysteries_alternative_history': [
        'Tartary', 'Mud_flood', 'Phantom_time_hypothesis',
        'Atlantis', 'Lemuria', 'Ancient_astronauts', 'Ancient_Aliens',
        'Nazca_Lines', 'Piri_Reis_map', 'Antikythera_mechanism',
        'Baghdad_Battery', 'Göbekli_Tepe', 'Pumapunku',
    ],
    
    'mysteries_flat_hollow_earth': [
        'Flat_Earth', 'Modern_flat_Earth_beliefs', 'Flat_Earth_Society',
        'Hollow_Earth', 'Agartha', 'Shambhala', 'Antarctica',
        'Firmament', 'Geocentric_model',
    ],
    
    'mysteries_secret_societies': [
        'Illuminati', 'New_World_Order_(conspiracy_theory)',
        'Freemason', 'Knights_Templar', 'Skull_and_Bones',
        'Bohemian_Grove', 'Bilderberg_Meeting', 'Rothschild_family',
    ],
    
    'mysteries_government_coverups': [
        'Area_51', 'Roswell_incident', 'Project_Blue_Book',
        'Majestic_12', 'Men_in_black', 'HAARP',
        'MKUltra', 'JFK_assassination', 'Operation_Paperclip',
    ],
    
    'mysteries_moon_space': [
        'Moon_landing_conspiracy_theories', 'Apollo_program',
        'Stanley_Kubrick', 'Van_Allen_radiation_belt', 'Apollo_11',
    ],
    
    'mysteries_alien_reptilian': [
        'Reptilian_conspiracy_theory', 'David_Icke', 'Annunaki',
        'Nephilim', 'Zecharia_Sitchin', 'Nibiru_cataclysm',
        'Grey_alien', 'Nordic_aliens', 'Abduction_phenomenon',
    ],
    
    'mysteries_matrix_simulation': [
        'Simulation_hypothesis', 'Simulated_reality', 'The_Matrix',
        'Mandela_effect', 'Déjà_vu', 'Glitch_in_the_Matrix',
    ],
    
    'mysteries_chemtrails': [
        'Chemtrail_conspiracy_theory', 'Contrail', 'Cloud_seeding',
        'Weather_modification', 'HAARP_conspiracy_theories',
        'Geoengineering', 'Climate_engineering',
    ],
    
    'mysteries_cryptids': [
        'Bigfoot', 'Yeti', 'Loch_Ness_Monster', 'Chupacabra',
        'Mothman', 'Jersey_Devil', 'Thunderbird_(cryptozoology)',
    ],
    
    'mysteries_paranormal': [
        'Ghost', 'Poltergeist', 'Shadow_person', 'Ouija',
        'Near-death_experience', 'Astral_projection', 'Remote_viewing',
        'Telepathy', 'Precognition', 'Psychokinesis',
    ],
}

class LibraryMonitor(xbmc.Monitor):
    """Monitor for library episode selection during speed dial browsing"""

    def __init__(self, overlay):
        xbmc.Monitor.__init__(self)
        self.overlay = overlay
        self.log("LibraryMonitor initialized")

    def log(self, msg):
        log("LibraryMonitor: " + msg)

    def onPlayBackStarted(self):
        """Detect when an episode starts playing from the library"""
        if self.overlay.monitoringLibrarySelection and xbmc.Player().isPlayingVideo():
            # Get the playing item info
            player = xbmc.Player()

            # Small delay to ensure info is available
            xbmc.sleep(100)

            try:
                # Get the file path of what's playing
                playingFile = player.getPlayingFile()

                # Stop the regular playback
                player.stop()

                # Trigger preemption with this file
                self.overlay.preemptChannelWithShow(playingFile)

            except:
                self.log("Failed to get playing file info")


class MyPlayer(xbmc.Player):
    def __init__(self):
        xbmc.Player.__init__(self, xbmc.Player())
        self.stopped = False
        self.ignoreNextStop = False
        self.overlay = None
        self.channelChangePending = False
        self.lastPlayingFile = None
        self.channelChangeTimer = None
        
    def log(self, msg, level=xbmc.LOGDEBUG):
        log("Player: " + msg, level)

    def onPlayBackStopped(self):
        """Handle when playback stops"""

        # Check if we should ignore this callback
        if self.ignoreNextStop:
            self.ignoreNextStop = False
            self.log("Playback stopped - ignored due to ignoreNextStop flag")
            return

        if self.stopped == False:
            self.log("Playback stopped")

            # Check if overlay exists and isn't exiting
            if (
                self.overlay
                and hasattr(self.overlay, "isExiting")
                and not self.overlay.isExiting
            ):
                try:
                    if self.overlay.sleepTimeValue == 0:
                        self.overlay.sleepTimer = threading.Timer(
                            1, self.overlay.sleepAction
                        )
                    self.overlay.background.setVisible(True)
                    self.overlay.sleepTimeValue = 1
                    self.overlay.startSleepTimer()
                    self.stopped = True
                except Exception as e:
                    self.log("Error in onPlayBackStopped: " + str(e))
                    # Overlay is likely closed, ignore
                    pass
            else:
                self.log(
                    "Overlay is None or exiting, skipping onPlayBackStopped actions"
                )

    def onPlayBackEnded(self):
        """Handle when playback ends naturally"""

        if hasattr(self.overlay, "isPreempting") and self.overlay.isPreempting:
            # Special programming has ended, use enhanced return
            self.overlay.returnFromOnDemand()


class TVOverlay(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        xbmcgui.WindowXMLDialog.__init__(self, *args, **kwargs)
        self.log("__init__")

        # Core components
        self.channels = []
        self.Player = MyPlayer()
        self.Player.overlay = self

        # Channel state
        self.currentChannel = 1
        self.maxChannels = 0
        self.inputChannel = -1
        self.channelDelay = 500
        self.previousChannel = 0  # For Last Channel feature

        # Timers
        self.lastActionTime = 0
        self.timeStarted = 0
        self.notPlayingCount = 0

        # Thread management
        self.actionSemaphore = threading.BoundedSemaphore()
        self.channelThread = ChannelListThread()
        self.channelThread.myOverlay = self

        # Display settings
        self.showingInfo = False
        self.infoOffset = 0
        self.showChannelBug = False
        self.infoOnChange = True
        self.showNextItem = False
        self.hideShortItems = False
        self.shortItemLength = 120

        # Weather overlay
        self.showingWeather = False
        self.weatherTimer = None
        self.weatherRefreshTimer = None

        # Calendar system (Sonarr/Radarr) - INITIALIZE EARLY
        self.showingCalendar = False
        self.sonarrCalendar = []  # FIXED: Initialize early
        self.radarrCalendar = []  # FIXED: Initialize early
        self.sonarrTodayIndex = 0
        self.radarrTodayIndex = 0
        self.calendarRotationTimer = None
        self.calendarRefreshTimer = None
        self.calendarRefreshInterval = 300  # Refresh every 5 minutes

        # Recently Added system
        self.showingRecentlyAdded = False
        self.recentlyAddedItems = []  # All 10 items
        self.recentlyAddedFeaturedIndex = 0  # Current featured item (0-4)
        self.recentlyAddedRotationTimer = None
        self.recentlyAddedRefreshTimer = None
        self.recentlyAddedRefreshInterval = 300  # Refresh every 5 minutes
        
        # Random Recommendations system
        self.showingRecommendations = False
        self.recommendationsItems = []  # All recommendation items
        self.recommendationsFeaturedIndex = 0  # Current featured item
        self.recommendationsRotationTimer = None
        self.recommendationsRefreshTimer = None
        self.recommendationsRefreshInterval = 300  # Refresh every 5 minutes (300 seconds)

        # Server Stats (Page 4) settings
        self.showingServerStats = False
        self.serverStatsData = {}
        self.serverStatsTimer = None
        self.serverStatsRefreshTimer = None
        self.unraidSSHHost = "10.0.0.39"
        self.unraidSSHUser = "root"
        self.unraidSSHKey = "/storage/.ssh/id_rsa"

        # Knowledge Page (Page 7) settings
        self.showingWikipedia = False  # Keep same flag for compatibility
        self.knowledge_current_content = None
        self.knowledge_rotation_index = 0  # Track which source to show next
        self.wikipedia_viewed_articles = []  # Track viewed articles to prevent repeats
        self.wikipedia_all_articles = []  # Flat list of all articles for cycling

        # Mysql Stats (Page 6) settings
        self.mysqlStatsData = {}
        self.mysqlStatsRefreshTimer = None
        self.showingMySQLStats = False
        
        # Kodi Box Stats (Page 5) settings
        self.kodiBoxStatsData = {}
        self.kodiBoxStatsRefreshTimer = None
        self.showingKodiBoxStats = False
        
        # Channel 99 page cycling 
        self.channel99PageTimer = None
        self.channel99CurrentPage = "calendar"  # "calendar" or "recentlyadded"
        self.channel99PageInterval = 60  # Switch pages every 60 seconds
        xbmcgui.Window(10000).clearProperty("PTV.Channel99")

        # UI Windows (will be initialized in onInit)
        self.myEPG = None
        self.mySidebar = None
        self.mySpeedDial = None  # Add Speed Dial window

        # Blackout state
        self.blackoutActive = False

        # Favorite shows system
        self.favoriteShows = []  # List of show names
        self.favoriteShowsNextAiring = (
            {}
        )  # Dict of {showname: (channel, starttime, endtime)}
        self.favoriteShowsLastNotification = (
            {}
        )  # Track when we last notified for each show
        self.epgScanTimer = None
        self.favoriteShowsScanInterval = 60  # Scan every 60 seconds for testing
        self.pendingFavoriteShowChannel = 0  # For jumping to channel from notification

        # Speed dial channels (1-9) and shows
        self.speedDialChannels = {}
        self.speedDialShows = {}

        # Preemption system
        self.isPreempting = False
        self.preemptedChannel = 0
        self.preemptStartTime = 0
        self.monitoringLibrarySelection = False
        self.libraryMonitor = None

        # Navigation settings
        self.seekForward = 30
        self.seekBackward = -30

        # System state
        self.isExiting = False  # ADD THIS FLAG
        self.isMaster = True
        self.forceReset = False
        self.backgroundUpdating = 0
        self.invalidatedChannelCount = 0

        # Notification system
        self.notificationLastChannel = 0
        self.notificationLastShow = 0
        self.notificationShowedNotif = False

        # Sleep system
        self.sleepTimeValue = 0
        self.sleepTimer = None

        # Action handling
        self.ignoreInfoAction = False
        self.runningActionChannel = 0

        # UI Controls (will be initialized in onInit)
        self.background = None
        self.channelNumberLabel = None
        self.channelNumberShadow = None
        self.blackoutControl = None

        # Color settings
        self.numberColor = NUM_COLOUR[int(ADDON.getSetting("NumberColour"))]

        # Initialize timers
        self.channelLabelTimer = threading.Timer(10.0, self.hideChannelLabel)
        self.playerTimer = threading.Timer(2.0, self.playerTimerAction)
        self.playerTimer.name = "PlayerTimer"
        self.infoTimer = threading.Timer(5.0, self.hideInfo)
        self.notificationTimer = threading.Timer(
            NOTIFICATION_CHECK_TIME, self.notificationAction
        )
        # Initialize favorite show timer to None
        self.favoriteShowTimer = None

        self.doModal()
        self.log("__init__ return")

    def onInit(self):
        self.log("onInit")

        # Create required directories
        if not self.createDirectories():
            return

        # Get UI controls
        self.background = self.getControl(101)
        self.getControl(102).setVisible(False)
        self.background.setVisible(True)

        # Get channel number controls from XML
        self.channelNumberShadow = self.getControl(1001)
        self.channelNumberLabel = self.getControl(1002)

        # Create dynamic UI elements
        self.createDynamicControls()

        # Initialize system
        self.backupFiles()
        ADDON_SETTINGS.loadSettings()

        # Load favorites and speed dial (with new persistence system)
        self.loadFavorites()
        self.loadSpeedDial()
        # Load favorite shows
        self.loadFavoriteShows()

        # Start EPG scanner for favorites
        if self.favoriteShows:
            self.epgScanTimer = threading.Timer(
                10.0, self.epgScanAction
            )  # First scan after 10 seconds
            self.epgScanTimer.start()

        # Handle channel sharing
        if CHANNEL_SHARING:
            self.initializeChannelSharing()
        else:
            self.isMaster = True

        # Run migration if master
        if self.isMaster:
            migratemaster = Migrate()
            migratemaster.migrate()

        # Don't allow any actions during initialization
        self.actionSemaphore.acquire()
        self.timeStarted = time.time()

        # Read configuration
        if self.readConfig() == False:
            return

        # Initialize EPG
        self.myEPG = EPGWindow("script.paragontv.EPG.xml", CWD, "default")
        self.myEPG.MyOverlayWindow = self
        self.myEPG.channelLogos = self.channelLogos

        # Initialize Sidebar
        self.mySidebar = SidebarWindow("script.paragontv.Sidebar.xml", CWD, "default")
        self.mySidebar.overlayWindow = self

        # Initialize Speed Dial Window
        self.mySpeedDial = SpeedDialWindow(
            "script.paragontv.SpeedDial.xml", CWD, "default"
        )
        self.mySpeedDial.overlayWindow = self

        # Initialize library monitor for preemption
        self.libraryMonitor = LibraryMonitor(self)

        # Validate channels
        self.maxChannels = len(self.channels)
        if not self.validateChannels():
            return

        # Initialize current channel
        try:
            if self.forceReset == False:
                self.currentChannel = self.fixChannel(
                    int(ADDON.getSetting("CurrentChannel"))
                )
            else:
                self.currentChannel = self.fixChannel(1)
        except:
            self.currentChannel = self.fixChannel(1)

        # Start playback
        self.resetChannelTimes()
        self.setChannel(self.currentChannel)
        self.background.setVisible(False)

        # Start timers
        self.startSleepTimer()
        self.startNotificationTimer()
        self.playerTimer.start()

        # Start weather refresh timer for periodic updates
        self.weatherRefreshTimer = threading.Timer(1800.0, self.weatherRefreshAction)
        self.weatherRefreshTimer.name = "WeatherRefreshTimer"
        self.weatherRefreshTimer.start()

        # Start channel thread if needed
        if self.backgroundUpdating < 2 or self.isMaster == False:
            self.channelThread.name = "ChannelThread"
            self.channelThread.start()

        self.actionSemaphore.release()
        self.log("onInit return")

    def createDynamicControls(self):
        """Create channel number display and blackout control"""
        # Channel number controls are now in XML, so we only create blackout control

        # Blackout control
        self.blackoutControl = xbmcgui.ControlImage(0, 0, 1920, 1080, "black.png")
        self.addControl(self.blackoutControl)
        self.blackoutControl.setVisible(False)

    def createDirectories(self):
        """Create required directories"""
        directories = [
            (GEN_CHAN_LOC, LANGUAGE(30035)),
            (MADE_CHAN_LOC, LANGUAGE(30036)),
            (CHANNELBUG_LOC, LANGUAGE(30036)),
        ]

        for directory, error_msg in directories:
            if not FileAccess.exists(directory):
                try:
                    FileAccess.makedirs(directory)
                except:
                    self.Error(error_msg)
                    return False
        return True

    def initializeChannelSharing(self):
        """Initialize channel sharing system"""
        updateDialog = xbmcgui.DialogProgressBG()
        updateDialog.create(ADDON_NAME, "")
        updateDialog.update(1, message="Initializing Channel Sharing")
        FileAccess.makedirs(LOCK_LOC)
        updateDialog.update(50, message="Initializing Channel Sharing")
        self.isMaster = GlobalFileLock.lockFile("MasterLock", False)
        updateDialog.update(100, message="Initializing Channel Sharing")
        xbmc.sleep(200)
        updateDialog.close()

    def validateChannels(self):
        """Validate that we have usable channels"""
        if self.maxChannels == 0:
            self.Error(LANGUAGE(30037))
            return False

        # Check for at least one valid channel
        for i in range(self.maxChannels):
            if self.channels[i].isValid:
                return True

        self.Error(LANGUAGE(30038))
        return False

    def loadFavorites(self):
        """Load favorite channels from settings"""
        self.favoriteChannels = []
        try:
            favs = ADDON.getSetting("FavoriteChannels")
            if favs:
                self.favoriteChannels = [int(x) for x in favs.split(",") if x.strip()]
        except:
            pass

    # Speed Dial Persistence Methods
    def loadSpeedDial(self):
        """Load speed dial assignments from multiple sources with fallback"""
        self.log("loadSpeedDial - Starting")
        self.speedDialChannels = {}
        self.speedDialShows = {}

        # First try to load from JSON file (most reliable)
        jsonLoaded = self.loadSpeedDialFromJSON()

        # If JSON doesn't exist or is empty, try addon settings
        if not jsonLoaded or (not self.speedDialChannels and not self.speedDialShows):
            self.log("loadSpeedDial - No JSON data, trying addon settings")
            self.loadSpeedDialFromSettings()

        # Log what we loaded
        self.log("loadSpeedDial - Loaded channels: " + str(self.speedDialChannels))
        self.log("loadSpeedDial - Loaded shows: " + str(self.speedDialShows))

    def loadSpeedDialFromJSON(self):
        """Load speed dial from JSON file"""
        speedDialFile = translatePath(os.path.join(SETTINGS_LOC, "speeddial.json"))
        try:
            if FileAccess.exists(speedDialFile):
                with open(speedDialFile, "r") as f:
                    data = json.load(f)
                    # Load channels
                    channels = data.get("channels", {})
                    self.speedDialChannels = {}
                    for k, v in channels.items():
                        try:
                            key = int(k)
                            channel = int(v)
                            if channel > 0:
                                self.speedDialChannels[key] = channel
                        except:
                            pass

                    # Load shows
                    self.speedDialShows = data.get("shows", {})

                    self.log(
                        "loadSpeedDialFromJSON - Successfully loaded from "
                        + speedDialFile
                    )
                    return True
        except Exception as e:
            self.log("loadSpeedDialFromJSON - Error: " + str(e))
        return False

    def loadSpeedDialFromSettings(self):
        """Load speed dial from addon settings as fallback"""
        # Load channel speed dials
        for i in range(1, 10):
            try:
                channel = int(ADDON.getSetting("SpeedDialChannel" + str(i)))
                if channel > 0:
                    self.speedDialChannels[i] = channel
                    self.log(
                        "loadSpeedDialFromSettings - Loaded channel %d for speed dial %d"
                        % (channel, i)
                    )
            except:
                pass

        # Load show speed dials
        for i in range(1, 4):
            try:
                showInfo = ADDON.getSetting("SpeedDialShow" + str(i))
                if showInfo:
                    self.speedDialShows[str(i)] = showInfo
                    self.log(
                        "loadSpeedDialFromSettings - Loaded show for speed dial %d" % i
                    )
            except:
                pass

    def saveSpeedDial(self):
        """Save speed dial assignments to both JSON and addon settings"""
        self.log("saveSpeedDial - Starting")

        # Save to JSON file (primary storage)
        self.saveSpeedDialToJSON()

        # Also save to addon settings (backup/settings.xml integration)
        self.saveSpeedDialToSettings()

        self.log("saveSpeedDial - Complete")

    def saveSpeedDialToJSON(self):
        """Save speed dial to JSON file"""
        speedDialFile = translatePath(os.path.join(SETTINGS_LOC, "speeddial.json"))
        try:
            # Ensure directory exists
            speedDialDir = os.path.dirname(speedDialFile)
            if not FileAccess.exists(speedDialDir):
                FileAccess.makedirs(speedDialDir)

            # Prepare data
            data = {
                "channels": {str(k): v for k, v in self.speedDialChannels.items()},
                "shows": self.speedDialShows,
                "version": "1.0",
                "lastUpdated": time.strftime("%Y-%m-%d %H:%M:%S"),
            }

            # Debug log
            self.log("saveSpeedDialToJSON - Saving shows: " + str(self.speedDialShows))

            # Write to file
            with open(speedDialFile, "w") as f:
                json.dump(data, f, indent=2)

            self.log("saveSpeedDialToJSON - Saved to " + speedDialFile)
        except Exception as e:
            self.log("saveSpeedDialToJSON - Error: " + str(e), xbmc.LOGERROR)

    def saveSpeedDialToSettings(self):
        """Save speed dial to addon settings"""
        # Save channels
        for i in range(1, 10):
            if i in self.speedDialChannels:
                ADDON.setSetting(
                    "SpeedDialChannel" + str(i), str(self.speedDialChannels[i])
                )
            else:
                ADDON.setSetting("SpeedDialChannel" + str(i), "0")

        # Save shows
        for i in range(1, 4):
            key = str(i)
            if key in self.speedDialShows:
                self.log(
                    "saveSpeedDialToSettings - Saving show %s: %s"
                    % (key, str(self.speedDialShows[key]))
                )
                ADDON.setSetting(
                    "SpeedDialShow" + str(i), str(self.speedDialShows[key])
                )
            else:
                ADDON.setSetting("SpeedDialShow" + str(i), "")

        self.log("saveSpeedDialToSettings - Saved to addon settings")

    def setSpeedDialChannel(self, slot, channel):
        """Set a speed dial channel slot"""
        if channel > 0 and channel <= self.maxChannels:
            self.speedDialChannels[slot] = channel
            self.saveSpeedDial()
            self.log(
                "setSpeedDialChannel - Set slot %d to channel %d" % (slot, channel)
            )
            return True
        return False

    def setSpeedDialShow(self, slot, showInfo):
        """Set a speed dial show slot"""
        self.speedDialShows[str(slot)] = showInfo
        self.saveSpeedDial()
        self.log("setSpeedDialShow - Set slot %d to show: %s" % (slot, showInfo))
        return True

    def clearSpeedDial(self):
        """Clear all speed dial assignments"""
        self.speedDialChannels = {}
        self.speedDialShows = {}
        self.saveSpeedDial()
        self.log("clearSpeedDial - Cleared all speed dial assignments")

    def saveFavorites(self):
        """Save favorite channels to settings"""
        ADDON.setSetting(
            "FavoriteChannels", ",".join(str(x) for x in self.favoriteChannels)
        )

    def loadFavoriteShows(self):
        """Load favorite shows from JSON storage"""
        self.log("loadFavoriteShows")

        favShowsFile = translatePath(
            os.path.join(SETTINGS_LOC, "favorite_shows.json")
        )
        try:
            if FileAccess.exists(favShowsFile):
                with open(favShowsFile, "r") as f:
                    data = json.load(f)
                    self.favoriteShows = data.get("shows", [])
                    self.log("Loaded %d favorite shows" % len(self.favoriteShows))
        except Exception as e:
            self.log("Error loading favorite shows: " + str(e))
            # Try loading from settings as fallback
            try:
                shows = ADDON.getSetting("FavoriteShowsList")
                if shows:
                    self.favoriteShows = [
                        s.strip() for s in shows.split(",") if s.strip()
                    ]
            except:
                pass

    def saveFavoriteShows(self):
        """Save favorite shows to JSON storage"""
        self.log("saveFavoriteShows")

        favShowsFile = translatePath(
            os.path.join(SETTINGS_LOC, "favorite_shows.json")
        )
        try:
            data = {
                "shows": self.favoriteShows,
                "version": "1.0",
                "lastUpdated": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            with open(favShowsFile, "w") as f:
                json.dump(data, f, indent=2)

            # Also save to settings for backup
            ADDON.setSetting("FavoriteShowsList", ", ".join(self.favoriteShows))

        except Exception as e:
            self.log("Error saving favorite shows: " + str(e))

    def toggleFavorite(self, channel=None):
        """Toggle favorite status for current or specified channel"""
        if channel is None:
            channel = self.currentChannel

        if channel in self.favoriteChannels:
            self.favoriteChannels.remove(channel)
            xbmc.executebuiltin(
                "Notification(%s, Channel %d removed from favorites, 2000, %s)"
                % (ADDON_NAME, channel, ICON)
            )
        else:
            self.favoriteChannels.append(channel)
            self.favoriteChannels.sort()
            xbmc.executebuiltin(
                "Notification(%s, Channel %d added to favorites, 2000, %s)"
                % (ADDON_NAME, channel, ICON)
            )

        self.saveFavorites()

    def scanEPGForFavorites(self):
        """Scan EPG for upcoming airings of favorite shows using EPG's timeline logic"""
        self.log("scanEPGForFavorites - Starting scan")

        if not self.favoriteShows:
            return

        currentTime = time.time()
        foundShows = {}

        # Scan all channels using the same logic as EPG
        for channelNum in range(1, self.maxChannels + 1):
            if not self.channels[channelNum - 1].isValid:
                continue

            channel = self.channels[channelNum - 1]

            # Get the channel's current timeline position (same as EPG)
            playlistPosition = channel.playlistPosition
            showTimeOffset = channel.showTimeOffset
            lastAccessTime = channel.lastAccessTime

            # Calculate current position in timeline
            timedif = currentTime - lastAccessTime

            # Find current show position
            while timedif > 0:
                # Get show duration at current position
                showLength = channel.getItemDuration(playlistPosition)

                if (showTimeOffset + timedif) < showLength:

                    break
                else:
                    # Move to next show
                    timedif -= showLength - showTimeOffset
                    showTimeOffset = 0
                    playlistPosition = channel.fixPlaylistIndex(playlistPosition + 1)

            # ADD THE DEBUG LOGGING HERE:
            self.log(
                "Channel %d: Current show at position %d, offset %d seconds into show"
                % (channelNum, playlistPosition, showTimeOffset + timedif)
            )

            # Now scan forward from current position for 30 minutes
            scanTime = 0
            scanPosition = playlistPosition
            currentShowTime = showTimeOffset + timedif

            while scanTime < 1800:  # 30 minutes
                # Get show info at this position
                showTitle = channel.getItemTitle(scanPosition).lower()
                showDuration = channel.getItemDuration(scanPosition)

                # Calculate when this show starts
                if scanPosition == playlistPosition:
                    # Current show - calculate remaining time
                    timeUntilEnd = showDuration - currentShowTime
                    showStartTime = currentTime - currentShowTime
                else:
                    # Future show
                    showStartTime = currentTime + scanTime
                    timeUntilEnd = showDuration

                # Check if this show is in favorites
                for favShow in self.favoriteShows:
                    # Use exact matching instead of substring matching
                    if favShow.lower() == showTitle.lower():
                        # Found a favorite show
                        if (
                            favShow not in foundShows
                            or foundShows[favShow][1] > showStartTime
                        ):
                            foundShows[favShow] = (
                                channelNum,
                                showStartTime,
                                showStartTime + showDuration,
                                showTitle,  # Use the actual title from EPG
                            )
                            self.log(
                                "Found %s on channel %d starting at %s"
                                % (
                                    favShow,
                                    channelNum,
                                    time.strftime(
                                        "%H:%M", time.localtime(showStartTime)
                                    ),
                                )
                            )

                # Move to next show
                if scanPosition == playlistPosition:
                    scanTime += timeUntilEnd
                else:
                    scanTime += showDuration
                scanPosition = channel.fixPlaylistIndex(scanPosition + 1)

        self.favoriteShowsNextAiring = foundShows

        # Check if any shows need notifications
        self.checkFavoriteShowNotifications()

        # Save schedule to text file
        self.saveFavoriteShowsSchedule()

    def saveFavoriteShowsSchedule(self):
        """Save a schedule of upcoming favorite shows to a text file"""
        self.log("saveFavoriteShowsSchedule")

        try:
            scheduleFile = translatePath(
                os.path.join(SETTINGS_LOC, "favorite_shows_schedule.txt")
            )

            with open(scheduleFile, "w") as f:
                f.write("PseudoTV Favorite Shows Schedule\n")
                f.write("Generated: %s\n" % time.strftime("%Y-%m-%d %H:%M:%S"))
                f.write("=" * 50 + "\n\n")

                if not self.favoriteShowsNextAiring:
                    f.write("No favorite shows found in the next 30 minutes.\n")
                else:
                    # Sort by start time
                    sortedShows = sorted(
                        self.favoriteShowsNextAiring.items(), key=lambda x: x[1][1]
                    )  # Sort by start time

                    for showName, (
                        channelNum,
                        startTime,
                        endTime,
                        fullTitle,
                    ) in sortedShows:
                        # Get channel name
                        channelName = (
                            self.channels[channelNum - 1].name
                            if channelNum <= self.maxChannels
                            else "Unknown"
                        )

                        # Format times
                        startStr = time.strftime(
                            "%Y-%m-%d %H:%M:%S", time.localtime(startTime)
                        )
                        timeUntil = startTime - time.time()

                        f.write("Show: %s\n" % fullTitle)
                        f.write("Channel: %d - %s\n" % (channelNum, channelName))
                        f.write("Start Time: %s\n" % startStr)

                        if timeUntil > 0:
                            minutes = int(timeUntil / 60)
                            if minutes > 0:
                                f.write("Starts in: %d minutes\n" % minutes)
                            else:
                                f.write("Starting now!\n")
                        else:
                            f.write("Already started\n")

                        f.write("-" * 30 + "\n\n")

                f.write(
                    "\nNext scan in %d minutes\n"
                    % (self.favoriteShowsScanInterval / 60)
                )

            self.log("Saved favorite shows schedule to: " + scheduleFile)

        except Exception as e:
            self.log("Error saving favorite shows schedule: " + str(e))

    def checkFavoriteShowNotifications(self):
        """Check if any favorite shows need notifications"""
        # Debug: Check raw setting value
        rawValue = ADDON.getSetting("FavoriteShowAdvance")
        self.log('FavoriteShowAdvance raw value from settings: "%s"' % rawValue)

        # Check if notifications are enabled
        if ADDON.getSetting("EnableFavoriteShows") != "true":
            self.log("Favorite show notifications are disabled in settings")
            return

        currentTime = time.time()
        notifyBefore = (
            int(ADDON.getSetting("FavoriteShowAdvance")) * 60
        )  # Convert minutes to seconds
        cooldown = int(ADDON.getSetting("FavoriteShowsCooldown")) * 60

        self.log(
            "checkFavoriteShowNotifications - notifyBefore: %d seconds, cooldown: %d seconds"
            % (notifyBefore, cooldown)
        )

        for showName, (
            channelNum,
            startTime,
            endTime,
            fullTitle,
        ) in self.favoriteShowsNextAiring.items():
            timeUntilShow = startTime - currentTime

            self.log(
                "Checking %s on channel %d - starts in %d seconds"
                % (showName, channelNum, int(timeUntilShow))
            )

            # Check if show is starting within notification window
            if -60 < timeUntilShow <= notifyBefore:
                # Check cooldown
                lastNotify = self.favoriteShowsLastNotification.get(showName, 0)
                timeSinceLastNotify = currentTime - lastNotify

                self.log(
                    "Show %s is in notification window. Last notified %d seconds ago"
                    % (showName, int(timeSinceLastNotify))
                )

                if timeSinceLastNotify > cooldown:
                    # Show notification
                    self.log("Triggering notification for %s" % showName)
                    self.showFavoriteShowNotification(
                        showName, channelNum, timeUntilShow, fullTitle
                    )
                    self.favoriteShowsLastNotification[showName] = currentTime
                else:
                    self.log(
                        "Skipping notification for %s - still in cooldown" % showName
                    )

    def epgScanAction(self):
        """Periodic EPG scan for favorite shows"""
        self.scanEPGForFavorites()

        # Schedule next scan
        self.epgScanTimer = threading.Timer(
            self.favoriteShowsScanInterval, self.epgScanAction
        )
        if not self.isExiting:
            self.epgScanTimer.start()

    def showFavoriteShowNotification(self, showName, channelNum, timeUntil, fullTitle):
        """Show notification for upcoming favorite show"""
        self.log(
            "showFavoriteShowNotification: %s on channel %d" % (showName, channelNum)
        )

        # Get show artwork (similar to coming up overlay)
        showImage = ""
        try:
            # Try to get artwork from the show's folder
            channel = self.channels[channelNum - 1]

            # Try JSON-RPC first
            json_query = {
                "jsonrpc": "2.0",
                "method": "VideoLibrary.GetTVShows",
                "params": {
                    "filter": {
                        "field": "title",
                        "operator": "contains",
                        "value": showName,
                    },
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
                    if "landscape" in show["art"]:
                        showImage = show["art"]["landscape"]
                    elif "fanart" in show["art"]:
                        showImage = show["art"]["fanart"]
                    elif "banner" in show["art"]:
                        showImage = show["art"]["banner"]

        except Exception as e:
            self.log("Error getting favorite show artwork: " + str(e))

        # Fallback to channel logo if no show art
        if not showImage:
            channelName = self.channels[channelNum - 1].name
            showImage = self.channelLogos + ascii(channelName) + "_landscape.png"
            if not FileAccess.exists(showImage):
                showImage = self.channelLogos + ascii(channelName) + ".png"
                if not FileAccess.exists(showImage):
                    showImage = ICON

        # Set properties for the favorite show overlay
        self.setProperty("PTV.FavoriteShow", "true")
        self.setProperty("PTV.FavoriteShow.Title", fullTitle)
        self.setProperty("PTV.FavoriteShow.Channel", str(channelNum))
        self.setProperty("PTV.FavoriteShow.Image", showImage)

        self.log("showFavoriteShowNotification - Properties set:")
        self.log(
            "  PTV.FavoriteShow = %s"
            % xbmcgui.Window(10000).getProperty("PTV.FavoriteShow")
        )
        self.log(
            "  PTV.FavoriteShow.Title = %s"
            % xbmcgui.Window(10000).getProperty("PTV.FavoriteShow.Title")
        )

        minutes = int(timeUntil / 60)
        if minutes <= 1:
            timeText = "Starting Now"
        else:
            timeText = "Starts in %d minutes" % minutes
        self.setProperty("PTV.FavoriteShow.Time", timeText)

        # Store info for potential channel jump
        self.pendingFavoriteShowChannel = channelNum

        # Auto-hide after display time
        if (
            hasattr(self, "favoriteShowTimer")
            and self.favoriteShowTimer
            and self.favoriteShowTimer.isAlive()
        ):
            self.favoriteShowTimer.cancel()

        self.favoriteShowTimer = threading.Timer(
            15.0, self.hideFavoriteShowNotification
        )
        self.favoriteShowTimer.start()

        # ADD THIS DEBUG LOG
        self.log("Favorite show notification displayed for %s" % showName)

    def hideFavoriteShowNotification(self):
        """Hide favorite show notification"""
        self.setProperty("PTV.FavoriteShow", "false")
        self.pendingFavoriteShowChannel = 0

    def showSidebar(self):
        """Show custom sidebar window"""
        self.log("showSidebar - using custom window")

        # Show the custom sidebar
        self.mySidebar.doModal()

        # Handle the selected action
        if self.mySidebar.selectedAction:
            action = self.mySidebar.selectedAction
            self.mySidebar.selectedAction = None  # Reset for next time

            if action == "epg":
                self.showEPG()
            elif action == "speeddial":
                self.showSpeedDialMenu()
            elif action == "favorites":
                self.showFavoritesMenu()
            elif action == "browse":
                # Use Kodi's browse dialog
                selected = xbmcgui.Dialog().browse(
                    1,
                    "Browse Videos",
                    "video",
                    ".avi|.flv|.mkv|.mp4|.strm|.ts",
                    False,
                    False,
                )
                if selected and selected != "":
                    self.log("User selected: " + str(selected))
                    if FileAccess.exists(selected):
                        # Use preemption system for on-demand content
                        self.preemptChannelWithShow(selected)
            elif action == "settings":
                xbmc.executebuiltin("ActivateWindow(videoosd)")
            elif action == "codecinfo":
                xbmc.executebuiltin("ActivateWindow(playerprocessinfo)")
            elif action == "blackout":
                self.toggleBlackout()
            elif action == "lastchannel":
                if (
                    self.previousChannel > 0
                    and self.previousChannel != self.currentChannel
                ):
                    self.background.setVisible(True)
                    self.setChannel(self.previousChannel)
                    self.background.setVisible(False)
                else:
                    xbmc.executebuiltin(
                        "Notification(%s, No previous channel available, 2000, %s)"
                        % (ADDON_NAME, ICON)
                    )
            elif action == "mute":
                # Toggle mute
                xbmc.executebuiltin("Mute")

                # Give it more time to update
                xbmc.sleep(100)

                # Try getting the mute state using JSON-RPC instead
                json_query = '{"jsonrpc": "2.0", "method": "Application.GetProperties", "params": {"properties": ["muted"]}, "id": 1}'
                result = xbmc.executeJSONRPC(json_query)
                result = json.loads(result)

                if "result" in result and "muted" in result["result"]:
                    isMuted = result["result"]["muted"]
                    if isMuted:
                        xbmc.executebuiltin(
                            "Notification(%s, Muted, 2000, %s)" % (ADDON_NAME, ICON)
                        )
                    else:
                        xbmc.executebuiltin(
                            "Notification(%s, Unmuted, 2000, %s)" % (ADDON_NAME, ICON)
                        )
                else:
                    # Fallback if JSON-RPC fails
                    xbmc.executebuiltin(
                        "Notification(%s, Mute Toggled, 2000, %s)" % (ADDON_NAME, ICON)
                    )
            elif action == "exit":
                dlg = xbmcgui.Dialog()
                if dlg.yesno(xbmc.getLocalizedString(13012), LANGUAGE(30031)):
                    self.end()

    def showSpeedDialMenu(self):
        """Show the new Speed Dial window"""
        self.log("showSpeedDialMenu - using custom window")

        # Reload speed dial settings to ensure latest data
        self.loadSpeedDial()

        # Update the speed dial window
        if self.mySpeedDial:
            self.mySpeedDial.speedDialChannels = self.speedDialChannels
            self.mySpeedDial.speedDialShows = self.speedDialShows

        # Show the custom speed dial window
        self.mySpeedDial.doModal()

        # Handle the selected action
        if self.mySpeedDial.selectedAction:
            actionType, actionData = self.mySpeedDial.selectedAction
            self.mySpeedDial.selectedAction = None  # Reset for next time

            if actionType == "channel":
                # Jump to channel
                self.background.setVisible(True)
                self.setChannel(actionData)
                self.background.setVisible(False)

            elif actionType == "playshow":
                # Open show library for preemption
                self.openShowLibrary(actionData)

    def playShow(self, showInfo):
        """Play a specific show from speed dial"""
        self.log("playShow: " + showInfo)

        try:
            # Parse show info (format: "showname|channel|path")
            parts = showInfo.split("|")
            if len(parts) >= 2:
                showName = parts[0]
                channelNum = int(parts[1])

                # Find the show in the channel
                if channelNum <= self.maxChannels:
                    channel = self.channels[channelNum - 1]
                    if channel.isValid:
                        # For now, just switch to the channel
                        # In future, could implement seeking to specific show
                        self.background.setVisible(True)
                        self.setChannel(channelNum)

                        xbmc.executebuiltin(
                            "Notification(%s, Playing %s, 3000, %s)"
                            % (ADDON_NAME, showName, ICON)
                        )

                        self.background.setVisible(False)
                        return

                        # Show not found in current schedule
                        xbmcgui.Dialog().ok(
                            "Show Not Found",
                            "Could not find '%s' in the current schedule." % showName,
                            "The show may not be playing right now.",
                        )

        except Exception as e:
            self.log("Error playing show: " + str(e), xbmc.LOGERROR)
            xbmcgui.Dialog().ok("Error", "Could not play the selected show.")

    def openShowLibrary(self, showInfo):
        """Open custom episode browser for the selected show"""
        self.log("openShowLibrary: " + str(showInfo))

        try:
            # Parse show info to get proper format
            if isinstance(showInfo, dict):
                # Already in dictionary format
                showDict = showInfo
            else:
                # Convert old string format to dict
                showDict = {
                    "title": showInfo.get("title", "Unknown Show"),
                    "path": showInfo.get("path", ""),
                    "channel": showInfo.get("channel", 0),
                }

            # Create and show the episode browser (which will immediately open season browser)
            episodeBrowser = EpisodeBrowserWindow(
                "script.paragontv.EpisodeBrowserWindow.xml",
                CWD,
                "default",
                showInfo=showDict,
                overlay=self,
            )
            episodeBrowser.doModal()

            # Check if an episode was selected
            if episodeBrowser.selectedEpisode:
                self.log("Episode selected: " + episodeBrowser.selectedEpisode)
                # Trigger preemption with the selected episode
                self.preemptChannelWithShow(episodeBrowser.selectedEpisode)

            del episodeBrowser

        except Exception as e:
            self.log("openShowLibrary error: " + str(e))

    def stopLibraryMonitoring(self):
        """Stop monitoring library selection"""
        self.monitoringLibrarySelection = False
        if hasattr(self, "monitorTimer"):
            self.monitorTimer.cancel()

        # Restore overlay visibility if not preempting
        if not self.isPreempting:
            self.getControl(101).setVisible(True)  # Show background
            if self.showChannelBug:
                self.getControl(103).setVisible(True)  # Show channel bug if enabled

    def preemptChannelWithShow(self, episodePath):
        """Preempt current channel with a selected show/episode"""
        self.log("preemptChannelWithShow: " + str(episodePath))

        # Stop monitoring
        self.stopLibraryMonitoring()

        # Save current channel state for restoration
        self.preemptedChannel = self.currentChannel
        self.preemptStartTime = time.time()

        # Save detailed position info for multiple return options
        if self.Player.isPlaying():
            self.preemptedPosition = self.Player.getTime()
            self.preemptedPlaylistPos = xbmc.PlayList(xbmc.PLAYLIST_MUSIC).getposition()
            self.preemptedTotalTime = self.Player.getTotalTime()

            # Also save channel state
            self.preemptedChannelTime = self.channels[
                self.currentChannel - 1
            ].showTimeOffset
            self.preemptedChannelPos = self.channels[
                self.currentChannel - 1
            ].playlistPosition

        # Mark that we're in preemption mode
        self.isPreempting = True

        # Force video surface refresh by briefly showing background
        self.background.setVisible(True)
        xbmc.sleep(200)  # Brief pause with background visible

        # Play the selected episode
        self.log("Playing preemption show: " + episodePath)
        self.Player.play(episodePath)

        # Wait for playback to start
        xbmc.sleep(100)

        # Hide background again
        self.background.setVisible(False)

        # Show notification
        xbmc.executebuiltin(
            "Notification(%s, Special Programming, 3000, %s)" % (ADDON_NAME, ICON)
        )

    def returnToScheduledProgramming(self):
        """Return to the preempted channel - now calls enhanced return"""
        self.log("returnToScheduledProgramming")

        if not hasattr(self, "isPreempting") or not self.isPreempting:
            return

        # Use the enhanced return system
        self.returnFromOnDemand()

    def returnFromOnDemand(self):
        """Enhanced return from on-demand content with user options"""
        self.log("returnFromOnDemand - Enhanced")

        if not hasattr(self, "isPreempting") or not self.isPreempting:
            return

        # Calculate elapsed time during preemption
        elapsedTime = time.time() - self.preemptStartTime
        self.log("Preemption lasted %d seconds" % int(elapsedTime))

        # Get return mode from settings
        returnMode = ADDON.getSetting("OnDemandReturnMode")

        if returnMode == "0":  # Ask each time
            options = [
                "Return to current live position",
                "Resume where I left off",
                "Start at beginning of current show",
                "Stay on this channel but skip ahead",
            ]

            select = xbmcgui.Dialog().select(
                "Return to Channel %d" % self.preemptedChannel, options
            )

            if select == 0:  # Current live position
                self.returnToLivePosition()
            elif select == 1:  # Resume where left off
                self.returnToSavedPosition()
            elif select == 2:  # Beginning of current show
                self.returnToShowStart()
            elif select == 3:  # Skip ahead
                self.returnWithSkip()
            else:  # Cancelled - stay in on-demand
                return

        elif returnMode == "1":  # Always return to live
            self.returnToLivePosition()
        elif returnMode == "2":  # Always resume where left off
            self.returnToSavedPosition()
        elif returnMode == "3":  # Always start of current show
            self.returnToShowStart()

    def returnToLivePosition(self):
        """Return to current real-time position (existing behavior)"""
        self.log("returnToLivePosition")

        # Clear preemption flag
        self.isPreempting = False

        # Show notification
        xbmc.executebuiltin(
            "Notification(%s, Returning to live programming...already in progress, 4000, %s)"
            % (ADDON_NAME, ICON)
        )

        xbmc.sleep(1000)

        # Return to channel at current time
        self.setChannel(self.preemptedChannel)

    def returnToSavedPosition(self):
        """Return to where we left off when starting on-demand"""
        self.log("returnToSavedPosition")

        # Clear preemption flag
        self.isPreempting = False

        # Show notification
        xbmc.executebuiltin(
            "Notification(%s, Resuming where you left off, 3000, %s)"
            % (ADDON_NAME, ICON)
        )

        # Restore the exact position
        self.background.setVisible(True)

        # Set channel without seeking to current time
        self.currentChannel = self.preemptedChannel
        xbmc.PlayList(xbmc.PLAYLIST_MUSIC).clear()
        xbmc.PlayList(xbmc.PLAYLIST_MUSIC).load(
            self.channels[self.preemptedChannel - 1].fileName
        )

        # Play from saved position
        self.Player.playselected(self.preemptedPlaylistPos)

        # Wait for playback to start
        xbmc.sleep(500)

        # Seek to saved time
        if hasattr(self, "preemptedPosition"):
            self.Player.seekTime(self.preemptedPosition)

        self.background.setVisible(False)
        self.showChannelLabel(self.currentChannel)

    def returnToShowStart(self):
        """Return to the beginning of whatever show is currently playing"""
        self.log("returnToShowStart")

        # Clear preemption flag
        self.isPreempting = False

        # Calculate what show should be playing now
        curtime = time.time()
        timedif = curtime - self.channels[self.preemptedChannel - 1].lastAccessTime

        # Find current show position
        showPos = self.channels[self.preemptedChannel - 1].playlistPosition
        showTime = self.channels[self.preemptedChannel - 1].showTimeOffset

        # Adjust for elapsed time
        while showTime + timedif > self.channels[
            self.preemptedChannel - 1
        ].getItemDuration(showPos):
            timedif -= (
                self.channels[self.preemptedChannel - 1].getItemDuration(showPos)
                - showTime
            )
            showPos = self.channels[self.preemptedChannel - 1].fixPlaylistIndex(
                showPos + 1
            )
            showTime = 0

        # Get show info for notification
        showName = self.channels[self.preemptedChannel - 1].getItemTitle(showPos)

        xbmc.executebuiltin(
            "Notification(%s, Starting: %s, 4000, %s)" % (ADDON_NAME, showName, ICON)
        )

        xbmc.sleep(1000)

        # Set channel and seek to beginning of current show
        self.background.setVisible(True)
        self.currentChannel = self.preemptedChannel
        xbmc.PlayList(xbmc.PLAYLIST_MUSIC).clear()
        xbmc.PlayList(xbmc.PLAYLIST_MUSIC).load(
            self.channels[self.preemptedChannel - 1].fileName
        )

        # Play at current show position with 0 offset
        self.Player.playselected(showPos)
        self.channels[self.preemptedChannel - 1].setShowPosition(showPos)
        self.channels[self.preemptedChannel - 1].setShowTime(0)
        self.channels[self.preemptedChannel - 1].setAccessTime(curtime)

        self.background.setVisible(False)
        self.showChannelLabel(self.currentChannel)

    def returnWithSkip(self):
        """Return to channel but skip current show"""
        self.log("returnWithSkip")

        # Clear preemption flag
        self.isPreempting = False

        # Calculate current position
        curtime = time.time()
        timedif = curtime - self.channels[self.preemptedChannel - 1].lastAccessTime

        # Find what show should be playing
        showPos = self.channels[self.preemptedChannel - 1].playlistPosition
        showTime = self.channels[self.preemptedChannel - 1].showTimeOffset

        # Skip to next show
        showPos = self.channels[self.preemptedChannel - 1].fixPlaylistIndex(showPos + 1)

        # Get show info
        showName = self.channels[self.preemptedChannel - 1].getItemTitle(showPos)

        xbmc.executebuiltin(
            "Notification(%s, Skipping to: %s, 4000, %s)" % (ADDON_NAME, showName, ICON)
        )

        xbmc.sleep(1000)

        # Set channel at next show
        self.background.setVisible(True)
        self.currentChannel = self.preemptedChannel
        xbmc.PlayList(xbmc.PLAYLIST_MUSIC).clear()
        xbmc.PlayList(xbmc.PLAYLIST_MUSIC).load(
            self.channels[self.preemptedChannel - 1].fileName
        )

        self.Player.playselected(showPos)
        self.channels[self.preemptedChannel - 1].setShowPosition(showPos)
        self.channels[self.preemptedChannel - 1].setShowTime(0)
        self.channels[self.preemptedChannel - 1].setAccessTime(curtime)

        self.background.setVisible(False)
        self.showChannelLabel(self.currentChannel)

    def showFavoritesMenu(self):
        """Show favorite shows menu"""
        self.log("showFavoritesMenu")

        while True:
            options = ["Manage Favorite Shows"]

            if self.favoriteShows:
                options.append("View Upcoming Airings")

            options.append("Exit")

            select = xbmcgui.Dialog().select(
                "Favorite Shows (%d shows)" % len(self.favoriteShows), options
            )

            if select < 0 or options[select] == "Exit":
                break
            elif options[select] == "Manage Favorite Shows":
                self.manageFavoriteShows()
            elif options[select] == "View Upcoming Airings":
                self.viewUpcomingFavorites()

    def manageFavoriteShows(self):
        """Manage favorite shows list"""
        while True:
            options = ["Add Show from Library", "Add Show Manually"]

            # List current favorites
            if self.favoriteShows:
                options.append("-" * 30)
                for show in sorted(self.favoriteShows):
                    options.append(show)
                options.append("-" * 30)
                options.append("Clear All")

            options.append("Done")

            select = xbmcgui.Dialog().select("Manage Favorite Shows", options)

            if select < 0 or options[select] == "Done":
                break
            elif options[select] == "Add Show from Library":
                self.addShowFromLibrary()
            elif options[select] == "Add Show Manually":
                keyboard = xbmc.Keyboard("", "Enter show name")
                keyboard.doModal()
                if keyboard.isConfirmed():
                    showName = keyboard.getText().strip()
                    if showName and showName not in self.favoriteShows:
                        self.favoriteShows.append(showName)
                        self.saveFavoriteShows()
                        xbmc.executebuiltin(
                            'Notification(%s, Added "%s" to favorites, 3000, %s)'
                            % (ADDON_NAME, showName, ICON)
                        )
                        # Rescan EPG
                        self.scanEPGForFavorites()
            elif options[select] == "Clear All":
                if xbmcgui.Dialog().yesno("Clear All", "Remove all favorite shows?"):
                    self.favoriteShows = []
                    self.saveFavoriteShows()
            elif options[select] in self.favoriteShows:
                # Long press simulation - ask to remove
                if xbmcgui.Dialog().yesno(
                    "Remove Show", 'Remove "%s" from favorites?' % options[select]
                ):
                    self.favoriteShows.remove(options[select])
                    self.saveFavoriteShows()

    def addShowFromLibrary(self):
        """Add favorite show by selecting from library"""
        self.log("addShowFromLibrary")

        try:
            # Get all TV shows from library
            json_query = {
                "jsonrpc": "2.0",
                "method": "VideoLibrary.GetTVShows",
                "params": {
                    "properties": ["title", "year", "episode"],
                    "sort": {"order": "ascending", "method": "title"},
                },
                "id": 1,
            }

            result = xbmc.executeJSONRPC(json.dumps(json_query))
            result = json.loads(result)

            if "result" in result and "tvshows" in result["result"]:
                tvshows = result["result"]["tvshows"]

                # Build list for multiselect dialog
                showList = []
                showTitles = []
                preselect = []

                for i, show in enumerate(tvshows):
                    title = show["title"]
                    showTitles.append(title)
                    # Format with episode count
                    label = "%s (%d episodes)" % (title, show.get("episode", 0))
                    showList.append(label)
                    # Pre-select if already in favorites
                    if title in self.favoriteShows:
                        preselect.append(i)

                # Show multiselect dialog
                selected = xbmcgui.Dialog().multiselect(
                    "Select Shows to Add to Favorites", showList, preselect=preselect
                )

                if selected is not None:  # None means cancelled
                    # Update favorites based on selection
                    # First, remove any shows that were deselected
                    for i, title in enumerate(showTitles):
                        if (
                            i in preselect
                            and i not in selected
                            and title in self.favoriteShows
                        ):
                            self.favoriteShows.remove(title)

                    # Then add any newly selected shows
                    addedShows = []
                    for i in selected:
                        if (
                            i not in preselect
                            and showTitles[i] not in self.favoriteShows
                        ):
                            self.favoriteShows.append(showTitles[i])
                            addedShows.append(showTitles[i])

                    if addedShows:
                        self.saveFavoriteShows()
                        xbmc.executebuiltin(
                            "Notification(%s, Added %d shows to favorites, 3000, %s)"
                            % (ADDON_NAME, len(addedShows), ICON)
                        )
                        # Rescan EPG
                        self.scanEPGForFavorites()
            else:
                xbmcgui.Dialog().ok("Library", "No TV shows found in library")

        except Exception as e:
            self.log("Error in addShowFromLibrary: " + str(e))
            xbmcgui.Dialog().ok("Error", "Could not load TV shows from library")

    def viewUpcomingFavorites(self):
        """View upcoming airings of favorite shows"""
        if not self.favoriteShowsNextAiring:
            xbmcgui.Dialog().ok(
                "Upcoming Shows", "No favorite shows found in the next 30 minutes"
            )
            return

        options = []
        # Sort by start time
        sortedShows = sorted(
            self.favoriteShowsNextAiring.items(), key=lambda x: x[1][1]
        )  # Sort by start time

        for showName, (channelNum, startTime, endTime, fullTitle) in sortedShows:
            timeUntil = startTime - time.time()
            channelName = (
                self.channels[channelNum - 1].name
                if channelNum <= self.maxChannels
                else "Unknown"
            )

            if timeUntil > 60:  # More than 1 minute away
                minutes = int(timeUntil / 60)
                timeStr = "in %d min" % minutes
            elif timeUntil > 0:  # Less than 1 minute away
                timeStr = "Starting now"
            else:  # Already started
                minutesAgo = int(abs(timeUntil) / 60)
                if minutesAgo == 0:
                    timeStr = "Just started"
                else:
                    timeStr = "Started %d min ago" % minutesAgo

            options.append(
                "%s - Ch %d: %s (%s)" % (fullTitle, channelNum, channelName, timeStr)
            )

        if options:
            select = xbmcgui.Dialog().select("Upcoming Favorite Shows", options)
            if select >= 0:
                # Extract channel number from selection
                showInfo = sortedShows[select]
                channelNum = showInfo[1][0]

                # Ask if user wants to jump to this channel
                if xbmcgui.Dialog().yesno(
                    "Jump to Channel", "Switch to channel %d now?" % channelNum
                ):
                    self.background.setVisible(True)
                    self.setChannel(channelNum)
                    self.background.setVisible(False)
        else:
            xbmcgui.Dialog().ok("Upcoming Shows", "No favorite shows found")

    def readConfig(self):
        """Read all configuration settings"""
        self.log("readConfig")

        # Sleep timer (30 minute increments)
        self.sleepTimeValue = int(ADDON.getSetting("AutoOff")) * 1800
        self.log("Auto off is " + str(self.sleepTimeValue))

        # Display settings
        self.infoOnChange = ADDON.getSetting("InfoOnChange") == "true"
        self.showChannelBug = ADDON.getSetting("ShowChannelBug") == "true"
        self.showNextItem = ADDON.getSetting("EnableComingUp") == "true"
        self.hideShortItems = ADDON.getSetting("HideClips") == "true"

        # Channel settings
        self.forceReset = ADDON.getSetting("ForceChannelReset") == "true"
        self.channelResetSetting = ADDON.getSetting("ChannelResetSetting")
        self.backgroundUpdating = int(ADDON.getSetting("ThreadMode"))

        # Navigation settings
        self.shortItemLength = SHORT_CLIP_ENUM[int(ADDON.getSetting("ClipLength"))]
        self.seekForward = SEEK_FORWARD[int(ADDON.getSetting("SeekForward"))]
        self.seekBackward = SEEK_BACKWARD[int(ADDON.getSetting("SeekBackward"))]

        # Channel logos
        self.channelLogos = translatePath(ADDON.getSetting("ChannelLogoFolder"))
        if not FileAccess.exists(self.channelLogos):
            self.channelLogos = LOGOS_LOC
        self.log("Channel logo folder - " + self.channelLogos)

        # Load channel list
        self.channelList = ChannelList()
        self.channelList.myOverlay = self
        self.channels = self.channelList.setupList()

        if self.channels is None:
            self.log("readConfig No channel list returned")
            self.end()
            return False

        self.Player.stop()
        self.log("readConfig return")
        return True

    def toggleBlackout(self):
        """Toggle blackout mode"""
        self.blackoutActive = not self.blackoutActive
        self.blackoutControl.setVisible(self.blackoutActive)

        if self.blackoutActive:
            xbmc.executebuiltin(
                "Notification(%s, Blackout Activated, 2000, %s)" % (ADDON_NAME, ICON)
            )
        else:
            xbmc.executebuiltin(
                "Notification(%s, Blackout Deactivated, 2000, %s)" % (ADDON_NAME, ICON)
            )

    def setChannel(self, channel):
        """Set the channel and start playback"""
        self.log("setChannel " + str(channel))
        # Add this debug line to see the call stack
        import traceback

        self.log("setChannel called from: " + "".join(traceback.format_stack()[-2:-1]))
        self.runActions(
            RULES_ACTION_OVERLAY_SET_CHANNEL, channel, self.channels[channel - 1]
        )

        if self.Player.stopped:
            self.log("setChannel player already stopped", xbmc.LOGERROR)
            return

        if channel < 1 or channel > self.maxChannels:
            self.log("setChannel invalid channel " + str(channel), xbmc.LOGERROR)
            return

        if self.channels[channel - 1].isValid == False:
            self.log("setChannel channel not valid " + str(channel), xbmc.LOGERROR)
            return

        # Initialize flags at the start
        showCalendarAfterPlayback = False
        showRecentlyAddedAfterPlayback = False
        
        # NEW: Handle channel 99 with page cycling (calendar <-> recently added)
        if channel == 99:
            # Set window property to activate channel 99 visualization mode
            xbmcgui.Window(10000).setProperty("PTV.Channel99", "true")
            self.log("Channel 99 visualization mode activated")
            
            # Start page cycling when tuning to channel 99
            if not self.showingCalendar and not self.showingRecentlyAdded:
                self.log("Channel 99 detected - starting page cycling")
                startChannel99CyclingAfterPlayback = True
            else:
                startChannel99CyclingAfterPlayback = False
        else:
            # Clear window property to deactivate channel 99 visualization mode
            xbmcgui.Window(10000).clearProperty("PTV.Channel99")
            self.log("Channel 99 visualization mode deactivated")
            
            startChannel99CyclingAfterPlayback = False
            # Stop page cycling if switching away from channel 99
            if self.showingCalendar or self.showingRecentlyAdded or self.showingRecommendations or self.showingServerStats or self.showingMySQLStats or self.showingKodiBoxStats or self.showingWikipedia:
                self.log("Leaving channel 99 - stopping page cycling")
                self.stopChannel99PageCycling()

        # Save previous channel
        if self.currentChannel != channel:
            self.previousChannel = self.currentChannel

        self.lastActionTime = 0
        timedif = 0
        self.getControl(102).setVisible(False)
        self.getControl(103).setImage("")
        self.showingInfo = False

        # Save current channel state
        if self.Player.isPlaying():
            if channel != self.currentChannel:
                self.channels[self.currentChannel - 1].setPaused(
                    xbmc.getCondVisibility("Player.Paused")
                )

                # Automatically pause in serial mode
                if self.channels[self.currentChannel - 1].mode & MODE_ALWAYSPAUSE > 0:
                    self.channels[self.currentChannel - 1].setPaused(True)

                self.channels[self.currentChannel - 1].setShowTime(
                    self.Player.getTime()
                )
                self.channels[self.currentChannel - 1].setShowPosition(
                    xbmc.PlayList(xbmc.PLAYLIST_MUSIC).getposition()
                )
                self.channels[self.currentChannel - 1].setAccessTime(time.time())

        self.currentChannel = channel

        # Load channel playlist
        xbmc.PlayList(xbmc.PLAYLIST_MUSIC).clear()
        if (
            xbmc.PlayList(xbmc.PLAYLIST_MUSIC).load(self.channels[channel - 1].fileName)
            == False
        ):
            self.log("Error loading playlist", xbmc.LOGERROR)
            self.InvalidateChannel(channel)
            return

        # Disable shuffle
        if xbmc.getInfoLabel("Playlist.Random").lower() == "random":
            self.log("Random on. Disabling.")
            xbmc.PlayList(xbmc.PLAYLIST_MUSIC).unshuffle()

        xbmc.executebuiltin("PlayerControl(RepeatAll)")

        # Calculate time difference
        curtime = time.time()
        timedif = curtime - self.channels[self.currentChannel - 1].lastAccessTime

        # Adjust show position if not paused
        if self.channels[self.currentChannel - 1].isPaused == False:
            while (
                self.channels[self.currentChannel - 1].showTimeOffset + timedif
                > self.channels[self.currentChannel - 1].getCurrentDuration()
            ):
                timedif -= (
                    self.channels[self.currentChannel - 1].getCurrentDuration()
                    - self.channels[self.currentChannel - 1].showTimeOffset
                )
                self.channels[self.currentChannel - 1].addShowPosition(1)
                self.channels[self.currentChannel - 1].setShowTime(0)

        xbmc.sleep(self.channelDelay)

        # Start playback
        self.Player.playselected(
            self.channels[self.currentChannel - 1].playlistPosition
        )

        self.channels[self.currentChannel - 1].setAccessTime(curtime)

        # Handle paused channels
        if self.channels[self.currentChannel - 1].isPaused:
            self.channels[self.currentChannel - 1].setPaused(False)
            try:
                self.Player.seekTime(
                    self.channels[self.currentChannel - 1].showTimeOffset
                )
                if self.channels[self.currentChannel - 1].mode & MODE_ALWAYSPAUSE == 0:
                    self.Player.pause()
                    if self.waitForVideoPaused() == False:
                        return
            except:
                self.log("Exception during seek on paused channel", xbmc.LOGERROR)
        else:
            # Seek to proper time
            seektime = (
                self.channels[self.currentChannel - 1].showTimeOffset
                + timedif
                + int((time.time() - curtime))
            )
            try:
                self.Player.seekTime(seektime)
            except:
                self.log("Unable to set proper seek time, trying different value")
                try:
                    seektime = (
                        self.channels[self.currentChannel - 1].showTimeOffset + timedif
                    )
                    self.Player.seekTime(seektime)
                except:
                    self.log("Exception during seek", xbmc.LOGERROR)

        self.showChannelLabel(self.currentChannel)
        self.lastActionTime = time.time()
        
        # NEW: Start channel 99 page cycling after playback has started
        if startChannel99CyclingAfterPlayback:
            # Small delay to ensure playback is running
            xbmc.sleep(500)
            self.startChannel99PageCycling()
            self.log("Channel 99 page cycling activated")
        
        self.runActions(
            RULES_ACTION_OVERLAY_SET_CHANNEL_END, channel, self.channels[channel - 1]
        )
        self.log("setChannel return")

    def showChannelLabel(self, channel):
        """Display the channel number"""
        self.log("showChannelLabel " + str(channel))

        # Cancel existing timer
        if self.channelLabelTimer.isAlive():
            self.channelLabelTimer.cancel()
            self.channelLabelTimer = threading.Timer(5.0, self.hideChannelLabel)

        # Format channel number
        if ADDON.getSetting("HideLeadingZero") == "false" and channel < 10:
            channelStr = "0" + str(channel)
        else:
            channelStr = str(channel)

        # ADD THIS LINE to set window property
        self.setProperty("PTV.ChannelNumber", channelStr)

        # Display channel number
        self.channelNumberLabel.setLabel(channelStr)
        self.channelNumberShadow.setLabel(channelStr)
        self.channelNumberLabel.setVisible(True)
        self.channelNumberShadow.setVisible(True)

        # Show info based on context
        if self.inputChannel > 0:
            # Manual channel entry - always show info
            self.infoOffset = 0
            self.showInfo(5.0)
        elif self.inputChannel == -1 and self.infoOnChange == True:
            # Channel up/down - show based on setting
            self.infoOffset = 0
            self.showInfo(5.0)

        # Show channel bug
        if self.showChannelBug == True:
            self.updateChannelBug()

        # Hide Kodi info if showing
        if xbmc.getCondVisibility("Player.ShowInfo"):
            json_query = '{"jsonrpc": "2.0", "method": "Input.Info", "id": 1}'
            self.ignoreInfoAction = True
            self.channelList.sendJSON(json_query)

        # Start timer
        self.channelLabelTimer.name = "ChannelLabel"
        self.channelLabelTimer.start()
        self.startNotificationTimer(10.0)
        self.log("showChannelLabel return")

    def hideChannelLabel(self):
        """Hide the channel number display"""
        self.log("hideChannelLabel")
        self.channelLabelTimer = threading.Timer(10.0, self.hideChannelLabel)

        self.channelNumberLabel.setVisible(False)
        self.channelNumberShadow.setVisible(False)
        self.inputChannel = -1

        # ADD THIS LINE to clear property
        self.setProperty("PTV.ChannelNumber", "")

        self.log("hideChannelLabel return")

    def updateChannelBug(self):
        """Update the channel bug/watermark"""
        if not self.showChannelBug:
            self.getControl(103).setImage("")
            return

        try:
            channelName = self.channels[self.currentChannel - 1].name
            logoPath = self.channelLogos + ascii(channelName) + ".png"

            if FileAccess.exists(logoPath):
                bugPath = CHANNELBUG_LOC + ascii(channelName) + ".png"

                # Generate bug if it doesn't exist
                if not FileAccess.exists(bugPath) and PIL_AVAILABLE:
                    try:
                        original = Image.open(logoPath)
                        if original.mode != "RGBA":
                            original = original.convert("RGBA")

                        # Resize to fit
                        original.thumbnail((220, 155), Image.ANTIALIAS)

                        # Make semi-transparent
                        alpha = original.split()[-1]
                        alpha = ImageEnhance.Brightness(alpha).enhance(0.4)
                        original.putalpha(alpha)

                        original.save(bugPath)
                    except Exception as e:
                        self.log("Error creating channel bug: " + str(e))
                        self.getControl(103).setImage("")
                        return

                if FileAccess.exists(bugPath):
                    self.getControl(103).setImage(bugPath)
                else:
                    self.getControl(103).setImage(logoPath)
            else:
                self.getControl(103).setImage("")
        except Exception as e:
            self.log("Error updating channel bug: " + str(e))
            self.getControl(103).setImage("")

    def showInfo(self, timer):
        """Show the info display"""
        if self.hideShortItems:
            position = xbmc.PlayList(xbmc.PLAYLIST_MUSIC).getposition()
            if (
                self.channels[self.currentChannel - 1].getItemDuration(position)
                < self.shortItemLength
            ):
                return

        self.getControl(103).setVisible(True)
        self.getControl(102).setVisible(True)
        self.showingInfo = True
        self.setShowInfo()

        # Also show channel number when info is displayed
        if ADDON.getSetting("HideLeadingZero") == "false" and self.currentChannel < 10:
            channelStr = "0" + str(self.currentChannel)
        else:
            channelStr = str(self.currentChannel)

        # Display channel number
        self.channelNumberLabel.setLabel(channelStr)
        self.channelNumberShadow.setLabel(channelStr)
        self.channelNumberLabel.setVisible(True)
        self.channelNumberShadow.setVisible(True)

        # Reset timer
        if self.infoTimer.isAlive():
            self.infoTimer.cancel()

        self.infoTimer = threading.Timer(timer, self.hideInfo)
        self.infoTimer.name = "InfoTimer"

        if xbmc.getCondVisibility("Player.ShowInfo"):
            json_query = '{"jsonrpc": "2.0", "method": "Input.Info", "id": 1}'
            self.ignoreInfoAction = True
            self.channelList.sendJSON(json_query)

        self.infoTimer.start()

    def hideInfo(self):
        """Hide the info display"""
        self.getControl(102).setVisible(False)
        self.getControl(103).setVisible(True)
        self.infoOffset = 0
        self.showingInfo = False

        # Also hide channel number when info is hidden
        self.channelNumberLabel.setVisible(False)
        self.channelNumberShadow.setVisible(False)

        if self.infoTimer.isAlive():
            self.infoTimer.cancel()

        self.infoTimer = threading.Timer(5.0, self.hideInfo)

    def setShowInfo(self):
        """Update the info display content"""
        self.log("setShowInfo")

        try:
            # Determine position
            if self.hideShortItems and self.infoOffset != 0:
                position = xbmc.PlayList(xbmc.PLAYLIST_MUSIC).getposition()
                curoffset = 0
                modifier = 1 if self.infoOffset > 0 else -1

                while curoffset != abs(self.infoOffset):
                    position = self.channels[self.currentChannel - 1].fixPlaylistIndex(
                        position + modifier
                    )
                    if (
                        self.channels[self.currentChannel - 1].getItemDuration(position)
                        >= self.shortItemLength
                    ):
                        curoffset += 1
            else:
                position = (
                    xbmc.PlayList(xbmc.PLAYLIST_MUSIC).getposition() + self.infoOffset
                )

            # Get info
            if self.infoOffset > 0:
                label = LANGUAGE(30041)  # Coming Up
            elif self.infoOffset < 0:
                label = LANGUAGE(30042)  # Previously
            else:
                label = LANGUAGE(30043)  # Now Playing

            title = self.channels[self.currentChannel - 1].getItemTitle(position)
            episode = self.channels[self.currentChannel - 1].getItemEpisodeTitle(
                position
            )
            description = self.channels[self.currentChannel - 1].getItemDescription(
                position
            )

            # Set controls
            self.getControl(502).setLabel(label)
            self.getControl(503).setLabel(title)
            self.getControl(504).setLabel(episode)
            self.getControl(505).setText(description)

            # Set channel icon
            logoPath = (
                self.channelLogos
                + ascii(self.channels[self.currentChannel - 1].name)
                + ".png"
            )
            if not FileAccess.exists(logoPath):
                logoPath = IMAGES_LOC + "Default.png"
            self.getControl(506).setImage(logoPath)

        except Exception as e:
            self.log("Error in setShowInfo: " + str(e), xbmc.LOGERROR)

        self.log("setShowInfo return")

    def showWeatherOverlay(self, persistent=False):
        """Display weather information as a custom overlay within PseudoTV"""
        self.log("showWeatherOverlay - STARTED")

        # Check if weather addon exists
        hasWeatherAddon = (
            xbmc.getCondVisibility("System.HasAddon(weather.multi)")
            or xbmc.getCondVisibility(
                "System.HasAddon(weather.openweathermap.extended)"
            )
            or xbmc.getCondVisibility("System.HasAddon(weather.gismeteo)")
        )

        if not hasWeatherAddon:
            xbmc.executebuiltin(
                "Notification(%s, No weather addon installed, 3000, %s)"
                % (ADDON_NAME, ICON)
            )
            return

        # Show weather overlay
        self.showingWeather = True
        self.setProperty("PTV.Weather", "true")

        # Update weather information
        self.updateWeatherInfo()

        # NEW: Only set auto-hide timer if NOT persistent
        if not persistent:
            # Auto-hide after 100 seconds (for manual weather button press)
            if (
                hasattr(self, "weatherTimer")
                and self.weatherTimer is not None
                and self.weatherTimer.isAlive()
            ):
                self.weatherTimer.cancel()

            self.weatherTimer = threading.Timer(100.0, self.hideWeatherOverlay)
            self.weatherTimer.start()
        else:
            # Cancel any existing timer for persistent mode
            if (
                hasattr(self, "weatherTimer")
                and self.weatherTimer is not None
                and self.weatherTimer.isAlive()
            ):
                self.weatherTimer.cancel()
            self.log("Weather overlay in persistent mode (no auto-hide)")

        self.log("showWeatherOverlay - COMPLETED")

    def updateWeatherInfo(self):
        """Update weather information properties with current data"""
        self.log("updateWeatherInfo")

        try:
            # Get weather information from Kodi
            weatherLocation = xbmc.getInfoLabel("Weather.Location")
            weatherTemp = xbmc.getInfoLabel("Weather.Temperature")
            weatherConditions = xbmc.getInfoLabel("Weather.Conditions")

            # Log what we're getting
            self.log(
                'Weather update - Location: "%s", Temp: "%s", Conditions: "%s"'
                % (weatherLocation, weatherTemp, weatherConditions)
            )

            # Update the properties
            self.setProperty("PTV.Weather.Location", weatherLocation)
            self.setProperty("PTV.Weather.Temperature", weatherTemp)
            self.setProperty("PTV.Weather.Conditions", weatherConditions)
            self.setProperty(
                "PTV.Weather.Humidity", xbmc.getInfoLabel("Weather.Humidity")
            )
            self.setProperty(
                "PTV.Weather.WindSpeed", xbmc.getInfoLabel("Weather.WindSpeed")
            )
            self.setProperty(
                "PTV.Weather.FeelsLike", xbmc.getInfoLabel("Weather.FeelsLike")
            )

            # Get current weather icon and extract just the filename
            weatherIcon = xbmc.getInfoLabel(
                "Window(Weather).Property(Current.ConditionIcon)"
            )
            if weatherIcon:
                # Extract just the filename (e.g., "29.png") from the full path
                import os

                iconFilename = os.path.basename(weatherIcon)
                self.setProperty("PTV.Weather.CurrentIcon", iconFilename)
            else:
                self.setProperty("PTV.Weather.CurrentIcon", "")

            # Update hourly forecast
            for i in range(6):
                hourTime = xbmc.getInfoLabel(
                    "Window(Weather).Property(Hourly.%d.Time)" % (i + 1)
                )
                hourTemp = xbmc.getInfoLabel(
                    "Window(Weather).Property(Hourly.%d.Temperature)" % (i + 1)
                )
                hourIcon = xbmc.getInfoLabel(
                    "Window(Weather).Property(Hourly.%d.OutlookIcon)" % (i + 1)
                )
                hourCondition = xbmc.getInfoLabel(
                    "Window(Weather).Property(Hourly.%d.Outlook)" % (i + 1)
                )

                # Extract just the filename for hourly icons too
                if hourIcon:
                    import os

                    hourIconFilename = os.path.basename(hourIcon)
                    self.setProperty("PTV.Weather.Hour%d.Icon" % i, hourIconFilename)
                else:
                    self.setProperty("PTV.Weather.Hour%d.Icon" % i, "")

                self.setProperty("PTV.Weather.Hour%d.Time" % i, hourTime)
                self.setProperty("PTV.Weather.Hour%d.Temp" % i, hourTemp)
                self.setProperty("PTV.Weather.Hour%d.Condition" % i, hourCondition)

            # If conditions are "Busy" or empty, try again after a delay
            if (
                weatherConditions == "Busy" or not weatherConditions
            ) and self.showingWeather:
                self.log('Weather conditions showing "Busy" or empty, retrying...')
                updateTimer = threading.Timer(1.0, self.updateWeatherInfo)
                updateTimer.start()

        except Exception as e:
            self.log("Error updating weather information: " + str(e), xbmc.LOGERROR)

    def hideWeatherOverlay(self):
        """Hide the weather overlay"""
        self.log("hideWeatherOverlay")
        self.showingWeather = False
        self.setProperty("PTV.Weather", "false")

        # FIX: Check if weatherTimer exists AND is not None before checking isAlive()
        if hasattr(self, "weatherTimer") and self.weatherTimer is not None and self.weatherTimer.isAlive():
            self.weatherTimer.cancel()

        self.log("hideWeatherOverlay return")

    def refreshWeatherData(self):
        """Refresh weather data in the background"""
        # This method is called periodically but we don't need to do anything
        # since weather data will be fetched when needed
        self.log("refreshWeatherData - periodic check")

    def weatherRefreshAction(self):
        """Periodically refresh weather data"""
        self.refreshWeatherData()
        # Restart timer
        self.weatherRefreshTimer = threading.Timer(1800.0, self.weatherRefreshAction)
        if not self.isExiting:
            self.weatherRefreshTimer.start()

    def fetchSonarrCalendar(self):
        """Fetch upcoming episodes from Sonarr API"""
        self.log("fetchSonarrCalendar - STARTED")
        
        # Check if Sonarr is enabled
        sonarrEnabled = ADDON.getSetting("SonarrEnabled") == "true"
        if not sonarrEnabled:
            self.log("Sonarr is disabled in settings")
            return []
        
        sonarrUrl = ADDON.getSetting("SonarrURL")
        sonarrApiKey = ADDON.getSetting("SonarrAPIKey")
        
        if not sonarrUrl or not sonarrApiKey:
            self.log("Sonarr URL or API key not configured")
            return []
        
        try:
            import urllib2
            # Import datetime with aliases to avoid conflicts
            from datetime import datetime as DT, date as DATE, timedelta as TIMEDELTA
            
            # Get date range (today + 7 days)
            today = DATE.today()
            endDate = today + TIMEDELTA(days=7)
            
            # Format dates for API
            startStr = today.strftime("%Y-%m-%d")
            endStr = endDate.strftime("%Y-%m-%d")
            
            # Build API URL - ensure no trailing slash issues
            baseUrl = sonarrUrl.rstrip('/')
            url = "%s/api/v3/calendar?start=%s&end=%s" % (baseUrl, startStr, endStr)
            
            self.log("Fetching Sonarr calendar from: " + url)
            
            # Create request with API key header
            request = urllib2.Request(url)
            request.add_header("X-Api-Key", sonarrApiKey)
            
            # Fetch data with timeout
            try:
                response = urllib2.urlopen(request, timeout=10)
                data = response.read()
                self.log("Sonarr API response received, length: %d bytes" % len(data))
            except urllib2.URLError as e:
                self.log("URLError fetching Sonarr: " + str(e), xbmc.LOGERROR)
                if hasattr(e, 'code'):
                    self.log("HTTP Error Code: %d" % e.code, xbmc.LOGERROR)
                if hasattr(e, 'reason'):
                    self.log("Reason: %s" % str(e.reason), xbmc.LOGERROR)
                return []
            except Exception as e:
                self.log("Error fetching Sonarr: " + str(e), xbmc.LOGERROR)
                return []
            
            # Parse JSON
            try:
                calendar = json.loads(data)
                self.log("Parsed Sonarr JSON: %d episodes found" % len(calendar))
            except Exception as e:
                self.log("Error parsing Sonarr JSON: " + str(e), xbmc.LOGERROR)
                self.log("Raw data preview: " + data[:200], xbmc.LOGERROR)
                return []
            
            # Build a cache of series info (seriesId -> series details)
            self.log("Building series cache from calendar data...")
            seriesCache = {}
            uniqueSeriesIds = set()
            
            # First pass: collect all unique series IDs
            for item in calendar:
                seriesId = item.get('seriesId')
                if seriesId:
                    uniqueSeriesIds.add(seriesId)
            
            self.log("Found %d unique series in calendar" % len(uniqueSeriesIds))
            
            # Fetch series details for each unique series ID
            for seriesId in uniqueSeriesIds:
                try:
                    seriesUrl = "%s/api/v3/series/%d" % (baseUrl, seriesId)
                    self.log("Fetching series details: " + seriesUrl)
                    
                    seriesRequest = urllib2.Request(seriesUrl)
                    seriesRequest.add_header("X-Api-Key", sonarrApiKey)
                    
                    seriesResponse = urllib2.urlopen(seriesRequest, timeout=5)
                    seriesData = seriesResponse.read()
                    seriesInfo = json.loads(seriesData)
                    
                    seriesCache[seriesId] = seriesInfo
                    self.log("Cached series: %s (ID: %d)" % (seriesInfo.get('title', 'Unknown'), seriesId))
                    
                except Exception as e:
                    self.log("Error fetching series %d: %s" % (seriesId, str(e)))
                    continue
            
            self.log("Series cache built with %d entries" % len(seriesCache))
            
            # Process episodes
            episodes = []
            for item in calendar:
                try:
                    # Parse air date and time - CONVERT TO LOCAL TIME FIRST
                    airDateUtc = item.get('airDateUtc', '')
                    airTime = ""
                    localAirDateTime = None

                    if airDateUtc:
                        try:
                            import time as time_module
                            import calendar as cal_module
                            
                            # Parse UTC time using DT alias
                            utcTime = DT.strptime(airDateUtc, "%Y-%m-%dT%H:%M:%SZ")
                            
                            # Convert to timestamp
                            utcTimestamp = cal_module.timegm(utcTime.timetuple())
                            
                            # Convert to local time using time module
                            localTimeStruct = time_module.localtime(utcTimestamp)
                            localYear = localTimeStruct.tm_year
                            localMonth = localTimeStruct.tm_mon
                            localDay = localTimeStruct.tm_mday
                            localHour = localTimeStruct.tm_hour
                            localMin = localTimeStruct.tm_min
                            
                            # Build datetime object manually using DT alias
                            localAirDateTime = DT(localYear, localMonth, localDay, localHour, localMin)
                            
                            # Format as 12-hour time
                            airTime = localAirDateTime.strftime("%I:%M %p").lstrip('0')
                            
                        except Exception as e:
                            self.log("Error parsing UTC time: %s" % str(e))
                            localAirDateTime = None

                    # Use LOCAL date for comparison, not Sonarr's airDate
                    if localAirDateTime:
                        airDate = localAirDateTime.date()
                    else:
                        # Fallback to Sonarr's date if we can't parse UTC time
                        airDateStr = item.get('airDate', '')
                        if not airDateStr:
                            continue
                        
                        # Parse date manually without strptime (avoid the None bug)
                        try:
                            dateParts = airDateStr.split('-')
                            year = int(dateParts[0])
                            month = int(dateParts[1])
                            day = int(dateParts[2])
                            airDate = DATE(year, month, day)
                        except:
                            self.log("Could not parse date: %s" % airDateStr)
                            continue

                    daysUntil = (airDate - today).days
                    isToday = (daysUntil == 0)
                    
                    # Format day string
                    if isToday:
                        dayStr = "Today"
                    elif daysUntil == 1:
                        dayStr = "Tomorrow"
                    elif daysUntil <= 7:
                        dayStr = airDate.strftime("%A")
                    else:
                        dayStr = airDate.strftime("%m/%d")
                    
                    # Get series info from cache
                    seriesId = item.get('seriesId')
                    seriesTitle = 'Unknown Show'
                    seriesImages = []
                    
                    if seriesId and seriesId in seriesCache:
                        seriesInfo = seriesCache[seriesId]
                        seriesTitle = seriesInfo.get('title', 'Unknown Show')
                        seriesImages = seriesInfo.get('images', [])
                        self.log("Using series: %s (ID: %d)" % (seriesTitle, seriesId))
                    else:
                        self.log("WARNING: Series ID %s not in cache" % str(seriesId))
                    
                    # Get episode info
                    seasonNumber = item.get('seasonNumber', 0)
                    episodeNumber = item.get('episodeNumber', 0)
                    episodeTitle = item.get('title', '')
                    
                    # Check if downloaded
                    hasFile = item.get('hasFile', False)
                    
                    # Determine status
                    if hasFile:
                        status = "âœ“ Downloaded"
                    elif isToday:
                        if airTime:
                            status = "Airing at %s" % airTime  
                        else:
                            status = "â˜… Airing Today"
                    else:
                        if airTime:
                            status = "%s at %s" % (dayStr, airTime)
                        else:
                            status = dayStr
                    
                    # Get artwork - TRY LIBRARY FIRST, then Sonarr series images from cache
                    poster = ""
                    libraryPoster = self.getLibraryPosterForShow(seriesTitle)
                    if libraryPoster:
                        poster = libraryPoster
                    else:
                        # Use images from cache (seriesImages)
                        for image in seriesImages:
                            if image.get('coverType') == 'poster':
                                poster = image.get('remoteUrl', '')
                                break
                        
                        # Fallback to fanart if no poster
                        if not poster:
                            for image in seriesImages:
                                if image.get('coverType') == 'fanart':
                                    poster = image.get('remoteUrl', '')
                                    break

                    if not poster:
                        self.log("WARNING: No poster found for " + seriesTitle)
                    
                    # Create episode object
                    episode = {
                        'type': 'tv',
                        'seriesTitle': seriesTitle,
                        'season': seasonNumber,
                        'episode': episodeNumber,
                        'title': episodeTitle,
                        'airDate': airDate,
                        'airTime': airTime,
                        'isToday': isToday,
                        'daysUntil': daysUntil,
                        'dayStr': dayStr,
                        'status': status,
                        'hasFile': hasFile,
                        'poster': poster
                    }
                    
                    episodes.append(episode)
                    self.log("Added episode: %s S%02dE%02d" % (seriesTitle, seasonNumber, episodeNumber))
                    
                except Exception as e:
                    self.log("Error parsing Sonarr episode: " + str(e), xbmc.LOGERROR)
                    import traceback
                    self.log("Traceback: " + traceback.format_exc(), xbmc.LOGERROR)
                    continue
            
            self.log("fetchSonarrCalendar - Returning %d episodes" % len(episodes))
            return episodes
            
        except Exception as e:
            self.log("Error in fetchSonarrCalendar: " + str(e), xbmc.LOGERROR)
            import traceback
            self.log("Traceback: " + traceback.format_exc(), xbmc.LOGERROR)
            return []


    def fetchRadarrCalendar(self):
        """Fetch upcoming movies from Radarr API"""
        self.log("fetchRadarrCalendar - STARTED")
        
        # Check if Radarr is enabled
        radarrEnabled = ADDON.getSetting("RadarrEnabled") == "true"
        if not radarrEnabled:
            self.log("Radarr is disabled in settings")
            return []
        
        radarrUrl = ADDON.getSetting("RadarrURL")
        radarrApiKey = ADDON.getSetting("RadarrAPIKey")
        
        if not radarrUrl or not radarrApiKey:
            self.log("Radarr URL or API key not configured")
            return []
        
        try:
            import urllib2
            from datetime import datetime, date, timedelta
            
            # Get date range
            today = date.today()
            endDate = today + timedelta(days=30)  # Movies: look ahead 30 days
            
            # Build API URL for calendar
            startStr = today.strftime("%Y-%m-%d")
            endStr = endDate.strftime("%Y-%m-%d")
            
            baseUrl = radarrUrl.rstrip('/')
            url = "%s/api/v3/calendar?start=%s&end=%s" % (baseUrl, startStr, endStr)
            
            self.log("Fetching Radarr calendar from: " + url)
            
            # Create request
            request = urllib2.Request(url)
            request.add_header("X-Api-Key", radarrApiKey)
            
            # Fetch data
            try:
                response = urllib2.urlopen(request, timeout=10)
                data = response.read()
                self.log("Radarr API response received, length: %d bytes" % len(data))
            except urllib2.URLError as e:
                self.log("URLError fetching Radarr: " + str(e), xbmc.LOGERROR)
                if hasattr(e, 'code'):
                    self.log("HTTP Error Code: %d" % e.code, xbmc.LOGERROR)
                if hasattr(e, 'reason'):
                    self.log("Reason: %s" % str(e.reason), xbmc.LOGERROR)
                return []
            except Exception as e:
                self.log("Error fetching Radarr: " + str(e), xbmc.LOGERROR)
                return []
            
            # Parse JSON
            try:
                calendar = json.loads(data)
                self.log("Parsed Radarr JSON: %d movies found" % len(calendar))
            except Exception as e:
                self.log("Error parsing Radarr JSON: " + str(e), xbmc.LOGERROR)
                self.log("Raw data preview: " + data[:200], xbmc.LOGERROR)
                return []
            
            # Process movies
            movies = []
            for item in calendar:
                try:
                    # Parse release date
                    releaseDateStr = item.get('physicalRelease') or item.get('digitalRelease') or item.get('inCinemas', '')
                    if not releaseDateStr:
                        continue
                    
                    releaseDate = datetime.strptime(releaseDateStr.split('T')[0], "%Y-%m-%d").date()
                    isToday = releaseDate == today
                    
                    # Calculate days until release
                    daysUntil = (releaseDate - today).days
                    
                    # Format day string
                    if isToday:
                        dayStr = "Today"
                    elif daysUntil == 1:
                        dayStr = "Tomorrow"
                    elif daysUntil <= 7:
                        dayStr = releaseDate.strftime("%A")
                    else:
                        dayStr = releaseDate.strftime("%m/%d/%Y")
                    
                    # Get movie info
                    title = item.get('title', 'Unknown Movie')
                    year = item.get('year', '')
                    
                    # Check if downloaded
                    hasFile = item.get('hasFile', False)
                    
                    # Determine status
                    if hasFile:
                        status = "âœ“ Available"
                    elif isToday:
                        status = "â˜… Releasing Today"
                    else:
                        status = "Releases %s" % dayStr
                    
                    # Get poster - TRY LIBRARY FIRST, then Radarr remote URLs
                    poster = ""

                    # First, try to get poster from Kodi library
                    libraryPoster = self.getLibraryPosterForMovie(title, year)
                    if libraryPoster:
                        poster = libraryPoster
                        self.log("Using library poster for " + title)
                    else:
                        # Fallback to Radarr remote URLs
                        if 'images' in item:
                            for image in item['images']:
                                if image.get('coverType') == 'poster':
                                    poster = image.get('remoteUrl', '')
                                    self.log("Using Radarr poster URL: " + poster)
                                    break

                    if not poster:
                        self.log("WARNING: No poster found for " + title)

                    # Create movie object
                    movie = {
                        'type': 'movie',
                        'title': title,
                        'year': year,
                        'releaseDate': releaseDate,
                        'isToday': isToday,
                        'daysUntil': daysUntil,
                        'dayStr': dayStr,
                        'status': status,
                        'hasFile': hasFile,
                        'poster': poster
                    }
                    
                    movies.append(movie)
                    self.log("Added movie: %s (%s)" % (title, year))
                    
                except Exception as e:
                    self.log("Error parsing Radarr movie: " + str(e), xbmc.LOGERROR)
                    import traceback
                    self.log("Traceback: " + traceback.format_exc(), xbmc.LOGERROR)
                    continue
            
            self.log("fetchRadarrCalendar - Returning %d movies" % len(movies))
            return movies
            
        except Exception as e:
            self.log("Error in fetchRadarrCalendar: " + str(e), xbmc.LOGERROR)
            import traceback
            self.log("Traceback: " + traceback.format_exc(), xbmc.LOGERROR)
            return []

    def getLibraryPosterForShow(self, showTitle):
        """Get poster from Kodi library for a show"""
        self.log("getLibraryPosterForShow: Looking for " + showTitle)
        
        try:
            # Search Kodi library for this show
            json_query = {
                "jsonrpc": "2.0",
                "method": "VideoLibrary.GetTVShows",
                "params": {
                    "filter": {
                        "field": "title",
                        "operator": "is",
                        "value": showTitle
                    },
                    "properties": ["art", "title"]
                },
                "id": 1
            }
            
            result = xbmc.executeJSONRPC(json.dumps(json_query))
            result = json.loads(result)
            
            if "result" in result and "tvshows" in result["result"] and result["result"]["tvshows"]:
                show = result["result"]["tvshows"][0]
                self.log("Found show in library: " + show.get('title', ''))
                
                if "art" in show:
                    art = show["art"]
                    
                    # Priority order: poster > fanart > landscape > banner
                    if "poster" in art and art["poster"]:
                        self.log("Using library poster")
                        return art["poster"]
                    elif "fanart" in art and art["fanart"]:
                        self.log("Using library fanart")
                        return art["fanart"]
                    elif "landscape" in art and art["landscape"]:
                        self.log("Using library landscape")
                        return art["landscape"]
                    elif "banner" in art and art["banner"]:
                        self.log("Using library banner")
                        return art["banner"]
            
            self.log("Show not found in library")
            return ""
            
        except Exception as e:
            self.log("Error getting library poster: " + str(e))
            return ""

    def getLibraryPosterForMovie(self, movieTitle, movieYear):
        """Get poster from Kodi library for a movie"""
        self.log("getLibraryPosterForMovie: Looking for " + movieTitle + " (" + str(movieYear) + ")")
        
        try:
            # Search Kodi library for this movie
            json_query = {
                "jsonrpc": "2.0",
                "method": "VideoLibrary.GetMovies",
                "params": {
                    "filter": {
                        "and": [
                            {
                                "field": "title",
                                "operator": "is",
                                "value": movieTitle
                            },
                            {
                                "field": "year",
                                "operator": "is",
                                "value": str(movieYear)
                            }
                        ]
                    },
                    "properties": ["art", "title", "year"]
                },
                "id": 1
            }
            
            result = xbmc.executeJSONRPC(json.dumps(json_query))
            result = json.loads(result)
            
            if "result" in result and "movies" in result["result"] and result["result"]["movies"]:
                movie = result["result"]["movies"][0]
                self.log("Found movie in library: " + movie.get('title', ''))
                
                if "art" in movie:
                    art = movie["art"]
                    
                    # Priority order: poster > fanart > landscape
                    if "poster" in art and art["poster"]:
                        self.log("Using library poster")
                        return art["poster"]
                    elif "fanart" in art and art["fanart"]:
                        self.log("Using library fanart")
                        return art["fanart"]
                    elif "landscape" in art and art["landscape"]:
                        self.log("Using library landscape")
                        return art["landscape"]
            
            self.log("Movie not found in library")
            return ""
            
        except Exception as e:
            self.log("Error getting library poster: " + str(e))
            return ""

    def updateCalendarData(self):
        """Update calendar data from Sonarr and Radarr"""
        self.log("updateCalendarData - STARTING")
        
        try:
            # Fetch from both APIs
            self.log("updateCalendarData - Fetching Sonarr...")
            sonarrData = self.fetchSonarrCalendar()
            self.sonarrCalendar = sonarrData if sonarrData else []
            self.log("updateCalendarData - Sonarr returned %d items" % len(self.sonarrCalendar))
            
            self.log("updateCalendarData - Fetching Radarr...")
            radarrData = self.fetchRadarrCalendar()
            self.radarrCalendar = radarrData if radarrData else []
            self.log("updateCalendarData - Radarr returned %d items" % len(self.radarrCalendar))
            
            # Combine and sort by date
            allItems = self.sonarrCalendar + self.radarrCalendar
            self.log("updateCalendarData - Total items: %d" % len(allItems))
            
            if not allItems:
                self.log("updateCalendarData - No items found from either service")
                # Set empty state
                self.setProperty("PTV.Calendar.Today.Title", "No new releases today")
                self.setProperty("PTV.Calendar.Today.Episode", "Check back tomorrow!")
                self.setProperty("PTV.Calendar.Today.Status", "")
                self.setProperty("PTV.Calendar.Today.Poster", "")
                return
            
            allItems.sort(key=lambda x: x.get('airDate') if x['type'] == 'tv' else x.get('releaseDate'))
            
            # Separate today's items from this week's items
            todayItems = [item for item in allItems if item.get('isToday', False)]
            weekItems = [item for item in allItems if not item.get('isToday', False) and item.get('daysUntil', 999) <= 7]
            
            self.log("updateCalendarData - Today items: %d, Week items: %d" % (len(todayItems), len(weekItems)))
            
            # Update today's display
            if todayItems:
                self.log("updateCalendarData - Calling updateTodayDisplay")
                self.updateTodayDisplay(todayItems[0])
                self.sonarrTodayIndex = 0
            else:
                self.log("updateCalendarData - No today items")
                self.setProperty("PTV.Calendar.Today.Title", "No new releases today")
                self.setProperty("PTV.Calendar.Today.Episode", "Check back tomorrow!")
                self.setProperty("PTV.Calendar.Today.Status", "")
                self.setProperty("PTV.Calendar.Today.Poster", "")
            
            # Update this week's list
            for i in range(10):
                if i < len(weekItems):
                    item = weekItems[i]
                    if item['type'] == 'tv':
                        label = "%s S%02dE%02d - %s" % (
                            item.get('seriesTitle', 'Unknown'),
                            item.get('season', 0),
                            item.get('episode', 0),
                            item.get('dayStr', '')
                        )
                        # Check if show is in library
                        inLibrary = self.getLibraryPosterForShow(item.get('seriesTitle', '')) != ""
                    else:
                        label = "%s (%s) - %s" % (
                            item.get('title', 'Unknown'),
                            item.get('year', ''),
                            item.get('dayStr', '')
                        )
                        # Check if movie is in library
                        inLibrary = self.getLibraryPosterForMovie(item.get('title', ''), item.get('year', '')) != ""
                    
                    self.setProperty("PTV.Calendar.Week.%d" % (i + 1), label)
                    self.setProperty("PTV.Calendar.Week.%d.InLibrary" % (i + 1), "true" if inLibrary else "false")
                else:
                    self.setProperty("PTV.Calendar.Week.%d" % (i + 1), "")
                    self.setProperty("PTV.Calendar.Week.%d.InLibrary" % (i + 1), "false")
            
        except Exception as e:
            self.log("updateCalendarData - ERROR: " + str(e), xbmc.LOGERROR)
            import traceback
            self.log("updateCalendarData - Traceback: " + traceback.format_exc(), xbmc.LOGERROR)
            # Set error state in UI
            self.setProperty("PTV.Calendar.Today.Title", "Error loading calendar")
            self.setProperty("PTV.Calendar.Today.Episode", "Check logs for details")
            self.setProperty("PTV.Calendar.Today.Status", "")
            self.setProperty("PTV.Calendar.Today.Poster", "")
            
    def updateTodayDisplay(self, item):
        """Update the display for today's featured item"""
        self.log("updateTodayDisplay - CALLED")
        
        if not item:
            self.log("updateTodayDisplay - Item is None!")
            return
        
        # Log the entire item to see what we have
        self.log("updateTodayDisplay - Item type: " + str(item.get('type', 'unknown')))
        self.log("updateTodayDisplay - Item keys: " + str(item.keys()))
        
        if item['type'] == 'tv':
            # TV Episode
            title = item.get('seriesTitle', 'NO TITLE FOUND')
            
            self.log("updateTodayDisplay - Extracted title: '" + str(title) + "'")
            
            # FORMAT AS: "Episode Title (S##E##)" - matching Spotlight
            episodeTitle = item['title']
            episodeInfo = "S%02dE%02d" % (item['season'], item['episode'])
            episode = "%s (%s)" % (episodeTitle, episodeInfo)
            
            self.log("updateTodayDisplay - Setting PTV.Calendar.Today.Title to: " + title)
            self.setProperty("PTV.Calendar.Today.Title", title)
            
            self.log("updateTodayDisplay - Setting PTV.Calendar.Today.Episode to: " + episode)
            self.setProperty("PTV.Calendar.Today.Episode", episode)
        else:
            # Movie
            self.log("updateTodayDisplay - Movie detected")
            self.setProperty("PTV.Calendar.Today.Title", item['title'])
            self.setProperty("PTV.Calendar.Today.Episode", "(%s)" % item['year'])
        
        self.log("updateTodayDisplay - Setting status: " + item['status'])
        self.setProperty("PTV.Calendar.Today.Status", item['status'])
        
        self.log("updateTodayDisplay - Setting poster: " + item['poster'])
        self.setProperty("PTV.Calendar.Today.Poster", item['poster'])
        
        self.log("updateTodayDisplay - COMPLETE")

    def rotateTodayItem(self):
        """Rotate to next item airing/releasing today"""
        if not self.showingCalendar:
            return
        
        # Get today's items
        allItems = self.sonarrCalendar + self.radarrCalendar
        todayItems = [item for item in allItems if item['isToday']]
        
        if not todayItems:
            # No items today, just reschedule
            self.calendarRotationTimer = threading.Timer(5.0, self.rotateTodayItem)
            if not self.isExiting:
                self.calendarRotationTimer.start()
            return
        
        # Move to next item
        self.sonarrTodayIndex = (self.sonarrTodayIndex + 1) % len(todayItems)
        
        # Update display
        self.updateTodayDisplay(todayItems[self.sonarrTodayIndex])
        
        # Schedule next rotation
        self.calendarRotationTimer = threading.Timer(5.0, self.rotateTodayItem)
        if not self.isExiting:
            self.calendarRotationTimer.start()

    def calendarRefreshAction(self):
        """Periodically refresh calendar data"""
        if not self.showingCalendar:
            return
        
        self.log("calendarRefreshAction - refreshing data")
        self.updateCalendarData()
        
        # Schedule next refresh
        self.calendarRefreshTimer = threading.Timer(
            self.calendarRefreshInterval, 
            self.calendarRefreshAction
        )
        if not self.isExiting:
            self.calendarRefreshTimer.start()

    def showCalendarOverlay(self, persistent=False):
        """Show the calendar overlay (with weather in lower third)"""
        self.log("showCalendarOverlay - STARTED")
        
        # Check if either Sonarr or Radarr is configured
        sonarrEnabled = ADDON.getSetting("SonarrEnabled") == "true"
        radarrEnabled = ADDON.getSetting("RadarrEnabled") == "true"
        
        if not sonarrEnabled and not radarrEnabled:
            self.log("showCalendarOverlay - Neither service enabled")
            xbmc.executebuiltin(
                "Notification(%s, Sonarr/Radarr not configured, 3000, %s)"
                % (ADDON_NAME, ICON)
            )
            return
        
        # Log settings for debugging
        if sonarrEnabled:
            sonarrUrl = ADDON.getSetting("SonarrURL")
            sonarrKey = ADDON.getSetting("SonarrAPIKey")
            self.log("Sonarr - URL: '%s', Has Key: %s" % (sonarrUrl, "Yes" if sonarrKey else "No"))
        
        if radarrEnabled:
            radarrUrl = ADDON.getSetting("RadarrURL")
            radarrKey = ADDON.getSetting("RadarrAPIKey")
            self.log("Radarr - URL: '%s', Has Key: %s" % (radarrUrl, "Yes" if radarrKey else "No"))
        
        # Show calendar overlay
        self.showingCalendar = True
        self.setProperty("PTV.Calendar", "true")
        
        # Also show weather in lower third
        self.showingWeather = True
        self.setProperty("PTV.Weather", "true")
        
        # Update weather info
        self.log("showCalendarOverlay - Updating weather")
        self.updateWeatherInfo()
        
        # Fetch initial calendar data
        self.log("showCalendarOverlay - About to call updateCalendarData")
        try:
            self.updateCalendarData()
            self.log("showCalendarOverlay - updateCalendarData completed")
        except Exception as e:
            self.log("showCalendarOverlay - updateCalendarData failed: " + str(e), xbmc.LOGERROR)
            import traceback
            self.log("showCalendarOverlay - Traceback: " + traceback.format_exc(), xbmc.LOGERROR)
        
        # Start rotation timer for today's items (10 second intervals)
        if self.calendarRotationTimer and self.calendarRotationTimer.isAlive():
            self.calendarRotationTimer.cancel()
        
        self.calendarRotationTimer = threading.Timer(10.0, self.rotateTodayItem)
        self.calendarRotationTimer.start()
        
        # Start refresh timer (5 minutes)
        if self.calendarRefreshTimer and self.calendarRefreshTimer.isAlive():
            self.calendarRefreshTimer.cancel()
        
        self.calendarRefreshTimer = threading.Timer(
            self.calendarRefreshInterval,
            self.calendarRefreshAction
        )
        self.calendarRefreshTimer.start()
        
        self.log("showCalendarOverlay - COMPLETED")

    def hideCalendarOverlay(self):
        """Hide the calendar overlay"""
        self.log("hideCalendarOverlay")
        self.showingCalendar = False
        self.setProperty("PTV.Calendar", "false")
        
        # Also hide weather
        self.showingWeather = False
        self.setProperty("PTV.Weather", "false")
        
        # Cancel timers
        if self.calendarRotationTimer is not None and self.calendarRotationTimer.isAlive():
            self.calendarRotationTimer.cancel()
        
        if self.calendarRefreshTimer is not None and self.calendarRefreshTimer.isAlive():
            self.calendarRefreshTimer.cancel()
        
        if self.weatherTimer is not None and self.weatherTimer.isAlive():
            self.weatherTimer.cancel()
        
        self.log("hideCalendarOverlay return")

    def fetchRecentlyAdded(self):
        """Fetch the 10 most recently added videos from Kodi library"""
        self.log("fetchRecentlyAdded - STARTED")
        recent_items = []
        
        try:
            # Fetch recent movies
            movies_query = {
                "jsonrpc": "2.0",
                "method": "VideoLibrary.GetRecentlyAddedMovies",
                "params": {
                    "properties": ["title", "art", "year", "dateadded", "file", "playcount", "plot"],  # ADDED "plot"
                    "limits": {"end": 10}
                },
                "id": "recentMovies"
            }
            
            movies_response = xbmc.executeJSONRPC(json.dumps(movies_query))
            movies_data = json.loads(movies_response)
            
            if "result" in movies_data and "movies" in movies_data["result"]:
                for movie in movies_data["result"]["movies"]:
                    recent_items.append({
                        "type": "movie",
                        "title": movie.get("title", "Unknown Movie"),
                        "poster": movie.get("art", {}).get("poster", ""),
                        "year": movie.get("year", ""),
                        "dateadded": movie.get("dateadded", ""),
                        "file": movie.get("file", ""),
                        "playcount": movie.get("playcount", 0),
                        "plot": movie.get("plot", ""),  # ADDED THIS LINE
                        "movieid": movie.get("movieid")
                    })
                    self.log("Added movie: %s (%s)" % (movie.get("title"), movie.get("year")))
            
            # Fetch recent episodes
            episodes_query = {
                "jsonrpc": "2.0",
                "method": "VideoLibrary.GetRecentlyAddedEpisodes",
                "params": {
                    "properties": ["showtitle", "season", "episode", "title", "art", "dateadded", "file", "playcount", "tvshowid", "plot"],  # ADDED "plot"
                    "limits": {"end": 10}
                },
                "id": "recentEpisodes"
            }
            
            episodes_response = xbmc.executeJSONRPC(json.dumps(episodes_query))
            episodes_data = json.loads(episodes_response)
            
            if "result" in episodes_data and "episodes" in episodes_data["result"]:
                for episode in episodes_data["result"]["episodes"]:
                    # Get the TV show poster
                    show_query = {
                        "jsonrpc": "2.0",
                        "method": "VideoLibrary.GetTVShowDetails",
                        "params": {
                            "tvshowid": episode.get("tvshowid"),
                            "properties": ["art"]
                        },
                        "id": "showArt"
                    }
                    show_response = xbmc.executeJSONRPC(json.dumps(show_query))
                    show_data = json.loads(show_response)
                    
                    poster = ""
                    if "result" in show_data and "tvshowdetails" in show_data["result"]:
                        poster = show_data["result"]["tvshowdetails"].get("art", {}).get("poster", "")
                    
                    episode_info = "S%02dE%02d" % (
                        episode.get("season", 0),
                        episode.get("episode", 0)
                    )
                    
                    recent_items.append({
                        "type": "episode",
                        "title": episode.get("showtitle", "Unknown Show"),
                        "episode_title": episode.get("title", ""),
                        "episode_info": episode_info,
                        "poster": poster,
                        "dateadded": episode.get("dateadded", ""),
                        "file": episode.get("file", ""),
                        "playcount": episode.get("playcount", 0),
                        "plot": episode.get("plot", ""),  # ADDED THIS LINE
                        "episodeid": episode.get("episodeid")
                    })
                    self.log("Added episode: %s %s" % (episode.get("showtitle"), episode_info))
            
            # Sort all items by date added (most recent first)
            recent_items.sort(key=lambda x: x.get("dateadded", ""), reverse=True)
            
            # Return only the 10 most recent
            result = recent_items[:10]
            self.log("fetchRecentlyAdded - Returning %d items" % len(result))
            return result
            
        except Exception as e:
            self.log("Error in fetchRecentlyAdded: " + str(e), xbmc.LOGERROR)
            import traceback
            self.log("Traceback: " + traceback.format_exc(), xbmc.LOGERROR)
            return []
    
    def updateRecentlyAddedData(self):
        """Update window properties with recently added data"""
        self.log("updateRecentlyAddedData - STARTING")
        
        recent_items = self.fetchRecentlyAdded()
        
        if not recent_items:
            self.log("No recently added items found")
            self.setProperty("PTV.Recent.Featured.Title", "No Recent Additions")
            self.setProperty("PTV.Recent.Featured.Subtitle", "")
            return
        
        # Store all items
        self.recentlyAddedItems = recent_items
        
        # Split into featured (first 5) and list (last 5)
        featured_items = recent_items[:5]
        list_items = recent_items[5:10]
        
        # Set the first featured item
        if featured_items:
            self.updateRecentlyAddedFeaturedItem(0)
        
        # Set list items (items 6-10)
        for i, item in enumerate(list_items, start=1):
            if item["type"] == "movie":
                label = "%s (%s)" % (item["title"], item.get("year", ""))
            else:
                label = "%s - %s" % (item["title"], item["episode_info"])
            
            self.setProperty("PTV.Recent.List.%d" % i, label)
            
            # Mark if watched
            watched = item.get("playcount", 0) > 0
            self.setProperty("PTV.Recent.List.%d.Watched" % i, str(watched))
        
        # Clear any unused list slots
        for i in range(len(list_items) + 1, 6):
            self.setProperty("PTV.Recent.List.%d" % i, "")
        
        self.log("updateRecentlyAddedData - COMPLETED")
    
    def updateRecentlyAddedFeaturedItem(self, index):
        """Update the featured item display"""
        self.log("updateRecentlyAddedFeaturedItem - index %d" % index)
        
        if not self.recentlyAddedItems or index >= len(self.recentlyAddedItems):
            return
        
        # Only cycle through first 5 items
        if index >= 5:
            index = 0
        
        item = self.recentlyAddedItems[index]
        self.recentlyAddedFeaturedIndex = index
        
        # Set featured properties
        self.setProperty("PTV.Recent.Featured.Poster", item.get("poster", ""))
        self.setProperty("PTV.Recent.Featured.Title", item.get("title", ""))
        
        if item["type"] == "movie":
            self.setProperty("PTV.Recent.Featured.Subtitle", str(item.get("year", "")))
            self.setProperty("PTV.Recent.Featured.EpisodeTitle", "")
            self.setProperty("PTV.Recent.Featured.Type", "Movie")
        else:
            # FORMAT AS: "Episode Title (S##E##)" - matching Spotlight
            episode_title = item.get("episode_title", "")
            episode_info = item.get("episode_info", "")
            
            if episode_title and episode_info:
                combined_title = "%s (%s)" % (episode_title, episode_info)
            elif episode_title:
                combined_title = episode_title
            elif episode_info:
                combined_title = episode_info
            else:
                combined_title = ""
            
            self.setProperty("PTV.Recent.Featured.Subtitle", "")
            self.setProperty("PTV.Recent.Featured.EpisodeTitle", combined_title)
            self.setProperty("PTV.Recent.Featured.Type", "TV Show")
        
        # Get plot summary instead of date
        plot = item.get('plot', '')
        self.log("DEBUG PLOT for %s: '%s'" % (item.get('title', 'Unknown'), plot[:100] if plot else "NO PLOT FOUND"))
        if plot:
            # Limit to ~300 characters for display (adjust as needed)
            if len(plot) > 300:
                plot = plot[:297] + '...'
            self.setProperty("PTV.Recent.Featured.Plot", plot)
        else:
            self.setProperty("PTV.Recent.Featured.Plot", "")
        
        # Mark if watched
        watched = item.get("playcount", 0) > 0
        self.setProperty("PTV.Recent.Featured.Watched", str(watched))
        
        self.log("updateRecentlyAddedFeaturedItem - Set to: %s" % item.get("title"))
    
    def rotateRecentlyAddedFeaturedItem(self):
        """Rotate to next featured item"""
        if not self.showingRecentlyAdded:
            return
        
        if not self.recentlyAddedItems or len(self.recentlyAddedItems) == 0:
            # Reschedule and return
            self.recentlyAddedRotationTimer = threading.Timer(5.0, self.rotateRecentlyAddedFeaturedItem)  # CHANGED
            if not self.isExiting:
                self.recentlyAddedRotationTimer.start()
            return
        
        # Move to next item (cycle through first 5 only)
        next_index = (self.recentlyAddedFeaturedIndex + 1) % min(5, len(self.recentlyAddedItems))
        
        # Update display
        self.updateRecentlyAddedFeaturedItem(next_index)
        
        # Schedule next rotation
        self.recentlyAddedRotationTimer = threading.Timer(5.0, self.rotateRecentlyAddedFeaturedItem)  # CHANGED
        if not self.isExiting:
            self.recentlyAddedRotationTimer.start()
    
    def recentlyAddedRefreshAction(self):
        """Periodically refresh recently added data"""
        if not self.showingRecentlyAdded:
            return
        
        self.log("recentlyAddedRefreshAction - refreshing data")
        self.updateRecentlyAddedData()
        
        # Schedule next refresh
        self.recentlyAddedRefreshTimer = threading.Timer(
            self.recentlyAddedRefreshInterval,
            self.recentlyAddedRefreshAction
        )
        if not self.isExiting:
            self.recentlyAddedRefreshTimer.start()
    
    def showRecentlyAddedOverlay(self, persistent=False):
        """Show the recently added overlay"""
        self.log("showRecentlyAddedOverlay - STARTED")
        
        # Show recently added overlay
        self.showingRecentlyAdded = True
        self.setProperty("PTV.RecentlyAdded", "true")
        
        # Also show weather in lower third
        self.showingWeather = True
        self.setProperty("PTV.Weather", "true")
        
        # Update weather info
        self.log("showRecentlyAddedOverlay - Updating weather")
        self.updateWeatherInfo()
        
        # Fetch initial recently added data
        self.log("showRecentlyAddedOverlay - About to call updateRecentlyAddedData")
        try:
            self.updateRecentlyAddedData()
            self.log("showRecentlyAddedOverlay - updateRecentlyAddedData completed")
        except Exception as e:
            self.log("showRecentlyAddedOverlay - updateRecentlyAddedData failed: " + str(e), xbmc.LOGERROR)
            import traceback
            self.log("showRecentlyAddedOverlay - Traceback: " + traceback.format_exc(), xbmc.LOGERROR)
        
        # Start rotation timer for featured items (10 second intervals)
        if self.recentlyAddedRotationTimer and self.recentlyAddedRotationTimer.isAlive():
            self.recentlyAddedRotationTimer.cancel()
        
        self.recentlyAddedRotationTimer = threading.Timer(10.0, self.rotateRecentlyAddedFeaturedItem)
        self.recentlyAddedRotationTimer.start()
        
        # Start refresh timer (5 minutes)
        if self.recentlyAddedRefreshTimer and self.recentlyAddedRefreshTimer.isAlive():
            self.recentlyAddedRefreshTimer.cancel()
        
        self.recentlyAddedRefreshTimer = threading.Timer(
            self.recentlyAddedRefreshInterval,
            self.recentlyAddedRefreshAction
        )
        self.recentlyAddedRefreshTimer.start()
        
        # NEW: Only set auto-hide timer if NOT persistent
        if not persistent:
            # Auto-hide after 100 seconds (for manual button press)
            if (
                hasattr(self, "recentlyAddedTimer")
                and self.recentlyAddedTimer is not None
                and self.recentlyAddedTimer.isAlive()
            ):
                self.recentlyAddedTimer.cancel()
            
            self.recentlyAddedTimer = threading.Timer(100.0, self.hideRecentlyAddedOverlay)
            self.recentlyAddedTimer.start()
        else:
            # Cancel any existing timer for persistent mode
            if (
                hasattr(self, "recentlyAddedTimer")
                and self.recentlyAddedTimer is not None
                and self.recentlyAddedTimer.isAlive()
            ):
                self.recentlyAddedTimer.cancel()
            self.log("Recently Added overlay in persistent mode (no auto-hide)")
        
        self.log("showRecentlyAddedOverlay - COMPLETED")
    
    def hideRecentlyAddedOverlay(self):
        """Hide the recently added overlay"""
        self.log("hideRecentlyAddedOverlay")
        self.showingRecentlyAdded = False
        self.setProperty("PTV.RecentlyAdded", "false")
        
        # Also hide weather
        self.showingWeather = False
        self.setProperty("PTV.Weather", "false")
        
        # Cancel timers
        if self.recentlyAddedRotationTimer is not None and self.recentlyAddedRotationTimer.isAlive():
            self.recentlyAddedRotationTimer.cancel()
        
        if self.recentlyAddedRefreshTimer is not None and self.recentlyAddedRefreshTimer.isAlive():
            self.recentlyAddedRefreshTimer.cancel()
        
        if hasattr(self, "recentlyAddedTimer") and self.recentlyAddedTimer is not None and self.recentlyAddedTimer.isAlive():
            self.recentlyAddedTimer.cancel()
        
        self.log("hideRecentlyAddedOverlay return")

    def fetchRandomRecommendations(self):
        """Fetch random items from channel playlists that will play before next 5 AM reset"""
        self.log("fetchRandomRecommendations - STARTED")
        recommendations = []
        
        try:
            import random
            import re  # ADD THIS LINE
            from datetime import datetime, timedelta
            
            # Get all valid channels (exclude Bumpers TV)
            validChannels = []
            for i, channel in enumerate(self.channels):
                if channel and channel.isValid:
                    channelName = channel.name.lower()
                    # Skip Bumpers TV channel
                    if "bumper" not in channelName:
                        validChannels.append((i, channel))
            
            if not validChannels:
                self.log("No valid channels found")
                return []
            
            self.log("Found %d valid channels" % len(validChannels))
            
            # Calculate viewing window: 9 AM - 11:59 PM
            currentTime = time.time()
            now = datetime.fromtimestamp(currentTime)
            
            # Determine viewing window based on current time
            if now.hour < 9:
                # Before 9 AM - show content from 9 AM today to 11:59 PM today
                viewingStart = now.replace(hour=9, minute=0, second=0, microsecond=0)
                viewingEnd = now.replace(hour=23, minute=59, second=59, microsecond=0)
            else:
                # After 9 AM - show content from NOW to 11:59 PM today
                viewingStart = now.replace(hour=now.hour, minute=now.minute, second=now.second, microsecond=0)
                viewingEnd = now.replace(hour=23, minute=59, second=59, microsecond=0)
            
            viewingStartTimestamp = time.mktime(viewingStart.timetuple())
            viewingEndTimestamp = time.mktime(viewingEnd.timetuple())
            
            # Calculate viewing window duration
            viewingWindowHours = (viewingEndTimestamp - viewingStartTimestamp) / 3600.0
            
            self.log("Current time: %s" % now.strftime("%Y-%m-%d %I:%M:%S %p"))
            self.log("Viewing window start: %s" % viewingStart.strftime("%Y-%m-%d %I:%M:%S %p"))
            self.log("Viewing window end (11:59 PM): %s" % viewingEnd.strftime("%Y-%m-%d %I:%M:%S %p"))
            self.log("Viewing window duration: %.2f hours" % viewingWindowHours)
            
            # Build pool of valid items during viewing hours
            validItems = []
            
            for channelIndex, channel in validChannels:
                channelNumber = channelIndex + 1
                playlistLength = channel.Playlist.size()
                
                if playlistLength == 0:
                    continue
                
                # Get channel's current state
                currentPos = channel.playlistPosition
                currentOffset = channel.showTimeOffset
                channelCurrentTime = channel.lastAccessTime
                
                # Calculate time position for each item in playlist
                timePosition = channelCurrentTime - currentOffset  # Start of current item
                
                for pos in range(playlistLength):
                    # Calculate when this position will air
                    if pos < currentPos:
                        # Item is behind current position - will play after loop
                        # Add time from current to end of playlist
                        tempTime = channelCurrentTime + (channel.getItemDuration(currentPos) - currentOffset)
                        for p in range(currentPos + 1, playlistLength):
                            tempTime += channel.getItemDuration(p)
                        # Add time from start to this position
                        for p in range(0, pos):
                            tempTime += channel.getItemDuration(p)
                        itemAirtime = tempTime
                    elif pos == currentPos:
                        # Currently playing item
                        itemAirtime = channelCurrentTime - currentOffset
                    else:
                        # Item is ahead - sum durations
                        tempTime = channelCurrentTime + (channel.getItemDuration(currentPos) - currentOffset)
                        for p in range(currentPos + 1, pos):
                            tempTime += channel.getItemDuration(p)
                        itemAirtime = tempTime
                    
                    # Check if item will play DURING viewing hours (9 AM - 11:59 PM)
                    if itemAirtime >= viewingStartTimestamp and itemAirtime <= viewingEndTimestamp:
                        validItems.append({
                            'channelIndex': channelIndex,
                            'channel': channel,
                            'channelNumber': channelNumber,
                            'position': pos,
                            'airtime': itemAirtime
                        })
            
            self.log("Found %d items playing during viewing hours (9 AM - 11:59 PM)" % len(validItems))
            
            if len(validItems) == 0:
                self.log("No items found during viewing hours (9 AM - 11:59 PM)")
                return []
            
           # Separate items by type for weighted selection
            movieItems = []
            audioItems = []
            tvItems = []
            
            # We need to build the recommendations first to determine type
            # So we'll do this in two passes
            self.log("Categorizing items by type for weighted selection...")
            
            tempRecommendations = []
            for item in validItems:
                try:
                    channel = item['channel']
                    randomPos = item['position']
                    channelNumber = item['channelNumber']
                    
                    # Get basic item info to determine type
                    episodeTitle = channel.getItemEpisodeTitle(randomPos)
                    itemPath = channel.getItemFilename(randomPos)
                    
                    # Determine type quickly
                    itemType = "movie"  # default
                    if itemPath:
                        itemPathLower = itemPath.lower()
                        if "/audio/" in itemPathLower or "\\audio\\" in itemPathLower:
                            itemType = "audio"
                        elif episodeTitle and episodeTitle.strip() != "":
                            itemType = "tv"
                    
                    # Add to appropriate category
                    itemData = {
                        'item': item,
                        'type': itemType
                    }
                    
                    if itemType == "audio":
                        audioItems.append(itemData)
                    elif itemType == "tv":
                        tvItems.append(itemData)
                    else:
                        movieItems.append(itemData)
                        
                except Exception as e:
                    self.log("Error categorizing item: %s" % str(e))
                    continue
            
            self.log("Found: %d movies, %d audio, %d TV shows" % (len(movieItems), len(audioItems), len(tvItems)))
            
            # Build weighted selection: 2 movies, 3 audio, 15 TV
            selectedItems = []
            
            # Select 2 movies
            if len(movieItems) >= 2:
                selectedMovies = random.sample(movieItems, 2)
            elif len(movieItems) > 0:
                selectedMovies = random.sample(movieItems, len(movieItems))
            else:
                selectedMovies = []
            selectedItems.extend([item['item'] for item in selectedMovies])
            
            # Select 3 audio
            if len(audioItems) >= 3:
                selectedAudio = random.sample(audioItems, 3)
            elif len(audioItems) > 0:
                selectedAudio = random.sample(audioItems, len(audioItems))
            else:
                selectedAudio = []
            selectedItems.extend([item['item'] for item in selectedAudio])
            
            # Select 15 TV shows (or fill remaining slots)
            remainingSlots = 20 - len(selectedItems)
            if len(tvItems) >= remainingSlots:
                selectedTV = random.sample(tvItems, remainingSlots)
            elif len(tvItems) > 0:
                selectedTV = random.sample(tvItems, len(tvItems))
            else:
                selectedTV = []
            selectedItems.extend([item['item'] for item in selectedTV])
            
            # If we still don't have 20, fill with any remaining items
            if len(selectedItems) < 20:
                self.log("Not enough items for ideal mix, filling with available content...")
                allRemaining = []
                # Add unused movies
                usedMovieItems = [item['item'] for item in selectedMovies] if selectedMovies else []
                allRemaining.extend([item['item'] for item in movieItems if item['item'] not in usedMovieItems])
                # Add unused audio
                usedAudioItems = [item['item'] for item in selectedAudio] if selectedAudio else []
                allRemaining.extend([item['item'] for item in audioItems if item['item'] not in usedAudioItems])
                # Add unused TV
                usedTVItems = [item['item'] for item in selectedTV] if selectedTV else []
                allRemaining.extend([item['item'] for item in tvItems if item['item'] not in usedTVItems])
                
                # Fill remaining slots
                slotsToFill = min(20 - len(selectedItems), len(allRemaining))
                if slotsToFill > 0:
                    fillItems = random.sample(allRemaining, slotsToFill)
                    selectedItems.extend(fillItems)
            
            # Shuffle the selected items so they're not grouped by type
            random.shuffle(selectedItems)
            
            self.log("Selected mix: %d total items for recommendations" % len(selectedItems))
            
            # Build recommendations from selected items
            for item in selectedItems:
                try:
                    channel = item['channel']
                    randomPos = item['position']
                    channelNumber = item['channelNumber']
                    airtime = item['airtime']
                    
                    # Get item info from playlist
                    title = channel.getItemTitle(randomPos)
                    episodeTitle = channel.getItemEpisodeTitle(randomPos)
                    description = channel.getItemDescription(randomPos)
                    
                    # Derive genre from channel name
                    genre = "General"
                    channelName = channel.name

                    # NEW: For audio channels (Music Genre - *), use the full channel name
                    if channelName and channelName.startswith("Music Genre - "):
                        genre = channelName  # Use full name: "Music Genre - Cinematic"
                        self.log("Audio channel detected, using full name as genre: %s" % genre)
                    # Try to extract genre from channel name patterns like "Action Movies" or "Comedy TV"
                    elif channelName:
                        # Common patterns: "Genre Movies", "Genre TV", "Genre - Something"
                        for genreType in [" Movies", " TV", " - "]:
                            if genreType in channelName:
                                genre = channelName.split(genreType)[0].strip()
                                break
                    
                    # Get poster/artwork - try multiple methods
                    poster = ""
                    itemPath = channel.getItemFilename(randomPos)
                    
                    # NEW: Detect if this is audio content and extract artist/album
                    isAudio = False
                    artist = ""
                    album = ""
                    if itemPath:
                        # Check if path contains /AUDIO/ folder
                        itemPathLower = itemPath.lower()
                        if "/audio/" in itemPathLower or "\\audio\\" in itemPathLower:
                            isAudio = True
                            self.log("Detected AUDIO content: %s" % itemPath)
                            
                            # Extract artist and album from path
                            # Example: /mnt/user/AUDIO/Dreamstate Logic/Era Three/01 - Track.mp3
                            # Artist: Dreamstate Logic, Album: Era Three
                            try:
                                import os
                                # Get the directory containing the file
                                itemDir = os.path.dirname(itemPath)
                                # Album is the immediate parent folder
                                album = os.path.basename(itemDir)
                                # Artist is the grandparent folder
                                parentDir = os.path.dirname(itemDir)
                                artist = os.path.basename(parentDir)
                                
                                # Clean up "AUDIO" if it appears in artist name
                                if artist.upper() == "AUDIO":
                                    artist = "Unknown Artist"
                                
                                self.log("Extracted - Artist: %s, Album: %s" % (artist, album))
                            except Exception as e:
                                self.log("Error extracting artist/album: %s" % str(e))
                                artist = "Unknown Artist"
                                album = "Unknown Album"
                    
                    # Only get poster for non-audio content
                    if not isAudio and itemPath and FileAccess.exists(itemPath):
                        itemDir = os.path.dirname(itemPath)
                        
                        # Check if we're in a Season folder - if so, go up to the show folder first
                        dirName = os.path.basename(itemDir).lower()
                        if "season" in dirName or dirName.startswith("s0") or dirName.startswith("s1"):
                            # We're in a season folder, use the parent (show) folder instead
                            itemDir = os.path.dirname(itemDir)
                            self.log("In season folder, checking show directory: %s" % itemDir)
                        
                        # Now check for poster/folder art (including files without extensions)
                        posterFiles = ["folder.jpg", "folder.png", "folder", "poster.jpg", "poster.png", "poster", "cover.jpg", "cover.png", "cover"]
                        for posterFile in posterFiles:
                            posterPath = os.path.join(itemDir, posterFile)
                            if FileAccess.exists(posterPath):
                                poster = posterPath
                                self.log("Found poster: %s" % posterPath)
                                break

                    # If still no poster, use channel logo as fallback
                    if not poster:
                        if isAudio:
                            self.log("Audio content - not using folder poster")
                        else:
                            self.log("No poster found for item, will use fallback")
                        poster = ""  # Let the XML fallback to Bumpers.jpg
                    
                    # Determine content type
                    if isAudio:
                        isTV = False  # Audio is neither TV nor Movie
                    else:
                        # Determine if TV or Movie based on episode title
                        isTV = episodeTitle and episodeTitle.strip() != ""

                    # Extract MPAA rating for movies from filename
                    mpaa = ""
                    if not isTV and itemPath:
                        filename = os.path.basename(itemPath)
                        # Movie pattern: Title - MPAA - Genre - Resolution...
                        parts = filename.split(" - ")
                        if len(parts) >= 2:
                            # Second part should be MPAA rating
                            mpaa = parts[1].strip()

                    # Format airtime info
                    airtimeInfo = self.formatAirtime(airtime, channelNumber)
                    
                    # Build recommendation object
                    recommendation = {
                        "title": title,
                        "poster": poster,
                        "plot": description,
                        "genre": genre if genre else "General",
                        "channelNumber": channelNumber,
                        "channelName": channel.name,
                        "airtimeInfo": airtimeInfo
                    }
                    
                    if isAudio:
                        recommendation["type"] = "audio"
                        recommendation["artist"] = artist
                        recommendation["album"] = album
                        # For audio, create a subtitle in "Artist - Album" format
                        if artist and album:
                            recommendation["audio_info"] = "%s - %s" % (artist, album)
                        elif artist:
                            recommendation["audio_info"] = artist
                        elif album:
                            recommendation["audio_info"] = album
                        else:
                            recommendation["audio_info"] = ""
                    elif isTV:
                        recommendation["type"] = "episode"
                        recommendation["episode_title"] = episodeTitle
                        
                        # Try to parse season/episode from episodeTitle
                        # Common formats: "S01E01", "1x01", "Season 1 Episode 1"
                        season = ""
                        episode = ""
                        
                        # Try S##E## format
                        match = re.search(r'[Ss](\d+)[Ee](\d+)', episodeTitle)
                        if match:
                            season = match.group(1)
                            episode = match.group(2)
                        else:
                            # Try #x## format
                            match = re.search(r'(\d+)x(\d+)', episodeTitle)
                            if match:
                                season = match.group(1)
                                episode = match.group(2)
                        
                        if season and episode:
                            recommendation["episode_info"] = "S%sE%s" % (season.zfill(2), episode.zfill(2))
                        else:
                            recommendation["episode_info"] = episodeTitle
                    else:
                        recommendation["type"] = "movie"
                        
                        # Try to extract year from filename for movies
                        year = ""
                        if itemPath:
                            filename = os.path.basename(itemPath)
                            # Look for 4-digit year in parentheses or brackets
                            match = re.search(r'[\(\[]?(19\d{2}|20\d{2})[\)\]]?', filename)
                            if match:
                                year = match.group(1)
                        
                        recommendation["year"] = year
                        recommendation["mpaa"] = mpaa
                    
                    recommendations.append(recommendation)
                    
                except Exception as e:
                    self.log("Error processing recommendation: %s" % str(e))
                    import traceback
                    self.log(traceback.format_exc())
                    continue
            
            self.log("fetchRandomRecommendations - returning %d recommendations" % len(recommendations))
            return recommendations
            
        except Exception as e:
            self.log("fetchRandomRecommendations FAILED: %s" % str(e))
            import traceback
            self.log(traceback.format_exc())
            return []
    
    def formatAirtime(self, airtime, channelNumber):
        """Format airtime timestamp into readable string"""
        try:
            from datetime import datetime
            
            # Convert to datetime
            airtimeDate = datetime.fromtimestamp(airtime)
            
            # Format the output
            dayName = airtimeDate.strftime("%A").upper()
            timeStr = airtimeDate.strftime("%I:%M %p").lstrip("0")
            
            return "%s - %s - CHANNEL %d" % (dayName, timeStr, channelNumber)
            
        except Exception as e:
            self.log("Error formatting airtime: %s" % str(e), xbmc.LOGERROR)
            return "CHANNEL %d" % channelNumber
    
    def updateRecommendationsData(self):
        """Update window properties with recommendations data"""
        self.log("updateRecommendationsData - STARTING")
        
        recommendations = self.fetchRandomRecommendations()
        
        if not recommendations:
            self.log("No recommendations found")
            self.setProperty("PTV.Recommendations.Featured.Title", "No Unwatched Content")
            self.setProperty("PTV.Recommendations.Featured.Subtitle", "Everything is watched!")
            return
        
        # Store all items
        self.recommendationsItems = recommendations
        
        # Set the first featured item
        if recommendations:
            self.updateRecommendationsFeaturedItem(0)
        
        self.log("updateRecommendationsData - COMPLETED")
    
    def getGenreArtwork(self, genre):
        """Map genre name to channel artwork file"""
        self.log("=== getGenreArtwork DEBUG START ===")
        self.log("Input genre: " + str(genre))
        
        # NEW: Check if this is an audio channel (starts with "Music Genre - ")
        if genre and genre.startswith("Music Genre - "):
            self.log("Detected audio channel genre")
            # Audio channels: use the full channel name as the filename
            artwork_filename = genre + ".png"
            self.log("Audio channel artwork filename: " + artwork_filename)
            
            artwork_path = translatePath(
                "special://home/addons/script.paragontv/resources/logos/" + artwork_filename
            )
            
            self.log("Checking audio channel path: " + artwork_path)
            
            if FileAccess.exists(artwork_path):
                self.log("SUCCESS: Found audio channel artwork at: " + artwork_path)
                self.log("=== getGenreArtwork DEBUG END ===")
                return artwork_path
            else:
                self.log("WARNING: Audio channel artwork not found at: " + artwork_path)
                self.log("=== getGenreArtwork DEBUG END ===")
                return ""
        
        # Determine if we're showing a movie or TV show based on the current featured item
        # Default to Movies
        item_type = "Movies"
        if self.recommendationsItems and self.recommendationsFeaturedIndex < len(self.recommendationsItems):
            current_item = self.recommendationsItems[self.recommendationsFeaturedIndex]
            item_type_raw = current_item.get("type")
            self.log("Current item type: " + str(item_type_raw))
            if item_type_raw == "episode":
                item_type = "TV"
        
        self.log("Determined item_type: " + item_type)
        
        # Map common genres to your channel artwork with type suffix
        genre_map = {
            "Action": "Action %s.png" % item_type,
            "Adventure": "Adventure %s.png" % item_type,
            "Animation": "Animation %s.png" % item_type,
            "Comedy": "Comedy %s.png" % item_type,
            "Crime": "Crime %s.png" % item_type,
            "Documentary": "Documentary %s.png" % item_type,
            "Drama": "Drama %s.png" % item_type,
            "Family": "Family %s.png" % item_type,
            "Fantasy": "Fantasy %s.png" % item_type,
            "Horror": "Horror %s.png" % item_type,
            "Mystery": "Mystery %s.png" % item_type,
            "Romance": "Romance %s.png" % item_type,
            "Science Fiction": "Science Fiction %s.png" % item_type,
            "Sci-Fi & Fantasy": "Science Fiction %s.png" % item_type,
            "Thriller": "Thriller %s.png" % item_type,
            "Western": "Western %s.png" % item_type,
            "War": "War %s.png" % item_type,
        }
        
        # Get the mapped artwork filename
        artwork_filename = genre_map.get(genre)
        self.log("Mapped filename from genre_map: " + str(artwork_filename))
        
        if not artwork_filename:
            # If genre not in map, try generic format
            artwork_filename = "%s %s.png" % (genre, item_type)
            self.log("Genre not in map, using generic format: " + artwork_filename)
        
        # Return full path to artwork in logos folder
        artwork_path = translatePath(
            "special://home/addons/script.paragontv/resources/logos/" + artwork_filename
        )
        
        self.log("Checking path: " + artwork_path)
        
        # Check if file exists
        if FileAccess.exists(artwork_path):
            self.log("SUCCESS: Found genre artwork at: " + artwork_path)
            self.log("=== getGenreArtwork DEBUG END ===")
            return artwork_path
        else:
            self.log("File NOT found at primary path")
            # Try fallback without type suffix
            fallback_filename = "%s.png" % genre
            fallback_path = translatePath(
                "special://home/addons/script.paragontv/resources/logos/" + fallback_filename
            )
            self.log("Trying fallback path: " + fallback_path)
            
            if FileAccess.exists(fallback_path):
                self.log("SUCCESS: Found genre artwork (fallback) at: " + fallback_path)
                self.log("=== getGenreArtwork DEBUG END ===")
                return fallback_path
            else:
                self.log("Fallback also NOT found")
                # Final fallback to icon.png
                icon_path = translatePath(
                    "special://home/addons/script.paragontv/icon.png"
                )
                self.log("Using final fallback: " + icon_path)
                self.log("=== getGenreArtwork DEBUG END ===")
                return icon_path
    
    def updateRecommendationsFeaturedItem(self, index):
        """Update the featured recommendation display"""
        self.log("updateRecommendationsFeaturedItem - index %d" % index)
        
        if not self.recommendationsItems or index >= len(self.recommendationsItems):
            return
        
        # Only cycle through first 4 items (2 min Ã· 30 sec each)
        if index >= 4:
            index = 0
        
        item = self.recommendationsItems[index]
        self.recommendationsFeaturedIndex = index
        
        # Set featured properties
        self.setProperty("PTV.Recommendations.Featured.Poster", item.get("poster", ""))
        self.setProperty("PTV.Recommendations.Featured.Title", item.get("title", ""))
        
        if item["type"] == "audio":
            self.setProperty("PTV.Recommendations.Featured.Subtitle", item.get("audio_info", ""))
            self.setProperty("PTV.Recommendations.Featured.EpisodeTitle", "")
            self.setProperty("PTV.Recommendations.Featured.Type", "Audio Track")
            self.setProperty("PTV.Recommendations.Featured.Plot", "")
            self.setProperty("PTV.Recommendations.Featured.MPAA", "")
        elif item["type"] == "movie":
            self.setProperty("PTV.Recommendations.Featured.Subtitle", str(item.get("year", "")))
            self.setProperty("PTV.Recommendations.Featured.EpisodeTitle", "")
            self.setProperty("PTV.Recommendations.Featured.Type", "Movie")
            self.setProperty("PTV.Recommendations.Featured.Plot", item.get("plot", ""))
            self.setProperty("PTV.Recommendations.Featured.MPAA", item.get("mpaa", ""))
        else:  # TV Show
            self.setProperty("PTV.Recommendations.Featured.Subtitle", item.get("episode_info", ""))
            self.setProperty("PTV.Recommendations.Featured.EpisodeTitle", item.get("episode_title", ""))
            self.setProperty("PTV.Recommendations.Featured.Type", "TV Show")
            self.setProperty("PTV.Recommendations.Featured.Plot", item.get("plot", ""))
            self.setProperty("PTV.Recommendations.Featured.MPAA", "")
        
        # Set the genre artwork for THIS featured item
        genre = item.get("genre", "")
        if genre:
            genre_artwork = self.getGenreArtwork(genre)
            self.setProperty("PTV.Recommendations.GenreArtwork", genre_artwork)
            self.log("Set genre artwork: " + genre_artwork)
        else:
            self.setProperty("PTV.Recommendations.GenreArtwork", "")
        
        # Set airtime info
        airtimeInfo = item.get("airtimeInfo", "")
        self.setProperty("PTV.Recommendations.AirtimeInfo", airtimeInfo)
        self.log("Set airtime info: " + airtimeInfo)
        
        self.log("updateRecommendationsFeaturedItem - Set to: %s" % item.get("title"))
    
    def rotateRecommendationsFeaturedItem(self):
        """Rotate to next featured recommendation"""
        if not self.showingRecommendations:
            return
        
        if not self.recommendationsItems or len(self.recommendationsItems) == 0:
            self.recommendationsRotationTimer = threading.Timer(30.0, self.rotateRecommendationsFeaturedItem)
            if not self.isExiting:
                self.recommendationsRotationTimer.start()
            return
        
        # Move to next item (cycle through 4 items: 2 min Ã· 30 sec each)
        next_index = (self.recommendationsFeaturedIndex + 1) % min(4, len(self.recommendationsItems))
        
        # Update display
        self.updateRecommendationsFeaturedItem(next_index)
        
        # Schedule next rotation
        self.recommendationsRotationTimer = threading.Timer(30.0, self.rotateRecommendationsFeaturedItem)
        if not self.isExiting:
            self.recommendationsRotationTimer.start()
    
    def recommendationsRefreshAction(self):
        """Periodically refresh recommendations data"""
        if not self.showingRecommendations:
            return
        
        self.log("recommendationsRefreshAction - refreshing data")
        self.updateRecommendationsData()
        
        # Schedule next refresh
        self.recommendationsRefreshTimer = threading.Timer(
            self.recommendationsRefreshInterval,
            self.recommendationsRefreshAction
        )
        if not self.isExiting:
            self.recommendationsRefreshTimer.start()
    
    def showRecommendationsOverlay(self, persistent=False):
        """Show the recommendations overlay"""
        self.log("showRecommendationsOverlay - STARTED")
        
        # Show recommendations overlay
        self.showingRecommendations = True
        self.setProperty("PTV.Recommendations", "true")
        
        # Also show weather in lower third
        self.showingWeather = True
        self.setProperty("PTV.Weather", "true")
        
        # Update weather info
        self.updateWeatherInfo()
        
        # Fetch recommendations data
        try:
            self.updateRecommendationsData()
        except Exception as e:
            self.log("showRecommendationsOverlay - updateRecommendationsData failed: " + str(e), xbmc.LOGERROR)
        
        # Start rotation timer
        if self.recommendationsRotationTimer and self.recommendationsRotationTimer.isAlive():
            self.recommendationsRotationTimer.cancel()
        
        self.recommendationsRotationTimer = threading.Timer(30.0, self.rotateRecommendationsFeaturedItem)
        self.recommendationsRotationTimer.start()
        
        # Start refresh timer
        if self.recommendationsRefreshTimer and self.recommendationsRefreshTimer.isAlive():
            self.recommendationsRefreshTimer.cancel()
        
        self.recommendationsRefreshTimer = threading.Timer(
            self.recommendationsRefreshInterval,
            self.recommendationsRefreshAction
        )
        self.recommendationsRefreshTimer.start()
        
        if not persistent:
            if (
                hasattr(self, "recommendationsTimer")
                and self.recommendationsTimer is not None
                and self.recommendationsTimer.isAlive()
            ):
                self.recommendationsTimer.cancel()
            
            self.recommendationsTimer = threading.Timer(100.0, self.hideRecommendationsOverlay)
            self.recommendationsTimer.start()
        
        self.log("showRecommendationsOverlay - COMPLETED")
    
    def hideRecommendationsOverlay(self):
        """Hide the recommendations overlay"""
        self.log("hideRecommendationsOverlay")
        self.showingRecommendations = False
        self.setProperty("PTV.Recommendations", "false")
        
        # Don't hide weather if we're on channel 99
        if self.currentChannel != 99:
            self.showingWeather = False
            self.setProperty("PTV.Weather", "false")
        
        # Cancel timers
        if self.recommendationsRotationTimer is not None and self.recommendationsRotationTimer.isAlive():
            self.recommendationsRotationTimer.cancel()
        
        if self.recommendationsRefreshTimer is not None and self.recommendationsRefreshTimer.isAlive():
            self.recommendationsRefreshTimer.cancel()
        
        if hasattr(self, "recommendationsTimer") and self.recommendationsTimer is not None and self.recommendationsTimer.isAlive():
            self.recommendationsTimer.cancel()
        
        self.log("hideRecommendationsOverlay return")

    def fetchServerStats(self):
        """Fetch stats from Unraid server via SSH"""
        self.log("fetchServerStats - STARTED")
        
        try:
            import subprocess
            
            stats = {}
            
            # Build SSH command prefix
            import platform
            if platform.system() == "Windows":
                # On Windows, check for SSH in multiple locations
                import os
                possible_ssh_paths = [
                    "C:\\Windows\\System32\\OpenSSH\\ssh.exe",
                    "C:\\Program Files\\Git\\usr\\bin\\ssh.exe",
                    "ssh.exe"  # Try PATH
                ]
                ssh_executable = None
                for path in possible_ssh_paths:
                    if os.path.exists(path) or path == "ssh.exe":
                        ssh_executable = path
                        break
                
                if not ssh_executable:
                    self.log("SSH not found on Windows", xbmc.LOGERROR)
                    return {}
                
                # Windows SSH key path
                import os.path
                ssh_key = os.path.expanduser("~/.ssh/id_rsa")
            else:
                ssh_executable = "ssh"
                ssh_key = self.unraidSSHKey

            ssh_cmd = [
                ssh_executable,
                "-i", ssh_key,
                "-o", "StrictHostKeyChecking=no",
                "-o", "UserKnownHostsFile=/dev/null",
                "-o", "LogLevel=ERROR",
                "%s@%s" % (self.unraidSSHUser, self.unraidSSHHost)
            ]
            
            # Get disk usage (df -h)
            self.log("Fetching disk usage...")
            result = subprocess.check_output(ssh_cmd + ["df -h | grep '/mnt/disk\\|/mnt/cache\\|/mnt/user'"])
            df_output = result
            
            # Get temperatures (sensors)
            self.log("Fetching temperatures...")
            result = subprocess.check_output(ssh_cmd + ["sensors"])
            sensors_output = result
            
            # Get uptime
            self.log("Fetching uptime...")
            result = subprocess.check_output(ssh_cmd + ["uptime"])
            uptime_output = result.strip()
            
            # Get CPU usage percentage (more reliable method)
            self.log("Fetching CPU usage...")
            result = subprocess.check_output(ssh_cmd + ["grep 'cpu ' /proc/stat | awk '{usage=($2+$4)*100/($2+$4+$5)} END {printf \"%.0f\", usage}'"])
            cpu_usage = result.strip()

            # Get RAM usage
            self.log("Fetching RAM usage...")
            result = subprocess.check_output(ssh_cmd + ["free | grep Mem | awk '{printf \"%.0f\", $3/$2 * 100.0}'"])
            ram_usage = result.strip()
            
            # Parse disk usage
            disks = []
            cache = {}
            array_total = {}

            for line in df_output.split('\n'):
                if not line.strip():
                    continue
                
                self.log("Parsing df line: %s" % line)
                
                try:
                    if '/mnt/disk' in line and 'tmpfs' not in line:  # ADD: and 'tmpfs' not in line
                        parts = line.split()
                        if len(parts) < 5:
                            self.log("Skipping malformed disk line: %s" % line)
                            continue
                        
                        # Try to extract disk number from device name
                        device = parts[0]
                        disk_num = "?"
                        
                        # Handle different formats: /dev/md1p1, /dev/sda1, etc.
                        if 'md' in device and 'p' in device:
                            disk_num = device.split('md')[1].split('p')[0]
                        elif 'sd' in device:
                            disk_num = device.split('sd')[1][0]  # Just the letter
                        
                        disks.append({
                            'name': 'Disk %s' % disk_num,
                            'total': parts[1],
                            'used': parts[2],
                            'avail': parts[3],
                            'percent': parts[4].rstrip('%')
                        })
                        
                    elif '/mnt/cache' in line:
                        parts = line.split()
                        if len(parts) >= 5:
                            cache = {
                                'total': parts[1],
                                'used': parts[2],
                                'avail': parts[3],
                                'percent': parts[4].rstrip('%')
                            }
                            
                    elif '/mnt/user' in line and 'user0' not in line:
                        parts = line.split()
                        if len(parts) >= 5:
                            array_total = {
                                'total': parts[1],
                                'used': parts[2],
                                'avail': parts[3],
                                'percent': parts[4].rstrip('%')
                            }
                except Exception as e:
                    self.log("Error parsing line '%s': %s" % (line, str(e)), xbmc.LOGERROR)
                    continue
            
            # Parse temperatures
            cpu_temp = ""
            cache_temp = ""

            for line in sensors_output.split('\n'):
                try:
                    if 'CPU Temp:' in line or 'Tctl:' in line:
                        # Extract temperature - handle both degree symbols
                        if '+' in line:
                            temp_str = line.split('+')[1]
                            # Split on either degree symbol or 'C'
                            temp = temp_str.split('C')[0].replace(u'Â°', '').strip()
                            if temp:
                                cpu_temp = "%dÂ°F" % int(float(temp) * 9/5 + 32)
                    elif 'Composite:' in line:
                        if '+' in line:
                            temp_str = line.split('+')[1]
                            temp = temp_str.split('C')[0].replace(u'Â°', '').strip()
                            if temp:
                                cache_temp = "%dÂ°F" % int(float(temp) * 9/5 + 32)
                except Exception as e:
                    self.log("Error parsing temperature line '%s': %s" % (line, str(e)), xbmc.LOGERROR)
                    continue
            
            # Parse uptime
            uptime_str = ""
            if 'up' in uptime_output:
                parts = uptime_output.split('up')[1].split(',')
                uptime_str = parts[0].strip()
                if len(parts) > 1:
                    uptime_str += ", " + parts[1].strip()
            
            # Parse load average
            load_avg = ""
            if 'load average:' in uptime_output:
                load_avg = uptime_output.split('load average:')[1].strip()
            
            # Build stats dictionary
            stats = {
                'disks': disks,
                'cache': cache,
                'cache_temp': cache_temp,
                'array_total': array_total,
                'cpu_temp': cpu_temp,
                'cpu_usage': cpu_usage + "%",  # ADD THIS
                'ram_usage': ram_usage + "%",  # ADD THIS
                'uptime': uptime_str,
                'load_avg': load_avg,
                'server_name': 'DIVINITY'
            }
            
            self.log("fetchServerStats - SUCCESS: %d disks, %s uptime" % (len(disks), uptime_str))
            return stats
            
        except Exception as e:
            self.log("Error fetching server stats: %s" % str(e), xbmc.LOGERROR)
            import traceback
            self.log("Traceback: %s" % traceback.format_exc(), xbmc.LOGERROR)
            return {}

    def updateServerStatsData(self):
        """Update server stats data"""
        self.log("updateServerStatsData - STARTING")
        
        try:
            stats = self.fetchServerStats()
            
            if not stats:
                self.log("No stats returned")
                return
            
            self.serverStatsData = stats
            
            # Set properties for XML
            self.setProperty("PTV.ServerStats.Name", stats.get('server_name', ''))
            self.setProperty("PTV.ServerStats.Uptime", stats.get('uptime', ''))
            self.setProperty("PTV.ServerStats.CPUTemp", stats.get('cpu_temp', ''))
            self.setProperty("PTV.ServerStats.LoadAvg", stats.get('load_avg', ''))
            self.setProperty("PTV.ServerStats.CPUUsage", stats.get('cpu_usage', ''))  # ADD THIS
            self.setProperty("PTV.ServerStats.RAMUsage", stats.get('ram_usage', ''))  # ADD THIS
            
            # Array total
            array = stats.get('array_total', {})
            self.setProperty("PTV.ServerStats.Array.Total", array.get('total', ''))
            self.setProperty("PTV.ServerStats.Array.Used", array.get('used', ''))
            self.setProperty("PTV.ServerStats.Array.Percent", array.get('percent', ''))
            
            # Cache
            cache = stats.get('cache', {})
            self.setProperty("PTV.ServerStats.Cache.Total", cache.get('total', ''))
            self.setProperty("PTV.ServerStats.Cache.Used", cache.get('used', ''))
            self.setProperty("PTV.ServerStats.Cache.Percent", cache.get('percent', ''))
            self.setProperty("PTV.ServerStats.Cache.Temp", stats.get('cache_temp', ''))
            
            # Individual disks
            disks = stats.get('disks', [])
            for i, disk in enumerate(disks[:5], 1):  # Up to 5 disks
                self.setProperty("PTV.ServerStats.Disk.%d.Name" % i, disk.get('name', ''))
                self.setProperty("PTV.ServerStats.Disk.%d.Used" % i, disk.get('used', ''))
                self.setProperty("PTV.ServerStats.Disk.%d.Total" % i, disk.get('total', ''))
                self.setProperty("PTV.ServerStats.Disk.%d.Percent" % i, disk.get('percent', ''))
            
            self.log("updateServerStatsData - COMPLETED")
            
        except Exception as e:
            self.log("Error in updateServerStatsData: %s" % str(e), xbmc.LOGERROR)

    def fetchRandomWikipediaArticle(self):
        """Fetch a random Wikipedia article from curated lists without repeating until all are viewed"""
        try:
            import random

            # Build flat list of all articles if not already done
            if not self.wikipedia_all_articles:
                self.log("Building flat list of all Wikipedia articles...")
                for category_articles in WIKIPEDIA_ARTICLES.values():
                    self.wikipedia_all_articles.extend(category_articles)
                self.log("Total Wikipedia articles available: %d" % len(self.wikipedia_all_articles))

            # If we've viewed all articles, reset the viewed list
            if len(self.wikipedia_viewed_articles) >= len(self.wikipedia_all_articles):
                self.log("All Wikipedia articles viewed! Resetting viewed list.")
                self.wikipedia_viewed_articles = []

            # Get list of unviewed articles
            unviewed_articles = [a for a in self.wikipedia_all_articles if a not in self.wikipedia_viewed_articles]

            # Pick random article from unviewed articles
            article_title = random.choice(unviewed_articles)
            self.log("Selected article: %s (viewed %d of %d)" % (
                article_title,
                len(self.wikipedia_viewed_articles),
                len(self.wikipedia_all_articles)
            ))

            # Fetch article content from Kiwix
            article_data = self.fetchWikipediaContent(article_title)

            if article_data:
                # Mark this article as viewed
                self.wikipedia_viewed_articles.append(article_title)

                self.knowledge_current_content = article_data
                self.updateKnowledgeDisplay()

        except Exception as e:
            self.log("Error fetching Wikipedia article: %s" % str(e))
    
    def fetchRandomFunFact(self):
        """Fetch a random fun fact article"""
        try:
            import random
            
            # Build flat list of all fun facts if not already done
            if not hasattr(self, 'funfacts_all_articles') or not self.funfacts_all_articles:
                self.funfacts_all_articles = []
                self.log("Building flat list of all Fun Facts articles...")
                for category_articles in FUNFACTS_ARTICLES.values():
                    self.funfacts_all_articles.extend(category_articles)
                self.log("Total Fun Facts articles available: %d" % len(self.funfacts_all_articles))
            
            # Pick random article from fun facts
            article_title = random.choice(self.funfacts_all_articles)
            self.log("Selected fun fact: %s" % article_title)
            
            # Fetch article content from Kiwix (uses same Wikipedia ZIM)
            article_data = self.fetchWikipediaContent(article_title)
            
            if article_data:
                # Override source to say "Fun Facts" instead of "Wikipedia"
                article_data['source'] = 'Fun Facts'
                self.knowledge_current_content = article_data
                self.updateKnowledgeDisplay()
                
        except Exception as e:
            self.log("Error fetching fun fact: %s" % str(e))

    def fetchRandomTrivia(self):
        """Fetch a random trivia article"""
        try:
            import random
            
            # Build flat list of all trivia if not already done
            if not hasattr(self, 'trivia_all_articles') or not self.trivia_all_articles:
                self.trivia_all_articles = []
                self.log("Building flat list of all Trivia articles...")
                for category_articles in TRIVIA_ARTICLES.values():
                    self.trivia_all_articles.extend(category_articles)
                self.log("Total Trivia articles available: %d" % len(self.trivia_all_articles))
            
            # Pick random article from trivia
            article_title = random.choice(self.trivia_all_articles)
            self.log("Selected trivia: %s" % article_title)
            
            # Fetch article content from Kiwix (uses same Wikipedia ZIM)
            article_data = self.fetchWikipediaContent(article_title)
            
            if article_data:
                # Override source to say "Trivia" instead of "Wikipedia"
                article_data['source'] = 'Trivia'
                self.knowledge_current_content = article_data
                self.updateKnowledgeDisplay()
                
        except Exception as e:
            self.log("Error fetching trivia: %s" % str(e))

    def fetchRandomMystery(self):
        """Fetch a random unsolved mystery article"""
        try:
            import random
            
            # Build flat list of all mysteries if not already done
            if not hasattr(self, 'mysteries_all_articles') or not self.mysteries_all_articles:
                self.mysteries_all_articles = []
                self.log("Building flat list of all Mystery articles...")
                for category_articles in MYSTERIES_ARTICLES.values():
                    self.mysteries_all_articles.extend(category_articles)
                self.log("Total Mystery articles available: %d" % len(self.mysteries_all_articles))
            
            # Pick random article from mysteries
            article_title = random.choice(self.mysteries_all_articles)
            self.log("Selected mystery: %s" % article_title)
            
            # Fetch article content from Kiwix (uses same Wikipedia ZIM)
            article_data = self.fetchWikipediaContent(article_title)
            
            if article_data:
                # Override source to say "Unsolved Mysteries" instead of "Wikipedia"
                article_data['source'] = 'Unsolved Mysteries'
                self.knowledge_current_content = article_data
                self.updateKnowledgeDisplay()
                
        except Exception as e:
            self.log("Error fetching mystery: %s" % str(e))
    
    def fetchWikipediaContent(self, article_title):
        """Fetch article content from Kiwix server"""
        try:
            import urllib2
            import re
            
            # Get Wikipedia config from KNOWLEDGE_SOURCES
            wiki_config = KNOWLEDGE_SOURCES['wikipedia']
            base_url = wiki_config['base_url']
            
            # Construct URL - first letter + article title
            first_letter = article_title[0].upper()
            url = "%s/%s/%s" % (base_url, first_letter, article_title)
            
            self.log("Fetching Wikipedia article: %s" % url)
            
            # Fetch article
            response = urllib2.urlopen(url, timeout=10)
            html_content = response.read()
            
            # Parse article
            article_data = self.parseWikipediaArticle(html_content, article_title)
            
            # Add type and source for Knowledge Page
            if article_data:
                article_data['type'] = 'article'
                article_data['source'] = 'Wikipedia'
            
            return article_data
            
        except Exception as e:
            self.log("Error fetching Wikipedia content for %s: %s" % (article_title, str(e)))
            return None
    
    def cleanWikipediaText(self, text):
        """Clean Wikipedia text by removing citations, HTML entities, and problematic characters."""
        if not text:
            return text
        
        # Ensure text is Unicode for Python 2/3 compatibility
        if sys.version_info[0] < 3:  # Python 2
            if not isinstance(text, unicode):
                text = text.decode('utf-8', 'ignore')
        
        # Decode HTML entities (Python 2/3 compatible)
        try:
            text = html.unescape(text)  # Python 3
        except AttributeError:
            text = html.unescape(text)  # Python 2 (html is HTMLParser instance)
        
        # Remove citation brackets
        text = re.sub(r'\[\d+\]', '', text)
        text = re.sub(r'\[note \d+\]', '', text)
        text = re.sub(r'\[citation needed\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\[clarification needed\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\[edit\]', '', text, flags=re.IGNORECASE)
        
        # Replace problematic Unicode characters
        replacements = {
            u'\u2013': '-', u'\u2014': '--', u'\u2212': '-',
            u'\u2018': "'", u'\u2019': "'", u'\u201c': '"', u'\u201d': '"',
            u'\u2026': '...', u'\u2022': '*', u'\u00a0': ' ',
            u'\u00b0': ' degrees', u'\u00d7': 'x', u'\u00f7': '/',
            u'\u00e9': 'e', u'\u00e8': 'e', u'\u00ea': 'e', u'\u00eb': 'e',
            u'\u00e0': 'a', u'\u00e1': 'a', u'\u00e2': 'a', u'\u00e4': 'a',
            u'\u00ed': 'i', u'\u00ec': 'i', u'\u00ee': 'i', u'\u00ef': 'i',
            u'\u00f3': 'o', u'\u00f2': 'o', u'\u00f4': 'o', u'\u00f6': 'o',
            u'\u00fa': 'u', u'\u00f9': 'u', u'\u00fb': 'u', u'\u00fc': 'u',
            u'\u00f1': 'n', u'\u00e7': 'c', u'\u00fd': 'y', u'\u00ff': 'y',
        }
        
        for unicode_char, replacement in replacements.items():
            text = text.replace(unicode_char, replacement)
        
        # Remove remaining non-ASCII characters
        # For Python 2, we need to handle this carefully
        cleaned_chars = []
        for char in text:
            try:
                if ord(char) < 128:
                    cleaned_chars.append(char)
                else:
                    cleaned_chars.append(' ')
            except:
                cleaned_chars.append(' ')
        
        text = ''.join(cleaned_chars)
        
        # Clean up multiple spaces
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Convert back to str for Python 2 compatibility
        if sys.version_info[0] < 3:  # Python 2
            text = text.encode('ascii', 'ignore')
        
        return text

    def parseWikipediaArticle(self, html_content, article_title):
        """Parse Wikipedia article HTML to extract title, image, text, metadata"""
        try:
            import re
            
            # URL decode the title first (converts %27 to ', %20 to space, etc.)
            try:
                import urllib
                decoded_title = urllib.unquote(article_title)
            except ImportError:
                import urllib.parse
                decoded_title = urllib.parse.unquote(article_title)
            
            article_data = {
                'title': self.cleanWikipediaText(decoded_title.replace('_', ' ')),  # Decode, replace underscores, then clean
                'image': '',
                'text': '',
                'categories': [],
                'word_count': 0
            }
            
            # Extract main image from infobox or first image
            img_pattern = r'<img[^>]+src="([^"]+)"[^>]*>'
            img_matches = re.findall(img_pattern, html_content)
            self.log("Found %d total images in article" % len(img_matches))

            # Separate landscape and portrait candidates
            landscape_candidates = []
            other_candidates = []

            if img_matches:
                # Get first substantial image (not icons)
                for img_url in img_matches:
                    self.log("Checking image URL: %s" % img_url)
                    
                    # Skip tiny icons, edit buttons, and UI elements
                    skip_terms = ['edit', 'icon', 'logo', '20px', '25px', '30px', '15px', 'button', 'magnify']
                    if any(skip in img_url.lower() for skip in skip_terms):
                        self.log("Skipping small/UI image")
                        continue
                    
                    # Skip SVG files (usually icons/diagrams)
                    if '.svg' in img_url.lower():
                        self.log("Skipping SVG image")
                        continue
                    
                    # Prioritize landscape images (common patterns in filenames)
                    landscape_hints = ['landscape', 'panorama', 'wide', 'view', 'scene', 'exterior']
                    is_landscape_hint = any(hint in img_url.lower() for hint in landscape_hints)
                    
                    # Also deprioritize portrait-style images
                    portrait_hints = ['portrait', 'poster', 'cover', 'infobox']
                    is_portrait_hint = any(hint in img_url.lower() for hint in portrait_hints)
                    
                    if is_landscape_hint:
                        landscape_candidates.insert(0, img_url)
                        self.log("Flagged as landscape candidate")
                    elif is_portrait_hint:
                        other_candidates.append(img_url)
                        self.log("Flagged as portrait candidate")
                    else:
                        landscape_candidates.append(img_url)
                
                # Try landscape candidates first, then others
                all_candidates = landscape_candidates + other_candidates
                
                for img_url in all_candidates:
                    # Found a good image - construct full URL with ZIM path
                    wiki_base = KNOWLEDGE_SOURCES['wikipedia']['base_url']
                    if img_url.startswith('http'):
                        full_url = img_url
                    elif img_url.startswith('//'):
                        full_url = "http:" + img_url
                    elif img_url.startswith('./'):
                        full_url = wiki_base + "/" + img_url[2:]
                    elif img_url.startswith('/'):
                        full_url = wiki_base + img_url
                    else:
                        full_url = wiki_base + "/" + img_url
                    
                    article_data['image'] = full_url
                    self.log("Selected article image: %s" % full_url)
                    break
                
                if not article_data['image']:
                    self.log("No suitable images found after filtering")
            else:
                self.log("No images found in article HTML")
            
            # Extract main content paragraphs
            content_start = html_content.find('<p>')
            if content_start > 0:
                html_content = html_content[content_start:]
            
            # Extract paragraphs
            p_pattern = r'<p>(.*?)</p>'
            paragraphs = re.findall(p_pattern, html_content, re.DOTALL)
            
            # Clean paragraphs
            cleaned_paragraphs = []
            for p in paragraphs[:15]:
                # Remove HTML tags
                clean = re.sub(r'<[^>]+>', '', p)
                # Remove reference markers
                clean = re.sub(r'\[\d+\]', '', clean)
                # Remove extra whitespace
                clean = re.sub(r'\s+', ' ', clean).strip()
                
                if len(clean) > 50:
                    cleaned_paragraphs.append(clean)
            
            # Join paragraphs and apply comprehensive cleaning
            article_data['text'] = self.cleanWikipediaText('\n\n'.join(cleaned_paragraphs))
            article_data['word_count'] = len(article_data['text'].split())
            
            # Extract categories
            cat_pattern = r'<a[^>]+title="Category:([^"]+)"'
            categories = re.findall(cat_pattern, html_content)
            article_data['categories'] = [self.cleanWikipediaText(cat) for cat in categories[:5]]
            
            return article_data
            
        except Exception as e:
            self.log("Error parsing Wikipedia article: %s" % str(e))
            return None
 
    def updateKnowledgeDisplay(self):
        """Update display for both Wikipedia and Stack Exchange content"""
        try:
            if not self.knowledge_current_content:
                return
            
            content = self.knowledge_current_content
            
            # Set source indicator
            self.setProperty("PTV.Knowledge.Source", content.get('source', 'Knowledge'))
            
            # Wikipedia article format (works for all our topics now!)
            self.setProperty("PTV.Wikipedia.Title", content['title'])
            
            if content.get('image'):
                self.setProperty("PTV.Wikipedia.Image", content['image'])
            else:
                self.setProperty("PTV.Wikipedia.Image", "DefaultVideo.png")
            
            self.setProperty("PTV.Wikipedia.Text", content['text'])
            self.setProperty("PTV.Wikipedia.WordCount", str(content['word_count']) + " words")
            
            if content.get('categories'):
                self.setProperty("PTV.Wikipedia.Categories", ", ".join(content['categories'][:3]))
            else:
                self.setProperty("PTV.Wikipedia.Categories", "General")
            
            # Set date
            import datetime
            current_date = datetime.datetime.now().strftime("%B %Y")
            self.setProperty("PTV.Wikipedia.Date", current_date)
            
            self.log("Knowledge updated: %s (%s)" % (content['title'], content.get('source', 'Unknown')))
            
        except Exception as e:
            self.log("Error updating knowledge display: %s" % str(e))

    def startKnowledgePage(self):
        """Initialize Knowledge Page - picks next source in rotation"""
        try:
            # Get next source in rotation
            source_key = KNOWLEDGE_ROTATION[self.knowledge_rotation_index]
            source_config = KNOWLEDGE_SOURCES[source_key]
            
            self.log("Starting Knowledge Page with source: %s" % source_config['name'])
            
            # Advance rotation index for next time
            self.knowledge_rotation_index = (self.knowledge_rotation_index + 1) % len(KNOWLEDGE_ROTATION)
            
            # Fetch content based on source type
            if source_config['type'] == 'article':
                self.fetchRandomWikipediaArticle()
            elif source_config['type'] == 'funfacts':
                self.fetchRandomFunFact()
            elif source_config['type'] == 'trivia':
                self.fetchRandomTrivia()
            elif source_config['type'] == 'mysteries':
                self.fetchRandomMystery()
            
            # Show overlay
            self.setProperty("PTV.ShowWikipedia", "true")
            self.showingWikipedia = True
            
        except Exception as e:
            self.log("Error starting Knowledge Page: %s" % str(e))

    def stopKnowledgePage(self):
        """Stop Knowledge Page and clear display"""
        try:
            self.log("Stopping Knowledge Page...")
            
            # Clear display
            self.setProperty("PTV.ShowWikipedia", "false")
            self.setProperty("PTV.Wikipedia.Title", "")
            self.setProperty("PTV.Wikipedia.Image", "")
            self.setProperty("PTV.Wikipedia.Text", "")
            self.setProperty("PTV.Wikipedia.WordCount", "")
            self.setProperty("PTV.Wikipedia.Categories", "")
            self.setProperty("PTV.Wikipedia.Date", "")
            self.setProperty("PTV.Knowledge.Source", "")
            
            self.showingWikipedia = False
            
        except Exception as e:
            self.log("Error stopping Knowledge Page: %s" % str(e))

    def showServerStatsOverlay(self, persistent=False):
        """Show the server stats overlay"""
        self.log("showServerStatsOverlay - STARTED")
        
        # Show server stats overlay
        self.showingServerStats = True
        self.setProperty("PTV.ServerStats", "true")
        
        # Also show weather in lower third
        self.showingWeather = True
        self.setProperty("PTV.Weather", "true")
        
        # Update weather info
        self.updateWeatherInfo()
        
        # Fetch server stats data
        try:
            self.updateServerStatsData()
        except Exception as e:
            self.log("showServerStatsOverlay - updateServerStatsData failed: " + str(e), xbmc.LOGERROR)
        
        # Start refresh timer (every 30 seconds)
        if self.serverStatsRefreshTimer and self.serverStatsRefreshTimer.isAlive():
            self.serverStatsRefreshTimer.cancel()
        
        self.serverStatsRefreshTimer = threading.Timer(30.0, self.refreshServerStats)
        self.serverStatsRefreshTimer.start()
        
        if not persistent:
            if (
                hasattr(self, "serverStatsTimer")
                and self.serverStatsTimer is not None
                and self.serverStatsTimer.isAlive()
            ):
                self.serverStatsTimer.cancel()
            
            self.serverStatsTimer = threading.Timer(120.0, self.hideServerStatsOverlay)
            self.serverStatsTimer.start()
        
        self.log("showServerStatsOverlay - COMPLETED")

    def hideServerStatsOverlay(self):
        """Hide the server stats overlay"""
        self.log("hideServerStatsOverlay")
        
        self.showingServerStats = False
        self.setProperty("PTV.ServerStats", "")
        
        # Cancel timers
        if hasattr(self, 'serverStatsTimer') and self.serverStatsTimer and self.serverStatsTimer.isAlive():
            self.serverStatsTimer.cancel()
            self.log("Cancelled serverStatsTimer")
        
        if hasattr(self, 'serverStatsRefreshTimer') and self.serverStatsRefreshTimer and self.serverStatsRefreshTimer.isAlive():
            self.serverStatsRefreshTimer.cancel()
            self.log("Cancelled serverStatsRefreshTimer")
        
        self.log("hideServerStatsOverlay return")

    # ADD THIS METHOD RIGHT HERE:
    def hideWikipediaOverlay(self):
        """Hide the Wikipedia overlay"""
        self.log("hideWikipediaOverlay")
        
        self.stopWikipediaPage()
        
        self.log("hideWikipediaOverlay return")

    def refreshServerStats(self):
        """Refresh server stats data periodically"""
        # CRITICAL: Check if we should still be refreshing
        if not self.showingServerStats or self.currentChannel != 99:
            self.log("refreshServerStats - stopping (showingServerStats=%s, channel=%d)" % (self.showingServerStats, self.currentChannel))
            return
        
        try:
            self.updateServerStatsData()
        except Exception as e:
            self.log("Error refreshing server stats: %s" % str(e), xbmc.LOGERROR)
        
        # Schedule next refresh ONLY if still on channel 99 and showing stats
        if self.showingServerStats and self.currentChannel == 99 and not self.isExiting:
            self.serverStatsRefreshTimer = threading.Timer(30.0, self.refreshServerStats)
            self.serverStatsRefreshTimer.start()
            self.log("refreshServerStats - scheduled next refresh")
        else:
            self.log("refreshServerStats - NOT scheduling next refresh")

    def getPageDuration(self, page):
        """Get the duration for each page in seconds"""
        if page == "calendar":
            return 25  # Calendar: 25 seconds
        elif page == "recentlyadded":
            return 25  # Recently Added: 25 seconds
        elif page == "recommendations":
            return 120  # Recommendations: 2 minutes
        elif page == "serverstats":
            return 25  # Server Stats: 25 seconds
        elif page == "mysqlstats":
            return 25  # MySQL Stats: 25 seconds
        elif page == "kodiboxstats":
            return 25  # Kodi Box Stats: 25 seconds
        elif page == "knowledge":
            return 120  # Knowledge Page: 2 minutes (source rotates each cycle)
        else:
            return 60  # Default fallback

    # ============================================================================
    # MYSQL STATS PAGE
    # ============================================================================
    
    def fetchMySQLStats(self):
        """Fetch stats from MySQL container via SSH"""
        self.log("fetchMySQLStats - STARTED")
        
        try:
            import subprocess
            import platform
            import os
            
            stats = {}
            
            # MySQL is on Kodi box, not Unraid - use separate settings
            MYSQL_SSH_HOST = "10.0.0.99"
            MYSQL_SSH_USER = "root"
            
            # Build SSH command prefix
            if platform.system() == "Windows":
                # On Windows, check for SSH in multiple locations
                possible_ssh_paths = [
                    "C:\\Windows\\System32\\OpenSSH\\ssh.exe",
                    "C:\\Program Files\\Git\\usr\\bin\\ssh.exe",
                    "ssh.exe"  # Try PATH
                ]
                ssh_executable = None
                for path in possible_ssh_paths:
                    if os.path.exists(path) or path == "ssh.exe":
                        ssh_executable = path
                        break
                
                if not ssh_executable:
                    self.log("SSH not found on Windows", xbmc.LOGERROR)
                    return {}
                
                # Windows SSH key path
                ssh_key = os.path.expanduser("~/.ssh/id_rsa")
            else:
                ssh_executable = "ssh"
                ssh_key = os.path.expanduser("~/.ssh/id_rsa")

            ssh_cmd = [
                ssh_executable,
                "-i", ssh_key,
                "-o", "StrictHostKeyChecking=no",
                "-o", "UserKnownHostsFile=/dev/null",
                "-o", "LogLevel=ERROR",
                "%s@%s" % (MYSQL_SSH_USER, MYSQL_SSH_HOST)
            ]
            
            # Run the MySQL health check script
            self.log("Fetching MySQL health stats...")
            result = subprocess.check_output(ssh_cmd + ["/bin/sh", "/storage/kodi-mysql-health.sh"])
            output = result
            
            # Parse the output
            self.log("Parsing MySQL output...")
            
            # Initialize stats
            container_status = "Unknown"
            uptime = ""
            cpu_usage = ""
            memory_usage = ""
            network_io = ""
            active_connections = "0"
            
            # Database sizes
            databases = []
            total_db_size = 0.0
            total_tables = 0
            
            # Library stats
            movies_count = "0"
            tvshows_count = "0"
            episodes_count = "0"
            files_count = "0"
            
            # Health status
            orphaned_episodes = 0
            orphaned_movies = 0
            orphaned_paths = 0
            table_integrity = "OK"
            connection_status = "OK"
            
            # Kodi clients
            kodi_clients = []
            
            # Parse output line by line
            lines = output.split('\n')
            current_section = ""
            
            for line in lines:
                line = line.strip()
                
                # Detect sections
                if '[1] Container Status' in line:
                    current_section = "container"
                elif '[2] Resource Usage' in line:
                    current_section = "resources"
                elif '[3] Database Sizes' in line:
                    current_section = "databases"
                elif '[4] Video Library Statistics' in line:
                    current_section = "library"
                elif '[5] Orphaned Entries' in line:
                    current_section = "orphaned"
                elif '[6] Table Integrity' in line:
                    current_section = "integrity"
                elif '[8] Active MySQL Connections' in line:
                    current_section = "connections"
                elif '[8.5] Connected Kodi Clients' in line:
                    current_section = "kodi_clients"
                
                # Parse container status
                if current_section == "container":
                    if 'Status:' in line and 'Running' in line:
                        container_status = "Running"
                    elif 'Uptime:' in line:
                        uptime = line.split('Uptime:')[1].strip()
                
                # Parse resource usage
                if current_section == "resources":
                    if 'CPU:' in line:
                        cpu_usage = line.split('CPU:')[1].strip()
                    elif 'Memory:' in line:
                        memory_usage = line.split('Memory:')[1].strip()
                    elif 'Network I/O:' in line:
                        network_io = line.split('Network I/O:')[1].strip()
                
                # Parse database sizes
                if current_section == "databases":
                    if 'MyVideos' in line or 'MyMusic' in line:
                        parts = line.split()
                        if len(parts) >= 3:
                            try:
                                db_name = parts[0]
                                db_size = float(parts[1])
                                db_tables = int(parts[2])
                                
                                databases.append({
                                    'name': db_name,
                                    'size': "%.2f MB" % db_size,
                                    'tables': db_tables
                                })
                                
                                total_db_size += db_size
                                total_tables += db_tables
                            except:
                                pass
                
                # Parse library statistics
                if current_section == "library":
                    if 'Movies' in line:
                        parts = line.split()
                        if len(parts) >= 2:
                            movies_count = parts[-1]
                    elif 'TV Shows' in line:
                        parts = line.split()
                        if len(parts) >= 2:
                            tvshows_count = parts[-1]
                    elif 'Episodes' in line:
                        parts = line.split()
                        if len(parts) >= 2:
                            episodes_count = parts[-1]
                    elif 'Files' in line and 'idFile' not in line:
                        parts = line.split()
                        if len(parts) >= 2:
                            files_count = parts[-1]
                
                # Parse orphaned entries
                if current_section == "orphaned":
                    if 'Episodes:' in line:
                        try:
                            orphaned_episodes = int(line.split(':')[1].strip())
                        except:
                            pass
                    elif 'Movies:' in line:
                        try:
                            orphaned_movies = int(line.split(':')[1].strip())
                        except:
                            pass
                    elif 'Paths:' in line:
                        try:
                            orphaned_paths = int(line.split(':')[1].strip())
                        except:
                            pass
                
                # Parse table integrity
                if current_section == "integrity":
                    if 'may have issues' in line:
                        table_integrity = "ISSUES"
                    elif 'are healthy' in line:
                        table_integrity = "OK"
                
                # Parse active connections
                if current_section == "connections":
                    if 'Active connections:' in line:
                        try:
                            active_connections = line.split(':')[1].strip()
                        except:
                            pass
                
                # Parse Kodi clients
                if current_section == "kodi_clients":
                    if 'Kodi' in line and ':' in line:
                        try:
                            parts = line.split(':')
                            client_name = parts[0].strip()
                            status = parts[1].strip()
                            
                            kodi_clients.append({
                                'name': client_name,
                                'status': status,
                                'online': 'Connected' in status
                            })
                        except:
                            pass
            
            # Calculate health status
            health_status = "Healthy"
            health_color = "green"
            orphaned_total = orphaned_episodes + orphaned_movies + orphaned_paths
            
            if orphaned_total > 0:
                health_status = "Needs Cleaning (%d orphaned)" % orphaned_total
                health_color = "yellow"
            
            if table_integrity != "OK":
                health_status = "Table Issues"
                health_color = "red"
            
            # Build stats dictionary
            stats = {
                'server_name': 'MYSQL-KODI',
                'container_status': container_status,
                'uptime': uptime,
                'cpu_usage': cpu_usage,
                'memory_usage': memory_usage,
                'network_io': network_io,
                'active_connections': active_connections,
                'databases': databases,
                'total_db_size': "%.2f MB" % total_db_size,
                'total_tables': str(total_tables),
                'movies_count': movies_count,
                'tvshows_count': tvshows_count,
                'episodes_count': episodes_count,
                'files_count': files_count,
                'health_status': health_status,
                'health_color': health_color,
                'orphaned_total': str(orphaned_total),
                'table_integrity': table_integrity,
                'kodi_clients': kodi_clients
            }
            
            self.log("fetchMySQLStats - SUCCESS: %s, %d databases, %d Kodi clients" % (container_status, len(databases), len(kodi_clients)))
            return stats
            
        except Exception as e:
            self.log("Error fetching MySQL stats: %s" % str(e), xbmc.LOGERROR)
            import traceback
            self.log("Traceback: %s" % traceback.format_exc(), xbmc.LOGERROR)
            return {}

    def updateMySQLStatsData(self):
        """Update MySQL stats data"""
        self.log("updateMySQLStatsData - STARTING")
        
        try:
            stats = self.fetchMySQLStats()
            
            if not stats:
                self.log("No MySQL stats returned")
                return
            
            self.mysqlStatsData = stats
            
            # Set properties for XML
            self.setProperty("PTV.MySQLStats.Name", stats.get('server_name', ''))
            self.setProperty("PTV.MySQLStats.Status", stats.get('container_status', ''))
            self.setProperty("PTV.MySQLStats.Uptime", stats.get('uptime', ''))
            self.setProperty("PTV.MySQLStats.CPUUsage", stats.get('cpu_usage', ''))
            self.setProperty("PTV.MySQLStats.MemoryUsage", stats.get('memory_usage', ''))
            self.setProperty("PTV.MySQLStats.NetworkIO", stats.get('network_io', ''))
            self.setProperty("PTV.MySQLStats.ActiveConnections", stats.get('active_connections', ''))
            
            # Database totals
            self.setProperty("PTV.MySQLStats.TotalSize", stats.get('total_db_size', ''))
            self.setProperty("PTV.MySQLStats.TotalTables", stats.get('total_tables', ''))
            
            # Individual databases
            databases = stats.get('databases', [])
            for i, db in enumerate(databases[:5], 1):  # Up to 5 databases
                self.setProperty("PTV.MySQLStats.DB.%d.Name" % i, db.get('name', ''))
                self.setProperty("PTV.MySQLStats.DB.%d.Size" % i, db.get('size', ''))
                self.setProperty("PTV.MySQLStats.DB.%d.Tables" % i, str(db.get('tables', '')))
            
            # Library stats
            self.setProperty("PTV.MySQLStats.Movies", stats.get('movies_count', ''))
            self.setProperty("PTV.MySQLStats.TVShows", stats.get('tvshows_count', ''))
            self.setProperty("PTV.MySQLStats.Episodes", stats.get('episodes_count', ''))
            self.setProperty("PTV.MySQLStats.Files", stats.get('files_count', ''))
            
            # Health status
            self.setProperty("PTV.MySQLStats.HealthStatus", stats.get('health_status', ''))
            self.setProperty("PTV.MySQLStats.HealthColor", stats.get('health_color', ''))
            self.setProperty("PTV.MySQLStats.OrphanedTotal", stats.get('orphaned_total', ''))
            self.setProperty("PTV.MySQLStats.TableIntegrity", stats.get('table_integrity', ''))
            
            # Kodi clients
            kodi_clients = stats.get('kodi_clients', [])
            for i, client in enumerate(kodi_clients[:5], 1):  # Up to 5 clients
                self.setProperty("PTV.MySQLStats.Client.%d.Name" % i, client.get('name', ''))
                self.setProperty("PTV.MySQLStats.Client.%d.Status" % i, client.get('status', ''))
                self.setProperty("PTV.MySQLStats.Client.%d.Online" % i, "true" if client.get('online', False) else "false")
            
            self.log("updateMySQLStatsData - COMPLETED")
            
        except Exception as e:
            self.log("Error in updateMySQLStatsData: %s" % str(e), xbmc.LOGERROR)

    def showMySQLStatsOverlay(self, persistent=False):
        """Show MySQL stats overlay - called by page rotation"""
        self.log("showMySQLStatsOverlay - STARTING")
        
        try:
            # Mark as showing
            self.showingMySQLStats = True
            
            # Start refresh timer
            self.startMySQLStatsRefresh()
            
            # Show overlay
            self.setProperty("PTV.MySQLStats", "true")
            
            self.log("showMySQLStatsOverlay - COMPLETED")
            
        except Exception as e:
            self.log("Error in showMySQLStatsOverlay: %s" % str(e), xbmc.LOGERROR)

    def hideMySQLStatsOverlay(self):
        """Hide MySQL stats overlay - called by page rotation"""
        self.log("hideMySQLStatsOverlay - STARTING")
        
        try:
            # Mark as not showing
            self.showingMySQLStats = False
            
            # Stop refresh timer
            self.stopMySQLStatsRefresh()
            
            # Hide overlay
            self.setProperty("PTV.MySQLStats", "")
            
            self.log("hideMySQLStatsOverlay - COMPLETED")
            
        except Exception as e:
            self.log("Error in hideMySQLStatsOverlay: %s" % str(e), xbmc.LOGERROR)

    def startMySQLStatsRefresh(self):
        """Start MySQL stats refresh timer"""
        self.log("startMySQLStatsRefresh - STARTING")
        
        try:
            # Cancel any existing timer
            if self.mysqlStatsRefreshTimer:
                self.mysqlStatsRefreshTimer.cancel()
            
            # Update data immediately
            self.updateMySQLStatsData()
            
            # Set up refresh timer (every 30 seconds)
            import threading
            self.mysqlStatsRefreshTimer = threading.Timer(30.0, self.startMySQLStatsRefresh)
            self.mysqlStatsRefreshTimer.start()
            
            self.log("startMySQLStatsRefresh - Timer started")
            
        except Exception as e:
            self.log("Error in startMySQLStatsRefresh: %s" % str(e), xbmc.LOGERROR)

    def stopMySQLStatsRefresh(self):
        """Stop MySQL stats refresh timer"""
        self.log("stopMySQLStatsRefresh - STARTING")
        
        try:
            if self.mysqlStatsRefreshTimer:
                self.mysqlStatsRefreshTimer.cancel()
                self.mysqlStatsRefreshTimer = None
            
            self.log("stopMySQLStatsRefresh - Timer stopped")
            
        except Exception as e:
            self.log("Error in stopMySQLStatsRefresh: %s" % str(e), xbmc.LOGERROR)

    # ============================================================
    # KODI BOX STATS METHODS (Page 7)
    # ============================================================

    def fetchKodiBoxStats(self):
        """Fetch system stats from Kodi box via SSH"""
        self.log("fetchKodiBoxStats - STARTED")
        
        try:
            import subprocess
            import platform
            import os
            import json
            
            # Kodi box SSH settings (same box as MySQL)
            KODI_BOX_SSH_HOST = "10.0.0.99"
            KODI_BOX_SSH_USER = "root"
            
            # Build SSH command prefix (same as MySQL method)
            if platform.system() == "Windows":
                possible_ssh_paths = [
                    "C:\\Windows\\System32\\OpenSSH\\ssh.exe",
                    "C:\\Program Files\\Git\\usr\\bin\\ssh.exe",
                    "ssh.exe"
                ]
                ssh_executable = None
                for path in possible_ssh_paths:
                    if os.path.exists(path) or path == "ssh.exe":
                        ssh_executable = path
                        break
                
                if not ssh_executable:
                    self.log("SSH not found on Windows", xbmc.LOGERROR)
                    return None
                
                ssh_key = os.path.expanduser("~/.ssh/id_rsa")
            else:
                ssh_executable = "ssh"
                ssh_key = os.path.expanduser("~/.ssh/id_rsa")

            ssh_cmd = [
                ssh_executable,
                "-i", ssh_key,
                "-o", "StrictHostKeyChecking=no",
                "-o", "UserKnownHostsFile=/dev/null",
                "-o", "LogLevel=ERROR",
                "%s@%s" % (KODI_BOX_SSH_USER, KODI_BOX_SSH_HOST)
            ]
            
            # Execute monitoring script
            self.log("Fetching Kodi box stats...")
            result = subprocess.check_output(ssh_cmd + ["/bin/sh", "/storage/kodi-box-monitor.sh"])
            output = result
            
            # Parse JSON output
            stats = json.loads(output)
            
            self.log("fetchKodiBoxStats - SUCCESS")
            return stats
            
        except Exception as e:
            self.log("Error fetching Kodi box stats: %s" % str(e), xbmc.LOGERROR)
            self.log("Traceback: %s" % traceback.format_exc(), xbmc.LOGERROR)
            return None

    def updateKodiBoxStats(self):
        """Update Kodi box stats data"""
        self.log("updateKodiBoxStats - STARTED")
        
        stats = self.fetchKodiBoxStats()
        
        if stats:
            self.kodiBoxStatsData = stats
            self.log("Kodi box stats updated successfully")
            
            # Always update the display when we have new stats
            self.displayKodiBoxStats()
        else:
            self.log("Failed to fetch Kodi box stats", xbmc.LOGERROR)

    def displayKodiBoxStats(self):
        """Display Kodi box stats on overlay"""
        if not self.kodiBoxStatsData:
            return
        
        stats = self.kodiBoxStatsData
        
        try:
            # Helper function to safely encode strings
            def safe_str(value):
                if isinstance(value, unicode):
                    return value.encode('utf-8')
                return str(value)
            
            # Left side - Main stats (user's custom order)
            # 9901 = Hostname
            self.getControl(9901).setLabel(safe_str(stats.get('hostname', 'UNKNOWN').upper()))
            
            # 9902 = Uptime
            self.getControl(9902).setLabel(safe_str("Uptime: %s" % stats.get('uptime', 'N/A')))
            
            # 9903 = CPU Temp
            cpu = stats.get('cpu', {})
            temp = cpu.get('temperature', 'N/A')
            self.getControl(9903).setLabel(safe_str("CPU Temp: %sC" % temp))
            
            # 9907 = Kodi Status (user has this in position 4)
            kodi = stats.get('kodi', {})
            kodi_status = kodi.get('status', 'Unknown')
            kodi_cpu = kodi.get('cpu_percent', '0')
            self.getControl(9907).setLabel(safe_str("Kodi: %s (%s%% CPU)" % (kodi_status, kodi_cpu)))
            
            # 9905 = Memory
            memory = stats.get('memory', {})
            mem_percent = memory.get('percent', 0)
            self.getControl(9905).setLabel(safe_str("Memory: %s%%" % mem_percent))
            
            # 9906 = Network
            network = stats.get('network', {})
            rx = network.get('rx_mb', '0')
            tx = network.get('tx_mb', '0')
            self.getControl(9906).setLabel(safe_str("Network: RX %sMB TX %sMB" % (rx, tx)))
            
            # Right side - System info
            # 9911 = LibreELEC
            self.getControl(9911).setLabel(safe_str("LibreELEC: %s" % stats.get('libreelec_version', 'N/A')))
            
            # 9912 = IP
            self.getControl(9912).setLabel(safe_str("IP: %s" % network.get('ip_address', 'N/A')))
            
            # 9913 = Root storage
            storage = stats.get('storage', {})
            root = storage.get('root', {})
            self.getControl(9913).setLabel(safe_str("Root: %s / %s (%s%%)" % (root.get('used', 'N/A'), root.get('total', 'N/A'), root.get('percent', 0))))
            
            # CPU Cores (9920-9927)
            core_usage = cpu.get('core_usage', [])
            for i, usage in enumerate(core_usage):
                if i < 8:  # Display up to 8 cores
                    control_id = 9920 + i
                    try:
                        self.getControl(control_id).setLabel(safe_str("Core %d: %s%%" % (i, usage)))
                    except:
                        pass
            
            self.log("Kodi box stats display updated")
            
        except Exception as e:
            self.log("Error displaying Kodi box stats: %s" % str(e), xbmc.LOGERROR)

    def showKodiBoxStatsOverlay(self):
        """Show Kodi box stats overlay"""
        try:
            self.log("showKodiBoxStatsOverlay - STARTED")
            
            # Update stats first
            self.updateKodiBoxStats()
            
            # Show the overlay using Window Property (like MySQL stats)
            self.setProperty("PTV.KodiBoxStats", "true")
            
            self.showingKodiBoxStats = True
            
            # Start refresh timer (refresh every 30 seconds)
            if self.kodiBoxStatsRefreshTimer:
                self.kodiBoxStatsRefreshTimer.cancel()
            
            self.kodiBoxStatsRefreshTimer = threading.Timer(30.0, self.refreshKodiBoxStats)
            self.kodiBoxStatsRefreshTimer.daemon = True
            self.kodiBoxStatsRefreshTimer.start()
            
            self.log("Kodi box stats overlay shown")
            
        except Exception as e:
            self.log("Error showing Kodi box stats overlay: %s" % str(e), xbmc.LOGERROR)

    def hideKodiBoxStatsOverlay(self):
        """Hide Kodi box stats overlay"""
        try:
            self.log("hideKodiBoxStatsOverlay - STARTED")
            
            # Hide the overlay using Window Property
            self.setProperty("PTV.KodiBoxStats", "false")
            
            self.showingKodiBoxStats = False
            
            # Cancel refresh timer
            if self.kodiBoxStatsRefreshTimer:
                self.kodiBoxStatsRefreshTimer.cancel()
                self.kodiBoxStatsRefreshTimer = None
            
            # Clear all properties
            self.setProperty("PTV.KodiBoxStats.Name", "")
            self.setProperty("PTV.KodiBoxStats.Uptime", "")
            self.setProperty("PTV.KodiBoxStats.LibreELECVersion", "")
            self.setProperty("PTV.KodiBoxStats.CPUModel", "")
            self.setProperty("PTV.KodiBoxStats.CPUTemp", "")
            self.setProperty("PTV.KodiBoxStats.CPUUsage", "")
            self.setProperty("PTV.KodiBoxStats.MemoryUsage", "")
            self.setProperty("PTV.KodiBoxStats.IPAddress", "")
            self.setProperty("PTV.KodiBoxStats.NetworkInterface", "")
            self.setProperty("PTV.KodiBoxStats.LinkSpeed", "")
            self.setProperty("PTV.KodiBoxStats.NetworkIO", "")
            self.setProperty("PTV.KodiBoxStats.RootUsage", "")
            self.setProperty("PTV.KodiBoxStats.StorageUsage", "")
            self.setProperty("PTV.KodiBoxStats.KodiStatus", "")
            self.setProperty("PTV.KodiBoxStats.KodiCPU", "")
            self.setProperty("PTV.KodiBoxStats.KodiMemory", "")
            self.setProperty("PTV.KodiBoxStats.KodiUptime", "")
            self.setProperty("PTV.KodiBoxStats.LoadAverage", "")
            for i in range(8):
                self.setProperty("PTV.KodiBoxStats.Core%d" % i, "")
            
            self.log("Kodi box stats overlay hidden")
            
        except Exception as e:
            self.log("Error hiding Kodi box stats overlay: %s" % str(e), xbmc.LOGERROR)

    def refreshKodiBoxStats(self):
        """Refresh Kodi box stats (called by timer)"""
        if self.showingKodiBoxStats:
            self.updateKodiBoxStats()
            
            # Schedule next refresh
            if self.kodiBoxStatsRefreshTimer:
                self.kodiBoxStatsRefreshTimer = threading.Timer(30.0, self.refreshKodiBoxStats)
                self.kodiBoxStatsRefreshTimer.daemon = True
                self.kodiBoxStatsRefreshTimer.start()


    def cycleChannel99Pages(self):
        """Cycle between calendar, recently added, recommendations, server stats, mysql stats, kodi box stats, and knowledge page on channel 99"""
        self.log("cycleChannel99Pages - Current page: %s" % self.channel99CurrentPage)
        
        # Only cycle if we're on channel 99
        if self.currentChannel != 99:
            self.log("Not on channel 99, stopping page cycling")
            return
        
        # Determine next page in cycle: calendar -> recentlyadded -> recommendations -> serverstats -> mysqlstats -> kodiboxstats -> knowledge -> calendar
        if self.channel99CurrentPage == "calendar":
            next_page = "recentlyadded"
        elif self.channel99CurrentPage == "recentlyadded":
            next_page = "recommendations"
        elif self.channel99CurrentPage == "recommendations":
            next_page = "serverstats"
        elif self.channel99CurrentPage == "serverstats":
            next_page = "mysqlstats"
        elif self.channel99CurrentPage == "mysqlstats":
            next_page = "kodiboxstats"
        elif self.channel99CurrentPage == "kodiboxstats":
            next_page = "knowledge"
        else:  # knowledge
            next_page = "calendar"
        
        self.log("Switching from %s to %s page" % (self.channel99CurrentPage, next_page))
        
        # Hide current page
        if self.channel99CurrentPage == "calendar":
            self.hideCalendarOverlay()
        elif self.channel99CurrentPage == "recentlyadded":
            self.hideRecentlyAddedOverlay()
        elif self.channel99CurrentPage == "recommendations":
            self.hideRecommendationsOverlay()
        elif self.channel99CurrentPage == "serverstats":
            self.hideServerStatsOverlay()
        elif self.channel99CurrentPage == "mysqlstats":
            self.hideMySQLStatsOverlay()
        elif self.channel99CurrentPage == "kodiboxstats":
            self.hideKodiBoxStatsOverlay()
        elif self.channel99CurrentPage == "knowledge":
            self.stopKnowledgePage()
        
        # Brief transition pause
        xbmc.sleep(300)  # 300ms pause for smooth transition
        
        # Show next page
        if next_page == "calendar":
            self.showCalendarOverlay(persistent=True)
        elif next_page == "recentlyadded":
            self.showRecentlyAddedOverlay(persistent=True)
        elif next_page == "recommendations":
            self.showRecommendationsOverlay(persistent=True)
        elif next_page == "serverstats":
            self.showServerStatsOverlay(persistent=True)
        elif next_page == "mysqlstats":
            self.showMySQLStatsOverlay(persistent=True)
        elif next_page == "kodiboxstats":
            self.showKodiBoxStatsOverlay()
        elif next_page == "knowledge":
            self.startKnowledgePage()
        
        # Update current page tracker
        self.channel99CurrentPage = next_page
        
        # Schedule next page switch with page-specific duration
        duration = self.getPageDuration(self.channel99CurrentPage)
        self.channel99PageTimer = threading.Timer(duration, self.cycleChannel99Pages)
        if not self.isExiting:
            self.channel99PageTimer.start()
            self.log("Next page switch scheduled in %d seconds" % duration)

    def startChannel99PageCycling(self):
        """Start the page cycling for channel 99"""
        self.log("startChannel99PageCycling")
        
        # Cancel any existing timer
        if hasattr(self, 'channel99PageTimer') and self.channel99PageTimer and self.channel99PageTimer.isAlive():
            self.channel99PageTimer.cancel()
        
        # Start with calendar page
        self.channel99CurrentPage = "calendar"
        self.showCalendarOverlay(persistent=True)
        
        # Schedule first page switch with page-specific duration
        duration = self.getPageDuration(self.channel99CurrentPage)
        self.channel99PageTimer = threading.Timer(duration, self.cycleChannel99Pages)
        self.channel99PageTimer.start()
        self.log("Channel 99 page cycling started - first switch in %d seconds" % duration)

    def stopChannel99PageCycling(self):
        """Stop the page cycling for channel 99"""
        self.log("stopChannel99PageCycling")
        
        # Cancel page cycle timer
        if hasattr(self, 'channel99PageTimer') and self.channel99PageTimer and self.channel99PageTimer.isAlive():
            self.channel99PageTimer.cancel()
            self.log("Channel 99 page timer cancelled")
        
        # Hide and cancel all overlays
        if hasattr(self, 'showingCalendar') and self.showingCalendar:
            self.log("Hiding calendar overlay")
            self.hideCalendarOverlay()
        
        if hasattr(self, 'showingRecentlyAdded') and self.showingRecentlyAdded:
            self.log("Hiding recently added overlay")
            self.hideRecentlyAddedOverlay()
        
        if hasattr(self, 'showingRecommendations') and self.showingRecommendations:
            self.log("Hiding recommendations overlay")
            self.hideRecommendationsOverlay()
        
        if hasattr(self, 'showingServerStats') and self.showingServerStats:
            self.log("Hiding server stats overlay")
            self.hideServerStatsOverlay()
        
        # Extra safety: Force cancel server stats timers even if overlay wasn't showing
        if hasattr(self, 'serverStatsTimer') and self.serverStatsTimer and self.serverStatsTimer.isAlive():
            self.serverStatsTimer.cancel()
            self.log("Force cancelled serverStatsTimer")
        
        if hasattr(self, 'serverStatsRefreshTimer') and self.serverStatsRefreshTimer and self.serverStatsRefreshTimer.isAlive():
            self.serverStatsRefreshTimer.cancel()
            self.log("Force cancelled serverStatsRefreshTimer")
        
        # ADD MYSQL STATS CLEANUP:
        if hasattr(self, 'showingMySQLStats') and self.showingMySQLStats:
            self.log("Hiding MySQL stats overlay")
            self.hideMySQLStatsOverlay()
        
        # Extra safety: Force cancel MySQL stats timers even if overlay wasn't showing
        if hasattr(self, 'mysqlStatsTimer') and self.mysqlStatsTimer and self.mysqlStatsTimer.isAlive():
            self.mysqlStatsTimer.cancel()
            self.log("Force cancelled mysqlStatsTimer")
        
        if hasattr(self, 'mysqlStatsRefreshTimer') and self.mysqlStatsRefreshTimer and self.mysqlStatsRefreshTimer.isAlive():
            self.mysqlStatsRefreshTimer.cancel()
            self.log("Force cancelled mysqlStatsRefreshTimer")
        
        # ADD KODI BOX STATS CLEANUP:
        if hasattr(self, 'showingKodiBoxStats') and self.showingKodiBoxStats:
            self.log("Hiding Kodi Box stats overlay")
            self.hideKodiBoxStatsOverlay()
        
        # Extra safety: Force cancel Kodi Box stats timers even if overlay wasn't showing
        if hasattr(self, 'kodiBoxStatsRefreshTimer') and self.kodiBoxStatsRefreshTimer and self.kodiBoxStatsRefreshTimer.isAlive():
            self.kodiBoxStatsRefreshTimer.cancel()
            self.log("Force cancelled kodiBoxStatsRefreshTimer")
        
        if hasattr(self, 'showingWikipedia') and self.showingWikipedia:
            self.log("Hiding knowledge page")
            self.stopKnowledgePage()

        self.log("Channel 99 page cycling stopped")

    def showComingUpOverlay(self, nextshow):
        """Show coming up overlay with landscape artwork"""
        self.log("showComingUpOverlay")

        # Get next show information from channel
        nextShowTitle = self.channels[self.currentChannel - 1].getItemTitle(nextshow)
        nextShowEpisode = self.channels[self.currentChannel - 1].getItemEpisodeTitle(
            nextshow
        )

        # ADD DEBUG LOGGING
        self.log(
            "showComingUpOverlay - Title: %s, Episode: %s"
            % (nextShowTitle, nextShowEpisode)
        )

        # Try to get the media path and extract artwork from it
        nextShowImage = ""
        try:
            # Get the file path of the next show
            mediaPath = self.channels[self.currentChannel - 1].getItemFilename(nextshow)
            self.log("showComingUpOverlay: mediaPath = " + str(mediaPath))

            # If it's a video file, navigate to the show's root folder
            if mediaPath and mediaPath.endswith(
                (".mkv", ".mp4", ".avi", ".mpg", ".mpeg", ".mov")
            ):
                # For TV shows: go up to the show folder (skip season folder)
                folderPath = os.path.dirname(mediaPath)  # Gets season folder
                showPath = os.path.dirname(folderPath)  # Gets show folder

                # Check if this looks like a TV show structure (has "Season" in the path)
                if "season" in folderPath.lower():
                    # It's a TV show - artwork should be in showPath
                    rootPath = showPath
                else:
                    # It's probably a movie - artwork should be in the same folder
                    rootPath = folderPath

                self.log("showComingUpOverlay: Looking for artwork in " + rootPath)

                # Look for artwork in the root folder
                artworkFiles = [
                    "landscape.jpg",
                    "landscape.png",
                    "fanart.jpg",
                    "fanart.png",
                    "banner.jpg",
                    "banner.png",
                ]

                for artFile in artworkFiles:
                    artPath = os.path.join(rootPath, artFile)
                    if FileAccess.exists(artPath):
                        nextShowImage = artPath
                        self.log("showComingUpOverlay: Found artwork at " + artPath)
                        break

        except Exception as e:
            self.log("showComingUpOverlay: Error getting show artwork - " + str(e))

        # If still no image, try to extract from Kodi database/library
        if not nextShowImage and nextShowTitle:
            try:
                # Use JSON-RPC to search for the show in the library
                json_query = {
                    "jsonrpc": "2.0",
                    "method": "VideoLibrary.GetTVShows",
                    "params": {
                        "filter": {
                            "field": "title",
                            "operator": "contains",
                            "value": nextShowTitle,
                        },
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
                        if "landscape" in show["art"]:
                            nextShowImage = show["art"]["landscape"]
                        elif "fanart" in show["art"]:
                            nextShowImage = show["art"]["fanart"]
                        elif "banner" in show["art"]:
                            nextShowImage = show["art"]["banner"]

            except Exception as e:
                self.log("showComingUpOverlay: Error searching library - " + str(e))

        # Fallback to channel artwork if no show artwork
        if not nextShowImage:
            self.log(
                "showComingUpOverlay: No show artwork found, using channel artwork"
            )
            channelName = self.channels[self.currentChannel - 1].name
            # Try channel landscape
            nextShowImage = self.channelLogos + ascii(channelName) + "_landscape.png"
            if not FileAccess.exists(nextShowImage):
                # Try channel logo
                nextShowImage = self.channelLogos + ascii(channelName) + ".png"
                if not FileAccess.exists(nextShowImage):
                    nextShowImage = ICON

        self.log("showComingUpOverlay: Final image = " + str(nextShowImage))

        # Set properties for the overlay
        self.setProperty("PTV.ComingUp", "true")
        self.setProperty("PTV.ComingUp.Title", nextShowTitle)
        self.setProperty("PTV.ComingUp.Episode", nextShowEpisode)
        self.setProperty("PTV.ComingUp.Image", nextShowImage)

        # ADD DEBUG TO VERIFY PROPERTIES ARE SET
        self.log("showComingUpOverlay - Properties set:")
        self.log(
            "  PTV.ComingUp = %s" % xbmcgui.Window(10000).getProperty("PTV.ComingUp")
        )
        self.log(
            "  PTV.ComingUp.Title = %s"
            % xbmcgui.Window(10000).getProperty("PTV.ComingUp.Title")
        )

        self.showingComingUp = True

        # Auto-hide after display time
        if (
            hasattr(self, "comingUpTimer")
            and self.comingUpTimer
            and self.comingUpTimer.isAlive()
        ):
            self.comingUpTimer.cancel()

        self.comingUpTimer = threading.Timer(
            NOTIFICATION_DISPLAY_TIME, self.hideComingUpOverlay
        )
        self.comingUpTimer.start()

    def hideComingUpOverlay(self):
        """Hide coming up overlay"""
        self.showingComingUp = False
        self.setProperty("PTV.ComingUp", "false")

        if hasattr(self, "comingUpTimer") and self.comingUpTimer.isAlive():
            self.comingUpTimer.cancel()

    def testOverlayVisibility(self):
        """Force test overlay visibility"""
        self.log("testOverlayVisibility - Starting")

        # Set the property
        self.setProperty("PTV.ComingUp", "true")
        self.setProperty("PTV.ComingUp.Title", "TEST OVERLAY VISIBILITY")
        self.setProperty("PTV.ComingUp.Image", ICON)

        # Log window IDs
        self.log("Current window ID: %s" % xbmcgui.getCurrentWindowId())
        self.log("Dialog window ID: %s" % xbmcgui.getCurrentWindowDialogId())

        # Check if property is actually set
        value = xbmcgui.Window(10000).getProperty("PTV.ComingUp")
        self.log('Property check - PTV.ComingUp = "%s"' % value)

        # Try setting on different window IDs
        xbmcgui.Window(10000).setProperty("PTV.ComingUp", "true")  # Home window
        xbmcgui.Window(xbmcgui.getCurrentWindowId()).setProperty(
            "PTV.ComingUp", "true"
        )  # Current window

        # Force a notification that we know works
        xbmc.executebuiltin(
            "Notification(Test, If you see this but not overlay - skin issue, 5000)"
        )

        # Keep it visible for 10 seconds
        xbmc.sleep(10000)

        # Clear
        self.setProperty("PTV.ComingUp", "false")
        self.log("testOverlayVisibility - Completed")

    def onAction(self, act):
        """Handle user input"""
        action = act.getId()
        self.log("onAction " + str(action))

        # MOVED TO TOP: Acquire semaphore FIRST before any other logic
        # Ignore actions if we're already processing one
        if self.actionSemaphore.acquire(False) == False:
            self.log("Unable to get semaphore")
            return

        # ADD THIS LINE TO TEST
        self.log("onAction: action id = %d, T key would be 84 or 116" % action)

        # Handle favorite show notification click
        if (
            hasattr(self, "pendingFavoriteShowChannel")
            and self.pendingFavoriteShowChannel > 0
        ):
            if action == ACTION_SELECT_ITEM:
                # Jump to the channel with the favorite show
                self.hideFavoriteShowNotification()
                self.background.setVisible(True)
                self.setChannel(self.pendingFavoriteShowChannel)
                self.background.setVisible(False)
                self.actionSemaphore.release()
                return
            elif action in ACTION_PREVIOUS_MENU:
                # Dismiss the notification
                self.hideFavoriteShowNotification()
                self.actionSemaphore.release()
                return

        if self.Player.stopped:
            self.actionSemaphore.release()
            return

        # Handle X button (ACTION_STOP) - check for preemption first
        if action == ACTION_STOP:
            if self.isPreempting:
                # If we're in preemption mode, return to scheduled programming
                self.returnToScheduledProgramming()
                self.actionSemaphore.release()
                return
            else:
                # Normal exit
                self.isExiting = True
                self.Player.ignoreNextStop = True

                # Stop the player first
                if self.Player and self.Player.isPlaying():
                    self.Player.stop()

                # Now end the overlay
                self.end()
                self.actionSemaphore.release()
                return

        # Handle weather overlay (but not on channel 99)
        if self.showingWeather and self.currentChannel != 99:
            if action in ACTION_PREVIOUS_MENU or action == ACTION_SELECT_ITEM:
                self.hideWeatherOverlay()
                self.actionSemaphore.release()
                return

        # Handle calendar overlay (but not on channel 99)
        if self.showingCalendar and self.currentChannel != 99:
            if action in ACTION_PREVIOUS_MENU or action == ACTION_SELECT_ITEM:
                self.hideCalendarOverlay()
                self.actionSemaphore.release()
                return

        # Handle recently added overlay (but not on channel 99)
        if self.showingRecentlyAdded and self.currentChannel != 99:
            if action in ACTION_PREVIOUS_MENU or action == ACTION_SELECT_ITEM:
                self.hideRecentlyAddedOverlay()
                self.actionSemaphore.release()
                return

        # Handle recommendations overlay (but not on channel 99)
        if self.showingRecommendations and self.currentChannel != 99:
            if action in ACTION_PREVIOUS_MENU or action == ACTION_SELECT_ITEM:
                self.hideRecommendationsOverlay()
                self.actionSemaphore.release()
                return

        # Handle server stats overlay (but not on channel 99)
        if self.showingServerStats and self.currentChannel != 99:
            if action in ACTION_PREVIOUS_MENU or action == ACTION_SELECT_ITEM:
                self.hideServerStatsOverlay()
                self.actionSemaphore.release()
                return

        # Handle MySQL stats overlay (but not on channel 99)
        if self.showingMySQLStats and self.currentChannel != 99:
            if action in ACTION_PREVIOUS_MENU or action == ACTION_SELECT_ITEM:
                self.hideMySQLStatsOverlay()
                self.actionSemaphore.release()
                return
        
        # Handle Kodi Box stats overlay (but not on channel 99)
        if self.showingKodiBoxStats and self.currentChannel != 99:
            if action in ACTION_PREVIOUS_MENU or action == ACTION_SELECT_ITEM:
                self.hideKodiBoxStatsOverlay()
                self.actionSemaphore.release()
                return
        
        lastaction = time.time() - self.lastActionTime

        # Ignore actions during channel changes
        if lastaction < 2:
            self.log("Not allowing actions")
            action = ACTION_INVALID

        self.startSleepTimer()

        if action == ACTION_SELECT_ITEM:
            self.handleSelectAction()
        elif action == ACTION_MOVE_UP or action == ACTION_PAGEUP:
            self.channelUp()
        elif action == ACTION_MOVE_DOWN or action == ACTION_PAGEDOWN:
            self.channelDown()
        elif action == ACTION_MOVE_LEFT:
            self.handleLeftAction()
        elif action == ACTION_MOVE_RIGHT:
            self.handleRightAction()
        elif action in ACTION_PREVIOUS_MENU:
            self.handleBackAction()
        elif action == ACTION_SHOW_INFO:
            self.handleInfoAction()
        elif action >= ACTION_NUMBER_0 and action <= ACTION_NUMBER_9:
            self.handleNumberAction(action)
        elif action == ACTION_OSD:
            xbmc.executebuiltin("ActivateWindow(videoosd)")
        # Disable fast forward action (F key)
        elif action == 77:  # ACTION_PLAYER_FORWARD (F key)
            icon = os.path.join(CWD, 'icon.png')
            xbmc.executebuiltin('Notification(Paragon TV, Cannot fast forward on live TV, 3000, %s)' % icon)
            self.log("Fast forward action (77) disabled - live TV mode")
        # Menu triggers
        elif action == 109:  # M key (moved from action 77 which conflicts with forward)
            self.showSidebar()
        elif action == 117:  # Context menu (C key)
            self.showSidebar()
        elif action == 83 or action == 115:  # S key
            self.showSidebar()
        elif action == 84 or action == 116:  # T key - ADD THIS
            self.testOverlayVisibility()

        self.actionSemaphore.release()
        self.log("onAction return")

    def onClick(self, controlId):
        """Handle button clicks"""
        self.log("onClick " + str(controlId))
        pass

    def handleSelectAction(self):
        """Handle select/enter key"""
        if self.inputChannel > 0:
            if (
                self.inputChannel != self.currentChannel
                and self.inputChannel <= self.maxChannels
            ):
                self.background.setVisible(True)
                self.setChannel(self.inputChannel)
                self.background.setVisible(False)
            self.inputChannel = -1
        else:
            # Show Info
            self.showInfo(10.0)

    def handleLeftAction(self):
        """Handle left arrow key"""
        if self.showingInfo:
            # Show sidebar instead of changing info offset
            self.showSidebar()
        else:
            xbmc.executebuiltin("Seek(" + str(self.seekBackward) + ")")

    def handleRightAction(self):
        """Handle right arrow key"""
        if self.showingInfo:
            self.infoOffset += 1
            self.showInfo(10.0)
        else:
            # Disabled for live TV experience - cannot skip forward on live TV
            icon = os.path.join(CWD, 'icon.png')
            xbmc.executebuiltin('Notification(Paragon TV, Cannot skip forward on live TV, 3000, %s)' % icon)
            self.log("Skip forward disabled - live TV mode")

    def handleBackAction(self):
        """Handle back/escape key"""
        if self.showingInfo:
            self.hideInfo()
        else:
            # Show background to hide video before showing dialog
            self.background.setVisible(True)

            dlg = xbmcgui.Dialog()
            if self.sleepTimeValue > 0:
                if self.sleepTimer.isAlive():
                    self.sleepTimer.cancel()
                    self.sleepTimer = threading.Timer(
                        self.sleepTimeValue, self.sleepAction
                    )

            if dlg.yesno(xbmc.getLocalizedString(13012), LANGUAGE(30031)):
                self.end()
                return
            else:
                # User chose not to exit, hide background and continue
                self.background.setVisible(False)
                self.startSleepTimer()

    def sleepAction(self):
        """Called when sleep timer expires"""
        self.log("sleepAction")
        self.actionSemaphore.acquire()
        self.end()

    def startNotificationTimer(self, timertime=NOTIFICATION_CHECK_TIME):
        """Start the notification timer"""
        self.log("startNotificationTimer")

        if self.notificationTimer.isAlive():
            self.notificationTimer.cancel()

        self.notificationTimer = threading.Timer(timertime, self.notificationAction)

        if self.Player.stopped == False:
            self.notificationTimer.name = "NotificationTimer"
            self.notificationTimer.start()

    def notificationAction(self):
        """Show coming up next notification"""
        self.log("notificationAction")

        if self.showNextItem == False:
            return

        if self.Player.isPlaying():
            # Check if we need to show notification
            docheck = False

            if self.notificationLastChannel != self.currentChannel:
                docheck = True
            elif (
                self.notificationLastShow
                != xbmc.PlayList(xbmc.PLAYLIST_MUSIC).getposition()
            ):
                docheck = True
            elif self.notificationShowedNotif == False:
                docheck = True

            if docheck == True:
                self.notificationLastChannel = self.currentChannel
                self.notificationLastShow = xbmc.PlayList(
                    xbmc.PLAYLIST_MUSIC
                ).getposition()
                self.notificationShowedNotif = False

                # Don't show for short items
                if self.hideShortItems:
                    if (
                        self.channels[self.currentChannel - 1].getItemDuration(
                            self.notificationLastShow
                        )
                        < self.shortItemLength
                    ):
                        self.notificationShowedNotif = True

                # Check if near end of show
                timedif = (
                    self.channels[self.currentChannel - 1].getItemDuration(
                        self.notificationLastShow
                    )
                    - self.Player.getTime()
                )

                if (
                    self.notificationShowedNotif == False
                    and timedif < NOTIFICATION_TIME_BEFORE_END
                    and timedif > NOTIFICATION_DISPLAY_TIME
                ):
                    # Find next show
                    nextshow = self.channels[self.currentChannel - 1].fixPlaylistIndex(
                        self.notificationLastShow + 1
                    )

                    if self.hideShortItems:
                        # Find next show >= short item length
                        while nextshow != self.notificationLastShow:
                            if (
                                self.channels[self.currentChannel - 1].getItemDuration(
                                    nextshow
                                )
                                >= self.shortItemLength
                            ):
                                break
                            nextshow = self.channels[
                                self.currentChannel - 1
                            ].fixPlaylistIndex(nextshow + 1)

                    # Show coming up overlay instead of notification
                    self.showComingUpOverlay(nextshow)
                    self.notificationShowedNotif = True

        self.startNotificationTimer()

    def playerTimerAction(self):
        """Monitor player status"""
        self.playerTimer = threading.Timer(2.0, self.playerTimerAction)

        if self.Player.isPlaying():
            self.lastPlayTime = int(self.Player.getTime())
            self.lastPlaylistPosition = xbmc.PlayList(xbmc.PLAYLIST_MUSIC).getposition()
            self.notPlayingCount = 0

            # Monitor playback speed to prevent fast forward (live TV mode)
            try:
                # Get active player ID
                result = xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Player.GetActivePlayers","id":1}')
                result_dict = json.loads(result)

                if 'result' in result_dict and len(result_dict['result']) > 0:
                    player_id = result_dict['result'][0]['playerid']

                    # Get player speed
                    speed_query = '{"jsonrpc":"2.0","method":"Player.GetProperties","params":{"playerid":%d,"properties":["speed"]},"id":1}' % player_id
                    speed_result = xbmc.executeJSONRPC(speed_query)
                    speed_dict = json.loads(speed_result)

                    if 'result' in speed_dict and 'speed' in speed_dict['result']:
                        current_speed = speed_dict['result']['speed']

                        # If speed is greater than normal (fast forward), reset it
                        if current_speed > 1:
                            self.log("Detected fast forward playback speed: %d - resetting to normal" % current_speed)

                            # Reset speed to normal
                            reset_query = '{"jsonrpc":"2.0","method":"Player.SetSpeed","params":{"playerid":%d,"speed":1},"id":1}' % player_id
                            xbmc.executeJSONRPC(reset_query)

                            # Show notification
                            icon = os.path.join(CWD, 'icon.png')
                            xbmc.executebuiltin('Notification(Paragon TV, Cannot fast forward on live TV, 3000, %s)' % icon)
            except Exception as e:
                self.log("Error monitoring playback speed: " + str(e))
        else:
            self.notPlayingCount += 1
            self.log("Adding to notPlayingCount")

        if self.notPlayingCount >= 3:
            self.end()
            return

        if self.Player.stopped == False:
            self.playerTimer.name = "PlayerTimer"
            self.playerTimer.start()

    def resetChannelTimes(self):
        """Reset channel access times"""
        for i in range(self.maxChannels):
            self.channels[i].setAccessTime(
                self.timeStarted - self.channels[i].totalTimePlayed
            )

    def backupFiles(self):
        """Backup channel files for sharing"""
        self.log("backupFiles")

        if CHANNEL_SHARING == False:
            return

        realloc = ADDON.getSetting("SettingsFolder")
        FileAccess.copy(realloc + "/settings2.xml", SETTINGS_LOC + "/settings2.xml")
        realloc = translatePath(os.path.join(realloc, "cache")) + "/"

        for i in range(1000):
            FileAccess.copy(
                realloc + "channel_" + str(i) + ".m3u",
                CHANNELS_LOC + "channel_" + str(i) + ".m3u",
            )

    def storeFiles(self):
        """Store channel files for sharing"""
        self.log("storeFiles")

        if CHANNEL_SHARING == False:
            return

        realloc = ADDON.getSetting("SettingsFolder")
        FileAccess.copy(SETTINGS_LOC + "/settings2.xml", realloc + "/settings2.xml")
        realloc = translatePath(os.path.join(realloc, "cache")) + "/"

        for i in range(self.maxChannels + 1):
            FileAccess.copy(
                CHANNELS_LOC + "channel_" + str(i) + ".m3u",
                realloc + "channel_" + str(i) + ".m3u",
            )

    def runActions(self, action, channel, parameter):
        """Run channel rules"""
        self.log("runActions " + str(action) + " on channel " + str(channel))

        if channel < 1:
            return

        self.runningActionChannel = channel
        index = 0

        for rule in self.channels[channel - 1].ruleList:
            if rule.actions & action > 0:
                self.runningActionId = index
                parameter = rule.runAction(action, self, parameter)

            index += 1

        self.runningActionChannel = 0
        self.runningActionId = 0
        return parameter

    def message(self, data):
        """Show a dialog message"""
        self.log("Dialog message: " + data)
        dlg = xbmcgui.Dialog()
        dlg.ok(xbmc.getLocalizedString(19033), data)
        del dlg

    def log(self, msg, level=xbmc.LOGDEBUG):
        """Log a message"""
        log("TVOverlay: " + msg, level)

    def setProperty(self, key, value):
        """Set a window property"""
        xbmcgui.Window(10000).setProperty(key, value)

    def onFocus(self, controlId):
        pass

    def Error(self, line1, line2="", line3=""):
        """Handle fatal errors"""
        self.log("FATAL ERROR: " + line1 + " " + line2 + " " + line3, xbmc.LOGFATAL)
        dlg = xbmcgui.Dialog()
        # Kodi 19+ API change: dialog.ok() only accepts 2 arguments
        lines = [line1]
        if line2:
            lines.append(line2)
        if line3:
            lines.append(line3)
        dlg.ok(xbmc.getLocalizedString(257), "\n".join(lines))
        del dlg
        self.end()

    def showExitImage(self):
        """Display exit image during shutdown"""
        try:
            # Path to exit image
            exitImagePath = os.path.join(ADDON_PATH, "resources", "skins", "default", "media", "exit.png")

            # Check if custom exit image exists, otherwise use logo
            if not xbmcvfs.exists(exitImagePath):
                exitImagePath = os.path.join(ADDON_PATH, "resources", "skins", "default", "media", "ptv_logo.png")

            # Set window property to show exit image in skin
            self.setProperty("PTV.ExitImage", exitImagePath)
            self.setProperty("PTV.ShowExitImage", "true")

            self.log("Exit image displayed: " + exitImagePath)
        except Exception as e:
            self.log("Error displaying exit image: " + str(e), xbmc.LOGERROR)

    def end(self):
        """Cleanup and exit"""
        self.log("end")
        # Set exit flag first
        self.isExiting = True
        # CRITICAL: Force hide all overlays IMMEDIATELY before any other cleanup
        self.log("end - Forcing overlay cleanup")
        try:
            # Stop channel 99 page cycling first
            if hasattr(self, 'channel99PageTimer') and self.channel99PageTimer and self.channel99PageTimer.isAlive():
                self.channel99PageTimer.cancel()
                self.log("end - Cancelled channel 99 page timer")
            
            # Clear channel 99 visualization property on exit
            xbmcgui.Window(10000).clearProperty("PTV.Channel99")
            self.log("end - Cleared channel 99 visualization property")

            
            # Force hide all overlays
            if hasattr(self, 'showingCalendar') and self.showingCalendar:
                self.log("end - Hiding calendar overlay")
                self.showingCalendar = False
                self.setProperty("PTV.Calendar", "false")
            
            if hasattr(self, 'showingRecentlyAdded') and self.showingRecentlyAdded:
                self.log("end - Hiding recently added overlay")
                self.showingRecentlyAdded = False
                self.setProperty("PTV.RecentlyAdded", "false")
            
            if hasattr(self, 'showingRecommendations') and self.showingRecommendations:
                self.log("end - Hiding recommendations overlay")
                self.showingRecommendations = False
                self.setProperty("PTV.Recommendations", "false")
            
            if hasattr(self, 'showingServerStats') and self.showingServerStats:
                self.log("end - Hiding server stats overlay")
                self.showingServerStats = False
                self.setProperty("PTV.ServerStats", "false")
            
            # ADD THIS BLOCK:
            if hasattr(self, 'showingMySQLStats') and self.showingMySQLStats:
                self.log("end - Hiding MySQL stats overlay")
                self.showingMySQLStats = False
                self.setProperty("PTV.MySQLStats", "false")
                
            if hasattr(self, 'showingKodiBoxStats') and self.showingKodiBoxStats:
                self.log("end - Hiding Kodi Box stats overlay")
                self.showingKodiBoxStats = False
                self.setProperty("PTV.KodiBoxStats", "false")        
            
            if hasattr(self, 'showingWikipedia') and self.showingWikipedia:
                self.log("end - Hiding wikipedia overlay")
                self.showingWikipedia = False
                self.setProperty("PTV.ShowWikipedia", "false")
            
            if hasattr(self, 'showingWeather') and self.showingWeather:
                self.log("end - Hiding weather overlay")
                self.showingWeather = False
                self.setProperty("PTV.Weather", "false")
                       
            # Clear ALL overlay-related window properties to ensure clean state
            self.setProperty("PTV.Calendar", "false")
            self.setProperty("PTV.RecentlyAdded", "false")
            self.setProperty("PTV.Recommendations", "false")
            self.setProperty("PTV.ServerStats", "false")
            self.setProperty("PTV.MySQLStats", "false")
            self.setProperty("PTV.KodiBoxStats", "false")  # ADD THIS LINE
            self.setProperty("PTV.ShowWikipedia", "false")
            self.setProperty("PTV.Weather", "false")
            self.setProperty("PTV.ComingUp", "false")
            self.setProperty("PTV.FavoriteShow", "false")
            self.setProperty("PTV.ChannelNumber", "")
            
            # Clear calendar properties
            self.setProperty("PTV.Calendar.Today.Title", "")
            self.setProperty("PTV.Calendar.Today.Episode", "")
            self.setProperty("PTV.Calendar.Today.Status", "")
            self.setProperty("PTV.Calendar.Today.Poster", "")
            for i in range(1, 11):
                self.setProperty("PTV.Calendar.Week.%d" % i, "")
                self.setProperty("PTV.Calendar.Week.%d.InLibrary" % i, "false")
            
            # Clear recently added properties
            self.setProperty("PTV.Recent.Featured.Title", "")
            self.setProperty("PTV.Recent.Featured.Subtitle", "")
            self.setProperty("PTV.Recent.Featured.EpisodeTitle", "")
            self.setProperty("PTV.Recent.Featured.Poster", "")
            self.setProperty("PTV.Recent.Featured.DateAdded", "")
            self.setProperty("PTV.Recent.Featured.Watched", "false")
            for i in range(1, 6):
                self.setProperty("PTV.Recent.List.%d" % i, "")
                self.setProperty("PTV.Recent.List.%d.Watched" % i, "false")
            
            # Clear recommendations properties
            self.setProperty("PTV.Recommendations", "false")
            self.setProperty("PTV.Recommendations.Featured.Title", "")
            self.setProperty("PTV.Recommendations.Featured.Subtitle", "")
            self.setProperty("PTV.Recommendations.Featured.EpisodeTitle", "")
            self.setProperty("PTV.Recommendations.Featured.Poster", "")
            self.setProperty("PTV.Recommendations.Featured.Genre", "")
            for i in range(1, 6):
                self.setProperty("PTV.Recommendations.Genre.%d" % i, "")
                self.setProperty("PTV.Recommendations.Genre.%d.Artwork" % i, "")
            
            # Clear server stats properties
            self.setProperty("PTV.ServerStats", "false")
            self.setProperty("PTV.ServerStats.Name", "")
            self.setProperty("PTV.ServerStats.Uptime", "")
            self.setProperty("PTV.ServerStats.CPUTemp", "")
            self.setProperty("PTV.ServerStats.CPUUsage", "")
            self.setProperty("PTV.ServerStats.RAMUsage", "")
            self.setProperty("PTV.ServerStats.LoadAvg", "")
            self.setProperty("PTV.ServerStats.Array.Total", "")
            self.setProperty("PTV.ServerStats.Array.Used", "")
            self.setProperty("PTV.ServerStats.Array.Percent", "")
            for i in range(1, 6):
                self.setProperty("PTV.ServerStats.Disk.%d.Name" % i, "")
                self.setProperty("PTV.ServerStats.Disk.%d.Used" % i, "")
                self.setProperty("PTV.ServerStats.Disk.%d.Total" % i, "")
                self.setProperty("PTV.ServerStats.Disk.%d.Percent" % i, "")
            self.setProperty("PTV.ServerStats.Cache.Total", "")
            self.setProperty("PTV.ServerStats.Cache.Used", "")
            self.setProperty("PTV.ServerStats.Cache.Percent", "")
            self.setProperty("PTV.ServerStats.Cache.Temp", "")
            
            # ADD THIS ENTIRE BLOCK - Clear MySQL stats properties:
            self.setProperty("PTV.MySQLStats", "false")
            self.setProperty("PTV.MySQLStats.Name", "")
            self.setProperty("PTV.MySQLStats.Status", "")
            self.setProperty("PTV.MySQLStats.Uptime", "")
            self.setProperty("PTV.MySQLStats.CPUUsage", "")
            self.setProperty("PTV.MySQLStats.MemoryUsage", "")
            self.setProperty("PTV.MySQLStats.NetworkIO", "")
            self.setProperty("PTV.MySQLStats.ActiveConnections", "")
            self.setProperty("PTV.MySQLStats.TotalSize", "")
            self.setProperty("PTV.MySQLStats.TotalTables", "")
            for i in range(1, 6):
                self.setProperty("PTV.MySQLStats.DB.%d.Name" % i, "")
                self.setProperty("PTV.MySQLStats.DB.%d.Size" % i, "")
                self.setProperty("PTV.MySQLStats.DB.%d.Tables" % i, "")
            self.setProperty("PTV.MySQLStats.Movies", "")
            self.setProperty("PTV.MySQLStats.TVShows", "")
            self.setProperty("PTV.MySQLStats.Episodes", "")
            self.setProperty("PTV.MySQLStats.Files", "")
            self.setProperty("PTV.MySQLStats.HealthStatus", "")
            self.setProperty("PTV.MySQLStats.HealthColor", "")
            self.setProperty("PTV.MySQLStats.OrphanedTotal", "")
            self.setProperty("PTV.MySQLStats.TableIntegrity", "")
            
            # ADD THIS ENTIRE BLOCK - Clear Kodi Box stats properties:
            self.setProperty("PTV.KodiBoxStats", "false")
            self.setProperty("PTV.KodiBoxStats.Name", "")
            self.setProperty("PTV.KodiBoxStats.Uptime", "")
            self.setProperty("PTV.KodiBoxStats.LibreELECVersion", "")
            self.setProperty("PTV.KodiBoxStats.CPUModel", "")
            self.setProperty("PTV.KodiBoxStats.CPUTemp", "")
            self.setProperty("PTV.KodiBoxStats.CPUUsage", "")
            self.setProperty("PTV.KodiBoxStats.MemoryUsage", "")
            self.setProperty("PTV.KodiBoxStats.IPAddress", "")
            self.setProperty("PTV.KodiBoxStats.NetworkInterface", "")
            self.setProperty("PTV.KodiBoxStats.LinkSpeed", "")
            self.setProperty("PTV.KodiBoxStats.NetworkIO", "")
            self.setProperty("PTV.KodiBoxStats.RootUsage", "")
            self.setProperty("PTV.KodiBoxStats.StorageUsage", "")
            self.setProperty("PTV.KodiBoxStats.KodiStatus", "")
            self.setProperty("PTV.KodiBoxStats.KodiCPU", "")
            self.setProperty("PTV.KodiBoxStats.KodiMemory", "")
            self.setProperty("PTV.KodiBoxStats.KodiUptime", "")
            self.setProperty("PTV.KodiBoxStats.LoadAverage", "")
            for i in range(8):
                self.setProperty("PTV.KodiBoxStats.Core%d" % i, "")
            
            # Clear Wikipedia properties:
            self.setProperty("PTV.ShowWikipedia", "false")
            self.setProperty("PTV.Wikipedia.Title", "")
            self.setProperty("PTV.Wikipedia.Image", "")
            self.setProperty("PTV.Wikipedia.Text", "")
            self.setProperty("PTV.Wikipedia.WordCount", "")
            self.setProperty("PTV.Wikipedia.Categories", "")
            self.setProperty("PTV.Wikipedia.Date", "")
            
            # Clear weather properties
            self.setProperty("PTV.Weather.Location", "")
            self.setProperty("PTV.Weather.Temperature", "")
            self.setProperty("PTV.Weather.Conditions", "")
            self.setProperty("PTV.Weather.CurrentIcon", "")
            for i in range(5):
                self.setProperty("PTV.Weather.Hour%d.Time" % i, "")
                self.setProperty("PTV.Weather.Hour%d.Temp" % i, "")
                self.setProperty("PTV.Weather.Hour%d.Icon" % i, "")
            
            self.log("end - Overlay cleanup complete")
        except Exception as e:
            self.log("end - Error during overlay cleanup: " + str(e), xbmc.LOGERROR)
            import traceback
            self.log("end - Traceback: " + traceback.format_exc(), xbmc.LOGERROR)

        # Show busy dialog while shutting down
        xbmc.executebuiltin("ActivateWindow(busydialog)")

        # Display exit image
        self.showExitImage()

        # Clear player reference to prevent callbacks
        if self.Player:
            self.Player.overlay = None
            self.Player.ignoreNextStop = True

        # Save favorites and speed dial BEFORE any other cleanup
        try:
            self.saveFavorites()
            self.saveSpeedDial()  # This now saves to both JSON and settings
        except Exception as e:
            self.log("Error saving favorites/speed dial: " + str(e))

        # Prevent the player from setting the sleep timer
        self.Player.stopped = True

        # Stop the player FIRST before hiding UI (unless browsing library)
        try:
            if self.Player.isPlaying() and not getattr(self, "browsingLibrary", False):
                self.lastPlayTime = self.Player.getTime()
                self.lastPlaylistPosition = xbmc.PlayList(
                    xbmc.PLAYLIST_MUSIC
                ).getposition()
                self.Player.stop()
        except:
            pass

        curtime = time.time()
        xbmc.executebuiltin("PlayerControl(RepeatOff)")

        # Hide the background
        try:
            self.background.setVisible(False)
        except:
            pass

        updateDialog = xbmcgui.DialogProgressBG()
        updateDialog.create(ADDON_NAME, "")

        # Clean up file locks
        if self.isMaster and CHANNEL_SHARING == True:
            updateDialog.update(1, message="Exiting - Removing File Locks")
            GlobalFileLock.unlockFile("MasterLock")

        GlobalFileLock.close()

        # Stop all timers
        updateDialog.update(2, message="Exiting - Stopping Threads")
        timers = [
            self.playerTimer,
            self.channelLabelTimer,
            self.notificationTimer,
            self.infoTimer,
            self.weatherTimer,
            self.weatherRefreshTimer,
            self.calendarRotationTimer,
            self.calendarRefreshTimer,
            self.epgScanTimer,
            self.favoriteShowTimer,
            self.recentlyAddedRotationTimer,
            self.recentlyAddedRefreshTimer,
            self.recommendationsRotationTimer,
            self.recommendationsRefreshTimer,
            self.channel99PageTimer,
            self.serverStatsRefreshTimer,
            self.mysqlStatsRefreshTimer,
            self.kodiBoxStatsRefreshTimer,   # ADD THIS LINE
        ]
        for i, timer in enumerate(timers):
            updateDialog.update(2 + i, message="Exiting - Stopping Threads")
            try:
                if timer and timer.isAlive():
                    timer.cancel()
                    # Don't join() here as it can cause deadlocks
            except:
                pass

        # Handle sleep timer
        try:
            if self.sleepTimeValue > 0:
                if self.sleepTimer and self.sleepTimer.isAlive():
                    self.sleepTimer.cancel()
        except:
            pass

        # Stop channel thread
        updateDialog.update(7, message="Exiting - Stopping Channel Thread")
        if self.channelThread.isAlive():
            try:
                self.channelThread.stop()  # If the thread has a stop method
            except:
                pass

            # Give it a moment to stop gracefully
            xbmc.sleep(500)

        # Save settings
        if self.isMaster:
            try:
                ADDON.setSetting("CurrentChannel", str(self.currentChannel))
            except:
                pass

            ADDON_SETTINGS.setSetting("LastExitTime", str(int(curtime)))

        # Save channel times
        if self.timeStarted > 0 and self.isMaster:
            updateDialog.update(40, message="Exiting - Saving Settings")
            validcount = 0

            for i in range(self.maxChannels):
                if self.channels[i].isValid:
                    validcount += 1

            if validcount > 0:
                incval = 60.0 / float(validcount)

                for i in range(self.maxChannels):
                    updateDialog.update(40 + int((incval * i)))

                    if self.channels[i].isValid:
                        if self.channels[i].mode & MODE_RESUME == 0:
                            ADDON_SETTINGS.setSetting(
                                "Channel_" + str(i + 1) + "_time",
                                str(
                                    int(
                                        curtime
                                        - self.timeStarted
                                        + self.channels[i].totalTimePlayed
                                    )
                                ),
                            )
                        else:
                            if i == self.currentChannel - 1:
                                # Calculate playlist time
                                pltime = 0
                                for pos in range(self.lastPlaylistPosition):
                                    pltime += self.channels[i].getItemDuration(pos)

                                ADDON_SETTINGS.setSetting(
                                    "Channel_" + str(i + 1) + "_time",
                                    str(pltime + self.lastPlayTime),
                                )
                            else:
                                # Calculate total time
                                tottime = 0
                                for j in range(self.channels[i].playlistPosition):
                                    tottime += self.channels[i].getItemDuration(j)

                                tottime += self.channels[i].showTimeOffset
                                ADDON_SETTINGS.setSetting(
                                    "Channel_" + str(i + 1) + "_time", str(int(tottime))
                                )

                self.storeFiles()

        updateDialog.close()

        # Clear the playlist
        try:
            xbmc.PlayList(xbmc.PLAYLIST_MUSIC).clear()
        except:
            pass
        # Final property cleanup before closing window
        try:
            self.log("end - Final property cleanup")
            self.setProperty("PTV.Calendar", "false")
            self.setProperty("PTV.RecentlyAdded", "false")
            self.setProperty("PTV.Recommendations", "false")
            self.setProperty("PTV.ServerStats", "false")
            self.setProperty("PTV.MySQLStats", "false")
            self.setProperty("PTV.KodiBoxStats", "false")  # ADD THIS LINE
            self.setProperty("PTV.Weather", "false")
            self.setProperty("PTV.ShowExitImage", "false")
            self.setProperty("PTV.ExitImage", "")
        except:
            pass
        # Close the window last
        self.log("end - closing window")
        self.close()

    def handleInfoAction(self):
        """Handle info key"""
        if self.ignoreInfoAction:
            self.ignoreInfoAction = False
        else:
            if self.showingInfo:
                self.hideInfo()
                if xbmc.getCondVisibility("Player.ShowInfo"):
                    json_query = '{"jsonrpc": "2.0", "method": "Input.Info", "id": 1}'
                    self.ignoreInfoAction = True
                    self.channelList.sendJSON(json_query)
            else:
                self.showInfo(10.0)

    def handleNumberAction(self, action):
        """Handle number input with speed dial support"""
        num = action - ACTION_NUMBER_0

        # Check for speed dial first (only for single digit, no input channel)
        if self.inputChannel < 0 and num >= 1 and num <= 9:
            if num in self.speedDialChannels:
                # Speed dial exists - jump to channel with delay
                speedChannel = self.speedDialChannels[num]
                if (
                    speedChannel <= self.maxChannels
                    and self.channels[speedChannel - 1].isValid
                ):
                    self.log(
                        "Speed Dial: Jumping to channel %d via key %d"
                        % (speedChannel, num)
                    )
                    xbmc.executebuiltin(
                        "Notification(Speed Dial %d, Channel %d, 1000, %s)"
                        % (num, speedChannel, ICON)
                    )
                    # Direct channel change like the original
                    self.background.setVisible(True)
                    self.setChannel(speedChannel)
                    self.background.setVisible(False)
                    return

        # Normal number input for channel selection
        if self.inputChannel < 0:
            self.inputChannel = num
        else:
            if self.inputChannel < 100:
                self.inputChannel = self.inputChannel * 10 + num

        self.showChannelLabel(self.inputChannel)

    def showEPG(self):
        """Show the EPG window"""
        if self.channelThread.isAlive():
            self.channelThread.pause()

        if self.notificationTimer.isAlive():
            self.notificationTimer.cancel()
            self.notificationTimer = threading.Timer(
                NOTIFICATION_CHECK_TIME, self.notificationAction
            )

        if self.sleepTimeValue > 0:
            if self.sleepTimer.isAlive():
                self.sleepTimer.cancel()
                self.sleepTimer = threading.Timer(self.sleepTimeValue, self.sleepAction)

        self.hideInfo()
        self.getControl(103).setVisible(False)
        self.newChannel = 0
        self.myEPG.doModal()
        self.getControl(103).setVisible(True)

        if self.channelThread.isAlive():
            self.channelThread.unpause()

        self.startNotificationTimer()

        if self.newChannel != 0:
            self.background.setVisible(True)
            self.setChannel(self.newChannel)
            self.background.setVisible(False)

    def channelUp(self):
        """Go to next channel"""
        self.log("channelUp")
        if self.maxChannels == 1:
            return

        self.background.setVisible(True)
        channel = self.fixChannel(self.currentChannel + 1)
        self.setChannel(channel)
        self.background.setVisible(False)
        self.log("channelUp return")

    def channelDown(self):
        """Go to previous channel"""
        self.log("channelDown")
        if self.maxChannels == 1:
            return

        self.background.setVisible(True)
        channel = self.fixChannel(self.currentChannel - 1, False)
        self.setChannel(channel)
        self.background.setVisible(False)
        self.log("channelDown return")

    def fixChannel(self, channel, increasing=True):
        """Return a valid channel number"""
        while channel < 1 or channel > self.maxChannels:
            if channel < 1:
                channel = self.maxChannels + channel
            if channel > self.maxChannels:
                channel -= self.maxChannels

        if increasing:
            direction = 1
        else:
            direction = -1

        if self.channels[channel - 1].isValid == False:
            return self.fixChannel(channel + direction, increasing)

        return channel

    def InvalidateChannel(self, channel):
        """Mark a channel as invalid"""
        self.log("InvalidateChannel" + str(channel))

        if channel < 1 or channel > self.maxChannels:
            self.log("InvalidateChannel invalid channel " + str(channel))
            return

        self.channels[channel - 1].isValid = False
        self.invalidatedChannelCount += 1

        if self.invalidatedChannelCount > 3:
            self.Error(LANGUAGE(30039))
            return

        remaining = 0
        for i in range(self.maxChannels):
            if self.channels[i].isValid:
                remaining += 1

        if remaining == 0:
            self.Error(LANGUAGE(30040))
            return

        self.setChannel(self.fixChannel(channel))

    def waitForVideoPaused(self):
        """Wait for video to pause"""
        self.log("waitForVideoPaused")
        sleeptime = 0

        while sleeptime < TIMEOUT:
            xbmc.sleep(100)

            if self.Player.isPlaying():
                if xbmc.getCondVisibility("Player.Paused"):
                    break

            sleeptime += 100
        else:
            self.log("Timeout waiting for pause", xbmc.LOGERROR)
            return False

        self.log("waitForVideoPaused return")
        return True

    def startSleepTimer(self):
        """Start or reset the sleep timer"""
        if self.sleepTimeValue == 0:
            return

        if self.sleepTimer and self.sleepTimer.isAlive():
            self.sleepTimer.cancel()

        self.sleepTimer = threading.Timer(self.sleepTimeValue, self.sleepAction)