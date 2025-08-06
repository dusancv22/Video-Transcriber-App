#!/usr/bin/env python3
"""
Comprehensive Test Runner for Critical Fixes Verification

This script runs all verification tests to ensure both critical fixes are working:
1. Browse Button Fix (Electron dialog API)
2. Python PATH Fix (start.bat virtual environment)

It provides a complete assessment of application readiness after fixes.
"""

import sys
import os
import time
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple
import unittest

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# Import test modules
from test_backend_startup import run_backend_startup_verification
from test_browse_button_fix import run_browse_button_verification
from test_workflow_verification import run_workflow_verification_tests


class ComprehensiveTestRunner:
    """Runs all verification tests and generates comprehensive report"""
    
    def __init__(self):
        self.results = {
            'backend_startup': {'passed': False, 'details': None},
            'browse_button': {'passed': False, 'details': None},
            'workflow_verification': {'passed': False, 'details': None}
        }
        self.start_time = time.time()
        
    def run_all_tests(self) -> Dict:
        """Run all test suites and collect results"""
        
        print("🚀 COMPREHENSIVE VERIFICATION TEST RUNNER")
        print("="*80)
        print("🎯 Verifying both critical fixes work correctly:")
        print("   1. ✅ Browse Button Fix (Electron dialog API)")
        print("   2. ✅ Python PATH Fix (start.bat virtual environment)")
        print("   3. 🔄 Complete Workflow Integration")
        print()
        
        # Run Backend Startup Verification
        print("🔧 RUNNING: Backend Startup Verification")
        print("-" * 60)
        
        try:
            backend_passed, backend_result = run_backend_startup_verification()
            self.results['backend_startup'] = {
                'passed': backend_passed,
                'details': {
                    'tests_run': backend_result.testsRun,
                    'failures': len(backend_result.failures),
                    'errors': len(backend_result.errors)
                }
            }
            
            print(f"✅ Backend Startup Tests: {'PASSED' if backend_passed else 'FAILED'}")
            
        except Exception as e:
            print(f"❌ Backend Startup Tests: FAILED with exception: {e}")
            self.results['backend_startup']['details'] = {'error': str(e)}
        
        print()
        
        # Run Browse Button Verification  
        print("🗂️  RUNNING: Browse Button Fix Verification")
        print("-" * 60)
        
        try:
            browse_passed, browse_result = run_browse_button_verification()
            self.results['browse_button'] = {
                'passed': browse_passed,
                'details': {
                    'tests_run': browse_result.testsRun,
                    'failures': len(browse_result.failures),
                    'errors': len(browse_result.errors)
                }
            }
            
            print(f"✅ Browse Button Tests: {'PASSED' if browse_passed else 'FAILED'}")
            
        except Exception as e:
            print(f"❌ Browse Button Tests: FAILED with exception: {e}")
            self.results['browse_button']['details'] = {'error': str(e)}
        
        print()
        
        # Run Workflow Verification
        print("🎬 RUNNING: Complete Workflow Verification")
        print("-" * 60)
        
        try:
            workflow_passed, workflow_result = run_workflow_verification_tests()
            self.results['workflow_verification'] = {
                'passed': workflow_passed,
                'details': {
                    'tests_run': getattr(workflow_result, 'testsRun', 0),
                    'failures': len(getattr(workflow_result, 'failures', [])),
                    'errors': len(getattr(workflow_result, 'errors', []))
                }
            }
            
            print(f"✅ Workflow Verification Tests: {'PASSED' if workflow_passed else 'FAILED'}")
            
        except Exception as e:
            print(f"❌ Workflow Verification Tests: FAILED with exception: {e}")
            self.results['workflow_verification']['details'] = {'error': str(e)}
        
        return self.results
    
    def generate_comprehensive_report(self) -> bool:
        """Generate final comprehensive report"""
        
        total_time = time.time() - self.start_time
        
        print("\n" + "="*80)
        print("📊 COMPREHENSIVE VERIFICATION REPORT")
        print("="*80)
        
        print(f"⏱️  Total Test Time: {total_time:.2f} seconds")
        print(f"📅 Test Date: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Individual test results
        print("\n🔍 INDIVIDUAL TEST RESULTS:")
        print("-" * 60)
        
        test_descriptions = {
            'backend_startup': {
                'name': 'Backend Startup Verification',
                'description': 'Tests start.bat Python PATH fix',
                'critical': True
            },
            'browse_button': {
                'name': 'Browse Button Fix Verification', 
                'description': 'Tests Electron dialog API exposure',
                'critical': True
            },
            'workflow_verification': {
                'name': 'Complete Workflow Verification',
                'description': 'Tests end-to-end application functionality',
                'critical': False
            }
        }
        
        passed_tests = 0
        critical_passed = 0
        total_critical = 0
        
        for test_key, result in self.results.items():
            test_info = test_descriptions[test_key]
            status = "✅ PASSED" if result['passed'] else "❌ FAILED"
            critical_mark = " [CRITICAL]" if test_info['critical'] else ""
            
            print(f"{test_info['name']}: {status}{critical_mark}")
            print(f"   Description: {test_info['description']}")
            
            if result['details'] and not isinstance(result['details'], dict) or 'error' not in result['details']:
                details = result['details']
                if hasattr(details, 'get'):
                    print(f"   Tests Run: {details.get('tests_run', 'N/A')}")
                    print(f"   Failures: {details.get('failures', 'N/A')}")
                    print(f"   Errors: {details.get('errors', 'N/A')}")
            elif result['details'] and 'error' in result['details']:
                print(f"   Error: {result['details']['error']}")
            
            if result['passed']:
                passed_tests += 1
                if test_info['critical']:
                    critical_passed += 1
                    
            if test_info['critical']:
                total_critical += 1
            
            print()
        
        # Summary statistics
        total_tests = len(self.results)
        success_rate = (passed_tests / total_tests) * 100
        critical_success_rate = (critical_passed / total_critical) * 100 if total_critical > 0 else 0
        
        print("📈 SUMMARY STATISTICS:")
        print(f"   Total Test Suites: {total_tests}")
        print(f"   Passed: {passed_tests}")
        print(f"   Failed: {total_tests - passed_tests}")
        print(f"   Overall Success Rate: {success_rate:.1f}%")
        print(f"   Critical Tests Passed: {critical_passed}/{total_critical}")
        print(f"   Critical Success Rate: {critical_success_rate:.1f}%")
        
        # Critical fixes assessment
        print("\n🎯 CRITICAL FIXES ASSESSMENT:")
        print("-" * 60)
        
        backend_working = self.results['backend_startup']['passed']
        browse_working = self.results['browse_button']['passed']
        
        print(f"Python PATH Fix (start.bat): {'✅ WORKING' if backend_working else '❌ BROKEN'}")
        if backend_working:
            print("   ✅ Virtual environment Python path is correctly configured")
            print("   ✅ Backend should start without Python errors")
        else:
            print("   ❌ start.bat still has Python PATH issues")
            print("   📌 ACTION: Fix virtual environment path in start.bat")
        
        print(f"Browse Button Fix (Electron): {'✅ WORKING' if browse_working else '❌ BROKEN'}")
        if browse_working:
            print("   ✅ Electron dialog API is properly exposed")
            print("   ✅ Browse button should open directory picker")
        else:
            print("   ❌ Electron dialog API is not accessible")
            print("   📌 ACTION: Configure dialog API in main.js")
        
        # Overall workflow status
        print("\n🚀 OVERALL WORKFLOW STATUS:")
        print("-" * 60)
        
        both_critical_working = backend_working and browse_working
        workflow_working = self.results['workflow_verification']['passed']
        
        if both_critical_working:
            print("🎉 CRITICAL FIXES: ✅ BOTH WORKING")
            print("   ✅ Python PATH fix is working")
            print("   ✅ Browse button fix is working")
            
            if workflow_working:
                print("\n🎊 APPLICATION STATUS: ✅ FULLY READY")
                print("   🎯 Complete end-to-end workflow is functional")
                print("   👥 Application is ready for user testing")
                overall_status = "fully_ready"
                
            else:
                print("\n🟡 APPLICATION STATUS: ⚠️ MOSTLY READY")
                print("   🎯 Core fixes work, but some workflow issues remain")
                print("   👥 Application should work for basic use cases")
                overall_status = "mostly_ready"
                
        else:
            print("🚨 CRITICAL FIXES: ❌ ISSUES REMAIN")
            
            if not backend_working and not browse_working:
                print("   ❌ Both Python PATH and Browse button fixes need work")
            elif not backend_working:
                print("   ❌ Python PATH fix needs work")
            elif not browse_working:
                print("   ❌ Browse button fix needs work")
            
            print("\n💥 APPLICATION STATUS: ❌ NOT READY")
            print("   🛑 Critical issues prevent normal operation")
            print("   🔧 Must fix critical issues before user testing")
            overall_status = "not_ready"
        
        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        print("-" * 60)
        
        if overall_status == "fully_ready":
            print("   🎉 Excellent! Both fixes are working correctly")
            print("   📋 Run manual user acceptance testing")
            print("   🚀 Application is ready for deployment")
            
        elif overall_status == "mostly_ready":
            print("   ✅ Core functionality should work")
            print("   🧪 Test with actual video files")
            print("   🔍 Address remaining workflow issues")
            
        else:
            print("   🔧 Fix critical issues first:")
            if not backend_working:
                print("      - Update start.bat with correct Python path")
                print("      - Test: python -c 'import sys; print(sys.executable)'")
            if not browse_working:
                print("      - Configure Electron dialog API in main.js")
                print("      - Test: Add ipcMain.handle for directory dialog")
            print("   🔄 Re-run tests after fixes")
        
        # Testing instructions
        print(f"\n🧪 NEXT STEPS:")
        print("-" * 60)
        
        if overall_status in ["fully_ready", "mostly_ready"]:
            print("   1. 📋 Run manual workflow test:")
            print("      python tests/manual_workflow_test.md")
            print("   2. 🎬 Test with real video files")
            print("   3. 👥 Conduct user acceptance testing")
            
        else:
            print("   1. 🔧 Fix critical issues identified above")
            print("   2. 🔄 Re-run comprehensive tests:")
            print("      python tests/run_comprehensive_tests.py")
            print("   3. ✅ Ensure all critical tests pass")
        
        # Save comprehensive report
        report_data = {
            'timestamp': time.time(),
            'test_duration': total_time,
            'results': self.results,
            'summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'success_rate': success_rate,
                'critical_passed': critical_passed,
                'critical_total': total_critical,
                'critical_success_rate': critical_success_rate
            },
            'fixes_status': {
                'python_path_fix': backend_working,
                'browse_button_fix': browse_working,
                'both_critical_working': both_critical_working
            },
            'overall_status': overall_status,
            'ready_for_users': overall_status in ["fully_ready", "mostly_ready"]
        }
        
        report_file = Path(__file__).parent / "comprehensive_test_report.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n💾 Comprehensive report saved to: {report_file}")
        
        return both_critical_working
    
    def run_quick_verification(self) -> bool:
        """Run quick verification of critical fixes only"""
        
        print("⚡ QUICK VERIFICATION: Critical Fixes Only")
        print("="*50)
        
        # Quick Python PATH check
        venv_path = project_root / "venv" / "Scripts" / "python.exe"
        start_bat_path = project_root / "video-transcriber-electron" / "start.bat"
        
        python_path_ok = venv_path.exists() and start_bat_path.exists()
        if python_path_ok and start_bat_path.exists():
            content = start_bat_path.read_text()
            python_path_ok = "venv" in content and "python" in content
        
        # Quick Browse button check
        main_js_paths = [
            project_root / "video-transcriber-electron" / "src" / "main.js",
            project_root / "video-transcriber-electron" / "main.js"
        ]
        
        browse_button_ok = False
        for main_js_path in main_js_paths:
            if main_js_path.exists():
                content = main_js_path.read_text()
                if "dialog" in content.lower() and "ipcmain" in content.lower():
                    browse_button_ok = True
                    break
        
        print(f"Python PATH Fix: {'✅ OK' if python_path_ok else '❌ NEEDS WORK'}")
        print(f"Browse Button Fix: {'✅ OK' if browse_button_ok else '❌ NEEDS WORK'}")
        
        both_ok = python_path_ok and browse_button_ok
        print(f"\nQuick Assessment: {'✅ READY FOR TESTING' if both_ok else '❌ NEEDS MORE WORK'}")
        
        return both_ok


def main():
    """Main entry point for comprehensive test runner"""
    
    import argparse
    parser = argparse.ArgumentParser(description="Run comprehensive verification tests")
    parser.add_argument('--quick', action='store_true', help='Run quick verification only')
    parser.add_argument('--verbose', action='store_true', help='Show verbose output')
    args = parser.parse_args()
    
    runner = ComprehensiveTestRunner()
    
    if args.quick:
        success = runner.run_quick_verification()
    else:
        runner.run_all_tests()
        success = runner.generate_comprehensive_report()
    
    print(f"\n🏁 FINAL RESULT:")
    if success:
        print("🎉 VERIFICATION PASSED - Critical fixes are working!")
        exit_code = 0
    else:
        print("❌ VERIFICATION FAILED - Critical issues need attention")
        exit_code = 1
    
    exit(exit_code)


if __name__ == "__main__":
    main()