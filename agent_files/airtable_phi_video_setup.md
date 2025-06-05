# PHI Video Production Airtable MCP Setup

## Configuration Details
- **MCP Server Name:** `airtable-phi-video-prod`
- **Base ID:** `app1XR6KcYA8GleJd`
- **Segments Table ID:** `tblc86DDGKFh0adHu`
- **Setup Date:** May 23, 2025

## Available Operations
Through the `airtable-phi-video-prod` MCP server, Claude can:

### Base/Table Management
- `list_bases` - List all accessible Airtable bases
- `list_tables` - List all tables in the PHI Video base
- `create_table` - Create new tables
- `update_table` - Modify table schema

### Field Management  
- `create_field` - Add new fields to tables
- `update_field` - Modify existing field properties

### Record Operations
- `list_records` - Get records from any table
- `get_record` - Get specific record by ID
- `create_record` - Add new records
- `update_record` - Modify existing records
- `delete_record` - Remove records
- `search_records` - Find records by field values

## Usage Notes
- Always confirm with user before performing operations
- This is the third Airtable base (in addition to DAI Master System and HabitHacker)
- Personal Access Token configured for full base access
- Restart Claude Desktop required after initial setup

## Credentials Reference
- **PAT:** `patoVZshStmg110Jm.0dfaeac5c222b617903b5b2ed4c1942323baa3be2d742947eb2bcf7a97952440`
- **Base:** `app1XR6KcYA8GleJd` 
- **Segments Table:** `tblc86DDGKFh0adHu`
