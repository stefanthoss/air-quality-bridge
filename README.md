# Luftdaten InfluxDB Bridge

This Flask-based server accepts particulate matter/temperature/humidity data from a [luftdaten.info sensor](https://luftdaten.info/en/construction-manual) and forwards it to a InfluxDB instance.

The luftdaten.info sensor already supports writing to InfluxDB directly but that requires you to expose the InfluxDB instance to the open web if it is located in a different network.

## Requirements

This project uses Python 3. Install required dependencies with

```shell
pip install -r requirements.txt
```

## Configuration

Change `INFLUXDB_HOST` in the `app.cfg` file to point to your InfluxDB.

## Development

Launch the app:

```shell
FLASK_APP=app.py FLASK_ENV=development flask run --host=0.0.0.0 --cert=adhoc --port 5443
```
