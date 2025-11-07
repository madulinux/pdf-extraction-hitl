"""
Debug configuration for better error messages
Install: pip install rich
"""
import sys
import os

def setup_debugging():
    """Setup enhanced debugging for development"""
    
    # Only in development
    if os.getenv('FLASK_ENV', 'development') == 'development':
        try:
            # Try to use rich for beautiful tracebacks
            from rich.traceback import install
            install(
                show_locals=True,
                max_frames=20,
                width=100,
                word_wrap=True,
                extra_lines=3,
                theme="monokai"
            )
            print("✅ Rich traceback installed")
            return True
        except ImportError:
            print("⚠️  Install 'rich' for better error messages:")
            print("   pip install rich")
            
            # Fallback to better_exceptions
            try:
                import better_exceptions
                better_exceptions.hook()
                print("✅ Better exceptions installed")
                return True
            except ImportError:
                print("⚠️  Or install 'better-exceptions':")
                print("   pip install better-exceptions")
                return False

def setup_logging():
    """Setup enhanced logging"""
    import logging
    
    try:
        from rich.logging import RichHandler
        
        # Configure logging with rich
        logging.basicConfig(
            level=logging.INFO,
            format="%(message)s",
            datefmt="[%X]",
            handlers=[RichHandler(
                rich_tracebacks=True,
                tracebacks_show_locals=True
            )]
        )
        print("✅ Rich logging installed")
    except ImportError:
        # Fallback to standard logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    return logging.getLogger("app")

if __name__ == "__main__":
    # Test the setup
    setup_debugging()
    logger = setup_logging()
    
    logger.info("Debug config loaded successfully!")
    
    # Test error display
    try:
        x = 1 / 0
    except Exception as e:
        logger.exception("Test error:")
