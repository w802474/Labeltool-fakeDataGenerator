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

### インペインティングエンドポイント
- `POST /api/v1/inpaint` - 提供されたマスクでインペインティング（画像バイナリを返す）
- `POST /api/v1/inpaint-regions` - テキストリージョンでインペインティング（画像バイナリを返す）
- `POST /api/v1/inpaint-regions-json` - テキストリージョンでインペインティング（JSON 統計を返す）

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

### 処理統計の取得
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