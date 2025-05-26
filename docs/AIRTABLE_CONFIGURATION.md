# 🗃️ Airtable Configuration Guide

## Overview
This guide provides step-by-step instructions for configuring the Airtable database structure to support the YouTube Video Engine's complete workflow with proper linked fields and optimized views.

## 📊 Current Table Structure

The system uses four main tables:

### 1. **Videos Table** (Main Project Records)
**Existing Fields:**
- `Description` (Single line text) - Video name/title
- `Video Script` (Long text) - Original script content
- `Segments` (Link to Segments table) - Connected segment records
- `Music Prompt` (Long text) - AI music generation prompt
- `Combined Segments Video` (Attachment) - Concatenated segments
- `Final Video` (Attachment) - Complete video with music
- `Music` (Attachment) - Generated background music

### 2. **Segments Table** (Individual Video Segments)
**Existing Fields:**
- `Video` (Link to Videos table) - Parent video
- `SRT Text` (Long text) - Segment script text
- `SRT Segment ID` (Number) - Segment order/number
- `Start Time` (Number) - Segment start time in seconds
- `End Time` (Number) - Segment end time in seconds
- `Video` (Attachment) - User-uploaded background video
- `Voiceover` (Attachment) - Generated AI voiceover
- `Combined` (Attachment) - Combined segment video

### 3. **Jobs Table** (Processing Status Tracking)
**Existing Fields:**
- `Type` (Single select) - Job type (voiceover, combine, etc.)
- `Status` (Single select) - Processing status
- `External Job ID` (Single line text) - External service job ID
- `Webhook URL` (URL) - Callback URL
- `Request Payload` (Long text) - Original request data
- `Response Payload` (Long text) - Service response data
- `Error Details` (Long text) - Error information if failed

### 4. **Webhook Events Table** (Event Logging)
**Existing Fields:**
- `Service` (Single select) - Source service (ElevenLabs, NCA, GoAPI)
- `Endpoint` (Single line text) - Webhook endpoint
- `Raw Payload` (Long text) - Complete webhook payload
- `Processed` (Checkbox) - Processing completion status
- `Success` (Checkbox) - Processing success status

## 🔧 Required Manual Configuration

### Step 1: Add Linked Fields to Jobs Table

**1.1 Add "Related Video" Field:**
1. Open Airtable base in browser
2. Navigate to **Jobs** table
3. Click **+** to add new field
4. Select **Link to another record**
5. Choose **Videos** table
6. Name: `Related Video`
7. Description: "Link to the video this job processes"
8. Click **Create field**

**1.2 Add "Related Segment" Field:**
1. Click **+** to add new field
2. Select **Link to another record**
3. Choose **Segments** table
4. Name: `Related Segment`
5. Description: "Link to the segment this job processes"
6. Click **Create field**

### Step 2: Create Lookup Fields

**2.1 Add Video Title Lookup:**
1. Add new field to Jobs table
2. Select **Lookup**
3. Choose **Related Video** as source field
4. Select **Description** as lookup field
5. Name: `Video Title`

**2.2 Add Segment Text Lookup:**
1. Add new field to Jobs table
2. Select **Lookup**
3. Choose **Related Segment** as source field
4. Select **SRT Text** as lookup field
5. Name: `Segment Text`

### Step 3: Create Formula Fields

**3.1 Add Job Duration Calculator:**
1. Add new field to Jobs table
2. Select **Formula**
3. Name: `Duration (Minutes)`
4. Formula: 
```
IF(
  AND({Created Time}, {Last Modified}),
  ROUND(
    DATETIME_DIFF({Last Modified}, {Created Time}, 'minutes'),
    2
  ),
  ""
)
```

**3.2 Add Job Summary Field:**
1. Add new field to Jobs table
2. Select **Formula**
3. Name: `Job Summary`
4. Formula:
```
CONCATENATE(
  {Type}, 
  " - ", 
  {Status},
  IF({Video Title}, " (" & {Video Title} & ")", ""),
  IF({External Job ID}, " [" & {External Job ID} & "]", "")
)
```

## 📋 Recommended Views

### Jobs Table Views

**1. Active Jobs View:**
- Filter: `Status` is not "completed" and not "failed"
- Sort: `Created Time` (newest first)
- Fields: Job Summary, Status, Type, Duration, Created Time

**2. Failed Jobs View:**
- Filter: `Status` is "failed"
- Sort: `Last Modified` (newest first)
- Fields: Job Summary, Error Details, Video Title, Segment Text

**3. Completed Jobs View:**
- Filter: `Status` is "completed"
- Sort: `Last Modified` (newest first)
- Fields: Job Summary, Duration, Video Title, Type

**4. By Video View:**
- Group by: `Related Video`
- Sort: `Created Time` (newest first)
- Fields: Type, Status, Duration, Segment Text

### Videos Table Views

**1. Production Status View:**
- Sort: `Last Modified` (newest first)
- Fields: Description, Status, # Segments, Created Time
- Color code by Status field

**2. Completed Videos View:**
- Filter: `Final Video` is not empty
- Sort: `Last Modified` (newest first)
- Fields: Description, Final Video, Music, Created Time

### Segments Table Views

**1. By Video View:**
- Group by: `Video`
- Sort: `SRT Segment ID` (ascending)
- Fields: SRT Text, Video (attachment), Voiceover, Combined

**2. Processing Status View:**
- Color code by processing status
- Fields: Video, SRT Segment ID, SRT Text, Video status, Voiceover status

## 🎨 Field Formatting Recommendations

### Status Field Colors
Configure single select field colors:
- **pending**: Gray
- **processing**: Yellow  
- **completed**: Green
- **failed**: Red
- **cancelled**: Light gray

### Job Type Colors
- **voiceover_generation**: Blue
- **media_combination**: Purple
- **video_concatenation**: Orange
- **music_generation**: Pink
- **music_addition**: Teal

## 🔄 Workflow Integration

### Automated Field Updates
The system will automatically populate:
- `Related Video` and `Related Segment` when jobs are created
- `External Job ID` when external services respond
- `Status` as jobs progress through their lifecycle
- `Response Payload` when webhooks are received

## 📊 Dashboard Setup (Optional)

Create a dashboard with these blocks:

**1. Job Status Summary:**
- Chart type: Donut
- Table: Jobs
- Field: Status
- Shows distribution of job statuses

**2. Jobs by Type:**
- Chart type: Bar
- Table: Jobs  
- Field: Type
- Shows volume by job type

**3. Recent Activity:**
- Chart type: Timeline
- Table: Jobs
- Shows recent job activity

**4. Error Rate:**
- Chart type: Number
- Table: Jobs
- Calculation: Count of failed jobs / total jobs

## ✅ Validation Checklist

After configuration, verify:
- [ ] Jobs table has `Related Video` and `Related Segment` linked fields
- [ ] Lookup fields show correct data from linked records
- [ ] Formula fields calculate properly
- [ ] Views filter and sort correctly
- [ ] Status colors display properly
- [ ] Dashboard blocks show accurate data

## 🚨 Important Notes

1. **Field Dependencies**: Don't delete existing fields as they're used by the API
2. **Naming Convention**: Keep field names consistent with API expectations
3. **Data Types**: Maintain correct field types to prevent API errors
4. **Backup**: Export base before making major changes
5. **Testing**: Test with sample data before production use

## 📞 Support

If you encounter issues:
1. Check field types match requirements
2. Verify linked record connections
3. Test formulas with sample data
4. Contact support with specific error messages

---
*This configuration enables comprehensive job tracking and project management through the Airtable interface.*
