import os
from dataclasses import dataclass

import wiuppy
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# Job types
FLAGS = "FLAGS"
IDENTITIES = "IDENTITIES"


@dataclass
class EnvironmentConfiguration:
    api_url: str
    environment_key: str
    identifier: str = "latencytester"

    @property
    def identities_url(self):
        return f"{self.api_url}/identities?identifier={self.identifier}"

    @property
    def flags_url(self):
        return f"{self.api_url}/flags/"

    def get_job_uri(self, job_type: str) -> str:
        return {
            IDENTITIES: self.identities_url,
            FLAGS: self.flags_url,
        }.get(job_type)


STAGING_CONFIG = EnvironmentConfiguration(
    api_url="https://edge.bullet-train-staging.win/api/v1",
    environment_key="nTmxbAMjkpGpPrbYNGWMrP",
)
PROD_CONFIG = EnvironmentConfiguration(
    api_url="https://edge.api.flagsmith.com/api/v1",
    environment_key="4vfqhypYjcPoGGu8ByrBaj",
)

TEST_LOCATIONS = [
    "newyork",
    "miami",
    "sandiego",
    "london",
    "frankfurt",
    "riga",
    "kharkiv",
    "mumbai",
    "singapore",
    "tokyo",
    "seoul",
    "sydney",
    "saopaulo",
]

wiu_client = wiuppy.WIU(
    os.getenv("WHEREITSUP_CLIENT_ID"), os.getenv("WHEREITSUP_TOKEN")
)


def main(config: EnvironmentConfiguration = PROD_CONFIG, job_type: str = FLAGS):
    job = wiuppy.Job(wiu_client)
    job.uri = config.get_job_uri(job_type)
    job.tests = ["http"]
    job.options = {"http": {"headers": f"X-Environment-Key: {config.environment_key}"}}
    job.servers = TEST_LOCATIONS

    job.submit()
    job.retrieve(poll=True)  # query the API until all the tasks are done

    complete_response = job.results.get("response").get("complete")

    print("\n\nSummary")
    print("=======\n")
    for key in complete_response:
        print(
            "%s: %s: %s"
            % (
                str(complete_response[key]["http"]["summary"][0]["responseCode"]),
                complete_response[key]["http"]["summary"][0]["timingTransfer"],
                key.title(),
            )
        )

    _send_to_influx(complete_response)


def _send_to_influx(complete_response: dict):
    # Set up InfluxDB
    url = os.getenv("INFLUXDB_URL")
    token = os.getenv("INFLUXDB_TOKEN")
    influx_org = os.getenv("INFLUXDB_ORG")
    bucket = os.getenv("INFLUXDB_BUCKET")

    if not all((url, token, influx_org, bucket)):
        return

    # Set a timeout to prevent threads being potentially stuck open due to network weirdness
    influxdb_client = InfluxDBClient(url=url, token=token, org=influx_org)
    influx_write_api = influxdb_client.write_api(write_options=SYNCHRONOUS)

    influx_points = [
        _build_influx_point(complete_response, key) for key in complete_response
    ]

    print("\n\nWriting data to InfluxDB Bucket: " + bucket)
    influx_write_api.write(bucket=bucket, org=influx_org, record=influx_points)
    print("Completed write")


def _build_influx_point(complete_response, key):
    return (
        Point("edge_latency")
        .tag("location", key)
        .field(
            "ms", float(complete_response[key]["http"]["summary"][0]["timingTransfer"])
        )
    )


if __name__ == "__main__":
    main()
