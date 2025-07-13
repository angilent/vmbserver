import os
import requests
import json
import logging
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("webhook_forwarder")

# Webhook配置
FORWARD_TO_WEBHOOK = os.getenv("FORWARD_TO_WEBHOOK", "false").lower() == "true"
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
WEBHOOK_TIMEOUT = int(os.getenv("WEBHOOK_TIMEOUT", 5))

def forward_to_webhook(data):
    """将传感器数据转发到配置的Webhook URL"""
    if not FORWARD_TO_WEBHOOK or not WEBHOOK_URL:
        return

    try:
        # 准备转发数据
        payload = {
            "device_id": data.device_id,
            "sensor_type": data.sensor_type,
            "value": data.value,
            "unit": data.unit,
            "timestamp": data.timestamp.isoformat() if data.timestamp else None
        }

        # 发送POST请求
        response = requests.post(
            WEBHOOK_URL,
            json=payload,
            timeout=WEBHOOK_TIMEOUT
        )

        if response.status_code in [200, 201, 202]:
            logger.info(f"数据已成功转发到Webhook: {WEBHOOK_URL}")
        else:
            logger.error(f"Webhook请求失败，状态码: {response.status_code}, 响应: {response.text}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Webhook转发请求异常: {str(e)}")
    except Exception as e:
        logger.error(f"Webhook转发处理异常: {str(e)}")