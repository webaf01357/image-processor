from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import boto3
import os

app = FastAPI()

# --- ここからCORS設定を追加 ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番ではCloudflareのURLに絞るとよりセキュアです
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# --- ここまで ---

# R2の接続設定（環境変数から読み込み）
s3 = boto3.client(
    's3',
    endpoint_url=os.getenv('R2_ENDPOINT_URL'),
    aws_access_key_id=os.getenv('R2_ACCESS_KEY'),
    aws_secret_access_key=os.getenv('R2_SECRET_KEY'),
    region_name='auto'
)

BUCKET_NAME = os.getenv('R2_BUCKET_NAME')

@app.post("/upload")
async def upload_image(file: UploadFile = File(...), target_path: str = Form(...)):
    file_content = await file.read()
    
    # R2へアップロード
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
