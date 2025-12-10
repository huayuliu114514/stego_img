from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import uuid
import shutil
from fastapi import WebSocket, WebSocketDisconnect
from fastapi import Body
import base64
from io import BytesIO
from PIL import Image
import base64


app = FastAPI()

static_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
print("Static files path:", static_path)
app.mount("/static",StaticFiles(directory=static_path,html = True),name="static")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 上传目录
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 专门保存原图+隐写图的文件夹
UPLOAD_PAIR_DIR = "uploads_pair"
os.makedirs(UPLOAD_PAIR_DIR, exist_ok=True)

# 静态文件访问
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.mount("/uploads_pair", StaticFiles(directory=UPLOAD_PAIR_DIR), name="uploads_pair")

# 公网访问地址
BASE_URL = "http://e76893b6.natappfree.cc"

# @app.get("/")
# def read_root():
#     return {"status": "backend running"}

# WebSocket 管理
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

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # 等待客户端消息
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# 上传单张图片接口（保持原来的逻辑）
@app.post("/upload_image/")
async def upload_image(file: UploadFile = File(...)):
    _, ext = os.path.splitext(file.filename)
    if not ext:
        ext = ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)
    image_url = f"{BASE_URL}/uploads/{filename}"
    await manager.broadcast(image_url)
    return {"status": True, "image_url": image_url}

# 任意格式转换成jpeg
def convert_to_jpeg(image_bytes: bytes) -> bytes:
    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    buffer = BytesIO()
    img.save(buffer, format="JPEG",quality=95)
    return buffer.getvalue()

# 提取 JPEG COM 段
def extract_com_segment(jpeg_bytes: bytes) -> str | None:
    i = 0
    L = len(jpeg_bytes)
    while i < L - 1:
        if jpeg_bytes[i] == 0xFF:
            marker = jpeg_bytes[i + 1]
            if marker == 0xFE:  # COM 段
                length = jpeg_bytes[i+2] * 256 + jpeg_bytes[i+3]
                data = jpeg_bytes[i + 4 : i + 2 + length]
                try:
                    return data.decode("utf-8", errors="ignore")
                except:
                    return None
            if 0xE0 <= marker <= 0xEF or marker in [0xDB, 0xDD, 0xC4]:
                length = jpeg_bytes[i+2] * 256 + jpeg_bytes[i+3]
                i += 2 + length
            else:
                i += 2
        else:
            i += 1
    return None


def insert_com_segment_bytes(jpeg_bytes: bytes, comment_text: str) -> bytes:
    if not (jpeg_bytes[0] == 0xFF and jpeg_bytes[1] == 0xD8):
        raise ValueError("不是 JPEG 文件")

    comment_bytes = comment_text.encode("utf-8")
    length = len(comment_bytes) + 2
    com_segment = b"\xFF\xFE" + length.to_bytes(2, "big") + comment_bytes

    return jpeg_bytes[:2] + com_segment + jpeg_bytes[2:]

@app.post("/generate_stego/")
async def generate_stego(
    original_base64: str = Body(...),
    hidden_text: str = Body(...)
):
    try:
        raw_bytes = base64.b64decode(original_base64)
    except:
        return {"error": "Base64 解码失败"}
    # 转成jpeg
    jpeg_bytes = convert_to_jpeg(raw_bytes)
    try:
        stego_bytes = insert_com_segment_bytes(jpeg_bytes, hidden_text)
    except Exception as e:
        return {"error": str(e)}

    stego_base64 = base64.b64encode(stego_bytes).decode()

    return {
        "status": True,
        "stego_base64": stego_base64
    }


# 上传原图+隐写图接口，保存到 uploads_pair
@app.post("/upload_pair/")
async def upload_pair(
    original_base64: str = Body(...),
    stego_base64: str = Body(...)
):
    ori_bytes = base64.b64decode(original_base64)
    stego_bytes = base64.b64decode(stego_base64)

    ori_bytes = convert_to_jpeg(ori_bytes)

    ori_name = f"{uuid.uuid4().hex}.jpg"
    stego_name = f"{uuid.uuid4().hex}.jpg"

    ori_path = os.path.join(UPLOAD_PAIR_DIR, ori_name)
    stego_path = os.path.join(UPLOAD_PAIR_DIR, stego_name)

    with open(ori_path, "wb") as f:
        f.write(ori_bytes)
    with open(stego_path, "wb") as f:
        f.write(stego_bytes)

    ori_url = f"{BASE_URL}/uploads_pair/{ori_name}"
    stego_url = f"{BASE_URL}/uploads_pair/{stego_name}"

    hidden_text = extract_com_segment(stego_bytes)

    print("隐文（COM 段内容）:", hidden_text)

    msg = {
        "original_url": ori_url,
        "stego_url": stego_url,
        "hidden_text": hidden_text
    }
    await manager.broadcast(str(msg))

    return {
        "status": True,
        "original_url": ori_url,
        "stego_url": stego_url,
        "hidden_text": hidden_text
    }



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)



