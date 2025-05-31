# Math Video Generator API Documentation

## 概要

Math Video Generator APIは、数学文書から動画を生成するためのRESTful APIです。

## ベースURL

```
http://localhost:8000/api
```

## 認証

現在のバージョンでは認証は不要です。

## エンドポイント

### 1. ファイルアップロード

#### `POST /upload`

数学文書（PDF、LaTeX、Markdown）をアップロードして解析を開始します。

**リクエスト**
```http
POST /api/upload
Content-Type: multipart/form-data

file: [ファイル]
```

**サポートファイル形式**
- PDF (`.pdf`)
- LaTeX (`.tex`)
- Markdown (`.md`)

**レスポンス**
```json
{
  "job_id": "uuid-string",
  "status": "uploaded",
  "filename": "document.pdf",
  "document_info": {
    "title": "数学解析の基礎",
    "author": "著者名",
    "chapters": 5,
    "pages": 20
  }
}
```

**エラーレスポンス**
```json
{
  "detail": "Unsupported file format. Allowed: ['.pdf', '.tex', '.md']"
}
```

### 2. 処理開始

#### `POST /process/{job_id}`

動画生成処理を開始します。

**リクエスト**
```http
POST /api/process/{job_id}
Content-Type: application/json

{
  "template": "academic",
  "voice": "ja-JP-Wavenet-A",
  "language": "ja",
  "chapters": true,
  "video_quality": "1080p",
  "animation_speed": 1.0
}
```

**パラメータ**
- `template`: スライドテンプレート（`academic`, `modern`, `default`）
- `voice`: TTS音声（Azure/Google音声名）
- `language`: 言語コード（`ja`, `en`）
- `chapters`: チャプター情報を含めるか
- `video_quality`: 動画品質（`720p`, `1080p`, `4k`）
- `animation_speed`: アニメーション速度

**レスポンス**
```json
{
  "job_id": "uuid-string",
  "status": "processing_started",
  "message": "Video generation started in background",
  "config": {
    "template": "academic",
    "voice": "ja-JP-Wavenet-A",
    "chapters": true
  }
}
```

### 3. 処理状況確認

#### `GET /process/{job_id}/status`

処理の進行状況を確認します。

**レスポンス**
```json
{
  "job_id": "uuid-string",
  "status": "processing",
  "progress": 45,
  "current_step": "generating_audio",
  "estimated_completion": "2024-01-01T12:30:00Z"
}
```

**ステータス値**
- `uploaded`: アップロード完了
- `parsing`: 文書解析中
- `generating_slides`: スライド生成中
- `generating_audio`: 音声生成中
- `generating_video`: 動画生成中
- `completed`: 完了
- `failed`: 失敗

### 4. ダウンロード

#### `GET /download/{job_id}/video`

生成された動画をダウンロードします。

**レスポンス**
- ファイル: MP4形式の動画
- Content-Type: `video/mp4`

#### `GET /download/{job_id}/slides`

生成されたスライド（PDF）をダウンロードします。

**レスポンス**
- ファイル: PDF形式のスライド
- Content-Type: `application/pdf`

#### `GET /download/{job_id}/info`

ダウンロード可能なファイル情報を取得します。

**レスポンス**
```json
{
  "job_id": "uuid-string",
  "available_files": {
    "video": true,
    "slides": true,
    "audio": false
  },
  "download_urls": {
    "video": "/api/download/uuid-string/video",
    "slides": "/api/download/uuid-string/slides"
  }
}
```

## エラーハンドリング

### HTTPステータスコード

- `200`: 成功
- `400`: 不正なリクエスト
- `404`: リソースが見つからない
- `413`: ファイルサイズが大きすぎる
- `422`: バリデーションエラー
- `500`: サーバーエラー

### エラーレスポンス形式

```json
{
  "detail": "エラーメッセージ"
}
```

## 使用例

### Python

```python
import requests
import time

# 1. ファイルアップロード
with open('math_document.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/upload',
        files={'file': f}
    )
    job_id = response.json()['job_id']

# 2. 処理開始
config = {
    'template': 'academic',
    'voice': 'ja-JP-Wavenet-A',
    'chapters': True,
    'video_quality': '1080p'
}
response = requests.post(
    f'http://localhost:8000/api/process/{job_id}',
    json=config
)

# 3. 処理完了まで待機
while True:
    response = requests.get(
        f'http://localhost:8000/api/process/{job_id}/status'
    )
    status = response.json()['status']
    
    if status == 'completed':
        break
    elif status == 'failed':
        print('処理に失敗しました')
        exit(1)
    
    time.sleep(10)

# 4. 動画ダウンロード
response = requests.get(
    f'http://localhost:8000/api/download/{job_id}/video'
)
with open('output_video.mp4', 'wb') as f:
    f.write(response.content)
```

### JavaScript

```javascript
// ファイルアップロード
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const uploadResponse = await fetch('/api/upload', {
  method: 'POST',
  body: formData
});
const { job_id } = await uploadResponse.json();

// 処理開始
const processResponse = await fetch(`/api/process/${job_id}`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    template: 'academic',
    voice: 'ja-JP-Wavenet-A',
    chapters: true,
    video_quality: '1080p'
  })
});

// 処理状況の監視
const checkStatus = async () => {
  const response = await fetch(`/api/process/${job_id}/status`);
  const data = await response.json();
  
  if (data.status === 'completed') {
    // ダウンロードリンクを表示
    const downloadUrl = `/api/download/${job_id}/video`;
    downloadLink.href = downloadUrl;
  } else if (data.status !== 'failed') {
    setTimeout(checkStatus, 5000);
  }
};

checkStatus();
```

## 制限事項

- 最大ファイルサイズ: 100MB
- 同時処理可能ジョブ数: 4
- 処理タイムアウト: 1時間
- サポート言語: 日本語、英語

## バージョン履歴

### v1.0.0
- 初回リリース
- PDF、LaTeX、Markdown対応
- 基本的な動画生成機能
- チャプター機能対応