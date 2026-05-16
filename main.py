from fastapi import FastAPI, UploadFile, File, Form, Query, HTTPException, Header
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
GAS_URL = "https://script.google.com/macros/s/AKfycbx1GfMHGGupmZNuVSEz9UR-L5Qui-AqkD2a6CB2vWPRfXaqY66tY2JJruIDlLA0ZuXg/exec"

def verify_line_token(authorization: str):
    """LINE Verify APIを用いたトークン検証（Phase 3のLIFF側実装に合わせて有効化）"""
    if not authorization:
        return None
    
    # 実際の検証ロジック（Phase 3でフロントエンド側がトークンを送信するようになったら有効化します）
    # headers = {"Authorization": authorization}
    # resp = requests.get("https://api.line.me/oauth2/v2.1/verify", headers=headers)
    # if resp.status_code != 200:
    #     raise HTTPException(status_code=401, detail="無効なLINEトークンです")
    # return resp.json()
    pass

@app.get("/gas-proxy")
def gas_proxy_get(api: str = Query(None), store: str = Query(None), authorization: str = Header(None)):
    """GASからの未処理データ取得用プロキシ"""
    verify_line_token(authorization)
    try:
        params = {"api": api}
        if store:
            params["store"] = store
            
        # タイムアウトを15秒→30秒に延長（GASコールドスタート対策）
        resp = requests.get(GAS_URL, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"GAS通信エラー: {str(e)}")

@app.post("/gas-proxy")
def gas_proxy_post(data: dict, authorization: str = Header(None)):
    """GASへのステータス更新用プロキシ"""
    verify_line_token(authorization)
    try:
        # タイムアウトを15秒→30秒に延長（GASコールドスタート対策）
        resp = requests.post(GAS_URL, json=data, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"GAS通信エラー: {str(e)}")

@app.post("/upload")
async def upload_image(file: UploadFile = File(...), target_path: str = Form(...), authorization: str = Header(None)):
    """R2への切り抜き済み画像アップロード"""
    verify_line_token(authorization)
    
    # MIMEタイプの厳格な検証（不正ファイル対策）
    if file.content_type not in ["image/webp", "image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="許可されていないファイル形式です")
        
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
