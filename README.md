# Air Quality -> InfluxDB Bridge

This Flask-based server accepts particulate matter/temperature/humidity data from a [sensor.community sensor](https://sensor.community/en/sensors/airrohr) and writes it to a InfluxDB2 instance. It also calculates the Air Quality Index (AQI) with [hrbonz/python-aqi](https://github.com/hrbonz/python-aqi).

## Requirements

This project uses Python 3. Install required dependencies with

```shell
pip install -r requirements.txt
```

## Configuration

The InfluxDB connection is configured via the environment variables `INFLUXDB_V2_URL`, `INFLUXDB_V2_TOKEN`, and `INFLUXDB_V2_ORG`. Other configuration parameters are documented in the [influxdb-client-python README](https://github.com/influxdata/influxdb-client-python#via-environment-properties).

Use `INFLUXDB_BUCKET` to configure the bucket (`db0` by default) and `INFLUXDB_MEASUREMENT` to configure the measurement name (`feinstaub` by default).

## Development

Launch the app locally in development mode and access it at <http://localhost:5000>:

```shell
export INFLUXDB_V2_URL="https://localhost:8086"
export INFLUXDB_V2_TOKEN="my-token"
export INFLUXDB_V2_ORG="my-org"
export INFLUXDB_V2_VERIFY_SSL="False"
export INFLUXDB_BUCKET="my-bucket"
export INFLUXDB_MEASUREMENT="feinstaub"
python main.py
```

If everything is configured correctly, executing `curl -X GET http://localhost:5000/info` should return a JSON object that indicates the InfluxDB client is ready.

## Deployment

```shell
docker build -t air-quality-influxdb-bridge:devel .
```

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

In the *Configuration* section of your sensor:

* Set *Server* to the IP of your deployment.
* Activate *Send data to custom API* and *HTTPS*.
* Set */path* to `/upload_measurement`.
* Set *Port* to 5443.
