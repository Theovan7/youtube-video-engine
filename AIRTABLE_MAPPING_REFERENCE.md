# Airtable Mapping Reference for Notion Database Column

## Instructions for Adding to Notion

1. Open the "YouTube Video Engine Functions" database in Notion
2. Add a new column called "Airtable Mapping" (type: Rich Text)
3. Copy the mapping information below for each function

## Function Mappings

### Process Script
**Input:**
- Creates in `Videos` table:
  - Description (from 'name' parameter)
  - Video Script (from 'script_text' parameter)

**Output:**
- Creates in `Segments` table:
  - SRT Segment ID
  - Videos (linked to created video)
  - SRT Text
  - Start Time
  - End Time
  - Timestamps

### Generate Voiceover
**Input:**
- Reads from `Segments` table:
  - SRT Text (for voiceover generation)

**Output:**
- Creates in `Jobs` table:
  - Type = 'voiceover'
  - External Job ID
  - Webhook URL
  - Status

### Combine Segment Media
**Input:**
- Reads from `Segments` table:
  - Video field (user-uploaded background video)

**Output:**
- Updates `Segments` table:
  - Combined media URL

### Combine All Segments
**Input:**
- Reads from `Segments` table:
  - All linked segments via Videos field

**Output:**
- Updates `Videos` table:
  - AI Video (combined video attachment)

### Generate and Add Music
**Input:**
- Reads from `Videos` table:
  - AI Video field

**Output:**
- Updates `Videos` table:
  - Music (attachment)
  - AI Music Task ID
  - Video + Music (final video)

### Health Check
**Airtable Mapping:** None - No database interaction

### Get Job Status
**Input:**
- Reads from `Jobs` table using job_id

**Output:**
- Returns: Status, Type, External Job ID, Error Details

### ElevenLabs Webhook
**Input:**
- Creates in `Webhook Events` table:
  - Service = 'elevenlabs'
  - Raw Payload

**Output:**
- Updates `Jobs` table: Status, Response Payload
- Updates `Segments` table: Voiceover URL

### Script Processing Service
**Airtable Mapping:** None - Internal processing only
