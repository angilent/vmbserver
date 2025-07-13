from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置数据库
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./iot_data.db")
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 数据库依赖项
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 数据模型 - 传感器数据
class SensorData(Base):
    __tablename__ = "sensor_data"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, index=True)
    sensor_type = Column(String, index=True)
    value = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    unit = Column(String, nullable=True)

# 创建数据库表
Base.metadata.create_all(bind=engine)