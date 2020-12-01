####Full Name: Haoyang Zeng
####Unique Name: haoyangz

from bs4 import BeautifulSoup
from pathlib import Path
import requests
import os
import json
import sqlite3
import plotly.graph_objs as go

base_url = "https://nierautomata.wiki.fextralife.com/"
NPC_url = base_url + "NPCs"
location_url = base_url + "Locations"
main_quest_url = base_url + "Main+Story+Quests"
side_quest_url = base_url + "Side+Quests"
fish_url = base_url + "Fishing"
CACHE_FILENAME = "NieR_Project_Cache.json"
DBNAME = "NieR.sqlite"

none_list = ["??", "N/A", "nothing", "none", "", " "]


class NPC:
    def __init__(self, url, name, info, gender, img_name):
        self.name = name
        self.url = url
        self.info = info
        self.gender = gender
        self.img_name = img_name

    def __str__(self):
        return f"{self.name}: {self.img_name}"
        #return f"{self.name} ({self.gender}): {self.info}"

class Location:
    def __init__(self, url, name, info, previous_location, next_location):
        self.url = url
        self.name = name
        self.info = info
        self.previous_location = previous_location
        self.next_location = next_location

    def __str__(self):
        return f"{self.name}(previous: {self.previous_location}, next: {self.next_location}): {self.info}"

class Quest:
    def __init__(self, url, name, giver, location, reward, category):
        self.url = url
        self.name = name
        self.giver = giver
        self.location = location
        self.reward = reward
        self.category = category

    def __str__(self):
        return f"{self.name} is a {self.category} quest given by {self.giver} in {self.location}. Reward: {self.reward}"

class Fish:
    def __init__(self, url, name, location, img_name, price):
        self.url = url
        self.name = name
        self.location = location
        self.img_name = img_name
        self.price = price

    def __str__(self):
        #return f"{self.name}({self.price}) can be found at: " + ", ".join(self.location)
        return f"{self.name}({self.price}) can be found at: {self.location}"

def open_cache():
    ''' Opens the cache file if it exists and loads the JSON into
    the CACHE_DICT dictionary.
    if the cache file doesn't exist, creates a new cache dictionary
    
    Parameters
    ----------
    None
    
    Returns
    -------
    The opened cache: dict
    '''
    try:
        cache_file = open(CACHE_FILENAME, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict


def save_cache(cache_dict):
    ''' Saves the current state of the cache to disk
    
    Parameters
    ----------
    cache_dict: dict
        The dictionary to save
    
    Returns
    -------
    None
    '''
    dumped_json_cache = json.dumps(cache_dict)
    fw = open(CACHE_FILENAME,"w")
    fw.write(dumped_json_cache)
    fw.close()  


def cache_or_fetch(url):

    cache_dict = open_cache()
    if url in cache_dict.keys():
        #print("Using Cache")
        soup = BeautifulSoup(cache_dict[url], "html.parser")
    else:
        #print("Fetching")
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        cache_dict[url] = response.text
        save_cache(cache_dict)

    return soup


def get_NPCs():

    soup = cache_or_fetch(NPC_url)
    content = soup.find("div", id = "wiki-content-block")
    rows = content.find_all("div", class_ = "row")
    NPC_url_dict = {}
    NPC_img_dict = {}
    NPC_list = []
    path = Path("img_cache")
    path.mkdir(parents = True, exist_ok = True)

    for row in rows:
        columns = row.find_all("div", class_ = "col-sm-4")
        for column in columns:
            img_url = base_url + column.find("img")["src"]
            img_name = img_url.split('/')[-1]
            if not (path / img_name).exists():
                response = requests.get(img_url)
                (path / img_name).open("wb").write(response.content)

            character = column.find("h3", style = "text-align: center;").find("a")
            href = character["href"]
            name = character.text.strip()
            NPC_url_dict[name] = base_url + href
            NPC_img_dict[name] = img_name

    for name, url in NPC_url_dict.items():
        soup = cache_or_fetch(url)
        table_info = soup.find("table", class_ = "wiki_table")
        if "Male" in table_info.text:
            gender = "Male"
        elif "Female" in table_info.text:
            gender = "Female"
        else:
            gender = None

        info = soup.find("div", id = "wiki-content-block").find("p").text.strip()

        NPC_list.append(NPC(url, name, info, gender, NPC_img_dict[name]))
    
    #for npc in NPC_list:
    #    print(npc)
    return NPC_list
    

def get_locations():
    
    soup = cache_or_fetch(location_url)
    content = soup.find("div", id = "wiki-content-block")
    rows = content.find_all("div", class_ = "row")
    location_url_dict = {}
    location_list = []

    for row in rows:
        columns = row.find_all("div", class_ = "col-sm-4")
        for column in columns:
            location = column.find("h3", style = "text-align: center;").find("a")
            href = location["href"]
            name = location.text.strip()
            if name == "Battle Arena (DLC)":
                name = "Battle Arena"
            if href == "/Battle+Arena+(DLC)":
                href = "/Battle+Arena"
            location_url_dict[name] = base_url + href

    for name, url in location_url_dict.items():
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        info = soup.find("div", id = "wiki-content-block").find("p").text.strip()

        table = soup.find("div", class_ = "col-sm-4 col-md-3 col-md-push-9")
        previous_location = table.find_all("li")[0].text.split(":")[-1].strip()
        if previous_location.lower() in none_list:
            previous_location = None
        
        next_location = table.find_all("li")[1].text.split(":")[-1].strip()
        if next_location.lower() in none_list:
            next_location = None

        if name == "Bunker":
            name = "The Bunker"

        location_list.append(Location(url, name, info, previous_location, next_location))

    #for l in location_list:
    #    print(l)
    return location_list


def get_main_quests():

    soup = cache_or_fetch(main_quest_url)
    tables = soup.find_all("table", class_ = "wiki_table")
    main_quest_list = []
    
    for table in tables[0:2]:
        rows = table.find("tbody").find_all("tr")
        for row in rows:
            columns = row.find_all("td")
            name = columns[0].text.strip()
            url = base_url + columns[0].find("a")["href"]
            giver = columns[1].text.strip()
            if giver in none_list or giver == "Default":
                giver = None
            if giver == "Command":
                giver = "Commander"
            location = columns[2].text.strip()
            if location == "Resistance Camp Inbox":
                location = "Resistance Camp"
            reward = columns[3].text.strip()
            if reward in none_list:
                reward = None
            main_quest_list.append(Quest(url, name, giver, location, reward, "main"))
    
    rows = tables[2].find("tbody").find_all("tr")
    for row in rows:
        columns = row.find_all("td")
        name = columns[0].text.strip()
        url = base_url + columns[0].find("a")["href"]
        giver = None
        location = columns[1].text.strip()
        reward = None
        main_quest_list.append(Quest(url, name, giver, location, reward, "main"))

    #for q in main_quest_list:
    #    print(q)
    return main_quest_list


def get_side_quests():

    soup = cache_or_fetch(side_quest_url)
    rows = soup.find("table", class_ = "wiki_table sortable").find("tbody").find_all("tr")
    side_quest_list = []

    for row in rows:
        columns = row.find_all("td")
        name = columns[0].text.strip()
        url = base_url + columns[0].find("a")["href"]
        giver = columns[1].text.split(":")[1].strip()
        if giver == "Jean-Paul":
            giver = "Sartre"
        location = columns[1].text.split(":")[0].strip()
        if location == "City Ruins (Forest Camp)":
            location = "City Ruins"
        reward = columns[2].text.strip().replace("\n", ", ")
        if reward in none_list:
            reward = None
        side_quest_list.append(Quest(url, name, giver, location, reward, "side"))

    #for q in side_quest_list:
    #    print(q)
    return side_quest_list


def get_fishes():

    soup = cache_or_fetch(fish_url)
    fish_list = []
    path = Path("img_cache")
    path.mkdir(parents = True, exist_ok = True)
    
    rows = soup.find("table", class_ = "wiki_table").find("tbody").find_all("tr")

    for row in rows:
        columns = row.find_all("td")

        img_url = base_url + columns[0].find("img")["src"]
        img_name = img_url.split('/')[-1]
        if not (path / img_name).exists():
            response = requests.get(img_url)
            (path / img_name).open("wb").write(response.content)
        
        name = columns[0].find_all("a")[-1].text.strip()
        url = base_url + columns[0].find("a")["href"]
        price = columns[1].find_all("p")[-1].text.strip()
        location = columns[2].text.strip().replace("\n", ", ")
        
        fish_list.append(Fish(url, name, location, img_name, price))

    #for f in fish_list:
    #    print(f)
    return fish_list

def convert_to_binary(filename):
    with open(filename, 'rb') as file:
        blob_data = file.read()
    return blob_data

def create_tables():

    connection = sqlite3.connect(DBNAME)
    cursor = connection.cursor()

    create_NPC = '''CREATE TABLE IF NOT EXISTS NPCs (Id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE, 
    Name TEXT NOT NULL UNIQUE, Url TEXT UNIQUE, Info TEXT, Gender TEXT, Image BLOB)'''
    cursor.execute(create_NPC)

    create_location = '''CREATE TABLE IF NOT EXISTS Locations (Id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE, 
    Name TEXT NOT NULL UNIQUE, Url TEXT UNIQUE, Info TEXT, PreviousLocation TEXT, NextLocation TEXT)'''
    cursor.execute(create_location)

    create_quest = '''CREATE TABLE IF NOT EXISTS Quests (Id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE, 
    Name TEXT NOT NULL UNIQUE, Url TEXT UNIQUE, Giver TEXT, Location INTEGER, Reward TEXT, Category TEXT,
    FOREIGN KEY(Location) REFERENCES Locations(Id))'''
    cursor.execute(create_quest)

    create_fish = '''CREATE TABLE IF NOT EXISTS Fishes (Id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE, 
    Name TEXT NOT NULL UNIQUE, Url TEXT UNIQUE, Location TEXT, Price TEXT, Image BLOB)'''
    cursor.execute(create_fish)

    create_fishing_location = '''CREATE TABLE IF NOT EXISTS FishingLocation (Fish INTEGER, Location INTEGER,
    FOREIGN KEY(Fish) REFERENCES Fishes(Id), FOREIGN KEY(Location) REFERENCES Locations(Id))'''
    cursor.execute(create_fishing_location)

    connection.commit()
    connection.close()

def insert_data():

    NPC_list = get_NPCs()
    location_list = get_locations()
    quest_list = get_main_quests() + get_side_quests()
    fish_list = get_fishes()
    connection = sqlite3.connect(DBNAME)
    cursor = connection.cursor()
    path = Path("img_cache")
    location_id_dict = {}
    fish_id_dict = {}

    insert = "INSERT OR IGNORE INTO NPCs ('Name', 'Url', 'Info', 'Gender', 'Image') VALUES(?, ?, ?, ?, ?)"
    for NPC in NPC_list:
        url = NPC.url
        name = NPC.name
        info = NPC.info
        gender = NPC.gender
        image = convert_to_binary((path / NPC.img_name))
        data_tuple = (name, url, info, gender, image)
        cursor.execute(insert, data_tuple)

    insert = "INSERT OR IGNORE INTO Locations ('Name', 'Url', 'Info', 'PreviousLocation', 'NextLocation') VALUES(?, ?, ?, ?, ?)"
    for location in location_list:
        url = location.url
        name = location.name
        info = location.info
        previous_location = location.previous_location
        next_location = location.next_location
        data_tuple = (name, url, info, previous_location, next_location)
        cursor.execute(insert, data_tuple)

    query = "SELECT Id, Name FROM Locations"
    result = cursor.execute(query).fetchall()
    for r in result:
        location_id_dict[r[1]] = r[0]
    
    insert = "INSERT OR IGNORE INTO Quests ('Name', 'Url', 'Giver', 'Location', 'Reward', 'Category') VALUES(?, ?, ?, ?, ?, ?)"
    for quest in quest_list:
        name = quest.name
        url = quest.url
        giver = quest.giver
        reward = quest.reward
        category = quest.category
        for key, value in location_id_dict.items():
            if quest.location == key:
                location = value
        data_tuple = (name, url, giver, location, reward, category)
        cursor.execute(insert, data_tuple)

    insert = "INSERT OR IGNORE INTO Fishes ('Name', 'Url', 'Location', 'Price', 'Image') VALUES(?, ?, ?, ?, ?)"
    for fish in fish_list:
        name = fish.name
        url = fish.url
        price = fish.price
        location = fish.location
        image = convert_to_binary((path / fish.img_name))
        data_tuple = (name, url, location, price, image)
        cursor.execute(insert, data_tuple)

    query = "SELECT Id, Name FROM Fishes"
    result = cursor.execute(query).fetchall()
    for r in result:
        fish_id_dict[r[1]] = r[0]

    insert = "INSERT OR IGNORE INTO FishingLocation ('Fish', 'Location') VALUES(?, ?)"
    for fish in fish_list:
        for location in location_list:
            if location.name in fish.location:
                data_tuple = (fish_id_dict[fish.name], location_id_dict[location.name])
                cursor.execute(insert, data_tuple)

    connection.commit()
    connection.close()

if __name__ == "__main__":
    create_tables()
    insert_data()
