# Math Video Generator

数学の教科書や論文からBeamerスライドベースの教育動画を自動生成するシステム

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Build Status](https://img.shields.io/badge/Build-Passing-brightgreen.svg)]()

## 🎯 概要

Math Video Generatorは、数学の教科書やアカデミックな論文（PDF、LaTeX形式）を入力として、YouTube風のチャプター付き教育動画を自動生成するツールです。3Blue1Brownスタイルの分かりやすい数学解説動画を簡単に作成できます。

### 主な機能

- 📄 **多形式対応**: PDF、LaTeX、Markdownファイルの処理
- 🎞️ **自動スライド生成**: Beamerベースのプロフェッショナルなスライド
- 🔊 **音声合成**: 高品質なTTSによる自動ナレーション
- 📊 **数式処理**: LaTeX数式の美しい視覚化とアニメーション
- 📑 **チャプター機能**: 章・節ごとの自動チャプター分割
- 🎨 **カスタマイズ**: 複数のテーマとスタイルオプション

## 🚀 クイックスタート

### 必要環境

- Python 3.9+
- Node.js 16+
- FFmpeg
- TeX Live (LaTeX処理用)

### インストール

```bash
# リポジトリのクローン
git clone https://github.com/takuyakubo/math-video-generator.git
cd math-video-generator

# Python依存関係のインストール
pip install -r requirements.txt

# フロントエンド依存関係のインストール
cd frontend
npm install
cd ..

# 設定ファイルの作成
cp .env.example .env
# .envファイルを編集してAPIキーなどを設定
```

### Dockerを使用する場合

```bash
# Docker Composeで起動
docker-compose up -d
```

## 📖 使用方法

### 1. Webインターフェース

```bash
# サーバー起動
python src/main.py

# フロントエンド開発サーバー起動
cd frontend
npm run dev
```

ブラウザで `http://localhost:3000` にアクセス

### 2. APIを直接使用

```python
import requests

# ファイルアップロード
files = {'file': open('sample.pdf', 'rb')}
response = requests.post('http://localhost:8000/api/upload', files=files)

# 動画生成開始
job_id = response.json()['job_id']
requests.post(f'http://localhost:8000/api/process/{job_id}', json={
    'template': 'academic',
    'voice': 'ja-JP-Wavenet-A',
    'chapters': True
})
```

### 3. コマンドライン

```bash
# 基本的な変換
python -m src.cli --input sample.pdf --output video.mp4

# オプション指定
python -m src.cli --input paper.tex --template modern --voice japanese --chapters
```

## 🏗️ アーキテクチャ

```
Frontend (Vue.js) → API Gateway → Processing Engine → Storage
                                       ↓
                                  Queue System → Video Workers
```

### 主要コンポーネント

- **Document Parser**: PDF/LaTeX解析エンジン
- **Slide Generator**: Beamerスライド生成
- **TTS Engine**: 音声合成システム
- **Video Generator**: 最終動画生成
- **Chapter Detector**: 自動章構造検出

## 🎨 サンプル

### 入力例
```latex
\section{微分積分学の基礎}
\subsection{導関数の定義}

関数 $f(x)$ の点 $a$ における導関数は以下で定義される：

$$f'(a) = \lim_{h \to 0} \frac{f(a+h) - f(a)}{h}$$
```

### 出力
- チャプター「1. 微分積分学の基礎」
- サブチャプター「1.1 導関数の定義」
- 数式アニメーション付きスライド
- 自然な日本語ナレーション

## 📋 API仕様

### エンドポイント

- `POST /api/upload` - ファイルアップロード
- `GET /api/process/{job_id}` - 処理状況確認
- `POST /api/process/{job_id}` - 動画生成開始
- `GET /api/download/{job_id}` - 動画ダウンロード

詳細は [API.md](docs/API.md) を参照

## 🛠️ 開発

### 開発環境セットアップ

```bash
# 開発用依存関係インストール
pip install -r requirements-dev.txt

# テスト実行
pytest tests/

# コード品質チェック
flake8 src/
black src/
mypy src/
```

### コントリビューション

1. Forkしてブランチを作成
2. 変更を実装
3. テストを追加/実行
4. プルリクエスト作成

詳細は [CONTRIBUTING.md](docs/CONTRIBUTING.md) を参照

## 📊 技術スタック

- **Backend**: FastAPI, SQLAlchemy, Celery
- **Frontend**: Vue.js 3, Vite, TypeScript
- **Processing**: PyPDF2, python-latex, SymPy
- **Media**: FFmpeg, MoviePy, Pillow
- **TTS**: Azure Cognitive Services, Google Cloud TTS
- **Database**: PostgreSQL, Redis
- **Deployment**: Docker, Kubernetes

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は [LICENSE](LICENSE) ファイルを参照してください。

## 🤝 サポート

- 📖 [ドキュメント](docs/)
- 🐛 [Issue報告](https://github.com/takuyakubo/math-video-generator/issues)
- 💬 [ディスカッション](https://github.com/takuyakubo/math-video-generator/discussions)

## 🎯 ロードマップ

- [ ] **Phase 1**: MVP（基本的なPDF→動画変換）
- [ ] **Phase 2**: 高度な数式処理とテンプレート
- [ ] **Phase 3**: AI支援による自動説明生成
- [ ] **Phase 4**: リアルタイム編集機能

---

Made with ❤️ for the mathematical community