"""OpenAI service for GPT-4o API integration."""

import logging
import os
from typing import List, Dict, Optional, Tuple
import openai
from openai import OpenAI
import time
import json

from config import get_config
from utils.logger import APILogger

logger = logging.getLogger(__name__)
api_logger = APILogger()


class OpenAIService:
    """Service for interacting with OpenAI's GPT-4o model."""
    
    # ElevenLabs markup prompt
    MARKUP_PROMPT = """# ElevenLabs TTS Advanced Markup Generator

You are an expert at analyzing text for speech synthesis. Your task is to take a text segment and apply ElevenLabs markup and text modifications for optimal text-to-speech rendering.

## Input Format
You will receive exactly:
1. **Previous segment** (the segment immediately before the target)
2. **TARGET SEGMENT** (the segment to be marked up)
3. **Following segment** (the segment immediately after the target)

## ElevenLabs Modification Techniques

### 1. Break Tags
- `<break time="0.3s"/>` - micro pause (hesitation)
- `<break time="0.5s"/>` - brief pause (commas, short breaths)
- `<break time="1.0s"/>` - medium pause (end of thoughts)
- `<break time="1.5s"/>` - dramatic pause (emphasis, revelations)
- `<break time="2.0s"/>` - significant break (scene transitions)

### 2. Natural Punctuation for Organic Flow
- **Ellipses (...)**: Natural trailing off or hesitation
  - "I don't know..." (uncertainty)
  - "Well... maybe" (contemplation)
- **Em-dashes (—)**: Interruption or dramatic pause
  - "The truth—if you can handle it—is complicated"
  - "I never—" (cut off mid-sentence)
- **Combination**: Mix SSML breaks with punctuation
  - "I... <break time="0.5s"/> I don't know" (stuttering hesitation)
  - "Wait—<break time="1.0s"/> that's impossible!"

### 3. Capitalization for Emphasis
- Single words: "This is UNACCEPTABLE"
- Key phrases: "You must NEVER FORGET this"
- Building intensity: "No, no, NO, ABSOLUTELY NOT!"
- Partial emphasis: "absoLUTELY ridiculous"

### 4. Punctuation Stacking for Emotion
- **Triple exclamation (!!!)**: Urgency without distortion
  - "Run!!!" vs "Run!" (more urgent)
- **Question stacking (???)**: Incredulity
  - "You did WHAT???"
- **Mixed punctuation (?!)**: Shocked questioning
  - "He's here?!"
- **Multiple periods (...)**: Distinct from ellipsis, creates staccato
  - "No. No. No." vs "No... no... no..."

### 5. Phonetic Extensions for Natural Speech
- **Vowel elongation**: Emotional expression
  - "Noooooo!" (despair)
  - "Pleeeease?" (pleading)
  - "Whaaaat?" (disbelief)
- **Consonant extension**: Emphasis or hesitation
  - "Ssssshh" (hushing)
  - "Wellllll..." (uncertainty)
- **Mixed extensions**: Complex emotions
  - "Ohhhhh nooooo!" (realization + dismay)

## Contextual Analysis Framework

### Segment Relationship Analysis
1. **Previous → Target**: How does the previous segment set up the target?
   - Continuation: Maintain similar pacing
   - Contrast: Add transitional pause
   - Escalation: Increase intensity markers

2. **Target → Following**: How does the target lead to the next segment?
   - Cliffhanger: End with dramatic pause
   - Resolution: Gentle trailing off
   - Interruption: Sharp cutoff with dash

### Emotional Context Mapping
1. **Hesitation/Uncertainty**
   - Use: Ellipses + micro breaks + repeated words
   - Example: "I... <break time="0.3s"/> I mean... <break time="0.5s"/> maybe?"

2. **Anger/Frustration**
   - Use: CAPS + punctuation stacking + sharp breaks
   - Example: "This is RIDICULOUS!!! <break time="0.5s"/> Absolutely UNACCEPTABLE!"

3. **Surprise/Shock**
   - Use: Phonetic extension + mixed punctuation + dramatic pauses
   - Example: "Whaaaat?! <break time="1.0s"/> You're joking—<break time="0.5s"/> right?"

4. **Sadness/Despair**
   - Use: Ellipses + longer breaks + phonetic extension
   - Example: "She's... <break time="1.5s"/> she's really gone..."

5. **Excitement/Joy**
   - Use: CAPS + exclamation stacking + shorter breaks
   - Example: "YES!!! <break time="0.3s"/> We DID IT!!!"

### Segment Type Considerations

#### Dialogue Segments
- More natural punctuation, phonetic extensions, emotional markers
- Consider speaker changes between segments
- Apply character-specific voice patterns

#### Narrative Segments
- Measured breaks, selective emphasis, fewer extensions
- Consider scene transitions between segments
- Maintain consistent narrator tone

#### Transitional Segments
- If target segment bridges two scenes/topics
- Add longer breaks at beginning/end
- Use punctuation to signal shift

## Specific Pattern Examples

### Inter-Segment Transitions
- **Topic shift**: Previous ends thought → Target starts new topic
  - Add: `<break time="2.0s"/>` at beginning
- **Emotional shift**: Previous is calm → Target is intense
  - Add: Building markers (gradual CAPS, increasing punctuation)
- **Speaker change**: Previous is one character → Target is another
  - Add: `<break time="1.5s"/>` between segments

### Building Tension Across Segments
- Previous: Setup → Target: Revelation → Following: Reaction
  - Target markup: "The killer was—<break time="1.5s"/> it was YOU!!!"

### Maintaining Flow
- Previous: Question → Target: Answer → Following: Elaboration
  - Target markup: "Yes... <break time="0.5s"/> but it's complicated."

## Output Instructions

Return ONLY the marked-up target segment with:
1. All appropriate modifications applied based on contextual analysis
2. Original meaning preserved while enhancing speech delivery
3. Natural flow maintained between segments
4. No additional explanation or commentary

## Examples

**Example 1:**
Previous segment: "The doctor entered the room with the test results."
TARGET SEGMENT: "I'm afraid I have some difficult news."
Following segment: "The cancer has returned."

**Output:**
I'm afraid I have some... <break time="1.5s"/> difficult news.

**Example 2:**
Previous segment: "Everything was going according to plan."
TARGET SEGMENT: "Then the alarms started blaring."
Following segment: "Red lights flashed everywhere."

**Output:**
Then the alarms started BLARING!!!

**Example 3:**
Previous segment: "She took a deep breath before speaking."
TARGET SEGMENT: "I can't do this anymore I just can't"
Following segment: "Tears streamed down her face."

**Output:**
I can't do this anymore—<break time="0.8s"/> I just... <break time="1.0s"/> I just CAN'T."""
    
    def __init__(self):
        """Initialize OpenAI service."""
        self.config = get_config()()
        self.api_key = self.config.OPENAI_API_KEY
        
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not found in environment variables")
            self.client = None
        else:
            try:
                # Initialize OpenAI client without proxies
                # Clear any proxy-related environment variables that might interfere
                import os
                proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']
                saved_proxies = {}
                for var in proxy_vars:
                    if var in os.environ:
                        saved_proxies[var] = os.environ.pop(var)
                
                try:
                    self.client = OpenAI(api_key=self.api_key)
                finally:
                    # Restore proxy environment variables
                    for var, value in saved_proxies.items():
                        os.environ[var] = value
                        
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self.client = None
        
        self.model = "gpt-4o"
        self.max_retries = 3
        self.retry_delay = 1
    
    def generate_elevenlabs_markup(
        self,
        target_segment: str,
        previous_segment: Optional[str] = None,
        following_segment: Optional[str] = None
    ) -> str:
        """
        Generate ElevenLabs markup for a segment using GPT-4o.
        
        Args:
            target_segment: The segment to process
            previous_segment: The segment before (if any)
            following_segment: The segment after (if any)
            
        Returns:
            The marked-up segment text
        """
        # Return original text if client not initialized
        if not self.client:
            logger.warning("OpenAI client not initialized, returning original text")
            return target_segment
            
        try:
            # Build the user prompt
            user_prompt = self._build_segment_prompt(
                target_segment,
                previous_segment,
                following_segment
            )
            
            # Make API call with retries
            for attempt in range(self.max_retries):
                try:
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": self.MARKUP_PROMPT},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=0.7,
                        max_tokens=500
                    )
                    
                    marked_text = response.choices[0].message.content.strip()
                    
                    # Log the API response
                    api_logger.log_api_response(
                        service="OpenAI",
                        endpoint="chat.completions",
                        status_code=200,
                        response={
                            "model": self.model,
                            "marked_text": marked_text[:50] + "..." if len(marked_text) > 50 else marked_text
                        }
                    )
                    
                    return marked_text
                    
                except Exception as e:
                    logger.warning(f"OpenAI API attempt {attempt + 1} failed: {e}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay * (attempt + 1))
                    else:
                        raise
                        
        except Exception as e:
            logger.error(f"Failed to generate markup for segment: {e}")
            # Return original text as fallback
            return target_segment
    
    def process_segments_batch(
        self,
        segments: List[Dict[str, any]],
        batch_size: int = 5
    ) -> List[Dict[str, any]]:
        """
        Process multiple segments in batches for efficiency.
        
        Args:
            segments: List of segment dictionaries with 'text' field
            batch_size: Number of segments to process concurrently
            
        Returns:
            List of segments with added 'marked_text' field
        """
        processed_segments = []
        
        for i, segment in enumerate(segments):
            # Get context segments
            previous = segments[i - 1]['text'] if i > 0 else None
            following = segments[i + 1]['text'] if i < len(segments) - 1 else None
            
            # Generate markup
            marked_text = self.generate_elevenlabs_markup(
                segment['text'],
                previous,
                following
            )
            
            # Add to segment data
            segment_with_markup = segment.copy()
            segment_with_markup['original_text'] = segment['text']
            segment_with_markup['marked_text'] = marked_text
            
            processed_segments.append(segment_with_markup)
            
            # Small delay to avoid rate limits
            if (i + 1) % batch_size == 0:
                time.sleep(0.5)
        
        return processed_segments
    
    def _build_segment_prompt(
        self,
        target: str,
        previous: Optional[str],
        following: Optional[str]
    ) -> str:
        """Build the user prompt for GPT-4o."""
        parts = []
        
        if previous:
            parts.append(f"Previous segment: \"{previous}\"")
        else:
            parts.append("Previous segment: [NONE - This is the first segment]")
        
        parts.append(f"TARGET SEGMENT: \"{target}\"")
        
        if following:
            parts.append(f"Following segment: \"{following}\"")
        else:
            parts.append("Following segment: [NONE - This is the last segment]")
        
        return "\n".join(parts)