#!/usr/bin/env python3
"""
AstroSurge - Unified Application Entrypoint

This script launches both the FastAPI backend and Flask frontend services
in a single, simple entrypoint.
"""

import os
import sys
import subprocess
import signal
import time
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load .env file before checking environment variables
load_dotenv(dotenv_path=project_root / '.env')

def main():
    """Main entrypoint that runs both services"""
    print("=" * 60)
    print("🚀 AstroSurge - Asteroid Mining Operation Simulator")
    print("=" * 60)
    print()
    
    # Check environment variables (after loading .env)
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        env_file = project_root / '.env'
        if env_file.exists():
            print("⚠️  Warning: MONGODB_URI not found in environment or .env file")
            print(f"   Please ensure MONGODB_URI is set in {env_file}")
        else:
            print("⚠️  Warning: MONGODB_URI environment variable not set")
            print(f"   Create a .env file in {project_root} with MONGODB_URI")
        print("   Some features may not work correctly")
        print()
    else:
        print("✅ MongoDB connection configured")
        print()
    
    # Determine ports
    api_port = int(os.getenv("API_PORT", "8000"))
    web_port = int(os.getenv("WEB_PORT", "5000"))
    
    print(f"📡 Starting FastAPI backend on port {api_port}...")
    print(f"🌐 Starting Flask web UI on port {web_port}...")
    print()
    
    # Prepare environment for subprocesses (includes .env variables loaded above)
    env = os.environ.copy()
    env['FLASK_PORT'] = str(web_port)
    
    # Start FastAPI backend (inherits environment with .env variables)
    api_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", str(api_port)],
        cwd=project_root,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Give API a moment to start
    time.sleep(2)
    
    # Start Flask frontend (inherits environment with .env variables)
    web_process = subprocess.Popen(
        [sys.executable, "webapp.py"],
        cwd=project_root,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait a moment for services to start
    time.sleep(2)
    
    print("✅ Services started successfully!")
    print()
    print(f"📊 Web Dashboard: http://localhost:{web_port}")
    print(f"🔗 API Documentation: http://localhost:{api_port}/docs")
    print(f"🔗 API Health Check: http://localhost:{api_port}/health")
    print()
    print("Press Ctrl+C to stop all services...")
    print("=" * 60)
    print()
    
    # Handle graceful shutdown
    def signal_handler(sig, frame):
        print("\n\n🛑 Shutting down services...")
        api_process.terminate()
        web_process.terminate()
        
        # Wait for processes to terminate
        try:
            api_process.wait(timeout=5)
            web_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            print("⚠️  Forcing shutdown...")
            api_process.kill()
            web_process.kill()
        
        print("✅ All services stopped")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Monitor processes
    try:
        while True:
            # Check if processes are still running
            if api_process.poll() is not None:
                print("❌ FastAPI backend process ended unexpectedly")
                break
            if web_process.poll() is not None:
                print("❌ Flask web UI process ended unexpectedly")
                break
            
            time.sleep(1)
    
    except KeyboardInterrupt:
        signal_handler(None, None)
    
    # Cleanup
    if api_process.poll() is None:
        api_process.terminate()
    if web_process.poll() is None:
        web_process.terminate()

if __name__ == "__main__":
    main()

