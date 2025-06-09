#!/usr/bin/env python3
"""
Pipeline test orchestrator for YouTube Video Engine
Runs a complete video production pipeline with function-organized test data
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from testing_environment.test_function import FunctionTester
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class PipelineTester:
    """Orchestrates a complete pipeline test"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv('TEST_BASE_URL', 'http://localhost:5000')
        self.function_tester = FunctionTester(self.base_url)
        self.test_inputs_dir = Path(__file__).parent / "test_inputs"
        self.pipeline_data = {}
        
    def run_pipeline(self, pipeline_name: str = "default"):
        """Run a complete pipeline test"""
        
        print(f"\n{'='*70}")
        print(f"YouTube Video Engine - Pipeline Test: {pipeline_name}")
        print(f"{'='*70}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"API URL: {self.base_url}")
        
        # Define pipeline steps
        pipeline_steps = [
            {
                "name": "Script Processing",
                "function": "process-script",
                "required": True,
                "saves_data": ["video_id", "segment_ids"]
            },
            {
                "name": "Voiceover Generation",
                "function": "generate-voiceover",
                "required": True,
                "uses_data": ["segment_ids"],
                "repeat_for": "segments"
            },
            {
                "name": "AI Image Generation",
                "function": "generate-ai-image",
                "required": False,
                "uses_data": ["segment_ids"],
                "repeat_for": "segments"
            },
            {
                "name": "Video Generation",
                "function": "generate-video",
                "required": False,
                "uses_data": ["segment_ids"],
                "depends_on": "AI Image Generation"
            },
            {
                "name": "Segment Media Combination",
                "function": "combine-segment-media",
                "required": True,
                "uses_data": ["segment_ids"],
                "repeat_for": "segments"
            },
            {
                "name": "Combine All Segments",
                "function": "combine-all-segments",
                "required": True,
                "uses_data": ["video_id"]
            },
            {
                "name": "Add Background Music",
                "function": "generate-and-add-music",
                "required": False,
                "uses_data": ["video_id"]
            }
        ]
        
        results = []
        
        # Setup
        self.function_tester.framework.setup()
        
        # Run each step
        for step in pipeline_steps:
            print(f"\n{'─'*60}")
            print(f"📋 Step: {step['name']}")
            print(f"{'─'*60}")
            
            # Check dependencies
            if "depends_on" in step:
                dep_result = next((r for r in results if r["name"] == step["depends_on"]), None)
                if not dep_result or not dep_result["success"]:
                    print(f"⏭️  Skipping - dependency '{step['depends_on']}' not met")
                    continue
            
            try:
                # Check if this step needs to repeat for each segment
                if step.get("repeat_for") == "segments" and "segment_ids" in self.pipeline_data:
                    segment_ids = self.pipeline_data["segment_ids"][:2]  # Test first 2 segments
                    
                    step_success = True
                    for i, segment_id in enumerate(segment_ids):
                        print(f"\n  Processing segment {i+1}/{len(segment_ids)}: {segment_id}")
                        
                        # Update current segment in pipeline data
                        self.pipeline_data["current_segment_id"] = segment_id
                        
                        # Run function test
                        success = self._run_step(step)
                        if not success:
                            step_success = False
                            if step["required"]:
                                break
                                
                        time.sleep(1)  # Rate limiting between segments
                    
                    results.append({
                        "name": step["name"],
                        "success": step_success,
                        "segments_processed": len(segment_ids)
                    })
                    
                else:
                    # Single execution
                    success = self._run_step(step)
                    results.append({
                        "name": step["name"],
                        "success": success
                    })
                    
                    if not success and step["required"]:
                        print(f"\n❌ Required step '{step['name']}' failed. Stopping pipeline.")
                        break
                        
            except Exception as e:
                print(f"❌ Step failed with error: {e}")
                results.append({
                    "name": step["name"],
                    "success": False,
                    "error": str(e)
                })
                
                if step["required"]:
                    break
        
        # Summary
        self._print_summary(results)
        
        # Save pipeline data
        pipeline_data_file = self.test_inputs_dir / f"pipeline_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(pipeline_data_file, 'w') as f:
            json.dump(self.pipeline_data, f, indent=2)
        print(f"\n💾 Pipeline data saved to: {pipeline_data_file}")
        
        return all(r["success"] for r in results if r.get("name") in [s["name"] for s in pipeline_steps if s["required"]])
    
    def _run_step(self, step: dict) -> bool:
        """Run a single pipeline step"""
        function_name = step["function"]
        
        # Prepare payload based on pipeline data
        payload = self._prepare_payload(function_name)
        
        # Save payload for debugging
        payload_file = self.test_inputs_dir / f"{function_name}/payloads/pipeline_test.json"
        payload_file.parent.mkdir(parents=True, exist_ok=True)
        with open(payload_file, 'w') as f:
            json.dump(payload, f, indent=2)
        
        # Run the function test
        success = self.function_tester.run_function_test(function_name, str(payload_file))
        
        # Extract data for next steps
        if success and "saves_data" in step:
            self._extract_step_data(function_name, step["saves_data"])
        
        return success
    
    def _prepare_payload(self, function_name: str) -> dict:
        """Prepare payload based on function and pipeline data"""
        
        if function_name == "process-script":
            # Load a test script
            script_file = self.test_inputs_dir / "process-script/scripts/short_demo.txt"
            if script_file.exists():
                script_text = script_file.read_text()
            else:
                script_text = "Test pipeline script.\n\nThis is segment one.\n\nThis is segment two."
            
            return {
                "script_text": script_text,
                "video_name": f"Pipeline Test - {datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "target_segment_duration": 30
            }
            
        elif function_name == "generate-voiceover":
            return {
                "record_id": self.pipeline_data.get("current_segment_id")
            }
            
        elif function_name == "generate-ai-image":
            return {
                "record_id": self.pipeline_data.get("current_segment_id"),
                "style": "photorealistic"
            }
            
        elif function_name == "combine-segment-media":
            return {
                "segment_id": self.pipeline_data.get("current_segment_id")
            }
            
        elif function_name == "combine-all-segments":
            return {
                "video_id": self.pipeline_data.get("video_id")
            }
            
        elif function_name == "generate-and-add-music":
            return {
                "video_id": self.pipeline_data.get("video_id"),
                "music_prompt": "upbeat corporate background music",
                "music_duration": 120,
                "music_volume": 0.3
            }
            
        return {}
    
    def _extract_step_data(self, function_name: str, data_keys: list):
        """Extract data from step results"""
        
        # Read the latest test report
        reports = list(Path(".").glob(f"test_report_{function_name}_*.txt"))
        if not reports:
            return
            
        latest_report = max(reports, key=lambda p: p.stat().st_mtime)
        
        # For now, manually extract from process-script
        if function_name == "process-script":
            # Check for saved segment IDs
            segment_ids_file = self.test_inputs_dir / "process-script/generated_segment_ids.json"
            if segment_ids_file.exists():
                with open(segment_ids_file, 'r') as f:
                    data = json.load(f)
                    self.pipeline_data.update(data)
    
    def _print_summary(self, results: list):
        """Print pipeline summary"""
        print(f"\n{'='*70}")
        print("Pipeline Test Summary")
        print(f"{'='*70}")
        
        total_steps = len(results)
        successful_steps = sum(1 for r in results if r["success"])
        
        print(f"\nCompleted: {successful_steps}/{total_steps} steps")
        
        print("\nStep Results:")
        for result in results:
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {result['name']}")
            if "segments_processed" in result:
                print(f"     Processed {result['segments_processed']} segments")
            if "error" in result:
                print(f"     Error: {result['error']}")
        
        print(f"\nFinished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Run pipeline tests")
    parser.add_argument("--pipeline", default="default",
                       help="Pipeline to run (default, quick, full)")
    parser.add_argument("--url", help="API base URL", default="http://localhost:5000")
    
    args = parser.parse_args()
    
    tester = PipelineTester(args.url)
    success = tester.run_pipeline(args.pipeline)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()