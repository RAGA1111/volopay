# Revenue Intelligence Inbox

**A lightweight revenue-intelligence workbench for sales managers and growth associates**

Converts sales call and meeting records into a prioritized, actionable work queue with explainable routing, reliable data reconciliation, and full audit trail.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Data Schema](#data-schema)
- [Routing Logic](#routing-logic)
- [Import & Reconciliation](#import--reconciliation)
- [Manual Corrections](#manual-corrections)
- [Exports & Manifest](#exports--manifest)
- [Testing](#testing)
- [Known Limitations](#known-limitations)
- [Deployment](#deployment)

---

## Overview

The Revenue Intelligence Inbox helps sales managers quickly answer:
- **What conversations need attention?**
- **Why do they matter?**
- **What should happen next?**

This is a **lean MVP** focused on:
- ✅ Reliable imports with duplicate detection
- ✅ Explainable routing with source evidence
- ✅ Manual corrections that persist across re-imports
- ✅ Clean exports with manifest validation
- ✅ Full audit trail for all changes

**Not a full CRM or advanced AI analytics system** - intentionally scoped for core workflow.

---

## Key Features

### 1. Smart Import Pipeline
- Upload CSV or JSON files
- Automatic column name normalization
- Validation with detailed error reporting
- Preview before commit
- **Reconciliation**: New, unchanged, updated, duplicate, conflict detection
- Stable identity matching to prevent duplicates

### 2. Explainable Routing
Every conversation is analyzed and assigned:
- **Category**: buying_signal, objection_blocker, customer_risk, product_feedback, routine, needs_review
- **Priority**: high, medium, low, needs_review
- **Evidence**: Specific content that supports the classification
- **Rationale**: Clear explanation of the decision
- **Next Action**: Recommended follow-up step

### 3. Manual Corrections with Audit Trail
- Override automated classifications
- Corrections preserved across re-imports
- Full history of changes with timestamps and reasons
- Conflict detection when source data changes

### 4. Overview Dashboard
- Unique conversation count
- Priority distribution (visual charts)
- Activity by type, owner, and date
- Import health monitoring

### 5. Verified Exports
- Export to CSV or JSON
- Apply filters before export
- **Manifest file** with:
  - Row counts and checksums
  - Schema documentation
  - Filter information
  - Verification results

---

## Test Data Files

Two CSV files are included for testing:

### `sample_data.csv`
15 simple example conversations covering all routing categories. Good for a quick first test.

### `volopay-conversation-records.csv` ⭐ Real Data
34 real-world SpendNest sales conversations from a single day (August 21, 2026), including:

| Group | Records | Description |
|-------|---------|-------------|
| B01–B20 | 20 calls | Short calls — voicemails and unresponsive (no transcript) |
| C01–C10 | 10 calls | Full transcript calls — mix of outcomes |
| M01–M14 | 14 meetings | Full meeting transcripts including partner, customer, and internal sessions |

**Column mapping (auto-detected by the app):**

| CSV Column | Maps To | Notes |
|------------|---------|-------|
| `source_id` | `source_id` | UUID — guarantees no duplicates on re-import |
| `conversation_date` | `conversation_date` | ISO 8601 format |
| `owner_name` | `owner` | Arun, Leela, Meera, Kiran, Dev |
| `title` | `topic` | Short label per record |
| `conversation_text` | `transcript` | Full text for routing analysis |
| `outcome` | `status` | voicemail, follow_up, referred, uninterested, etc. |
| `source_type` | `conversation_type` | call / meeting |

**Expected routing results after import:**

| Record | Expected Category | Expected Priority | Reason |
|--------|------------------|------------------|--------|
| M01 | buying_signal | high | "let us get the partner onboarding started" |
| C08 | buying_signal | medium | Referred to decision-maker, proposal requested |
| C07 | buying_signal | medium | Partnership discussion, follow-up agreed |
| M03 | objection_blocker | medium | Pricing discrepancy raised by customer |
| M04 | objection_blocker | medium | Credit vs prepaid blocker identified |
| M07 | customer_risk | high | Multiple product bugs reported live |
| M09 | customer_risk | high | Login broken, token expired on fresh link |
| C01 | routine | low | Explicitly uninterested, cold call |
| C06 | routine | low | Already automated, no need |
| B01–B20 | needs_review | needs_review | No transcript available |

---

## Quick Start

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Installation

1. **Clone or download this repository**

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Run the application:**
```bash
streamlit run app.py
```

4. **Access the app:**
   - The app will open automatically in your browser
   - Default URL: `http://localhost:8501`

### First Steps

1. **Import Data**
   - Navigate to "Import Data" page
   - Upload `volopay-conversation-records.csv` (34 real conversations) or `sample_data.csv` (15 simple examples)
   - Preview and validate — all 34 records should pass
   - Commit the import — routing runs automatically

2. **View Dashboard**
   - Go to "Overview" to see activity metrics
   - Review priority distribution and trends

3. **Process Inbox**
   - Visit "Inbox" to see prioritized conversations
   - Review routing rationale and evidence
   - Make manual corrections if needed

4. **Export Results**
   - Go to "Exports" to generate reports
   - Download CSV/JSON with manifest
   - Verify export integrity

---

## Architecture

### Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| UI Framework | Streamlit | Multi-page web application |
| Data Processing | Pandas | DataFrame operations and normalization |
| Database | SQLite | Persistence (conversations, analysis, audit) |
| Visualization | Plotly | Interactive charts and graphs |
| Language | Python 3.8+ | Core logic and business rules |

### Project Structure

```
revenue-intelligence-inbox/
├── app.py                      # Main entry point
├── pages/
│   ├── 1_Overview.py          # Dashboard with metrics
│   ├── 2_Inbox.py             # Conversation queue and detail
│   ├── 3_Import_Data.py       # Upload and reconciliation
│   └── 4_Exports.py           # Export generation
├── src/
│   ├── database.py            # SQLite schema and queries
│   ├── readers.py             # CSV/JSON parsing and normalization
│   ├── validation.py          # Record validation
│   ├── reconciliation.py      # Duplicate detection and merge logic
│   ├── routing.py             # Classification and priority rules
│   ├── corrections.py         # Manual override management
│   ├── metrics.py             # Dashboard calculations
│   └── exports.py             # Export and manifest generation
├── tests/
│   ├── test_imports.py        # Import pipeline tests
│   ├── test_routing.py        # Classification tests
│   ├── test_exports.py        # Export verification tests
│   └── run_all_tests.py       # Test suite runner
├── exports/                    # Generated export files
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Data Schema

### Database Tables

#### conversations
Primary table for all conversation records.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Internal primary key |
| source_id | TEXT | Unique identifier from source system |
| source_type | TEXT | File type (csv, json) |
| source_hash | TEXT | Content hash for change detection |
| source_payload | TEXT | Original JSON data |
| conversation_date | TEXT | Date/time of conversation |
| conversation_type | TEXT | Type (call, meeting, etc.) |
| owner | TEXT | Sales rep or owner |
| account_name | TEXT | Customer account name |
| contact_name | TEXT | Contact person |
| duration_minutes | INTEGER | Conversation length |
| topic | TEXT | Conversation topic/subject |
| transcript | TEXT | Full transcript if available |
| notes | TEXT | Summary notes |
| status | TEXT | Current status |
| created_at | TEXT | Record creation timestamp |
| updated_at | TEXT | Last update timestamp |
| source_updated_at | TEXT | Last source change timestamp |

#### analysis_results
Routing and classification results.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| conversation_id | INTEGER | FK to conversations |
| category | TEXT | Classification category |
| priority | TEXT | Priority level |
| rationale | TEXT | Explanation for classification |
| evidence | TEXT | Supporting content excerpt |
| next_action | TEXT | Recommended next step |
| review_status | TEXT | pending/completed |
| rule_version | TEXT | Routing logic version |
| created_at | TEXT | Analysis timestamp |
| updated_at | TEXT | Last update |

#### manual_overrides
User corrections with audit trail.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| conversation_id | INTEGER | FK to conversations |
| field_name | TEXT | Field being overridden |
| override_value | TEXT | New value |
| source_value_at_override | TEXT | Original value when override applied |
| reason | TEXT | User explanation |
| timestamp | TEXT | Override timestamp |
| active | INTEGER | 1 if currently active |

#### import_batches
Import operation tracking.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Batch primary key |
| filename | TEXT | Source filename |
| file_hash | TEXT | File content hash |
| timestamp | TEXT | Import timestamp |
| status | TEXT | success/failed/pending |
| total_rows | INTEGER | Total records in file |
| new_count | INTEGER | New records inserted |
| unchanged_count | INTEGER | Unchanged records |
| updated_count | INTEGER | Updated records |
| duplicate_count | INTEGER | Duplicates detected |
| invalid_count | INTEGER | Invalid records |
| conflict_count | INTEGER | Conflicts with overrides |
| error_message | TEXT | Error details if failed |

#### audit_log
Comprehensive change tracking.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Log entry ID |
| entity_type | TEXT | Type of entity changed |
| entity_id | INTEGER | ID of entity |
| action | TEXT | Action performed |
| field_name | TEXT | Field changed |
| old_value | TEXT | Previous value |
| new_value | TEXT | New value |
| reason | TEXT | Change reason |
| timestamp | TEXT | Change timestamp |
| batch_id | INTEGER | Associated import batch |

### Column Name Normalization

The system automatically normalizes common variations:

| Target Field | Source Variations |
|-------------|-------------------|
| source_id | source_id, conversation_id, id, call_id, meeting_id |
| conversation_date | date, timestamp, conversation_date, call_date |
| conversation_type | type, call_type, meeting_type |
| owner | owner, sales_rep, rep_name, assigned_to |
| account_name | account, company, company_name |
| contact_name | contact, contact_name, attendee |
| duration_minutes | duration, duration_minutes, length |
| topic | topic, subject, title |
| transcript | transcript, recording_transcript, call_transcript |
| notes | notes, summary, description |

---

## Routing Logic

### Categories

| Category | Evidence Patterns | Typical Priority |
|----------|------------------|-----------------|
| **buying_signal** | "interested in", "want to buy", "request demo/proposal", "ready to sign", "when can we start" | Medium-High |
| **objection_blocker** | "too expensive", "missing feature", "competitor", "concern", "procurement process" | Medium-High |
| **customer_risk** | "urgent", "critical", "escalate", "cancel", "unhappy", "deadline" | High |
| **product_feedback** | "feature request", "suggestion", "usability", "bug", "improvement" | Low-Medium |
| **routine** | "schedule", "thanks", "follow up", "introduction", "checking in" | Low |
| **needs_review** | Insufficient content or ambiguous patterns | Needs Review |

### Priority Levels

| Priority | Criteria |
|----------|----------|
| **High** | Customer risk, urgent buying signals, critical blockers |
| **Medium** | Active buying signals, unresolved objections, repeated feedback |
| **Low** | Routine conversations, standard workflow |
| **Needs Review** | Insufficient or conflicting evidence |

### Rationale & Evidence

Every classification includes:
- **Evidence**: Direct quote or excerpt from conversation content (30-60 characters context)
- **Rationale**: Human-readable explanation of why this category was chosen
- **Next Action**: Specific recommended follow-up step

**Example:**
```
Category: buying_signal
Priority: high
Evidence: "...urgently and want to sign the contract asap..."
Rationale: Detected expressed purchase intent. Time-sensitive buying signal.
Next Action: Assign to Alice Smith: Confirm next steps with sales owner and schedule follow-up.
```

### Guardrails

- ❌ No keyword-only classification - requires context
- ❌ No fabricated values - displays "unknown" if field missing
- ❌ No invented dates - only shows if available in source
- ✅ Ambiguous content flagged for human review
- ✅ Every classification shows source evidence
- ✅ Transparent rule version tracking

---

## Import & Reconciliation

### Import Workflow

1. **Upload**: CSV or JSON file
2. **Normalize**: Column name mapping
3. **Validate**: Check required fields, data types, content
4. **Preview**: Data quality report
5. **Reconcile**: Match against existing records
6. **Commit**: Apply changes in transaction
7. **Analyze**: Run routing rules on new/updated records

### Reconciliation Logic

When importing a file, each record is categorized as:

| Category | Meaning | Action |
|----------|---------|--------|
| **New** | source_id not in database | Insert new record |
| **Unchanged** | source_id exists, content hash identical | No action, increment counter |
| **Updated** | source_id exists, content changed | Update source fields, log change |
| **Conflict** | source_id exists, has active manual overrides | Update source but preserve overrides, flag for review |
| **Duplicate** | Multiple records with same source_id in batch | Keep first occurrence |
| **Invalid** | Missing required fields or validation errors | Reject, report errors |

### Identity Matching

**Priority 1: Stable source_id**
- Use provided `source_id`, `conversation_id`, or `id` field
- Convert to string for consistency

**Priority 2: Generated ID**
- If no ID field present, generate from:
  - conversation_date + owner + account + contact + topic
- Use MD5 hash of combined fields
- Document this strategy in import logs

### Testing Import Reliability

Run the test suite to verify:
```bash
python tests/test_imports.py
```

Tests cover:
- ✅ Same file imported twice → no duplicates
- ✅ Changed record → updates correctly
- ✅ Manual override → persists through re-import
- ✅ Invalid file → rejected cleanly
- ✅ Ambiguous identity → flagged for review

---

## Manual Corrections

### Editable Fields

Users can override these fields:
- `category` - Routing category
- `priority` - Priority level
- `review_status` - Review state
- `next_action` - Recommended action
- `status` - Conversation status
- `owner` - Assigned owner

### Override Workflow

1. Navigate to conversation in Inbox
2. Click "Edit Classification"
3. Select field and new value
4. Provide reason for override
5. Submit

### Conflict Policy

When source data is re-imported after a manual override:

1. **Source fields are updated** with new data
2. **Override remains active** on the overridden field
3. **Conflict is flagged** in reconciliation report
4. **Audit log records** both source change and override preservation

**Example:**
```
Initial: category = "routine" (from routing)
Override: category = "buying_signal" (manual, reason: "Sales manager insight")
Re-import: Source data changes but category stays "buying_signal"
Result: Conflict count = 1, override preserved, logged
```

### Audit Trail

All corrections are tracked:
- Timestamp
- Field changed
- Old value → New value
- Reason provided by user
- Active status

View history in conversation detail page.

---

## Exports & Manifest

### Export Options

- **Format**: CSV or JSON
- **Filters**: Priority, category, owner, status
- **Overrides**: Include indicator columns for overridden fields

### Manifest Contents

Every export includes a JSON manifest with:

```json
{
  "export_metadata": {
    "generated_at": "2026-10-23T10:30:00Z",
    "generator": "Revenue Intelligence Inbox v1.0.0",
    "export_type": "conversations_and_analysis"
  },
  "files": [
    {
      "filename": "conversations_20261023_103000.csv",
      "format": "csv",
      "row_count": 150,
      "file_size_bytes": 45230,
      "sha256_checksum": "a1b2c3..."
    }
  ],
  "data_summary": {
    "total_conversations_in_database": 200,
    "conversations_in_export": 150,
    "active_overrides_in_database": 12,
    "overrides_included": true
  },
  "filters_applied": {
    "priority": "high"
  },
  "schema_version": "1.0",
  "field_definitions": {
    "source_id": "Original identifier from source data",
    "category": "Routing category",
    ...
  },
  "verification": {
    "row_count_matches": true,
    "checksum_valid": true,
    "all_files_present": true
  }
}
```

### Verification

Use the manifest to verify export integrity:

```python
from src.exports import verify_export
from pathlib import Path

result = verify_export(Path('exports/manifest_20261023_103000.json'))
print(result['valid'])  # True if all checks pass
```

Checks performed:
- ✅ Files exist
- ✅ Row counts match
- ✅ Checksums match (no tampering)
- ✅ No data corruption

---

## Testing

### Run All Tests

```bash
python tests/run_all_tests.py
```

### Individual Test Modules

**Import & Reconciliation:**
```bash
python tests/test_imports.py
```

**Routing & Classification:**
```bash
python tests/test_routing.py
```

**Exports & Manifest:**
```bash
python tests/test_exports.py
```

### Test Coverage

✅ **Import Pipeline**
- Same file imported twice
- Changed record updates
- Manual override persistence
- Invalid file rejection
- Ambiguous identity handling

✅ **Routing Logic**
- Buying signal detection
- Objection/blocker classification
- Customer risk prioritization
- Product feedback capture
- Routine conversation handling
- Needs review flagging
- Evidence provision
- Priority escalation

✅ **Export System**
- File generation
- Manifest completeness
- Verification integrity
- Filtered export accuracy

---

## Known Limitations

### By Design (Lean MVP Scope)

❌ **No advanced AI/LLM summaries** - Uses deterministic rules for reliability
❌ **No automated CRM sync** - Manual export/import workflow
❌ **No revenue forecasting** - Requires deal values and stage history
❌ **No multi-user permissions** - Single deployment, trusted access
❌ **No real-time alerts** - Dashboard refresh required
❌ **No mobile optimization** - Desktop browser recommended

### Data Requirements

⚠️ **Requires meaningful content** - At least one of: transcript, notes, topic
⚠️ **Best with stable IDs** - Source system should provide unique conversation IDs
⚠️ **Date format flexible** - ISO format recommended but attempts to parse others

### Technical Constraints

⚠️ **SQLite for MVP** - Consider PostgreSQL for production at scale
⚠️ **In-memory processing** - Large files (>100K rows) may require chunking
⚠️ **Single-threaded** - Analysis runs sequentially per import

### Unsupported Metrics

The dashboard **does NOT show**:
- Revenue totals (no deal values in schema)
- Win rates (no outcome tracking)
- Conversion metrics (no funnel stages)
- Forecast predictions (no historical outcomes)

If source data doesn't contain a field, the UI displays "unknown" or "N/A" rather than making assumptions.

---

## Deployment

### 🚀 Quick Deploy to Streamlit Cloud (Recommended)

**Live in 5 minutes:**

1. **Push to GitHub**
2. **Connect Streamlit Cloud** (https://streamlit.io/cloud)
3. **Select repo** and set main file: `app.py`
4. **Deploy!**

**Detailed instructions:** See [DEPLOYMENT.md](DEPLOYMENT.md)

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py

# Access at: http://localhost:8501
```

### Production Hosting Options

| Platform | Best For | Free Tier | Setup Time |
|----------|----------|-----------|------------|
| **Streamlit Cloud** ⭐ | MVP demos, assignments | Yes | 5 minutes |
| **Heroku** | Production with persistence | Limited | 15 minutes |
| **Render** | Modern hosting | Yes | 10 minutes |
| **Railway** | Developer-friendly | $5 credit | 10 minutes |
| **AWS EC2** | Full control | Free tier | 30 minutes |

**Recommendation:** Use **Streamlit Cloud** for this assignment. Perfect for demos, zero configuration, and completely free.

### Deployment Checklist

- [ ] Code pushed to GitHub (public repo)
- [ ] Connected to Streamlit Cloud
- [ ] App deployed and accessible
- [ ] Tested in private browser
- [ ] Sample data imports successfully
- [ ] All pages load without errors
- [ ] Export downloads work
- [ ] Live URL added to slide deck
- [ ] Demo recorded with live app

### Database Persistence Note

⚠️ **Streamlit Cloud free tier:** SQLite database resets on app restart (by design).

**For this assignment:** This is actually ideal because:
- Reviewers can test import workflow from scratch
- Shows data reconciliation clearly
- No sensitive data persists

**For production:** Connect to PostgreSQL/MySQL (instructions in [DEPLOYMENT.md](DEPLOYMENT.md))

---

## FAQ

**Q: What if my CSV has different column names?**  
A: The system auto-maps common variations. Check "Detected Data Dictionary" during import.

**Q: Can I undo a manual override?**  
A: Yes, use the revert function in the override history section.

**Q: What happens if I import the same file twice?**  
A: Second import will show all records as "unchanged" with no duplicates created.

**Q: How do I customize routing rules?**  
A: Edit `src/routing.py` and update the pattern matching logic. Increment `RULE_VERSION`.

**Q: Can I export only high-priority conversations?**  
A: Yes, use the filter options on the Exports page before generating.

**Q: Is my data secure?**  
A: Data stays on your deployment. No external API calls. Use secure hosting and access controls.

---

## License

This project is provided as-is for evaluation purposes.

---

## Support

For questions or issues:
1. Check the [Known Limitations](#known-limitations) section
2. Review test files for usage examples
3. Inspect the code comments in `src/` modules

---

**Built with Python, Streamlit, Pandas, SQLite, and Plotly**  
**Version 1.0.0 | October 2026**
