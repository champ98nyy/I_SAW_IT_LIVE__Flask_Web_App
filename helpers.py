#----- DEPENDENCIES -----#
import os
import requests
import urllib.parse
import urllib.request
from flask import redirect, render_template, request, session
from functools import wraps
import datetime

#----- CUSTOM FUNCTIONS -----#

#----- APOLOGY() -----#
# Custom Function to display an error code and message
def apology(message, code=400):
    return render_template("apology.html", message=message, code=code)


#----- LOGIN_REQUIRED() -----#
# Flask decorator function to require user to be logged in for corresponding route
# https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


#----- CUSTOM FUNCTIONS FOR SEARCH ROUTE -----#

#----- SHOW_COUNT() -----#
# Custom Function to count total qty of setlists in setlist.fm db for a given artist
# Works in correlation with Search route in order to iterate through all pages of results
def show_count(search, pg_num):
    try:
        url = "https://api.setlist.fm/rest/1.0/search/setlists?artistName=" + search + "&p=" + f'{pg_num}'
        headers = {"Accept": "application/json", "x-api-key": os.environ.get("API_KEY")}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.RequestException:
        return None

    try:
        total = response.json()["total"]
        return total

    except (KeyError, TypeError, ValueError):
        return None


#----- LOOKUP() -----#
# Custom Function to return all data for all concerts by a specific artist/band
def lookup(search, pg_num):
    try:
        url = "https://api.setlist.fm/rest/1.0/search/setlists?artistName=" + search + "&p=" + f'{pg_num}'
        headers = {"Accept": "application/json", "x-api-key": os.environ.get("API_KEY")}
        response = requests.get(url, headers=headers)
        response.raise_for_status()

    except requests.RequestException:
        return None

    try:
        data = response.json()["setlist"]
        return data

    except (KeyError, TypeError, ValueError):
        return None


#----- CUSTOM FUNCTIONS FOR ADDSHOW/REMOVESHOW ROUTES -----#

#----- ISCOVERSONG() -----#
# Custom Function to determine if any song is a cover song
def isCoverSong(dict):
    if "cover" in dict:
        return True


#----- ISENCORESONG() -----#
# Custom Function to determine if a set is an encore
def isEncore(dict):
    if "encore" in dict:
        return True


#----- CONCERTEXISTS() -----#
# Custom Function to determine if a concert is already in ISIL db
def concertExists(setlistId, db):
    x = db.execute("SELECT setlistId FROM concerts WHERE setlistId = ?", setlistId)
    if len(x) > 0:
        return True
    else:
        return False


#----- VENUEEXISTS() -----#
# Custom Function to determine if a venue is already in ISIL db
def venueExists(venueId, db):
    x = db.execute("SELECT * FROM venues WHERE id = ?", venueId)
    if len(x) > 0:
        return True
    else:
        return False


#----- USERATTENDED() -----#
# Custom Function to determine if a user already added a specific concert to their ISIL History
def userAttended(setlistId, userId, db):
    x = db.execute("SELECT userId FROM isil WHERE setlistId = ? AND userId = ?", setlistId, userId)
    if len(x) > 0:
        return True
    else:
        return False


#----- CONCERTDETAILS() -----#
# Custom Function to return details of a specific concert, given a setlistId
def concertDetails(setlistId):
    try:
        url = "https://api.setlist.fm/rest/1.0/setlist/" + setlistId
        headers = {"Accept": "application/json", "x-api-key": os.environ.get("API_KEY")}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.RequestException:
        return None

    try:
        show = response.json() # ALL DATA FROM JSON RESPONSE
        setlistId = show["id"]
        url = show["url"]
        date = datetime.datetime.strptime(show["eventDate"], "%d-%m-%Y").strftime("%Y/%m/%d")
        testdate = show["eventDate"]
        artist = (show["artist"])["name"]
        venueId = (show["venue"])["id"]
        venue = (show["venue"])["name"]
        city = ((show["venue"])["city"])["name"]
        latitude = (((show["venue"])["city"])["coords"])["lat"]
        longitude = (((show["venue"])["city"])["coords"])["long"]
        country = (((show["venue"])["city"])["country"])["name"]

        try:
            state = ((show["venue"])["city"])["state"]
        except (KeyError):
            state = " "

        try:
            tour = (show["tour"])["name"]
        except (KeyError):
            tour = "N/A"

        setsBuffer = (show["sets"])["set"] # LIST OF SETS DICTIONARIES

        # Determine if show had only one set (no possibility there was an encore)
        totalSetsQty = len(setsBuffer) # RETURNS AN INTEGER INDICATING THE QUANTITY OF SETS PLAYED AT A CONCERT

        # If there was only 1 set, that set is the main set and there was no encore
        if totalSetsQty == 1:
            regularSets = setsBuffer
            encoreSets = "N/A"
            encoreSetsQty = 0

        # If more than 1 set was played at a concert, any set besides the first may have been an encore.
        # Declare an empty list to store regular sets and another empty list to store encore sets.
        else:
            regularSets = []
            encoreSets = []

            # Loop through all sets, checking whether or not it was an encore, add set to appropriate list based on results
            for i in setsBuffer:
                if isEncore(i):
                    encoreSets.append(i)
                else:
                    regularSets.append(i)

            # Determine quantity of regular sets and encore sets by measuring the length of each list
            regularSetsQty = len(regularSets)
            encoreSetsQty = len(encoreSets)

        return {
            "setlistId": setlistId,
            "url": url,
            "date": date,
            "artist": artist,
            "venueId": venueId,
            "venue": venue,
            "city": city,
            "latitude": latitude,
            "longitude": longitude,
            "state": state,
            "country": country,
            "tour": tour,
            "regSetSongs": regularSets,
            "encoreSetSongs": encoreSets,
            "encoreSetsQty": encoreSetsQty
        }

    except (KeyError, TypeError, ValueError):
        return None