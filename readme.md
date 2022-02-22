# Overview

This tool uses https://wheresitup.com/ to run latency tests from PoPs around the world
and optionally send the results to InfluxDB.

You will need to set the following Env Vars:

- `WHEREITSUP_CLIENT_ID`
- `WHEREITSUP_TOKEN`

Additionally, if you want to send the data to InfluxDB, you will need the following
env vars.

- `INFLUXDB_URL`
- `INFLUXDB_TOKEN`
- `INFLUXDB_ORG`
- `INFLUXDB_BUCKET`

To run the test, simply run the following command from this directory.

```python
python main.py
```

Note that the client code was obtained from https://github.com/WonderNetwork/wiuppy.
