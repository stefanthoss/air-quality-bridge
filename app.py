#!/usr/bin/python3

from flask import Flask, jsonify, request
from flask_influxdb import InfluxDB
from threema.gateway import Connection
from threema.gateway.simple import TextMessage
import aqi
import asyncio


AQI_CATEGORIES = {
    (-1, 50): "Good",
    (50, 100): "Moderate",
    (100, 150): "Unhealthy for Sensitive Groups",
    (150, 200): "Unhealthy",
    (200, 300): "Very Unhealthy",
    (300, 500): "Hazardous",
}

ALERT_MESSAGES = {
    "Good": "\U0001F7E2 The air quality is good, go outside!",
    "Moderate": "\U0001F7E1 The air quality is moderate.",
    "Unhealthy for Sensitive Groups": "\U0001F7E0 The air quality is unhealthy for sensitive groups.",
    "Unhealthy": "\U0001F534 The air quality is unhealthy.",
    "Very Unhealthy": "\U0001F7E3 The air quality is very unhealthy.",
    "Hazardous": "\U0001F7E4 The air quality is hazardous.",
}

app = Flask(__name__)
app.config.from_pyfile("app.cfg")
influx_db = InfluxDB(app=app)

MEASUREMENT_NAME = "feinstaub"
THREEMA_IDENTITY = "*ABCDEFG"
THREEMA_RECIPIENTS = ["HIJKLMN", "OPQRSTU"]
THREEMA_SECRET = "SECRET"


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
    categories = [i["AQI_category"] for i in result.get_points(measurement=MEASUREMENT_NAME)]
    current_category = categories[0]

    result = influx_db.query("SELECT last(alert) FROM notifications;")
    notifications = list(result.get_points(measurement="notifications"))
    if len(notifications) == 0:
        last_category = "Good"
    else:
        last_category = notifications[0]["last"]

    if len(set(categories)) == 1 and current_category != last_category:
        influx_db.write_points([{"fields": {"alert": current_category}, "measurement": "notifications"}])
        app.logger.info(f"New alert status: {current_category}")

        asyncio.set_event_loop(asyncio.new_event_loop())
        threema_connection = Connection(
            identity=THREEMA_IDENTITY, secret=THREEMA_SECRET, verify_fingerprint=True, blocking=True
        )
        for recipient in THREEMA_RECIPIENTS:
            message = TextMessage(connection=threema_connection, to_id=recipient, text=ALERT_MESSAGES[current_category])
            message.send()
        threema_connection.close()


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
