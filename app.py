#!/usr/bin/python3

from flask import Flask, jsonify, request
from flask_influxdb import InfluxDB
import aqi


AQI_CATEGORIES = {
    (-1, 50): "Good",
    (50, 100): "Moderate",
    (100, 150): "Unhealthy for Sensitive Groups",
    (150, 200): "Unhealthy",
    (200, 300): "Very Unhealthy",
    (300, 500): "Hazardous",
}

app = Flask(__name__)
app.config.from_pyfile("app.cfg")
influx_db = InfluxDB(app=app)


def transform_data(data):
    data_points = {}
    for dp in data:
        data_points[dp["value_type"]] = float(dp["value"])
    return data_points


def get_aqi_category(aqi_value):
    for limits, category in AQI_CATEGORIES.items():
        if aqi_value > limits[0] and aqi_value <= limits[1]:
            return category


@app.route("/", methods=["GET"])
def root():
    return jsonify({"name": app.name})


@app.route("/post", methods=["POST"])
def post():
    data = request.json
    app.logger.debug(f"Received data: {data}")
    data_points = transform_data(data["sensordatavalues"])

    aqi_value = float(
        aqi.to_aqi([(aqi.POLLUTANT_PM10, data_points["SDS_P1"]), (aqi.POLLUTANT_PM25, data_points["SDS_P2"])])
    )
    data_points["AQI_value"] = aqi_value
    data_points["AQI_category"] = get_aqi_category(aqi_value)

    app.logger.debug(f"Writing data: {data_points}")
    influx_db.write_points(
        [{"fields": data_points, "tags": {"node": f"esp8266-{data['esp8266id']}"}, "measurement": "feinstaub"}]
    )

    return jsonify({"success": "true"})


if __name__ == "__main__":
    app.run()
