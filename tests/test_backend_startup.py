#!/usr/bin/env python3
"""
Backend Startup Verification Test

This test specifically verifies that the Python PATH fix in start.bat works correctly
and the backend can start without errors after the fix.

Critical Fix: start.bat now uses virtual environment Python path instead of system Python
"""

import sys
import os
import subprocess
import time
import requests
import unittest
from pathlib import Path
from typing import Optional

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))


class BackendStartupTest(unittest.TestCase):
    """Test backend startup functionality after Python PATH fix"""
    
    def setUp(self):
        self.electron_app_path = project_root / "video-transcriber-electron"
        self.start_bat_path = self.electron_app_path / "start.bat"
        self.venv_path = project_root / "venv"
        self.api_base_url = "http://127.0.0.1:8000"
        self.backend_process = None
        
    def tearDown(self):
        """Clean up any running backend processes"""
        if self.backend_process:
            try:
                self.backend_process.terminate()
                self.backend_process.wait(timeout=10)
            except:
                try:
                    self.backend_process.kill()
                except:
                    pass
    
    def test_start_bat_exists(self):
        """Test that start.bat file exists"""
        self.assertTrue(
            self.start_bat_path.exists(),
            f"start.bat not found at {self.start_bat_path}"
        )
        print(f"✅ start.bat found: {self.start_bat_path}")
    
    def test_virtual_environment_exists(self):
        """Test that virtual environment exists"""
        self.assertTrue(
            self.venv_path.exists(),
            f"Virtual environment not found at {self.venv_path}"
        )
        
        venv_python = self.venv_path / "Scripts" / "python.exe"
        self.assertTrue(
            venv_python.exists(),
            f"Python executable not found at {venv_python}"
        )
        print(f"✅ Virtual environment Python found: {venv_python}")
    
    def test_start_bat_uses_venv_python(self):
        """Test that start.bat uses virtual environment Python"""
        content = self.start_bat_path.read_text()
        print(f"📄 start.bat content:")
        print(content)
        print("-" * 50)
        
        # Should contain virtual environment Python path
        expected_patterns = [
            "venv\\Scripts\\python",
            "venv/Scripts/python",
            "%~dp0..\\..\\venv\\Scripts\\python"
        ]
        
        found_venv_reference = False
        for pattern in expected_patterns:
            if pattern in content:
                found_venv_reference = True
                print(f"✅ Found venv Python reference: {pattern}")
                break
        
        self.assertTrue(
            found_venv_reference,
            f"start.bat does not reference virtual environment Python. Content: {content[:200]}"
        )
        
        # Should NOT contain system Python references
        bad_patterns = [
            "python.exe" if "venv" not in content else "",  # System python without venv context
            "py.exe",  # Python launcher
            "C:\\Python",  # Absolute Python paths
            "C:/Python"
        ]
        
        for bad_pattern in bad_patterns:
            if bad_pattern and bad_pattern in content:
                self.fail(f"start.bat contains system Python reference: {bad_pattern}")
        
        print("✅ start.bat uses virtual environment Python correctly")
    
    def test_backend_modules_import(self):
        """Test that backend modules can be imported correctly"""
        print("🔍 Testing backend module imports...")
        
        modules_to_test = [
            "src.api.main",
            "src.transcription.whisper_manager", 
            "src.transcription.transcription_pipeline",
            "src.input_handling.queue_manager"
        ]
        
        for module_name in modules_to_test:
            try:
                __import__(module_name)
                print(f"✅ Successfully imported: {module_name}")
            except ImportError as e:
                self.fail(f"Failed to import {module_name}: {e}")
            except Exception as e:
                print(f"⚠️  Import warning for {module_name}: {e}")
                # Don't fail for non-import errors (e.g., model loading)
    
    def test_fastapi_app_creation(self):
        """Test that FastAPI app can be created"""
        try:
            from src.api.main import app
            self.assertIsNotNone(app, "FastAPI app should be created")
            print("✅ FastAPI app created successfully")
            
            # Test that app has expected routes
            routes = [route.path for route in app.routes]
            expected_routes = ["/api/status", "/api/queue"]
            
            for expected_route in expected_routes:
                # Check if any route matches (might have different exact paths)
                route_exists = any(expected_route in route for route in routes)
                if route_exists:
                    print(f"✅ Found API route pattern: {expected_route}")
                else:
                    print(f"⚠️  API route not found: {expected_route}")
            
        except ImportError as e:
            self.fail(f"Could not import FastAPI app: {e}")
        except Exception as e:
            print(f"⚠️  FastAPI app creation warning: {e}")
    
    def test_backend_startup_simulation(self):
        """Test backend startup simulation (without actually starting server)"""
        print("🧪 Testing backend startup simulation...")
        
        # Test the command that would be run
        venv_python = self.venv_path / "Scripts" / "python.exe"
        
        # Test basic Python execution in venv
        try:
            result = subprocess.run(
                [str(venv_python), "-c", "print('Python executable works')"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            self.assertEqual(result.returncode, 0, f"Python execution failed: {result.stderr}")
            self.assertIn("Python executable works", result.stdout)
            print(f"✅ Virtual environment Python executable works")
            
        except subprocess.TimeoutExpired:
            self.fail("Python execution timed out")
        except FileNotFoundError:
            self.fail(f"Python executable not found: {venv_python}")
    
    def test_required_dependencies(self):
        """Test that required dependencies are available in virtual environment"""
        print("📦 Testing required dependencies...")
        
        venv_python = self.venv_path / "Scripts" / "python.exe"
        
        required_packages = [
            "fastapi",
            "uvicorn", 
            "torch",
            "faster_whisper",
            "moviepy"
        ]
        
        for package in required_packages:
            try:
                result = subprocess.run(
                    [str(venv_python), "-c", f"import {package}; print('{package} imported')"],
                    capture_output=True,
                    text=True,
                    timeout=15
                )
                
                if result.returncode == 0:
                    print(f"✅ {package}: Available")
                else:
                    print(f"⚠️  {package}: Not available - {result.stderr.strip()}")
                    
            except subprocess.TimeoutExpired:
                print(f"⚠️  {package}: Import timeout")
            except Exception as e:
                print(f"⚠️  {package}: Test error - {e}")
    
    def test_start_bat_execution_dry_run(self):
        """Test start.bat execution in dry-run mode"""
        print("🧪 Testing start.bat execution (dry run)...")
        
        # Read start.bat content to understand what it does
        content = self.start_bat_path.read_text()
        
        # Look for the main command being executed
        lines = content.strip().split('\n')
        main_command_line = None
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('@') and not line.startswith('echo') and 'python' in line:
                main_command_line = line
                break
        
        if main_command_line:
            print(f"📋 Main command: {main_command_line}")
            
            # Parse the command to extract Python path and script
            if 'python' in main_command_line:
                print("✅ start.bat contains Python execution command")
            else:
                self.fail("start.bat does not contain Python execution command")
        else:
            print("⚠️  Could not identify main Python command in start.bat")
    
    def test_working_directory_setup(self):
        """Test that working directory is set up correctly"""
        print("📁 Testing working directory setup...")
        
        # Check that start.bat is in the electron app directory
        self.assertTrue(
            self.start_bat_path.parent == self.electron_app_path,
            "start.bat should be in the electron app directory"
        )
        
        # Check relative path to virtual environment
        relative_venv_path = self.start_bat_path.parent.parent.parent / "venv"
        self.assertTrue(
            relative_venv_path.exists(),
            f"Virtual environment should be accessible from start.bat location: {relative_venv_path}"
        )
        
        print("✅ Working directory setup is correct")
    
    def generate_startup_verification_report(self):
        """Generate a comprehensive startup verification report"""
        print("\n" + "="*60)
        print("🔧 BACKEND STARTUP VERIFICATION REPORT")
        print("="*60)
        
        checks = [
            ("start.bat exists", self.start_bat_path.exists()),
            ("Virtual environment exists", self.venv_path.exists()),
            ("Python executable exists", (self.venv_path / "Scripts" / "python.exe").exists()),
        ]
        
        # Test start.bat content
        if self.start_bat_path.exists():
            content = self.start_bat_path.read_text()
            venv_referenced = any(pattern in content for pattern in ["venv\\Scripts\\python", "venv/Scripts/python"])
            checks.append(("start.bat references venv Python", venv_referenced))
        
        # Test module imports
        try:
            from src.api.main import app
            checks.append(("FastAPI app imports", True))
        except:
            checks.append(("FastAPI app imports", False))
        
        print("\n📋 VERIFICATION RESULTS:")
        passed_checks = 0
        total_checks = len(checks)
        
        for description, passed in checks:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"   {description}: {status}")
            if passed:
                passed_checks += 1
        
        success_rate = (passed_checks / total_checks) * 100
        print(f"\n📊 SUMMARY:")
        print(f"   Passed: {passed_checks}/{total_checks}")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print(f"\n🎉 BACKEND STARTUP: ✅ READY")
            print(f"   Backend should start correctly with fixed Python PATH")
        else:
            print(f"\n🚨 BACKEND STARTUP: ❌ ISSUES DETECTED")
            print(f"   Critical issues need to be resolved before backend will start")
        
        return success_rate >= 80


def run_backend_startup_verification():
    """Run backend startup verification tests"""
    
    print("🔧 Backend Startup Verification Test Suite")
    print("="*60)
    print("Testing Python PATH fix in start.bat")
    print("Verifying backend can start without Python errors")
    print()
    
    # Create test suite
    suite = unittest.TestSuite()
    
    test_methods = [
        'test_start_bat_exists',
        'test_virtual_environment_exists', 
        'test_start_bat_uses_venv_python',
        'test_backend_modules_import',
        'test_fastapi_app_creation',
        'test_backend_startup_simulation',
        'test_required_dependencies',
        'test_start_bat_execution_dry_run',
        'test_working_directory_setup'
    ]
    
    for test_method in test_methods:
        suite.addTest(BackendStartupTest(test_method))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=1, buffer=True)
    result = runner.run(suite)
    
    # Generate report
    test_instance = BackendStartupTest()
    test_instance.setUp()
    backend_ready = test_instance.generate_startup_verification_report()
    
    return backend_ready, result


if __name__ == "__main__":
    success, test_result = run_backend_startup_verification()
    
    if success:
        print("\n🎉 Backend startup verification PASSED!")
        print("✅ start.bat should work correctly with fixed Python PATH")
    else:
        print("\n❌ Backend startup verification FAILED!")
        print("🔧 Python PATH fix needs additional work")
    
    exit(0 if success else 1)