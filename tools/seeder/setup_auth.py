"""
Setup Authentication for Seeder

Creates default admin user for automated seeding

Usage:
    python setup_auth.py
"""

import requests
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

API_BASE_URL = 'http://localhost:8000/api/v1'

def create_admin_user():
    """Create default admin user"""
    
    url = f"{API_BASE_URL}/auth/register"
    
    data = {
        'username': 'madulinux',
        'email': 'madulinux@gmail.com',
        'password': 'justice#404',
        'full_name': 'Admin User'
    }
    
    try:
        logger.info("🔐 Creating admin user...")
        response = requests.post(url, json=data)
        
        if response.status_code == 201:
            logger.info("✅ Admin user created successfully!")
            logger.info(f"   Username: {data['username']}")
            logger.info(f"   Password: {data['password']}")
            return True
        elif response.status_code == 400:
            result = response.json()
            if 'already exists' in result.get('message', '').lower():
                logger.info("ℹ️  Admin user already exists")
                return True
            else:
                logger.error(f"❌ Failed to create user: {result.get('message')}")
                return False
        else:
            logger.error(f"❌ Failed to create user: {response.status_code}")
            logger.error(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        logger.error("❌ Cannot connect to API server")
        logger.error("   Make sure backend is running: python backend/app.py")
        return False
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        return False


def test_login():
    """Test login with admin credentials"""
    
    url = f"{API_BASE_URL}/auth/login"
    
    data = {
        'username': 'madulinux',
        'password': 'justice#404'
    }
    
    try:
        logger.info("\n🔐 Testing login...")
        response = requests.post(url, json=data)
        
        if response.status_code == 200:
            result = response.json()
            tokens = result.get('data', {}).get('tokens', {})
            
            logger.info("✅ Login successful!")
            logger.info(f"   Access token: {tokens.get('access_token')[:50]}...")
            logger.info(f"   Refresh token: {tokens.get('refresh_token')[:50]}...")
            return True
        else:
            logger.error(f"❌ Login failed: {response.status_code}")
            logger.error(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        return False


def main():
    """Main entry point"""
    logger.info("=" * 70)
    logger.info("🚀 AUTHENTICATION SETUP FOR SEEDER")
    logger.info("=" * 70)
    
    # Create admin user
    if not create_admin_user():
        logger.error("\n❌ Setup failed!")
        return
    
    # Test login
    if not test_login():
        logger.error("\n❌ Setup failed!")
        return
    
    logger.info("\n" + "=" * 70)
    logger.info("✅ SETUP COMPLETED SUCCESSFULLY!")
    logger.info("=" * 70)
    logger.info("\nYou can now run the seeder:")
    logger.info("  python automated_seeder.py --template certificate_template --count 5")
    logger.info("\nOr with custom credentials:")
    logger.info("  python automated_seeder.py --template certificate_template --count 5 \\")
    logger.info("    --username madulinux --password justice#404")
    logger.info("=" * 70)


if __name__ == '__main__':
    main()
