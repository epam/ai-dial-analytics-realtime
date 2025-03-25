# InfluxDB Buckets and Tasks for Aggregated Dashboards

This document explains how to manually create InfluxDB buckets and import Flux tasks to support the optional aggregated Grafana dashboards for AI DIAL Realtime Analytics.

> ⚠️ These steps are **not automated by the Helm chart** and must be performed manually using the InfluxDB CLI or UI.

---

## 📦 Required Buckets

| Bucket Name            | Retention Policy | Description                                                                 |
|------------------------|------------------|-----------------------------------------------------------------------------|
| `default_agg_stats`    | infinite (0s)     | Stores 6-hour aggregated statistics like token counts, price, etc.         |
| `default_agg_topic`    | infinite (0s)     | Stores topic-level aggregates (e.g., count of requests per topic).         |
| `default_agg_topic_2`  | infinite (0s)     | Stores additional topic-level metrics with different grouping logic.       |
| `default_agg_kpi`      | infinite (0s)     | Stores user/project-level KPIs such as cost and usage per time period.     |
| `default_agg_chatid`   | infinite (0s)     | Aggregates request count by `chat_id` over time.                           |
| `default_agg_month`    | infinite (0s)     | Stores monthly summaries used in monthly KPI dashboards.                   |

---

## 🧾 Bucket Creation via CLI

If you have access to the Influx CLI and are authenticated, run the following:

```bash
# Aggregated buckets
influx bucket create --name "default_agg" --retention 0s --org <your-org>
influx bucket create --name "default_agg_stats" --retention 0s --org <your-org>
influx bucket create --name "default_agg_topic" --retention 0s --org <your-org>
influx bucket create --name "default_agg_topic_2" --retention 0s --org <your-org>
influx bucket create --name "default_agg_kpi" --retention 0s --org <your-org>
influx bucket create --name "default_agg_chatid" --retention 0s --org <your-org>
influx bucket create --name "default_agg_month" --retention 0s --org <your-org>
```
Replace <your-org> with your actual InfluxDB organization (e.g. dial).

🖥️ Bucket Creation via InfluxDB UI
Log in to your InfluxDB instance.

Navigate to Data > Buckets.

Click "Create Bucket" for each of the following:

- default_agg
- default_agg_stats
- default_agg_topic
- default_agg_topic_2
- default_agg_kpi
- default_agg_chatid
- default_agg_month

Set Retention Period to infinite (or 0s) for each.

✅ After Bucket Creation
Once the buckets are created, you can import and activate the Flux tasks that populate these buckets with aggregated data.

👉 Task definitions are located in the influxdb/tasks/ folder.

## 🧠 Importing Flux Tasks into InfluxDB

The project provides pre-defined Flux tasks that perform automatic aggregation on a schedule.


### 📦 Task Files

| Task Name         | Schedule            | Description                                |
|-------------------|---------------------|--------------------------------------------|
| `aggregate_data`  | Every 6 hours       | Performs 6-hour rolling aggregations       |
| `monthly_agg`     | 1st of each month   | Computes monthly summaries and KPIs        |

---

### 📥 Importing a Task via CLI

To import a task JSON file using the `influx` CLI:

```bash
influx apply --org <your-org> --file influxdb/tasks/aggregate_data.json
influx apply --org <your-org> --file influxdb/tasks/monthly_agg.json
```
🛠 Make sure you've already authenticated via influx auth login, and replace <your-org> with your actual organization name.


You can verify successful import by listing tasks:
```bash
influx task list --org <your-org>
```