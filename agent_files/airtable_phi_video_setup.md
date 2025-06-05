# Airtable Schema Notes - YouTube Video Engine

## Jobs Table
**Table ID:** `tblEjYfRwCztHOF5G`

### Key Fields
| Field Name | Field ID | Type | Description |
|------------|----------|------|-------------|
| Job ID | fldKSDMemREvpEwOi | Text | Single line of text |
| Type | fldLiddAGJ423Dqd7 | Single select | Job type (voiceover, combine, concatenate, music, final, ai_image, video_generation, Undefined, add_music_to_video) |
| Status | fldqxdYmcyYNL1PFz | Single select | Job status (pending, processing, completed, failed, Undefined, webhook_error, "processed") |
| Last Modified time | fldvEGptfsq4WB1r2 | Formula | LAST_MODIFIED_TIME() |
| External Job ID | fldhQ2Cs71olPMDe5 | Text | UUID for external tracking |
| Webhook URL | fld9zumnnhPI9vgwtURL | URL | Callback URL for job completion |
| Request Payload | fldY68OBABMwRknAr | Long text | JSON request data |
| Response Payload | fldcw5ZLqEtMonqbJ | Long text | JSON response data |
| Error Details | fldn2rhy5jhBVmIbP | Long text | Error information |
| Result | fld1FJoCERSaIe2cM | Long text | Job result data |
| Record ID | fldAbXu2kT3rfZj2n | Formula | RECORD_ID() |
| Segments | fldR39EIMMDtuY7Pu | Link to another record | Links to Segments table |
| SRT Text (from Segments) | fldio71WggETaAtVd | Lookup | Array from linked Segments |
| Status (from Segments) | fldMhU9cs57Lq86Lp | Lookup | Array from linked Segments |
| Related Video | flduFb1EvNaahcyXF | Link to another record | Links to Videos table |
| Description (from Related Video) | fldQDIdZaE0O8iHE0 | Lookup | Array from linked Videos |
| Notes | fldx0wiUcU79napoX | Long text | Additional notes |
| Error Message | fldGKH6CnrMGYqE0P | Long text | Error messages |

### Notes
- Table IDs and field IDs can be used interchangeably with names in API requests
- Using IDs prevents issues when names change
- Single select fields will fail if exact match not found unless typecast is enabled

## Segments Table
**Table ID:** `tblc86DDGKFh0adHu`

### Key Fields
| Field Name | Field ID | Type | Description |
|------------|----------|------|-------------|
| Segment ID | fldgqzV0U8F8Mqxkc | Auto Number | Automatically incremented unique counter |
| SRT Text | fldWf8rRBUon3ul2J | Long text | Multiple lines of text for SRT content |
| Random Notes | fldv454xxpFTmBgst | Long text | Additional notes |
| Status | fld13CH6qdwkjEvgO | Single select | (Ready, Generating Voiceover, Voiceover Ready, Voiceover Failed, Combining Media, Media Combined, combination_failed, Generating Image, Image Ready, Image Generation Failed, Generating Video, Video Ready, combined, Video Generation Failed, Combination Failed, Undefined) |
| Start Time | fldWzBYlbrPCw4fmH | Duration | Start time in seconds |
| End Time | fldKYmth6mbnop25J | Duration | End time in seconds |
| Duration | fldAp8VTTMzcxeOhb | Formula | CEILING({End Time} - {Start Time}) |
| Videos | fldL8a5eC107i49Cn | Link to another record | Links to Videos table |
| Voices | fldYhtnmg73duK9gw | Link to another record | Links to Voices table |
| Name (from Voices) | fldAqy8rVrOs0XFSv | Lookup | Voice name from linked Voices |
| Description (from Voices) | fld4aGBAodjNoAzVX | Lookup | Voice description from linked Voices |
| Speed (from Voices) | fldOglW2wIFXIIYrM | Lookup | Voice speed setting |
| Style Exaggeration (from Voices) | fldUyIpnuDFJoPBsy | Lookup | Voice style exaggeration |
| Speaker Boost (from Voices) | fldOfouNwmtzQsrC5 | Lookup | Voice speaker boost setting |
| Voiceover Go | fldECAlSOeYRi50h8 | Checkbox | Trigger for voiceover generation |
| Voiceover | fldkhZi1gQigBtCLg | Attachment | Audio file attachments |
| B-Roll | fldBrdYNY7ita5h2h | Checkbox | B-roll flag |
| Image Themes | fldrE6cED32l8PRdI | Link to another record | Links to Image Themes table |
| Image Theme Name (from Notes) | fldl8av2nFuocriNT | Lookup | Theme name from linked Image Themes |
| Description (from Notes) | fldwAi4MDyeW0zHaK | Lookup | Theme description from linked Image Themes |
| Examples (from Notes) | fldT7lFq0e6X8yAri | Lookup | Theme examples from linked Image Themes |
| AI Image Prompt | fld5mclyD9ZgmyUOv | Long text | Prompt for AI image generation |
| Image | fldLFBSDme87N1vXq | Attachment | Generated image attachments |
| Redo Image | fld4pExR5eBYCuobk | Checkbox | Flag to regenerate image |
| Select Image | fldUDl2UQSJYIo9Ko | Single select | Image selection (1, 2, 3, 4) |
| Upscale Image | fldwpxLKZzNiY7fn7 | Attachment | Upscaled image attachments |
| Video Style | fldc1G4Tmf3pMGILF | Single select | Video generation style (Kling Video, Zoom) |
| Video | fldZBXJEqEcJT7n8N | Attachment | Generated video attachments |
| Redo Video | fldwh7Uj2DOcFYeBQ | Checkbox | Flag to regenerate video |
| Combine VO + Vid | fld19DCXT7HWikHcS | Checkbox | Flag to combine voiceover and video |
| Voiceover + Video | fldmOgodOfRnrhyeY | Attachment | Combined audio/video attachments |
| Record ID | flddi3FOJUaj6TBRq | Formula | RECORD_ID() |
| Last Modified Time | fldfbQ59d3mVScaqJ | Formula | LAST_MODIFIED_TIME() |
| SRT Segment ID | fldSiFysie0mML3nn | Text | Segment identifier for SRT |
| SRT Segment | fldXxBCRkAtv36qvR | Long text | SRT segment content |
| Timestamps | fldctAiPmcqYIV7Fg | Text | SRT timestamp format |
| Video Script (from Videos) | fldQ1WRvGjKTX1SHJ | Lookup | Script from linked Videos |
| Active Video (from Videos) | fldnKBuaqtv0kVN7R | Lookup | Active flag from linked Videos |
| Width | fldo2JB62hZv994FY | Lookup | Video width from linked Videos |
| Height | fldOiCEWIipGia9XF | Lookup | Video height from linked Videos |
| Image ID | fldER146CCHSwoRBv | Text | External image identifier |
| Upscale ID | fldNl5j7fMWL8FUC9 | Text | External upscale identifier |
| Video ID | fldEdkdIG3WK6Rz0U | Text | External video identifier |
| Voices copy | fldSuO4S6L32GfnVi | Text | Voice backup field |
| Jobs | fldp2wajSIWvGPs7M | Link to another record | Links to Jobs table |

### Important Status Values for Segments
- **Ready**: Segment ready for processing
- **Generating Voiceover**: Audio generation in progress
- **Voiceover Ready**: Audio generation complete
- **Generating Image**: Image generation in progress
- **Image Ready**: Image generation complete
- **Generating Video**: Video generation in progress
- **Video Ready**: Video generation complete
- **Combined**: Audio and video combined
- **Failed states**: Various failure conditions

## Videos Table
**Table ID:** `tblQP6jkQ5od8aeUi`

### Key Fields
| Field Name | Field ID | Type | Description |
|------------|----------|------|-------------|
| Video ID | fld0y4ViPzNHDRrYk | Auto Number | Automatically incremented unique counter |
| Active Video | fldvwkk7NtIByA2sj | Checkbox | Marks video as active |
| Description | fldaIiL9yD1xf4N0D | Long text | Video description |
| Video Script | fld5TfVh7RoYcEf3Q | Long text | Full video script content |
| Width | fldKh2OiGKnTXUOSp | Number | Video width in pixels |
| Height | fldxoRBkLBxtKmuiM | Number | Video height in pixels |
| Video GO | fldno7g7OYN6wFxtr | Checkbox | Trigger video generation workflow |
| Voiceover GO | fldiyeXLn8Z9qvgjb | Checkbox | Trigger voiceover generation |
| Segmentation Go | fldBtCYqnvd1HqGuR | Checkbox | Trigger script segmentation |
| Voiceover + Video (from Segments) | fldu007Np3cVUZn3R | Lookup | Combined media from linked Segments |
| Combine Segments Go | fldtS97WeF1nYJqNw | Checkbox | Trigger segment combination |
| Combined Segments Video | fld2VogXX9tsDSZDg | Attachment | Final combined video file |
| Segmentation Go (VO) | fldT0REONTRK3vvKA | Checkbox | Trigger voiceover segmentation |
| Music Prompt | fld6W7YKG9yk1wquJ | Long text | Prompt for AI music generation |
| Generate Music Go | fldI2TKjokbchBVpm | Checkbox | Trigger music generation |
| Music | fldnqrf5o2aHwY9OM | Attachment | Generated music files |
| AI Music Task ID | fldo3BPxXEGN0283s | Text | External music generation task ID |
| Add Music to Video Go | fldma5zutzROoFzpi | Checkbox | Trigger music addition to video |
| Video + Music | flda4ZlNCeh6lh4r4 | Attachment | Video with background music |
| Video + Captions | fldSUPlABkZXKs0qG | Attachment | Video with captions overlay |
| Video SRT | fld5FWCcog9sB3vKT | URL | SRT subtitle file URL |
| Archive | fldEwzADv5eECvi7c | Checkbox | Archive flag |
| Record ID | fldbHoYZVIFCzaN0G | Formula | RECORD_ID() |
| Video + B-Roll Go | fld6C633dbX6hz7Pb | Checkbox | Trigger B-roll addition |
| Video + B-Roll | fld39ZeTEd4Jkq6d7 | Attachment | Video with B-roll footage |
| AI Video | fldd2W9bhwp8ykExz | Attachment | AI-generated video content |
| Segments | fldevfszbdpSYK6SR | Link to another record | Links to Segments table |
| Transcript URL | fldQuhi8qf1dVbEpz | URL | Transcript file URL |
| # Segments | fldMPj4qfzj4VFyfv | Count | Number of linked segments |
| Segments 2 | fldk1LiEXbkMte20e | Text | Additional segments reference |
| Jobs | fldWNjAlc59ka2Ey6 | Link to another record | Links to Jobs table |

### Video Generation Workflow Triggers
- **Video GO**: Main video generation trigger
- **Voiceover GO**: Generate voiceovers for segments
- **Segmentation Go**: Split script into segments
- **Segmentation Go (VO)**: Split script for voiceover processing
- **Combine Segments Go**: Combine all segment videos
- **Generate Music Go**: Generate background music
- **Add Music to Video Go**: Add music to final video
- **Video + B-Roll Go**: Add B-roll footage

### Key Output Files
- **Combined Segments Video**: Final assembled video
- **Video + Music**: Video with background music
- **Video + Captions**: Video with subtitle overlay
- **Video + B-Roll**: Video with B-roll footage
- **Music**: Generated background music
- **AI Video**: AI-generated video content
