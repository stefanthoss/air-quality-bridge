#!/usr/bin/python3

import json
import os

import aqi
from flask import Flask, jsonify, request
from flask_mqtt import Mqtt
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
from waitress import serve

AQI_CATEGORIES = {
    (-1, 50): "Good",
    (50, 100): "Moderate",
    (100, 150): "Unhealthy for Sensitive Groups",
    (150, 200): "Unhealthy",
    (200, 300): "Very Unhealthy",
    (300, 500): "Hazardous",
}

app = Flask(__name__)

ENABLE_INFLUXDB = os.environ.get("ENABLE_INFLUXDB", "false").lower() == "true"
app.logger.debug(f"InfluxDB enabled: {ENABLE_INFLUXDB}")
ENABLE_MQTT = os.environ.get("ENABLE_MQTT", "false").lower() == "true"
app.logger.debug(f"MQTT enabled: {ENABLE_MQTT}")

if not ENABLE_INFLUXDB and not ENABLE_MQTT:
    app.logger.warning("No data destination configured, the bridge will not forward incoming data.")

if ENABLE_INFLUXDB:
    app.logger.info("Creating InfluxDB connection...")
    influxdb_client = InfluxDBClient.from_env_properties()
    write_api = influxdb_client.write_api(write_options=SYNCHRONOUS)
    influxdb_bucket = os.environ.get("INFLUXDB_BUCKET", "sensors")
    influxdb_measurement = os.environ.get("INFLUXDB_MEASUREMENT", "air_quality")

if ENABLE_MQTT:
    app.logger.info("Creating MQTT connection...")
    app.config["MQTT_BROKER_URL"] = os.environ.get("MQTT_BROKER_URL")
    app.config["MQTT_BROKER_PORT"] = int(os.environ.get("MQTT_BROKER_PORT", 1883))
    app.config["MQTT_USERNAME"] = os.environ.get("MQTT_USERNAME")
    app.config["MQTT_PASSWORD"] = os.environ.get("MQTT_PASSWORD")
    app.config["MQTT_CLIENT_ID"] = os.environ.get("MQTT_CLIENT_ID", "air-quality-bridge")
    mqtt = Mqtt(app)


def register_mqtt_sensor(device_name, sensor_name, device_info_dict):
    device_class = None  # https://developers.home-assistant.io/docs/core/entity/sensor/#available-device-classes
    sensor_name_readable = sensor_name
    unit_of_measurement = None
    enabled_by_default = "true"

    if sensor_name.endswith("P0"):
        device_class = "pm1"
        sensor_name_readable = "PM 1"
        unit_of_measurement = "µg/m³"
    elif sensor_name.endswith("P1"):
        device_class = "pm10"
        sensor_name_readable = "PM 10"
        unit_of_measurement = "µg/m³"
    elif sensor_name.endswith("P2"):
        device_class = "pm25"
        sensor_name_readable = "PM 2.5"
        unit_of_measurement = "µg/m³"
    elif sensor_name.endswith("temperature"):
        device_class = "temperature"
        sensor_name_readable = "Temperature"
        unit_of_measurement = "°C"
    elif sensor_name.endswith("humidity"):
        device_class = "humidity"
        sensor_name_readable = "Humidity"
        unit_of_measurement = "%"
    elif sensor_name.endswith("pressure"):
        device_class = "pressure"
        sensor_name_readable = "Pressure"
        unit_of_measurement = "Pa"
    elif sensor_name.endswith("lux"):
        device_class = "illuminance"
        sensor_name_readable = "Light"
        unit_of_measurement = "lx"
    elif sensor_name == "AQI_value":
        device_class = "aqi"
        sensor_name_readable = "AQI"
    elif sensor_name == "AQI_category":
        sensor_name_readable = "AQI Category"
    else:
        enabled_by_default = "false"

    ha_sensor_config = {
        "availability_topic": f"homeassistant/sensor/{device_name}/status",
        "device": device_info_dict,
        "enabled_by_default": enabled_by_default,
        "name": f"{device_name} {sensor_name_readable}",
        "state_class": "measurement",
        "state_topic": f"homeassistant/sensor/{device_name}/state",
        "unique_id": f"{device_name}_{sensor_name}",
        "value_template": f"{{{{ value_json.{sensor_name} }}}}",
    }
    if device_class is not None:
        ha_sensor_config["device_class"] = device_class
    if unit_of_measurement is not None:
        ha_sensor_config["unit_of_measurement"] = unit_of_measurement

    # Publish configuration
    app.logger.debug(f"Configuring MQTT sensor: {ha_sensor_config}")
    mqtt.publish(f"homeassistant/sensor/{device_name}/{sensor_name}/config", json.dumps(ha_sensor_config), retain=True)


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
def info():
    response = {"app_name": app.name}
    if ENABLE_INFLUXDB:
        response["influxdb_client"] = influxdb_client.ready().status
    return jsonify(response)


@app.route("/upload_measurement", methods=["POST"])
def upload_measurement():
    data = request.json
    app.logger.debug(f"Received data from sensor: {data}")
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
        app.logger.warn("Measurement for {node_tag} does not contain air pollutant data.")

    if aqi_value is not None:
        data_points["AQI_value"] = aqi_value
        data_points["AQI_category"] = get_aqi_category(aqi_value)

    app.logger.debug(f"Parsed and transformed data: {data_points}")

    if ENABLE_INFLUXDB:
        app.logger.debug("Writing data to InfluxDB...")
        write_api.write(
            bucket=influxdb_bucket,
            record=[{"measurement": influxdb_measurement, "tags": {"node": node_tag}, "fields": data_points}],
        )

    if ENABLE_MQTT:
        app.logger.debug("Writing data to MQTT...")

        ip_addr = request.environ.get("HTTP_X_FORWARDED_FOR", request.remote_addr)
        device_info_dict = {
            "configuration_url": f"http://{ip_addr}",
            "identifiers": node_tag,
            "manufacturer": "Sensor.Community",
            "name": f"Air Sensor {node_tag}",
            "sw_version": data["software_version"],
            "via_device": "air-quality-bridge",
        }

        # Publish HA sensor data to MQTT
        for sensor_name in data_points:
            register_mqtt_sensor(node_tag, sensor_name, device_info_dict)
        mqtt.publish(f"homeassistant/sensor/{node_tag}/status", "online")
        mqtt.publish(f"homeassistant/sensor/{node_tag}/state", json.dumps(data_points), retain=True)

    return jsonify({"success": "true"})


if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=5000)
