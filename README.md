# Air Quality -> InfluxDB Bridge

This Flask-based server accepts particulate matter/temperature/humidity data from a [sensor.community sensor](https://sensor.community/en/sensors/airrohr) and writes it to a InfluxDB instance. It also calculates the Air Quality Index (AQI) with [hrbonz/python-aqi](https://github.com/hrbonz/python-aqi).

## Requirements

This project uses Python 3. Install required dependencies with

```shell
pip install -r requirements.txt
```

## Configuration

Change the values in `main.cfg` to point to your InfluxDB instance.

## Development

Launch the app locally in development mode and access it at <http://127.0.0.1:5000>:

```shell
FLASK_APP=main.py FLASK_ENV=development APP_SETTINGS=main.cfg flask run
```

## Deployment

Create a `prod.cfg` file.

```shell
docker build -t air-quality-influxdb-bridge:devel .


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
