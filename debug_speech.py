#!/usr/bin/env python3
"""
Debug script to check Google Cloud Speech-to-Text setup
Run this script to diagnose common issues
"""

import os
import sys
from dotenv import load_dotenv

def check_google_cloud_speech():
    print("=== Google Cloud Speech-to-Text Debug Script ===\n")
    
    # Load environment variables
    load_dotenv()
    
    # Check 1: Import library
    try:
        from google.cloud import speech
        from google.oauth2 import service_account
        print("✅ Google Cloud Speech library imported successfully")
        print(f"   Library location: {speech.__file__}")
    except ImportError as e:
        print(f"❌ Failed to import Google Cloud Speech library: {e}")
        print("   Fix: pip install google-cloud-speech")
        return False
    
    # Check 2: Check for service account file
    service_account_file = "jsongooglecloudstt.json"
    if os.path.exists(service_account_file):
        print(f"✅ Service account file found: {service_account_file}")
        
        # Check file permissions
        if os.access(service_account_file, os.R_OK):
            print("✅ Service account file is readable")
        else:
            print("❌ Service account file is not readable")
            return False
            
        # Try to load the service account
        try:
            import json
            with open(service_account_file, 'r') as f:
                creds = json.load(f)
            
            required_fields = ['type', 'project_id', 'private_key', 'client_email']
            missing = [field for field in required_fields if field not in creds]
            
            if missing:
                print(f"❌ Missing required fields in service account: {missing}")
                return False
            else:
                print("✅ Service account file has required fields")
                print(f"   Project ID: {creds.get('project_id')}")
                print(f"   Client Email: {creds.get('client_email')}")
                
        except Exception as e:
            print(f"❌ Error reading service account file: {e}")
            return False
    else:
        print(f"⚠️  Service account file not found: {service_account_file}")
        print("   Checking environment variables...")
        
        # Check environment variables
        env_vars = [
            'GOOGLE_TYPE', 'GOOGLE_PROJECT_ID', 'GOOGLE_PRIVATE_KEY',
            'GOOGLE_CLIENT_EMAIL', 'GOOGLE_CLIENT_ID'
        ]
        
        missing_env = []
        for var in env_vars:
            if not os.getenv(var):
                missing_env.append(var)
        
        if missing_env:
            print(f"❌ Missing environment variables: {missing_env}")
            return False
        else:
            print("✅ Required environment variables found")
    
    # Check 3: Try to initialize the client
    try:
        if os.path.exists(service_account_file):
            client = speech.SpeechClient.from_service_account_json(service_account_file)
        else:
            # Use environment variables
            service_account_info = {
                "type": os.getenv("GOOGLE_TYPE"),
                "project_id": os.getenv("GOOGLE_PROJECT_ID"),
                "private_key_id": os.getenv("GOOGLE_PRIVATE_KEY_ID"),
                "private_key": os.getenv("GOOGLE_PRIVATE_KEY", "").replace('\\n', '\n'),
                "client_email": os.getenv("GOOGLE_CLIENT_EMAIL"),
                "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": os.getenv("GOOGLE_CLIENT_X509_CERT_URL"),
                "universe_domain": "googleapis.com"
            }
            credentials = service_account.Credentials.from_service_account_info(service_account_info)
            client = speech.SpeechClient(credentials=credentials)
        
        print("✅ Speech client initialized successfully")
        
    except Exception as e:
        print(f"❌ Failed to initialize speech client: {e}")
        return False
    
    # Check 4: Test basic functionality
    try:
        # Test audio encoding constants
        encodings = [
            ('LINEAR16', speech.RecognitionConfig.AudioEncoding.LINEAR16),
            ('FLAC', speech.RecognitionConfig.AudioEncoding.FLAC),
            ('WEBM_OPUS', speech.RecognitionConfig.AudioEncoding.WEBM_OPUS),
            ('MP3', speech.RecognitionConfig.AudioEncoding.MP3),
            ('OGG_OPUS', speech.RecognitionConfig.AudioEncoding.OGG_OPUS),
        ]
        
        print("\n✅ Available audio encodings:")
        for name, encoding in encodings:
            print(f"   - {name}: {encoding}")
            
    except AttributeError as e:
        print(f"❌ Audio encoding constants not available: {e}")
        print("   This might indicate an outdated library version")
        return False
    
    # Check 5: Test configuration creation
    try:
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
            sample_rate_hertz=48000,
            language_code="en-US",
            enable_automatic_punctuation=True,
        )
        print("✅ Configuration object created successfully")
        
    except Exception as e:
        print(f"❌ Failed to create configuration: {e}")
        return False
    
    print("\n🎉 All checks passed! Your Google Cloud Speech setup should work.")
    return True

if __name__ == "__main__":
    success = check_google_cloud_speech()
    sys.exit(0 if success else 1)