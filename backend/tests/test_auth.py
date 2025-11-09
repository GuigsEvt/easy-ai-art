#!/usr/bin/env python3
"""
Simple test script to verify authentication setup
"""
import os
import sys
sys.path.append('/Users/guigs/Documents/GitHub/easy-ai-art/backend')

try:
    from app.core.auth import AUTH_ENABLED, AUTH_USERNAME, AUTH_PASSWORD, authenticate_user, create_session, validate_session
    print("✅ Authentication module imported successfully")
    print(f"🔐 Auth Enabled: {AUTH_ENABLED}")
    print(f"👤 Username: {AUTH_USERNAME}")
    print(f"🔑 Password: {'*' * len(AUTH_PASSWORD)}")
    
    # Test authentication
    test_result = authenticate_user(AUTH_USERNAME, AUTH_PASSWORD)
    print(f"🧪 Authentication test: {'✅ PASS' if test_result else '❌ FAIL'}")
    
    # Test session creation
    if test_result:
        session_token = create_session(AUTH_USERNAME)
        print(f"🎫 Session token created: {session_token[:10]}...")
        
        # Test session validation
        is_valid = validate_session(session_token)
        print(f"🔍 Session validation: {'✅ VALID' if is_valid else '❌ INVALID'}")
    
    print("\n✅ All authentication components are working correctly!")
    
except Exception as e:
    print(f"❌ Error testing authentication: {e}")
    import traceback
    traceback.print_exc()