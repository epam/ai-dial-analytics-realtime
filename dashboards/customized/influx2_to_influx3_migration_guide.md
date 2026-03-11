# Migrating Data from InfluxDB2 to InfluxDB3

## Overview

This document describes the recommended procedure for migrating analytics data from **InfluxDB2** to **InfluxDB3**.

Only the **`default` bucket** needs to be migrated.

All other buckets contain **derived / aggregated data** and should **not be migrated**. Instead, they should be recreated using the **backfilling mode** of the [aggregation plugin](./influxdb_v3/README.md).


The migration process consists of:

1. Exporting the `default` bucket from **InfluxDB2** as **Line Protocol**
2. Splitting the export into chunks
3. Uploading the chunks in parallel to **InfluxDB3**

The instructions below assume that **InfluxDB2** is running using the Bitnami container image:

```yaml
image:
  registry: bitnamilegacy
  repository: influxdb
  tag: 2.7.11-debian-12-r20
```

In this image the storage engine resides at:

```
/bitnami/influxdb
```

---

## Migration script

```sh
set -euo pipefail

# Get the bucket id of the "default" bucket
BUCKET_ID=$(influx bucket list --org dial --json \
  | jq -r '.[] | select(.name == "default") | .id')

echo "Bucket id: ${BUCKET_ID}"

cd /tmp

# Export and split into chunks 500K datapoints each
influxd inspect export-lp \
  --bucket-id "${BUCKET_ID}" \
  --engine-path /bitnami/influxdb \
  --output-path - \
  | split -l 500000 - chunk_

# Upload chunks to InfluxDB 3 in parallel
find . -maxdepth 1 -name 'chunk_*' -print0 \
  | xargs -0 -n1 -P4 -I{} \
    curl --fail -sS \
      -X POST "${INFLUXDB3_URL}/api/v3/write_lp?db=default&precision=ns" \
      -H "Authorization: Bearer ${INFLUXDB3_TOKEN}" \
      -H "Content-Type: text/plain; charset=utf-8" \
      --data-binary @{}
```
