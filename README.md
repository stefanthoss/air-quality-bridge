# Air Quality Bridge

This Flask-based server accepts particulate matter/temperature/humidity data from a [sensor.community sensor](https://sensor.community/en/sensors/airrohr) and writes it to a InfluxDB 2.0 server. It also calculates the Air Quality Index (AQI) with [hrbonz/python-aqi](https://github.com/hrbonz/python-aqi).

## Requirements

This project uses Python 3. Install the required dependencies with

```shell
pip install -r requirements.txt
```

## Configuration

The InfluxDB connection is configured via the environment variables `INFLUXDB_V2_URL`, `INFLUXDB_V2_TOKEN`, and `INFLUXDB_V2_ORG`. Other configuration parameters for InfluxDB are documented in the [influxdb-client-python README](https://github.com/influxdata/influxdb-client-python#via-environment-properties).

Use `INFLUXDB_BUCKET` to configure the bucket (default: `sensors`) and `INFLUXDB_MEASUREMENT` to configure the measurement name (default: `air_quality`).

## Development

Launch the app locally in development mode and access it at <http://localhost:5000>:

```shell
export INFLUXDB_V2_URL="https://localhost:8086"
export INFLUXDB_V2_TOKEN="my-token"
export INFLUXDB_V2_ORG="my-org"
export INFLUXDB_BUCKET="my-bucket"
export INFLUXDB_MEASUREMENT="air_quality"
python main.py
```

If everything is configured correctly, executing `curl -X GET http://localhost:5000/info` should return a JSON object that indicates the InfluxDB client is ready.

If you want to build the Docker image locally, execute:

```shell
docker build -t air-quality-bridge:devel .
```

## Deployment

The Docker image from the repository gets automatically build and published to the GitHub Container Registry as [ghcr.io/stefanthoss/air-quality-bridge](https://github.com/stefanthoss/air-quality-bridge/pkgs/container/air-quality-bridge).

The best way to deploy the application is with Docker Compose. Download the `docker-compose.yml` file, change the environment variables according to your local setup, and start the Docker service with `docker-compose up`:

If your InfluxDB server doesn't use a trusted SSL certificate, you'll have to add the environment variable `INFLUXDB_V2_VERIFY_SSL=False`.

## Sample Payload

From the sensor firmware version `NRZ-2020-129`:

```json
{
    "esp8266id": "9372054",
    "software_version": "NRZ-2020-129",
    "sensordatavalues": [
        {
            "value_type": "SDS_P1",
            "value": "18.83"
        },
        {
            "value_type": "SDS_P2",
            "value": "10.60"
        },
        {
            "value_type": "BME280_temperature",
            "value": "17.00"
        },
        {
            "value_type": "BME280_pressure",
            "value": "101001.28"
        },
        {
            "value_type": "BME280_humidity",
            "value": "66.66"
        },
        {
            "value_type": "samples",
            "value": "4314326"
        },
        {
            "value_type": "min_micro",
            "value": "33"
        },
        {
            "value_type": "max_micro",
            "value": "20201"
        },
        {
            "value_type": "signal",
            "value": "-46"
        }
    ]
}
```

## Sensor Configuration

In the *Configuration* section of your air quality sensor:

* Set *Server* to the IP of your deployment.
* Activate *Send data to custom API* and *HTTPS*.
* Set */path* to `/upload_measurement`.
* Set *Port* to 5443.
