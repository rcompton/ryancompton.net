---
layout: post
title: "Taxi Strava"
description: ""
category:
tags: ["coding"]
---
{% include JB/setup %}

{% excerpt %}

Last year @? used a FOIA request to obtain a dataset with information on the locations, times, and medallions for 173 million NYC cab rides. In this blog post we'll look through this data to see which cabs are fastest cabs are and how quickly they can get between various parts of the city.

As someone who loves biking to work but hates how taxi drivers are always trying to race (kill?) me

{% endexcerpt %}

## Data

Reddit users imjasonh and fhoffa parsed the FOIA'd data and loaded it into [a public BigQuery table]( https://bigquery.cloud.google.com/table/imjasonh-storage:nyctaxi.trip_fare ) ([another version](https://bigquery.cloud.google.com/table/nyc-tlc:yellow.trips) is also available from the NYC Taxi and Limousine Commission) The schema looks like:

![schema]({{site.url}}/assets/taxi-strava/schema.png)

As you can see, each ride has very specific details on pickup/dropoff locations as well as start/end times. I am interested in answering questions along the lines of "How fast do cabs get to the Flatiron from the Upper East Side?" which is hard to do from precise latitudes and longitudes. To rectify this I took a 6-character [geohash](https://en.wikipedia.org/wiki/Geohash) of every pickup and dropoff location. A 6-character geohash buckets together coordinates that are within 0.61km of each other which allowed me to easily aggregate popular routes. An example is shown below (image from [movable-type](http://www.movable-type.co.uk/scripts/geohash.html)):

![geohash-example]({{ site.url }}/assets/taxi-strava/geohash-example.jpg)

The actual computations were done in Javascript using <https://github.com/davetroy/geohash-js> via a BigQuery UDF.

To make things more human readable, I used the [geonames api](http://www.geonames.org/maps/us-reverse-geocoder.html#findNearestIntersection) to map the center of each bucket to an intersection. Not every geohash could be mapped to an intersection this way and those trips were dropped. Data was further cleaned by dropping trips using `(hack_license != "0") AND (hack_license != "CFCD208495D565EF66E7DFF9F98764DA")` which was observed in [a discussion](https://www.reddit.com/r/bigquery/comments/28ialf/173_million_2013_nyc_taxi_rides_shared_on_bigquery) about the dataset.

This leaves us with a dataset of 158,320,608 cab rides bucketed into 32,654 distinct start/end points.

## Results

*Note: The 999th quantile for a trip's average speed is 49.4289 mph - one trip had an average speed of 236,986,708 mph (roughly one third the speed of light). I removed any trip with average speed over 60mph from the data.*


**It takes ~20 minutes to get from 79th and York to the NYSE**

The taxi stand at East 79th Street and York Avenue has been taking residents of the Upper East Side to Wall Street since 1987. It has [4 stars on Yelp](http://www.yelp.com/biz/79th-and-york-cab-share-new-york). Each cab moves [2 or more passengers at a fare of $6]( http://www.nyc.gov/html/tlc/downloads/pdf/group_ride_commission_presentation_x90_06-18-10.pdf)

I found 252,210 trips along this route in my data. On average cabs take 20.35 minutes and move at 22.11 mph. Of course you'll go faster at 4am but most people don't start their commute until 6 or 7am:

![taxi79th]({{ site.url }}/assets/taxi-strava/taxi79th.png)

Of the 13,347 medallions only a few regularly make the trip from 79th and York to Wall Street. The most dedicated cab drove the route 234 times over the year (only 7 drove it over 100 times):

![taxi79th]({{ site.url }}/assets/taxi-strava/trips_per_medallion.png)

The top 10 most frequent cab share drivers don't go any faster than most though their average speed is more predictable (probably due to the fact that they often drive at the same time each day).
Additionally, when one uses the morning cab share they are far more likely to be picked up by a usual (especially at 5am):

![taxi79th]({{ site.url }}/assets/taxi-strava/usuals_vs_overalls.png)






{% highlight sql %}
SELECT
  pickup_street1, pickup_street2, dropoff_street1, dropoff_street2,
  trips_medallion, trips_pickup_datetime, trips_dropoff_datetime,
  ROUND(trips_avg_mph,4) AS avg_mpg,
  ROUND(trips_trip_duration_hours,4) AS num_hours
FROM
  [taxi_strava.joined_geohash_geonames]
WHERE
  trips_geohashed_dropoff = 'dr5ru2'
  AND trips_geohashed_pickup = 'dr5rvj'
{% endhighlight sql %}
