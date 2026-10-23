# Quick Start Guide

Get the Revenue Intelligence Inbox running in 5 minutes.

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

**Required packages:**
- streamlit (UI framework)
- pandas (data processing)
- plotly (visualizations)
- python-dateutil (date parsing)

## Step 2: Launch the Application

```bash
streamlit run app.py
```

The app will automatically open in your browser at `http://localhost:8501`

## Step 3: Import Sample Data

1. Click **"Import Data"** in the sidebar
2. Upload the provided `sample_data.csv` file
3. Review the detected schema and preview
4. Click **"Continue to Validation"**
5. Check validation results (should be all valid)
6. Click **"Continue to Preview"**
7. Review reconciliation (15 new records)
8. Click **"Commit Import"**
9. Wait for analysis to complete

**Expected Result:** 15 conversations imported and analyzed

## Step 4: Explore the Dashboard

1. Click **"Overview"** in the sidebar
2. View key metrics:
   - Total Conversations: 15
   - High Priority: 2-3
   - Priority Distribution chart
   - Activity by Type
   - Category Distribution

## Step 5: Process the Inbox

1. Click **"Inbox"** in the sidebar
2. Filter by priority: **"high"**
3. Select a high-priority conversation
4. Review:
   - Classification category
   - Evidence (quoted content)
   - Rationale (explanation)
   - Recommended next action

## Step 6: Make a Manual Correction

1. In the Inbox, select any conversation
2. Scroll to **"Manual Correction"** section
3. Click **"Edit Classification"**
4. Change priority to "low"
5. Enter reason: "Sales manager override"
6. Click **"Apply Override"**
7. Notice the change is immediate

## Step 7: Re-import Same File

1. Go back to **"Import Data"**
2. Upload `sample_data.csv` again
3. Proceed through validation and reconciliation
4. Notice: **0 new, 15 unchanged** (no duplicates!)
5. Your manual override from Step 6 should still be active

## Step 8: Generate Export

1. Click **"Exports"** in the sidebar
2. Select format: **CSV**
3. Apply filter: Priority = **"high"**
4. Click **"Generate Export"**
5. Download both the CSV and manifest
6. Open the manifest JSON to see metadata

## Step 9: Run Tests

Verify everything works correctly:

```bash
python tests/run_all_tests.py
```

**Expected:** All tests pass ✅

## Step 10: Explore Features

### Dashboard Filters
- Filter by owner, date range
- View activity trends over time

### Inbox Search
- Search by account name or contact
- Filter by category, priority, status
- Sort conversations

### Routing Examples

Check these conversations in the sample data:

| ID | Expected Category | Expected Priority |
|----|------------------|------------------|
| CONV-001 | buying_signal | medium-high |
| CONV-002 | objection_blocker | medium |
| CONV-004 | customer_risk | high |
| CONV-005 | product_feedback | low-medium |
| CONV-003 | routine | low |

Each should have:
- ✅ Clear evidence quote
- ✅ Explainable rationale
- ✅ Recommended next action

---

## Troubleshooting

**App won't start:**
```bash
# Check Python version (need 3.8+)
python --version

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

**Import fails:**
- Verify CSV file is not empty
- Check that file has required columns (or will be normalized)
- Review validation error messages

**Database issues:**
- Delete `revenue_intelligence.db` file to reset
- Restart the application

**Port already in use:**
```bash
streamlit run app.py --server.port 8502
```

---

## Next Steps

1. **Import Your Own Data**
   - Prepare CSV/JSON with conversation records
   - Required: at least source_id and some content (transcript/notes)
   - Upload and let the system normalize columns

2. **Customize Routing Rules**
   - Edit `src/routing.py`
   - Add new patterns for your business
   - Update `RULE_VERSION` constant

3. **Review Documentation**
   - Read full `README.md` for detailed info
   - Check routing logic section
   - Understand reconciliation behavior

4. **Deploy to Production**
   - Follow deployment guide in README
   - Choose hosting platform (Streamlit Cloud, Heroku, AWS, etc.)
   - Configure persistent storage

---

## Sample Data Details

The included `sample_data.csv` contains 15 realistic conversations covering:

- 🟢 **3 Buying Signals** (interested customers, proposal requests)
- 🟡 **4 Objections/Blockers** (price concerns, technical barriers)
- 🔴 **2 Customer Risks** (urgent issues, retention concerns)
- 💡 **2 Product Feedback** (feature requests, usability issues)
- 📋 **4 Routine** (check-ins, quick questions)

Perfect for testing the routing logic and exploring the application!

---

**Ready to process real revenue intelligence? Import your sales call data and let's go! 🚀**
