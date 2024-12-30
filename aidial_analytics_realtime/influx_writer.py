import os
from logging import Logger
from typing import Awaitable, Callable, Tuple

from influxdb_client import Point
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync

from aidial_analytics_realtime.utils.log_config import with_prefix
from aidial_analytics_realtime.utils.timer import Timer

InfluxWriterAsync = Callable[[Logger, Point], Awaitable[None]]


def create_influx_writer() -> Tuple[InfluxDBClientAsync, InfluxWriterAsync]:
    influx_url = os.environ["INFLUX_URL"]
    influx_api_token = os.environ.get("INFLUX_API_TOKEN")
    influx_org = os.environ["INFLUX_ORG"]
    influx_bucket = os.environ["INFLUX_BUCKET"]

    client = InfluxDBClientAsync(
        url=influx_url, token=influx_api_token, org=influx_org
    )
    influx_write_api = client.write_api()

    async def influx_writer_impl(logger: Logger, record: Point):
        with Timer(with_prefix(logger, "[influx]").debug):
            await influx_write_api.write(bucket=influx_bucket, record=record)

    return client, influx_writer_impl
