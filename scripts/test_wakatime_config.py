#!/usr/bin/env python3
"""
Test script to verify WakaTime OAuth configuration
Run this script to check if your WakaTime settings are correct
"""

import os
from app.config import settings

def test_wakatime_config():
    print("=== WakaTime Configuration Test ===")
    print()
    
    # Check required environment variables
    required_vars = [
        'WAKATIME_CLIENT_ID',
        'WAKATIME_CLIENT_SECRET', 
        'REDIRECT_URI',
        'FRONTEND_DOMAIN'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = getattr(settings, var, None)
        if not value:
            missing_vars.append(var)
        else:
            if var == 'WAKATIME_CLIENT_SECRET':
                print(f"✓ {var}: {'*' * len(value)}")  # Hide secret
            else:
                print(f"✓ {var}: {value}")
    
    if missing_vars:
        print()
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        return False
    
    print()
    print("=== Configuration Validation ===")
    
    # Validate redirect URI format
    redirect_uri = settings.REDIRECT_URI
    if not redirect_uri.startswith(('http://', 'https://')):
        print(f"❌ REDIRECT_URI should start with http:// or https://")
        print(f"   Current: {redirect_uri}")
        return False
    else:
        print(f"✓ REDIRECT_URI format is valid")
    
    # Check if redirect URI matches frontend domain
    frontend_domain = settings.FRONTEND_DOMAIN
    if not redirect_uri.startswith(frontend_domain):
        print(f"⚠️  WARNING: REDIRECT_URI doesn't start with FRONTEND_DOMAIN")
        print(f"   FRONTEND_DOMAIN: {frontend_domain}")
        print(f"   REDIRECT_URI: {redirect_uri}")
        print(f"   This might cause issues if they don't match your WakaTime app configuration")
    
    print()
    print("=== WakaTime App Settings Checklist ===")
    print("Please verify these settings in your WakaTime app dashboard:")
    print(f"1. Client ID matches: {settings.WAKATIME_CLIENT_ID}")
    print(f"2. Redirect URI matches: {settings.REDIRECT_URI}")
    print("3. App is not in sandbox mode (if applicable)")
    print("4. Required scopes are enabled: email, read_logged_time, read_stats")
    
    print()
    print("=== Debugging Tips ===")
    print("1. Make sure your frontend only makes ONE request to /api/wakatime/callback")
    print("2. Authorization codes expire quickly (5-10 minutes)")
    print("3. Authorization codes can only be used once")
    print("4. The redirect_uri must EXACTLY match what's registered with WakaTime")
    
    return True

if __name__ == "__main__":
    try:
        success = test_wakatime_config()
        if success:
            print()
            print("✅ Configuration test completed successfully!")
        else:
            print()
            print("❌ Configuration test failed. Please fix the issues above.")
    except Exception as e:
        print(f"❌ Error running configuration test: {e}") 