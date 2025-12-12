"""
Flask Backend for Adaptive PDF Data Extraction System
Main application entry point

Follows best practices:
- Centralized configuration
- Standardized error handling
- Consistent API responses
- Separation of concerns
"""
from flask import Flask
from flask_cors import CORS
from flasgger import Swagger
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import configuration
from config import get_config

# Import API v1 routes
from api.v1.auth import auth_bp
from api.v1.templates import templates_bp
from api.v1.extraction import extraction_bp as extraction_v1_bp
from api.v1.learning import learning_bp
from api.v1.preview import preview_bp as preview_v1_bp
from api.v1.data_quality import data_quality_bp
from api.v1.strategy_performance import strategy_performance_bp
from api.v1.pattern_info import pattern_info_bp
from api.v1.pattern_cleanup import pattern_cleanup_bp
from api.v1.pattern_statistics import pattern_statistics_bp
from api.v1.dashboard import dashboard_bp
from api.v1.jobs import jobs_bp

# Import utilities
from utils.response import APIResponse
from shared.exceptions import ApplicationError

def create_app(config_name=None):
    """Application factory pattern"""
    # Initialize Flask app
    app = Flask(__name__)
    
    # Load configuration
    config_class = get_config(config_name)
    config_class.init_app(app)
    
    # Initialize CORS
    CORS(app, origins=config_class.CORS_ORIGINS)
    
    # Initialize Swagger/OpenAPI documentation
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": 'apispec',
                "route": '/apispec.json',
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/api/docs"
    }
    
    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "Adaptive PDF Data Extraction API",
            "description": "REST API for adaptive PDF data extraction system with Human-in-the-Loop learning",
            "version": "1.0.0",
            "contact": {
                "name": "API Support",
                "email": "support@example.com"
            }
        },
        "host": "localhost:8000",
        "basePath": "/",
        "schemes": ["http", "https"],
        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "JWT Authorization header using the Bearer scheme. Example: 'Authorization: Bearer {token}'"
            }
        },
        "tags": [
            {"name": "Auth", "description": "Authentication endpoints"},
            {"name": "Templates", "description": "Template management"},
            {"name": "Extraction", "description": "Document extraction"},
            {"name": "Learning", "description": "Model training and learning"},
            {"name": "Patterns", "description": "Pattern management"},
            {"name": "Preview", "description": "Document preview"},
            {"name": "Data Quality", "description": "Data quality metrics"},
            {"name": "Strategy Performance", "description": "Extraction strategy performance tracking"}
        ]
    }
    
    Swagger(app, config=swagger_config, template=swagger_template)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    return app

def register_blueprints(app):
    """Register all route blueprints"""
    # API v1 routes (with auth protection)
    app.register_blueprint(auth_bp)
    app.register_blueprint(templates_bp)
    app.register_blueprint(extraction_v1_bp)
    app.register_blueprint(learning_bp)
    app.register_blueprint(preview_v1_bp)
    app.register_blueprint(data_quality_bp)
    app.register_blueprint(strategy_performance_bp)
    app.register_blueprint(pattern_info_bp)
    app.register_blueprint(pattern_cleanup_bp)
    app.register_blueprint(pattern_statistics_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(jobs_bp)

def register_error_handlers(app):
    """Register global error handlers"""
    
    @app.errorhandler(ApplicationError)
    def handle_application_error(error):
        """Handle custom application errors"""
        return APIResponse.error(error.message, status_code=error.status_code)
    
    @app.errorhandler(413)
    def request_entity_too_large(error):
        """Handle file too large error"""
        return APIResponse.bad_request("File size exceeds maximum limit (16MB)")
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors"""
        return APIResponse.not_found("Endpoint not found")
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        """Handle method not allowed"""
        return APIResponse.error("Method not allowed", status_code=405)
    
    @app.errorhandler(500)
    def internal_server_error(error):
        """Handle internal server errors"""
        return APIResponse.internal_error("An internal server error occurred")

# Create app instance
app = create_app()

# Health check endpoints
@app.route('/health', methods=['GET'])
def health_check_simple():
    """Simple health check endpoint for Docker"""
    from flask import jsonify
    return jsonify({'status': 'healthy'}), 200

@app.route('/api/health', methods=['GET'])
def health_check():
    """Detailed health check endpoint"""
    return APIResponse.success(
        data={
            'status': 'healthy',
            'version': '1.0.0',
            'environment': os.environ.get('FLASK_ENV', 'development')
        },
        message='Service is running'
    )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
