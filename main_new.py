from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import uuid
import shutil
from fastapi import WebSocket, WebSocketDisconnect

app = FastAPI()

# CORS 配置（允许前端A访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 保存目录
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 静态文件访问（使返回的图片可以被访问）
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# 替换为你的公网地址（natapp）
BASE_URL = "http://e76893b6.natappfree.cc"

@app.get("/")
def read_root():
    return {"status": "backend running"}

from fastapi import WebSocket, WebSocketDisconnect
# WebSocket 连接管理器
class ConnectionManager:
    def __init__(self):
        self.active_connections = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()
# this is the WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # 不需要内容，只是等待客户端
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.post("/upload_image/")
async def upload_image(file: UploadFile = File(...)):
    # 获取扩展名
    _, ext = os.path.splitext(file.filename)
    if not ext:
        ext = ".jpg"

    # 生成唯一名称
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    # 保存文件
    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # 可访问的 URL
    image_url = f"{BASE_URL}/uploads/{filename}"

    # 向前端 B 推送消息（image_url）
    await manager.broadcast(image_url)
    
    return {
        "status": True,
        "image_url": image_url
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
