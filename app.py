from flask import Flask, jsonify, request
from flask_influxdb import InfluxDB

app = Flask(__name__)
app.config.from_pyfile("app.cfg")
influx_db = InfluxDB(app=app)


def transform_data(data):
    data_points = {}
    for dp in data:
        data_points[dp["value_type"]] = float(dp["value"])
    return data_points


@app.route("/", methods=["GET"])
def root():
    return jsonify({"name": app.name})


@app.route("/post", methods=["POST"])
def post():
    data = request.json
    app.logger.debug(f"Received data: {data}")
    data_points = transform_data(data["sensordatavalues"])
    app.logger.debug(f"Writing data: {data_points}")
    influx_db.write_points(
        [{"fields": data_points, "tags": {"node": f"esp8266-{data['esp8266id']}"}, "measurement": "feinstaub",}]
    )

    return jsonify({"success": "true"})


if __name__ == "__main__":
    app.run()
