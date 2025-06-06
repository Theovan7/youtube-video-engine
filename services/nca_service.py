"""NCA Toolkit service for media processing and file storage."""

import logging
import json
import requests
from typing import Dict, Optional, List, Any
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import get_config
from utils.logger import APILogger
from utils.decorators import retry, rate_limit

logger = logging.getLogger(__name__)
api_logger = APILogger()


class NCAService:
    """Service for interacting with NCA Toolkit API."""
    
    def __init__(self):
        """Initialize NCA service."""
        self.config = get_config()()
        self.api_key = self.config.NCA_API_KEY
        self.base_url = self.config.NCA_BASE_URL
        
        # Create session with retry logic
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
            backoff_factor=1
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set default headers
        self.session.headers.update({
            'x-api-key': self.api_key,
            'Content-Type': 'application/json'
        })
    
    def check_health(self) -> bool:
        """Check if NCA Toolkit service is healthy."""
        try:
            # Use the NCA Toolkit test endpoint for health check
            # Using a GET request with proper headers
            headers = {'x-api-key': self.api_key}
            response = requests.get(
                f"{self.base_url}/v1/toolkit/test", 
                headers=headers,
                timeout=10  # Increased timeout
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"NCA Toolkit health check failed: {e}")
            return False
    
    @retry(max_attempts=3, exceptions=(requests.RequestException,))
    def upload_file(self, file_data: bytes, filename: str, 
                   content_type: str = 'application/octet-stream') -> Dict:
        """Upload a file directly to S3 storage."""
        try:
            import boto3
            from botocore.client import Config
            
            # Initialize S3 client with DigitalOcean Spaces credentials
            s3_client = boto3.client(
                's3',
                endpoint_url='https://nyc3.digitaloceanspaces.com',
                aws_access_key_id=self.config.NCA_S3_ACCESS_KEY,
                aws_secret_access_key=self.config.NCA_S3_SECRET_KEY,
                config=Config(signature_version='s3v4'),
                region_name=self.config.NCA_S3_REGION
            )
            
            # Generate a unique key for the file
            from datetime import datetime
            import uuid
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_id = str(uuid.uuid4())[:8]
            key = f"youtube-video-engine/voiceovers/{timestamp}_{unique_id}_{filename}"
            
            # Upload to S3
            s3_client.put_object(
                Bucket=self.config.NCA_S3_BUCKET_NAME,
                Key=key,
                Body=file_data,
                ContentType=content_type,
                ACL='public-read'  # Make it publicly accessible
            )
            
            # Return the public URL
            public_url = f"https://{self.config.NCA_S3_BUCKET_NAME}.nyc3.digitaloceanspaces.com/{key}"
            
            return {
                'url': public_url,
                'key': key,
                'bucket': self.config.NCA_S3_BUCKET_NAME
            }
            
        except Exception as e:
            api_logger.log_error('nca', e, {'operation': 'upload_file'})
            raise
    
    def combine_audio_video(self, video_url: str, audio_url: str, 
                          output_filename: str, webhook_url: Optional[str] = None,
                          custom_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Combine audio and video files using FFmpeg compose endpoint.
        If video is shorter than audio, the last frame will be held (freeze frame).
        The output duration will be determined by the audio stream.
        """
        current_payload_for_logging: Optional[Dict[str, Any]] = None
        try:
            logger.info(f"Attempting to combine video ({video_url}) and audio ({audio_url}) with output name {output_filename}.")
            logger.info(f"FFmpeg strategy: Video holds last frame if shorter than audio, output duration matches audio.")

            # Video input (Input 0) - no looping
            video_input_spec: Dict[str, Any] = {
                'file_url': video_url
            }
            
            # Audio input (Input 1)
            audio_input_spec: Dict[str, Any] = {'file_url': audio_url}

            ffmpeg_inputs_payload: List[Dict[str, Any]] = [video_input_spec, audio_input_spec]
            
            # Filters to hold last frame when video ends
            # tpad=stop_mode=clone - holds the last frame after video ends
            # The filter will extend video to match audio duration
            ffmpeg_filters_payload: List[Dict[str, Any]] = [
                {'filter': '[0:v]tpad=stop_mode=clone[v]'}
            ]
            
            # Output options
            # -map [v] -> use the filtered video with last frame hold
            # -map 1:a:0 -> take audio from second input (audio_url)
            # -c:v libx264 -> re-encode video
            # -c:a aac -> re-encode audio to AAC
            # -shortest -> stop when the shortest stream (audio) ends
            ffmpeg_output_options_payload: List[Dict[str, Any]] = [
                {'option': '-map', 'argument': '[v]'},
                {'option': '-map', 'argument': '1:a:0'},
                {'option': '-c:v', 'argument': 'libx264'},
                {'option': '-c:a', 'argument': 'aac'},
                {'option': '-shortest', 'argument': None}  # Python None becomes JSON null
            ]
            logger.info(f"Video will hold last frame if shorter than audio. Output duration will match audio. Video codec: libx264, Audio codec: aac.")

            # Define the output object, including its filename and options
            output_definition = {
                'filename': output_filename,
                'options': ffmpeg_output_options_payload
            }

            current_payload_for_logging = {
                'inputs': ffmpeg_inputs_payload,
                'filters': ffmpeg_filters_payload,  # Add the filter for last frame hold
                'outputs': [output_definition] # outputs is a list containing the output_definition
                # 'filename' is now inside output_definition
                # 'global_options' removed for simplification
            }
            
            if webhook_url:
                current_payload_for_logging['webhook_url'] = webhook_url
            if custom_id:
                current_payload_for_logging['id'] = custom_id
            
            api_logger.log_api_request('nca', 'combine_audio_video', current_payload_for_logging)
            logger.debug(f"NCA /v1/ffmpeg/compose payload: {json.dumps(current_payload_for_logging, indent=2)}")
            
            response = self.session.post(
                f"{self.base_url}/v1/ffmpeg/compose",
                json=current_payload_for_logging
            )
            response.raise_for_status()
            
            result = response.json()
            api_logger.log_api_response('nca', 'combine_audio_video', 
                                      response.status_code, result)
            logger.info(f"NCA combine_audio_video call successful for output {output_filename}. Job ID: {result.get('job_id')}")
            return result

        except requests.exceptions.RequestException as e:
            payload_str_for_log = json.dumps(current_payload_for_logging, indent=2) if current_payload_for_logging else 'Payload not constructed or error before construction'
            error_context = {
                'operation': 'combine_audio_video',
                'video_url': video_url,
                'audio_url': audio_url,
                'output_filename': output_filename,
                'payload_sent': payload_str_for_log
            }
            logger.error(f"NCA combine_audio_video API request failed: {e}. Context: {json.dumps(error_context, indent=2)}")
            api_logger.log_error('nca', e, error_context)
            raise
        except Exception as e: # Catch any other unexpected errors
            payload_str_for_log = json.dumps(current_payload_for_logging, indent=2) if current_payload_for_logging else 'Payload not constructed or error before construction'
            error_context = {
                'operation': 'combine_audio_video',
                'video_url': video_url,
                'audio_url': audio_url,
                'output_filename': output_filename,
                'stage': 'payload_construction_or_unexpected',
                'current_payload_for_logging': payload_str_for_log
            }
            logger.error(f"Unexpected error in combine_audio_video: {e}. Context: {json.dumps(error_context, indent=2)}")
            api_logger.log_error('nca', e, error_context)
            raise
    
    def concatenate_videos(self, video_urls: List[str], output_filename: str,
                         webhook_url: Optional[str] = None, 
                         custom_id: Optional[str] = None) -> Dict:
        """Concatenate multiple videos into one using NCA video concatenate endpoint."""
        try:
            # Use correct NCA Toolkit payload structure based on API documentation
            payload = {
                'video_urls': [
                    {'video_url': url} for url in video_urls  # Convert URLs to required object format
                ]
            }
            
            # Add optional parameters
            if webhook_url:
                payload['webhook_url'] = webhook_url
            
            if custom_id:
                payload['id'] = custom_id
            
            api_logger.log_api_request('nca', 'concatenate_videos', payload)
            
            # Use correct NCA Toolkit endpoint for video concatenation
            response = self.session.post(
                f"{self.base_url}/v1/video/concatenate",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            api_logger.log_api_response('nca', 'concatenate_videos', 
                                      response.status_code, result)
            
            return result
        except Exception as e:
            api_logger.log_error('nca', e, {'operation': 'concatenate_videos'})
            raise
    
    def add_background_music(self, video_url: str, music_url: str, 
                           output_filename: str, volume_ratio: float = 0.2,
                           webhook_url: Optional[str] = None,
                           custom_id: Optional[str] = None) -> Dict:
        """Add background music to a video using FFmpeg compose endpoint."""
        try:
            # Use correct NCA Toolkit payload structure based on API documentation
            payload = {
                'inputs': [
                    {'file_url': video_url},  # Video input as object with file_url
                    {'file_url': music_url}   # Music input as object with file_url
                ],
                'filters': [{
                    'filter': f'[0:a]volume=1.0[a0];[1:a]volume={volume_ratio}[a1];[a0][a1]amix=inputs=2:duration=shortest[aout]'
                }],
                'outputs': [{
                    'options': [  # Options must be in array format
                        {'option': '-map', 'argument': '0:v'},      # Map video from 1st input
                        {'option': '-map', 'argument': '[aout]'},   # Map the mixed audio stream
                        {'option': '-c:v', 'argument': 'copy'},  # Copy video without re-encoding
                        {'option': '-c:a', 'argument': 'aac'},   # Encode audio to AAC
                        {'option': '-shortest', 'argument': None} # Ensure output terminates with the shortest stream
                    ]
                }],
                'global_options': [
                    {'option': '-y'}  # Overwrite output files without asking
                ]
            }
            
            # Add optional parameters
            if webhook_url:
                payload['webhook_url'] = webhook_url
            
            if custom_id:
                payload['id'] = custom_id
            
            api_logger.log_api_request('nca', 'add_background_music', payload)
            
            # Use correct NCA Toolkit endpoint
            response = self.session.post(
                f"{self.base_url}/v1/ffmpeg/compose",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            api_logger.log_api_response('nca', 'add_background_music', 
                                      response.status_code, result)
            
            return result
        except Exception as e:
            api_logger.log_error('nca', e, {'operation': 'add_background_music'})
            raise

    def submit_ffmpeg_commands(self, commands: List[List[str]], output_filename: str,
                           input_definitions: Optional[List[Dict[str, Any]]] = None,
                           filter_strings: Optional[List[str]] = None, 
                           webhook_url: Optional[str] = None,
                           custom_id: Optional[str] = None,
                           global_ffmpeg_options: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Submit FFmpeg commands to the /v1/ffmpeg/compose endpoint.
        Output FFmpeg options are transformed into {'option': k, 'argument': v} pairs.
        Global FFmpeg options are transformed into {'option': k} objects.
        Filters are provided as raw FFmpeg filter strings.
        Input definitions are expected to have their 'options' pre-formatted if provided.

        Args:
            commands: A list containing one FFmpeg command array for output options.
                      This inner list must be flat and strictly alternating option-argument pairs.
                      Example: [['-c:v', 'libx264', '-crf', '23']]
            output_filename: The desired output filename (e.g., "processed_video.mp4").
            input_definitions: Optional list of input definitions for NCA API.
                               Each dict can include 'file_url', 'filename', and 'options'.
                               'options' should be pre-formatted: [{'option': k, 'argument': v}].
            filter_strings: Optional list of raw FFmpeg filter strings.
                            Example: ["scale=3840:-1,zoompan=z='min(zoom+0.0016,1.2)'"]
            webhook_url: Optional URL for NCA Toolkit to send a callback.
            custom_id: Optional custom identifier for the job.
            global_ffmpeg_options: Optional list of standalone global FFmpeg flags (e.g., ['-y', '-an']).
                                   These are transformed into [{'option': k}] objects.

        Returns:
            A dictionary containing the NCA Toolkit's response (e.g., job_id).
        
        Raises:
            ValueError: If 'commands' or 'global_ffmpeg_options' are improperly structured.
            requests.exceptions.RequestException: For HTTP or network-related errors.
        """
        current_payload_for_logging: Optional[Dict[str, Any]] = None
        try:
            logger.info(f"Attempting to submit FFmpeg commands for output: {output_filename}.")

            if not commands or not isinstance(commands, list) or len(commands) != 1 or \
               not commands[0] or not isinstance(commands[0], list):
                error_msg = (
                    "The 'commands' argument must be a list containing exactly one list "
                    "of FFmpeg command strings (e.g., [['-c:v', 'libx264', '-crf', '23']])."
                )
                logger.error(f"{error_msg} Received: {commands}")
                raise ValueError(error_msg)

            payload: Dict[str, Any] = {}

            if input_definitions:
                payload['inputs'] = input_definitions # Assumes options within are pre-formatted
            
            if filter_strings:
                if not isinstance(filter_strings, list) or \
                   not all(isinstance(fs, str) for fs in filter_strings):
                    err_filter_msg = f"'filter_strings' must be a list of strings. Received: {filter_strings}"
                    logger.error(err_filter_msg)
                    raise ValueError(err_filter_msg)
                payload['filters'] = [{'filter': fs} for fs in filter_strings]

            # Process output options: must be strictly alternating key-value pairs
            output_options_raw = commands[0]
            formatted_output_options = []
            if len(output_options_raw) % 2 != 0:
                err_val_msg = f"Output FFmpeg options list must contain option-argument pairs. Received: {output_options_raw}"
                logger.error(err_val_msg)
                raise ValueError(err_val_msg)
            for i in range(0, len(output_options_raw), 2):
                formatted_output_options.append({
                    "option": str(output_options_raw[i]),
                    "argument": str(output_options_raw[i+1]) # Ensure argument is string
                })
            
            payload['outputs'] = [{
                'filename': output_filename,
                'options': formatted_output_options
            }]
            
            # Process global FFmpeg options: standalone flags
            if global_ffmpeg_options:
                if not isinstance(global_ffmpeg_options, list):
                    err_glob_msg = f"global_ffmpeg_options must be a list of strings. Received: {global_ffmpeg_options}"
                    logger.error(err_glob_msg)
                    raise ValueError(err_glob_msg)
                
                formatted_global_options = []
                for opt_flag in global_ffmpeg_options:
                    if not isinstance(opt_flag, str):
                        err_flag_type = f"Each item in global_ffmpeg_options must be a string. Found: {opt_flag}"
                        logger.error(err_flag_type)
                        raise ValueError(err_flag_type)
                    formatted_global_options.append({"option": opt_flag})
                
                if formatted_global_options: # Only add if there are any
                    payload['global_options'] = formatted_global_options

            if webhook_url:
                payload['webhook_url'] = webhook_url
            if custom_id:
                payload['id'] = custom_id
            
            current_payload_for_logging = payload
            
            api_logger.log_api_request('nca', 'submit_ffmpeg_commands', current_payload_for_logging)
            logger.debug(f"NCA /v1/ffmpeg/compose payload: {json.dumps(current_payload_for_logging, indent=2)}")
            
            response = self.session.post(
                f"{self.base_url}/v1/ffmpeg/compose",
                json=current_payload_for_logging
            )
            response.raise_for_status()
            
            result = response.json()
            api_logger.log_api_response('nca', 'submit_ffmpeg_commands', 
                                      response.status_code, result)
            logger.info(f"NCA submit_ffmpeg_commands call successful for output {output_filename}. Job ID: {result.get('job_id')}")
            return result

        except requests.exceptions.RequestException as e:
            payload_str_for_log = json.dumps(current_payload_for_logging, indent=2) if current_payload_for_logging else 'Payload not constructed'
            nca_error_detail = str(e)
            if e.response is not None:
                try:
                    nca_error_detail = e.response.json()
                except json.JSONDecodeError:
                    nca_error_detail = e.response.text

            error_context = {
                'operation': 'submit_ffmpeg_commands',
                'output_filename': output_filename,
                'payload_sent': payload_str_for_log,
                'error_detail': nca_error_detail
            }
            logger.error(f"NCA submit_ffmpeg_commands API request failed: {e}. Context: {json.dumps(error_context, indent=2)}")
            api_logger.log_error('nca', e, error_context)
            raise
        except Exception as e: 
            payload_str_for_log = json.dumps(current_payload_for_logging, indent=2) if current_payload_for_logging else 'Payload not constructed'
            error_context = {
                'operation': 'submit_ffmpeg_commands',
                'output_filename': output_filename,
                'stage': 'payload_construction_or_unexpected',
                'current_payload_for_logging': payload_str_for_log,
                'error_type': type(e).__name__,
                'error_message': str(e)
            }
            logger.error(f"Unexpected error in submit_ffmpeg_commands: {e}. Context: {json.dumps(error_context, indent=2)}")
            api_logger.log_error('nca', e, error_context)
            raise


    def invoke_ffmpeg_compose_job(self,
                                  inputs_payload: List[Dict[str, Any]],
                                  outputs_payload: List[Dict[str, Any]],
                                  filters_payload: Optional[List[Dict[str, Any]]] = None,
                                  global_options_payload: Optional[List[Dict[str, Any]]] = None,
                                  webhook_url: Optional[str] = None,
                                  custom_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Invokes the NCA /v1/ffmpeg/compose endpoint with a pre-structured payload.

        Args:
            inputs_payload: The 'inputs' part of the NCA payload.
            outputs_payload: The 'outputs' part of the NCA payload.
            filters_payload: Optional 'filters' part of the NCA payload.
            global_options_payload: Optional 'global_options' part of the NCA payload.
            webhook_url: Optional URL for NCA Toolkit to send a callback.
            custom_id: Optional custom identifier for the job (will be sent as 'id').

        Returns:
            A dictionary containing the NCA Toolkit's response.
        
        Raises:
            requests.exceptions.RequestException: For HTTP or network-related errors.
            Exception: For other unexpected errors during the process.
        """
        current_payload_for_logging: Dict[str, Any] = {}
        operation_name = 'invoke_ffmpeg_compose_job' # For logging
        try:
            logger.info(f"Attempting to {operation_name}. Custom ID: {custom_id}")

            payload: Dict[str, Any] = {
                'inputs': inputs_payload,
                'outputs': outputs_payload
            }

            if filters_payload:
                payload['filters'] = filters_payload
            
            if global_options_payload:
                payload['global_options'] = global_options_payload

            if webhook_url:
                payload['webhook_url'] = webhook_url
            if custom_id:
                payload['id'] = custom_id  # NCA expects 'id' for custom identifier
            
            current_payload_for_logging = payload
            
            api_logger.log_api_request('nca', operation_name, current_payload_for_logging)
            logger.debug(f"NCA /v1/ffmpeg/compose payload for {operation_name}: {json.dumps(current_payload_for_logging, indent=2)}")
            
            response = self.session.post(
                f"{self.base_url}/v1/ffmpeg/compose",
                json=current_payload_for_logging
            )
            response.raise_for_status() # Raises HTTPError for bad responses (4XX or 5XX)
            
            result = response.json()
            api_logger.log_api_response('nca', operation_name, 
                                      response.status_code, result)
            logger.info(f"NCA {operation_name} call successful. Job ID: {result.get('job_id')}, Custom ID: {custom_id}")
            return result

        except requests.exceptions.RequestException as e:
            payload_str_for_log = json.dumps(current_payload_for_logging, indent=2) if current_payload_for_logging else 'Payload not fully constructed'
            nca_error_detail = str(e)
            if e.response is not None:
                try:
                    nca_error_detail = e.response.json()
                except json.JSONDecodeError:
                    nca_error_detail = e.response.text
            
            error_context = {
                'operation': operation_name,
                'custom_id': custom_id,
                'payload_sent': payload_str_for_log,
                'error_detail': nca_error_detail
            }
            logger.error(f"NCA {operation_name} API request failed: {e}. Context: {json.dumps(error_context, indent=2)}")
            api_logger.log_error('nca', e, error_context)
            raise
        except Exception as e: # Catch any other unexpected errors
            payload_str_for_log = json.dumps(current_payload_for_logging, indent=2) if current_payload_for_logging else 'Payload not fully constructed'
            error_context = {
                'operation': operation_name,
                'custom_id': custom_id,
                'stage': 'payload_construction_or_unexpected',
                'current_payload_for_logging': payload_str_for_log,
                'error_type': type(e).__name__,
                'error_message': str(e)
            }
            logger.error(f"Unexpected error in {operation_name}: {e}. Context: {json.dumps(error_context, indent=2)}")
            api_logger.log_error('nca', e, error_context)
            raise

    def get_job_status(self, job_id: str) -> Dict:
        """Get the status of a processing job using correct NCA endpoint."""
        try:
            api_logger.log_api_request('nca', 'get_job_status', {'job_id': job_id})
            
            # Use correct NCA Toolkit endpoint
            response = self.session.get(
                f"{self.base_url}/v1/job/status/{job_id}"
            )
            response.raise_for_status()
            
            result = response.json()
            api_logger.log_api_response('nca', 'get_job_status', 
                                      response.status_code, result)
            
            return result
        except Exception as e:
            api_logger.log_error('nca', e, {'operation': 'get_job_status'})
            raise
