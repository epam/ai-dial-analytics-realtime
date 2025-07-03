# InfluxDB Buckets and Tasks for Aggregated Dashboards

This document explains how to manually create InfluxDB buckets and import Flux tasks to support the optional aggregated Grafana dashboards for AI DIAL Realtime Analytics.

## 📦 Required Secrets
👉 As part of this project, the storage of values for the Organization name and the default bucket is implemented using the InfluxDB kind: Secret.
| Secret Name | Description |
|------------------------|-----------------------------------------------------------------------------|
| `org` | Stores your organization name. |
| `bucket` | Stores **`default`** bucket serves as the **primary source of raw data** for the `aggregate_data` task. |

## 📦 Required Buckets

| Bucket Name            | Retention Policy | Description                                                                 |
|------------------------|------------------|-----------------------------------------------------------------------------|
| `default_agg_stats`    | infinite (0s)     | Stores 6-hour aggregated statistics like token counts, price, etc.         |
| `default_agg_topic`    | infinite (0s)     | Stores topic-level aggregates (e.g., count of requests per topic).         |
| `default_agg_topic_2`  | infinite (0s)     | Stores additional topic-level metrics with different grouping logic.       |
| `default_agg_kpi`      | infinite (0s)     | Stores user/project-level KPIs such as cost and usage per time period.     |
| `default_agg_chatid`   | infinite (0s)     | Aggregates request count by `chat_id` over time.                           |
| `default_agg_month`    | infinite (0s)     | Stores monthly summaries used in monthly KPI dashboards.                   |

### 📦 Tasks template File
The following **Flux tasks** perform periodic aggregation of data from:

- the main **`default`** bucket (containing raw analytics data), and  
- the 6-hour aggregated buckets  

into their respective **target aggregation buckets** used for Grafana dashboards.

> 🔹 The **`default`** bucket serves as the **primary source of raw data** for the `aggregate_data` task.

| Task Name         | Schedule            | Description                                | Source Buckets                              | Target Buckets                                                                                                          |
|------------------|---------------------|--------------------------------------------|---------------------------------------------|-------------------------------------------------------------------------------------------------------------------------|
| `aggregate_data` | Every 6 hours       | Performs 6-hour rolling aggregations       | `default`                                   | `default_agg_stats`, `default_agg_topic`, `default_agg_topic_2`, `default_agg_kpi`, `default_agg_chatid`              |
| `monthly_agg`    | 1st of each month   | Computes monthly summaries and KPIs        | `default_agg_stats`, `default_agg_kpi`      | `default_agg_month`                                                                                                    |
### 📥 Creating an InfluxDB secrets via CLI
To import a template YML file using the `influx` CLI:
Secret for the store organization name:
```bash
influx secret update -k org -v <your-org> --token <your-token>
```
Secret for the store default bucket name:
```bash
influx secret update -k bucket -v <your-default-bucket-name>
```

### 📥 Importing an InfluxDB template via CLI
The project provides pre-defined Flux tasks that perform automatic aggregation on a schedule.
Once a template is imported, InfluxDB will automatically create the necessary buckets and tasks.

👉 Template definitions are located in the influxdb/tasks/ folder.

To import a template YML file using the `influx` CLI:

```bash
influx apply --org <your-org> --file influxdb/tasks/tasks_template.yml --force yes --token <your-token>
```
🛠 Make sure you've already authenticated via influx auth login, and replace <your-org> with your actual organization name.


You can verify a successful import by listing tasks:
```bash
influx task list --org <your-org> --token <your-token>
```
🛠 Make sure you've already authenticated via influx auth login, and replace <your-org> with your actual organization name.
---


