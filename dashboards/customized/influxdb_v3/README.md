# InfluxDB 3 Aggregation Triggers for Analytics Dashboards

This document explains how aggregated analytics tables are produced in **InfluxDB 3** using **scheduled triggers and a Python plugin**.
These aggregates are used by Grafana dashboards for AI DIAL Realtime Analytics.

---

## Database Layout

We use **two databases**:

| Database        | Purpose                                                    |
| --------------- | ---------------------------------------------------------- |
| `default`       | Stores **raw analytics events** (source of truth).         |
| `analytics_agg` | Stores **aggregated / roll-up tables** used by dashboards. |

---

## Aggregation Tables (in `analytics_agg`)

Aggregated data is written into the following **tables** (tables are created automatically on first write):

| Table Name            | Description                                                    |
| --------------------- | -------------------------------------------------------------- |
| `default_agg_stats`   | 6-hour aggregates: tokens, price, request counts, unique users |
| `default_agg_topic`   | Topic-level aggregates (request counts, tokens, price)         |
| `default_agg_topic_2` | Additional topic-level metrics with alternative grouping       |
| `default_agg_kpi`     | User / project-level KPIs (cost, usage, tokens)                |
| `default_agg_chatid`  | Request counts grouped by `chat_id`                            |
| `default_agg_month`   | Monthly roll-ups used by KPI dashboards                        |

> Tables are **schema-on-write** in InfluxDB 3 — no explicit creation step is required.

---

## Aggregation Logic Overview

All aggregation logic lives in a **single Python scheduled plugin**, structured as a small [package](./plugin/).

This plugin:

* queries raw data from the `default.analytics` table
* writes hourly and monthly roll-ups into `analytics_agg.*` tables
* supports **scheduled execution** and **manual backfills** using the same code paths

---

## Scheduled Triggers

InfluxDB 3 executes plugins via **triggers**, which can be time-based using `cron:` or `every:` specifications.

We define **two triggers**, both referencing the same plugin package.

---

### 6-Hour Aggregation Trigger

Runs at the following UTC times every day:

```txt
00:02, 06:02, 12:02, 18:02 (UTC)
```

The 2-minute offset (`02` instead of `00`) ensures that all raw data for the previous window is ingested before aggregation runs.

Trigger spec:

```txt
cron:2 0 */6 * * *
```

What it does:

* aggregates the previous 6-hour window of raw data
* window bins are aligned to 6-hour boundaries (00:00, 06:00, 12:00, 18:00) which makes the query **idempotent** and backfill straightforward
* writes results into:

  * `default_agg_stats`
  * `default_agg_topic`
  * `default_agg_topic_2`
  * `default_agg_kpi`
  * `default_agg_chatid`

Example trigger creation:

```sh
influxdb3 create trigger \
  --database default \
  --path analytics_rollups \
  --trigger-spec "cron:2 0 */6 * * *" \
  --trigger-arguments mode=hourly,raw_table=analytics,agg_database=analytics_agg,window_hours=6 \
  analytics_6h_rollups
```

---

### Monthly Aggregation Trigger

Runs at:

```txt
00:00:02 UTC on the 1st day of each month
```

The 2-minute offset (`02` instead of `00`) ensures that all raw data for the previous window is ingested before aggregation runs.

Trigger spec:

```txt
cron:2 0 0 1 * *
```

What it does:

* reads from 6-hour aggregate tables
* window bins are aligned to monthly boundaries which makes the query **idempotent** and backfill straightforward
* computes monthly totals, averages, and uniques
* writes results into `default_agg_month`

Example trigger creation:

```sh
influxdb3 create trigger \
  --database analytics_agg \
  --path analytics_rollups \
  --trigger-spec "cron:2 0 0 1 * *" \
  --trigger-arguments mode=monthly,agg_database=analytics_agg \
  analytics_monthly_rollups
```

---

## Backfill Procedure

Scheduled triggers **do not process historical data automatically**.
If you already have existing raw data, you **must backfill aggregates explicitly**.

### Built-in Backfill Support

The plugin supports two optional arguments:

* `start_time` — ISO 8601 timestamp (inclusive)
* `end_time` — ISO 8601 timestamp (exclusive)

When provided, these **override the scheduled window**.

Example (single 6-hour window):

```text
mode=hourly,
window_hours=6,
raw_table=analytics,
agg_database=analytics_agg,
start_time=2026-01-01T00:00:00Z,
end_time=2026-01-01T06:00:00Z
```

---

### Recommended Backfill Strategy

### Step 1: Disable scheduled triggers

```sh
influxdb3 update trigger analytics_6h_rollups --disable
```

### Step 2: Backfill in deterministic 6-hour windows

* Run the plugin repeatedly for each window
* Windows must not overlap
* Use the same plugin and logic as production

Typical approaches:

* one-off Kubernetes Job
* admin CLI loop
* temporary high-frequency trigger

### Step 3: Re-enable scheduled triggers

```bash
influxdb3 update trigger analytics_6h_rollups --enable
```

Because:

* each aggregate point is written with a deterministic timestamp
* tags uniquely identify the aggregation dimensions

👉 **Re-running the same window is safe and idempotent.**

---

## Validation

After triggers are enabled:

* Query `analytics_agg.default_agg_stats` to confirm 6-hour data
* Query `analytics_agg.default_agg_month` after the first month boundary
* Verify Grafana dashboards point to `analytics_agg` tables
