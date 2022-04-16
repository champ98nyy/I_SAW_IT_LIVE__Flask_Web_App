#----- DEPENDENCIES -----#

import os
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required, lookup, show_count, concertDetails, isCoverSong, isEncore, concertExists, venueExists, userAttended
import math
import datetime
import time
from collections import Counter
from operator import itemgetter
import numpy as np


#----- CONFIGURATIONS -----#

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure SQLite Database
db = SQL("sqlite:///isil.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError


#----- ROUTES -----#

#----- USER'S HOME PAGE -----#
# Displays User's Full ISIL History + High-Level Stats

@app.route("/")
@login_required
def index():
    # Declare a variable for current session's user id, then pull user info from db and store in dict
    userId = session["user_id"]
    # userInfo = db.execute("SELECT username, zip_code, member_since FROM users WHERE id = ?", userId)
    userInfo = db.execute("SELECT username, zip_code, member_since "
                          "FROM users "
                          "WHERE id = ?", userId)

    userInfo = {
        "username": userInfo[0]["username"].upper(),
        "zipCode": userInfo[0]["zip_code"],
        "memberSince": datetime.datetime.strptime((userInfo[0]["member_since"])[:10], "%Y-%m-%d").strftime("%m/%d/%Y")
    }

    # Declare a variable for all concerts user has attended, selected from ISIL Database
    concerts = db.execute("SELECT date, artist, concerts.setlistId, url, name AS venue, city, state, country FROM concerts INNER JOIN venues ON concerts.venueId = venues.id INNER JOIN isil ON concerts.setlistId = isil.setlistId WHERE userId = ? ORDER BY date DESC", userId)

    # Declare empty lists to calculate total quantities of artists seen, concerts attended and venues visited
    # Append each concert to include a setlist URL (for modals) and a reformated date (for display in table)
    allArtists = []
    allConcerts = []
    allVenues = []
    for i in concerts:
        i["setlistUrl"] = "https://www.setlist.fm/widgets/setlist-image-v1?id=" + i["setlistId"] + "&size=large"
        i["date2"] = datetime.datetime.strptime(i["date"], "%Y/%m/%d").strftime("%m/%d/%Y")
        allArtists.append(i["artist"])
        allConcerts.append(i["date"])
        allVenues.append(i["venue"])

    allArtistsQty = len(list(set(allArtists)))
    allConcertsQty = len(list(set(allConcerts)))
    allVenuesQty = len(list(set(allVenues)))

    # Declare a dictionary that will hold the high-level stats for user's homepage
    statsOverview = {
        "allArtistsQty": allArtistsQty,
        "allConcertsQty": allConcertsQty,
        "allVenuesQty": allVenuesQty
    }
    return render_template("index.html", userInfo=userInfo, concerts=concerts, statsOverview=statsOverview)


#----- USER'S EXPERIENCE DASHBOARD -----#
# Displays a full dashboard of stats based on User's Full ISIL History

@app.route("/experience")
@login_required
def experience():

    # Declare a variable for current session's user id, then pull user info from db and store in dict
    userId = session["user_id"]
    userInfo = db.execute("SELECT username, zip_code, member_since from users WHERE id = ?", userId)
    userInfo = {
        "username": userInfo[0]["username"].upper(),
        "zipCode": userInfo[0]["zip_code"],
        "memberSince": datetime.datetime.strptime((userInfo[0]["member_since"])[:10], "%Y-%m-%d").strftime("%m/%d/%Y")
    }

    #----- ARTISTS STATS -----#
    # Declare a variable for all concerts user has attended, selected from ISIL Database
    concerts = db.execute("SELECT date, artist, concerts.setlistId, url, name AS venue, city, state, country FROM concerts INNER JOIN venues ON concerts.venueId = venues.id INNER JOIN isil ON concerts.setlistId = isil.setlistId WHERE userId = ? ORDER BY date DESC", userId)

    # Validate that user has previously added at least 1 concert to their ISIL History. If they haven't yet, they will be redirected to the index page.
    # Otherwise, they will continue on to the Experience Dashboard
    if not concerts:
        return redirect("/")

    else:
        for i in concerts:
            i["setlistUrl"] = "https://www.setlist.fm/widgets/setlist-image-v1?id=" + i["setlistId"] + "&size=large"

        setlistIds = []
        for i in concerts:
            setlistIds.append(i["setlistId"])

        # Declare empty list to store all artists user has seen live
        # Loop through all setlistIds to get artist for each show and add to list of allArtists, including repeats
        allArtists = []
        for i in setlistIds:
            allArtists.append(db.execute("SELECT artist FROM concerts INNER JOIN isil ON concerts.setlistId = isil.setlistId WHERE isil.setlistId = ?", i)[0]["artist"])

        # Create dict of how many performances user has seen by each unique artist {artist name: qty}
        # Declare variable to calculate total qty of unique artists user has seen live
        artistsSeen = dict(Counter(allArtists).most_common())
        artistsSeenQty = len(artistsSeen)

        # Remove duplicate artists from list
        allArtists = list(set(allArtists))

        # Declare variable to hold top 5 (performance qty) artists user has seen
        artistsSeenTop5 = list(artistsSeen.items())[:5]

    #----- SETLIST STATS -----#
        # Check every setlistId for a corresponding setlist of songs
        # If no songs in db match setlistId, it's a show without a setlist

        print("START OF SETLIST STATS")
        noSetListShows = 0
        for i in setlistIds:
            setlist = db.execute("SELECT title FROM songs WHERE setlistId = ?", i)
            if not setlist:
                noSetListShows += 1

        # Declare an empty list to store all songs user has heard live
        allSongs = []

        # For each unique artist user has seen live, get the title of each song performed by that artist at any concert the user attended
        for artist in allArtists:
            songs = db.execute("SELECT title FROM songs INNER JOIN concerts ON songs.setlistId = concerts.setlistId WHERE concerts.artist = ? AND songs.setlistId IN(?)", artist, setlistIds) # Returns list of dicts {"title": song title}
            songs = [d['title'] for d in songs] # Converts list of dicts into list of corresponding values only
            allSongs.append({
                "artist": artist,
                "songs": songs
            }) # Creates a list of dictionaries, each of which contains 2 keys (artist: artist name, songs: [list of all songs performed by that artist, including duplicate])

        # Combine allsongs dicts (song title/qty) with artist's name to create new list of dicts, each containing artist name, song title, qty user has heard the song live
        workingDict = {}
        workingList = []
        for i in allSongs:
            tempList = dict(Counter(i["songs"]))
            tempArtist = i["artist"]
            for key, value in tempList.items():
                workingDict = {
                    "artist": tempArtist,
                    "song": key,
                    "qty": value
                }
                workingList.append(workingDict)

        # Using itemgetter function from operator module (converts dict keys into tuples)
        # sort list of song dicts descendingly, based on qty user has seen song performed live
        allSongsSorted = sorted(workingList, key=itemgetter("qty"), reverse=True)
        print("ALL SONGS SORTED: ", allSongsSorted)


        # Declare a variable to calculate total quantity of songs user has heard live, NOT including repeats
        uniqueSongsQty = len(allSongsSorted)

        # Declare a variable to calculate total quantity of songs user has heard live, including repeats
        songsHeardLiveQty = 0
        for i in allSongsSorted:
            qty = i["qty"]
            songsHeardLiveQty += qty
        print("SONGS HEARD LIVE QTY: ", songsHeardLiveQty)


        # Declare variable to keep track of the 5 songs a user has seen live the most times.
        # If user has heard less than 5 songs live, their list will include as many songs as they have heard
        if len(allSongsSorted) >= 5:
            top5Songs = allSongsSorted[:5]
        else:
            top5Songs = allSongsSorted
        print("TOP 5 SONGS: ", top5Songs)

        # For each unique artist user has seen live, get the title of each song performed by that artist at any concert the user attended
        print("START OF ENCORE SONGS STATS")
        allEncoreSongs = []
        for artist in allArtists:
            encoreSongs = db.execute("SELECT title FROM songs INNER JOIN concerts ON songs.setlistID = concerts.setlistId WHERE concerts.artist = ? AND songs.encore = 1 AND songs.setlistId IN(?)", artist, setlistIds)
            encoreSongs = [d['title'] for d in encoreSongs] # Converts list of dicts into list of corresponding values only
            allEncoreSongs.append({
                "artist": artist,
                "encoreSongs": encoreSongs
            }) # Creates a list of dictionaries, each of which contains 2 keys (artist: artist name, encore songs: [list of all encore songs performed by that artist, including duplicates])
        print("ALL ENCORE SONGS BEFORE SORTING: ", allEncoreSongs)

        # Combine allEncoreSongs dicts (encore song title/qty) with artist's name to create new list of dicts, each containing artist name, encore song title, qty user has heard the song as an encore live
        workingEncoreDict = {}
        workingEncoreList = []
        for i in allEncoreSongs:
            tempEncoreList = dict(Counter(i["encoreSongs"]))
            tempEncoreArtist = i["artist"]
            for key, value in tempEncoreList.items():
                workingEncoreDict = {
                    "artist": tempEncoreArtist,
                    "encoreSong": key,
                    "qty": value
                }
                workingEncoreList.append(workingEncoreDict)

        # Using itemgetter function from operator module (converts dict keys into tuples)
        # sort list of encore song dicts descendingly, based on qty user has seen song performed live
        allEncoreSongsSorted = sorted(workingEncoreList, key=itemgetter("qty"), reverse=True)
        print("ALL ENCORE SONGS SORTED: ", allEncoreSongsSorted)
        # Declare a variable to calculate total quantity of songs user has heard as encores live, NOT including repeats
        uniqueEncoreSongsQty = len(allEncoreSongsSorted)
        print("UNIQUE ENCORE SONGS QTY: ", uniqueEncoreSongsQty)
        # Declare a variable to calculate total quantity of songs user has heard as encores live, including repeats
        encoreSongsHeardLiveQty = 0
        for i in allEncoreSongsSorted:
            qty = i["qty"]
            encoreSongsHeardLiveQty += qty
        print("ENCORE SONGS HEARD LIVE QTY: ", encoreSongsHeardLiveQty)

        # Declare variable to keep track of the 5 songs a user has heard as encores live the most times.
        # If the user has heard less than 5 encore songs live, their list will include as many songs as they have heard as an encore
        if len(allEncoreSongsSorted) >= 5:
            top5EncoreSongs = allEncoreSongsSorted[:5]
        else:
            top5EncoreSongs = allEncoreSongsSorted
        print("TOP 5 ENCORE SONGS: ", top5EncoreSongs)

        """ Need a list of unique dates user has attended a performance on. Will assume any performance on same date is part of one concert.
        This will ensure stats related to locations/venues don't count more than once for the same concert.
        """
        # Declare an empty list to store the date of every performance user has seen, including repeats from different artists at same concert
        totalPerformances = []
        for i in concerts:
            uniqueDate = i["date"]
            totalPerformances.append(uniqueDate)

        # Using unique() function from Numpy library, remove duplicate dates from list
        uniqueDates = np.unique(np.array(totalPerformances))
        print("UNIQUE DATES: ", uniqueDates)
        print("UNIQUE DATES IS TYPE: ", type(uniqueDates))
        uniqueDates = uniqueDates.tolist()
        print("NOW UNIQUE DATES: ", uniqueDates)
        print("NOW UNIQUE DATES IS TYPE: ", type(uniqueDates))
    #----- VENUES + LOCATIONS -----#
        # Declare empty lists to store all info on venues/locations visited,  date of every performance user has seen, including repeats from different artists at same concert
        venuesVisited = []
        citiesVisited = []
        statesVisited = []
        countriesVisited = []

        # print("UNIQUE DATES IS TYPE: ", type(uniqueDates))

        for date in uniqueDates:
            print(date)
            info = db.execute("SELECT DISTINCT name AS venue, city, state, country FROM venues INNER JOIN concerts ON venues.id = concerts.venueId INNER JOIN isil ON concerts.setlistId = isil.setlistId WHERE userId = ? AND date = ?", userId, date)
            venuesVisited.append(info[0]["venue"])
            citiesVisited.append(info[0]["city"])
            statesVisited.append(info[0]["state"])
            countriesVisited.append(info[0]["country"])

        venuesVisited = dict(Counter(venuesVisited).most_common())
        venuesVisitedQty = len(venuesVisited)

        if venuesVisitedQty >= 5:
            venuesVisitedTop5 = list(venuesVisited.items())[:5]
        else:
            venuesVisitedTop5 = list(venuesVisited.items())

        citiesVisited = dict(Counter(citiesVisited).most_common())
        citiesVisitedQty = len(citiesVisited)

        statesVisited = dict(Counter(statesVisited).most_common())
        statesVisitedQty = len(statesVisited)

        countriesVisited = dict(Counter(countriesVisited).most_common())
        countriesVisitedQty = len(countriesVisited)

    #----- CONCERTS/PERFORMANCES STATS -----#
        # Declare variables to calculate total qty of performances and concerts user has attended
        totalPerformances = len(totalPerformances)
        concertsAttended = len(uniqueDates)

    #----- FIRST SHOW/LAST SHOW STATS -----#
        # Declare empty list to store db details of first concert user ever attended
        firstShowArtists = []
        firstShow = db.execute("SELECT artist, venueId, name AS venue, city, state, country FROM concerts INNER JOIN venues ON concerts.venueId = venues.id INNER JOIN isil ON concerts.setlistId = isil.setlistId WHERE date = ? AND userId = ?", uniqueDates[0], userId)
        for i in firstShow:
            firstShowArtists.append(i["artist"])

        # Store all details of first concert in a dict
        firstShow = {
            "date": datetime.datetime.strptime(uniqueDates[0], "%Y/%m/%d").strftime("%m/%d/%Y"),
            "artists": firstShowArtists,
            "venue": firstShow[0]["venue"],
            "city": firstShow[0]["city"],
            "state": firstShow[0]["state"],
            "country": firstShow[0]["country"]
        }

        # Using datetime module, calculate how many days it's been since user attended first concert
        today = datetime.date.today()
        firstShowSeen = datetime.datetime.strptime(uniqueDates[0], "%Y/%m/%d").date()
        sinceFirstShow = (today - firstShowSeen).days

        # Setup parameters to convert days into years and days (if it's been more than a year)
        # Use math module to round down
        if sinceFirstShow >= 365:
            yearsSinceFirstShow = sinceFirstShow/365.25
            yearsBuffer = math.floor(yearsSinceFirstShow)
            daysBuffer = math.floor(math.fmod(sinceFirstShow, 365.25))
            sinceFirstShow = {
                "years": yearsBuffer,
                "days": daysBuffer
            }
        else:
            sinceFirstShow = {
                "years": 0,
                "days": sinceFirstShow
            }

        # Declare empty list to store db details of most recent concert user attended
        lastShowArtists = []
        lastShow = db.execute("SELECT artist, venueId, name AS venue, city, state, country FROM concerts INNER JOIN venues ON concerts.venueId = venues.id INNER JOIN isil ON concerts.setlistId = isil.setlistId WHERE date = ? AND userId = ?", uniqueDates[-1], userId)
        for i in lastShow:
            lastShowArtists.append(i["artist"])

        # Store all details of most recent concert in a dict
        lastShow = {
            "date": datetime.datetime.strptime(uniqueDates[-1], "%Y/%m/%d").strftime("%m/%d/%Y"),
            "artists": lastShowArtists,
            "venue": lastShow[0]["venue"],
            "city": lastShow[0]["city"],
            "state": lastShow[0]["state"],
            "country": lastShow[0]["country"]
        }

        # Using datetime module, calculate how many days it's been since user attended most recent concert
        lastShowSeen = datetime.datetime.strptime(uniqueDates[-1], "%Y/%m/%d").date()
        sinceLastShow = (today - lastShowSeen).days

        # Setup parameters to convert days into years and days (if it's been more than a year)
        # Use math module to round down
        if sinceLastShow >= 365:
            yearsSinceLastShow = sinceLastShow/365.25
            yearsBuffer = math.floor(yearsSinceLastShow)
            daysBuffer = math.floor(math.fmod(sinceLastShow, 365.25))
            sinceLastShow = {
                "years": yearsBuffer,
                "days": daysBuffer
            }
        else:
            sinceLastShow = {
                "years": 0,
                "days": sinceLastShow
            }

    #----- FINAL STATS -----#
        # Store all statistical details in a dict
        userStats = {
            "venuesVisited": venuesVisited,
            "venuesVisitedQty": venuesVisitedQty,
            "venuesVisitedTop5": venuesVisitedTop5,
            "citiesVisited": citiesVisited,
            "citiesVisitedQty": citiesVisitedQty,
            "statesVisited": statesVisited,
            "statesVisitedQty": statesVisitedQty,
            "countriesVisited": countriesVisited,
            "countriesVisitedQty": countriesVisitedQty,
            "totalPerformances": totalPerformances,
            "concertsAttended": concertsAttended,
            "firstShow": firstShow,
            "sinceFirstShow": sinceFirstShow,
            "lastShow": lastShow,
            "sinceLastShow": sinceLastShow,
            "artistsSeen": artistsSeen,
            "artistsSeenQty": artistsSeenQty,
            "artistsSeenTop5": artistsSeenTop5,
            "songsHeard": allSongsSorted,
            "songsHeardTop5": top5Songs,
            "songsHeardLiveQty": songsHeardLiveQty,
            "uniqueSongsQty": uniqueSongsQty,
            "noSetListShows": noSetListShows,
            "encoreSongs": allEncoreSongsSorted,
            "encoreSongsHeardTop5": top5EncoreSongs,
            "encoreSongsHeardLiveQty": encoreSongsHeardLiveQty,
            "uniqueEncoreSongsQty": uniqueEncoreSongsQty
        }

        # Re-format the dates into MM-DD-YYYY format for display
        for i in concerts:
            value = datetime.datetime.strptime(i["date"], "%Y/%m/%d").strftime("%m/%d/%Y")
            i.update({"date": value})

        return render_template("experience.html", userInfo=userInfo, concerts=concerts, userStats=userStats)


#----- NEW USER REGISTRATION PAGE -----#
@app.route("/register", methods=["GET", "POST"])
def register():

    # User reached route via POST (submitted registration form)
    if request.method == "POST":

        # Declare a variable for each piece of data submitted in the form
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        zip_code = request.form.get("zip_code")

        # Ensure username was submitted
        if not username:
            return apology("PLEASE PROVIDE A USERNAME", 400)

        # Ensure password was submitted
        elif not password:
            return apology("PLEASE PROVIDE A PASSWORD", 400)

        # Ensure password matches password confirmation
        elif password != confirmation:
            return apology("PASSWORD CONFIRMATION MUST MATCH PASSWORD. PLEASE TRY AGAIN.", 400)

        # Ensure zip code was submitted
        elif not zip_code:
            return apology("PLEASE PROVIDE YOUR ZIP CODE", 400)

        # Query db to check if username already exists
        rows = db.execute("SELECT * FROM users WHERE upper(username) = ?", username.upper())

        # If the username already exists, return an error
        if len(rows) > 0:
            return apology("SORRY, BUT THAT USERNAME IS ALREADY IN USE. PLEASE TRY AGAIN.", 400)

        # Otherwise, register new user by hashing their password and adding them to database
        else:
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
            db.execute("INSERT INTO users (username, password, zip_code) VALUES(?, ?, ?)", username, hashed_password, zip_code)

        # Return newly registered user to login page
        return redirect("/login")
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


#----- LOGIN PAGE -----#
# Default route if user is not currently signed in

@app.route("/login", methods=["GET", "POST"])
def login():

    # Forget any previous user info
    session.clear()

    # User reached route via POST (submitted login form)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("PLEASE PROVIDE A USERNAME", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("PLEASE PROVIDE A PASSWORD", 403)

        # Query db for username
        rows = db.execute("SELECT * FROM users WHERE upper(username) = ?", request.form.get("username").upper())

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["password"], request.form.get("password")):
            return apology("INVALID USERNAME AND/OR PASSWORD. PLEASE TRY AGAIN.", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect logged-in user to Home Page
        return redirect("/")

    # User reached route via GET
    else:
        return render_template("login.html")


#----- LOGOUT FUNCTIONALITY -----#
@app.route("/logout")
def logout():

    # Forget existing user info
    session.clear()

    # Redirect user to Login Page
    return redirect("/")


#----- SEARCH PAGE + FUNCTIONALITY -----#
@app.route("/search", methods=["GET", "POST"])
@login_required
def search():

    # User reached route via POST (submitted a search query)
    if request.method == "POST":

        # Declare a variable for current session's user id
        userId = session["user_id"]

        """ Need a list of all performances user has seen live and already added to their ISIL History
        so they can be marked off if they appear in search results.
        """
        # Declare a variable to temporarily store list of dicts of setlist ID for all concerts user has attended, selected from ISIL Database
        concerts = db.execute("SELECT setlistId FROM isil WHERE userId = ?", userId)

        # Declare an empty list to add all setlist IDs to
        setlistIds = []
        for concert in concerts:
            setlistIds.append(concert["setlistId"])

        # Declare a variable to store the search terms input by user
        search = request.form.get("search")

        """
        setlist.fm limits all search results made through api calls to 20/page.
        In order to return full search results, api calls must be made iteratively for each page of 20 results.
        This is achieved by defaulting to "pg 1" on the first api call, checking the response for the total qty of
        concert setlists available for the artist searched for, dividing by 20 (max results/pg), then rounding up to nearest integer.
        If more than 1 pg of results exists, successive api calls will be made for each pg available, and all will be stored in a single results list variable.
        """
        # Declare a variable to initiate a counter that keeps track of the pages in the search results
        pg_num = 1

        # Using show_count custom function calculate total pages of search results needed
        total_shows = show_count(search, pg_num)

        # Ensure search term is valid, then display requested results in "searched.html" view
        # If search was invalid, serve error message
        if total_shows == None:
            return apology("YOUR SEARCH CAME UP EMPTY. PLEASE TRY AGAIN.", 400)

        total_pgs = math.ceil(total_shows/20)

        # Declare a variable to store the results of calling the lookup function on the search terms input by user + the page number (will iterate)
        shows_buffer = []
        for page in range(total_pgs):
            shows_buffer.append(lookup(search, pg_num))
            pg_num += 1
        shows = []

        for results in shows_buffer:
            for concert in results:

                setlistId = concert["id"]
                url = concert["url"]
                setlistUrl = "https://www.setlist.fm/widgets/setlist-image-v1?id=" + setlistId + "&size=large"
                date = datetime.datetime.strptime(concert["eventDate"], "%d-%m-%Y").strftime("%m/%d/%Y")

                # date2 will be used to properly sort search results table by date, while displaying dates in above format
                date2 = datetime.datetime.strptime(concert["eventDate"], "%d-%m-%Y").strftime("%Y/%m/%d")
                artist = (concert["artist"])["name"]
                venue = (concert["venue"])["name"]
                city = ((concert["venue"])["city"])["name"]
                country = (((concert["venue"])["city"])["country"])["name"]

                try:
                    state = ((concert["venue"])["city"])["state"]
                except KeyError:
                    state = " "

                shows.append({
                    "setlistId": setlistId,
                    "url": url,
                    "setlistUrl": setlistUrl,
                    "date": date,
                    "date2": date2,
                    "artist": artist,
                    "venue": venue,
                    "city": city,
                    "state": state,
                    "country": country
                })
        return render_template("searched.html", shows=shows, total_pgs=total_pgs, setlistIds=setlistIds)

  # User reached route via GET (clicked on link or input url for Search Page)
    else:
        return render_template("search.html")


#----- FUNCTIONALITY FOR USER TO ADD A PERFORMANCE TO THEIR ISIL HISTORY -----#
@app.route("/addShow", methods=["POST"])
@login_required
def addShow():
    # User reached route via POST (Clicked ADD SHOW Button for specific performance)
    if request.method == "POST":

        # Declare variables to store the setlistId + current session's userId
        setlistId = request.form.get("setlistId")
        userId = session["user_id"]

        # Using userAttended() custom function, query db to check if user has previously added this concert to their ISIL History
        if userAttended(setlistId, userId, db) == True:
            flash("YOU HAVE ALREADY ADDED THIS PERFORMANCE TO YOUR ISIL HISTORY.")
            return redirect("/")

        # If the user has previously added the concert to their ISIL experiences, it would also indicate that the concert and venue exist in the ISIL db
        # If not, add the concert to the user's ISIL History, flash a message confirming it's been added, then check if the concert/venue exist in their respective tables
        else:
            db.execute("INSERT INTO isil (userId, setlistId) VALUES(?, ?)", userId, setlistId)
            flash("YOU HAVE SUCCESSFULLY ADDED THIS PERFORMANCE TO YOUR ISIL HISTORY.")

        # Check if concert already exists in isil db (previously added by different user). If yes, the venue must also already exist, so that step can be skipped
        # User can be returned to ISIL Home Page
        if concertExists(setlistId, db) == True:
            return redirect("/")

        # If concert does not already exist, get concert details and check if venue already exists
        else:
            show = concertDetails(setlistId)
            date = show["date"]
            venueId = show["venueId"]
            artist = show["artist"]
            tour = show["tour"]
            url = show["url"]
            encoreSetsQty = show["encoreSetsQty"]
            regSetSongsBuffer = show["regSetSongs"]
            encoreSetSongsBuffer = show["encoreSetSongs"]
            regSetSongs = []
            encoreSetSongs = []

            # Loop through every song in regSetSongsBuffer, create uniform/updated dictionary and add to songs table of ISIL db
            for i in regSetSongsBuffer:
                for j in i["song"]:
                    song = {
                        "title": j["name"],
                        "info": "N/A",
                        "cover": {
                            "isCover": False,
                            "artistName": "N/A"
                        },
                        "encore": False,
                        "guests": "N/A"
                    }

                    if "info" in j:
                        song.update({"info": j["info"]})

                    if "cover" in j:
                        (song["cover"])["isCover"] = True
                        (song["cover"])["artistName"] = (j["cover"])["name"]

                    if "with" in j:
                        song["guests"] = (j["with"])["name"]

                    db.execute("INSERT INTO songs (setlistId, title, info, cover, coverArtist, encore, guests) VALUES(?, ?, ?, ?, ?, ?, ?)", setlistId, song["title"], song["info"], (song["cover"])["isCover"], (song["cover"]["artistName"]), song["encore"], song["guests"])

            # Check if there were any encore sets. If so, loop through every song in encoreSetSongsBuffer, create uniform/updated dictionary and add to songs table of ISIL db
            if encoreSetsQty > 0:
                for k in encoreSetSongsBuffer:
                    for l in k["song"]:
                        song = {
                            "title": l["name"],
                            "info": "N/A",
                            "cover": {
                                "isCover": False,
                                "artistName": "N/A"
                            },
                            "encore": True,
                            "guests": "N/A"
                        }

                        if "info" in l:
                            song.update({"info": l["info"]})

                        if "cover" in l:
                            (song["cover"])["isCover"] = True
                            (song["cover"])["artistName"] = (l["cover"])["name"]

                        if "with" in l:
                            song["guests"] = (l["with"])["name"]

                        db.execute("INSERT INTO songs (setlistId, title, info, cover, coverArtist, encore, guests) VALUES(?, ?, ?, ?, ?, ?, ?)", setlistId, song["title"], song["info"], (song["cover"])["isCover"], (song["cover"]["artistName"]), song["encore"], song["guests"])

            # Check if venue already exists in venues table of ISIL db. If not, declare variables for venue details
            if venueExists(venueId, db) == False:
                venue = show["venue"]
                city = show["city"]
                latitude = show["latitude"]
                longitude = show["longitude"]
                state = show["state"]
                country = show["country"]

                # Add to venues table in ISIL db.
                db.execute("INSERT INTO venues (id, name, city, state, country, latitude, longitude) VALUES(?, ?, ?, ?, ?, ?, ?)", venueId, venue, city, state, country, latitude, longitude)

        # Add concert details to concerts table in ISIL db, then return user to ISIL Home Page
        db.execute("INSERT INTO concerts (setlistId, date, artist, venueId, encoreSetsQty, url) VALUES(?, ?, ?, ?, ?, ?)", setlistId, date, artist, venueId, encoreSetsQty, url)

        return redirect("/")


#----- FUNCTIONALITY FOR USER TO REMOVE A PERFORMANCE FROM THEIR ISIL HISTORY -----#
@app.route("/removeShow", methods=["POST"])
@login_required
def removeShow():

    # User reached route via POST (Clicked Remove Show Button for specific concert)
    if request.method == "POST":

        # Declare variables to store the setlistId + current session's userId
        setlistId = request.form.get("setlistId")
        userId = session["user_id"]

        # Using userAttended() custom function, query db to validate user currently has this concert included in their ISIL History
        if userAttended(setlistId, userId, db) == True:

            # Delete corresponding record from ISIL table, then return user to ISIL Home Page
            db.execute("DELETE FROM isil WHERE userId = ? AND setlistId = ?", userId, setlistId)
            flash("PERFORMANCE HAS BEEN REMOVED FROM YOUR ISIL HISTORY.")

        return redirect("/")

#----- FUNCTION TO HANDLE ERRORS -----#
def errorhandler(e):
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


#----- FUNCTION TO LISTEN FOR ERRORS -----#
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)