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

MEASUREMENT_NAME = "feinstaub"


def get_aqi_category(aqi_value):
    for limits, category in AQI_CATEGORIES.items():
        if aqi_value > limits[0] and aqi_value <= limits[1]:
            return category


def transform_data(data):
    data_points = {}
    for dp in data:
        data_points[dp["value_type"]] = float(dp["value"])
    return data_points


def trigger_alerts():
    result = influx_db.query(f"SELECT AQI_category FROM {MEASUREMENT_NAME} WHERE time > now() - 15m;")
    app.logger.debug(f"Result: {result}")
    categories = [i["AQI_category"] for i in result.get_points(measurement=MEASUREMENT_NAME)]
    app.logger.debug(f"Categories: {categories}")
    if len(set(categories)) == 1:
        app.logger.debug(f"We're in one category: {categories[0]}")


@app.route("/", methods=["GET"])
def root():
    return jsonify({"name": app.name})


@app.route("/upload_measurement", methods=["POST"])
def upload_measurement():
    data = request.json
    app.logger.debug(f"Received data: {data}")
    data_points = transform_data(data["sensordatavalues"])

    node_tag = "unknown"
    if "esp8266id" in data:
        node_tag = f"esp8266-{data['esp8266id']}"
    elif "rpiid" in data:
        node_tag = f"rpi-{data['rpiid']}"

    aqi_value = float(
        aqi.to_aqi([(aqi.POLLUTANT_PM10, data_points["SDS_P1"]), (aqi.POLLUTANT_PM25, data_points["SDS_P2"])])
    )
    data_points["AQI_value"] = aqi_value
    data_points["AQI_category"] = get_aqi_category(aqi_value)

    app.logger.debug(f"Writing data: {data_points}")
    influx_db.write_points([{"fields": data_points, "tags": {"node": node_tag}, "measurement": MEASUREMENT_NAME}])

    trigger_alerts()

    return jsonify({"success": "true"})


if __name__ == "__main__":
    app.run()
