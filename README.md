# wisewheels
Insight Data Science Project

In this project, I intend to predict the end destination of a Citibike trip once the bike is picked up. The outcome is: 

* a multiclass classification model
* a website (www.wisewheels.us) that allows visitor to make interactive predictions. For more details, please visit www.wisewheels.us/story.

To quickly sum up what are behind the scene, I use the past Citibike trip [data](http://https://www.citibikenyc.com/system-data), and merge those trip data with (1) the daily weather data (for the day of the trip), (2) station information, and (3) demographic data, to build a classification model to predict the end neighborhood (out of total of 60) of a new Citibike trip.
