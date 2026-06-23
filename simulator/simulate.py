import time
import random
import json
import logging
from datetime import datetime
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# ??? Logging setup ???????????????????????????????????????????
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

# ??? Configuration ???????????????????????????????????????????
MQTT_BROKER   = "mosquitto"
MQTT_PORT     = 1883
MQTT_TOPIC    = "iot/sensors"

INFLUX_URL    = "http://influxdb:8086"
INFLUX_TOKEN  = "my-secret-token"
INFLUX_ORG    = "iot-org"
INFLUX_BUCKET = "iot-bucket"

INTERVAL_SEC  = 5   # how often to send data (seconds)

# ??? Sensor simulation ???????????????????????????????????????
def get_sensor_readings():
    return {
        "temperature": round(random.uniform(20.0, 35.0), 2),
        "humidity":    round(random.uniform(40.0, 80.0), 2),
        "pressure":    round(random.uniform(1000.0, 1025.0), 2),
        "timestamp":   datetime.utcnow().isoformat()
    }

# ??? MQTT callbacks ??????????????????????????????????????????
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        log.info("Connected to Mosquitto broker")
    else:
        log.error(f"Failed to connect to MQTT broker, code: {rc}")

# ??? InfluxDB writer ?????????????????????????????????????????
def write_to_influx(influx_write_api, readings):
    point = (
        Point("sensor_data")
        .tag("location", "jetson-simulator")
        .field("temperature", readings["temperature"])
        .field("humidity",    readings["humidity"])
        .field("pressure",    readings["pressure"])
    )
    influx_write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
    log.info(f"Written to InfluxDB: {readings}")

# ??? Main loop ???????????????????????????????????????????????
def main():
    # Setup MQTT
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect

    log.info("Waiting for Mosquitto to be ready...")
    time.sleep(5)

    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    mqtt_client.loop_start()

    # Setup InfluxDB
    log.info("Connecting to InfluxDB...")
    influx_client = InfluxDBClient(
        url=INFLUX_URL,
        token=INFLUX_TOKEN,
        org=INFLUX_ORG
    )
    influx_write_api = influx_client.write_api(write_options=SYNCHRONOUS)

    log.info("Simulator started. Publishing every 5 seconds...")

    try:
        while True:
            readings = get_sensor_readings()

            # Publish to MQTT
            payload = json.dumps(readings)
            mqtt_client.publish(MQTT_TOPIC, payload)
            log.info(f"Published to MQTT [{MQTT_TOPIC}]: {payload}")

            # Write to InfluxDB
            write_to_influx(influx_write_api, readings)

            time.sleep(INTERVAL_SEC)

    except KeyboardInterrupt:
        log.info("Simulator stopped.")
    finally:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        influx_client.close()

if __name__ == "__main__":
    main()
