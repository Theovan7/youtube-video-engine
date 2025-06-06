"""Script processing service for parsing scripts into timed segments."""

import logging
import re
import math
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

from config import get_config
from utils.logger import APILogger
from services.openai_service import OpenAIService

logger = logging.getLogger(__name__)
api_logger = APILogger()


@dataclass
class Segment:
    """Represents a script segment."""
    text: str
    order: int
    start_time: float
    end_time: float
    estimated_duration: float
    word_count: int
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


class ScriptProcessor:
    """Service for processing scripts into timed segments."""
    
    # Average speaking rate (words per minute)
    WORDS_PER_MINUTE = 150
    # Words per second
    WORDS_PER_SECOND = WORDS_PER_MINUTE / 60
    
    def __init__(self):
        """Initialize script processor."""
        self.config = get_config()()
        self.default_segment_duration = self.config.DEFAULT_SEGMENT_DURATION
        self.openai_service = OpenAIService()
    
    def process_script(self, script: str, target_segment_duration: Optional[int] = None) -> List[Segment]:
        """
        Process a script into timed segments.
        
        Args:
            script: The script text to process
            target_segment_duration: Target duration for each segment in seconds
            
        Returns:
            List of Segment objects
        """
        if not script or not script.strip():
            raise ValueError("Script cannot be empty")
        
        duration = target_segment_duration or self.default_segment_duration
        
        # Clean and normalize the script
        clean_script = self._clean_script(script)
        
        # Split into segments
        segments = self._split_into_segments(clean_script, duration)
        
        # Calculate timings
        segments_with_timing = self._calculate_timings(segments)
        
        logger.info(f"Processed script into {len(segments_with_timing)} segments")
        
        return segments_with_timing
    
    def process_script_by_newlines(self, script: str) -> List[Segment]:
        """
        Process a script into timed segments by splitting on newlines.
        
        Args:
            script: The script text to process
            
        Returns:
            List of Segment objects
        """
        if not script or not script.strip():
            raise ValueError("Script cannot be empty")
        
        # Normalize line endings (handle Windows \r\n and Unix \n)
        script = script.replace('\r\n', '\n').replace('\r', '\n')
        
        # Split by newlines and filter out empty lines
        lines = script.strip().split('\n')
        segments = [line.strip() for line in lines if line.strip()]
        
        # Calculate timings for each segment
        segments_with_timing = self._calculate_timings(segments)
        
        logger.info(f"Processed script into {len(segments_with_timing)} segments using newline segmentation")
        
        return segments_with_timing
    
    def _clean_script(self, script: str) -> str:
        """Clean and normalize script text."""
        # Remove extra whitespace
        script = re.sub(r'\s+', ' ', script)
        
        # Normalize line breaks
        script = re.sub(r'\n+', '\n', script)
        
        # Remove leading/trailing whitespace
        script = script.strip()
        
        return script
    
    def _split_into_segments(self, script: str, target_duration: int) -> List[str]:
        """Split script into segments based on target duration."""
        # Calculate target words per segment
        target_words = int(target_duration * self.WORDS_PER_SECOND)
        
        # Split script into sentences
        sentences = self._split_into_sentences(script)
        
        segments = []
        current_segment = []
        current_word_count = 0
        
        for sentence in sentences:
            sentence_words = sentence.split()
            sentence_word_count = len(sentence_words)
            
            # If adding this sentence would exceed target, create new segment
            if current_word_count + sentence_word_count > target_words * 1.2 and current_segment:
                # Join current segment and add to segments
                segments.append(' '.join(current_segment))
                current_segment = [sentence]
                current_word_count = sentence_word_count
            else:
                # Add sentence to current segment
                current_segment.append(sentence)
                current_word_count += sentence_word_count
                
                # If we've reached approximately the target, create segment
                if current_word_count >= target_words * 0.8:
                    segments.append(' '.join(current_segment))
                    current_segment = []
                    current_word_count = 0
        
        # Add any remaining content
        if current_segment:
            segments.append(' '.join(current_segment))
        
        return segments
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Split on sentence endings
        sentence_endings = r'[.!?]+'
        sentences = re.split(f'({sentence_endings})', text)
        
        # Reconstruct sentences with their endings
        reconstructed = []
        for i in range(0, len(sentences) - 1, 2):
            sentence = sentences[i].strip()
            if i + 1 < len(sentences):
                ending = sentences[i + 1]
                sentence += ending
            if sentence:
                reconstructed.append(sentence)
        
        # Handle last element if it's not empty
        if len(sentences) % 2 == 1 and sentences[-1].strip():
            reconstructed.append(sentences[-1].strip())
        
        return reconstructed
    
    def _calculate_timings(self, segments: List[str]) -> List[Segment]:
        """Calculate timing information for each segment."""
        timed_segments = []
        current_time = 0.0
        
        for i, text in enumerate(segments):
            # Count words
            word_count = len(text.split())
            
            # Calculate duration based on word count
            duration = word_count / self.WORDS_PER_SECOND
            
            # Create segment
            segment = Segment(
                text=text,
                order=i + 1,
                start_time=current_time,
                end_time=current_time + duration,
                estimated_duration=duration,
                word_count=word_count
            )
            
            timed_segments.append(segment)
            current_time += duration
        
        return timed_segments
    
    def merge_segments(self, segments: List[Segment], indices: List[int]) -> Segment:
        """Merge multiple segments into one."""
        if not indices:
            raise ValueError("No indices provided for merging")
        
        # Sort indices
        indices = sorted(indices)
        
        # Validate indices
        for idx in indices:
            if idx < 0 or idx >= len(segments):
                raise ValueError(f"Invalid segment index: {idx}")
        
        # Get segments to merge
        segments_to_merge = [segments[i] for i in indices]
        
        # Combine text
        merged_text = ' '.join(seg.text for seg in segments_to_merge)
        
        # Calculate new timing
        start_time = segments_to_merge[0].start_time
        end_time = segments_to_merge[-1].end_time
        duration = end_time - start_time
        word_count = sum(seg.word_count for seg in segments_to_merge)
        
        return Segment(
            text=merged_text,
            order=segments_to_merge[0].order,
            start_time=start_time,
            end_time=end_time,
            estimated_duration=duration,
            word_count=word_count
        )
    
    def split_segment(self, segment: Segment, split_point: int) -> tuple[Segment, Segment]:
        """Split a segment at a specific word index."""
        words = segment.text.split()
        
        if split_point <= 0 or split_point >= len(words):
            raise ValueError(f"Invalid split point: {split_point}")
        
        # Split text
        first_text = ' '.join(words[:split_point])
        second_text = ' '.join(words[split_point:])
        
        # Calculate timing for each part
        first_word_count = len(words[:split_point])
        second_word_count = len(words[split_point:])
        
        first_duration = first_word_count / self.WORDS_PER_SECOND
        second_duration = second_word_count / self.WORDS_PER_SECOND
        
        # Create segments
        first_segment = Segment(
            text=first_text,
            order=segment.order,
            start_time=segment.start_time,
            end_time=segment.start_time + first_duration,
            estimated_duration=first_duration,
            word_count=first_word_count
        )
        
        second_segment = Segment(
            text=second_text,
            order=segment.order + 1,
            start_time=segment.start_time + first_duration,
            end_time=segment.end_time,
            estimated_duration=second_duration,
            word_count=second_word_count
        )
        
        return first_segment, second_segment
    
    def estimate_script_duration(self, script: str) -> float:
        """Estimate total duration of a script in seconds."""
        word_count = len(script.split())
        return word_count / self.WORDS_PER_SECOND
    
    def process_segments_with_markup(self, segments: List[Segment]) -> List[Dict]:
        """
        Process segments to add ElevenLabs markup using GPT-4o.
        
        Args:
            segments: List of Segment objects
            
        Returns:
            List of dictionaries with both original and marked-up text
        """
        try:
            processed_segments = []
            
            for i, segment in enumerate(segments):
                # Get context segments
                previous_text = segments[i - 1].text if i > 0 else None
                following_text = segments[i + 1].text if i < len(segments) - 1 else None
                
                # Generate markup
                marked_text = self.openai_service.generate_elevenlabs_markup(
                    segment.text,
                    previous_text,
                    following_text
                )
                
                # Create segment data with both original and marked text
                segment_data = {
                    'original_text': segment.text,
                    'text': marked_text,  # This will go in 'SRT Text' field
                    'order': segment.order,
                    'start_time': segment.start_time,
                    'end_time': segment.end_time,
                    'estimated_duration': segment.estimated_duration,
                    'word_count': segment.word_count
                }
                
                processed_segments.append(segment_data)
                
            logger.info(f"Processed {len(processed_segments)} segments with ElevenLabs markup")
            return processed_segments
            
        except Exception as e:
            logger.error(f"Error processing segments with markup: {e}")
            # Fallback: return segments without markup
            return [
                {
                    'original_text': seg.text,
                    'text': seg.text,
                    'order': seg.order,
                    'start_time': seg.start_time,
                    'end_time': seg.end_time,
                    'estimated_duration': seg.estimated_duration,
                    'word_count': seg.word_count
                }
                for seg in segments
            ]
