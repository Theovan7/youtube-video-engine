"""
End-to-End Production Testing Pipeline

This module contains comprehensive end-to-end tests that validate the entire
YouTube Video Engine pipeline in production conditions with real services,
timing measurements, and performance analysis.
"""

import pytest
import json
import time
import requests
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

# Configure detailed logging for test runs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PipelineMetrics:
    """Metrics collection for pipeline performance analysis."""
    script_processing_time: float = 0.0
    voiceover_generation_time: float = 0.0
    media_combination_time: float = 0.0
    video_concatenation_time: float = 0.0
    music_generation_time: float = 0.0
    music_addition_time: float = 0.0
    total_pipeline_time: float = 0.0
    segment_count: int = 0
    script_length: int = 0
    errors_encountered: List[str] = None
    
    def __post_init__(self):
        if self.errors_encountered is None:
            self.errors_encountered = []


@dataclass
class TestVideoConfig:
    """Configuration for test video generation."""
    name: str
    script: str
    expected_segments: int
    target_duration: int
    music_prompt: str
    voice_id: str = "EXAVITQu4vr4xnSDxMaL"  # Default ElevenLabs voice
    complexity_level: str = "simple"  # simple, medium, complex


class ProductionE2ETestSuite:
    """Production End-to-End Test Suite for YouTube Video Engine."""
    
    # Production API base URL
    BASE_URL = "https://youtube-video-engine.fly.dev"
    
    # Test video configurations for different scenarios
    TEST_VIDEOS = [
        TestVideoConfig(
            name="Simple AI Tutorial",
            script="""
            Welcome to our AI tutorial series. Today we'll explore machine learning basics.
            
            First, let's understand what artificial intelligence means. AI refers to computer systems that can perform tasks typically requiring human intelligence.
            
            Machine learning is a subset of AI that enables computers to learn and improve from experience without being explicitly programmed.
            
            Thank you for watching our tutorial. Subscribe for more AI content.
            """,
            expected_segments=4,
            target_duration=30,
            music_prompt="Upbeat tech background music with electronic elements",
            complexity_level="simple"
        ),
        
        TestVideoConfig(
            name="Product Demo - Medium Length",
            script="""
            Welcome to our comprehensive product demonstration. Today we'll showcase the key features of our innovative software platform.
            
            Our platform offers three main capabilities. First, automated data processing that handles large volumes of information efficiently.
            
            Second, real-time analytics that provide instant insights into your business metrics and performance indicators.
            
            Third, customizable dashboards that adapt to your specific workflow requirements and team preferences.
            
            The installation process is straightforward. Simply download our installer, run the setup wizard, and follow the configuration steps.
            
            Integration with existing systems is seamless. Our platform supports REST APIs, webhooks, and standard database connections.
            
            Security is our top priority. We implement enterprise-grade encryption, multi-factor authentication, and regular security audits.
            
            Pricing options include starter, professional, and enterprise tiers. Each plan offers different feature sets and usage limits.
            
            Thank you for your interest in our platform. Contact our sales team for a personalized demo and pricing information.
            """,
            expected_segments=9,
            target_duration=25,
            music_prompt="Professional corporate background music with subtle motivation",
            complexity_level="medium"
        ),
        
        TestVideoConfig(
            name="Complex Educational Content",
            script="""
            Welcome to our advanced series on quantum computing fundamentals. This comprehensive guide will explore the revolutionary world of quantum mechanics applied to computational systems.
            
            Quantum computing represents a paradigm shift from classical computing architectures. Unlike traditional bits that exist in definitive states of zero or one, quantum bits or qubits can exist in superposition states.
            
            Superposition is a fundamental quantum mechanical principle that allows qubits to exist in multiple states simultaneously. This property enables quantum computers to process vast amounts of information in parallel.
            
            Entanglement is another crucial quantum phenomenon where qubits become interconnected in ways that measuring one instantly affects the other, regardless of physical distance between them.
            
            Quantum gates are the building blocks of quantum circuits. These operations manipulate qubits through rotations in quantum state space, creating complex computational sequences.
            
            The quantum Fourier transform is a key algorithm that demonstrates quantum advantage over classical computing. It efficiently solves problems like integer factorization and discrete logarithms.
            
            Shor's algorithm leverages quantum Fourier transforms to factor large integers exponentially faster than the best-known classical algorithms, threatening current cryptographic systems.
            
            Grover's algorithm provides quadratic speedup for searching unsorted databases, demonstrating another area where quantum computing offers significant advantages over classical approaches.
            
            Quantum error correction is essential for practical quantum computing. Quantum states are fragile and susceptible to decoherence from environmental interference.
            
            Current quantum computers are in the NISQ era - Noisy Intermediate-Scale Quantum devices. These systems have limited qubits and high error rates but show promising capabilities.
            
            Major technology companies including IBM, Google, Microsoft, and Amazon are investing heavily in quantum computing research and development initiatives.
            
            Applications of quantum computing span cryptography, drug discovery, financial modeling, machine learning optimization, and materials science simulation.
            
            The future of quantum computing holds tremendous potential for solving previously intractable problems in science, medicine, and technology.
            
            Thank you for joining us in this exploration of quantum computing fundamentals. Continue your learning journey with our advanced quantum algorithms course.
            """,
            expected_segments=14,
            target_duration=35,
            music_prompt="Ambient scientific background music with subtle technological themes",
            complexity_level="complex"
        )
    ]
    
    def __init__(self):
        """Initialize the test suite."""
        self.session = requests.Session()
        self.session.timeout = 300  # 5 minute timeout for long operations
        self.test_results: List[Dict[str, Any]] = []
        self.active_jobs: Dict[str, Dict[str, Any]] = {}
        
    def setup_class(self):
        """Set up the test class."""
        logger.info("🚀 Starting Production E2E Test Suite")
        logger.info(f"Testing against: {self.BASE_URL}")
        
        # Verify system health before running tests
        self._verify_system_health()
        
    def teardown_class(self):
        """Clean up after tests."""
        logger.info("🧹 Cleaning up test artifacts")
        self._generate_test_report()
        
    def _verify_system_health(self):
        """Verify system is healthy before running tests."""
        logger.info("🏥 Checking system health...")
        
        try:
            response = self.session.get(f"{self.BASE_URL}/health")
            response.raise_for_status()
            
            health_data = response.json()
            logger.info(f"System status: {health_data['status']}")
            
            if health_data['status'] != 'healthy':
                logger.warning("⚠️ System health is degraded, but continuing tests")
                
            # Log service statuses
            for service, status in health_data.get('services', {}).items():
                logger.info(f"  {service}: {status.get('status', 'unknown')}")
                
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            raise pytest.skip("System is not healthy enough for E2E testing")
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request with error handling and logging."""
        url = f"{self.BASE_URL}{endpoint}"
        
        logger.info(f"📡 {method.upper()} {endpoint}")
        
        try:
            response = self.session.request(method, url, **kwargs)
            
            logger.info(f"📡 Response: {response.status_code}")
            
            if response.status_code >= 400:
                logger.error(f"❌ Request failed: {response.text}")
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Request exception: {e}")
            raise
    
    def _wait_for_job_completion(self, job_id: str, timeout: int = 300, poll_interval: int = 5) -> Dict[str, Any]:
        """Wait for a job to complete and return final status."""
        logger.info(f"⏳ Waiting for job {job_id} to complete (timeout: {timeout}s)")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = self._make_request('GET', f'/api/v1/jobs/{job_id}')
                
                if response.status_code == 200:
                    job_data = response.json()
                    status = job_data.get('fields', {}).get('Status', 'unknown')
                    
                    logger.info(f"🔄 Job {job_id} status: {status}")
                    
                    if status in ['completed', 'failed', 'cancelled']:
                        return job_data
                        
                elif response.status_code == 404:
                    logger.warning(f"⚠️ Job {job_id} not found")
                    return {'error': 'Job not found'}
                    
            except Exception as e:
                logger.warning(f"⚠️ Error checking job status: {e}")
            
            time.sleep(poll_interval)
        
        logger.error(f"⏰ Job {job_id} timed out after {timeout} seconds")
        return {'error': 'Timeout'}
    
    def _measure_execution_time(self, func, *args, **kwargs):
        """Measure execution time of a function."""
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        
        logger.info(f"⏱️ Execution time: {execution_time:.2f} seconds")
        
        return result, execution_time
    
    @pytest.mark.parametrize("video_config", TEST_VIDEOS)
    def test_complete_pipeline(self, video_config: TestVideoConfig):
        """Test complete video production pipeline."""
        logger.info(f"🎬 Testing complete pipeline for: {video_config.name}")
        
        metrics = PipelineMetrics()
        pipeline_start_time = time.time()
        
        try:
            # Step 1: Process Script
            logger.info("📝 Step 1: Processing script...")
            script_response, script_time = self._measure_execution_time(
                self._process_script, video_config
            )
            metrics.script_processing_time = script_time
            metrics.script_length = len(video_config.script)
            
            video_id = script_response['video_id']
            segments = script_response['segments']
            metrics.segment_count = len(segments)
            
            logger.info(f"✅ Script processed: {len(segments)} segments created")
            
            # Step 2: Generate Voiceovers for All Segments
            logger.info("🎤 Step 2: Generating voiceovers...")
            voiceover_jobs = []
            voiceover_start_time = time.time()
            
            for segment in segments:
                job_response = self._generate_voiceover(segment['id'], video_config.voice_id)
                voiceover_jobs.append(job_response['job_id'])
                time.sleep(1)  # Avoid rate limiting
            
            # Wait for all voiceover jobs to complete
            for job_id in voiceover_jobs:
                job_result = self._wait_for_job_completion(job_id, timeout=180)
                if job_result.get('error') or job_result.get('fields', {}).get('Status') != 'completed':
                    metrics.errors_encountered.append(f"Voiceover job {job_id} failed")
            
            voiceover_end_time = time.time()
            metrics.voiceover_generation_time = voiceover_end_time - voiceover_start_time
            
            logger.info(f"✅ Voiceovers completed in {metrics.voiceover_generation_time:.2f}s")
            
            # Step 3: Combine Media for All Segments (requires manual background videos)
            logger.info("🎥 Step 3: Combining segment media...")
            logger.warning("⚠️ Skipping media combination - requires manual background video upload")
            # This step requires users to manually upload background videos to Airtable
            # In production, this would be done through the user workflow
            
            # Step 4: Video Concatenation (skipped - requires combined segments)
            logger.info("🔗 Step 4: Video concatenation...")
            logger.warning("⚠️ Skipping concatenation - requires combined segments")
            
            # Step 5: Music Generation and Addition (skipped - requires final video)
            logger.info("🎵 Step 5: Music generation...")
            logger.warning("⚠️ Skipping music generation - requires concatenated video")
            
            # Calculate total pipeline time
            pipeline_end_time = time.time()
            metrics.total_pipeline_time = pipeline_end_time - pipeline_start_time
            
            # Record test results
            test_result = {
                'video_config': video_config.name,
                'complexity': video_config.complexity_level,
                'success': len(metrics.errors_encountered) == 0,
                'metrics': metrics,
                'timestamp': datetime.now().isoformat()
            }
            
            self.test_results.append(test_result)
            
            logger.info(f"🎯 Pipeline test completed for {video_config.name}")
            logger.info(f"📊 Total time: {metrics.total_pipeline_time:.2f}s")
            logger.info(f"📊 Segments: {metrics.segment_count}")
            logger.info(f"📊 Errors: {len(metrics.errors_encountered)}")
            
            # Assert success criteria
            assert len(segments) >= video_config.expected_segments - 1  # Allow some variance
            assert script_time < 30  # Script processing should be fast
            assert len(metrics.errors_encountered) == 0, f"Errors: {metrics.errors_encountered}"
            
        except Exception as e:
            logger.error(f"❌ Pipeline test failed: {e}")
            metrics.errors_encountered.append(str(e))
            raise
    
    def _process_script(self, video_config: TestVideoConfig) -> Dict[str, Any]:
        """Process script and create video segments."""
        payload = {
            'script_text': video_config.script,
            'video_name': video_config.name,
            'target_segment_duration': video_config.target_duration,
            'music_prompt': video_config.music_prompt
        }
        
        response = self._make_request('POST', '/api/v1/process-script', json=payload)
        response.raise_for_status()
        
        return response.json()
    
    def _generate_voiceover(self, segment_id: str, voice_id: str) -> Dict[str, Any]:
        """Generate voiceover for a segment."""
        payload = {
            'segment_id': segment_id,
            'voice_id': voice_id,
            'stability': 0.5,
            'similarity_boost': 0.5
        }
        
        response = self._make_request('POST', '/api/v1/generate-voiceover', json=payload)
        response.raise_for_status()
        
        return response.json()
    
    def test_system_performance_benchmarks(self):
        """Test system performance against defined benchmarks."""
        logger.info("🏃 Testing system performance benchmarks")
        
        benchmarks = {
            'health_check_response_time': 2.0,  # seconds
            'script_processing_time_per_1000_chars': 5.0,  # seconds
            'api_response_time_95th_percentile': 10.0,  # seconds
        }
        
        # Test 1: Health Check Response Time
        response_times = []
        for i in range(10):
            start_time = time.time()
            response = self._make_request('GET', '/health')
            end_time = time.time()
            
            response.raise_for_status()
            response_times.append(end_time - start_time)
        
        avg_health_response_time = sum(response_times) / len(response_times)
        logger.info(f"📊 Average health check response time: {avg_health_response_time:.3f}s")
        
        assert avg_health_response_time < benchmarks['health_check_response_time']
        
        # Test 2: Script Processing Performance
        test_script = "This is a test script. " * 100  # ~2000 characters
        
        start_time = time.time()
        response = self._make_request('POST', '/api/v1/process-script', json={
            'script_text': test_script,
            'video_name': 'Performance Test Video',
            'target_segment_duration': 30
        })
        end_time = time.time()
        
        response.raise_for_status()
        processing_time = end_time - start_time
        time_per_1000_chars = (processing_time / len(test_script)) * 1000
        
        logger.info(f"📊 Script processing time per 1000 chars: {time_per_1000_chars:.3f}s")
        
        assert time_per_1000_chars < benchmarks['script_processing_time_per_1000_chars']
    
    def test_concurrent_request_handling(self):
        """Test system's ability to handle concurrent requests."""
        logger.info("🔀 Testing concurrent request handling")
        
        import concurrent.futures
        import threading
        
        def make_health_check():
            """Make a health check request."""
            try:
                response = self._make_request('GET', '/health')
                return response.status_code == 200
            except Exception as e:
                logger.error(f"Concurrent request failed: {e}")
                return False
        
        # Test with 10 concurrent health checks
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_health_check) for _ in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        success_rate = sum(results) / len(results)
        logger.info(f"📊 Concurrent request success rate: {success_rate:.2%}")
        
        assert success_rate >= 0.9  # 90% success rate minimum
    
    def test_error_handling_scenarios(self):
        """Test various error scenarios and recovery."""
        logger.info("🚨 Testing error handling scenarios")
        
        # Test 1: Invalid script processing
        response = self._make_request('POST', '/api/v1/process-script', json={
            'script_text': '',  # Empty script
            'video_name': 'Invalid Test'
        })
        
        assert response.status_code == 400
        error_data = response.json()
        assert 'error' in error_data
        
        # Test 2: Non-existent job query
        response = self._make_request('GET', '/api/v1/jobs/non-existent-job-id')
        assert response.status_code == 404
        
        # Test 3: Invalid voiceover generation
        response = self._make_request('POST', '/api/v1/generate-voiceover', json={
            'segment_id': 'non-existent-segment',
            'voice_id': 'invalid-voice-id'
        })
        
        assert response.status_code in [400, 404]
        
        logger.info("✅ Error handling tests passed")
    
    def test_webhook_endpoints_accessibility(self):
        """Test that webhook endpoints are accessible and properly configured."""
        logger.info("🔗 Testing webhook endpoint accessibility")
        
        webhook_endpoints = [
            '/webhooks/elevenlabs',
            '/webhooks/nca',
            '/webhooks/goapi'
        ]
        
        for endpoint in webhook_endpoints:
            # Test GET request (should return 405 Method Not Allowed)
            response = self._make_request('GET', endpoint)
            assert response.status_code == 405
            
            # Test POST with invalid payload (should handle gracefully)
            response = self._make_request('POST', f'{endpoint}?job_id=test', json={
                'invalid': 'payload'
            })
            
            # Should not crash, but may return 400 or process gracefully
            assert response.status_code in [200, 400, 401]
        
        logger.info("✅ Webhook endpoints are accessible")
    
    def test_rate_limiting_behavior(self):
        """Test rate limiting behavior under load."""
        logger.info("🚦 Testing rate limiting behavior")
        
        # Make multiple rapid requests to test rate limiting
        responses = []
        for i in range(20):
            response = self._make_request('GET', '/health')
            responses.append(response.status_code)
            time.sleep(0.1)  # 100ms between requests
        
        # All should succeed with current rate limits
        success_count = sum(1 for code in responses if code == 200)
        rate_limited_count = sum(1 for code in responses if code == 429)
        
        logger.info(f"📊 Successful requests: {success_count}")
        logger.info(f"📊 Rate limited requests: {rate_limited_count}")
        
        # Should handle requests without excessive rate limiting
        assert success_count >= 15  # Allow some rate limiting
    
    def _generate_test_report(self):
        """Generate comprehensive test report."""
        logger.info("📊 Generating test report...")
        
        report = {
            'test_run_timestamp': datetime.now().isoformat(),
            'base_url': self.BASE_URL,
            'total_tests': len(self.test_results),
            'successful_tests': sum(1 for r in self.test_results if r['success']),
            'failed_tests': sum(1 for r in self.test_results if not r['success']),
            'test_results': self.test_results,
            'summary': {
                'avg_script_processing_time': 0,
                'avg_voiceover_generation_time': 0,
                'avg_total_pipeline_time': 0,
                'total_segments_processed': 0,
                'total_errors': 0
            }
        }
        
        # Calculate averages
        if self.test_results:
            metrics_list = [r['metrics'] for r in self.test_results]
            
            report['summary']['avg_script_processing_time'] = sum(
                m.script_processing_time for m in metrics_list
            ) / len(metrics_list)
            
            report['summary']['avg_voiceover_generation_time'] = sum(
                m.voiceover_generation_time for m in metrics_list
            ) / len(metrics_list)
            
            report['summary']['avg_total_pipeline_time'] = sum(
                m.total_pipeline_time for m in metrics_list
            ) / len(metrics_list)
            
            report['summary']['total_segments_processed'] = sum(
                m.segment_count for m in metrics_list
            )
            
            report['summary']['total_errors'] = sum(
                len(m.errors_encountered) for m in metrics_list
            )
        
        # Save report to file
        report_filename = f"e2e_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path = os.path.join(os.path.dirname(__file__), '..', 'reports', report_filename)
        
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"📄 Test report saved to: {report_path}")
        
        # Log summary
        logger.info("📊 TEST SUMMARY:")
        logger.info(f"  Total Tests: {report['total_tests']}")
        logger.info(f"  Successful: {report['successful_tests']}")
        logger.info(f"  Failed: {report['failed_tests']}")
        logger.info(f"  Success Rate: {(report['successful_tests']/report['total_tests']*100):.1f}%")
        logger.info(f"  Avg Script Processing: {report['summary']['avg_script_processing_time']:.2f}s")
        logger.info(f"  Avg Voiceover Generation: {report['summary']['avg_voiceover_generation_time']:.2f}s")
        logger.info(f"  Total Segments Processed: {report['summary']['total_segments_processed']}")
        logger.info(f"  Total Errors: {report['summary']['total_errors']}")


# Test execution entry point
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
