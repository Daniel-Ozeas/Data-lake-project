import configparser
from datetime import datetime
import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import udf, col
from pyspark.sql.functions import year, month, dayofmonth, hour, weekofyear, date_format, monotonically_increasing_id, dayofweek
from pyspark.sql.types import TimestampType

config = configparser.ConfigParser()
config.read('dl.cfg')

os.environ['AWS_ACCESS_KEY_ID']=config['AWS']['AWS_ACCESS_KEY_ID']
os.environ['AWS_SECRET_ACCESS_KEY']=config['AWS']['AWS_SECRET_ACCESS_KEY']


def create_spark_session():
    """
    Create a SparkSession with its packages and Hadoop ecosystem
    """
    spark = SparkSession \
        .builder \
        .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:2.7.0") \
        .getOrCreate()
    return spark

def process_song_data(spark, input_data, output_data):
    """
    spark : Spark instance created
    input_data : The path where the original data is
    output_data : The path where the data already processed will be saved
    
    The function select columns from song_data dataset in .json format and write 2 tables: songs_table and artist_table and saves them in S3
    """
    # get filepath to song data file
    song_data = input_data + 'song_data/*/*/*/*.json'
    
    # read song data file
    df = spark.read.json(song_data)

    # extract columns to create songs table
    songs_table = df.select(['song_id', 'title', 'artist_id', 'year', 'duration']).dropDuplicates(['song_id'])
    
    # write songs table to parquet files partitioned by year and artist
    songs_table.write.parquet(output_data + 'song/', mode='overwrite', partitionBy=['year', 'artist_id'])

    # extract columns to create artists table
    artists_table = df.select(['artist_id', 'artist_name', 'artist_location', 'artist_latitude', 'artist_longitude'])
    
    # write artists table to parquet files
    artists_table.write.parquet(output_data + 'artist/', mode='overwrite')


def process_log_data(spark, input_data, output_data):
    """
    spark : Spark instance created
    input_data : The path where the original data is
    output_data : The path where the data already processed will be saved
    
    The function selects columns from log_data dataset in .json format and write 3 tables: artists_table, time_table, songplays_table and saves them \
    in S3. 
    """
    
    # get filepath to log data file
    log_data = os.path.join(input_data, 'log-data/')

    # read log data file
    df = spark.read.json(log_data).drop_duplicates()
    
    # filter by actions for song plays
    df = df.filter(df.page == 'NextSong')

    # extract columns for users table    
    users_table = df.select(['userId', 'firstName', 'lastName', 'gender', 'level']).drop_duplicates()
    
    # write users table to parquet files
    users_table.write.parquet(os.path.join(output_data, 'users/'), mode='overwrite')

    # create timestamp column from original timestamp column
    get_timestamp = udf(lambda x : datetime.utcfromtimestamp(int(x)/1000), TimestampType())
    df = df.withColumn('start_time', get_timestamp('ts'))
    
    # extract columns to create time table
    time_table = df.withColumn('hour', hour('start_time'))\
        .withColumn('day', dayofmonth('start_time'))\
        .withColumn('week', weekofyear('start_time'))\
        .withColumn('month', month('start_time'))\
        .withColumn('year', year('start_time'))\
        .withColumn('weekday', dayofweek('start_time'))\
        .select('ts', 'start_time', 'hour', 'day', 'week', 'month', 'year', 'weekday')\
        .drop_duplicates()
    
    # write time table to parquet files partitioned by year and month
    time_table.write.parquet(os.path.join(output_data, 'time_table/'), mode='overwrite', partitionBy=['year', 'month'])

    # read in song data to use for songplays table
    song_df = spark.read.parquet(output_data + 'song/')
    # extract columns from joined song and log datasets to create songplays table 
    songplays_table = df.join(song_df, df.song == song_df.title, how='inner')\
                        .select(monotonically_increasing_id().alias('songplay_id'), \
                                                                col('start_time').alias('start_time'),\
                                                                col('userId').alias('user_id'),\
                                                                'level', \
                                                                'song_id', \
                                                                'artist_id', \
                                                                col('sessionId').alias('session_id'), \
                                                                'location', \
                                                                col('userAgent').alias('user_agent'))
    
    songplays_table = songplays_table\
    .join(time_table, songplays_table.start_time == time_table.start_time, how='inner') \
    .select('songplay_id', songplays_table.start_time, 'user_id', 'level', 'song_id', \
            'artist_id', 'session_id', 'location', 'user_agent', time_table['year'], time_table['month'])
    
    # write songplays table to parquet files partitioned by year and month
    songplays_table.write.parquet(os.path.join(output_data, 'songplays/'), mode='overwrite', partitionBy=['year', 'month'])


def main():
    spark = create_spark_session()
    input_data = "s3a://udacity-datalake-data/"
    output_data = "s3a://udacity-datalake-data/"
    
    process_song_data(spark, input_data, output_data)    
    process_log_data(spark, input_data, output_data)


if __name__ == "__main__":
    main()
