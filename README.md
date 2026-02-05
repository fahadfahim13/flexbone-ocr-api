# Flexbone OCR API

Production-ready OCR text extraction API built with FastAPI and deployed on Google Cloud Run.

## Live Demo

**Public URL:** https://flexbone-ocr-api-813818964446.us-central1.run.app

## Features

- Extract text from JPG/PNG/GIF images using Google Cloud Vision API
- **Batch processing** - Extract text from multiple images in one request
- **Text preprocessing** - Automatic cleanup and normalization of extracted text
- **Intelligent caching** - Identical images return cached results instantly
- Optional JWT authentication (configurable)
- Rate limiting support
- Confidence scores and language detection
- Health check endpoint for Cloud Run
- Auto-generated OpenAPI documentation
- Comprehensive test suite

## Quick Start

### Prerequisites

- Python 3.11+
- Google Cloud account with Vision API enabled
- Service account with Vision API permissions

### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/fahadfahim13/flexbone-ocr-api.git
   cd flexbone-ocr-api
   ```

2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   make dev
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your GCP project ID and credentials path
   ```

5. Run the server:
   ```bash
   make run
   ```

6. Open http://localhost:8080/docs for API documentation

## API Usage

### Extract Text (No Auth)

```bash
curl -X POST \
  -F "image=@/path/to/image.jpg" \
  http://localhost:8080/api/v1/ocr/extract
```

### Extract Text (With Auth)

```bash
# Get token
TOKEN=$(curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"demo123"}' \
  http://localhost:8080/api/v1/auth/token | jq -r '.access_token')

# Use token
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -F "image=@/path/to/image.jpg" \
  http://localhost:8080/api/v1/ocr/extract
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `GCP_PROJECT_ID` | required | Google Cloud project ID |
| `AUTH_ENABLED` | `false` | Enable JWT authentication |
| `JWT_SECRET_KEY` | required if auth | Secret for JWT signing |
| `RATE_LIMIT_ENABLED` | `false` | Enable rate limiting |
| `MAX_FILE_SIZE_MB` | `10` | Maximum upload size |
| `LOG_LEVEL` | `INFO` | Logging level |

## Testing

```bash
make test        # Run tests with coverage
make test-cov    # Generate HTML coverage report
```

## Code Quality

```bash
make lint        # Run linter
make format      # Format code
make type-check  # Run type checker
make security    # Run security scanner
make check       # Run all checks
```

## Docker

```bash
make docker-build  # Build Docker image
make docker-run    # Run with docker-compose
```

## Deployment

The project includes GitHub Actions workflows for:
- CI: Linting, testing, and building on every push
- CD: Automatic deployment to Cloud Run on push to main

See `.github/workflows/` for details.

## Implementation

### OCR Service

This API uses **Google Cloud Vision API** for text extraction. The Vision API provides:
- High accuracy text detection using machine learning
- Support for multiple languages
- Confidence scores for extracted text
- Handles various image qualities and text orientations

### File Upload & Validation

File uploads are validated through multiple layers:

1. **File Size Check**: Rejects files larger than 10MB
2. **Extension Validation**: Only accepts `.jpg`, `.jpeg`, and `.png` files
3. **MIME Type Validation**: Verifies actual file content using magic bytes (not just extension)
4. **Image Integrity Check**: Opens and validates image using Pillow to ensure it's not corrupted

### Caching

The API implements intelligent caching for identical images:
- Uses SHA256 hash of image content as cache key
- Caches up to 100 results with 1-hour TTL
- Subsequent requests for the same image return instantly
- Significantly reduces Vision API costs and latency for repeated images

### Deployment Strategy

The API is deployed on **Google Cloud Run** with the following configuration:
- **Containerized**: Multi-stage Docker build with Python 3.11-slim
- **Auto-scaling**: 0-10 instances based on traffic
- **Memory**: 512Mi per instance
- **Timeout**: 60 seconds per request
- **CI/CD**: GitHub Actions automatically deploys on push to main branch

## Testing Instructions

### Test the Live API

**Health Check:**
```bash
curl https://flexbone-ocr-api-813818964446.us-central1.run.app/api/v1/health
```

**Extract Text from Image:**
```bash
curl -X POST -F "image=@your-image.jpg" https://flexbone-ocr-api-813818964446.us-central1.run.app/api/v1/ocr/extract
```

**Example Response:**
```json
{
  "success": true,
  "text": "LOVE\nJOY\nPEACE",
  "confidence": 0.95,
  "processing_time_ms": 847
}
```

### Test with Sample Images

```bash
# Test with any JPG image
curl -X POST -F "image=@test.jpg" https://flexbone-ocr-api-813818964446.us-central1.run.app/api/v1/ocr/extract

# Test with PNG image
curl -X POST -F "image=@test.png" https://flexbone-ocr-api-813818964446.us-central1.run.app/api/v1/ocr/extract

# Test with GIF image
curl -X POST -F "image=@test.gif" https://flexbone-ocr-api-813818964446.us-central1.run.app/api/v1/ocr/extract
```

### Batch Processing (Multiple Images)

```bash
curl -X POST \
  -F "images=@image1.jpg" \
  -F "images=@image2.jpg" \
  -F "images=@image3.png" \
  https://flexbone-ocr-api-813818964446.us-central1.run.app/api/v1/ocr/batch
```

### Interactive API Documentation

Visit the Swagger UI for interactive testing:
https://flexbone-ocr-api-813818964446.us-central1.run.app/docs

## License

MIT
