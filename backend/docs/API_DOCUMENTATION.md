# 📚 Adaptive PDF Data Extraction API Documentation

**Version:** 1.0.0  
**Base URL:** `http://localhost:8000`  
**Swagger UI:** `http://localhost:8000/api/docs`

---

## 🔐 Authentication

Most endpoints require JWT authentication via Bearer token.

**Header Format:**
```
Authorization: Bearer <your_jwt_token>
```

---

## 📑 Table of Contents

1. [Authentication](#1-authentication)
2. [Templates](#2-templates)
3. [Extraction](#3-extraction)
4. [Learning](#4-learning)
5. [Patterns](#5-patterns)
6. [Preview](#6-preview)
7. [Data Quality](#7-data-quality)
8. [Strategy Performance](#8-strategy-performance)

---

## 1. Authentication

### 1.1 Register User

**POST** `/api/v1/auth/register`

Register a new user account.

**Request Body:**
```json
{
  "username": "string",
  "email": "string",
  "password": "string"
}
```

**Response (201):**
```json
{
  "success": true,
  "message": "User registered successfully",
  "data": {
    "user_id": 1,
    "username": "john_doe",
    "email": "john@example.com"
  }
}
```

---

### 1.2 Login

**POST** `/api/v1/auth/login`

Authenticate and receive JWT token.

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": 1,
      "username": "john_doe",
      "email": "john@example.com"
    }
  }
}
```

---

## 2. Templates

### 2.1 List Templates

**GET** `/api/v1/templates`

Get all templates.

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "Certificate Template",
      "description": "Training certificate template",
      "created_at": "2024-01-01T00:00:00",
      "fields_count": 9
    }
  ]
}
```

---

### 2.2 Get Template Details

**GET** `/api/v1/templates/{template_id}`

Get detailed information about a specific template.

**Parameters:**
- `template_id` (path, integer, required): Template ID

**Response (200):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Certificate Template",
    "description": "Training certificate template",
    "config": {
      "fields": {
        "recipient_name": {
          "type": "text",
          "required": true,
          "pattern": "^[A-Za-z\\s]+$"
        }
      }
    },
    "created_at": "2024-01-01T00:00:00"
  }
}
```

---

### 2.3 Create Template

**POST** `/api/v1/templates`

Create a new template by analyzing a PDF.

**Request:**
- Content-Type: `multipart/form-data`
- Body:
  - `file` (file, required): PDF template file
  - `name` (string, required): Template name
  - `description` (string, optional): Template description

**Response (201):**
```json
{
  "success": true,
  "message": "Template created successfully",
  "data": {
    "template_id": 1,
    "name": "Certificate Template",
    "fields_detected": 9
  }
}
```

---

### 2.4 Update Template

**PUT** `/api/v1/templates/{template_id}`

Update template configuration.

**Parameters:**
- `template_id` (path, integer, required): Template ID

**Request Body:**
```json
{
  "name": "string",
  "description": "string",
  "config": {
    "fields": {}
  }
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Template updated successfully"
}
```

---

### 2.5 Delete Template

**DELETE** `/api/v1/templates/{template_id}`

Delete a template.

**Parameters:**
- `template_id` (path, integer, required): Template ID

**Response (200):**
```json
{
  "success": true,
  "message": "Template deleted successfully"
}
```

---

## 3. Extraction

### 3.1 Extract Document

**POST** `/api/v1/extraction/extract`

Extract data from a PDF document using a template.

**Request:**
- Content-Type: `multipart/form-data`
- Body:
  - `file` (file, required): PDF document to extract
  - `template_id` (integer, required): Template ID to use

**Response (200):**
```json
{
  "success": true,
  "data": {
    "document_id": 123,
    "extracted_data": {
      "recipient_name": "John Doe",
      "certificate_number": "CERT-001",
      "issue_date": "2024-01-15"
    },
    "extraction_methods": {
      "recipient_name": "crf",
      "certificate_number": "position_based",
      "issue_date": "crf"
    },
    "confidence_scores": {
      "recipient_name": 0.95,
      "certificate_number": 0.98,
      "issue_date": 0.92
    }
  }
}
```

---

### 3.2 Get Document

**GET** `/api/v1/extraction/documents/{document_id}`

Get extraction results for a specific document.

**Parameters:**
- `document_id` (path, integer, required): Document ID

**Response (200):**
```json
{
  "success": true,
  "data": {
    "id": 123,
    "template_id": 1,
    "filename": "certificate_001.pdf",
    "extracted_data": {},
    "extraction_methods": {},
    "created_at": "2024-01-15T10:30:00"
  }
}
```

---

### 3.3 Submit Feedback

**POST** `/api/v1/extraction/feedback`

Submit corrections for extracted data (Human-in-the-Loop).

**Request Body:**
```json
{
  "document_id": 123,
  "corrections": {
    "recipient_name": "Corrected Name",
    "issue_date": "2024-01-20"
  }
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Feedback submitted successfully",
  "data": {
    "feedback_ids": [1, 2],
    "document_id": 123,
    "corrections_count": 2
  }
}
```

---

### 3.4 List Documents

**GET** `/api/v1/extraction/documents`

Get list of all extracted documents.

**Query Parameters:**
- `template_id` (integer, optional): Filter by template
- `limit` (integer, optional, default: 50): Number of results
- `offset` (integer, optional, default: 0): Pagination offset

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "id": 123,
      "template_id": 1,
      "filename": "certificate_001.pdf",
      "created_at": "2024-01-15T10:30:00"
    }
  ],
  "count": 1,
  "total": 100
}
```

---

## 4. Learning

### 4.1 Train Model

**POST** `/api/v1/learning/train`

Train or retrain CRF model for a template.

**Request Body:**
```json
{
  "template_id": 1,
  "use_all_feedback": true,
  "is_incremental": false,
  "force_validation": false
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Model trained successfully",
  "data": {
    "template_id": 1,
    "training_samples": 150,
    "validation_accuracy": 0.92,
    "model_path": "models/template_1_model.joblib",
    "training_time": 12.5,
    "data_quality": {
      "leakage_detected": false,
      "diversity_score": 0.85
    }
  }
}
```

---

### 4.2 Get Model Info

**GET** `/api/v1/learning/models/{template_id}`

Get information about trained model.

**Parameters:**
- `template_id` (path, integer, required): Template ID

**Response (200):**
```json
{
  "success": true,
  "data": {
    "template_id": 1,
    "model_exists": true,
    "model_path": "models/template_1_model.joblib",
    "last_trained": "2024-01-15T10:00:00",
    "training_samples": 150,
    "accuracy": 0.92
  }
}
```

---

### 4.3 Get Training History

**GET** `/api/v1/learning/training-history/{template_id}`

Get training history for a template.

**Parameters:**
- `template_id` (path, integer, required): Template ID
- `limit` (query, integer, optional, default: 10): Number of records

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "template_id": 1,
      "training_samples": 150,
      "accuracy": 0.92,
      "trained_at": "2024-01-15T10:00:00"
    }
  ]
}
```

---

## 5. Patterns

### 5.1 Get Patterns

**GET** `/api/v1/patterns/{template_id}`

Get extraction patterns for a template.

**Parameters:**
- `template_id` (path, integer, required): Template ID

**Response (200):**
```json
{
  "success": true,
  "data": {
    "template_id": 1,
    "patterns": {
      "recipient_name": {
        "regex": "^[A-Za-z\\s]+$",
        "position": {"x": 100, "y": 200}
      }
    }
  }
}
```

---

### 5.2 Update Patterns

**PUT** `/api/v1/patterns/{template_id}`

Update extraction patterns.

**Parameters:**
- `template_id` (path, integer, required): Template ID

**Request Body:**
```json
{
  "patterns": {
    "recipient_name": {
      "regex": "^[A-Za-z\\s]+$",
      "position": {"x": 100, "y": 200}
    }
  }
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Patterns updated successfully"
}
```

---

## 6. Preview

### 6.1 Generate Preview

**POST** `/api/v1/preview/generate`

Generate preview image from PDF.

**Request:**
- Content-Type: `multipart/form-data`
- Body:
  - `file` (file, required): PDF file
  - `page` (integer, optional, default: 1): Page number

**Response (200):**
```json
{
  "success": true,
  "data": {
    "preview_url": "/uploads/previews/abc123.png",
    "width": 1200,
    "height": 1600
  }
}
```

---

## 7. Data Quality

### 7.1 Get Latest Metrics

**GET** `/api/v1/templates/{template_id}/data-quality/latest`

Get latest data quality metrics for a template.

**Parameters:**
- `template_id` (path, integer, required): Template ID

**Response (200):**
```json
{
  "success": true,
  "metrics": {
    "template_id": 1,
    "leakage_detected": false,
    "leakage_score": 0.02,
    "diversity_score": 0.85,
    "recommendations": [
      "Data quality is good",
      "Consider adding more diverse samples"
    ],
    "checked_at": "2024-01-15T10:00:00"
  }
}
```

---

### 7.2 Get Metrics History

**GET** `/api/v1/templates/{template_id}/data-quality/history`

Get history of data quality metrics.

**Parameters:**
- `template_id` (path, integer, required): Template ID
- `limit` (query, integer, optional, default: 10): Number of records

**Response (200):**
```json
{
  "success": true,
  "count": 5,
  "metrics": [
    {
      "id": 1,
      "template_id": 1,
      "leakage_detected": false,
      "diversity_score": 0.85,
      "checked_at": "2024-01-15T10:00:00"
    }
  ]
}
```

---

## 8. Strategy Performance

### 8.1 Get All Performance Data

**GET** `/api/v1/templates/{template_id}/strategy-performance`

Get all strategy performance data for a template.

**Parameters:**
- `template_id` (path, integer, required): Template ID

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "template_id": 1,
      "field_name": "recipient_name",
      "strategy_type": "crf",
      "accuracy": 0.90,
      "total_extractions": 100,
      "correct_extractions": 90,
      "last_updated": "2024-01-15T10:00:00"
    }
  ],
  "count": 27
}
```

---

### 8.2 Get Strategy Statistics

**GET** `/api/v1/templates/{template_id}/strategy-performance/stats`

Get aggregated statistics for each strategy.

**Parameters:**
- `template_id` (path, integer, required): Template ID

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "strategy_type": "crf",
      "total_fields": 9,
      "avg_accuracy": 67.14,
      "total_extractions": 499,
      "total_correct": 355,
      "best_field": "supervisor_name",
      "best_field_accuracy": 96.51,
      "worst_field": "event_name",
      "worst_field_accuracy": 0.0
    },
    {
      "strategy_type": "rule_based",
      "total_fields": 9,
      "avg_accuracy": 41.5,
      "total_extractions": 958,
      "total_correct": 403,
      "best_field": "certificate_number",
      "best_field_accuracy": 87.5,
      "worst_field": "event_location",
      "worst_field_accuracy": 0.0
    }
  ],
  "template_id": 1
}
```

---

### 8.3 Get Field Performance Comparison

**GET** `/api/v1/templates/{template_id}/strategy-performance/fields/{field_name}`

Get performance comparison for a specific field.

**Parameters:**
- `template_id` (path, integer, required): Template ID
- `field_name` (path, string, required): Field name

**Response (200):**
```json
{
  "success": true,
  "data": {
    "field_name": "recipient_name",
    "strategies": [
      {
        "strategy_type": "crf",
        "accuracy": 90.0,
        "total_extractions": 100,
        "correct_extractions": 90
      },
      {
        "strategy_type": "rule_based",
        "accuracy": 75.0,
        "total_extractions": 100,
        "correct_extractions": 75
      }
    ],
    "best_strategy": "crf",
    "best_accuracy": 90.0
  }
}
```

---

### 8.4 Get All Fields Comparison

**GET** `/api/v1/templates/{template_id}/strategy-performance/comparison`

Get strategy comparison for all fields.

**Parameters:**
- `template_id` (path, integer, required): Template ID

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "field_name": "certificate_number",
      "best_strategy": "position_based",
      "best_accuracy": 100.0,
      "strategies": [...]
    },
    {
      "field_name": "recipient_name",
      "best_strategy": "crf",
      "best_accuracy": 90.0,
      "strategies": [...]
    }
  ],
  "template_id": 1,
  "total_fields": 9
}
```

---

### 8.5 Get Best Strategies

**GET** `/api/v1/templates/{template_id}/strategy-performance/best`

Get best performing strategy for each field.

**Parameters:**
- `template_id` (path, integer, required): Template ID

**Response (200):**
```json
{
  "success": true,
  "data": {
    "certificate_number": {
      "strategy": "position_based",
      "accuracy": 100.0
    },
    "recipient_name": {
      "strategy": "crf",
      "accuracy": 90.0
    },
    "issue_date": {
      "strategy": "crf",
      "accuracy": 92.31
    }
  },
  "template_id": 1
}
```

---

### 8.6 Get Strategy-Specific Performance

**GET** `/api/v1/templates/{template_id}/strategy-performance/{strategy_type}`

Get all fields and their performance for a specific strategy.

**Parameters:**
- `template_id` (path, integer, required): Template ID
- `strategy_type` (path, string, required): Strategy type (crf, rule_based, position_based)

**Response (200):**
```json
{
  "success": true,
  "data": {
    "strategy_type": "crf",
    "fields": [
      {
        "field_name": "supervisor_name",
        "accuracy": 0.9651,
        "total_extractions": 83,
        "correct_extractions": 80
      },
      {
        "field_name": "issue_date",
        "accuracy": 0.9231,
        "total_extractions": 65,
        "correct_extractions": 60
      }
    ],
    "summary": {
      "avg_accuracy": 67.14,
      "total_fields": 9,
      "total_extractions": 499,
      "total_correct": 355
    }
  }
}
```

---

## 🔄 Common Response Formats

### Success Response
```json
{
  "success": true,
  "message": "Operation successful",
  "data": {},
  "timestamp": "2024-01-15T10:00:00"
}
```

### Error Response
```json
{
  "success": false,
  "message": "Error description",
  "error": "Detailed error message",
  "timestamp": "2024-01-15T10:00:00"
}
```

---

## 📊 Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 413 | File Too Large (>16MB) |
| 500 | Internal Server Error |

---

## 🚀 Quick Start Examples

### Example 1: Extract Document with Feedback Loop

```bash
# 1. Upload and extract document
curl -X POST http://localhost:8000/api/v1/extraction/extract \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@certificate.pdf" \
  -F "template_id=1"

# Response: { "data": { "document_id": 123, "extracted_data": {...} } }

# 2. Submit corrections
curl -X POST http://localhost:8000/api/v1/extraction/feedback \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": 123,
    "corrections": {
      "recipient_name": "Corrected Name"
    }
  }'

# 3. Retrain model with feedback
curl -X POST http://localhost:8000/api/v1/learning/train \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": 1,
    "use_all_feedback": true,
    "is_incremental": true
  }'
```

### Example 2: Check Strategy Performance

```bash
# Get strategy statistics
curl -X GET http://localhost:8000/api/v1/templates/1/strategy-performance/stats

# Get best strategies for all fields
curl -X GET http://localhost:8000/api/v1/templates/1/strategy-performance/best

# Get CRF performance details
curl -X GET http://localhost:8000/api/v1/templates/1/strategy-performance/crf
```

---

## 📝 Notes

1. **Authentication**: Most endpoints require JWT token in Authorization header
2. **File Upload**: Maximum file size is 16MB
3. **Rate Limiting**: Currently no rate limiting implemented
4. **CORS**: Enabled for development (configure for production)
5. **Swagger UI**: Interactive API documentation available at `/api/docs`

---

## 🔗 Additional Resources

- **Swagger UI**: http://localhost:8000/api/docs
- **OpenAPI Spec**: http://localhost:8000/apispec.json
- **Health Check**: http://localhost:8000/api/health

---

**Last Updated:** 2024-11-08  
**API Version:** 1.0.0
