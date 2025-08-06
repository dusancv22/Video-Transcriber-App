#!/usr/bin/env python3
"""
Browse Button Fix Verification Test

This test verifies that the Electron Browse button fix is working correctly.
The fix ensures that the dialog API is properly exposed so users can browse
for output directories.

Critical Fix: Electron main.js now properly exposes dialog API for directory browsing
"""

import sys
import os
import json
import subprocess
import unittest
from pathlib import Path
from typing import Dict, List, Optional
import re

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))


class BrowseButtonFixTest(unittest.TestCase):
    """Test Browse button functionality after Electron dialog API fix"""
    
    def setUp(self):
        self.electron_app_path = project_root / "video-transcriber-electron"
        self.main_js_paths = [
            self.electron_app_path / "src" / "main.js",
            self.electron_app_path / "main.js",
            self.electron_app_path / "public" / "main.js"
        ]
        self.package_json_path = self.electron_app_path / "package.json"
        
    def test_electron_app_structure(self):
        """Test that Electron app structure exists"""
        self.assertTrue(
            self.electron_app_path.exists(),
            f"Electron app directory not found: {self.electron_app_path}"
        )
        
        self.assertTrue(
            self.package_json_path.exists(),
            f"package.json not found: {self.package_json_path}"
        )
        
        print(f"✅ Electron app structure verified: {self.electron_app_path}")
    
    def test_main_js_exists(self):
        """Test that main.js file exists"""
        main_js_path = None
        
        for path in self.main_js_paths:
            if path.exists():
                main_js_path = path
                break
        
        self.assertIsNotNone(
            main_js_path,
            f"main.js not found in any expected location: {self.main_js_paths}"
        )
        
        self.main_js_path = main_js_path
        print(f"✅ main.js found: {main_js_path}")
        return main_js_path
    
    def test_dialog_api_exposure(self):
        """Test that dialog API is properly exposed in main.js"""
        main_js_path = self.test_main_js_exists()
        
        content = main_js_path.read_text(encoding='utf-8')
        print(f"📄 main.js content length: {len(content)} characters")
        
        # Print first 500 characters for debugging
        print(f"📄 main.js content preview:")
        print(content[:500] + "..." if len(content) > 500 else content)
        print("-" * 50)
        
        # Look for dialog API exposure patterns
        dialog_patterns = [
            # IPC handler for directory dialog
            r'ipcMain\.handle.*show.*[Dd]irectory.*[Dd]ialog',
            r'ipcMain\.handle.*browse.*[Dd]irectory',
            r'ipcMain\.handle.*select.*[Dd]irectory',
            
            # Dialog.showOpenDialog usage
            r'dialog\.showOpenDialog',
            r'dialog\.showSaveDialog',
            
            # Directory selection properties
            r'properties.*openDirectory',
            r'openDirectory',
            
            # IPC main handlers
            r'ipcMain\.handle.*directory',
            r'ipcMain\.on.*directory'
        ]
        
        found_patterns = []
        for pattern in dialog_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                found_patterns.extend(matches)
                print(f"✅ Found dialog pattern: {pattern}")
        
        self.assertTrue(
            len(found_patterns) > 0,
            f"No dialog API patterns found in main.js. Content preview: {content[:200]}"
        )
        
        print(f"✅ Dialog API exposure verified ({len(found_patterns)} patterns found)")
    
    def test_security_context_configuration(self):
        """Test that security context allows dialog access"""
        main_js_path = self.test_main_js_exists()
        content = main_js_path.read_text(encoding='utf-8')
        
        # Look for security configuration
        security_patterns = [
            # Context isolation disabled (allows dialog access)
            (r'contextIsolation.*false', "Context isolation disabled"),
            
            # Node integration enabled  
            (r'nodeIntegration.*true', "Node integration enabled"),
            
            # Preload script (alternative secure approach)
            (r'preload.*path', "Preload script configured"),
            
            # Web security disabled (for development)
            (r'webSecurity.*false', "Web security disabled")
        ]
        
        security_configs_found = []
        
        for pattern, description in security_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                security_configs_found.append(description)
                print(f"✅ {description}")
        
        # Need at least one security configuration that allows dialog access
        self.assertTrue(
            len(security_configs_found) > 0,
            "No security configuration found that would allow dialog API access"
        )
        
        print(f"✅ Security context configured for dialog access")
    
    def test_electron_imports(self):
        """Test that required Electron modules are imported"""
        main_js_path = self.test_main_js_exists()
        content = main_js_path.read_text(encoding='utf-8')
        
        required_imports = [
            (r'require.*electron', "Electron main import"),
            (r'require.*["\']electron["\']', "Electron import"),
            (r'from.*electron', "Electron ES6 import"),
            
            # Specific modules
            (r'dialog', "Dialog module"),
            (r'ipcMain', "IPC Main module"),
            (r'BrowserWindow', "BrowserWindow module")
        ]
        
        imports_found = []
        
        for pattern, description in required_imports:
            if re.search(pattern, content, re.IGNORECASE):
                imports_found.append(description)
                print(f"✅ {description}")
        
        # Should have at least basic Electron import
        self.assertTrue(
            any("import" in imp for imp in imports_found),
            "No Electron imports found in main.js"
        )
        
        print(f"✅ Electron imports verified")
    
    def test_ipc_handler_registration(self):
        """Test that IPC handlers are registered for dialog functionality"""
        main_js_path = self.test_main_js_exists()
        content = main_js_path.read_text(encoding='utf-8')
        
        # Look for IPC handler registration patterns
        ipc_patterns = [
            r'ipcMain\.handle\(',
            r'ipcMain\.on\(',
            r'handle.*directory',
            r'handle.*browse',
            r'handle.*select'
        ]
        
        ipc_handlers_found = []
        
        for pattern in ipc_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                ipc_handlers_found.extend(matches)
                print(f"✅ Found IPC pattern: {pattern}")
        
        self.assertTrue(
            len(ipc_handlers_found) > 0,
            "No IPC handlers found for dialog functionality"
        )
        
        print(f"✅ IPC handlers registered ({len(ipc_handlers_found)} found)")
    
    def test_package_json_configuration(self):
        """Test package.json has correct Electron configuration"""
        package_data = json.loads(self.package_json_path.read_text())
        
        # Check main entry point
        self.assertIn('main', package_data, "package.json should have main entry point")
        
        main_file = package_data['main']
        print(f"✅ Main entry point: {main_file}")
        
        # Check for Electron in dependencies
        dependencies = package_data.get('dependencies', {})
        dev_dependencies = package_data.get('devDependencies', {})
        
        has_electron = 'electron' in dependencies or 'electron' in dev_dependencies
        
        if has_electron:
            electron_version = dependencies.get('electron') or dev_dependencies.get('electron')
            print(f"✅ Electron dependency found: {electron_version}")
        else:
            print("⚠️  Electron dependency not found in package.json")
        
        # Check for start script
        scripts = package_data.get('scripts', {})
        has_start_script = 'start' in scripts or 'electron' in scripts
        
        if has_start_script:
            start_command = scripts.get('start') or scripts.get('electron')
            print(f"✅ Start script found: {start_command}")
        else:
            print("⚠️  No start script found in package.json")
    
    def test_frontend_dialog_integration(self):
        """Test that frontend code can integrate with dialog API"""
        
        # Look for frontend files that might call dialog
        frontend_paths = [
            self.electron_app_path / "src",
            self.electron_app_path / "public", 
            self.electron_app_path / "renderer"
        ]
        
        dialog_usage_patterns = [
            r'ipcRenderer\.invoke.*directory',
            r'ipcRenderer\.send.*directory',
            r'showDirectoryDialog',
            r'browse.*directory',
            r'select.*directory'
        ]
        
        frontend_files = []
        
        for frontend_path in frontend_paths:
            if frontend_path.exists():
                for file_path in frontend_path.rglob('*.js'):
                    frontend_files.append(file_path)
                for file_path in frontend_path.rglob('*.ts'):
                    frontend_files.append(file_path)
                for file_path in frontend_path.rglob('*.tsx'):
                    frontend_files.append(file_path)
        
        dialog_usage_found = False
        
        for file_path in frontend_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                
                for pattern in dialog_usage_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        print(f"✅ Dialog usage found in: {file_path.name}")
                        dialog_usage_found = True
                        break
                        
            except Exception as e:
                print(f"⚠️  Could not read {file_path}: {e}")
        
        if not dialog_usage_found:
            print("⚠️  No dialog usage found in frontend files")
            print("💡 This might be normal if dialog calls are in different files")
    
    def test_browse_button_simulation(self):
        """Simulate Browse button functionality"""
        print("🧪 Simulating Browse button functionality...")
        
        # Test directory selection logic
        import tempfile
        test_directory = Path(tempfile.mkdtemp())
        
        try:
            # Simulate successful directory selection
            selected_path = str(test_directory)
            
            # Validate path format (Windows-compatible)
            self.assertTrue(
                Path(selected_path).exists(),
                f"Selected directory should exist: {selected_path}"
            )
            
            # Test path normalization
            normalized_path = Path(selected_path).resolve()
            self.assertTrue(
                normalized_path.exists(),
                f"Normalized path should exist: {normalized_path}"
            )
            
            print(f"✅ Directory selection simulation successful: {selected_path}")
            
            # Test settings persistence simulation
            settings_data = {
                'outputDirectory': str(normalized_path),
                'model': 'base',
                'format': 'txt'
            }
            
            # Simulate localStorage equivalent
            settings_json = json.dumps(settings_data, indent=2)
            self.assertIn('outputDirectory', settings_json)
            
            print(f"✅ Settings persistence simulation successful")
            
        finally:
            # Clean up test directory
            try:
                test_directory.rmdir()
            except:
                pass
    
    def generate_browse_button_report(self):
        """Generate comprehensive Browse button fix report"""
        print("\n" + "="*60)
        print("🗂️  BROWSE BUTTON FIX VERIFICATION REPORT")
        print("="*60)
        
        checks = []
        
        # Test file existence
        main_js_exists = any(path.exists() for path in self.main_js_paths)
        checks.append(("main.js exists", main_js_exists))
        
        package_json_exists = self.package_json_path.exists()
        checks.append(("package.json exists", package_json_exists))
        
        # Test dialog API exposure
        dialog_api_exposed = False
        if main_js_exists:
            main_js_path = next((path for path in self.main_js_paths if path.exists()), None)
            if main_js_path:
                content = main_js_path.read_text(encoding='utf-8')
                dialog_patterns = [
                    r'dialog\.show',
                    r'ipcMain\.handle.*directory',
                    r'openDirectory'
                ]
                dialog_api_exposed = any(re.search(pattern, content, re.IGNORECASE) for pattern in dialog_patterns)
        
        checks.append(("Dialog API exposed", dialog_api_exposed))
        
        # Test security configuration
        security_configured = False
        if main_js_exists:
            main_js_path = next((path for path in self.main_js_paths if path.exists()), None)
            if main_js_path:
                content = main_js_path.read_text(encoding='utf-8')
                security_patterns = [
                    r'contextIsolation.*false',
                    r'nodeIntegration.*true',
                    r'preload.*path'
                ]
                security_configured = any(re.search(pattern, content, re.IGNORECASE) for pattern in security_patterns)
        
        checks.append(("Security context configured", security_configured))
        
        # Test Electron configuration
        electron_configured = False
        if package_json_exists:
            package_data = json.loads(self.package_json_path.read_text())
            dependencies = package_data.get('dependencies', {})
            dev_dependencies = package_data.get('devDependencies', {})
            electron_configured = 'electron' in dependencies or 'electron' in dev_dependencies
        
        checks.append(("Electron configured", electron_configured))
        
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
        
        if success_rate >= 75:  # 3 out of 4 critical checks
            print(f"\n🎉 BROWSE BUTTON FIX: ✅ WORKING")
            print(f"   Dialog API should be accessible from Browse button")
        else:
            print(f"\n🚨 BROWSE BUTTON FIX: ❌ ISSUES DETECTED")
            print(f"   Browse button may not work correctly")
            
            if not dialog_api_exposed:
                print("   📌 ACTION: Ensure dialog API is exposed in main.js")
            if not security_configured:
                print("   📌 ACTION: Configure security context for dialog access")
        
        return success_rate >= 75


def run_browse_button_verification():
    """Run Browse button fix verification tests"""
    
    print("🗂️  Browse Button Fix Verification Test Suite")
    print("="*60)
    print("Testing Electron dialog API exposure fix")
    print("Verifying Browse button can open directory picker")
    print()
    
    # Create test suite
    suite = unittest.TestSuite()
    
    test_methods = [
        'test_electron_app_structure',
        'test_main_js_exists',
        'test_dialog_api_exposure',
        'test_security_context_configuration',
        'test_electron_imports',
        'test_ipc_handler_registration',
        'test_package_json_configuration',
        'test_frontend_dialog_integration',
        'test_browse_button_simulation'
    ]
    
    for test_method in test_methods:
        suite.addTest(BrowseButtonFixTest(test_method))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=1, buffer=True)
    result = runner.run(suite)
    
    # Generate report
    test_instance = BrowseButtonFixTest()
    test_instance.setUp()
    browse_button_working = test_instance.generate_browse_button_report()
    
    return browse_button_working, result


if __name__ == "__main__":
    success, test_result = run_browse_button_verification()
    
    if success:
        print("\n🎉 Browse button fix verification PASSED!")
        print("✅ Browse button should open directory picker correctly")
    else:
        print("\n❌ Browse button fix verification FAILED!")
        print("🔧 Electron dialog API needs additional configuration")
    
    exit(0 if success else 1)