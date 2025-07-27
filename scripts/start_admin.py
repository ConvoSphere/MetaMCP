#!/usr/bin/env python3
"""
Start Script for MetaMCP Admin Interface

This script starts the Streamlit-based admin interface.
"""

import os
import sys
import subprocess
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from metamcp.config import get_settings


def main():
    """Start the Streamlit admin interface."""
    settings = get_settings()
    
    # Check if admin is enabled
    if not settings.admin_enabled:
        print("❌ Admin interface is disabled in configuration")
        print("Set admin_enabled=true in your .env file or configuration")
        sys.exit(1)
    
    # Set environment variables
    os.environ["STREAMLIT_SERVER_PORT"] = str(settings.admin_port)
    os.environ["STREAMLIT_SERVER_ADDRESS"] = "0.0.0.0"
    os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
    os.environ["STREAMLIT_SERVER_ENABLE_CORS"] = "false"
    os.environ["STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION"] = "false"
    
    # Path to the Streamlit app
    app_path = project_root / "metamcp" / "admin" / "streamlit_app.py"
    
    if not app_path.exists():
        print(f"❌ Streamlit app not found at {app_path}")
        sys.exit(1)
    
    print(f"🚀 Starting MetaMCP Admin Interface...")
    print(f"📍 URL: http://localhost:{settings.admin_port}")
    print(f"🔧 Admin Port: {settings.admin_port}")
    print(f"🌍 Environment: {settings.environment}")
    print(f"📱 App: {app_path}")
    print()
    print("Press Ctrl+C to stop the admin interface")
    print()
    
    try:
        # Start Streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", str(app_path),
            "--server.port", str(settings.admin_port),
            "--server.address", "0.0.0.0",
            "--server.headless", "true",
            "--server.enableCORS", "false",
            "--server.enableXsrfProtection", "false",
            "--browser.gatherUsageStats", "false"
        ], check=True)
    except KeyboardInterrupt:
        print("\n👋 Admin interface stopped")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start admin interface: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()