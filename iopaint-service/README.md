# IOPaint Text Removal Service

**🌍 [中文](README.zh-CN.md) | [日本語](README.ja.md) | English**

🎯 **Professional microservice for advanced text inpainting and removal using IOPaint 1.6.0**

A production-ready, standalone microservice that provides powerful text removal capabilities with real-time progress tracking. Designed for easy integration into any application requiring high-quality text inpainting from images.

## ✨ Key Features

- 🔧 **Advanced Text Removal**: State-of-the-art IOPaint with LAMA model for seamless background preservation
- 🚀 **Real-time Processing**: WebSocket-based progress tracking for long-running tasks  
- 🎛️ **Multiple Processing Modes**: Synchronous, asynchronous, and batch processing support
- 🎨 **Flexible Input Methods**: Mask-based, region-based, and coordinate-based inpainting
- 🏗️ **Production Ready**: Docker containerization, health monitoring, and comprehensive error handling
- ⚡ **Performance Optimized**: GPU acceleration, memory management, and intelligent image scaling
- 🔌 **Easy Integration**: RESTful API with OpenAPI documentation and multiple SDKs
- 📊 **Advanced Monitoring**: Resource tracking, diagnostics, and processing analytics

## 📋 API Endpoints

### Core Endpoints
- `GET /` - Service information and status
- `GET /api/v1/health` - Health check
- `GET /api/v1/model` - Current model information
- `GET /api/v1/info` - Detailed service information

### Inpainting Endpoints
- `POST /api/v1/inpaint` - Inpaint with provided mask (returns image binary)
- `POST /api/v1/inpaint-regions` - Inpaint with text regions (returns image binary)
- `POST /api/v1/inpaint-regions-json` - Inpaint with text regions (returns JSON stats)

### Documentation
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation (ReDoc)

## 🛠️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `IOPAINT_HOST` | `0.0.0.0` | Service host address |
| `IOPAINT_PORT` | `8081` | Service port |
| `IOPAINT_MODEL` | `lama` | IOPaint model to use |
| `IOPAINT_DEVICE` | `cpu` | Device for processing (cpu/cuda/mps) |
| `IOPAINT_LOW_MEM` | `true` | Enable low memory mode |
| `IOPAINT_CPU_OFFLOAD` | `true` | Enable CPU offloading |
| `MAX_IMAGE_SIZE` | `2048` | Maximum image dimension |
| `MAX_FILE_SIZE` | `52428800` | Maximum file size (50MB) |
| `REQUEST_TIMEOUT` | `300` | Request timeout in seconds |
| `LOG_LEVEL` | `INFO` | Logging level |

### Supported Models
- **lama** (default) - Large Mask Inpainting model (best quality)
- **ldm** - Latent Diffusion Model
- **zits** - Incremental Transformer Structure
- **mat** - Mask-Aware Transformer
- **fcf** - Fourier Convolutions
- **manga** - Specialized for manga/anime images

## 🚢 Docker Deployment

### Standalone Deployment
```bash
# Build the image
docker build -t iopaint-service .

# Run the container
docker run -d \
  --name iopaint-service \
  -p 8081:8081 \
  -e IOPAINT_MODEL=lama \
  -e IOPAINT_DEVICE=cpu \
  iopaint-service
```

### With GPU Support
```bash
docker run -d \
  --name iopaint-service \
  --gpus all \
  -p 8081:8081 \
  -e IOPAINT_DEVICE=cuda \
  iopaint-service
```

### Docker Compose Integration
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

## 🔌 API Usage Examples

### Health Check
```bash
curl http://localhost:8081/api/v1/health
```

### Inpainting with Regions
```python
import requests
import base64

# Prepare image and regions
with open('image.jpg', 'rb') as f:
    image_b64 = base64.b64encode(f.read()).decode('utf-8')

regions = [
    {"x": 100, "y": 50, "width": 200, "height": 30},
    {"x": 150, "y": 200, "width": 150, "height": 25}
]

# Send request
response = requests.post(
    'http://localhost:8081/api/v1/inpaint-regions',
    json={
        "image": image_b64,
        "regions": regions
    }
)

# Save result
if response.status_code == 200:
    with open('result.png', 'wb') as f:
        f.write(response.content)
```

### Get Processing Stats
```python
response = requests.post(
    'http://localhost:8081/api/v1/inpaint-regions-json',
    json={
        "image": image_b64,
        "regions": regions
    }
)

stats = response.json()
print(f"Processed {stats['processing_stats']['regions_processed']} regions")
print(f"Processing time: {stats['processing_stats']['processing_time']:.2f}s")
```

## 🏗️ Development

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
python -m uvicorn app.main:app --host 0.0.0.0 --port 8081 --reload
```

### Testing
```bash
# Test health endpoint
curl http://localhost:8081/api/v1/health

# View API documentation
open http://localhost:8081/docs
```

## 📊 Monitoring

### Health Check Endpoint
The `/api/v1/health` endpoint provides service status:
```json
{
  "status": "healthy",
  "message": "IOPaint service is running",
  "timestamp": "2024-01-01T12:00:00",
  "version": "1.0.0"
}
```

### Service Metrics
Response headers include processing metrics:
- `X-Processing-Time`: Processing duration in seconds
- `X-Regions-Count`: Number of regions processed
- `X-Total-Area`: Total area processed in pixels
- `X-Timestamp`: Processing timestamp

## 🔧 Troubleshooting

### Common Issues

1. **Service startup timeout**
   - Increase startup timeout (models need to download on first run)
   - Check internet connection for model downloads
   - Ensure sufficient disk space for model cache

2. **Out of memory errors**
   - Enable `IOPAINT_LOW_MEM=true`
   - Enable `IOPAINT_CPU_OFFLOAD=true`
   - Reduce `MAX_IMAGE_SIZE`

3. **Slow processing**
   - Use GPU acceleration with `IOPAINT_DEVICE=cuda`
   - Consider faster models (fcf, zits) for speed over quality
   - Reduce image resolution

### Logs
Service logs provide detailed information about processing:
```bash
docker logs iopaint-service
```

## 📝 License

This service is part of the LabelTool project and follows the same licensing terms.