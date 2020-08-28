# Air Quality -> InfluxDB Bridge

This Flask-based server accepts particulate matter/temperature/humidity data from a [sensor.community sensor](https://sensor.community/en/sensors/airrohr) and writes it to a InfluxDB instance. It also calculates the Air Quality Index (AQI) with [hrbonz/python-aqi](https://github.com/hrbonz/python-aqi).

## Requirements

This project uses Python 3. Install required dependencies with

```shell
pip install -r requirements.txt
```

## Configuration

Change the values in `app.cfg` to point to your InfluxDB instance.

## Development

Launch the app locally in development mode:

```shell
FLASK_APP=app.py FLASK_ENV=development flask run --host=0.0.0.0 --cert=adhoc --port 5443
```

## Sensor Configuration

In the *Configuration* section of your sensor:

* Set *Server* to the IP of your deployment.
* Activate *Send data to custom API* and *HTTPS*.
* Set */path* to `/upload_measurement`.
* Set *Port* to 5443.
