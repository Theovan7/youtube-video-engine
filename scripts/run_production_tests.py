#!/usr/bin/env python3
"""
Production Test Runner for YouTube Video Engine

This script provides an easy interface to run various test suites
against the production YouTube Video Engine deployment.
"""

import os
import sys
import argparse
import subprocess
import json
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestRunner:
    """Test runner for YouTube Video Engine production tests."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.test_dir = self.project_root / "tests"
        self.reports_dir = self.project_root / "reports"
        
        # Ensure reports directory exists
        self.reports_dir.mkdir(exist_ok=True)
    
    def run_health_check(self):
        """Run basic health check test."""
        print("🏥 Running health check test...")
        
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            str(self.test_dir / "test_e2e_production.py::ProductionE2ETestSuite::test_system_performance_benchmarks"),
            "-v", "-s"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Health check passed")
        else:
            print("❌ Health check failed")
            print(result.stdout)
            print(result.stderr)
        
        return result.returncode == 0
    
    def run_performance_tests(self):
        """Run performance benchmark tests."""
        print("🏃 Running performance tests...")
        
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            str(self.test_dir / "test_e2e_production.py::ProductionE2ETestSuite::test_system_performance_benchmarks"),
            str(self.test_dir / "test_e2e_production.py::ProductionE2ETestSuite::test_concurrent_request_handling"),
            str(self.test_dir / "test_e2e_production.py::ProductionE2ETestSuite::test_rate_limiting_behavior"),
            "-v", "-s"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Performance tests passed")
        else:
            print("❌ Performance tests failed")
            print(result.stdout)
            print(result.stderr)
        
        return result.returncode == 0
    
    def run_pipeline_tests(self, complexity: str = "simple"):
        """Run full pipeline tests."""
        print(f"🎬 Running {complexity} pipeline tests...")
        
        # Map complexity to test parameters
        test_params = {
            "simple": "test_complete_pipeline[video_config0]",
            "medium": "test_complete_pipeline[video_config1]", 
            "complex": "test_complete_pipeline[video_config2]"
        }
        
        if complexity == "all":
            test_filter = "test_complete_pipeline"
        else:
            test_filter = test_params.get(complexity, test_params["simple"])
        
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            f"{str(self.test_dir / 'test_e2e_production.py::ProductionE2ETestSuite::')}{ test_filter}",
            "-v", "-s"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Pipeline tests passed")
        else:
            print("❌ Pipeline tests failed")
            print(result.stdout)
            print(result.stderr)
        
        return result.returncode == 0
    
    def run_error_handling_tests(self):
        """Run error handling and edge case tests."""
        print("🚨 Running error handling tests...")
        
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            str(self.test_dir / "test_e2e_production.py::ProductionE2ETestSuite::test_error_handling_scenarios"),
            str(self.test_dir / "test_e2e_production.py::ProductionE2ETestSuite::test_webhook_endpoints_accessibility"),
            "-v", "-s"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Error handling tests passed")
        else:
            print("❌ Error handling tests failed")
            print(result.stdout)
            print(result.stderr)
        
        return result.returncode == 0
    
    def run_all_tests(self):
        """Run complete test suite."""
        print("🚀 Running complete test suite...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.reports_dir / f"complete_test_run_{timestamp}.html"
        
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            str(self.test_dir / "test_e2e_production.py"),
            "-v", "-s",
            f"--html={report_file}",
            "--self-contained-html"
        ], capture_output=True, text=True)
        
        print(f"📄 Test report saved to: {report_file}")
        
        if result.returncode == 0:
            print("✅ All tests passed")
        else:
            print("❌ Some tests failed")
            print(result.stdout)
            print(result.stderr)
        
        return result.returncode == 0
    
    def run_smoke_tests(self):
        """Run quick smoke tests for basic functionality."""
        print("💨 Running smoke tests...")
        
        tests = [
            "test_system_performance_benchmarks",
            "test_webhook_endpoints_accessibility",
            "test_error_handling_scenarios"
        ]
        
        all_passed = True
        for test in tests:
            result = subprocess.run([
                sys.executable, "-m", "pytest",
                f"{str(self.test_dir / 'test_e2e_production.py::ProductionE2ETestSuite::')}{ test}",
                "-v", "-q"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ {test}")
            else:
                print(f"❌ {test}")
                all_passed = False
        
        return all_passed
    
    def generate_load_test_report(self):
        """Generate load testing report with recommendations."""
        print("📊 Generating load test report...")
        
        # Run performance tests and capture results
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            str(self.test_dir / "test_e2e_production.py::ProductionE2ETestSuite::test_concurrent_request_handling"),
            "-v", "-s", "--tb=short"
        ], capture_output=True, text=True)
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "test_output": result.stdout,
            "test_errors": result.stderr,
            "success": result.returncode == 0,
            "recommendations": [
                "Monitor response times under concurrent load",
                "Consider implementing connection pooling if not already done",
                "Set up auto-scaling based on CPU/memory metrics",
                "Implement circuit breakers for external service calls",
                "Add request queuing for high-traffic scenarios"
            ]
        }
        
        report_file = self.reports_dir / f"load_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Load test report saved to: {report_file}")
        
        return report


def main():
    """Main entry point for test runner."""
    parser = argparse.ArgumentParser(description="YouTube Video Engine Production Test Runner")
    
    parser.add_argument(
        "test_type",
        choices=["health", "performance", "pipeline", "errors", "all", "smoke", "load-report"],
        help="Type of tests to run"
    )
    
    parser.add_argument(
        "--complexity",
        choices=["simple", "medium", "complex", "all"],
        default="simple",
        help="Complexity level for pipeline tests (default: simple)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    print("🎬 YouTube Video Engine - Production Test Runner")
    print("=" * 50)
    
    success = False
    
    if args.test_type == "health":
        success = runner.run_health_check()
    elif args.test_type == "performance":
        success = runner.run_performance_tests()
    elif args.test_type == "pipeline":
        success = runner.run_pipeline_tests(args.complexity)
    elif args.test_type == "errors":
        success = runner.run_error_handling_tests()
    elif args.test_type == "all":
        success = runner.run_all_tests()
    elif args.test_type == "smoke":
        success = runner.run_smoke_tests()
    elif args.test_type == "load-report":
        report = runner.generate_load_test_report()
        success = report["success"]
    
    print("=" * 50)
    
    if success:
        print("🎉 Test execution completed successfully!")
        sys.exit(0)
    else:
        print("❌ Test execution failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
