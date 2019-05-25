# A description of how it works
It's a screen which displays the time, date, menu, any public transport disruptions and departures from nearby stops. 

##  The frontend
The layout is defined in index.html together with norefresh.css. Many elements in the html are empty and are filled or changed using javascript.

The clock in the corner is updated twice every second (because why only once?). The ```updateClock()``` function also checks how long ago things were updated. If the times haven't been updated in 30 seconds or the disruptions in 3 minutes, a small warning appears. If 3 minutes have passed since the last update of the times then the screen clears so that old information is not displayed. If it's between 20:00 and 7:00 then a notice appears that times are not updated between those times. This is to let the heroku server sleep to prevent having to pay money. >:D The date and week is updated every 15 minutes using the ```updateDate()``` function.

The ```formatTime()``` function is used for displaying the warning messages mentioned above. It's easier to read 1 hour than 3600 seconds.

```getJson()``` is the core function used for communicating with the server. It does not send requests at night unless testing mode is enabled. It uses AJAX to update the times without reloading the page. When the response has been received the ```updateScreen()``` function is called (as a callback).

```clearTables()``` does what you think it does. It clears the screen of old times and disruption so new ones can be displayed.

```updateScreen()``` first checks so the response was 200 OK then converts the json to a JS object called ```data```. (Very useful when debugging in the browser, just type ```data``` into the console to see everything received from the server) The function then calls specialised print functions and sets a timer so the times can be updated in 15 seconds.

```printDisruption()``` first checks the data if there are any disruptions. The title and description of the disruption are displayed. Two images of warning signs are set to be visible to draw attention to any disruption.

```printDepartures()``` needs the stop name and the data. The departures are displayed in a table where each line/direction get their own row. ```createElements()``` is called for each departure.

```createElements()``` creates a row with the line number, destination and minutes left for the departures. Everything using the easy to use ```document.createElement()``` function... All departures are already grouped by the server so the frontend doesn't have to do much other than displaying it.

```printMeny()``` cleares the old menu and then fills in the new stuff. It finds the right day using the Date thingy.

The page reloads every 24 hours to prevent having to refresh the page manually when something happens, like an update.

## The backend
There are 3 python files (4 incl. creds.py which is only used when testing) running it all. ```app.py``` is the main file which contains all the important bits. ```vasttrafik.py``` includes methods for communicating with the Västtrafik API and ```skolmaten.py``` the same but for, you guessed it, skolmaten.

### ```vasttrafik.py``` 
It includes 3 classes: ```Auth```, ```Reseplaneraren``` & ```TrafficSituations```. Each request needs a token which it gets from the ```Auth``` object. ```Auth``` gives out tokens and also checks the responses for errors. When the tokens expire they are renewed and the request is sent again with the new token. 

### ```skolmaten.py```
Contains the ```get_menu()``` function. You call it and it gives you this week's menu. That's it.

### ```app.py```
The main thing. This is the server which also contains the functions for the data processing. (It contains a lot of ```datetime.now(tz.gettz("Europe/Stockholm")``` but it is necessary to get the time zone right if the server is placed in another. Which it is..)

```/``` just returns the html file. ```/get_info``` is used by the JavaScript (AJAX). That's where the magic happens. It gets the departures, disruptions and the menu, puts it in a dict and turns it into JSON which is then sent to the client.

```get_async_departures()``` takes all stop IDs and sends requests to the API asynchronously so it doesn't take 3 seconds for it to send them one by one. The data is then sent to the ```format_departures()``` function so it can be put into a nicely organised dict. Each line/direction get their own dict and if a line has more than 1 departure then they are put in the same one. ```calculate_minutes()``` calculates how many minutes are left until departure as well as formatting it. Inställd when cancelled, Nu when 0 minutes left and Ca x when no real time info is available (instead using the timetable). Right before returning the array of departures it sorts it by line and destination so it's not all random.

```get_disruptions()``` first checks how long has passed since the last request. It only updates every 3 minutes because it doesn't have to be updated every 15 seconds. It calls ```get_trafficsituation()``` when it should update. If there are multiple disruptions then the server cycles between which ones it sends to the client.

```get_trafficsituation()``` gets all current disruptions from Västtrafik and then filters them. It skips all disruptions which are not classed as severe or normal. It then only saves disruptions which affect Kapellplatsen, Chalmers, Chalmersplatsen or Chalmers Tvärgata. If any of them are only at night then it is of no interest and is skipped.