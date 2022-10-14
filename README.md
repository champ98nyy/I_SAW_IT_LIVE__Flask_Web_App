
# **I SAW IT LIVE**

[Walkthrough Video]

I SAW IT LIVE (ISIL) is a personal concert tracker web application, providing users with a central hub to keep track of every concert they have ever attended. Beyond just a list, or even a datatable of all the concerts, ISIL also provides a dynamically-generated data dashboard specific to their lifetime live music experience.

Users can search for concerts they have been to, add them to their ISIL History, and then view their Experience Dashboard for deeper insights into their lifetime statistics. As concerts get added to their ISIL History, the statistics in the Experience Dashboard also update accordingly.

Inspired by my own journey of live musical experiences over the past 30+ years, and my attempts to keep track of those experiences, first in a pre-digital world via pen and paper, then translated into an Excel Spreadsheet stored locally on my PC, then to a Google Sheet in the cloud, and now in a dynamic web application that others can also utilize.

I SAW IT LIVE is a Model-View-Controller web application built on Flask’s framework.

## **MODEL**

### **isil.db**
The ISIL database is built in SQLite.
The database contains the following tables:

#### **concerts**
The concerts table stores data on every concert an ISIL user has attended. New rows representing each concert, are added to the table the first time any ISIL user adds a specific concert. If a second user later adds the same concert to their ISIL History, the concerts table will not be modified.
<img width="1152" alt="image" src="https://user-images.githubusercontent.com/78568826/195933128-bcd1cb76-dfd7-4859-83ff-dbeead05c83a.png">

Each concert is identified by a unique id (PRIMARY KEY), along with a setlistId provided by setlist.fm. Additionally, each concert row includes the date of the concert, name of the artist, setlist.fm venueId (FOREIGN KEY), setlist.fm setlist url and a boolean variable for whether or not the concert included an encore set.

`CREATE TABLE 'concerts' ('id' integer PRIMARY KEY AUTOINCREMENT NOT NULL, 'setlistId' varchar(16) NOT NULL, 'date' date NOT NULL, artist varchar(255) NOT NULL DEFAULT ' ','venueId' varchar(20) NOT NULL DEFAULT 'None','encoreSetsQty' smallint NOT NULL DEFAULT 0, 'url' text NOT NULL DEFAULT 'tbd')`

#### **songs**
The songs table keeps track of every song played at every concert an ISIL user (or multiple users) has attended. New rows representing each song of the setlist, are added to the table the first time any ISIL user adds a specific concert. If a second user later adds the same concert to their ISIL History, the songs table will not be modified.

Each song is identified by a unique id (PRIMARY KEY). Additionally, each row includes the setlist.fm setlistId of the concert corresponding to the concert at which the song was played, along with the title of the song, any additional information about the song, the name of the original artist if the song was a cover, and the name of any guests performing the song with the main artist, if applicable. Finally, there are boolean variables for whether or not the song was a cover song and whether or not the song was played during the encore of the given concert.

`CREATE TABLE 'songs' ('id' integer PRIMARY KEY AUTOINCREMENT NOT NULL, 'setlistId' varchar(16) NOT NULL, 'title' text NOT NULL, 'info' text NOT NULL, 'cover' boolean NOT NULL, 'coverArtist' varchar(255) NOT NULL, 'encore' boolean NOT NULL, 'guests' varchar(255) NOT NULL)`

#### **venues**
The venues table stores data on every venue an ISIL user has attended a concert at. New rows representing each venue, are added to the table the first time any ISIL user adds any concert that took place at the venue. If another concert taking place at the same venue is later added by a second user (or the original user), the  table will not be modified.

Each venue is identified by a unique id provided by setlist.fm (PRIMARY KEY), along with the venue’s name, city, state (if applicable), country, latitude and longitude

`CREATE TABLE 'venues' ('id' varchar(20) PRIMARY KEY NOT NULL, 'name' varchar(255) NOT NULL, 'city' varchar(120), 'state' varchar(120), 'country' varchar(120), 'latitude' text, 'longitude' text)`

#### **users**
The users table keeps track of every ISIL user. Each user is identified by a unique id (PRIMARY KEY), along with their username, password, home zip code and the timestamp of when they first registered for an ISIL account.

`CREATE TABLE users ( id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL, zip_code CHAR(5) NOT NULL, member_since TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP)`

#### **isil**
The isil table keeps track of which users have been to which concerts. A new row is created every time any user adds a concert to their ISIL History, and removed if a user removes a concert from their ISIL History.

Each row is identified by a unique id (PRIMARY KEY), and also includes the userId (FOREIGN KEY) of the user adding a concert and the setlistId of the concert being added by the user. Unlike the concerts table, setlistIds can be duplicated in the isil table if more than one user adds the same concert to their ISIL History.

`CREATE TABLE 'isil' ('id' integer PRIMARY KEY AUTOINCREMENT NOT NULL, 'userId' integer NOT NULL, 'setlistId' varchar(16) NOT NULL)`

#### **setlist.fm**
In addition to the data stored locally in isil.db, I SAW IT LIVE utilizes data from setlist.fm, through API calls. This takes place when a user performs a search. When a concert gets added to a user’s ISIL History, the tables of isil.db are updated with data pulled from setlist.fm. However, once that data has been stored locally, it is not necessary to make additional API calls in order to populate a user’s ISIL History table or any of their Experience Dashboard statistics.

A setlist.fm API Key will need to be obtained in order to properly run this program:
*  [Apply Here]
*  You will need to sign in to your [setlist.fm user account] before requesting an API Key

## **VIEW**

### **Templates**:
### **layout.html**
Serves as the “skeleton” template that the rest of the below views inherit. This includes elements such as the page title, expandable/collapsible navbar, flashed messages container, animated loading indicator, footer and a block for the main content of any view.

Additionally, each view has access to the packages included in the header of layout.html (Bootstrap CSS, Bootstrap JS Bundle, Bootstrap Icons, Favicon, jQuery Bundle, jQuery DataTables ISIL’s Custom CSS, and JS functions that are needed across multiple views (Dynamic Creation/Display of setlist modals, displaying animated loading indicator, displaying Tooltips when triggered and toggling the color switch of the ISIL Home Button upon hover.

### **index.html**
![I SAW IT LIVE INDEX PAGE](https://github.com/champ98nyy/I_SAW_IT_LIVE__Flask_Web_App/blob/707aa85c1bb09041239f4533ce5bd5210ff5e0c8/static/ISIL_History_01.gif "I SAW IT LIVE INDEX PAGE")

Supporting the “GET” method only, index.html inherits the structure of layout.html and serves as the main landing page and account overview once a user has logged in. This view will also be served after a user adds/removes a concert to their ISIL History, as well as whenever the ISIL icon in the navigation is clicked on.

Jinja variables and expressions are leveraged to dynamically display a "Welcome Back (username)” message, along with an indication of how long the user has been an ISIL member.

As a bit of a tease and trail of breadcrumbs for the user to go view their full Experience Dashboard, (3) mini statistical cards are also displayed at the top of this view, letting the user know their total lifetime quantity of concerts attended, artists seen and venues visited.

Beneath that top section is the user’s full history of concert attendance displayed in a jQuery DataTable. This allowed for the inclusion of features, such as Filtering, Multi-Column Sorting and Pagination (both quantity of records displayed/page, along with the ability to toggle between pages of the table, if applicable).

Clicking any concert in the table will trigger a modal displaying the associated setlist (more detail on setlist modals below).

Finally, the last column of the table includes a “REMOVE SHOW” button, allowing users to delete a concert from their ISIL History if it was not a show they attended, or if they just choose to not include it. As a fail-safe for accidental clicking of this button, a confirmation modal is triggered first, requiring a user to either confirm or cancel the request to remove the concert from their history. If they confirm the removal, a POST request is made to the /removeShow route (see “CONTROLLER” section), index.html is then reloaded, including flashing an alert message at the top of the screen, confirming that the concert has been removed.

### **login.html**
![I SAW IT LIVE INDEX PAGE](https://github.com/champ98nyy/I_SAW_IT_LIVE__Flask_Web_App/blob/master/static/ISIL_Login_01.gif "I SAW IT LIVE INDEX PAGE")

Supporting both “GET” and “POST” methods of the /login route (see “CONTROLLER” section), login.html inherits the structure of layout.html and serves as the initial gatekeeper of I SAW IT LIVE, given all other routes (besides /register) first require a user to be logged-in before accessing.

In addition to allowing existing users to log in to their account, this view also provides non-members with an overview description of I SAW IT LIVE in order to pique their interest and lead them to click through to register for an account.

The fullscreen video background of a concert-goer’s POV of a band performing onstage, plays off of the more abstract icon of the same POV being used as the background of the Username/Password Log in form.  The background video is filtered through a partially opaque black layer, to ensure the main content of the page still pops.

### **register.html**
![I SAW IT LIVE REGISTRATION PAGE](https://user-images.githubusercontent.com/78568826/153443621-f7931c93-8a04-4cf4-b832-7cde460671c1.png "I SAW IT LIVE REGISTRATION PAGE")
Supporting both “GET” and “POST” methods of the /register route (see “CONTROLLER” section), register.html inherits the structure of layout.html and allows new users to register for an I SAW IT LIVE account.

### **search.html**
![I SAW IT LIVE SEARCH PAGE](https://github.com/champ98nyy/I_SAW_IT_LIVE__Flask_Web_App/blob/c2b0c2a68ab428edcfd7f9a30ba21dc96bf9a604/static/ISIL_Search_01.gif "I SAW IT LIVE SEARCH PAGE")
While the /search route (see “CONTROLLER section) supports both “GET” and “POST” methods, a user will be served the search.html view if they reach the route via “GET” request (see searched.html for “POST” requests).

This view inherits the structure of layout.html and serves as the main destination for users to search for, then add concerts to their ISIL History. Users input the name of the artist/band they would like to search for, triggering a “POST” request method on the /search route and sending the user to the searched.html view for the results.

### **searched.html**
![I SAW IT LIVE SEARCH RESULTS PAGE](https://github.com/champ98nyy/I_SAW_IT_LIVE__Flask_Web_App/blob/c2b0c2a68ab428edcfd7f9a30ba21dc96bf9a604/static/ISIL_Searched_01.gif "I SAW IT LIVE SEARCH RESULTS PAGE")
While search.html is responsible for serving users a location in which to search for concerts, searched.html inherits the structure of layout.html and plays the complementary role of displaying said search results. At the top of the page is a miniature recurrence of the previous search.html functionality, allowing users to search again if the results are not what they were looking for, or if they would just like to search for another artist.

The remainder of this view closely mirrors the data table portion of index.html, housing a jQuery DataTable of every concert performed by the artist searched for. Again, Filtering, Multi-Column Sorting and Pagination functionality are built into the table.

Clicking any concert in the table will trigger a modal displaying the associated setlist (more detail on setlist modals below).

The “REMOVE SHOW” button from the ISIL History table is replaced by an “ADD SHOW” button, allowing users to add the concert to their ISIL History. As a fail-safe for accidental clicking of this button, a confirmation modal is triggered first, requiring a user to either confirm or cancel the request to add the concert to their history. If they confirm the addition, a POST request is made to the /addShow route (see “CONTROLLER” section), and the user is returned to index.html where an alert message is flashed at the top of the screen, confirming that the concert has been added.

### **experience.html**
![I SAW IT LIVE EXPERIENCE DASHBOARD PAGE MILESTONE DATES](https://github.com/champ98nyy/I_SAW_IT_LIVE__Flask_Web_App/blob/41d2e7667555f1692b727a0bdc6ce1914ed9ffe6/static/ISIL_XD_01.gif "I SAW IT LIVE EXPERIENCE DASHBOARD PAGE MILESTONE DATES")
Supporting the “GET” method only, experience.html inherits the structure of layout.html and serves as the user’s statistical data dashboard.
Jinja variables and expressions are leveraged to dynamically display 17 separate statistical cards across 4 categories.

Each statistical card leverages Bootstrap 5.0’s card component, and the “Top 5” cards, each of which include a button to see more, will trigger a Bootstrap Offcanvas via JavaScript.

Control Structures were also added to each of the “Top 5” cards, in order to handle scenarios in which a user has not yet added enough concerts to necessitate an Offcanvas to display the full results. In those instances, the button to view more will not be displayed.

Additionally, Jinja mathematical operators were leveraged in order to calculate the difference between the total quantity of results of a statistical category and the top 5 results already being displayed in the card. This allowed for the buttons within the “Top 5” cards to dynamically display the quantity of additional results available by clicking on the button (e.g. a user has attended concerts at 14 unique venues, 5 of which are listed in their “Top 5 Venues Visited” card. Therefore, the button to trigger the Offcanvas would say, “9 More” (14 - 5)).

#### MILESTONE DATES
* 1st Concert
    * Date, Artist Name(s), Venue Name, Venue Location associated with the first concert (by date) the user attended
* Time Since First Concert
    * The length of time that has passed since the 1st concert took place, displayed in years/days
    * Jinja Control Structure used to only display “Days” if less than a year has passed
* Most Recent Concert
    * Date, Artist Name(s), Venue Name, Venue Location associated with the most recent concert (by date) the user attended
* Time Since Last Concert
    * The length of time that has passed since the most recent concert took place, displayed in years/days
    * Jinja Control Structure used to only display “Days” if less than a year has passed

#### PERFORMANCES + ARTISTS
![I SAW IT LIVE EXPERIENCE DASHBOARD PAGE PERFORMANCES + ARTISTS](https://github.com/champ98nyy/I_SAW_IT_LIVE__Flask_Web_App/blob/41d2e7667555f1692b727a0bdc6ce1914ed9ffe6/static/ISIL_Artists.gif "I SAW IT LIVE EXPERIENCE DASHBOARD PAGE PERFORMANCES + ARTISTS")
* Concerts Attended
    * Total quantity of concerts the user has attended
    * As indicated in the notes above this section of statistical cards, a “Concert” is defined as “1 (or more) Performance(s) by 1 (or more) Artist(s).” This handles a common scenario in which a user attends a concert with more than one act performing (e.g. an opening act performs, followed by the headline act). Although the user in this scenario would have seen 2 Performances by 2 Artists, colloquially, they attended 1 Concert, not 2
* Performances Seen
    * Total quantity of performances the user has attended
    * As indicated in the notes above this section of statistical cards, a “Performance” is defined as “A set of 1 (or more) Songs performed by an Artist at a Concert (e.g. an opening act performs, followed by the headline act). Although the user in this scenario would have only attended 1 Concert, they would have seen 2 Performances by 2 Artists. Additionally, if a user has seen the same artist perform on multiple occasions, each one would count towards this total
* Unique Artists Seen
    * Total quantity of Artists the user has seen perform live at least once
    * If a user has seen the same Artist perform on multiple occasions, only the first occurrence would count towards this total
* Top 5 Artists Seen
    * The top 5 artists the user has seen the highest quantity of live performances by
    * If the user has attended live performances by more than 5 unique artists, a button will be added within this card, indicating how many more unique artists they have seen live. Clicking the button will trigger an OffCanvas, which displays a table of every artist the user has seen perform live and the total quantity of performances the user has attended for each artist.
        * At the bottom of the OffCanvas, is another button that will bring the user to search.html to search for additional concerts to add to their ISIL History. This was included here because it’s a natural next step to take if a user has just read through the entire list of artists they have ever seen perform live, and realizes that somebody is missing from the list

#### SONGS
![I SAW IT LIVE EXPERIENCE DASHBOARD PAGE SONGS](https://github.com/champ98nyy/I_SAW_IT_LIVE__Flask_Web_App/blob/41d2e7667555f1692b727a0bdc6ce1914ed9ffe6/static/ISIL_Songs.gif "I SAW IT LIVE EXPERIENCE DASHBOARD PAGE SONGS")
* Total Songs Heard
    * Total quantity of songs the user has heard live at all of the concerts they have attended
    * As indicated in the notes above this section of statistical cards, repeat songs are counted. That means that if a user has heard the same song performed by the same artist at more than one concert, each instance would count towards this total
    * This quantity is inclusive of songs heard both during a main set and as part of an encore
* Unique Songs Heard
    * Total quantity of songs the user has heard live at least once at all of the concerts they have attended
    * As indicated in the notes above this section of statistical cards, repeat songs are NOT counted. That means that if a user has heard the same song performed by the same artist at more than one concert, only the first instance would count towards this total
    * This quantity is inclusive of songs heard both during a main set and as part of an encore
* Songs Heard As Encores
    * This statistic follows the same parameters as “Total Songs Heard” (above), except ONLY includes the songs that were played as part of an encore set, per the structure of the setlist
* Unique Songs Heard As Encores
    * This statistic follows the same premise as “Unique Songs Heard” (above), except ONLY includes the songs that were played as part of an encore set, per the structure of the setlist. Additionally, if a user has previously heard a specific song performed by an artist during a main set, then at a future concert hears the same song performed by the same artist, but as part of an encore set, the song would still count towards this statistic
* Top 5 Songs Heard
    * The top 5 songs the user has heard performed by the same artist the highest quantity of times
    * If the user has heard more than 5 unique songs performed, a button will be added within this card, indicating how many more unique songs they have heard performed live. Clicking the button will trigger an OffCanvas, which displays a table of every song the user has heard performed live and the total quantity of performances of that song the user has been in attendance for
        * At the bottom of the OffCanvas, is another button that will bring the user to search.html to search for additional concerts to add to their ISIL History. This was included here because it’s a natural next step to take if a user has just read through the entire list of songs they have ever heard performed live, and realizes that something is missing from the list

* Top 5 Songs Heard As Encores
    * This statistic follows the same premise as “Top 5 Songs Heard” (above), except ONLY includes the songs that were played as part of an encore set, per the structure of the setlist

* One additional note included at the top of this section of statistical cards, states that “Song Stats don’t include songs from (dynamically generated quantity) performances seen, which don’t have setlist information.” This accounts for the fact that not every performance in setlist.fm’s database has a corresponding setlist. It is not uncommon for older shows and/or some opening acts to be listed within the database, but not contain any information regarding the set performed
    * The quantity depends on each individual user’s history of performances attended, and is dynamically generated by the /experience route and displayed as a fraction in the following manner:
        * Total quantity of performances attended for which there is no setlist information/Total quantity of all performances attended

#### LOCATIONS
![I SAW IT LIVE EXPERIENCE DASHBOARD PAGE LOCATIONS](https://github.com/champ98nyy/I_SAW_IT_LIVE__Flask_Web_App/blob/41d2e7667555f1692b727a0bdc6ce1914ed9ffe6/static/ISIL_Locations.gif "I SAW IT LIVE EXPERIENCE DASHBOARD PAGE LOCATIONS")

* Locations Explored
    * Total quantities of Cities, States and Countries in which the user has attended at least one concert
    * If a user has attended multiple concerts in the same city/state/country, only the first occurrence would count towards these totals
* Unique Venues Visited
    * Total quantity of unique venues in which the user has attended at least one concert
    * If a user has attended multiple concerts (or multiple performances at the same concert) at the same venue, only the first occurrence would count towards this total
* Top 5 Venues Visited
    * The top 5 venues the user has attended concerts within, based on quantity
    * If the user has attended concerts at more than 5 unique venues, a button will be added within this card, indicating how many more unique venues they have been to. Clicking the button will trigger an OffCanvas, which displays a table of every venue the user has attended a concert at, and the total quantity of concerts the user has been in attendance for at that venue
        * At the bottom of the OffCanvas, is another button that will bring the user to search.html to search for additional concerts to add to their ISIL History. This was included here because it’s a natural next step to take if a user has just read through the entire list of venues in which they have ever attended a concert, and realizes that somewhere is missing from the list

### **apology.html**
![I SAW IT LIVE ERROR PAGE](https://user-images.githubusercontent.com/78568826/153454315-b32bf9aa-0e96-4a93-b47f-5c6cf56a1ddf.png "I SAW IT LIVE ERROR PAGE")
This view inherits the structure of layout.html and dynamically serves error messages and their corresponding error codes encountered by an ISIL user.

### **Modals**
Though not a standalone view like the aforementioned views above, the complexity of the setlist modals is worth noting here. As indicated above in the index.html and searched.html view explanations, each concert displayed in a user’s ISIL History (index.html) and in the results of a search (searched.html) is clickable. Doing so will toggle a modal that pops up onscreen and displays (.png file) the setlist of that particular concert.

Rather than linking to a hard-coded version of the .png file for every concert a user may encounter on ISIL, multiple methods were leveraged in order to dynamically generate the setlists on-demand:

**setlist.fm Widget**
* setlist.fm offers a customizable setlist widget tool which serves as the foundation for the setlist modals on ISIL. Within the setlist generator widget users can choose the Font, Font Size, Font Color, Background Color and Border Color for which to display a chosen setlist in.
* After making final choices, the HTML code to share/embed the setlist is provided
![setlist.fm Widget Code Example](https://user-images.githubusercontent.com/78568826/153436263-396b0c3c-aff2-4c7e-859d-f1be05e7d973.png "setlist.fm Widget Code Example")
* The end result looks like this

![setlist.fm Setlist Widget Example](https://user-images.githubusercontent.com/78568826/153436318-1cd9f4f7-d66e-41a3-8b67-869501047cfb.png "setlist.fm Setlist Widget Example")
* Back on the I SAW IT LIVE end, the HTML code written for the setlist modal was done so in a template-fashion, leaving placeholder values for the `<a href>`, `<a title>`, `<img src>` and `<img alt>` attributes
* If the .png file of the setlist is represented by the `<img src>` value in setlist.fm’s provided HTML code, that same value needs to end up as the `<img src>` value within ISIL’s modal body HTML code.
* Additionally, there needs to be a way to temporarily store the `<a href>` and `<a title>` values so that the setlist displayed within ISIL will lead the user to setlist.fm’s corresponding page if a user clicks on the .png of the setlist once it is displayed in modal, as well as the `<img alt>` value so accessibility compliance is maintained (e.g. `<img alt>`, `<a title>` values)
* Finally, the setlist.fm setlistId value is needed so that if a user clicks to add the concert to their ISIL History from within the open setlist modal, the /addShow route has a setlistId to reference
* This was achieved by leveraging `data-*` attributes to store custom data attributes. This is first done by passing values over when the data table is initially populated with rows representing the concerts. While only one Jinja variable was needed to display the corresponding value of each column of each row in the table (e.g. `{{ concert.date }}`, `{{ concert.artist }}`, etc.), additional Jinja variables were utilized to access and collect values for the following data-attributes:
    * `data-bs-setlistId`
    * `data-bs-url`
    * `data-bs-setlistUrl`
    * `data-bs-artist`
    * `data-bs-date`
    * `data-bs-venue`
* Additionally, to connect the rows to the modal whenever a row is clicked on, the following data-attributes were also included:
    * `data-bs-toggle=“modal”`
    * `data-bs-target=“#setlistModal”` (this is the id of the setlist modal template element
* Now, every concert row was ready to alter the contents displayed in the setlist modal, if a user chose to click on it, but the final piece to the puzzle is a block of JavaScript that gets triggered when a user clicks on a concert row. At that point, the image URL, setlist URL, Setlist Id, Artist Name, Date of Concert, Venue Name/City/State/Country corresponding with the data-attributes of the row, are all referenced and stored within the JS function. Then, each of the necessary data-attributes of the modal element in the HTML code are updated with the corresponding values just collected, and the correct setlist image is displayed within the modal on the user’s screen
* This process is repeated every time another concert row is clicked
![ISIL Setlist Modal Code Process Map"](https://user-images.githubusercontent.com/78568826/153437566-f6cc4877-903a-4715-9191-67a35fbfb24a.png "ISIL Setlist Modal Code Process Map")

## **CONTROLLER**

### **application.py**
The main controller of I SAW IT LIVE, application.py imports the modules that ISIL is dependent upon, and is responsible for initializing and configuring both the app as well as the ISIL database. It also handles the vast majority of backend logic, including all of the routes (besides for /apology), as well as error-handling.

#### Routes
#### **/**
* This route connects with the index.html view
* After validating that a user is logged in to their ISIL account, the index( ) function within the route is responsible for retrieving information from isil.db about the user, as well as all of the concerts they have attended in order to populate the user’s ISIL History table with the correct information.
* The function will also determine the values to display within the statistical cards at the top of the page (Concerts, Artists, Venues)


#### **/experience**
* This route connects with the experience.html view
* After validating that a user is logged in to their ISIL account, the experience( ) function within the route is responsible for retrieving information from isil.db about the user, as well as performing all of the statistical calculations that are displayed in the user’s Experience Dashboard.


#### **/register**
* This route connects with the register.html view
* The register( ) function within the route is responsible for accepting the user’s inputs in the registration form, validating each of them (all form fields filled out, username doesn’t already exist in isil.db, password and password confirmation match), then if all validations are successful, adding a new record into the users table of isil.db
Werkzeug’s generate_password_hash( ) function is used to hash the user’s selected password  with the pbkdf2:sha256 method of encryption and a salt length of 8


#### **/login**
* This route connects with the login.html view
* The login( ) function within the route is responsible for accepting the user’s inputs in the log in form, validating each of them (all form fields filled out, username exists in isil.db and password matches the hashed password in isil.db), then if all validations are successful, logging the user into I SAW IT LIVE
* Additionally, before doing anything else, the login( ) function will clear any existing session data to allow for the new user to log in. Then, the final step of the function, before redirecting the user to the index page, is to create a new session referencing the user’s id from the users table of isil.db. This session info ensures that all activity made by the user gets associated with their records within the database


#### **/logout**
* This route connects with the login.html view
* The logout( ) function, triggered by clicking “Log Out” in the navbar on any page of I SAW IT LOIVE, is responsible for ending the user’s session and disconnecting from I SAW IT LIVE. The function clears any existing session data, returning the user to the login.html view and necessitating the user to re-enter their credentials in order to log back in and continue using ISIL


#### **/search**
* This route connects with both the search.html and searched.html views
* The search( ) function first determines the user’s id and then selects the setlistId of every concert the user has already added to their ISIL History, before actually performing the search for the artist input by the user. This step is taken in order to prevent a user from adding a concert returned in the search results to their ISIL History if it has been added previously and is still present in the isil table of isil.db. It also allows the searched.html view to replace the “ADD SHOW” button in the results table with a tickets icon, representing a concert the user has already added to their ISIL History
* In compliance with the structure of setlist.fm’s API responses, the function then determines how many pages of results will be required (setlist.fm only returns 20 results/pg and requires a single page number to be searched for each API call). From there, consecutive API calls are made, incrementing the pg number each time, until all pages have been accounted for
* All results are then parsed into a dictionary for each concert, and then passed to the searched.html view to be displayed in the search results table


#### **/addShow**
* This route is connected with the searched.html view and is triggered if a user clicks the “ADD SHOW” button for any concert found in the search results
* The addShow( ) function, with the help of 6 other custom functions from helpers.py, goes through a step-by-step process of determining whether or not the concert has already been added by the user, and if not, whether a different user has previously added it to their ISIL History. The first step is taken to prevent duplicate records of the user’s attendance of a specific concert. The second step is taken to ensure duplicate records of a concert don’t get added to isil.db
* Assuming the user hasn’t previously added the concert, nor have any other users, the concertDetails( ) function will be called to make an API call to setlist.fm and retrieve all of the pertinent details of the concert and the setlist(s). All data is then added into the respective tables of isil.db
* Because it’s possible for a concert to not yet exist within the ISIL database, but for the venue in which that concert was played to exist (added from a previous concert that also took place in the same venue), the last validation step the addShow( ) function takes is to check whether or not the venue exists within the venues table of isil.db. If not, it will be added


#### **/removeShow**
* This route is connected with the index.html view, specifically the user’s ISIL History table
* If a user wants to remove a concert from their ISIL History, clicking the “REMOVE SHOW” button in the last column of any row of the table will trigger the /removeShow route
* The corresponding setlistId (stored within a data-attribute of the button element) is then passed to the removeShow( ) function, the user’s Id is referenced from the session, and a DELETE statement is sent to isil.db in order to remove the corresponding record from the isil table
* I chose not to delete the corresponding records from the concerts, songs and venues tables as doing so would require multiple additional validating steps to be taken, in order to prevent a situation in which other users have pre-existing connections with those records, which are then severed. Additionally, by keeping the records in the table, it reduces the steps that would need to be taken by the addShow( ) function if the same user, or another were to add the same concert again

### **helpers.py**
This file takes after its namesake, by providing multiple custom functions that application.py can import and run across its routes. This was done to help keep everything organized, and to reduce the level of complication and computation taking place directly within the lines of code for each route.

The following functions live within helpers.py:

#### **apology(message, code)**
The aforementioned apology function/route generates a custom error message to be displayed if a user encounters an error along the way.

#### **login_required(f)**
This is a Flask decorator function applied to most of the routes. It requires users to be logged in to their ISIL account in order to access the corresponding route.

##### Custom Functions For Searching:
#### **show_count(search, pg_num)**
Due to the logic of setlist.fm’s own search route, ISIL needs to take additional steps in order to properly make API calls and return search results to a user.

Namely, setlist.fm is configured so that a maximum of 20 results (“1 page”) can be returned per API call. Considering the fact that most artists have played more than 20 concerts, and many have played hundreds if not thousands, receiving only 20 results at a time is less than ideal. In order to get around this restriction, I implemented a for loop function that will make consecutive API calls, first requesting the results of page 1 and then incrementing the requested page # until all concerts have been returned.

However, in order to properly set the parameters of the for loop, we first need to know how many pages of results a given artist has in setlist.fm’s database. Total pages is not a datapoint provided by setlist.fm either, but if we know the total quantity of setlists and divide it by 20 (max results/page), then round up to the nearest integer, we will have the correct quantity of pages of results for a given artist.

The show_count function accepts two parameters: the artist’s name that the user searched for and the page number, which is initiated at 1 in the /search route of application.py. Therefore, this function makes the initial call to setlist.fm’s API, and simply returns the total quantity of concert setlists available for the artist that was searched for. With that information now known, the for loop in the /search route can take over, making consecutive API calls to setlist.fm and receiving all of the pertinent information on every concert ever played by the artist.

#### **lookup(search, pg_num)**
This function takes over the search process once show_count( ) has returned the total quantity of concerts and then the total quantity of pages is calculated. From there, the lookup( ) function is run as many times as there are pages of results, each time incrementing the pg_num parameter by 1 to request the next page of results.

This function returns a .json containing key information about each concert, which the /search route then parses through, creating a dict for each concert and then passing all of the dicts through to be displayed in the search results table of the searched.html view.

##### Custom Functions For Adding/Removing A Concert From A User’s ISIL History:
Both the /addShow and /removeShow routes in application.py utilize custom functions from within helpers.py.

#### **isCoverSong(dict)**
Returns True if a song in a setlist was a cover song

#### **isEncore(dict)**
Returns True if a set in a setlist was considered an encore set

#### **concertDetails(setlistId)**
The /addShow route relies on obtaining key pieces of information about the concert a user is attempting to add, which this function will return when called upon.

Referencing the setlistId of the particular concert being added, concertDetails( ) makes an API call to setlist.fm’s database and returns the requested info.
In order to handle potential exceptions due to a concert taking place in a location that does not include a state name, or a concert is not listed as part of a specific tour by the performing artist, Try and Except statements are used for those two data points. If a KeyError is encountered, a placeholder value will be returned as to not throw an exception to the entire function.

In addition to the above functions used to acquire information about a given concert, custom functions were written to make determinations on the existence of the concert within the ISIL Database at the time of request to add. These steps are taken in order to not duplicate records of the same concerts within the ISIL Database:

#### **userAttended(setlistId, userId, db)**
The first check that takes place when a user attempts to add a concert to their ISIL History, is whether or not that user has already added the concert previously. This function will look inside the isil table of isil.db and will return True if any matches of the user’s ID and the setlist’s ID exist.

If userAttended( ) returns True, not only does it signify that the user has already added this concert to their ISIL History, but in turn, would mean that the concert information (including info on the songs played, the venue, etc.) also must already exist within isil.db. In turn, the user is notified that they have already added this concert previously, and they are returned to their ISIL History page.

If userAttended( ) returns False, then additional checks are made within the tables of isil.db to determine whether or not the concert has ever been added by a different user(concertExists( ) function) and depending on that result, if the venue has ever been added to isil.db as part of a different concert played within it (venueExists( ) function).

The userAttended( ) function is also used by the /removeShow route to first validate that a user actually attended the concert they are attempting to remove from their ISIL History. This is more of a failsafe for a front-end bug that would indicate that a user had attended a concert that the backend data doesn’t validate.

#### **concertExists(setlistId, db)**
This function will look inside the concerts table of isil.db and will return True if any matches of the setlistId exist. If it returns False, the concert will be added to the table and the /addShow route will continue on to the next check of whether or not the venue exists in isil.db already.

#### **venueExists(venueId, db)**
This function will look inside the venues table of isil.db and will return True if any matches of the venueId exist. If it returns False, the venue will be added to the table.

## REQUIREMENTS
* Python 3
* Flask
* Flask-Session
* werkzeug
* Math
* Datetime
* Time
* Collections
* Operator
* Numpy
* Bootstrap 5
* JQuery

   [Walkthrough Video]: <https://youtu.be/mmu7qPxe9-M>
   [setlist.fm user account]: <https://www.setlist.fm/signin>
   [Apply Here]: <https://www.setlist.fm/settings/api>
