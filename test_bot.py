#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script for Our Goal Bot
Tests basic functionality without requiring actual bot token
"""

import sys
import os
import json
from datetime import datetime

def test_imports():
    """Test that all modules can be imported successfully."""
    print("🔍 Testing imports...")
    
    try:
        import config
        print("✅ config module imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import config: {e}")
        return False
    
    try:
        import data_manager
        print("✅ data_manager module imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import data_manager: {e}")
        return False
    
    try:
        # Import handlers without running them
        import handlers
        print("✅ handlers module imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import handlers: {e}")
        return False
    
    return True

def test_config():
    """Test configuration values."""
    print("\n🔧 Testing configuration...")
    
    try:
        import config
        
        # Test team definitions
        if not config.TEAMS:
            print("❌ TEAMS dictionary is empty")
            return False
        
        print(f"✅ Found {len(config.TEAMS)} teams configured")
        for team_id, team_name in config.TEAMS.items():
            print(f"   - {team_id}: {team_name}")
        
        # Test message templates
        required_messages = [
            'WELCOME_MESSAGE', 'TEAM_SELECTION_MESSAGE', 'EXPERIENCE_QUESTION',
            'APPLICATION_SUBMITTED', 'ALREADY_APPLIED', 'CANCEL_MESSAGE'
        ]
        
        for msg in required_messages:
            if not hasattr(config, msg):
                print(f"❌ Missing message template: {msg}")
                return False
        
        print("✅ All required message templates found")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_data_manager():
    """Test data manager functionality."""
    print("\n💾 Testing data manager...")
    
    try:
        from data_manager import DataManager
        
        # Create test instance
        dm = DataManager()
        print("✅ DataManager instance created successfully")
        
        # Test basic methods
        stats = dm.get_statistics()
        print(f"✅ Statistics retrieved: {stats}")
        
        # Test user application check
        has_applied = dm.has_user_applied(12345, "team_exams")
        print(f"✅ User application check works: {has_applied}")
        
        # Test user status
        user_status = dm.get_user_status(12345)
        print(f"✅ User status retrieved: {user_status['total_applications']} applications")
        
        return True
        
    except Exception as e:
        print(f"❌ Data manager test failed: {e}")
        return False

def test_file_structure():
    """Test that all required files are present."""
    print("\n📁 Testing file structure...")
    
    required_files = [
        'main.py', 'config.py', 'handlers.py', 'data_manager.py',
        'requirements.txt', '.env.example', 'README.md', '.gitignore',
        'Procfile', 'railway.json', 'runtime.txt'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
        else:
            print(f"✅ {file}")
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    
    print("✅ All required files present")
    return True

def test_json_structure():
    """Test JSON file creation and structure."""
    print("\n📄 Testing JSON file handling...")
    
    try:
        from data_manager import DataManager
        
        # Create test application data
        test_app = {
            'user_info': {
                'user_id': 12345,
                'first_name': 'Test',
                'last_name': 'User',
                'username': 'testuser',
                'timestamp': datetime.now().isoformat()
            },
            'selected_team': 'team_exams',
            'team_name': 'تيم الاختبارات',
            'reason': 'Test reason for joining',
            'experience': 'Test experience description',
            'timestamp': datetime.now().isoformat()
        }
        
        dm = DataManager()
        
        # Test saving application (this will create JSON files)
        success = dm.save_application(test_app)
        if success:
            print("✅ Test application saved successfully")
        else:
            print("❌ Failed to save test application")
            return False
        
        # Test retrieving data
        stats = dm.get_statistics()
        if stats['total_applications'] > 0:
            print(f"✅ Application data retrieved: {stats['total_applications']} applications")
        else:
            print("❌ No applications found after saving")
            return False
        
        # Clean up test data
        dm.clear_applications()
        print("✅ Test data cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ JSON structure test failed: {e}")
        return False

def test_environment_validation():
    """Test environment variable validation."""
    print("\n🌍 Testing environment validation...")
    
    try:
        # Test without environment variables
        os.environ.pop('BOT_TOKEN', None)
        os.environ.pop('ADMIN_GROUP_ID', None)
        
        # Import main module functions
        sys.path.insert(0, '.')
        from main import validate_environment
        
        # Should fail without environment variables
        if validate_environment():
            print("❌ Environment validation should fail without variables")
            return False
        else:
            print("✅ Environment validation correctly fails without variables")
        
        # Test with valid environment variables
        os.environ['BOT_TOKEN'] = 'test_token'
        os.environ['ADMIN_GROUP_ID'] = '12345'
        
        if validate_environment():
            print("✅ Environment validation passes with valid variables")
        else:
            print("❌ Environment validation should pass with valid variables")
            return False
        
        # Test with invalid admin group ID
        os.environ['ADMIN_GROUP_ID'] = 'invalid_id'
        
        if validate_environment():
            print("❌ Environment validation should fail with invalid admin group ID")
            return False
        else:
            print("✅ Environment validation correctly fails with invalid admin group ID")
        
        return True
        
    except Exception as e:
        print(f"❌ Environment validation test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Starting Our Goal Bot Tests\n")
    
    tests = [
        ("Import Tests", test_imports),
        ("Configuration Tests", test_config),
        ("Data Manager Tests", test_data_manager),
        ("File Structure Tests", test_file_structure),
        ("JSON Handling Tests", test_json_structure),
        ("Environment Validation Tests", test_environment_validation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print('='*50)
        
        try:
            if test_func():
                print(f"\n✅ {test_name} PASSED")
                passed += 1
            else:
                print(f"\n❌ {test_name} FAILED")
        except Exception as e:
            print(f"\n💥 {test_name} CRASHED: {e}")
    
    print(f"\n{'='*50}")
    print(f"TEST RESULTS: {passed}/{total} tests passed")
    print('='*50)
    
    if passed == total:
        print("🎉 All tests passed! Bot is ready for deployment.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

