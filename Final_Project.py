####Full Name: Haoyang Zeng
####Unique Name: haoyangz

from bs4 import BeautifulSoup
from pathlib import Path
import requests
import json
import sqlite3
import plotly.graph_objs as go
import base64

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
        return f"{self.name} ({self.gender}): {self.info}"

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
    '''Decide whether to use crawler or cache. Use the crawler only if the url is not in cache.
        
    Parameters
    ----------
    url: str
        The url to be parsed by BS.
    
    Returns
    -------
    soup: str
        The parsed result of the url.
    '''
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
    '''Parse all NPC information
        
    Parameters
    ----------
    None
    
    Returns
    -------
    NPC_list: list
        A list of NPC instances.
    '''
    soup = cache_or_fetch(NPC_url)
    content = soup.find("div", id = "wiki-content-block")
    rows = content.find_all("div", class_ = "row")
    NPC_url_dict = {}
    NPC_img_dict = {}
    NPC_list = []
    p = Path("img_cache")
    p.mkdir(parents = True, exist_ok = True)

    for row in rows:
        columns = row.find_all("div", class_ = "col-sm-4")
        for column in columns:
            img_url = base_url + column.find("img")["src"]
            img_name = img_url.split('/')[-1]
            if not (p / img_name).exists():
                response = requests.get(img_url)
                (p / img_name).open("wb").write(response.content)

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

        info = soup.find("div", id = "wiki-content-block").find("p").text.strip().replace(u'\xa0', u' ')

        NPC_list.append(NPC(url, name, info, gender, NPC_img_dict[name]))
    
    #for npc in NPC_list:
    #    print(npc)
    return NPC_list
    

def get_locations():
    '''Parse all location information
        
    Parameters
    ----------
    None
    
    Returns
    -------
    location_list: list
        A list of location instances.
    '''
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

        info = soup.find("div", id = "wiki-content-block").find("p").text.strip().replace(u'\xa0', u' ')

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
    '''Parse all main quest information
        
    Parameters
    ----------
    None
    
    Returns
    -------
    main_quest_list: list
        A list of quest instances whose category is set to "main".
    '''
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
            reward = columns[3].text.strip().replace(u'\xa0', u' ')
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
    '''Parse all main quest information
        
    Parameters
    ----------
    None
    
    Returns
    -------
    side_quest_list: list
        A list of quest instances whose category is set to "side".
    '''
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
        if giver == "Operator 60":
            giver = "Operator 6O"
        if giver == "Operator 210":
            giver = "Operator 21O"
        if giver == "High-speed Machine":
            giver = "High-Speed Machine"
        if giver == "Devola" or giver == "Popola":
            giver = "Devola & Popola"
        location = columns[1].text.split(":")[0].strip()
        if location == "City Ruins (Forest Camp)":
            location = "City Ruins"
        reward = columns[2].text.strip().replace("\n", ", ").replace(u'\xa0', u' ')
        if reward in none_list:
            reward = None
        side_quest_list.append(Quest(url, name, giver, location, reward, "side"))

    #for q in side_quest_list:
    #    print(q)
    return side_quest_list


def get_fishes():
    '''Parse all fish information
        
    Parameters
    ----------
    None
    
    Returns
    -------
    fish_list: list
        A list of fish instances.
    '''
    soup = cache_or_fetch(fish_url)
    fish_list = []
    p = Path("img_cache")
    p.mkdir(parents = True, exist_ok = True)
    
    rows = soup.find("table", class_ = "wiki_table").find("tbody").find_all("tr")

    for row in rows:
        columns = row.find_all("td")

        img_url = base_url + columns[0].find("img")["src"]
        img_name = img_url.split('/')[-1]
        if not (p / img_name).exists():
            response = requests.get(img_url)
            (p / img_name).open("wb").write(response.content)
        
        name = columns[0].find_all("a")[-1].text.strip()
        url = base_url + columns[0].find("a")["href"]
        price = columns[1].find_all("p")[-1].text.strip()
        price = int(price.strip("G").replace(",", ""))
        location = columns[2].text.strip().replace("\n", ", ").replace(u'\xa0', u' ')
        
        fish_list.append(Fish(url, name, location, img_name, price))

    #for f in fish_list:
    #    print(f)
    return fish_list


def convert_to_binary(filename):
    '''Convert jpg image to binary in order to store in database.
        
    Parameters
    ----------
    filename: str
        The path of the image file to be converted.
    
    Returns
    -------
    blob_data: str
        The binary string of the image.
    '''
    with open(filename, 'rb') as file:
        blob_data = file.read()
    return blob_data


def create_tables():
    '''Create all database tables.
        
    Parameters
    ----------
    None
    
    Returns
    -------
    None
    '''
    connection = sqlite3.connect(DBNAME)
    cursor = connection.cursor()

    create_NPC = '''CREATE TABLE IF NOT EXISTS NPCs (Id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE, 
    Name TEXT NOT NULL UNIQUE COLLATE NOCASE, Url TEXT UNIQUE, Info TEXT, Gender TEXT, Image BLOB)'''
    cursor.execute(create_NPC)

    create_location = '''CREATE TABLE IF NOT EXISTS Locations (Id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE, 
    Name TEXT NOT NULL UNIQUE COLLATE NOCASE, Url TEXT UNIQUE COLLATE NOCASE, Info TEXT, PreviousLocation TEXT, NextLocation TEXT)'''
    cursor.execute(create_location)

    create_quest = '''CREATE TABLE IF NOT EXISTS Quests (Id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE, 
    Name TEXT NOT NULL UNIQUE COLLATE NOCASE, Url TEXT UNIQUE, Giver TEXT COLLATE NOCASE, Location INTEGER, Reward TEXT COLLATE NOCASE, Category TEXT,
    FOREIGN KEY(Location) REFERENCES Locations(Id))'''
    cursor.execute(create_quest)

    create_fish = '''CREATE TABLE IF NOT EXISTS Fishes (Id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE, 
    Name TEXT NOT NULL UNIQUE COLLATE NOCASE, Url TEXT UNIQUE, Location TEXT COLLATE NOCASE, Price INTEGER, Image BLOB)'''
    cursor.execute(create_fish)

    create_fishing_location = '''CREATE TABLE IF NOT EXISTS FishingLocation (Fish INTEGER, Location INTEGER,
    FOREIGN KEY(Fish) REFERENCES Fishes(Id), FOREIGN KEY(Location) REFERENCES Locations(Id))'''
    cursor.execute(create_fishing_location)

    connection.commit()
    connection.close()


def insert_data():
    '''Insert all database data.
        
    Parameters
    ----------
    None
    
    Returns
    -------
    None
    '''
    NPC_list = get_NPCs()
    location_list = get_locations()
    quest_list = get_main_quests() + get_side_quests()
    fish_list = get_fishes()
    connection = sqlite3.connect(DBNAME)
    cursor = connection.cursor()
    p = Path("img_cache")
    location_id_dict = {}
    fish_id_dict = {}

    insert = "INSERT OR IGNORE INTO NPCs ('Name', 'Url', 'Info', 'Gender', 'Image') VALUES(?, ?, ?, ?, ?)"
    for NPC in NPC_list:
        url = NPC.url
        name = NPC.name
        info = NPC.info
        gender = NPC.gender
        image = convert_to_binary((p / NPC.img_name))
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
        image = convert_to_binary((p / fish.img_name))
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


def make_tables(header_data, cell_data):
    '''Use table to display chosen query data.
        
    Parameters
    ----------
    header_data: list
        The list of table header.
    cell_data: list of lists
        The list all data columns. Each data column has a list.
    
    Returns
    -------
    None
    '''
    fig = go.Figure(data=[go.Table(header = dict(
            values = header_data, #['A Scores', 'B Scores'],
            line_color = 'darkslategray',
            fill_color = 'lightskyblue',
            align = 'center'),
        cells = dict(
            values = cell_data, #[[100, 90, 80, 90], [95, 85, 75, 95]],
            line_color = 'darkslategray',
            fill_color = 'lightcyan',
            align='center'))])
    fig.show()
    

def bar_chart(xvals, yvals):
    '''Generate and display a barchart of the given data in the browser.
    The length of X and Y values should be identical.

    Parameters
    ----------
    xvals: list
        The X-values of the chart
    yvals: list
        The Y-values of the chart
    
    Returns
    -------
    None
    '''
    bar_data = go.Bar(x = xvals, y = yvals)
    basic_layout = go.Layout()
    fig = go.Figure(data = bar_data, layout = basic_layout)
    fig.show()


def show_image(binary_strings):
    '''Use Plotly to display the chosen images.
        
    Parameters
    ----------
    binary_strings: list
        The list of all binary strings of the chosen images.
    
    Returns
    -------
    None
    '''
    prefix = "data:image/jpg;base64,"
    for img in binary_strings:
        img = prefix + base64.b64encode(img).decode("utf-8")
        fig = go.Figure(go.Image(source = img))
        fig.update_xaxes(showticklabels = False)
        fig.update_yaxes(showticklabels = False)
        fig.show()


def run_queries(query, para = None):
    '''Run SQL query specified by the parameter 'query'.
    
    Parameters
    ----------
    query: string
        The query string for SQL.
    
    Returns
    -------
    result: list
        The search result as a list of tuples.
    '''
    connection = sqlite3.connect(DBNAME)
    cursor = connection.cursor()
    if para is not None:
        result = cursor.execute(query, para).fetchall()
    else:
        result = cursor.execute(query).fetchall()
    return result


def NPC_prompt():
    '''The prompt for NPC query.
    
    Parameters
    ----------
    None
    
    Returns
    -------
    None
    '''
    while True:
        response = input("Select your filter on NPCs (all, with main quest, with side quest, name) or go back: ").lower().strip()
        query = "SELECT DISTINCT NPCs.Name, NPCs.Info, NPCs.Gender FROM NPCs "

        if response == "all":
            result = run_queries(query)
            return result

        elif response == "with main quest":
            query += "JOIN Quests ON Quests.Giver = NPCs.Name WHERE Quests.Category = 'main'"
            result = run_queries(query)
            return result

        elif response == "with side quest":
            query += "JOIN Quests ON Quests.Giver = NPCs.Name WHERE Quests.Category = 'side'"
            result = run_queries(query)
            return result

        elif response == "name":
            name = ("%" + input("Please enter the name of the NPC: ").strip() + "%", )
            query += "WHERE NPCs.Name LIKE ?"
            result = run_queries(query, name)
            return result

        elif response == "back":
            print("Back")
            break

        else:
            print("Invalid input please try again.")


def location_prompt():
    '''The prompt for location query.
    
    Parameters
    ----------
    None
    
    Returns
    -------
    None
    '''
    while True:
        response = input("Select your filter on locations (all, quest, fish, name) or go back: ").lower().strip()
        query = "SELECT DISTINCT Locations.Name, Locations.Info FROM Locations "

        if response == "all":
            result = run_queries(query)
            return result

        elif response == "quest":
            name = (input("Please enter the quest whose location you want to search (please enter the exact name for uniqueness): ").strip(), )
            query += "JOIN Quests ON Quests.Location = Locations.Id WHERE Quests.Name = ?"
            result = run_queries(query, name)
            return result

        elif response == "fish":
            name = (input("Please enter the fish whose location you want to search (please enter the exact name for uniqueness): ").strip(), )
            query += "JOIN FishingLocation ON Locations.Id = FishingLocation.Location JOIN Fishes ON FishingLocation.Fish = Fishes.Id WHERE Fishes.Name = ?"
            result = run_queries(query, name)
            return result

        elif response == "name":
            name = ("%" + input("Please enter the name of the location: ").strip() + "%", )
            query += "WHERE Locations.Name LIKE ?"
            result = run_queries(query, name)
            return result

        elif response == "back":
            print("Back")
            break

        else:
            print("Invalid input please try again.")


def quest_prompt():
    '''The prompt for quest query.
    
    Parameters
    ----------
    None
    
    Returns
    -------
    None
    '''
    while True:
        response = input("Select your filter on quests (all, giver, location, reward, category, name) or go back: ").lower().strip()
        query = "SELECT Quests.Name, Quests.Giver, Locations.Name, Quests.Reward, Quests.Category FROM Quests, Locations WHERE Quests.Location = Locations.Id "

        if response == "all":
            result = run_queries(query)
            return result

        elif response == "giver":
            name = ("%" + input("Please enter the giver of the quest or 'no giver': ").strip() + "%", )
            if name == ("%no giver%", ):
                query += "AND Quests.Giver IS NULL"
                result = run_queries(query)
            else:
                query += "AND Quests.Giver LIKE ?"
                result = run_queries(query, name)
            return result

        elif response == "location":
            name = ("%" + input("Please enter the location of the quest: ").strip() + "%", )
            query += "AND Locations.Name LIKE ?"
            result = run_queries(query, name)
            return result

        elif response == "reward":
            name = ("%" + input("Please enter the reward of the quest or 'no reward': ").strip() + "%", )
            if name == ("%no reward%", ):
                query += "AND Quests.Reward IS NULL"
                result = run_queries(query)
            else:
                query += "AND Quests.Reward LIKE ?"
                result = run_queries(query, name)
            return result

        elif response == "category":
            name = (input("Please enter the category of the quest (main or side): ").strip(), )
            query += "AND Quests.Category = ?"
            result = run_queries(query, name)
            return result

        elif response == "name":
            name = ("%" + input("Please enter the name of the quest: ").strip() + "%", )
            query += "AND Quests.Name LIKE ?"
            result = run_queries(query, name)
            return result

        elif response == "back":
            print("Back")
            break

        else:
            print("Invalid input please try again.")


def fish_prompt():
    '''The prompt for fish query.
    
    Parameters
    ----------
    None
    
    Returns
    -------
    None
    '''
    while True:
        response = input("Select your filter on Fishes (all, location, price, name) or go back: ").lower().strip()
        query = "SELECT Fishes.Name, Fishes.Location, Fishes.Price FROM Fishes "

        if response == "all":
            result = run_queries(query)
            return result

        elif response == "location":
            name = ("%" + input("Please enter the location of the fish: ").strip() + "%", )
            query += "WHERE Fishes.Location LIKE ?"
            result = run_queries(query, name)
            return result
        
        elif response == "price":
            query += "WHERE Fishes.Price >= ?"
            while True:
                price = input("Please enter the price of the fish (an integer) or go back: ").strip()
                if price == "back":
                    print("Back")
                    break
                else:
                    try:
                        price = (int(float(price)), )
                        result = run_queries(query, price)
                        print(len(result))
                        return result
                    except:
                        print("Invalid input please try again.")
        
        elif response == "name":
            name = ("%" + input("Please enter the name of the fish: ").strip() + "%", )
            query += "WHERE Fishes.Name LIKE ?"
            result = run_queries(query, name)
            return result

        elif response == "back":
            print("Back")
            break

        else:
            print("Invalid input please try again.")


def stats_prompt():
    '''The prompt for stats query.
    
    Parameters
    ----------
    None
    
    Returns
    -------
    None
    '''
    while True:
        print("1. Location -  Number of Quest\n2. Location - Kinds of Fishes\n3. Location - Average Fish Price\n"\
            "4. Fish - Number of Fishing Location\n5. NPC - Number of Quest")
        response = input("Select a statistical information or go back: ").lower().strip()

        if response == "1":
            query = "SELECT Locations.Name, COUNT(*) FROM Locations JOIN Quests ON Quests.Location = Locations.Id GROUP BY Locations.Name ORDER BY COUNT(*) DESC"
            result = run_queries(query)
            return result

        elif response == "2":
            query = "SELECT Locations.Name, COUNT(*) FROM Locations JOIN FishingLocation ON FishingLocation.Location = Locations.Id "\
                    "GROUP BY Locations.Name ORDER BY COUNT(*) DESC"
            result = run_queries(query)
            return result

        elif response == "3":
            query = "SELECT Locations.Name, AVG(Fishes.Price) FROM Locations JOIN FishingLocation ON FishingLocation.Location = Locations.Id "\
                    "JOIN Fishes ON Fishes.Id = FishingLocation.Fish GROUP BY Locations.Name ORDER BY AVG(Fishes.Price) DESC"
            result = run_queries(query)
            return result

        elif response == "4":
            query = "SELECT Fishes.Name, COUNT(*) FROM Fishes JOIN FishingLocation ON FishingLocation.Fish = Fishes.Id "\
                    "JOIN Locations ON Locations.Id = FishingLocation.Location GROUP BY Fishes.Name ORDER BY COUNT(*) DESC"
            result = run_queries(query)
            return result
        
        elif response == "5":
            query = "SELECT NPCs.Name, COUNT(*) FROM NPCs JOIN Quests ON Quests.Giver = NPCs.Name GROUP BY NPCs.Name ORDER BY COUNT(*) DESC"
            result = run_queries(query)
            return result

        elif response == "back":
            print("Back")
            break

        else:
            print("Invalid input please try again.")
        

def image_prompt():
    '''The prompt for image query.
    
    Parameters
    ----------
    None
    
    Returns
    -------
    None
    '''
    while True:
        response = input("Choose the entity that you would like to view (NPC or Fish) or go back: ").lower().strip()

        if response == "npc":
            query = "SELECT NPCs.Image FROM NPCs "
            name = ("%" + input("Please enter the name of the NPC: ").strip() + "%", )
            query += "WHERE NPCs.Name LIKE ?"
            result = run_queries(query, name)
            img = [data[0] for data in result]
            show_image(img)
            break

        elif response == "fish":
            query = "SELECT Fishes.Image FROM Fishes "
            name = ("%" + input("Please enter the name of the fish: ").strip() + "%", )
            query += "WHERE Fishes.Name LIKE ?"
            result = run_queries(query, name)
            img = [data[0] for data in result]
            show_image(img)
            break

        elif response == "back":
            print("Back")
            break

        else:
            print("Invalid input please try again.")

def base_prompt():
    '''The base prompt. Shown when the program is executed and database is ready.
    
    Parameters
    ----------
    None
    
    Returns
    -------
    None
    '''
    while True:
        response = input("Select the entity that you would like to query (NPC, Location, Quest, Fish) or stats or image or exit: ").lower().strip()

        if response == "exit":
            print("Exit")
            break

        elif response == "npc":
            result = NPC_prompt()
            if result is not None:
                name = [data[0] for data in result]
                info = [data[1] for data in result]
                gender = [data[2] for data in result]
            else:
                name = []
                info = []
                gender = []
            header_data = ["Name", "Info", "Gender"]
            cell_data = [name, info, gender]
            make_tables(header_data, cell_data)

        elif response == "location":
            result = location_prompt()
            if result is not None:
                name = [data[0] for data in result]
                info = [data[1] for data in result]
            else:
                name = []
                info = []
            header_data = ["Name", "Info"]
            cell_data = [name, info]
            make_tables(header_data, cell_data)
        
        elif response == "quest":
            result = quest_prompt()
            if result is not None:
                name = [data[0] for data in result]
                giver = [data[1] for data in result]
                location = [data[2] for data in result]
                reward = [data[3] for data in result]
                category = [data[4] for data in result]
            else:
                name = []
                giver = []
                location = []
                reward = []
                category = []

            header_data = ["Name", "Giver", "Location", "Reward", "Category"]
            cell_data = [name, giver, location, reward, category]
            make_tables(header_data, cell_data)

        elif response == "fish":
            result = fish_prompt()
            if result is not None:
                name = [data[0] for data in result]
                location = [data[1] for data in result]
                price = [data[2] for data in result]
            else:
                name = []
                location = []
                price = []
            header_data = ["Name", "Location", "Price"]
            cell_data = [name, location, price]
            make_tables(header_data, cell_data)

        elif response == "stats":
            result = stats_prompt()
            if result is not None:
                xvals = [data[0] for data in result]
                yvals = [data[1] for data in result]
            else:
                xvals = []
                yvals = []
            bar_chart(xvals, yvals)

        elif response == "image":
            image_prompt()
        
        else:
            print("Invalid input please try again.")

if __name__ == "__main__":
    
    p = Path()
    if not (p / DBNAME).exists():
        create_tables()
        insert_data()
    base_prompt()