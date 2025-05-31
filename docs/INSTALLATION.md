# Math Video Generator インストールガイド

## システム要件

### 必須要件

- **Python**: 3.9以上
- **Node.js**: 16以上
- **FFmpeg**: 最新版
- **TeX Live**: LaTeX処理用
- **メモリ**: 最低4GB、推奨8GB
- **ストレージ**: 最低10GB の空き容量

### 対応OS

- Ubuntu 20.04+
- macOS 10.15+
- Windows 10+ (WSL2推奨)

## インストール手順

### 1. システム依存関係のインストール

#### Ubuntu/Debian

```bash
# 基本パッケージ
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nodejs npm

# FFmpeg
sudo apt install -y ffmpeg

# TeX Live (フルインストール)
sudo apt install -y texlive-full

# PDF処理用
sudo apt install -y poppler-utils

# PostgreSQL (本番環境用)
sudo apt install -y postgresql postgresql-contrib

# Redis
sudo apt install -y redis-server
```

#### macOS

```bash
# Homebrew経由でインストール
brew install python@3.11 node ffmpeg

# TeX Live
brew install --cask mactex

# PDF処理用
brew install poppler

# PostgreSQL
brew install postgresql
brew services start postgresql

# Redis
brew install redis
brew services start redis
```

#### Windows (WSL2)

```bash
# WSL2 (Ubuntu) 内で実行
sudo apt update
sudo apt install -y python3 python3-pip python3-venv

# Node.js (NodeSource経由)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# FFmpeg
sudo apt install -y ffmpeg

# TeX Live
sudo apt install -y texlive-full

# その他の依存関係
sudo apt install -y poppler-utils postgresql redis-server
```

### 2. リポジトリのクローン

```bash
git clone https://github.com/takuyakubo/math-video-generator.git
cd math-video-generator
```

### 3. Pythonバックエンドのセットアップ

```bash
# 仮想環境の作成
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係のインストール
pip install --upgrade pip
pip install -r requirements.txt

# 開発用依存関係（オプション）
pip install -r requirements-dev.txt
```

### 4. フロントエンドのセットアップ

```bash
cd frontend
npm install
npm run build
cd ..
```

### 5. データベースのセットアップ

#### PostgreSQL設定

```bash
# PostgreSQLサービス開始
sudo systemctl start postgresql  # Linux
# brew services start postgresql  # macOS

# データベースとユーザー作成
sudo -u postgres psql
```

```sql
CREATE DATABASE mathvideo;
CREATE USER mathvideo_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE mathvideo TO mathvideo_user;
\q
```

### 6. 環境設定

```bash
# 設定ファイルをコピー
cp .env.example .env

# .envファイルを編集
nano .env
```

**.env の設定例:**

```bash
# API Configuration
APP_NAME=Math Video Generator
DEBUG=true
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=postgresql://mathvideo_user:your_password@localhost/mathvideo

# Redis
REDIS_URL=redis://localhost:6379/0

# File Storage
UPLOAD_DIR=./data/uploads
OUTPUT_DIR=./data/outputs
TEMP_DIR=./data/temp
MAX_FILE_SIZE=104857600

# TTS Configuration (オプション)
AZURE_SPEECH_KEY=your_azure_key
AZURE_SPEECH_REGION=japaneast
GOOGLE_TTS_CREDENTIALS=./path/to/google-credentials.json

# Processing
MAX_WORKERS=4
PROCESSING_TIMEOUT=3600

# LaTeX
LATEX_TIMEOUT=300
PDFLATEX_PATH=pdflatex

# FFmpeg
FFMPEG_PATH=ffmpeg
```

### 7. データベースマイグレーション

```bash
# Alembicでマイグレーション実行
alembic upgrade head
```

### 8. 必要なディレクトリの作成

```bash
mkdir -p data/{uploads,outputs,temp}
mkdir -p logs
```

### 9. TTS サービスの設定（オプション）

#### Azure Cognitive Services

1. [Azure Portal](https://portal.azure.com) でCognitive Servicesリソースを作成
2. Speech Serviceのキーとリージョンを取得
3. `.env`ファイルに設定

#### Google Cloud Text-to-Speech

1. [Google Cloud Console](https://console.cloud.google.com) でプロジェクト作成
2. Text-to-Speech API を有効化
3. サービスアカウントキーをダウンロード
4. 認証情報ファイルのパスを`.env`に設定

## 起動

### 開発環境での起動

#### バックエンド

```bash
# 仮想環境をアクティベート
source venv/bin/activate

# メインサーバー起動
python src/main.py

# または uvicorn で起動
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

#### ワーカープロセス（別ターミナル）

```bash
source venv/bin/activate
celery -A src.worker worker --loglevel=info
```

#### フロントエンド（別ターミナル）

```bash
cd frontend
npm run dev
```

### Docker Composeでの起動

```bash
# 全サービスを起動
docker-compose up -d

# ログを確認
docker-compose logs -f

# 停止
docker-compose down
```

## 動作確認

### ヘルスチェック

```bash
curl http://localhost:8000/health
```

**期待される応答:**
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

### Webインターフェース

ブラウザで以下にアクセス:
- フロントエンド: http://localhost:3000
- API ドキュメント: http://localhost:8000/docs

### 簡単な動作テスト

```bash
# テストファイルをアップロード
curl -X POST "http://localhost:8000/api/upload" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@tests/fixtures/sample.pdf"
```

## トラブルシューティング

### よくある問題

#### 1. LaTeX コンパイルエラー

```bash
# TeX Live が正しくインストールされているか確認
pdflatex --version

# 日本語フォントの問題の場合
sudo apt install -y fonts-noto-cjk
```

#### 2. FFmpeg エラー

```bash
# FFmpeg のバージョン確認
ffmpeg -version

# パスが正しく設定されているか確認
which ffmpeg
```

#### 3. PostgreSQL 接続エラー

```bash
# PostgreSQL サービス状況確認
sudo systemctl status postgresql

# 接続テスト
psql -h localhost -U mathvideo_user -d mathvideo
```

#### 4. Redis 接続エラー

```bash
# Redis サービス確認
sudo systemctl status redis-server

# Redis CLI で接続テスト
redis-cli ping
```

#### 5. メモリ不足

```bash
# メモリ使用量確認
free -h

# スワップファイル作成（必要に応じて）
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### ログファイル

```bash
# アプリケーションログ
tail -f logs/app.log

# Celeryワーカーログ
tail -f logs/celery.log

# システムログ（Ubuntu）
sudo journalctl -u math-video-generator -f
```

### パフォーマンステューニング

#### 1. ワーカープロセス数の調整

```bash
# CPUコア数に応じて調整
celery -A src.worker worker --concurrency=4
```

#### 2. データベース最適化

```sql
-- PostgreSQL の設定調整（postgresql.conf）
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
```

#### 3. Redis メモリ設定

```bash
# redis.conf
maxmemory 512mb
maxmemory-policy allkeys-lru
```

## 本番環境への展開

本番環境での展開については、[DEPLOYMENT.md](DEPLOYMENT.md) を参照してください。

## アップデート

```bash
# 最新版を取得
git pull origin main

# 依存関係を更新
source venv/bin/activate
pip install -r requirements.txt

# フロントエンド更新
cd frontend
npm install
npm run build
cd ..

# データベースマイグレーション
alembic upgrade head

# サービス再起動
sudo systemctl restart math-video-generator
```