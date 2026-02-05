# API Documentation

## Base URL

- Local: `http://localhost:8080`
- Production: `https://flexbone-ocr-api-813818964446.us-central1.run.app`

## Authentication

When enabled (`AUTH_ENABLED=true`), include JWT token:
```
Authorization: Bearer <token>
```

### Get Token

**POST** `/api/v1/auth/token`

```json
{
  "username": "demo",
  "password": "demo123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Refresh Token

**POST** `/api/v1/auth/refresh`

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

## Endpoints

### Extract Text from Image

**POST** `/api/v1/ocr/extract`

**Request:**
- Content-Type: `multipart/form-data`
- Body: `image` - JPG, PNG, or GIF file (max 10MB)

**Example:**
```bash
curl -X POST \
  -F "image=@test.jpg" \
  https://flexbone-ocr-api-813818964446.us-central1.run.app/api/v1/ocr/extract
```

**Success Response (200):**
```json
{
  "success": true,
  "text": "Extracted text content here",
  "confidence": 0.95,
  "processing_time_ms": 847
}
```

**No Text Found Response (200):**
```json
{
  "success": true,
  "text": "",
  "confidence": 0.0,
  "processing_time_ms": 523,
  "message": "No text could be detected in the uploaded image"
}
```

**Error Response (400/401/413/415/429/500):**
```json
{
  "success": false,
  "error": {
    "code": "FILE_TOO_LARGE",
    "message": "File size exceeds maximum allowed size of 10MB",
    "details": {
      "max_size_mb": 10,
      "actual_size_mb": 15.5
    }
  },
  "metadata": {
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "processing_time_ms": 12
  }
}
```

### Batch Extract Text from Multiple Images

**POST** `/api/v1/ocr/batch`

**Request:**
- Content-Type: `multipart/form-data`
- Body: `images` - Multiple JPG, PNG, or GIF files (max 10 images, 10MB each)

**Example:**
```bash
curl -X POST \
  -F "images=@image1.jpg" \
  -F "images=@image2.jpg" \
  -F "images=@image3.png" \
  https://flexbone-ocr-api-813818964446.us-central1.run.app/api/v1/ocr/batch
```

**Success Response (200):**
```json
{
  "success": true,
  "total_images": 3,
  "successful": 2,
  "failed": 1,
  "total_processing_time_ms": 2500,
  "results": [
    {
      "filename": "image1.jpg",
      "success": true,
      "text": "Hello World",
      "confidence": 0.95,
      "processing_time_ms": 800,
      "error": null
    },
    {
      "filename": "image2.jpg",
      "success": true,
      "text": "Sample Text",
      "confidence": 0.92,
      "processing_time_ms": 750,
      "error": null
    },
    {
      "filename": "invalid.txt",
      "success": false,
      "text": null,
      "confidence": null,
      "processing_time_ms": null,
      "error": "Unsupported file type"
    }
  ]
}
```

## Health Check

**GET** `/api/v1/health`

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `FILE_TOO_LARGE` | 400 | File exceeds size limit |
| `UNSUPPORTED_FILE_TYPE` | 400 | Invalid file format |
| `INVALID_FILE` | 400 | Corrupted or invalid file |
| `AUTHENTICATION_FAILED` | 401 | Invalid credentials or token |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `OCR_PROCESSING_ERROR` | 500 | Vision API error |
| `INTERNAL_SERVER_ERROR` | 500 | Unexpected error |
