# Flexbone OCR API

Production-ready OCR text extraction API built with FastAPI and deployed on Google Cloud Run.

## Features

- Extract text from JPG/PNG images using Google Cloud Vision API
- Optional JWT authentication (configurable)
- Rate limiting support
- Confidence scores and language detection
- Health check endpoints for Cloud Run
- Auto-generated OpenAPI documentation
- Comprehensive test suite (80%+ coverage)

## Quick Start

### Prerequisites

- Python 3.11+
- Google Cloud account with Vision API enabled
- Service account with Vision API permissions

### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/flexbone-ocr-api.git
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

## License

MIT
