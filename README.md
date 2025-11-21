# 📄 Adaptive Learning System for PDF Template Data Extraction

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18.0+-61DAFB.svg)](https://reactjs.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Research-orange.svg)]()

> A Human-in-the-Loop (HITL) system that combines rule-based and machine learning approaches for efficient PDF template data extraction with minimal training data.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Research Contributions](#research-contributions)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage Guide](#usage-guide)
- [Experimental Results](#experimental-results)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Publications](#publications)
- [Citation](#citation)
- [License](#license)
- [Contact](#contact)

---

## 🎯 Overview

This project implements a novel **hybrid adaptive learning system** that addresses the challenge of extracting structured data from PDF template documents. Unlike traditional approaches that require either extensive manual rule configuration or large labeled datasets, our system learns incrementally from minimal user feedback.

### The Problem

Organizations process millions of PDF documents daily (forms, invoices, reports, contracts), but extracting structured data remains challenging:
- **Rule-based systems**: Efficient but rigid, requiring manual updates for each variation
- **Deep learning models**: High accuracy but need thousands of labeled documents and GPU resources
- **Existing HITL systems**: Limited to validation rather than actual learning

### Our Solution

A **hybrid architecture** that intelligently combines:
1. **Rule-based extraction** for structured fields (IDs, dates, phone numbers)
2. **CRF (Conditional Random Fields)** for context-dependent fields (names, addresses, descriptions)
3. **Human-in-the-Loop learning** that converts user corrections into system knowledge
4. **Confidence-based strategy selection** that chooses the best approach per field

### Key Achievement

**98.61% accuracy** with only **25-35 documents** and **7% user correction rate**, running on **CPU-only** hardware.

---

## ✨ Key Features

### 🎯 Core Capabilities

- **Minimal Data Requirement**: Achieves >95% accuracy with only 25-35 documents per template
- **Fast Convergence**: Reaches production-ready accuracy within 5-7 batches
- **Low User Burden**: Only 7% of fields require correction
- **Resource Efficient**: Runs on CPU-only hardware (50-100 MB footprint)
- **Real-time Processing**: 0.1-0.5 seconds per document
- **Incremental Learning**: CRF model updates without full retraining

### 🔧 Technical Features

- **Hybrid Strategy**: Intelligent combination of rule-based and CRF approaches
- **Confidence Scoring**: Dynamic per-field strategy selection
- **Pattern Learning**: Automatic rule generation from user feedback
- **Table Extraction**: Specialized handling for tabular data
- **BIO Tagging**: Sequence labeling for entity extraction
- **Post-processing**: Validation and cleanup of extracted data

### 🎨 User Interface

- **Interactive Feedback**: Visual correction interface
- **Real-time Validation**: Immediate feedback on corrections
- **Template Management**: Easy template creation and configuration
- **Performance Monitoring**: Track accuracy and learning progress
- **Batch Processing**: Efficient handling of multiple documents

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Upload     │  │  Extraction  │  │   Feedback   │      │
│  │  Interface   │  │   Results    │  │  Correction  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend (Flask API)                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Extraction Service                      │   │
│  │  ┌────────────────┐  ┌────────────────┐            │   │
│  │  │  Rule-Based    │  │  CRF Strategy  │            │   │
│  │  │   Strategy     │  │                │            │   │
│  │  └────────────────┘  └────────────────┘            │   │
│  │           │                  │                      │   │
│  │           └──────────┬───────┘                      │   │
│  │                      ▼                               │   │
│  │           ┌────────────────────┐                    │   │
│  │           │  Hybrid Selector   │                    │   │
│  │           │ (Confidence-based) │                    │   │
│  │           └────────────────────┘                    │   │
│  └──────────────────────────────────────────────────────┘   │
│                            │                                 │
│                            ▼                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Learning Service                        │   │
│  │  ┌────────────────┐  ┌────────────────┐            │   │
│  │  │ Pattern        │  │ CRF Incremental│            │   │
│  │  │ Learning       │  │   Training     │            │   │
│  │  └────────────────┘  └────────────────┘            │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Database (SQLite)                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │Templates │  │Documents │  │ Feedback │  │  Models  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Component Description

**Frontend (React + TypeScript)**
- Modern, responsive UI built with React 18
- Real-time feedback interface for corrections
- Document upload and preview
- Performance monitoring dashboard

**Backend (Flask + Python)**
- RESTful API for all operations
- Hybrid extraction engine
- Incremental learning system
- Template management

**Database (SQLite)**
- Document storage and metadata
- Feedback tracking for learning
- Template configurations
- Model versioning

---

## 🔬 Research Contributions

### 1. Methodological Contribution

**First systematic framework** integrating rule-based transparency with CRF statistical learning in HITL context:
- Confidence-based adaptive weighting mechanism
- Intelligent per-field strategy selection
- Dual learning pathways (pattern + CRF)

### 2. Practical Contribution

**Production-ready system** demonstrating competitive accuracy with minimal resources:
- 98.61% accuracy with only 25-35 documents
- 7% correction rate (minimal user effort)
- CPU-only, 50-100 MB footprint
- Fills gap between rigid rule-based and resource-intensive large models

### 3. Empirical Contribution

**Comprehensive evaluation** across 140 documents and 4 diverse template types:
- Statistical significance: p < 0.001, Cohen's d = 8.95
- Strong evidence for hybrid HITL effectiveness
- Validates generalization capability

---

## 🚀 Installation

### Prerequisites

- **Python**: 3.9 or higher
- **Node.js**: 16.0 or higher
- **npm**: 8.0 or higher
- **Operating System**: macOS, Linux, or Windows

### Backend Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/pdf-extraction-hitl.git
cd pdf-extraction-hitl

# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -c "from database.db_manager import DatabaseManager; DatabaseManager()"

# Run backend server
python app.py
```

Backend will run on `http://localhost:5000`

### Frontend Setup

```bash
# Navigate to frontend directory (from project root)
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will run on `http://localhost:3000`

---

## 🎯 Quick Start

### 1. Create a Template

```bash
# Using the API
curl -X POST http://localhost:5000/api/templates \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Invoice Template",
    "description": "Standard invoice format",
    "fields": [
      {"name": "invoice_number", "type": "text"},
      {"name": "date", "type": "date"},
      {"name": "total", "type": "number"}
    ]
  }'
```

### 2. Upload Documents

```bash
# Upload a PDF document
curl -X POST http://localhost:5000/api/documents/upload \
  -F "file=@invoice.pdf" \
  -F "template_id=1"
```

### 3. Extract Data

```bash
# Trigger extraction
curl -X POST http://localhost:5000/api/extract/1
```

### 4. Provide Feedback

```bash
# Submit corrections
curl -X POST http://localhost:5000/api/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": 1,
    "field_name": "invoice_number",
    "original_value": "INV-001",
    "corrected_value": "INV-0001"
  }'
```

### 5. Train Model

```bash
# Trigger incremental training
curl -X POST http://localhost:5000/api/train/1
```

---

## 📖 Usage Guide

### Template Configuration

Templates define the structure of documents to extract:

```python
{
  "name": "Form Template",
  "description": "Government form",
  "fields": [
    {
      "name": "id_number",
      "type": "text",
      "required": true,
      "validation_rule": "^[A-Z0-9]{10}$"
    },
    {
      "name": "birth_date",
      "type": "date",
      "format": "DD-MM-YYYY"
    },
    {
      "name": "address",
      "type": "text",
      "multiline": true
    }
  ]
}
```

### Extraction Strategies

The system automatically selects the best strategy per field:

**Rule-based Strategy** (for structured fields):
- Pattern matching with regex
- Position-based extraction
- Keyword-based search
- Best for: IDs, dates, phone numbers

**CRF Strategy** (for context-dependent fields):
- Sequence labeling with BIO tags
- Contextual feature extraction
- Statistical learning from feedback
- Best for: names, addresses, descriptions

**Hybrid Selection**:
```python
if confidence_rule > threshold and confidence_crf > threshold:
    # Use strategy with higher confidence
    result = max(rule_result, crf_result, key=lambda x: x.confidence)
elif confidence_rule > threshold:
    result = rule_result
elif confidence_crf > threshold:
    result = crf_result
else:
    # Fallback or request user input
    result = None
```

### Learning Process

1. **Initial Extraction**: System attempts extraction with baseline strategies
2. **User Feedback**: User corrects errors through UI
3. **Pattern Learning**: System identifies patterns in corrections
4. **CRF Training**: Model updates incrementally with new examples
5. **Improved Extraction**: Next documents benefit from learned patterns

### Batch Processing

```python
from core.extraction.services import ExtractionService

# Initialize service
service = ExtractionService(...)

# Process batch
results = service.extract_batch(
    template_id=1,
    document_ids=[1, 2, 3, 4, 5],
    batch_size=5
)

# Collect feedback
for doc_id, result in results.items():
    feedback = get_user_corrections(doc_id, result)
    service.submit_feedback(feedback)

# Trigger training after batch
service.train_model(template_id=1)
```

---

## 📊 Experimental Results

### Overall Performance

| Metric | Baseline | Adaptive | Improvement |
|--------|----------|----------|-------------|
| **Accuracy** | 72.64% | 98.61% | +35.74% (relative) |
| **Precision** | 73.15% | 98.64% | +34.84% |
| **Recall** | 99.00% | 99.97% | +0.97% |
| **F1-Score** | 84.12% | 99.29% | +18.03% |

### Template-Specific Results

| Template | Type | Baseline | Adaptive | Improvement |
|----------|------|----------|----------|-------------|
| Template 1 | Form | 76.76% | 100.00% | +23.24 pp |
| Template 2 | Table | 74.78% | 100.00% | +25.22 pp |
| Template 3 | Letter | 69.52% | 94.83% | +25.31 pp |
| Template 4 | Mixed | 69.52% | 99.59% | +30.07 pp |

### Learning Efficiency

- **Total Documents**: 140 (35 per template)
- **Total Fields**: 2,800
- **Corrections Required**: 196 (7%)
- **Corrections per Percentage Point**: 1.88
- **Batches to >95% Accuracy**: 5-7 batches
- **Learning Efficiency Score**: 14.09

### Statistical Significance

- **Paired t-test**: t(3) = 17.89, p < 0.001
- **Cohen's d**: 8.95 (very large effect size)
- **Conclusion**: Improvement is statistically significant and robust

### Error Reduction

- **False Positives**: 94.68% reduction (752 → 40)
- **False Negatives**: 95.24% reduction (21 → 1)
- **Overall Error Rate**: 94.92% reduction (27.35% → 1.39%)

### Performance Metrics

- **Processing Time**: 0.1-0.5 seconds per document
- **Memory Usage**: 50-100 MB
- **Training Time**: 2-5 seconds per batch (incremental)
- **Model Size**: 1-5 MB per template

---

## 📁 Project Structure

```
pdf-extraction-hitl/
│
├── backend/                      # Backend application
│   ├── app.py                   # Flask application entry point
│   ├── config.py                # Configuration settings
│   ├── requirements.txt         # Python dependencies
│   │
│   ├── api/                     # API routes
│   │   ├── auth.py             # Authentication endpoints
│   │   ├── documents.py        # Document management
│   │   ├── extraction.py       # Extraction endpoints
│   │   ├── feedback.py         # Feedback submission
│   │   └── templates.py        # Template management
│   │
│   ├── core/                    # Core business logic
│   │   ├── extraction/         # Extraction strategies
│   │   │   ├── rule_based_strategy.py
│   │   │   ├── crf_strategy.py
│   │   │   ├── hybrid_strategy.py
│   │   │   ├── table_extractor.py
│   │   │   └── services.py
│   │   │
│   │   ├── learning/           # Learning components
│   │   │   ├── learner.py      # CRF training
│   │   │   ├── pattern_learner.py
│   │   │   └── feedback_processor.py
│   │   │
│   │   └── preprocessing/      # Document preprocessing
│   │       ├── pdf_parser.py
│   │       └── text_cleaner.py
│   │
│   ├── database/               # Database layer
│   │   ├── db_manager.py       # Database connection
│   │   ├── models.py           # SQLAlchemy models
│   │   └── repositories/       # Data access layer
│   │       ├── document_repository.py
│   │       ├── feedback_repository.py
│   │       └── template_repository.py
│   │
│   ├── experiments/            # Experimental evaluation
│   │   ├── run_experiment.py   # Main experiment script
│   │   ├── evaluate_baseline.py
│   │   ├── evaluate_adaptive.py
│   │   └── results/            # Experiment results (JSON)
│   │
│   ├── data/                   # Data directory
│   │   └── app.db             # SQLite database
│   │
│   ├── models/                 # Trained models
│   │   └── template_*/        # Per-template models
│   │
│   └── uploads/               # Uploaded documents
│
├── frontend/                   # Frontend application
│   ├── package.json           # Node dependencies
│   ├── tsconfig.json          # TypeScript config
│   │
│   ├── src/
│   │   ├── App.tsx            # Main application
│   │   ├── main.tsx           # Entry point
│   │   │
│   │   ├── components/        # React components
│   │   │   ├── DocumentUpload.tsx
│   │   │   ├── ExtractionResults.tsx
│   │   │   ├── FeedbackForm.tsx
│   │   │   └── TemplateManager.tsx
│   │   │
│   │   ├── services/          # API services
│   │   │   ├── api.ts
│   │   │   └── auth.ts
│   │   │
│   │   └── types/             # TypeScript types
│   │       └── index.ts
│   │
│   └── public/                # Static assets
│
├── documents/                  # Research documentation
│   ├── jurnal/                # Journal paper (LaTeX)
│   │   ├── main.tex
│   │   ├── main.pdf
│   │   ├── sections/          # Paper sections
│   │   ├── tables/            # LaTeX tables
│   │   └── figures/           # Figures and charts
│   │
│   └── tesis/                 # Thesis documentation
│
├── tools/                      # Utility scripts
│   └── seeder/                # Data generation
│       └── generate_documents.py
│
├── .gitignore
├── LICENSE
└── README.md                   # This file
```

---

## 🔌 API Documentation

### Authentication

```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "password"
}

Response: 200 OK
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "admin"
  }
}
```

### Templates

```http
# Create template
POST /api/templates
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Invoice",
  "description": "Standard invoice",
  "fields": [...]
}

# Get all templates
GET /api/templates
Authorization: Bearer <token>

# Get template by ID
GET /api/templates/{id}
Authorization: Bearer <token>

# Update template
PUT /api/templates/{id}
Authorization: Bearer <token>

# Delete template
DELETE /api/templates/{id}
Authorization: Bearer <token>
```

### Documents

```http
# Upload document
POST /api/documents/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <pdf_file>
template_id: 1

# Get all documents
GET /api/documents?template_id=1
Authorization: Bearer <token>

# Get document by ID
GET /api/documents/{id}
Authorization: Bearer <token>

# Delete document
DELETE /api/documents/{id}
Authorization: Bearer <token>
```

### Extraction

```http
# Extract data from document
POST /api/extract/{document_id}
Authorization: Bearer <token>

Response: 200 OK
{
  "document_id": 1,
  "results": {
    "invoice_number": {
      "value": "INV-001",
      "confidence": 0.95,
      "strategy": "rule_based"
    },
    "date": {
      "value": "2024-01-15",
      "confidence": 0.98,
      "strategy": "rule_based"
    }
  }
}

# Batch extraction
POST /api/extract/batch
Authorization: Bearer <token>
Content-Type: application/json

{
  "template_id": 1,
  "document_ids": [1, 2, 3, 4, 5]
}
```

### Feedback

```http
# Submit feedback
POST /api/feedback
Authorization: Bearer <token>
Content-Type: application/json

{
  "document_id": 1,
  "field_name": "invoice_number",
  "original_value": "INV-001",
  "corrected_value": "INV-0001",
  "confidence": 0.95,
  "strategy_used": "rule_based"
}

# Get feedback for document
GET /api/feedback/document/{document_id}
Authorization: Bearer <token>

# Get feedback for template
GET /api/feedback/template/{template_id}
Authorization: Bearer <token>
```

### Training

```http
# Train model for template
POST /api/train/{template_id}
Authorization: Bearer <token>

Response: 200 OK
{
  "template_id": 1,
  "training_samples": 45,
  "model_version": 2,
  "accuracy": 0.9561,
  "training_time": 3.2
}

# Get training status
GET /api/train/status/{template_id}
Authorization: Bearer <token>
```

### Performance

```http
# Get performance metrics
GET /api/performance/{template_id}
Authorization: Bearer <token>

Response: 200 OK
{
  "template_id": 1,
  "accuracy": 0.9861,
  "precision": 0.9864,
  "recall": 0.9997,
  "f1_score": 0.9929,
  "total_documents": 35,
  "total_corrections": 24,
  "correction_rate": 0.07
}
```

---

## 📚 Publications

### Journal Paper

**Title**: Adaptive Learning System Based on Human-in-the-Loop for PDF Template Data Extraction

**Authors**: Moh Syaiful Rahman

**Abstract**: This research develops an adaptive learning system that integrates rule-based and CRF strategies in a Human-in-the-Loop framework for PDF template data extraction. The system achieves 98.61% accuracy with only 25-35 documents per template and 7% user correction rate, demonstrating effective learning from minimal data in resource-constrained environments.

**Status**: Ready for submission

**Paper Location**: `documents/jurnal/main.pdf`

### Key Findings

1. **Hybrid approach** yields 35.74% relative improvement over baseline
2. **Minimal data requirement**: 25-35 documents sufficient for >95% accuracy
3. **Low user burden**: Only 7% correction rate
4. **Fast convergence**: 5-7 batches to production-ready accuracy
5. **Resource efficient**: CPU-only, 50-100 MB footprint

---

## 📖 Citation

If you use this work in your research, please cite:

```bibtex
@article{yourname2025adaptive,
  title={Adaptive Learning System Based on Human-in-the-Loop for PDF Template Data Extraction},
  author={Your Name and Co-authors},
  journal={Journal Name},
  year={2025},
  note={Submitted}
}
```

---

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

### Reporting Issues

- Use GitHub Issues for bug reports and feature requests
- Provide detailed description and steps to reproduce
- Include system information and error messages

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Code Style

- **Python**: Follow PEP 8
- **TypeScript**: Follow Airbnb style guide
- **Commits**: Use conventional commits format

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2025 [Your Name]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 📞 Contact

**Author**: [madulinux](https://github.com/madulinux)  
**Email**: [madulinux@gmail.com]  
**Institution**: Universitas Nasional  
**GitHub**: [@madulinux](https://github.com/madulinux)

**Project Link**: [https://github.com/madulinux/pdf-extraction-hitl](https://github.com/madulinux/pdf-extraction-hitl)

---

## 🙏 Acknowledgments

- Universitas Nasional for providing research facilities and support
- Anonymous reviewers for valuable feedback
- Open-source community for excellent tools and libraries

---

## 📊 Project Statistics

![GitHub stars](https://img.shields.io/github/stars/yourusername/pdf-extraction-hitl?style=social)
![GitHub forks](https://img.shields.io/github/forks/yourusername/pdf-extraction-hitl?style=social)
![GitHub issues](https://img.shields.io/github/issues/yourusername/pdf-extraction-hitl)
![GitHub pull requests](https://img.shields.io/github/issues-pr/yourusername/pdf-extraction-hitl)

---

## 🗺️ Roadmap

### Version 1.0 (Current)
- ✅ Hybrid extraction (rule-based + CRF)
- ✅ Human-in-the-Loop learning
- ✅ Template management
- ✅ Batch processing
- ✅ Performance monitoring

### Version 1.1 (Planned)
- [ ] Deep learning integration (DistilBERT embeddings)
- [ ] Transfer learning across templates
- [ ] Multi-language support
- [ ] Enhanced table extraction
- [ ] API rate limiting

### Version 2.0 (Future)
- [ ] Reinforcement learning for HITL optimization
- [ ] Multi-modal processing (text + images)
- [ ] Cloud deployment support
- [ ] Real-time collaboration
- [ ] Advanced analytics dashboard

---

## ❓ FAQ

**Q: How much training data do I need?**  
A: Only 25-35 documents per template to reach >95% accuracy.

**Q: Do I need a GPU?**  
A: No, the system runs efficiently on CPU-only hardware.

**Q: How long does training take?**  
A: 2-5 seconds per batch (incremental training).

**Q: Can I use this for non-template documents?**  
A: The system is optimized for template-based documents. For unstructured documents, consider deep learning approaches.

**Q: Is this production-ready?**  
A: Yes, the system achieves 98.61% accuracy and has been tested on 140 documents across 4 template types.

**Q: How do I add a new template?**  
A: Use the template management API or UI to define fields and upload seed documents.

**Q: What PDF formats are supported?**  
A: Text-based PDFs. Scanned documents require OCR preprocessing.

---

<div align="center">

**⭐ Star this repository if you find it useful! ⭐**

Made with ❤️ for the research community

</div>
