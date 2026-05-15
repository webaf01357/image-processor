from fastapi import FastAPI, UploadFile, File, Form, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import boto3
import os
import requests

app = FastAPI(title="ProStore Image Processor")

# CORS設定：LIFFアプリからの通信を許可
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cloudflare R2 設定
s3 = boto3.client(
    's3',
    endpoint_url=os.getenv('R2_ENDPOINT_URL'),
    aws_access_key_id=os.getenv('R2_ACCESS_KEY'),
    aws_secret_access_key=os.getenv('R2_SECRET_KEY'),
    region_name='auto'
)

BUCKET_NAME = os.getenv('R2_BUCKET_NAME')
# 接続先のGAS URL（最新版）
GAS_URL = "https://script.google.com/macros/s/AKfycbwYCa2OjvrjniRZNX7MtdMZG2iodUbT52XoMN40CqqSwDGF7A-u7ahKPYlluNR2fMPr/exec"

@app.get("/gas-proxy")
def gas_proxy_get(api: str = Query(None), store: str = Query(None)):
    """GASからの未処理データ取得用プロキシ"""
    try:
        params = {"api": api}
        if store:
            params["store"] = store
            
        resp = requests.get(GAS_URL, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"GAS通信エラー: {str(e)}")

@app.post("/gas-proxy")
def gas_proxy_post(data: dict):
    """GASへのステータス更新用プロキシ"""
    try:
        resp = requests.post(GAS_URL, json=data, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"GAS通信エラー: {str(e)}")

@app.post("/upload")
async def upload_image(file: UploadFile = File(...), target_path: str = Form(...)):
    """R2への切り抜き済み画像アップロード"""
    try:
        file_content = await file.read()
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=target_path,
            Body=file_content,
            ContentType='image/webp' # WebP固定で最適化
        )
        return {"message": "Upload successful", "path": target_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"R2アップロードエラー: {str(e)}")

@app.get("/")
def read_root():
    return {"status": "running", "service": "image-processor"}
