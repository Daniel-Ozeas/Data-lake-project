## Project Summary

The Sparkify is a music app that generates a lot of data about users and songs. All the data is inside a data lake in AWS S3 Bucket in .json format and the analytics team ask to data engineer prepare the data to find more insights in what songs their users are listening to.

The project consist in creates a ETL pipeline to a datalake hosted on S3. The goal was load data from S3, process it into analytics tables using Spark and, load them back to S3


## About Tables

The structure of the analytics table is a star schema format. This format can be easier to the team realize joins and rise the productivity.

#### Fact Table

1. songplays - records in log data associated with song plays i.e. records with page NextSong
    * songplay_id, start_time, user_id, level, song_id, artist_id, session_id, location, user_agent

#### Dimension Tables

2. users - users in the app
    * user_id, first_name, last_name, gender, level


3. songs - songs in music database
    * song_id, title, artist_id, year, duration


4. artists - artists in music database
    * artist_id, name, location, lattitude, longitude
    

5. time - timestamps of records in songplays broken down into specific units
    * start_time, hour, day, week, month, year, weekday

## About Files

The project have three files: 

1. etl.py - reads data from S3, processes data using Spark, and writes them back to S3

2. dl.cfg - contains AWS credentials

3. readme.md - provides a summary about the project and some decisions.
