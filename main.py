#!/usr/bin/python3

import json
import os

import aqi
from flask import Flask, jsonify, request
from flask_mqtt import Mqtt
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

influxdb_client = InfluxDBClient.from_env_properties()
write_api = influxdb_client.write_api(write_options=SYNCHRONOUS)

app.config["MQTT_CLIENT_ID"] = "air-quality-bridge"
app.config["MQTT_REFRESH_TIME"] = 5
mqtt = Mqtt(app)


def register_mqtt_sensor(device_name, sensor_name, sensor_sw_version):
    ha_device_class = "None"
    sensor_name_readable = sensor_name

    if sensor_name.endswith("P0"):
        ha_device_class = "pm1"
        sensor_name_readable = "PM 1"
    elif sensor_name.endswith("P1"):
        ha_device_class = "pm10"
        sensor_name_readable = "PM 10"
    elif sensor_name.endswith("P2"):
        ha_device_class = "pm25"
        sensor_name_readable = "PM 2.5"
    elif sensor_name.endswith("temperature"):
        ha_device_class = "temperature"
        sensor_name_readable = "Temperature"
    elif sensor_name.endswith("humidity"):
        ha_device_class = "humidity"
        sensor_name_readable = "Humidity"
    elif sensor_name.endswith("pressure"):
        ha_device_class = "pressure"
        sensor_name_readable = "Pressure"
    elif sensor_name.endswith("lux"):
        ha_device_class = "illuminance"
        sensor_name_readable = "Light"
    elif sensor_name == "AQI_value":
        ha_device_class = "aqi"
        sensor_name_readable = "AQI"
    elif sensor_name == "AQI_category":
        ha_device_class = "None"
        sensor_name_readable = "AQI Category"

    ha_sensor_config = {
        "availability_topic": f"air-quality/{device_name}/status",
        "device": {"identifiers": device_name, "sw_version": sensor_sw_version, "via_device": "air-quality-bridge"},
        "device_class": ha_device_class,
        "name": sensor_name_readable,
        "state_class": "measurement",
        "state_topic": f"air-quality/{device_name}/state",
        "unique_id": f"{device_name}-{sensor_name}",
        "value_template": f"{{{{ value_json.{sensor_name} }}}}",
    }

    # Publish configuration
    mqtt.publish(f"homeassistant/sensor/{device_name}/{sensor_name}/config", json.dumps(ha_sensor_config))


def publish_mqtt_values(device_name, sensor_dict):
    # Make sensor available
    mqtt.publish(f"air-quality/{device_name}/status", "online")

    # TODO: Implement


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
    return jsonify({"app_name": app.name, "influxdb_client": influxdb_client.ready().status})


@app.route("/upload_measurement", methods=["POST"])
def upload_measurement():
    data = request.json
    app.logger.debug(f"Received data: {data}")
    data_points = transform_data(data["sensordatavalues"])

    node_tag = "unknown"
    if "esp8266id" in data:
        node_tag = f"esp8266-{data['esp8266id']}"
    elif "raspiid" in data:
        node_tag = f"raspi-{data['raspiid']}"

    aqi_value = None
    if "SDS_P1" in data_points and "SDS_P2" in data_points:
        aqi_value = float(
            aqi.to_aqi([(aqi.POLLUTANT_PM10, data_points["SDS_P1"]), (aqi.POLLUTANT_PM25, data_points["SDS_P2"])])
        )
    elif "PMS_P1" in data_points and "PMS_P2" in data_points:
        aqi_value = float(
            aqi.to_aqi([(aqi.POLLUTANT_PM10, data_points["PMS_P1"]), (aqi.POLLUTANT_PM25, data_points["PMS_P2"])])
        )
    else:
        app.logger.warn("Measurement for {node_tag} does not contain pollutant data.")

    if aqi_value:
        data_points["AQI_value"] = aqi_value
        data_points["AQI_category"] = get_aqi_category(aqi_value)

    app.logger.debug(f"Writing data: {data_points}")
    write_api.write(
        bucket=influxdb_bucket,
        record=[{"measurement": influxdb_measurement, "tags": {"node": node_tag}, "fields": data_points}],
    )

    # Publish HA sensor data to MQTT
    for sensor_name in data_points:
        register_mqtt_sensor(node_tag, sensor_name, data["software_version"])
    mqtt.publish(f"air-quality/{node_tag}/status", "online")
    mqtt.publish(f"air-quality/{node_tag}/state", json.dumps(data_points))

    return jsonify({"success": "true"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, use_reloader=False)
