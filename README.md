# IoT 数据服务平台

一个使用 FastAPI 实现的本地 IoT 数据服务平台，适用于 ESP32 等设备通过 HTTP、WebSocket 或 MQTT 协议上传传感器数据，进行本地保存、查询和转发。

## ✨ 功能特点

- 🌐 **多协议支持**：HTTP、WebSocket 和 MQTT 协议上传数据
- 🧠 **本地数据存储**：使用 SQLite 数据库（支持扩展为 PostgreSQL）
- 🔄 **数据转发**：支持转发至 MQTT Broker 或 Webhook
- 📊 **实时可视化**：基于 Chart.js 的前端仪表盘
- 📚 **API 文档**：自动生成的交互式 API 文档（Swagger UI 和 ReDoc）

## 🚀 快速开始

### 前提条件

- Python 3.8+ 
- pip (Python 包管理器)
- MQTT Broker (可选，用于 MQTT 功能)

### 安装步骤

1. **克隆仓库**（如果使用版本控制）
   ```bash
   git clone <repository-url>
   cd vmbserver
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **配置环境变量**
   编辑 `.env` 文件设置相关参数，如数据库连接、MQTT 配置等
   ```
   # 数据库配置
   DATABASE_URL=sqlite:///./iot_data.db
   
   # MQTT配置
   MQTT_BROKER=localhost
   MQTT_PORT=1883
   MQTT_USERNAME=
   MQTT_PASSWORD=
   MQTT_TOPIC=iot/sensors/#
   
   # 数据转发配置
   FORWARD_TO_MQTT=true
   FORWARD_TO_WEBHOOK=false
   WEBHOOK_URL=http://example.com/webhook
   
   # 服务器配置
   SERVER_HOST=0.0.0.0
   SERVER_PORT=8000
   ```

4. **启动服务**
   ```bash
   python main.py
   ```
   或使用 uvicorn 直接运行
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

5. **访问服务**
   - 仪表盘: http://localhost:8000/static
   - API 文档: http://localhost:8000/docs 或 http://localhost:8000/redoc

## 📡 数据上传方式

### 1. HTTP POST 请求

发送 JSON 格式数据到 `/data` 端点：

```bash
curl -X POST http://localhost:8000/data \
  -H "Content-Type: application/json" \
  -d '{"device_id":"esp32_01","sensor_type":"temperature","value":25.5,"unit":"°C"}'
```

### 2. WebSocket 连接

连接到 `/ws` 端点并发送 JSON 数据：

```python
import websockets
import json
import asyncio

async def send_data():
    uri = "ws://localhost:8000/ws"
    async with websockets.connect(uri) as websocket:
        data = {
            "device_id": "esp32_01",
            "sensor_type": "humidity",
            "value": 60.2,
            "unit": "%"
        }
        await websocket.send(json.dumps(data))
        response = await websocket.recv()
        print(f"收到响应: {response}")

asyncio.get_event_loop().run_until_complete(send_data())
```

### 3. MQTT 协议

发布消息到配置的 MQTT 主题（默认：`iot/sensors/#`）：

```python
import paho.mqtt.client as mqtt
import json

client = mqtt.Client()
client.connect("localhost", 1883, 60)

data = {
    "device_id": "esp32_01",
    "sensor_type": "pressure",
    "value": 1013.25,
    "unit": "hPa"
}

client.publish("iot/sensors/esp32_01/pressure", json.dumps(data))
client.disconnect()
```

## 📊 数据查询

通过 HTTP GET 请求查询传感器数据：

```bash
# 查询所有数据
curl http://localhost:8000/data

# 按设备ID查询
curl http://localhost:8000/data?device_id=esp32_01

# 按传感器类型查询
curl http://localhost:8000/data?sensor_type=temperature

# 分页查询
curl http://localhost:8000/data?skip=0&limit=50
```

## ⚙️ 项目结构

```
vmbserver/
├── main.py              # 应用入口点
├── models.py            # 数据库模型
├── mqtt_client.py       # MQTT客户端实现
├── webhook_forwarder.py # Webhook转发功能
├── requirements.txt     # 项目依赖
├── .env                 # 环境变量配置
├── README.md            # 项目文档
├── static/
│   └── index.html       # 前端仪表盘
└── iot_data.db          # SQLite数据库文件
```

## 🔧 配置选项

所有配置都通过 `.env` 文件进行管理：

| 配置项 | 描述 | 默认值 |
|--------|------|--------|
| DATABASE_URL | 数据库连接URL | sqlite:///./iot_data.db |
| MQTT_BROKER | MQTT Broker地址 | localhost |
| MQTT_PORT | MQTT Broker端口 | 1883 |
| MQTT_USERNAME | MQTT认证用户名 | 空 |
| MQTT_PASSWORD | MQTT认证密码 | 空 |
| MQTT_TOPIC | MQTT订阅主题 | iot/sensors/# |
| FORWARD_TO_MQTT | 是否转发数据到MQTT | true |
| FORWARD_TO_WEBHOOK | 是否转发数据到Webhook | false |
| WEBHOOK_URL | Webhook目标URL | http://example.com/webhook |
| SERVER_HOST | 服务器绑定地址 | 0.0.0.0 |
| SERVER_PORT | 服务器监听端口 | 8000 |

## 📈 未来扩展

- [ ] 支持 PostgreSQL 数据库
- [ ] 添加用户认证和权限控制
- [ ] 实现数据导出功能
- [ ] 添加报警阈值设置
- [ ] 支持更多数据可视化图表

## 📄 许可证

[MIT](LICENSE)
