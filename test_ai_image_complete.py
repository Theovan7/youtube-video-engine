#!/usr/bin/env python3
"""
Complete test script for AI image generation with 10-minute timeout support.

This script provides comprehensive testing for the generate AI image endpoint
including timeout monitoring, error analysis, and detailed reporting.

Usage:
    python test_ai_image_complete.py [segment_id] [optional_base_url]

Example:
    python test_ai_image_complete.py recxGRBRi1Qe9sLDn
    python test_ai_image_complete.py recxGRBRi1Qe9sLDn http://localhost:5000
    python test_ai_image_complete.py recxGRBRi1Qe9sLDn https://your-production-url.com

Features:
- 10-minute timeout support
- Real-time progress monitoring
- Detailed error analysis
- Performance metrics
- Multiple test scenarios
- Image URL validation
"""

import sys
import json
import requests
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Optional, List


class ProgressMonitor:
    """Real-time progress monitor for long-running requests."""
    
    def __init__(self):
        self.start_time = None
        self.stop_monitoring = False
        self.monitoring_thread = None
    
    def start(self):
        """Start monitoring progress."""
        self.start_time = time.time()
        self.stop_monitoring = False
        self.monitoring_thread = threading.Thread(target=self._monitor_progress)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
    
    def stop(self):
        """Stop monitoring progress."""
        self.stop_monitoring = True
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=1)
    
    def _monitor_progress(self):
        """Monitor and display progress."""
        while not self.stop_monitoring:
            elapsed = time.time() - self.start_time
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            
            if elapsed < 60:
                progress_msg = f"⏱️  {seconds}s elapsed"
            elif elapsed < 300:  # Less than 5 minutes
                progress_msg = f"⏱️  {minutes}m {seconds}s elapsed (Normal range)"
            elif elapsed < 600:  # Less than 10 minutes
                progress_msg = f"⏱️  {minutes}m {seconds}s elapsed (Extended processing)"
            else:  # Over 10 minutes
                progress_msg = f"⏱️  {minutes}m {seconds}s elapsed (⚠️  Very long)"
            
            print(f"\r{progress_msg}", end="", flush=True)
            time.sleep(1)


def validate_image_urls(urls: List[str]) -> Dict:
    """Validate that image URLs are accessible."""
    results = {
        'valid_urls': [],
        'invalid_urls': [],
        'total_count': len(urls),
        'success_rate': 0
    }
    
    print(f"\n🔍 Validating {len(urls)} image URLs...")
    
    for i, url in enumerate(urls, 1):
        try:
            # Quick HEAD request to check if URL exists
            response = requests.head(url, timeout=10)
            if response.status_code == 200:
                results['valid_urls'].append(url)
                print(f"  ✅ Image {i}: Valid (HTTP {response.status_code})")
            else:
                results['invalid_urls'].append(url)
                print(f"  ❌ Image {i}: Invalid (HTTP {response.status_code})")
        except Exception as e:
            results['invalid_urls'].append(url)
            print(f"  ❌ Image {i}: Error - {e}")
    
    results['success_rate'] = (len(results['valid_urls']) / len(urls)) * 100 if urls else 0
    return results


def analyze_error_response(response) -> Dict:
    """Analyze error response and provide detailed feedback."""
    analysis = {
        'error_type': 'unknown',
        'is_timeout': False,
        'is_auth_error': False,
        'is_rate_limit': False,
        'is_server_error': False,
        'recommendations': []
    }
    
    status_code = response.status_code
    
    try:
        error_data = response.json()
        error_str = json.dumps(error_data).lower()
        
        # Analyze different error types
        if 'timeout' in error_str or status_code == 408:
            analysis['error_type'] = 'timeout'
            analysis['is_timeout'] = True
            analysis['recommendations'] = [
                "The OpenAI API is taking longer than 10 minutes",
                "Consider reducing from 4 images to 2 images",
                "Check OpenAI API status at https://status.openai.com",
                "Consider implementing async processing"
            ]
        
        elif status_code == 401:
            analysis['error_type'] = 'authentication'
            analysis['is_auth_error'] = True
            analysis['recommendations'] = [
                "Check OPENAI_API_KEY in .env file",
                "Verify API key is valid and active",
                "Ensure API key has image generation permissions"
            ]
        
        elif status_code == 429:
            analysis['error_type'] = 'rate_limit'
            analysis['is_rate_limit'] = True
            analysis['recommendations'] = [
                "OpenAI API rate limit exceeded",
                "Wait before retrying",
                "Consider upgrading OpenAI plan",
                "Implement request queuing"
            ]
        
        elif status_code >= 500:
            analysis['error_type'] = 'server_error'
            analysis['is_server_error'] = True
            analysis['recommendations'] = [
                "OpenAI API server error",
                "This is likely temporary - retry later",
                "Check OpenAI status page",
                "Monitor for continued issues"
            ]
        
        elif 'includes is not a function' in error_str:
            analysis['error_type'] = 'javascript_error'
            analysis['recommendations'] = [
                "Airtable script error handling bug",
                "Update Airtable script error handling",
                "This is a client-side scripting issue"
            ]
    
    except:
        # If we can't parse JSON, analyze raw text
        error_text = response.text.lower()
        if 'timeout' in error_text:
            analysis['is_timeout'] = True
            analysis['error_type'] = 'timeout'
    
    return analysis


def test_ai_image_generation(segment_id: str, base_url: str = 'http://localhost:5000') -> Dict:
    """
    Comprehensive test of AI image generation endpoint.
    
    Args:
        segment_id: The segment ID to test with
        base_url: Base URL of the API
    
    Returns:
        Dict with test results
    """
    endpoint = f"{base_url}/api/v2/generate-ai-image"
    
    test_scenarios = [
        {
            'name': 'Default Settings (YouTube Optimized)',
            'payload': {
                'segment_id': segment_id,
                'size': '1792x1008'  # YouTube optimized
            },
            'expected_duration': '2-8 minutes',
            'description': 'Standard 4-image generation for YouTube content'
        },
        {
            'name': 'Square Format',
            'payload': {
                'segment_id': segment_id,
                'size': '1024x1024'
            },
            'expected_duration': '2-8 minutes',
            'description': 'Square format for social media'
        },
        {
            'name': 'Auto Size',
            'payload': {
                'segment_id': segment_id,
                'size': 'auto'
            },
            'expected_duration': '2-8 minutes',
            'description': 'Let OpenAI choose optimal size'
        }
    ]
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'segment_id': segment_id,
        'endpoint': endpoint,
        'test_results': [],
        'overall_success': False,
        'total_tests': len(test_scenarios),
        'passed_tests': 0
    }
    
    print(f"{'='*80}")
    print(f"🧪 COMPREHENSIVE AI IMAGE GENERATION TEST")
    print(f"{'='*80}")
    print(f"📍 Endpoint: {endpoint}")
    print(f"🎯 Segment ID: {segment_id}")
    print(f"🕐 Timestamp: {results['timestamp']}")
    print(f"⏰ Timeout: 10 minutes (600 seconds)")
    print(f"📊 Test Scenarios: {len(test_scenarios)}")
    print(f"{'='*80}")
    
    for i, test in enumerate(test_scenarios, 1):
        print(f"\n🔬 TEST {i}/{len(test_scenarios)}: {test['name']}")
        print(f"📝 Description: {test['description']}")
        print(f"⏱️  Expected Duration: {test['expected_duration']}")
        print(f"📤 Payload: {json.dumps(test['payload'], indent=2)}")
        print(f"{'-'*60}")
        
        # Initialize progress monitor
        monitor = ProgressMonitor()
        start_time = time.time()
        
        test_result = {
            'test_name': test['name'],
            'payload': test['payload'],
            'success': False,
            'duration': 0,
            'error': None,
            'response_data': None,
            'image_validation': None
        }
        
        try:
            print("🚀 Starting request...")
            monitor.start()
            
            # Make the request with 10+ minute timeout
            response = requests.post(
                endpoint,
                json=test['payload'],
                headers={'Content-Type': 'application/json'},
                timeout=660  # 11 minutes client timeout (longer than server 10min)
            )
            
            monitor.stop()
            end_time = time.time()
            duration = end_time - start_time
            test_result['duration'] = duration
            
            print(f"\n✅ Request completed!")
            print(f"⏱️  Total Duration: {duration:.2f} seconds ({duration/60:.1f} minutes)")
            print(f"📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                # Success case
                data = response.json()
                test_result['success'] = True
                test_result['response_data'] = data
                
                print("🎉 SUCCESS! Response:")
                print(json.dumps(data, indent=2))
                
                # Validate images if URLs provided
                if 'image_urls' in data and data['image_urls']:
                    validation = validate_image_urls(data['image_urls'])
                    test_result['image_validation'] = validation
                    
                    print(f"\n📊 Image Validation Results:")
                    print(f"  🖼️  Total Images: {validation['total_count']}")
                    print(f"  ✅ Valid URLs: {len(validation['valid_urls'])}")
                    print(f"  ❌ Invalid URLs: {len(validation['invalid_urls'])}")
                    print(f"  📈 Success Rate: {validation['success_rate']:.1f}%")
                
                # Performance analysis
                if duration < 120:  # Under 2 minutes
                    print(f"🚀 Performance: Excellent (under 2 minutes)")
                elif duration < 300:  # Under 5 minutes
                    print(f"✅ Performance: Good (under 5 minutes)")
                elif duration < 600:  # Under 10 minutes
                    print(f"⚠️  Performance: Acceptable (under 10 minutes)")
                else:  # Over 10 minutes
                    print(f"🐌 Performance: Slow (over 10 minutes)")
                
                results['passed_tests'] += 1
                
            else:
                # Error case
                monitor.stop()
                test_result['success'] = False
                
                print(f"❌ ERROR: HTTP {response.status_code}")
                
                # Analyze the error
                error_analysis = analyze_error_response(response)
                test_result['error'] = {
                    'status_code': response.status_code,
                    'analysis': error_analysis,
                    'raw_response': response.text[:1000] if response.text else None
                }
                
                print(f"🔍 Error Analysis:")
                print(f"  Type: {error_analysis['error_type']}")
                print(f"  Timeout: {error_analysis['is_timeout']}")
                print(f"  Auth Error: {error_analysis['is_auth_error']}")
                print(f"  Rate Limited: {error_analysis['is_rate_limit']}")
                
                if error_analysis['recommendations']:
                    print(f"💡 Recommendations:")
                    for rec in error_analysis['recommendations']:
                        print(f"  • {rec}")
                
                # Show raw error response
                try:
                    error_data = response.json()
                    print(f"\n📄 Error Response:")
                    print(json.dumps(error_data, indent=2))
                except:
                    print(f"\n📄 Raw Error Response:")
                    print(response.text[:500] + "..." if len(response.text) > 500 else response.text)
        
        except requests.exceptions.Timeout:
            monitor.stop()
            duration = time.time() - start_time
            test_result['duration'] = duration
            test_result['error'] = {'type': 'client_timeout', 'duration': duration}
            
            print(f"\n⏰ CLIENT TIMEOUT after {duration:.2f} seconds ({duration/60:.1f} minutes)")
            print("   The client gave up waiting, but the server might still be processing")
            print("   Check the segment record in Airtable to see if images were generated")
        
        except requests.exceptions.ConnectionError:
            monitor.stop()
            test_result['error'] = {'type': 'connection_error'}
            print(f"\n🔌 CONNECTION ERROR: Could not connect to {base_url}")
            print("   Is the server running? Check the URL and try again.")
        
        except Exception as e:
            monitor.stop()
            duration = time.time() - start_time
            test_result['duration'] = duration
            test_result['error'] = {'type': 'unexpected_error', 'message': str(e)}
            print(f"\n💥 UNEXPECTED ERROR: {type(e).__name__}: {e}")
        
        results['test_results'].append(test_result)
        
        # Ask user if they want to continue with more tests
        if i < len(test_scenarios):
            print(f"\n{'='*60}")
            user_input = input(f"Continue with test {i+1}/{len(test_scenarios)}? (y/n/skip): ").lower().strip()
            if user_input == 'n':
                break
            elif user_input == 'skip':
                print("Skipping remaining tests...")
                break
    
    # Final results summary
    results['overall_success'] = results['passed_tests'] > 0
    
    print(f"\n{'='*80}")
    print(f"📊 FINAL TEST RESULTS")
    print(f"{'='*80}")
    print(f"✅ Passed Tests: {results['passed_tests']}/{results['total_tests']}")
    print(f"❌ Failed Tests: {results['total_tests'] - results['passed_tests']}/{results['total_tests']}")
    print(f"📈 Success Rate: {(results['passed_tests']/results['total_tests'])*100:.1f}%")
    
    if results['overall_success']:
        print(f"🎉 Overall Result: SUCCESS - At least one test passed")
    else:
        print(f"💥 Overall Result: FAILURE - All tests failed")
    
    # Recommendations based on results
    print(f"\n💡 RECOMMENDATIONS:")
    if results['passed_tests'] == results['total_tests']:
        print("  🌟 All tests passed! The timeout fix is working perfectly.")
        print("  🔧 Don't forget to fix the Airtable script error handling.")
    elif results['passed_tests'] > 0:
        print("  ⚠️  Some tests passed, some failed. Check individual test results.")
        print("  🔍 Investigate failed scenarios for specific issues.")
    else:
        print("  🚨 All tests failed. Major issues detected:")
        print("  • Check server is running and accessible")
        print("  • Verify OpenAI API key and permissions") 
        print("  • Check segment exists with AI Image Prompt field")
        print("  • Consider further timeout increases or async processing")
    
    return results


def main():
    """Main function with argument parsing and execution."""
    if len(sys.argv) < 2:
        print("🧪 Complete AI Image Generation Test Script")
        print("=" * 50)
        print("\nUsage:")
        print("  python test_ai_image_complete.py [segment_id] [optional_base_url]")
        print("\nExamples:")
        print("  python test_ai_image_complete.py recxGRBRi1Qe9sLDn")
        print("  python test_ai_image_complete.py recxGRBRi1Qe9sLDn http://localhost:5000")
        print("  python test_ai_image_complete.py recxGRBRi1Qe9sLDn https://production-url.com")
        print("\nPrerequisites:")
        print("  ✅ Server running (python app.py)")
        print("  ✅ OPENAI_API_KEY set in .env file")
        print("  ✅ Segment exists in Airtable with 'AI Image Prompt' field")
        print("  ✅ OpenAI API account with image generation access")
        print("\nFeatures:")
        print("  • 10-minute timeout support")
        print("  • Real-time progress monitoring")
        print("  • Multiple test scenarios")
        print("  • Image URL validation")
        print("  • Detailed error analysis")
        print("  • Performance metrics")
        sys.exit(1)
    
    segment_id = sys.argv[1]
    base_url = sys.argv[2] if len(sys.argv) > 2 else 'http://localhost:5000'
    
    # Validate inputs
    if not segment_id.startswith('rec'):
        print(f"⚠️  Warning: Segment ID '{segment_id}' doesn't look like an Airtable record ID")
        print("   Airtable record IDs typically start with 'rec'")
        confirm = input("Continue anyway? (y/n): ").lower().strip()
        if confirm != 'y':
            print("Aborted.")
            sys.exit(1)
    
    print(f"🚀 Starting comprehensive AI image generation test...")
    print(f"🎯 Target: {segment_id}")
    print(f"🌐 Server: {base_url}")
    
    try:
        results = test_ai_image_generation(segment_id, base_url)
        
        # Save detailed results to file
        results_filename = f"ai_image_test_results_{segment_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Detailed results saved to: {results_filename}")
        print("🎯 Test completed!")
        
        # Exit with appropriate code
        sys.exit(0 if results['overall_success'] else 1)
    
    except KeyboardInterrupt:
        print(f"\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error during testing: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
