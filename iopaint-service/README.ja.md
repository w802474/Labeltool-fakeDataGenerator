# IOPaint テキスト除去サービス

**🌍 [中文](README.zh-CN.md) | 日本語 | [English](README.md)**

🎯 **IOPaint 1.6.0 を使用した高度なテキストインペインティングと除去のためのプロフェッショナルマイクロサービス**

リアルタイム進行状況追跡機能を備えた、強力なテキスト除去機能を提供する本格的な独立マイクロサービスです。高品質な画像テキストインペインティングが必要なアプリケーションへの簡単な統合を実現します。

## ✨ 主要機能

- 🔧 **高度なテキスト除去**: LAMA モデルを使用した最先端の IOPaint による、シームレスな背景保護
- 🚀 **リアルタイム処理**: 長時間実行タスクに対応した WebSocket ベースの進行状況追跡  
- 🎛️ **複数の処理モード**: 同期、非同期、バッチ処理のサポート
- 🎨 **柔軟な入力方式**: マスクベース、リージョンベース、座標ベースのインペインティング
- 🏗️ **本番環境対応**: Docker コンテナ化、ヘルスモニタリング、包括的なエラーハンドリング
- ⚡ **パフォーマンス最適化**: GPU アクセラレーション、メモリ管理、インテリジェントな画像スケーリング
- 🔌 **統合の容易さ**: OpenAPI ドキュメント付き RESTful API と複数 SDK
- 📊 **高度なモニタリング**: リソース追跡、診断、処理分析

## 📋 API エンドポイント

### コアエンドポイント
- `GET /` - サービス情報とステータス
- `GET /api/v1/health` - ヘルスチェック
- `GET /api/v1/model` - 現在のモデル情報
- `GET /api/v1/info` - 詳細なサービス情報

### 同期インペインティング
- `POST /api/v1/inpaint` - 提供されたマスクでインペインティング（画像バイナリを返す）
- `POST /api/v1/inpaint-regions` - テキストリージョンでインペインティング（画像バイナリを返す）
- `POST /api/v1/inpaint-regions-json` - テキストリージョンでインペインティング（JSON 統計を返す）

### 非同期処理
- `POST /api/v1/inpaint-regions-async` - 進捗追跡付き非同期インペインティングを開始
- `GET /api/v1/task-status/{task_id}` - タスクステータスと進捗を取得
- `POST /api/v1/cancel-task/{task_id}` - 実行中のタスクをキャンセル
- `GET /api/v1/tasks` - タスク統計とキュー状態を取得

### WebSocket エンドポイント
- `WS /api/v1/ws/progress/{task_id}` - 特定タスクのリアルタイム進捗更新
- `WS /api/v1/ws/progress` - すべてのタスクの一般的な進捗更新

### ドキュメント
- `GET /docs` - インタラクティブ API ドキュメント（Swagger UI）
- `GET /redoc` - 代替 API ドキュメント（ReDoc）

## 🛠️ 設定

### 環境変数

| 変数 | デフォルト | 説明 |
|------|----------|------|
| `IOPAINT_HOST` | `0.0.0.0` | サービスホストアドレス |
| `IOPAINT_PORT` | `8081` | サービスポート |
| `IOPAINT_MODEL` | `lama` | 使用する IOPaint モデル |
| `IOPAINT_DEVICE` | `cpu` | 処理デバイス（cpu/cuda/mps） |
| `IOPAINT_LOW_MEM` | `true` | 低メモリモードを有効化 |
| `IOPAINT_CPU_OFFLOAD` | `true` | CPU オフロードを有効化 |
| `MAX_IMAGE_SIZE` | `2048` | 画像の最大サイズ |
| `MAX_FILE_SIZE` | `52428800` | 最大ファイルサイズ（50MB） |
| `REQUEST_TIMEOUT` | `300` | リクエストタイムアウト（秒） |
| `LOG_LEVEL` | `INFO` | ログレベル |

### サポートされるモデル
- **lama**（デフォルト）- Large Mask Inpainting モデル（最高品質）
- **ldm** - Latent Diffusion Model
- **zits** - Incremental Transformer Structure
- **mat** - Mask-Aware Transformer
- **fcf** - Fourier Convolutions
- **manga** - マンガ・アニメ画像専用

## 🚢 Docker デプロイメント

### スタンドアロンデプロイメント
```bash
# イメージをビルド
docker build -t iopaint-service .

# コンテナを実行
docker run -d \
  --name iopaint-service \
  -p 8081:8081 \
  -e IOPAINT_MODEL=lama \
  -e IOPAINT_DEVICE=cpu \
  iopaint-service
```

### GPU サポート付き
```bash
docker run -d \
  --name iopaint-service \
  --gpus all \
  -p 8081:8081 \
  -e IOPAINT_DEVICE=cuda \
  iopaint-service
```

### Docker Compose 統合
```yaml
services:
  iopaint-service:
    build: ./iopaint-service
    container_name: iopaint-service
    restart: unless-stopped
    ports:
      - "8081:8081"
    environment:
      - IOPAINT_MODEL=lama
      - IOPAINT_DEVICE=cpu
      - IOPAINT_LOW_MEM=true
    volumes:
      - iopaint_cache:/root/.cache/huggingface
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8081/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

volumes:
  iopaint_cache:
    driver: local

networks:
  app-network:
    driver: bridge
```

## 🔌 API 使用例

### ヘルスチェック
```bash
curl http://localhost:8081/api/v1/health
```

### リージョンインペインティング
```python
import requests
import base64

# 画像とリージョンを準備
with open('image.jpg', 'rb') as f:
    image_b64 = base64.b64encode(f.read()).decode('utf-8')

regions = [
    {"x": 100, "y": 50, "width": 200, "height": 30},
    {"x": 150, "y": 200, "width": 150, "height": 25}
]

# リクエストを送信
response = requests.post(
    'http://localhost:8081/api/v1/inpaint-regions',
    json={
        "image": image_b64,
        "regions": regions
    }
)

# 結果を保存
if response.status_code == 200:
    with open('result.png', 'wb') as f:
        f.write(response.content)
```

### 処理統計の取得（JSON レスポンス）
```python
response = requests.post(
    'http://localhost:8081/api/v1/inpaint-regions-json',
    json={
        "image": image_b64,
        "regions": regions
    }
)

stats = response.json()
print(f"処理されたリージョン数: {stats['processing_stats']['regions_processed']}")
print(f"処理時間: {stats['processing_stats']['processing_time']:.2f}秒")
```

### 進捗追跡付き非同期処理
```python
import requests
import uuid

# 非同期処理を開始
task_id = str(uuid.uuid4())
response = requests.post(
    'http://localhost:8081/api/v1/inpaint-regions-async',
    json={
        "image": image_b64,
        "regions": regions,
        "task_id": task_id,
        "enable_progress": True
    }
)

async_result = response.json()
print(f"タスク開始: {async_result['task_id']}")
print(f"WebSocket URL: {async_result['websocket_url']}")

# タスクステータスを確認
status_response = requests.get(f'http://localhost:8081/api/v1/task-status/{task_id}')
status = status_response.json()
print(f"タスクステータス: {status['status']}")
```

### バックエンドサービス統合

この IOPaint サービスは、フロントエンドアプリケーションから直接呼び出すのではなく、メインバックエンド API を通じて呼び出すように設計されています。バックエンドサービスはセッション管理、ファイルストレージを処理し、完全な OCR + テキスト除去ワークフローを調整します。

#### バックエンド統合例 (Python)
```python
# バックエンドサービスが IOPaint と統合する方法
# ファイル: backend/app/infrastructure/clients/iopaint_client.py

import aiohttp
import base64

class IOPaintClient:
    def __init__(self, base_url="http://iopaint-service:8081"):
        self.base_url = base_url
    
    async def inpaint_regions_async(self, image_path: str, text_regions: List[dict], task_id: str):
        """非同期テキスト除去処理を開始。"""
        # 画像をbase64に変換
        async with aiofiles.open(image_path, 'rb') as f:
            image_data = await f.read()
            image_b64 = base64.b64encode(image_data).decode('utf-8')
        
        # リージョンをIOPaint形式に変換
        regions = []
        for region in text_regions:
            regions.append({
                "x": region["bounding_box"]["x"],
                "y": region["bounding_box"]["y"], 
                "width": region["bounding_box"]["width"],
                "height": region["bounding_box"]["height"]
            })
        
        # IOPaintサービスを呼び出し
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/v1/inpaint-regions-async",
                json={
                    "image": image_b64,
                    "regions": regions,
                    "task_id": task_id,
                    "enable_progress": True
                }
            ) as response:
                return await response.json()
```

#### WebSocket 進捗統合 (バックエンド)
```python
# バックエンドWebSocketからフロントエンドへのリレー
# ファイル: backend/app/infrastructure/api/websocket_routes.py

from fastapi import WebSocket
import websockets
import json

async def relay_iopaint_progress(websocket: WebSocket, task_id: str):
    """バックエンドWebSocketを通じてIOPaint進捗をフロントエンドにリレー。"""
    iopaint_ws_url = f"ws://iopaint-service:8081/api/v1/ws/progress/{task_id}"
    
    try:
        async with websockets.connect(iopaint_ws_url) as iopaint_ws:
            async for message in iopaint_ws:
                # 進捗をフロントエンドにリレー
                await websocket.send_text(message)
    except Exception as e:
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": f"進捗追跡エラー: {str(e)}"
        }))
```

### カスタムパラメータでの高度な使用
```python
# カスタムパラメータでの高度なインペインティング
response = requests.post(
    'http://localhost:8081/api/v1/inpaint-regions-async',
    json={
        "image": image_b64,
        "regions": regions,
        "task_id": task_id,
        "enable_progress": True,
        # 高度なIOPaintパラメータ
        "sd_seed": 42,
        "sd_steps": 20,
        "sd_strength": 0.8,
        "sd_guidance_scale": 7.5,
        "hd_strategy": "Original",
        "hd_strategy_crop_trigger_size": 1024,
        "hd_strategy_crop_margin": 32
    }
)
```

## 🏗️ 開発

### ローカル開発
```bash
# 依存関係をインストール
pip install -r requirements.txt

# サービスを実行
python -m uvicorn app.main:app --host 0.0.0.0 --port 8081 --reload
```

### テスト
```bash
# ヘルスエンドポイントをテスト
curl http://localhost:8081/api/v1/health

# API ドキュメントを表示
open http://localhost:8081/docs
```

## 📊 モニタリング

### ヘルスチェックエンドポイント
`/api/v1/health` エンドポイントはサービスステータスを提供します：
```json
{
  "status": "healthy",
  "message": "IOPaint service is running",
  "timestamp": "2024-01-01T12:00:00",
  "version": "1.0.0"
}
```

### サービスメトリクス
レスポンスヘッダーには処理メトリクスが含まれます：
- `X-Processing-Time`: 処理時間（秒）
- `X-Regions-Count`: 処理されたリージョン数
- `X-Total-Area`: 処理された総面積（ピクセル）
- `X-Timestamp`: 処理タイムスタンプ

## 🔧 トラブルシューティング

### よくある問題

1. **サービス起動タイムアウト**
   - 起動タイムアウトを増加（初回実行時はモデルのダウンロードが必要）
   - モデルダウンロード用のインターネット接続を確認
   - モデルキャッシュ用の十分なディスク容量を確保

2. **メモリ不足エラー**
   - `IOPAINT_LOW_MEM=true` を有効化
   - `IOPAINT_CPU_OFFLOAD=true` を有効化
   - `MAX_IMAGE_SIZE` を削減

3. **処理速度が遅い**
   - `IOPAINT_DEVICE=cuda` で GPU アクセラレーションを使用
   - 品質より速度を重視する場合は高速モデル（fcf、zits）を検討
   - 画像解像度を削減

### ログ
サービスログは処理の詳細情報を提供します：
```bash
docker logs iopaint-service
```

## 🌟 既存プロジェクトへの統合

### 基本的な統合手順

1. **既存の Docker Compose に追加**
```yaml
# docker-compose.yml に追加
iopaint-service:
  image: iopaint-service:latest
  ports:
    - "8081:8081"
  environment:
    - IOPAINT_MODEL=lama
    - IOPAINT_DEVICE=cpu
```

2. **Python 統合例**
```python
import aiohttp
import base64

class IOPaintClient:
    def __init__(self, base_url="http://localhost:8081"):
        self.base_url = base_url
    
    async def remove_text_regions(self, image_path, regions):
        """画像から指定リージョンのテキストを除去"""
        with open(image_path, 'rb') as f:
            image_b64 = base64.b64encode(f.read()).decode('utf-8')
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/v1/inpaint-regions",
                json={"image": image_b64, "regions": regions}
            ) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    raise Exception(f"リクエスト失敗: {response.status}")

# 使用例
client = IOPaintClient()
regions = [{"x": 100, "y": 50, "width": 200, "height": 30}]
result = await client.remove_text_regions("input.jpg", regions)
```

3. **JavaScript/Node.js 統合例**
```javascript
const axios = require('axios');
const fs = require('fs');

class IOPaintClient {
    constructor(baseUrl = 'http://localhost:8081') {
        this.baseUrl = baseUrl;
    }
    
    async removeTextRegions(imagePath, regions) {
        const imageBuffer = fs.readFileSync(imagePath);
        const imageB64 = imageBuffer.toString('base64');
        
        const response = await axios.post(
            `${this.baseUrl}/api/v1/inpaint-regions`,
            {
                image: imageB64,
                regions: regions
            },
            { responseType: 'arraybuffer' }
        );
        
        return response.data;
    }
}

// 使用例
const client = new IOPaintClient();
const regions = [{x: 100, y: 50, width: 200, height: 30}];
const result = await client.removeTextRegions('input.jpg', regions);
fs.writeFileSync('output.png', result);
```

## 📈 パフォーマンス最適化の推奨事項

### サーバー構成
- **CPU**: 4コア以上を推奨
- **メモリ**: 8GB以上を推奨（LAMAモデルは大量のメモリが必要）
- **ストレージ**: モデル読み込み速度向上のためSSDストレージ
- **GPU**: NVIDIA GPU（CUDA対応）で処理速度が大幅に向上

### 本番環境デプロイメント
```yaml
# 本番環境用 docker-compose.yml 例
version: '3.8'
services:
  iopaint-service:
    build: ./iopaint-service
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 8G
          cpus: '4'
        reservations:
          memory: 4G
          cpus: '2'
    environment:
      - IOPAINT_MODEL=lama
      - IOPAINT_DEVICE=cuda
      - IOPAINT_LOW_MEM=false
      - MAX_IMAGE_SIZE=2048
    volumes:
      - iopaint_cache:/root/.cache/huggingface
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8081/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## 🚀 アーキテクチャの特徴

### マイクロサービス設計
- **疎結合**: 他のサービスから独立して動作
- **スケーラブル**: 負荷に応じて水平スケーリング可能
- **復元力**: 単一障害点を排除した設計
- **観測可能性**: 包括的なログとメトリクス

### セキュリティ機能
- **入力検証**: 全ての入力パラメータの厳密な検証
- **リソース制限**: メモリとCPU使用量の制御
- **タイムアウト**: 長時間実行タスクの適切な処理
- **エラーハンドリング**: セキュアなエラー応答

## 📝 ライセンス

このサービスは LabelTool プロジェクトの一部であり、同じライセンス条項に従います。