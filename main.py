from fastapi import FastAPI, UploadFile, File, Form, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import boto3
import os
import requests  # requirements.txtに記載済み

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

s3 = boto3.client(
    's3',
    endpoint_url=os.getenv('R2_ENDPOINT_URL'),
    aws_access_key_id=os.getenv('R2_ACCESS_KEY'),
    aws_secret_access_key=os.getenv('R2_SECRET_KEY'),
    region_name='auto'
)

BUCKET_NAME = os.getenv('R2_BUCKET_NAME')
GAS_URL = "https://script.google.com/macros/s/AKfycbyVaTM1_iXPgn0vIMTbtjrvmJDv2bBzfeJyjikUVcJM1d1XKFZrWN1FdJb75WLAOBj0/exec"

# ⚠️修正ポイント1: 'async def' ではなく 'def' にすることで、FastAPIが別スレッドで安全に処理（フリーズ回避）
@app.get("/gas-proxy")
def gas_proxy_get(api: str = Query(None)):
    try:
        resp = requests.get(GAS_URL, params={"api": api}, timeout=10) # 10秒でタイムアウト
        resp.raise_for_status() # HTTPエラー（404, 500など）を検知
        return resp.json()
    # ⚠️修正ポイント2: エラーを握りつぶさず、何が起きたかブラウザへ正確に伝える
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"GASとの通信エラー: {str(e)}")

@app.post("/gas-proxy")
def gas_proxy_post(data: dict):
    try:
        resp = requests.post(GAS_URL, json=data, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"GASとの通信エラー: {str(e)}")

@app.post("/upload")
async def upload_image(file: UploadFile = File(...), target_path: str = Form(...)):
    file_content = await file.read()
    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=target_path,
        Body=file_content,
        ContentType=file.content_type
    )
    return {"message": "Upload successful", "path": target_path}

@app.get("/")
def read_root():
    return {"status": "running"}
