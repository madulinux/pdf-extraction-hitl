# 🚀 API Quick Reference Guide

**Base URL:** `http://localhost:8000`  
**Swagger UI:** [http://localhost:8000/api/docs](http://localhost:8000/api/docs)

---

## 📋 All Endpoints Summary

### 🔐 Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login and get JWT token |

### 📄 Templates
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/templates` | List all templates |
| GET | `/api/v1/templates/{id}` | Get template details |
| POST | `/api/v1/templates` | Create new template |
| PUT | `/api/v1/templates/{id}` | Update template |
| DELETE | `/api/v1/templates/{id}` | Delete template |

### 📊 Extraction
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/extraction/extract` | Extract data from PDF |
| GET | `/api/v1/extraction/documents` | List all documents |
| GET | `/api/v1/extraction/documents/{id}` | Get document details |
| POST | `/api/v1/extraction/feedback` | Submit corrections (HITL) |

### 🧠 Learning
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/learning/train` | Train/retrain CRF model |
| GET | `/api/v1/learning/models/{template_id}` | Get model info |
| GET | `/api/v1/learning/training-history/{template_id}` | Get training history |

### 🎯 Patterns
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/patterns/{template_id}` | Get extraction patterns |
| PUT | `/api/v1/patterns/{template_id}` | Update patterns |

### 🖼️ Preview
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/preview/generate` | Generate PDF preview image |

### 📈 Data Quality
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/templates/{id}/data-quality/latest` | Get latest metrics |
| GET | `/api/v1/templates/{id}/data-quality/history` | Get metrics history |

### 🎯 Strategy Performance
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/templates/{id}/strategy-performance` | Get all performance data |
| GET | `/api/v1/templates/{id}/strategy-performance/stats` | Get strategy statistics |
| GET | `/api/v1/templates/{id}/strategy-performance/fields/{field}` | Get field comparison |
| GET | `/api/v1/templates/{id}/strategy-performance/comparison` | Get all fields comparison |
| GET | `/api/v1/templates/{id}/strategy-performance/best` | Get best strategies |
| GET | `/api/v1/templates/{id}/strategy-performance/{strategy}` | Get strategy details |

---

## 🔥 Most Used Workflows

### 1️⃣ Complete Extraction Workflow
```bash
# Step 1: Extract document
curl -X POST http://localhost:8000/api/v1/extraction/extract \
  -F "file=@document.pdf" \
  -F "template_id=1"

# Step 2: Submit corrections
curl -X POST http://localhost:8000/api/v1/extraction/feedback \
  -H "Content-Type: application/json" \
  -d '{"document_id": 123, "corrections": {"field": "value"}}'

# Step 3: Retrain model
curl -X POST http://localhost:8000/api/v1/learning/train \
  -H "Content-Type: application/json" \
  -d '{"template_id": 1, "use_all_feedback": true}'
```

### 2️⃣ Check Strategy Performance
```bash
# Get overall stats
curl http://localhost:8000/api/v1/templates/1/strategy-performance/stats

# Get best strategies
curl http://localhost:8000/api/v1/templates/1/strategy-performance/best

# Get CRF performance
curl http://localhost:8000/api/v1/templates/1/strategy-performance/crf
```

### 3️⃣ Monitor Data Quality
```bash
# Get latest metrics
curl http://localhost:8000/api/v1/templates/1/data-quality/latest

# Get history
curl http://localhost:8000/api/v1/templates/1/data-quality/history?limit=10
```

---

## 📦 Response Format

### ✅ Success Response
```json
{
  "success": true,
  "message": "Operation successful",
  "data": {},
  "timestamp": "2024-01-15T10:00:00"
}
```

### ❌ Error Response
```json
{
  "success": false,
  "message": "Error description",
  "error": "Detailed error",
  "timestamp": "2024-01-15T10:00:00"
}
```

---

## 🔑 Authentication

Most endpoints require JWT token:

```bash
# Get token
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}' \
  | jq -r '.data.token')

# Use token
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/templates
```

---

## 🎯 Key Features

### Adaptive Learning (HITL)
1. **Extract** → System extracts data using hybrid strategy
2. **Validate** → User validates and corrects data
3. **Learn** → System learns from corrections
4. **Improve** → Model accuracy improves over time

### Strategy Types
- **CRF**: Conditional Random Fields (ML-based)
- **Rule-based**: Regex and pattern matching
- **Position-based**: Coordinate-based extraction

### Performance Tracking
- Per-field accuracy
- Per-strategy accuracy
- Best strategy selection
- Historical performance

---

## 📊 Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 404 | Not Found |
| 413 | File Too Large |
| 500 | Server Error |

---

## 🔗 Resources

- **Swagger UI**: http://localhost:8000/api/docs
- **OpenAPI Spec**: http://localhost:8000/apispec.json
- **Health Check**: http://localhost:8000/api/health
- **Full Documentation**: [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)

---

**Last Updated:** 2024-11-08  
**Version:** 1.0.0
