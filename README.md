# Air Quality Bridge

This Flask-based server accepts air quality/temperature/humidity data from a [sensor.community sensor](https://sensor.community/en/sensors/airrohr) and forwards it to an InfluxDB 2.0 server or a Home Assistant instance through an MQTT broker. It also calculates the Air Quality Index (AQI) with [hrbonz/python-aqi](https://github.com/hrbonz/python-aqi).

The bridge supports receiving data from multiple air quality sensors at the same time and is configured using environment variables.

## Deployment

The Docker image from the repository gets automatically build and published to the GitHub Container Registry as [ghcr.io/stefanthoss/air-quality-bridge](https://github.com/stefanthoss/air-quality-bridge/pkgs/container/air-quality-bridge).

The best way to deploy the application is with Docker Compose. Download the `docker-compose.yml` file, change the environment variables according to your local setup, and start the Docker service with `docker-compose up`:

If your InfluxDB server doesn't use a trusted SSL certificate, you'll have to add the environment variable `INFLUXDB_V2_VERIFY_SSL=False`.

## InfluxDB Configuration

Set `ENABLE_INFLUXDB=true` to enable writing data to InfluxDB. The InfluxDB connection is configured using the environment variables `INFLUXDB_V2_URL`, `INFLUXDB_V2_TOKEN`, and `INFLUXDB_V2_ORG`. Other configuration parameters for InfluxDB are documented in the [influxdb-client-python README](https://github.com/influxdata/influxdb-client-python#via-environment-properties). Use `INFLUXDB_BUCKET` to configure the bucket (default: `sensors`) and `INFLUXDB_MEASUREMENT` to configure the measurement name (default: `air_quality`).

## Home Assistant / MQTT Integration

Set `ENABLE_MQTT=true` to enable writing data to MQTT and exposing the data as a sensor in Home Assistant. The MQTT broker is configured using the environment variables `MQTT_BROKER_URL`, `MQTT_BROKER_PORT`, `MQTT_USERNAME`, `MQTT_PASSWORD`, and `MQTT_CLIENT_ID`. Other configuration parameters for MQTT are documented in the [flask-mqtt README](https://flask-mqtt.readthedocs.io/en/latest/configuration.html#configuration-keys).

In Home Assistant, add the [MQTT integration](https://www.home-assistant.io/integrations/mqtt/) and enable *Enable newly added entities* in the integration's system options. Once the Air Quality Bridge is running and receives data, it will publish data to MQTT which Home Assistant will use to create devices and entities for the air quality sensor through MQTT's auto discovery feature.

## Sensor Configuration

In the *Configuration* / *APIs* section of your air quality sensor:

* Enable *Send data to custom API*.
* Set *Server* to the IP of your Docker deployment.
* Set *Pathth* to `/upload_measurement`.
* Set *Port* to 5000.

## Development / Non-Docker Usage

This project uses Python 3. Install the required dependencies with

```shell
pip install -r requirements.txt
```

Launch the app locally in development mode and access it at <http://localhost:5000>:

```shell
export INFLUXDB_V2_URL="https://localhost:8086"
export INFLUXDB_V2_TOKEN="my-token"
export INFLUXDB_V2_ORG="my-org"
export INFLUXDB_BUCKET="my-bucket"
export INFLUXDB_MEASUREMENT="air_quality"
export MQTT_BROKER_URL="my-mqtt-broker"
export MQTT_BROKER_PORT=1883
export MQTT_USERNAME="air-quality"
export MQTT_PASSWORD="my-password"
python main.py
```

If everything is configured correctly, executing `curl -X GET http://localhost:5000/info` should return a JSON object that indicates the InfluxDB client is ready.

If you want to build the Docker image locally, execute:

```shell
docker build -t air-quality-bridge:devel .
```

Add the environment variable `FLASK_DEBUG=1` for further debugging.

## Sample Sensor Payload

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

Use `curl -X POST -H "Content-Type: application/json" -d @test/measurement.json http://127.0.0.1:5000/upload_measurement` to use this test file locally.
