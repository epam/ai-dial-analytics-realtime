DIAL Analytics – InfluxDB & Grafana Architecture Documentation

# Overview


This documentation presents the complete architecture and implementation of the DIAL Analytics platform, built on top of InfluxDB and Grafana. The solution was designed to overcome severe performance limitations in the previous setup, enabling fast, scalable, and reliable querying across various analytical dimensions such as usage behaviour, cost trends, user activity, application and project metrics, and system-level statistics.

The document covers:

All aggregated Grafana dashboards and visuals, including their data sources.

A breakdown of InfluxDB buckets, the tasks that populate them, and their structure (fields, dimensions).

A description of the aggregation logic implemented via Flux tasks that run on a recurring basis (every 6 hours, daily, or monthly).

An explanation of the hybrid query logic in dashboards like DIAL Analytics Aggregated, which dynamically selects between raw and aggregated buckets depending on time range and resolution needs.

A detailed template and process for loading historical data using Python and Flux, making it possible to backfill any of the aggregation buckets in a consistent, controlled manner.

# Grafana Dashboards and Visuals


## Dashboard: DIAL Application Insights


### Visual: Request count - Applications


- Type: barchart

- Source Bucket: default_agg_stats

### Visual: Top Models


- Type: table

- Source Bucket: default_agg_application

### Visual: Application Stats


- Type: table

- Source Bucket: default_agg_application

### Visual: Application Insights


- Type: table

- Source Bucket: default_agg_application

## Dashboard: DIAL User Insights


### Visual: Messages per Conversation


- Type: stat

- Source Bucket: default_agg_chatid

### Visual: Distribution of Cost (user/project)


- Type: piechart

- Source Bucket: default_agg_kpi

### Visual: Distribution of Requests (user/project)


- Type: piechart

- Source Bucket: default_agg_kpi

### Visual: Distribution of conversation length


- Type: barchart

- Source Bucket: default_agg_chatid

### Visual: Cost share by deciles of Users in chat


- Type: barchart

- Source Bucket: default_agg_kpi

### Visual: Cost share by deciles of Users in chat


- Type: table

- Source Bucket: default_agg_kpi

### Visual: Chat Usage by Title


- Type: table

- Source Bucket: default_agg_topic_2

### Requests share by deciles of Users in chat


- Type: barchart

- Source Bucket: default_agg_kpi

### Visual: Requests share by deciles of Users in chat


- Type: table

- Source Bucket: default_agg_kpi

### Visual: Chat Usage by Deployment/Model


- Type: table

- Source Bucket: default_agg_stats

### Visual: Distribution of messages length in tokens


- Type: barchart

- Source Bucket: default_agg_topic

### Visual: Chat Usage by Topic


- Type: table

- Source Bucket: default_agg_topic_2

### Visual: Distribution of messages length in tokens


- Type: table

- Source Bucket: default_agg_topic

### Visual: Language Stats table


- Type: table

- Source Bucket: default_agg_stats

## Dashbaord: DIAL Project Insights


### Visual: Project Stats


- Type: table

- Source Bucket: default_agg_stats

### Visual: Distribution of Requests (user/project)


- Type: piechart

- Source Bucket: default_agg_kpi

### Visual: Distribution of Cost (user/project)


- Type: piechart

- Source Bucket: default_agg_kpi

### Visual: Project/Deployment/Model Stats


- Type: table

- Source Bucket: default_agg_stats

### Visual: Deployment/Model Stats


- Type: table

- Source Bucket: default_agg_stats

### Visual: Project Requests share by deciles


- Type: barchart

- Source Bucket: default_agg_kpi

### Visual: Project Requests share by deciles


- Type: table

- Source Bucket: default_agg_kpi

### Visual: Top 10 Projects by Request count


- Type: table

- Source Bucket: default_agg_kpi

### Visual: Project Cost share by deciles


- Type: barchart

- Source Bucket: default_agg_kpi

### Visual: Project Cost share by deciles


- Type: table

- Source Bucket: default_agg_kpi

### Visual: Top 10 Projects by Cost


- Type: table

- Source Bucket: default_agg_kpi

### Visual: Distribution of messages length in tokens


- Type: barchart

- Source Bucket: default_agg_topic

### Visual: Distribution of messages length in tokens


- Type: table

- Source Bucket: default_agg_topic

### Visual: Model - Deployment mismatch


- Type: table

- Source Bucket: default_agg_stats

## Dashboard: DIAL Cost Insights


### Visual: Total Cost - Current Year Forecast ($)


- Type: stat

- Source Bucket: default_agg_kpi

### Visual: Project API Cost - Current Year Forecast ($)


- Type: stat

- Source Bucket: default_agg_kpi

### Visual: Chat Cost - Current Year Forecast ($)


- Type: stat

- Source Bucket: default_agg_kpi

### Visual: Avg Cost Per User Per Month - Current Year Forecast ($)


- Type: stat

- Source Bucket: default_agg_month

### Visual: Total Cost - Full Previous Year ($)


- Type: stat

- Source Bucket: default_agg_month

### Visual: Project API Cost - Full Previous Year ($)


- Type: stat

- Source Bucket: default_agg_month

### Visual: Chat Cost - Full Previous Year ($)


- Type: stat

- Source Bucket: default_agg_month

### Visual: Avg Cost Per User Per Month - Full Previous Year ($)


- Type: stat

- Source Bucket: default_agg_month

### Visual: Monthly Stats


- Type: table

- Source Bucket: default_agg_month

### Visual: Monthly Total User Cost and Avg Cost Per User


- Type: timeseries

- Source Bucket: default_agg_month

### Visual: Monthly Active Users and Projects


- Type: timeseries

- Source Bucket: default_agg_month

## Dashbaord: DIAL Analytics Aggregated


### Overview


This dashboard presents a comprehensive summary of aggregated platform usage metrics including user activity, topic popularity, project statistics, and system load. The core innovation lies in dynamic bucket selection, which determines whether to use the raw or aggregated data based on the selected time range. The dashboard uses variables and helper functions in Flux to maintain consistent aggregation logic.

### Bucket Selection Logic


There are two types of buckets used in this dashboard:
- `default`: contains detailed, unaggregated real-time data.
- `default_agg_*`: contains pre-aggregated data in 6-hour windows.

The logic to choose between these depends on the time window of the query. If the time range is <= 1 day (specified by `threshold_duration_ns`), only the `default` bucket is used. Otherwise, the data is split:
- the start portion (if misaligned with 6-hour intervals) comes from `default`
- the middle (fully aligned) from the aggregated bucket (e.g., `default_agg_stats`, `default_agg_topic`)
- the end portion (if misaligned) again from `default`

### Visualizations


#### Visual: Unique Users


- Type: stat

- Source Bucket: default / default_agg_stats

#### Visual: Popular Topics


- Type: magnesium-wordcloud-panel

- Source Bucket: default / default_agg_topic

#### Visual: Active Projects


- Type: stat

- Source Bucket: default_agg_stats

#### Visual: Title-Topic Heatmap


- Type: ae3e-plotly-panel

- Source Bucket: default / default_agg_topic

#### Visual: System Usage


- Type: timeseries

- Source Bucket: default / default_agg_stats

#### Visual: Stats Table


- Type: table

- Source Bucket: default / default_agg_stats

#### Visual: Project Stats Table


- Type: table

- Source Bucket: default / default_agg_stats

#### Visual: Deployment/Model Stats Table


- Type: table

- Source Bucket: default / default_agg_stats

# InfluxDB Buckets


## default_agg_stats


1. Dimensions: _time, deployment, model, project_id, parent_deployment, language, title

1. Fields: completion_tokens, number_request_messages, price, prompt_tokens, user_hash

1. Populated by Tasks: aggregate_data

## default_agg_topic


1. Dimensions: _time, title, topic

1. Fields: number_request_messages, request_count, prompt_token_class, topic_count

1. Populated by Tasks: aggregate_data

## default_agg_topic2


1. Dimensions: _time, title, topic, model

1. Fields: number_request_messages, request_count, topic_count, price, prompt_tokens, competition_tokens

1. Populated by Tasks: aggregate_data

## default_agg_kpi


1. Dimensions: _time, parent_deployment, model, project_id, user_hash,, title

1. Fields: request_count, completion_tokens, cost, prompt_tokens

1. Populated by Tasks: aggregate_data

## default_agg_chatid


1. Dimensions: _time, chat_id,

1. Fields: request_count,

1. Populated by Tasks: aggregate_data

## default_agg_application


1. Dimensions: _time, deployment, model, parent_deployment, title

1. Fields: user_request_count, api_request_count, user_hash, deployment_price, number_request_messages, price, competition_tokens, prompt_tokens

1. Populated by Tasks: aggregate_data_daily

## default_agg_month


1. Dimensions: _time,

1. Fields: Avg_Cost_Per_Model, Total_Cost_Per_Model, Avg_RC_Per_Api, Total_RC_Per_Api, Active_Apis, Avg_Cost_Per_Api, Total_Cost_Per_Api, Unique_Users, Avg_Cost_Per_User, total_user_cost

1. Populated by Tasks: monthly_agg

# InfluxDB Tasks


## Aggreaget_data


### Writes to Buckets


- default_agg_stats, default_agg_topic, default_agg_topic, default_agg_kpi, default_agg_chatid

### Description


- This Flux task runs every 6 hours to aggregate metrics from the `default` bucket.

- It computes totals of `prompt_tokens`, `completion_tokens`, `price`, and `number_request_messages`.

- Request counts are calculated using `user_hash`, and timestamps are rounded to 6-hour intervals.

- The script handles boundary corrections to avoid overlapping or dropped records.

- For per-user aggregations, the minimum `_time` per `user_hash` group is used to retain fidelity.

## aggregate_data_daily


- Schedule: Daily at 00:00

### Writes to Buckets


- default_agg_application

### Description


- Summarizes daily totals for application-level metrics, aggregating prompt_tokens, completion_tokens, and price by deployment and application. This provides high-level daily cost and usage trends.

## monthly_agg


- Schedule: 1st of each month

### Writes to Buckets


- default_agg_month

### Description


- Aggregates cost, user and request data monthly. This allows month-over-month comparison of project usage, useful for long-term trend reporting and budget forecasting.

# Historical Data Loading Template


## Overview


- This document provides a reusable template for loading historical data into InfluxDB buckets by mimicking the logic of an existing Flux task. This approach is useful when backfilling data for past time ranges, typically using Python and the InfluxDB client API.

## Use Case


- You can extract the Flux script logic from a production task and embed it into a Python string template. This enables running aggregations manually over historical time windows, and inserting the results back into target buckets using the InfluxDB Python client.

## Steps


- 1. Extract the Flux aggregation logic from the task of interest.

- 2. Replace any `{}` curly braces used in Flux maps or structs with `{{}}` to escape them in the Python f-string.

- 3. Insert `start` and `stop` placeholders using Python variables, e.g., `range(start: {start_time}, stop: {stop_time})`.

- 4. Copy the modified Flux into your Python script and use it inside a `f"""..."""` multiline string.

- 5. Loop over the historical date range and execute the Flux for each window.

- 6. Convert the result to a DataFrame and write to the target bucket.

## Template Flux Query (for f-string use in Python)


This is an example script to load historic data from default bucket to default_agg_chatid bucket covering the following time frame: 2024.02.19.  2025.02.25.


```python

from influxdb_client import InfluxDBClient, Point, WriteOptions
import pandas as pd
from datetime import datetime, timedelta

# Constants
bucket = "default" #from bucket
agg_bucket = "default_agg_chatid" #to bucket

org = "dial"
token = "your token"  # instert your token here

url = "http://localhost:8086" #make sure to run port forward in advance

# Initialize the client
client = InfluxDBClient(url=url, token=token, org=org, timeout=None)
delete_api = client.delete_api()
# Start and stop time for the first query
start_date = datetime(2025, 2, 25)
end_date = datetime(2024, 2, 19)
delta_hours = 6

# Function to delete data for a specific day # in case you’d like to overwrite data, it needs to be deleted first
def delete_data_for_day(start_time, stop_time):
    try:
        print(f"Deleting data from {start_time} to {stop_time}...")
        delete_api.delete(start=start_time, stop=stop_time, predicate='', bucket=agg_bucket, org=org) #comment this line out if there is no need for data deletion from the target bucket
        print(f"Data from {start_time} to {stop_time} deleted successfully.")
    except Exception as e:
        print(f"Error occurred while deleting data from {start_time} to {stop_time}: {e}")


# Loop for the defined time range in 6-hour blocks
while start_date > end_date:
    try:
        client = InfluxDBClient(url=url, token=token, org=org, timeout=None)
        # Set the start and stop time for each 6-hour block
        start_time = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
        stop_time = (start_date - timedelta(hours=delta_hours)).strftime("%Y-%m-%dT%H:%M:%SZ")  # Move 6 hours back
        start_time = (start_date - timedelta(seconds=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        print(start_time)
        print(stop_time)
        #delete_data_for_day(stop_time, start_time)
        # Query to get the data from the original bucket

# The query should be directly copied from the influxdb task into the f string.

#make sure to escape ‘{‘ and ‘}’ characthers in the f string
        query = f'''
        import "influxdata/influxdb/schema"
        import "experimental"

        getOrDefault = (f, d) => if exists f then f else d

        from(bucket: "{bucket}")
          |> range(start: {stop_time}, stop: {start_time})
        |> filter(
            fn: (r) =>
                r._measurement == "analytics" and (r._field == "chat_id" ),
        )

        |> schema.fieldsAsCols()
        |> group()
          |> map(fn: (r) => ({{r with request_count: 1}}))
          |> map(fn: (r) => ({{r with _floored_time: time(v: int(v: r._time) - int(v: r._time) % 21600000000000)}}))
          |> group(columns: [  "_floored_time",
                                "chat_id",
                               ])
           |> reduce(
            fn: (r, accumulator) =>
                ({{
                    request_count: getOrDefault(f: r.request_count, d: 0) + accumulator.request_count,
                }}),
            identity: {{request_count: 0}},
        )

        '''

        query_api = client.query_api()
        raw_result = query_api.query(org=org, query=query)

        # Convert FluxRecords to DataFrame
        records = []
        for table in raw_result:
            for record in table.records:
                records.append(record.values)

        if not records:
            print(f"No data found for {stop_time} to {start_time}")
        else:
            df = pd.DataFrame(records)
            print(f"Data loaded for {stop_time} to {start_time}")

            df['_time'] = df['_floored_time']

            # Write data to the aggregation bucket
            write_api = client.write_api(write_options=WriteOptions(batch_size=500, flush_interval=10_000))
            for _, row in df.iterrows():
                point = Point("analytics")
                point.time(row['_time'])

                # Add tags

                point.tag("chat_id", str(row['chat_id']))
                # Add fields with adjusted "cost"
                point.field("request_count", int(row['request_count']))
                # Write the point
                write_api.write(bucket=agg_bucket, org=org, record=point)

            # Close write API explicitly after each iteration to reduce server stress
            write_api.close()
            print(f"Data for {stop_time} to {start_time} written to InfluxDB.")

    except Exception as e:
        print(f"Error processing data for {stop_time} to {start_time}: {e}")

    finally:
        # Move to the previous 6-hour block
        start_date -= timedelta(hours=delta_hours)
        client.close()

# Close the client
client.close()
print("Process completed.")