"""
Application Configuration
Centralized configuration management
"""
import os
from pathlib import Path

class Config:
    """Base configuration"""
    
    # Base directory
    BASE_DIR = Path(__file__).parent
    
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # CORS
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*')
    
    # File Upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'pdf'}
    
    # Directories
    UPLOAD_FOLDER = BASE_DIR / 'uploads'
    TEMPLATE_FOLDER = BASE_DIR / 'templates'
    MODEL_FOLDER = BASE_DIR / 'models'
    FEEDBACK_FOLDER = BASE_DIR / 'feedback'
    PREVIEW_FOLDER = BASE_DIR / 'previews'
    DATA_FOLDER = BASE_DIR / 'data'
    
    # Database
    DATABASE_PATH = DATA_FOLDER / 'pdf_extraction.db'
    
    # PDF Processing
    PDF_DPI = 150  # DPI for PDF to image conversion
    
    # Pattern Learning
    DEFAULT_PATTERN_LIMIT = 5
    MAX_PATTERN_LIMIT = 20
    
    @classmethod
    def init_app(cls, app):
        """Initialize application with configuration"""
        # Create necessary directories
        for folder in [
            cls.UPLOAD_FOLDER,
            cls.TEMPLATE_FOLDER,
            cls.MODEL_FOLDER,
            cls.FEEDBACK_FOLDER,
            cls.PREVIEW_FOLDER,
            cls.DATA_FOLDER
        ]:
            folder.mkdir(parents=True, exist_ok=True)
        
        # Set Flask config
        app.config['UPLOAD_FOLDER'] = str(cls.UPLOAD_FOLDER)
        app.config['TEMPLATE_FOLDER'] = str(cls.TEMPLATE_FOLDER)
        app.config['MODEL_FOLDER'] = str(cls.MODEL_FOLDER)
        app.config['FEEDBACK_FOLDER'] = str(cls.FEEDBACK_FOLDER)
        app.config['PREVIEW_FOLDER'] = str(cls.PREVIEW_FOLDER)
        app.config['MAX_CONTENT_LENGTH'] = cls.MAX_CONTENT_LENGTH
        app.config['SECRET_KEY'] = cls.SECRET_KEY

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    
    @classmethod
    def init_app(cls, app):
        """Initialize production config"""
        super().init_app(app)
        
        # Validate required production settings
        if not os.environ.get('SECRET_KEY'):
            raise ValueError("SECRET_KEY must be set in production")
        
        app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DATABASE_PATH = Config.BASE_DIR / 'data' / 'test.db'

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(env=None):
    """Get configuration based on environment"""
    if env is None:
        env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])
