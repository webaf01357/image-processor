import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from PIL import Image
import io
import boto3
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cloudflare R2 設定（GCPの環境変数から読み込む設計です）
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY")
R2_SECRET_KEY = os.getenv("R2_SECRET_KEY")
R2_ENDPOINT_URL = os.getenv("R2_ENDPOINT_URL")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME")
R2_PUBLIC_DOMAIN = os.getenv("R2_PUBLIC_DOMAIN")

s3 = boto3.client(
    's3',
    endpoint_url=R2_ENDPOINT_URL,
    aws_access_key_id=R2_ACCESS_KEY,
    aws_secret_access_key=R2_SECRET_KEY
)

class CropRequest(BaseModel):
    image_url: str
    x: float
    y: float
    width: float
    height: float
    file_name: str

@app.post("/crop")
async def crop_image(req: CropRequest):
    try:
        # 1. 画像のダウンロード [cite: 1184]
        response = requests.get(req.image_url)
        img = Image.open(io.BytesIO(response.content))

        # 2. トリミング (x, y, x+w, y+h) [cite: 1184, 1225]
        cropped_img = img.crop((req.x, req.y, req.x + req.width, req.y + req.height))

        # 3. WebPに変換して最適化 [cite: 1185, 1225]
        buffer = io.BytesIO()
        cropped_img.save(buffer, format="WEBP", quality=80)
        buffer.seek(0)

        # 4. Cloudflare R2へアップロード [cite: 1186, 1226]
        file_path = f"processed/{req.file_name}.webp"
        s3.put_object(
            Bucket=R2_BUCKET_NAME,
            Key=file_path,
            Body=buffer,
            ContentType="image/webp"
        )

        return {"url": f"{R2_PUBLIC_DOMAIN}/{file_path}"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
