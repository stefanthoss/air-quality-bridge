#!/usr/bin/python3

import os

import aqi
from flask import Flask, jsonify, request
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS

AQI_CATEGORIES = {
    (-1, 50): "Good",
    (50, 100): "Moderate",
    (100, 150): "Unhealthy for Sensitive Groups",
    (150, 200): "Unhealthy",
    (200, 300): "Very Unhealthy",
    (300, 500): "Hazardous",
}

influxdb_bucket = os.environ.get("INFLUXDB_BUCKET", "sensors")
influxdb_measurement = os.environ.get("INFLUXDB_MEASUREMENT", "air_quality")

app = Flask(__name__)

client = InfluxDBClient.from_env_properties()
write_api = client.write_api(write_options=SYNCHRONOUS)


def transform_data(data):
    data_points = {}
    for dp in data:
        data_points[dp["value_type"]] = float(dp["value"])
    return data_points


def get_aqi_category(aqi_value):
    for limits, category in AQI_CATEGORIES.items():
        if aqi_value > limits[0] and aqi_value <= limits[1]:
            return category


@app.route("/info", methods=["GET"])
def root():
    return jsonify({"app_name": app.name, "influxdb_client": client.ready().status})


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
    write_api.write(
        bucket=influxdb_bucket,
        record=[{"measurement": influxdb_measurement, "tags": {"node": node_tag}, "fields": data_points}],
    )

    return jsonify({"success": "true"})


if __name__ == "__main__":
    app.run(host="0.0.0.0")
