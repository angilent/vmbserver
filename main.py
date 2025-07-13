from fastapi import FastAPI, WebSocket, Depends, HTTPException
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime
import os
from dotenv import load_dotenv
import asyncio
from fastapi import FastAPI, WebSocket, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import paho.mqtt.client as mqtt
import json
from webhook_forwarder import forward_to_webhook

# 导入MQTT客户端
from mqtt_client import mqtt_client

# 导入数据库模型和配置
from models import Base, engine, SessionLocal, get_db, SensorData

# 加载环境变量
load_dotenv()

# 初始化FastAPI应用
app = FastAPI(title="IoT Data Service Platform")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic模型 - 数据接收
class SensorDataCreate(BaseModel):
    device_id: str
    sensor_type: str
    value: float
    unit: str = None

# Pydantic模型 - 数据返回
class SensorDataResponse(SensorDataCreate):
    id: int
    timestamp: datetime

    class Config:
        orm_mode = True

# 根路由
@app.get("/")
async def root():
    return {"message": "Welcome to IoT Data Service Platform", "endpoints": ["/docs", "/redoc", "/data", "/ws"]}

# HTTP接口 - 接收传感器数据
@app.post("/data", response_model=SensorDataResponse)
def create_sensor_data(data: SensorDataCreate, db: Session = Depends(get_db)):
    db_data = SensorData(**data.dict())
    db.add(db_data)
    db.commit()
    db.refresh(db_data)
    # 转发数据到Webhook
    forward_to_webhook(db_data)
    return db_data

# HTTP接口 - 查询传感器数据
@app.get("/data", response_model=List[SensorDataResponse])
def read_sensor_data(
    device_id: str = None,
    sensor_type: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(SensorData)
    if device_id:
        query = query.filter(SensorData.device_id == device_id)
    if sensor_type:
        query = query.filter(SensorData.sensor_type == sensor_type)
    return query.order_by(SensorData.timestamp.desc()).offset(skip).limit(limit).all()

# WebSocket - 实时数据推送
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # 接收WebSocket消息
            data = await websocket.receive_text()
            try:
                # 解析JSON数据
                payload = json.loads(data)
                
                # 验证必要字段
                required_fields = ["device_id", "sensor_type", "value"]
                if not all(field in payload for field in required_fields):
                    await websocket.send_text(json.dumps({
                        "status": "error", 
                        "message": "缺少必要字段: device_id, sensor_type, value"
                    }))
                    continue
                
                # 保存到数据库
                db: Session = next(get_db())
                db_data = SensorData(
                    device_id=payload["device_id"],
                    sensor_type=payload["sensor_type"],
                    value=payload["value"],
                    unit=payload.get("unit")
                )
                db.add(db_data)
                db.commit()
                db.refresh(db_data)
                
                # 转发到Webhook
                forward_to_webhook(db_data)
                
                # 返回成功响应
                await websocket.send_text(json.dumps({
                    "status": "success", 
                    "id": db_data.id,
                    "timestamp": db_data.timestamp.isoformat()
                }))
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "status": "error", 
                    "message": "无效的JSON格式"
                }))
            except Exception as e:
                await websocket.send_text(json.dumps({
                    "status": "error", 
                    "message": f"处理数据时出错: {str(e)}"
                }))
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()

# 挂载静态文件目录（用于前端仪表盘）
app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    # 启动MQTT客户端
    mqtt_client.start()
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    finally:
        # 停止MQTT客户端
        mqtt_client.stop()