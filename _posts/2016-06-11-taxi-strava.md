---
layout: post
title: "Taxi Strava"
description: ""
category:
tags: ["coding"]
---
{% include JB/setup %}

{% excerpt %}

Last year @? used a FOIA request to obtain a dataset with information on the locations, times, and medallions for 173 million NYC cab rides. As someone who loves biking to work but hates how taxi drivers are always trying to race (kill?) me I was interested in collecting data on who the fastest cabs are and how quickly they can get between various parts of the city.

{% endexcerpt %}

## Data

Reddit users imjasonh and fhoffa parsed the FOIA'd data and loaded it into [a public BigQuery table]( https://bigquery.cloud.google.com/table/imjasonh-storage:nyctaxi.trip_fare ).  The schema looks like:

As you can see, each ride has very specific details on pickup/dropoff locations as well as start/end times. I am interested in answering questions along the lines of "How fast do cabs get to the Flatiron from the Upper East Side?" which is hard to do from precise latitudes and longitudes. To rectify this I took a 6-character [geohash](https://en.wikipedia.org/wiki/Geohash) of every pickup and dropoff location. A 6-character geohash buckets together coordinates that are within 0.61km of each other which allowed me to easily aggregate popular routes. An example is shown below (image from [movable-type](http://www.movable-type.co.uk/scripts/geohash.html)):

![geohash-example]({{ site.url }}/assets/taxi-strava/geohash-example.jpg)

The actual computations were done in Javascript using <https://github.com/davetroy/geohash-js> and a BigQuery UDF. There are a total of 32,654 buckets in my data.

To make things more human readable, I used the [geonames api](http://www.geonames.org/maps/us-reverse-geocoder.html#findNearestIntersection) to map the center of each bucket to an intersection. Not every geohash could be mapped to an intersection this way and those trips were dropped. Data was further cleaned by dropping trips using `(hack_license != "0") AND (hack_license != "CFCD208495D565EF66E7DFF9F98764DA")` which was observed in [a discussion](https://www.reddit.com/r/bigquery/comments/28ialf/173_million_2013_nyc_taxi_rides_shared_on_bigquery) about the dataset. This left me with a dataset of $158,320,608$ cab rides.

## Results


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
