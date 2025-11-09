# 📚 API Documentation

Welcome to the **Adaptive PDF Data Extraction System** API documentation.

---

## 📖 Available Documentation

### 1. **[API Documentation](./API_DOCUMENTATION.md)** 📘
Complete API reference with detailed descriptions, request/response examples, and all available endpoints.

**Best for:**
- Understanding all API capabilities
- Detailed request/response schemas
- Complete endpoint specifications
- Integration planning

### 2. **[Quick Reference Guide](./API_QUICK_REFERENCE.md)** ⚡
Quick lookup table of all endpoints with common workflows and examples.

**Best for:**
- Quick endpoint lookup
- Common workflow examples
- Fast reference during development
- Copy-paste code snippets

### 3. **[Swagger UI](http://localhost:8000/api/docs)** 🎨
Interactive API documentation with live testing capabilities.

**Best for:**
- Testing endpoints directly
- Exploring API interactively
- Viewing real-time responses
- Understanding request formats

---

## 🚀 Quick Start

### 1. Start the Server
```bash
cd backend
python app.py
```

### 2. Access Documentation
- **Swagger UI**: http://localhost:8000/api/docs
- **API Spec**: http://localhost:8000/apispec.json
- **Health Check**: http://localhost:8000/api/health

### 3. Test an Endpoint
```bash
# Health check
curl http://localhost:8000/api/health

# Get templates
curl http://localhost:8000/api/v1/templates
```

---

## 📋 API Overview

### Core Features

#### 🔐 **Authentication**
- User registration and login
- JWT token-based authentication
- Secure endpoint protection

#### 📄 **Template Management**
- Create templates from PDF analysis
- Update and delete templates
- Field configuration management

#### 📊 **Document Extraction**
- Hybrid extraction strategy (CRF + Rule-based + Position-based)
- Confidence scoring
- Strategy selection based on historical performance

#### 🧠 **Adaptive Learning (HITL)**
- Human-in-the-Loop feedback
- Incremental model training
- Performance tracking and improvement

#### 📈 **Strategy Performance**
- Per-field accuracy tracking
- Per-strategy performance metrics
- Best strategy recommendations
- Historical performance analysis

#### 🎯 **Data Quality**
- Leakage detection
- Diversity scoring
- Training recommendations

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Frontend (Next.js)                │
└─────────────────────┬───────────────────────────────┘
                      │ HTTP/REST
┌─────────────────────▼───────────────────────────────┐
│              Flask REST API (Backend)               │
├─────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌─────────────────┐  │
│  │  Auth    │  │Templates │  │   Extraction    │  │
│  └──────────┘  └──────────┘  └─────────────────┘  │
│  ┌──────────┐  ┌──────────┐  ┌─────────────────┐  │
│  │ Learning │  │ Patterns │  │ Data Quality    │  │
│  └──────────┘  └──────────┘  └─────────────────┘  │
│  ┌──────────────────────────────────────────────┐  │
│  │      Strategy Performance Tracking           │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│              Core Business Logic                    │
├─────────────────────────────────────────────────────┤
│  • HybridExtractionStrategy (CRF + Rules + Pos)    │
│  • AdaptiveLearner (Incremental Training)          │
│  • PostProcessor (Data Cleaning)                   │
│  • ValidationStrategy (Data Quality)               │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│                  Data Layer                         │
├─────────────────────────────────────────────────────┤
│  • SQLite Database (Metadata, Performance)         │
│  • File Storage (PDFs, Models, Configs)            │
│  • Repository Pattern (Data Access)                │
└─────────────────────────────────────────────────────┘
```

---

## 🎯 Key Concepts

### Hybrid Extraction Strategy
The system uses three extraction strategies and selects the best one based on historical performance:

1. **CRF (Conditional Random Fields)** - ML-based sequence labeling
2. **Rule-based** - Regex and pattern matching
3. **Position-based** - Coordinate-based extraction

**Selection Formula:**
```
score = (confidence × 0.3) + (strategy_weight × 0.2) + (historical_accuracy × 0.5)
```

### Human-in-the-Loop (HITL)
1. System extracts data
2. User validates and corrects
3. Corrections become training data
4. Model retrains and improves
5. Accuracy increases over time

### Adaptive Learning
- **Incremental Training**: Add new data without full retrain
- **Performance Tracking**: Monitor accuracy per field and strategy
- **Strategy Selection**: Automatically choose best strategy
- **Data Quality**: Ensure training data quality

---

## 📊 Performance Metrics

### Strategy Performance
- **Accuracy**: Correct extractions / Total extractions
- **Coverage**: Fields covered by each strategy
- **Confidence**: Model confidence scores
- **Selection Rate**: How often each strategy is chosen

### Data Quality
- **Leakage Score**: Train/test data overlap
- **Diversity Score**: Sample variety
- **Recommendations**: Actionable insights

---

## 🔧 Configuration

### Environment Variables
```bash
FLASK_ENV=development
FLASK_DEBUG=True
PORT=8000
DATABASE_PATH=data/app.db
UPLOAD_FOLDER=uploads
MODEL_FOLDER=models
MAX_CONTENT_LENGTH=16777216  # 16MB
```

### Swagger Configuration
```python
# In app.py
swagger_config = {
    "specs_route": "/api/docs",
    "swagger_ui": True
}
```

---

## 🧪 Testing

### Manual Testing
Use Swagger UI at http://localhost:8000/api/docs

### cURL Examples
See [Quick Reference Guide](./API_QUICK_REFERENCE.md)

### Postman Collection
Import OpenAPI spec from http://localhost:8000/apispec.json

---

## 📝 Response Standards

All API responses follow a consistent format:

### Success
```json
{
  "success": true,
  "message": "Operation successful",
  "data": {},
  "timestamp": "2024-01-15T10:00:00"
}
```

### Error
```json
{
  "success": false,
  "message": "Error description",
  "error": "Detailed error message",
  "timestamp": "2024-01-15T10:00:00"
}
```

---

## 🔐 Security

### Authentication
- JWT token-based authentication
- Bearer token in Authorization header
- Token expiration and refresh

### File Upload
- Max file size: 16MB
- Allowed types: PDF only
- Virus scanning (recommended for production)

### CORS
- Configured for development
- Restrict origins in production

---

## 📈 Monitoring

### Health Check
```bash
curl http://localhost:8000/api/health
```

### Performance Metrics
- Strategy accuracy per field
- Model training time
- Extraction time per document
- API response times

---

## 🚀 Deployment

### Development
```bash
python app.py
```

### Production
```bash
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### Docker
```dockerfile
FROM python:3.12
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:app"]
```

---

## 📞 Support

For questions or issues:
- **Email**: support@example.com
- **Documentation**: This directory
- **Swagger UI**: http://localhost:8000/api/docs

---

## 📄 License

Copyright © 2024. All rights reserved.

---

**Last Updated:** 2024-11-08  
**API Version:** 1.0.0  
**Documentation Version:** 1.0.0
