# backend/app.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import os

# ========== 修改这两行 ==========
MYSQL_USER = "root"
MYSQL_PASSWORD = "123456"
# ================================

DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@localhost:3306/ai_quote?charset=utf8mb4"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 数据模型
class Favorite(Base):
    __tablename__ = "favorites"
    id = Column(Integer, primary_key=True, index=True)
    content = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# 创建表
Base.metadata.create_all(bind=engine)

# FastAPI 应用
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 接口：获取所有收藏
@app.get("/favorites")
def get_favorites(db: Session = Depends(get_db)):
    return db.query(Favorite).all()

# 接口：添加收藏
@app.post("/favorites")
def add_favorite(content: str, db: Session = Depends(get_db)):
    fav = Favorite(content=content)
    db.add(fav)
    db.commit()
    db.refresh(fav)
    return fav

# 接口：删除收藏
@app.delete("/favorites/{id}")
def delete_favorite(id: int, db: Session = Depends(get_db)):
    fav = db.query(Favorite).filter(Favorite.id == id).first()
    if not fav:
        raise HTTPException(404, "收藏不存在")
    db.delete(fav)
    db.commit()
    return {"ok": True}

@app.get("/")
def root():
    return {"message": "AI Quote API is running"}