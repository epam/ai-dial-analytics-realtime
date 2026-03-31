import os
from typing import Awaitable, Callable, Tuple

from influxdb_client import Point
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync

from aidial_analytics_realtime.utils.env import get_env
from aidial_analytics_realtime.utils.logging import app_logger as logger
from aidial_analytics_realtime.utils.timer import Timer

InfluxWriterAsync = Callable[[Point], Awaitable[None]]


def create_influx_writer() -> Tuple[InfluxDBClientAsync, InfluxWriterAsync]:
    influx_url = get_env("INFLUX_URL")
    influx_api_token = get_env("INFLUX_API_TOKEN")

    if (bucket := os.getenv("INFLUX_BUCKET")) and (
        database := os.getenv("INFLUX_DATABASE")
    ):
        raise ValueError(
            "Both INFLUX_BUCKET and INFLUX_DATABASE env variables are set. "
            "Only one of them should be set."
        )

    if bucket:
        # InfluxDB 2 case
        influx_org = get_env("INFLUX_ORG")
        bucket_or_database = bucket
    elif database:
        # InfluxDB 3 case
        influx_org = "ignored"
        bucket_or_database = database
    else:
        raise ValueError(
            "Neither INFLUX_BUCKET nor INFLUX_DATABASE env variable is set. "
            "Only one of them should be set."
        )

    client = InfluxDBClientAsync(
        url=influx_url, token=influx_api_token, org=influx_org
    )
    influx_write_api = client.write_api()

    async def influx_writer_impl(record: Point):
        with Timer(logger.debug, format="influx {elapsed}"):
            await influx_write_api.write(
                bucket=bucket_or_database, record=record
            )

    return client, influx_writer_impl
