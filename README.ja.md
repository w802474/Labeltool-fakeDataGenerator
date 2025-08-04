# LabelTool - インテリジェントテキスト検出・除去ツール

**🌍 [中文](README.zh-CN.md) | 日本語 | [English](README.md)**

包括的なWebベースのインテリジェントテキストアノテーション・処理ツールで、自動検出から手動調整、インテリジェント除去、スマートテキスト生成まで、完全なテキスト処理ワークフローを提供します。スケーラビリティと保守性を備えた現代的なマイクロサービスアーキテクチャで構築されています。

## 🎯 プロジェクト概要

LabelTool は最先端のAIモデルと直感的なユーザーインターフェースを組み合わせて、プロフェッショナルなテキストアノテーション・除去機能を提供する本格的なインテリジェントテキスト処理プラットフォームです：

### 🔄 完全な処理ワークフロー
1. **自動テキスト検出** PaddleOCR による高精度検出
2. **手動テキスト領域調整** 直感的なドラッグ・アンド・ドロップインターフェース  
3. **高度な修復テキスト除去** IOPaint によるシームレスな背景保護
4. **テキスト生成と置換** 処理済み画像への カスタムテキスト追加機能
5. **デュアルモード編集システム** OCR編集と処理画像テキスト生成の両方をサポート

### 🏗️ モダンアーキテクチャ
- **マイクロサービスアーキテクチャ**: 独立サービスによる優れたスケーラビリティとリソース管理
- **ドメイン駆動設計**: バックエンドでDDDパターンを採用し、関心事の明確な分離
- **リアルタイム処理**: 長時間実行タスクのWebSocketベース進行状況追跡
- **本番環境対応**: Docker コンテナ化、包括的監視・エラーハンドリング

## ✨ 主要機能

### 🤖 高度なAI機能
- **高精度OCR**: PaddleOCR と PP-OCRv5 モデルによる精密なテキスト検出
- **最先端の修復技術**: IOPaint LAMA モデルによるシームレスな背景保護
- **インテリジェントフォント分析**: テキスト生成用の自動フォント属性検出
- **スマート画像スケーリング**: 大画像の自動最適化処理

### 🎨 インタラクティブなユーザーエクスペリエンス
- **インタラクティブキャンバス**: Konva.js 駆動のドラッグ・アンド・ドロップテキスト領域編集
- **デュアルモードシステム**: OCR訂正とテキスト生成の独立編集モード
- **高度な元に戻す/やり直し**: コマンドパターンベースの操作履歴、モード分離をサポート
- **リアルタイム進行状況**: 処理中のリアルタイム WebSocket 更新
- **レスポンシブデザイン**: デスクトップとタブレット デバイス用に最適化

### 🏗️ 技術的優秀性
- **マイクロサービスアーキテクチャ**: スケーラビリティをサポートする独立サービス
- **本番環境対応**: 包括的なエラーハンドリング、ヘルス監視、診断
- **Docker ネイティブ**: 完全なコンテナ化、永続化モデルキャッシュ
- **パフォーマンス最適化**: GPU アクセラレーション、メモリ管理、インテリジェントリソース使用

## 🚀 クイックスタート

### Docker Compose を使用（推奨）

```bash
# リポジトリをクローン
git clone <repository-url>
cd labeltool-fakeDataGenerator

# 全サービス起動
docker-compose up --build

# アプリケーションにアクセス
# フロントエンド: http://localhost:3000
# バックエンド API: http://localhost:8000/docs
# IOPaint サービス: http://localhost:8081/docs
```

これだけです！全てのAIモデルと依存関係を含めてアプリケーションが完全に動作します。

### パフォーマンス注意事項
- **初回実行**: AIモデルのダウンロード（約2-3GB）で5-10分程度かかる可能性があります
- **以降の実行**: モデルがキャッシュされ、起動が高速になります
- **GPU サポート**: より高速な処理のためにCUDAを有効化（設定を参照）

## 🏗️ アーキテクチャ概要

### マイクロサービスアーキテクチャ
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│フロントエンドサービス│    │ バックエンドサービス │    │ IOPaint サービス │
│   (React App)   │────│  (FastAPI)      │────│   (FastAPI)     │
│   ポート: 3000   │    │  ポート: 8000    │    │  ポート: 8081    │  
│                 │    │                 │    │                 │
│ • ユーザーIF    │    │ • OCR 検出      │    │ • テキスト除去  │
│ • キャンバス編集│    │ • セッション管理│    │ • LAMA モデル   │
│ • ファイル上传  │    │ • API ゲートウェイ│    │ • 画像修復      │
│ • 状態管理      │    │ • ビジネスロジック│    │ • 進行状況追跡  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                        │                        │
        └─────────── WebSocket & HTTP/REST ───────────────┘
```

### サービス責任

**フロントエンドサービス**:
- React 18 + TypeScript + Vite
- 領域編集用のインタラクティブ Konva.js キャンバス
- 元に戻す/やり直しシステム付き Zustand 状態管理
- リアルタイム WebSocket 進行状況追跡
- レスポンシブ Tailwind CSS デザイン

**バックエンドサービス**:
- FastAPI + Python 3.11 と DDD アーキテクチャ
- テキスト検出用 PaddleOCR 統合
- セッション・タスク管理
- IOPaint サービス クライアント統合
- 包括的ドキュメント付き RESTful API

**IOPaint サービス** ([📖 詳細ドキュメント](iopaint-service/README.ja.md)):
- 独立した FastAPI マイクロサービス
- IOPaint 1.6.0 と LAMA モデル
- 高度な画像修復機能
- リソース監視と最適化
- 独立デプロイメント機能

## 🛠️ 技術スタック

### フロントエンド技術
- **フレームワーク**: React 18 + TypeScript + Vite
- **キャンバス**: インタラクティブ編集用 Konva.js + react-konva
- **状態管理**: 永続化・元に戻す/やり直し付き Zustand
- **スタイリング**: カスタムコンポーネント付き Tailwind CSS
- **HTTP クライアント**: インターセプター付き Axios
- **ファイルアップロード**: 進行状況追跡付き React-Dropzone
- **テスト**: Jest + React Testing Library

### バックエンド技術
- **フレームワーク**: FastAPI + Python 3.11 + Pydantic v2
- **OCR エンジン**: PaddleOCR（PP-OCRv5 モデル付き最新版）
- **画像処理**: OpenCV + Pillow + NumPy
- **アーキテクチャ**: ドメイン駆動設計（DDD）
- **非同期処理**: aiohttp + WebSocket サポート
- **設定**: 環境変数付き Pydantic Settings
- **ログ**: 構造化ログ付き Loguru

### IOPaint サービス技術
- **フレームワーク**: FastAPI + Python 3.11
- **AI モデル**: IOPaint 1.6.0 と LAMA 修復モデル
- **画像処理**: 高度なスケーリングと最適化
- **監視**: リソース追跡と診断
- **エラーハンドリング**: インテリジェント再試行・回復メカニズム

### インフラ・DevOps
- **コンテナ化**: Docker + Docker Compose
- **モデルキャッシュ**: AI モデル用永続化ボリューム
- **ネットワーク**: サービス発見付きブリッジネットワーク
- **ヘルス監視**: 包括的ヘルスチェック
- **ボリューム管理**: 画像とキャッシュ用共有ストレージ

## 🎯 ユーザーワークフロー

### 1. 基本テキスト除去ワークフロー
```
画像アップロード → OCR検出 → 手動調整 → AI修復 → 結果ダウンロード
      ↓            ↓       ↓       ↓         ↓
    検証        テキスト領域 ドラッグ操作 LAMAモデル  PNG出力
```

### 2. 高度なテキスト生成ワークフロー
```
画像アップロード → OCR検出 → AI修復 → テキスト生成 → 結果ダウンロード
      ↓            ↓       ↓       ↓          ↓
    検証        テキスト領域 背景除去  フォント分析   画像強化
                                   + 配置
```

### 3. デュアルモード編集システム

**OCRモード**:
- 検出されたテキスト内容の編集
- テキスト領域境界の調整
- OCR認識エラーの修正
- テキストアノテーション・修正に最適

**処理モード**:
- 修復された背景画像の使用
- インテリジェント配置によるカスタムテキストの追加
- フォント認識テキストレンダリング
- テキスト置換・強化に最適

## 🔌 API ドキュメント

### メインバックエンド API（ポート 8000）

**セッション管理**:
```bash
POST   /api/v1/sessions                    # OCR検出付きセッション作成
GET    /api/v1/sessions/{id}               # セッション詳細取得
PUT    /api/v1/sessions/{id}/regions       # テキスト領域更新（デュアルモード）
DELETE /api/v1/sessions/{id}               # セッション・ファイルクリーンアップ
```

**処理エンドポイント**:
```bash
POST   /api/v1/sessions/{id}/process-async # 非同期テキスト除去開始
GET    /api/v1/tasks/{id}/status           # 処理ステータス取得
POST   /api/v1/tasks/{id}/cancel           # 処理タスクキャンセル
```

**テキスト生成**:
```bash
POST   /api/v1/sessions/{id}/generate-text # 領域内テキスト生成
POST   /api/v1/sessions/{id}/preview-text  # テキスト生成プレビュー
```

**ファイル操作**:
```bash
GET    /api/v1/sessions/{id}/image         # オリジナル画像取得
GET    /api/v1/sessions/{id}/result        # 処理結果ダウンロード
```

### IOPaint サービス API（ポート 8081）

詳細な IOPaint サービスドキュメントについては：**[IOPaint サービスドキュメント](iopaint-service/README.ja.md)**

**コアエンドポイント**:
```bash
GET    /api/v1/health                      # 診断付きヘルスチェック
GET    /api/v1/info                        # サービス情報
POST   /api/v1/inpaint-regions            # テキスト領域修復
POST   /api/v1/inpaint-regions-json       # 統計付き修復
```

## 💻 開発セットアップ

### ローカル開発

**前提条件**:
- Docker & Docker Compose（推奨）
- Python 3.11+ & Node.js 18+（ローカル開発用）
- Git バージョン管理

**オプション1: Docker 開発**
```bash
# フルスタック開発
docker-compose up --build

# バックエンドのみ
docker-compose up backend iopaint-service

# フロントエンド開発サーバー
cd frontend && npm run dev  # ホットリロード付きポート5173
```

**オプション2: ローカル開発**
```bash
# バックエンドセットアップ
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# IOPaint サービスセットアップ（新しいターミナル）
cd iopaint-service
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8081 --reload

# フロントエンドセットアップ（新しいターミナル）
cd frontend
npm install
npm run dev
```

### テスト

**バックエンドテスト**:
```bash
cd backend
pytest tests/ -v --cov=app
```

**フロントエンドテスト**:
```bash
cd frontend
npm run test        # テスト実行
npm run test:watch  # ウォッチモード
npm run test:coverage  # カバレッジレポート
```

**統合テスト**:
```bash
# Docker で完全ワークフローテスト
docker-compose up -d
curl http://localhost:8000/api/v1/health
curl http://localhost:8081/api/v1/health
```

## 🚢 本番デプロイメント

### Docker 本番セットアップ

```bash
# 本番ビルド
docker-compose -f docker-compose.prod.yml up --build -d

# GPU サポート
docker-compose -f docker-compose.gpu.yml up --build -d

# サービス監視
docker-compose logs -f
docker-compose ps
```

### 環境設定

**バックエンド環境**:
```env
# OCR 設定
PADDLEOCR_DEVICE=cpu          # cpu/cuda
PADDLEOCR_LANG=en             # 言語サポート

# IOPaint サービス
IOPAINT_SERVICE_URL=http://iopaint-service:8081
IOPAINT_TIMEOUT=300           # 処理タイムアウト

# アプリケーション設定
MAX_FILE_SIZE=52428800        # 50MB最大アップロード
LOG_LEVEL=INFO                # ログレベル
```

**IOPaint サービス環境**:
```env
# モデル設定
IOPAINT_MODEL=lama            # AIモデル選択
IOPAINT_DEVICE=cpu            # cpu/cuda/mps
IOPAINT_LOW_MEM=true          # メモリ最適化

# パフォーマンス設定
MAX_IMAGE_SIZE=2048           # 最大サイズ
REQUEST_TIMEOUT=300           # 処理タイムアウト
```

## 📊 監視・オブザーバビリティ

### ヘルス監視

**サービスヘルスチェック**:
```bash
# メインアプリケーションヘルス
curl http://localhost:8000/api/v1/health

# IOPaint サービスヘルス
curl http://localhost:8081/api/v1/health

# Docker ヘルスステータス
docker-compose ps
```

**処理メトリクス**:
- WebSocket によるリアルタイム進行状況追跡
- 処理時間とリソース使用状況
- エラー率と再試行統計
- モデルパフォーマンスメトリクス

### ログ記録

**構造化ログ**:
- 本番環境用 JSON フォーマットログ
- リクエスト/レスポンス追跡
- スタックトレース付きエラー追跡
- パフォーマンスメトリクスログ

**ログアクセス**:
```bash
# サービスログ表示
docker-compose logs -f backend
docker-compose logs -f iopaint-service
docker-compose logs -f frontend

# ログエクスポート
docker-compose logs --no-color > application.log
```

## 🔧 設定・カスタマイズ

### OCR 設定

**PaddleOCR 設定**:
```python
OCR_CONFIG = {
    "det_db_thresh": 0.3,        # 検出閾値
    "det_db_box_thresh": 0.6,    # バウンディングボックス閾値
    "det_limit_side_len": 1920,  # 最大画像サイズ
    "use_angle_cls": True,       # テキスト角度分類
    "lang": "en"                 # 言語サポート
}
```

### IOPaint 設定

**モデルオプション**:
- **lama**（デフォルト）: 最高品質修復
- **ldm**: 潜在拡散モデル
- **zits**: 高速処理
- **mat**: マスク認識Transformer
- **fcf**: フーリエ畳み込み
- **manga**: アニメ・マンガ専用

**パフォーマンスチューニング**:
```env
IOPAINT_LOW_MEM=true          # メモリ制限時に有効化
IOPAINT_CPU_OFFLOAD=true      # CPU/GPU負荷分散
MAX_IMAGE_SIZE=2048           # 高速処理のために削減
```

## 🛠️ トラブルシューティング

### よくある問題

**1. サービス起動問題**
```bash
# Docker ステータス確認
docker --version
docker-compose --version

# サービスログ表示
docker-compose logs backend
docker-compose logs iopaint-service

# サービス再起動
docker-compose restart
```

**2. モデルダウンロード問題**
```bash
# ネットワーク接続確認
curl -I https://huggingface.co

# モデルキャッシュクリア
rm -rf volumes/huggingface_cache/*
rm -rf volumes/paddlex_cache/*

# 新しいモデルで再構築
docker-compose down -v
docker-compose up --build
```

**3. パフォーマンス問題**
```bash
# GPU サポート有効化
docker-compose -f docker-compose.gpu.yml up

# 画像サイズ制限削減
# 環境変数編集:
# MAX_IMAGE_SIZE=1024
# MAX_FILE_SIZE=10485760  # 10MB
```

**4. メモリ問題**
```bash
# 低メモリモード有効化
# IOPaint サービス環境:
IOPAINT_LOW_MEM=true
IOPAINT_CPU_OFFLOAD=true

# 同時処理削減
MAX_CONCURRENT_TASKS=1
```

### ヘルプの取得

**ログ・診断**:
```bash
# 診断レポート生成
docker-compose logs --no-color > diagnostic.log
docker-compose ps >> diagnostic.log
docker system df >> diagnostic.log

# リソース使用状況確認
docker stats
```

**一般的な解決策**:
- モデルダウンロードのため初回実行は時間がかかります
- メモリが限られている場合は小さな画像を使用してください
- より高速な処理のためにGPUサポートを有効化してください
- ポートアクセスのためファイアウォール設定を確認してください

## 📖 追加ドキュメント

- **[IOPaint サービス](iopaint-service/README.ja.md)** - 詳細サービスドキュメント
- **[Docker デプロイメント](DOCKER.md)** - 完全デプロイメントガイド
- **[API リファレンス](http://localhost:8000/docs)** - インタラクティブ API ドキュメント
- **[開発ガイド](docs/DEVELOPMENT.md)** - 貢献ガイドライン

## 🤝 貢献

貢献を歓迎します！以下の詳細については貢献ガイドラインをご覧ください：
- コードスタイルと標準
- テスト要件
- プルリクエストプロセス
- 問題報告

## 📝 ライセンス

このプロジェクトは MIT ライセンスの下でライセンスされています - 詳細については LICENSE ファイルをご覧ください。

## 🙏 謝辞

- **PaddleOCR チーム** 優秀な OCR モデルの提供
- **IOPaint 開発者** 最先端の修復機能の提供
- **React & FastAPI コミュニティ** 強力なフレームワークの提供
- **Docker** コンテナ化サポートの提供