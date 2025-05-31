# Math Video Generator 使用ガイド

## 概要

Math Video Generatorは、数学の教科書や論文から教育動画を自動生成するツールです。PDF、LaTeX、Markdownファイルを入力として、Beamerスライドベースの動画を生成します。

## 基本的な使用方法

### 1. Webインターフェースを使用

#### ステップ1: ファイルのアップロード

1. ブラウザで `http://localhost:3000` にアクセス
2. 「ファイルを選択」ボタンをクリック
3. 数学文書（PDF、LaTeX、Markdown）を選択
4. 「アップロード」をクリック

**サポートファイル形式:**
- PDF: 数学論文、教科書のPDF
- LaTeX: `.tex` ファイル
- Markdown: 数式を含むMarkdownファイル

#### ステップ2: 設定の調整

アップロード後、以下の設定を調整できます:

**基本設定:**
- **テンプレート**: `academic`, `modern`, `default`
- **動画品質**: `720p`, `1080p`, `4k`
- **言語**: `日本語`, `English`

**音声設定:**
- **音声タイプ**: Azure または Google TTS
- **音声**: 利用可能な音声から選択
- **速度**: 0.5倍 〜 2.0倍

**詳細設定:**
- **チャプター**: 自動チャプター分割の有効/無効
- **アニメーション**: 数式アニメーションの速度

#### ステップ3: 動画生成

1. 設定完了後「動画生成開始」をクリック
2. 進行状況が表示されます：
   - 文書解析中
   - スライド生成中
   - 音声生成中
   - 動画生成中
3. 完了後、ダウンロードリンクが表示されます

### 2. API を直接使用

#### Python例

```python
import requests
import time
from pathlib import Path

class MathVideoGenerator:
    def __init__(self, base_url="http://localhost:8000/api"):
        self.base_url = base_url
    
    def upload_file(self, file_path):
        """ファイルをアップロード"""
        with open(file_path, 'rb') as f:
            files = {'file': (Path(file_path).name, f)}
            response = requests.post(f"{self.base_url}/upload", files=files)
            response.raise_for_status()
            return response.json()['job_id']
    
    def start_processing(self, job_id, config):
        """処理を開始"""
        response = requests.post(
            f"{self.base_url}/process/{job_id}",
            json=config
        )
        response.raise_for_status()
        return response.json()
    
    def wait_for_completion(self, job_id, timeout=3600):
        """処理完了まで待機"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            response = requests.get(f"{self.base_url}/process/{job_id}/status")
            response.raise_for_status()
            
            status_data = response.json()
            status = status_data['status']
            progress = status_data.get('progress', 0)
            
            print(f"Status: {status}, Progress: {progress}%")
            
            if status == 'completed':
                return True
            elif status == 'failed':
                error_msg = status_data.get('error_message', 'Unknown error')
                raise Exception(f"Processing failed: {error_msg}")
            
            time.sleep(10)
        
        raise TimeoutError("Processing timed out")
    
    def download_video(self, job_id, output_path):
        """動画をダウンロード"""
        response = requests.get(f"{self.base_url}/download/{job_id}/video")
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        print(f"Video saved to: {output_path}")

# 使用例
generator = MathVideoGenerator()

# 1. ファイルアップロード
job_id = generator.upload_file("math_paper.pdf")
print(f"Job ID: {job_id}")

# 2. 処理設定
config = {
    "template": "academic",
    "voice": "ja-JP-NanamiNeural",
    "language": "ja",
    "chapters": True,
    "video_quality": "1080p",
    "animation_speed": 1.0
}

# 3. 処理開始
generator.start_processing(job_id, config)

# 4. 完了まで待機
generator.wait_for_completion(job_id)

# 5. 動画ダウンロード
generator.download_video(job_id, "output_video.mp4")
```

#### cURL例

```bash
#!/bin/bash

# 1. ファイルアップロード
echo "Uploading file..."
UPLOAD_RESPONSE=$(curl -s -X POST \
  "http://localhost:8000/api/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@math_document.pdf")

JOB_ID=$(echo $UPLOAD_RESPONSE | jq -r '.job_id')
echo "Job ID: $JOB_ID"

# 2. 処理開始
echo "Starting processing..."
curl -s -X POST \
  "http://localhost:8000/api/process/$JOB_ID" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "template": "academic",
    "voice": "ja-JP-Wavenet-A",
    "language": "ja",
    "chapters": true,
    "video_quality": "1080p"
  }'

# 3. 処理完了まで待機
echo "Waiting for completion..."
while true; do
  STATUS_RESPONSE=$(curl -s "http://localhost:8000/api/process/$JOB_ID/status")
  STATUS=$(echo $STATUS_RESPONSE | jq -r '.status')
  PROGRESS=$(echo $STATUS_RESPONSE | jq -r '.progress')
  
  echo "Status: $STATUS, Progress: $PROGRESS%"
  
  if [ "$STATUS" = "completed" ]; then
    echo "Processing completed!"
    break
  elif [ "$STATUS" = "failed" ]; then
    echo "Processing failed!"
    exit 1
  fi
  
  sleep 10
done

# 4. 動画ダウンロード
echo "Downloading video..."
curl -o "output_video.mp4" \
  "http://localhost:8000/api/download/$JOB_ID/video"

echo "Video saved as output_video.mp4"
```

### 3. コマンドラインツール（計画中）

```bash
# 基本的な使用法
mathvideo generate input.pdf --output video.mp4

# オプション指定
mathvideo generate paper.tex \
  --template modern \
  --voice ja-JP-Wavenet-A \
  --quality 1080p \
  --chapters \
  --output lecture.mp4
```

## 詳細設定

### テンプレート

#### Academic テンプレート
- 学術論文・教科書向け
- シンプルで読みやすいデザイン
- 数式の視認性を重視

#### Modern テンプレート
- 現代的なデザイン
- 視覚的にインパクトのある表現
- プレゼンテーション向け

#### カスタムテンプレート

独自のBeamerテンプレートを追加することも可能です：

1. `src/templates/beamer/` にテンプレートファイルを配置
2. `SlideGenerator` クラスにテンプレート関数を追加
3. 設定で指定

### 音声設定

#### 利用可能な音声（Azure）

**日本語:**
- `ja-JP-NanamiNeural`: 女性、自然
- `ja-JP-KeitaNeural`: 男性、明瞭
- `ja-JP-AoiNeural`: 女性、若々しい

**英語:**
- `en-US-JennyNeural`: 女性、標準アメリカ英語
- `en-US-GuyNeural`: 男性、標準アメリカ英語
- `en-GB-LibbyNeural`: 女性、イギリス英語

#### 数式の読み上げ

システムは自動的にLaTeX数式を音声用テキストに変換します：

```latex
\frac{df}{dx} → "dエフ dx分の dエフ"
\sum_{i=1}^n → "アイが1からnまでの総和"
\int_a^b f(x)dx → "aからbまでのf(x)の積分"
```

### チャプター機能

チャプター機能を有効にすると、以下の構造を自動検出します：

#### LaTeX文書
```latex
\chapter{微分積分学}
\section{導関数の定義}
\subsection{極限の概念}
```

#### PDF文書
- 「第1章」「Chapter 1」などのパターン
- 大見出しの自動検出
- フォントサイズベースの階層判定

#### Markdown文書
```markdown
# 微分積分学
## 導関数の定義
### 極限の概念
```

## 入力ファイルの準備

### PDF文書のベストプラクティス

1. **テキスト形式のPDF**: 画像スキャンではなくテキストPDFを使用
2. **明確な章構造**: 章番号とタイトルを明確に記載
3. **適切なフォント**: 数式が正しく表示されるフォントを使用

### LaTeX文書のベストプラクティス

```latex
\documentclass[12pt]{article}
\usepackage{amsmath, amssymb, amsfonts}
\usepackage[utf8]{inputenc}
\usepackage[japanese]{babel}

\title{数学解析の基礎}
\author{著者名}

\begin{document}
\maketitle

\begin{abstract}
本論文では微分積分学の基礎概念について説明する。
\end{abstract}

\section{導関数}
関数$f(x)$の導関数は以下で定義される：
$$f'(x) = \lim_{h \to 0} \frac{f(x+h) - f(x)}{h}$$

\end{document}
```

### Markdown文書のベストプラクティス

```markdown
# 数学解析の基礎

著者: 山田太郎

## 概要

本文書では微分積分学の基礎について説明します。

## 導関数の定義

関数 $f(x)$ の導関数は以下で定義されます：

$$f'(x) = \lim_{h \to 0} \frac{f(x+h) - f(x)}{h}$$

### 幾何学的解釈

導関数は接線の傾きを表します。
```

## トラブルシューティング

### よくある問題と解決策

#### 1. 数式が正しく認識されない

**問題**: PDF内の数式がテキストとして抽出できない

**解決策**:
- テキストベースのPDFを使用
- LaTeX形式で再作成
- OCRソフトウェアでテキスト化

#### 2. 音声品質が悪い

**問題**: 生成された音声が不自然

**解決策**:
- 異なる音声を試す
- 読み上げ速度を調整
- 数式読み上げ設定を変更

#### 3. 動画生成が失敗する

**問題**: FFmpegエラーで動画生成が失敗

**解決策**:
```bash
# FFmpegバージョン確認
ffmpeg -version

# 権限確認
ls -la /usr/bin/ffmpeg

# 一時ファイルディレクトリの確認
ls -la data/temp/
```

#### 4. LaTexコンパイルエラー

**問題**: スライド生成時のLaTeXエラー

**解決策**:
```bash
# TeX Liveの確認
tex --version
pdflatex --version

# 日本語フォントの確認
fc-list | grep -i japanese

# 権限確認
ls -la ~/.texlive*/
```

### ログの確認

```bash
# アプリケーションログ
tail -f logs/app.log

# 特定のジョブのログ
grep "job_id:your-job-id" logs/app.log

# エラーのみ
grep "ERROR" logs/app.log
```

## パフォーマンス最適化

### 処理時間短縮

1. **並列処理**: ワーカープロセス数を増加
2. **キャッシュ**: 同じ文書の再処理時間短縮
3. **品質調整**: 必要に応じて低解像度で生成

### メモリ使用量削減

1. **ファイルサイズ制限**: 大きすぎるファイルは分割
2. **一時ファイル管理**: 定期的な清掃
3. **プロセス監視**: メモリリーク検出

## 高度な使用法

### バッチ処理

```python
# 複数ファイルの一括処理
files = ['paper1.pdf', 'paper2.tex', 'paper3.md']
jobs = []

for file in files:
    job_id = generator.upload_file(file)
    generator.start_processing(job_id, config)
    jobs.append(job_id)

# 全ジョブの完了を待機
for job_id in jobs:
    generator.wait_for_completion(job_id)
    generator.download_video(job_id, f"{job_id}.mp4")
```

### カスタム音声処理

```python
# 独自のTTSプロバイダーを追加
class CustomTTSProvider(TTSProvider):
    async def synthesize_text(self, text, output_path, voice=None):
        # カスタム実装
        pass

# エンジンに登録
tts_engine.providers['custom'] = CustomTTSProvider()
```

### Webhook通知

```python
# 処理完了時の通知設定
config = {
    "template": "academic",
    "webhook_url": "https://your-server.com/webhook",
    "notification_events": ["completed", "failed"]
}
```

## ベストプラクティス

### 1. ファイル準備
- 明確な章構造を持つ文書を使用
- 数式は標準的なLaTeX記法で記述
- 図表は高解像度で埋め込み

### 2. 設定選択
- 用途に応じたテンプレート選択
- 聴衆に適した音声選択
- 必要十分な品質設定

### 3. 品質管理
- 生成前にプレビュー確認
- 音声テストの実施
- 段階的な品質向上

### 4. 効率的な運用
- 定期的なシステムメンテナンス
- ログの監視
- パフォーマンス測定

## 次のステップ

- [API仕様書](API.md) でプログラム連携を学ぶ
- [開発ガイド](CONTRIBUTING.md) でカスタマイズ方法を確認
- [FAQ](FAQ.md) でよくある質問を参照