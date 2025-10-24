"""
WhatsApp Order Automation - Backend Setup Script
This script helps you set up the backend environment
"""

import os
import sys
import subprocess
import platform

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}...")
    try:
        if platform.system() == "Windows":
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        else:
            result = subprocess.run(command.split(), check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stdout:
            print(f"Output: {e.stdout}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} is not compatible")
        print("Please install Python 3.8 or higher")
        return False

def check_chrome():
    """Check if Chrome browser is available"""
    print("🌐 Checking Chrome browser...")
    chrome_paths = [
        "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    ]
    
    for path in chrome_paths:
        if os.path.exists(path):
            print("✅ Chrome browser found")
            return True
    
    print("⚠️ Chrome browser not found")
    print("Please install Google Chrome browser for WhatsApp Web integration")
    print("Download from: https://www.google.com/chrome/")
    return False

def setup_environment():
    """Set up the Python environment"""
    print("\n🔧 Setting up environment...")
    
    # Check if we're in a virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Virtual environment detected")
    else:
        print("⚠️ Not in a virtual environment")
        print("Recommended: Create a virtual environment first")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            return False
    
    # Install requirements
    if not run_command("pip install -r requirements.txt", "Installing Python dependencies"):
        return False
    
    return True

def setup_database():
    """Set up the database"""
    print("\n🗄️ Setting up database...")
    
    try:
        # Create database tables
        from app.database import engine, test_connection
        from app.models import Base
        
        if test_connection():
            print("✅ Database connection successful")
            Base.metadata.create_all(bind=engine)
            print("✅ Database tables created")
            return True
        else:
            print("❌ Database connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def setup_directories():
    """Create required directories"""
    print("\n📁 Creating directories...")
    
    directories = [
        "static",
        "logs", 
        "exports",
        "whatsapp_sessions"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    return True

def setup_env_file():
    """Set up environment file"""
    print("\n⚙️ Setting up environment file...")
    
    if os.path.exists('.env'):
        print("✅ .env file already exists")
        return True
    
    if os.path.exists('.env.example'):
        try:
            # Copy .env.example to .env
            with open('.env.example', 'r') as src:
                content = src.read()
            
            with open('.env', 'w') as dst:
                dst.write(content)
            
            print("✅ Created .env file from .env.example")
            print("⚠️ Please edit .env file with your configuration")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create .env file: {e}")
            return False
    else:
        print("❌ .env.example file not found")
        return False

def main():
    """Main setup function"""
    print("🚀 WhatsApp Order Automation - Backend Setup")
    print("=" * 50)
    
    # Step 1: Check Python version
    if not check_python_version():
        return False
    
    # Step 2: Check Chrome browser
    check_chrome()  # Warning only, not required for API
    
    # Step 3: Set up directories
    if not setup_directories():
        return False
    
    # Step 4: Set up environment file
    if not setup_env_file():
        return False
    
    # Step 5: Set up Python environment
    if not setup_environment():
        return False
    
    # Step 6: Set up database
    if not setup_database():
        print("⚠️ Database setup failed, but you can continue with SQLite")
    
    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Edit .env file with your configuration")
    print("2. Start the server: python main.py")
    print("3. Test WhatsApp integration: python test_whatsapp.py")
    print("4. Test API endpoints: python test_api.py")
    print("5. Visit http://localhost:8000/docs for API documentation")
    
    print("\nFor WhatsApp integration:")
    print("1. Create a test WhatsApp group")
    print("2. Run the WhatsApp test script")
    print("3. Scan QR code when prompted")
    print("4. Send test order messages to the group")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            print("\n❌ Setup failed. Please check the errors above.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
