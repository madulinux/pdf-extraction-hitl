# Contributing to PDF Extraction HITL

Thank you for your interest in contributing to this project! This document provides guidelines and instructions for contributing.

## 🤝 How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with:
- Clear, descriptive title
- Detailed description of the problem
- Steps to reproduce
- Expected vs actual behavior
- System information (OS, Python version, etc.)
- Error messages and stack traces

### Suggesting Features

Feature requests are welcome! Please:
- Check if the feature already exists or is planned
- Clearly describe the feature and its use case
- Explain why it would be valuable
- Provide examples if possible

### Pull Requests

1. **Fork the repository**
   ```bash
   git clone https://github.com/yourusername/pdf-extraction-hitl.git
   cd pdf-extraction-hitl
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Write clean, documented code
   - Follow existing code style
   - Add tests for new features
   - Update documentation

4. **Test your changes**
   ```bash
   # Backend tests
   cd backend
   pytest
   
   # Frontend tests
   cd frontend
   npm test
   ```

5. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add amazing feature"
   ```
   
   Use conventional commits:
   - `feat:` new feature
   - `fix:` bug fix
   - `docs:` documentation changes
   - `style:` formatting, missing semicolons, etc.
   - `refactor:` code restructuring
   - `test:` adding tests
   - `chore:` maintenance tasks

6. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then create a Pull Request on GitHub.

## 📝 Code Style

### Python (Backend)

Follow PEP 8:
```python
# Good
def extract_field(document: Document, field_name: str) -> Optional[str]:
    """Extract a field from document.
    
    Args:
        document: The document to extract from
        field_name: Name of the field to extract
        
    Returns:
        Extracted value or None if not found
    """
    result = document.get_field(field_name)
    return result.value if result else None

# Bad
def extractField(doc,field):
    result=doc.getField(field)
    return result.value if result else None
```

### TypeScript (Frontend)

Follow Airbnb style guide:
```typescript
// Good
interface ExtractionResult {
  value: string;
  confidence: number;
  strategy: string;
}

const extractData = async (documentId: number): Promise<ExtractionResult> => {
  const response = await api.get(`/extract/${documentId}`);
  return response.data;
};

// Bad
interface extractionResult {
  value:string
  confidence:number
  strategy:string
}

const ExtractData = async (documentId) => {
  const response = await api.get('/extract/' + documentId)
  return response.data
}
```

## 🧪 Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run specific test file
pytest tests/test_extraction.py

# Run with coverage
pytest --cov=core --cov-report=html
```

### Frontend Tests

```bash
cd frontend

# Run all tests
npm test

# Run with coverage
npm test -- --coverage

# Run specific test
npm test -- DocumentUpload.test.tsx
```

## 📚 Documentation

- Update README.md for user-facing changes
- Add docstrings to all functions and classes
- Update API documentation for endpoint changes
- Add comments for complex logic

## 🔍 Code Review Process

1. **Automated Checks**
   - All tests must pass
   - Code coverage should not decrease
   - Linting must pass

2. **Manual Review**
   - Code quality and style
   - Documentation completeness
   - Test coverage
   - Performance implications

3. **Approval**
   - At least one maintainer approval required
   - All comments addressed
   - CI/CD pipeline green

## 🎯 Development Setup

### Backend Development

```bash
cd backend

# Install development dependencies
pip install -r requirements-dev.txt

# Run in development mode
export FLASK_ENV=development
python app.py

# Run linter
flake8 .

# Run type checker
mypy .
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Run linter
npm run lint

# Run type checker
npm run type-check
```

## 🐛 Debugging

### Backend Debugging

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Use debugger
import pdb; pdb.set_trace()
```

### Frontend Debugging

```typescript
// Use console for debugging
console.log('Debug:', variable);

// Use React DevTools
// Install: https://react.dev/learn/react-developer-tools
```

## 📦 Release Process

1. Update version in `package.json` and `setup.py`
2. Update CHANGELOG.md
3. Create release branch: `release/v1.x.x`
4. Run full test suite
5. Create GitHub release with tag
6. Deploy to production

## 🙋 Questions?

- Open an issue for questions
- Join our discussions
- Email: [your.email@example.com]

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing! 🎉
