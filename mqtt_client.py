import paho.mqtt.client as mqtt
import os
import json
from datetime import datetime
from sqlalchemy.orm import Session
from models import SensorData, get_db
from dotenv import load_dotenv
import logging

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mqtt_client")

# MQTT配置
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "iot/sensors/#")
FORWARD_TO_MQTT = os.getenv("FORWARD_TO_MQTT", "true").lower() == "true"

class MQTTClient:
    def __init__(self):
        self.client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

        # 设置认证信息
        if MQTT_USERNAME and MQTT_PASSWORD:
            self.client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

        # 连接到MQTT broker
        try:
            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
        except Exception as e:
            logger.error(f"无法连接到MQTT Broker: {e}")

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("已连接到MQTT Broker")
            # 订阅主题
            client.subscribe(MQTT_TOPIC)
            logger.info(f"已订阅主题: {MQTT_TOPIC}")
        else:
            logger.error(f"连接失败，错误代码: {rc}")

    def on_message(self, client, userdata, msg):
        try:
            # 解析MQTT消息
            payload = json.loads(msg.payload.decode())
            logger.info(f"收到MQTT消息: {payload}")

            # 验证消息格式
            required_fields = ["device_id", "sensor_type", "value"]
            if not all(field in payload for field in required_fields):
                logger.error("MQTT消息格式不正确，缺少必要字段")
                return

            # 保存到数据库
            db: Session = next(get_db())
            db_data = SensorData(
                device_id=payload["device_id"],
                sensor_type=payload["sensor_type"],
                value=payload["value"],
                unit=payload.get("unit"),
                timestamp=datetime.utcnow()
            )
            db.add(db_data)
            db.commit()
            db.refresh(db_data)
            logger.info(f"MQTT数据已保存到数据库: {db_data.id}")

        except json.JSONDecodeError:
            logger.error("无法解析MQTT消息 payload")
        except Exception as e:
            logger.error(f"处理MQTT消息时出错: {e}")

    def on_disconnect(self, client, userdata, rc):
        if rc != 0:
            logger.warning("意外断开MQTT连接")
        # 尝试重新连接
        self.client.reconnect()

    def publish(self, topic, payload):
        """发布消息到MQTT broker"""
        if FORWARD_TO_MQTT:
            try:
                result = self.client.publish(topic, json.dumps(payload), qos=1)
                status = result[0]
                if status == 0:
                    logger.info(f"消息已发布到主题 {topic}")
                else:
                    logger.error(f"发布消息到主题 {topic} 失败")
            except Exception as e:
                logger.error(f"发布MQTT消息时出错: {e}")

    def start(self):
        """启动MQTT客户端"""
        self.client.loop_start()

    def stop(self):
        """停止MQTT客户端"""
        self.client.loop_stop()
        self.client.disconnect()

mqtt_client = MQTTClient()