# Demo Script - 3-Minute Walkthrough

Use this script for your recorded demo or live presentation.

---

## Preparation (Before Recording)

1. **Open your deployed app** in a clean browser window
2. **Close all other tabs** for clean recording
3. **Have sample_data.csv downloaded** and ready
4. **Test your microphone** - clear audio is critical
5. **Full screen the app** - hide bookmarks bar
6. **Start with empty app** - shows the full workflow

---

## Script: 3-Minute Demo

### 0:00 - 0:25 | Opening & Overview (25 seconds)

**Say:**
> "Hi, I'm [Your Name]. This is the Revenue Intelligence Inbox - a lightweight tool that helps sales managers prioritize which conversations need attention and why.
>
> The problem: Sales teams have hundreds of calls and meetings, but limited time. Which conversations should they focus on first?
>
> This tool automatically imports conversation records, analyzes them, and creates a prioritized work queue with explainable reasoning."

**Show:**
- Landing page of the app
- Point to the 4 main sections in sidebar

**Click:** Overview (to show dashboard)

---

### 0:25 - 1:05 | Inbox & Evidence-Based Routing (40 seconds)

**Say:**
> "Let me show you the inbox. Notice each conversation has a category, priority, and most importantly - evidence and rationale.
>
> For example, this high-priority conversation was classified as a 'buying signal' because the customer explicitly mentioned wanting to purchase and requested a proposal. You can see the exact quote from their conversation right here.
>
> The next action is specific: 'Assign to Alice Smith - confirm next steps and schedule follow-up.'
>
> Everything is explainable with source evidence. No black-box AI making decisions you can't trust."

**Show:**
- Overview dashboard with metrics
- Click to Inbox
- Filter by "high" priority
- Select a buying signal conversation
- Point to the evidence quote
- Point to rationale
- Point to next action
- Scroll to show the actual transcript

---

### 1:05 - 1:40 | Difficult Routing Decision (35 seconds)

**Say:**
> "Here's an interesting case - this conversation mentioned pricing concerns and competitor evaluation. The system detected this as an 'objection_blocker' with medium priority.
>
> But look at this one - ambiguous content with no clear buying signals or concerns. Instead of guessing, the system flags it as 'needs_review' for human verification.
>
> This is important: when evidence is insufficient, we don't pretend to know. We route it to a human for proper classification."

**Show:**
- Filter by category: "objection_blocker"
- Select the pricing objection conversation
- Show evidence: "price is too expensive"
- Then show a "needs_review" conversation
- Explain why it needs human review

---

### 1:40 - 2:30 | Import Workflow & Data Reliability (50 seconds)

**Say:**
> "Now let me demonstrate the import workflow and data reliability - this is critical.
>
> I'll import our sample conversation data. The system validates the records, checks for issues, and then reconciles them against the existing database.
>
> Watch what happens: 15 new records imported and automatically analyzed.
>
> Now here's the test: I'll import the exact same file again. Notice: zero new records, 15 unchanged. No duplicates created. This is idempotent - you can safely re-import the same data.
>
> If I make a manual correction here - changing this to low priority with a reason - and then re-import, my override persists. The system detects the conflict and preserves my human judgment."

**Show:**
- Click "Import Data"
- Upload sample_data.csv
- Show validation: 15 valid
- Show reconciliation: 15 new
- Click through to commit
- **Go back and upload same file again**
- Show reconciliation: 0 new, 15 unchanged
- Go to inbox, make a manual correction
- Mention that re-importing would preserve this

---

### 2:30 - 3:00 | Exports & Closing (30 seconds)

**Say:**
> "Finally, exports. The system generates CSV or JSON files with a verification manifest.
>
> This manifest includes row counts, checksums, and field definitions - everything you need to verify the data hasn't been tampered with.
>
> Every decision is traceable: from the source conversation, through the routing logic with evidence, to the final export.
>
> This is a lean MVP focused on reliability and transparency. It's not a full CRM, but it solves the core problem: helping sales managers quickly identify what needs attention and why.
>
> Thanks for watching. The app is live at [your URL] and the code is on GitHub."

**Show:**
- Click "Exports"
- Generate export (CSV, high priority filter)
- Show manifest structure briefly
- Return to overview dashboard
- Show your deployed URL on screen

---

## Recording Tips

### Audio Quality
✅ **Use a decent microphone** (laptop mic usually OK)
✅ **Record in quiet room** - no background noise
✅ **Speak clearly and steadily** - not too fast
✅ **Practice once before recording** for smooth delivery

### Visual Quality
✅ **1080p resolution minimum** (1920x1080)
✅ **Full screen the app** - no distractions
✅ **Smooth mouse movements** - not jerky
✅ **Cursor highlights key info** as you speak

### Content Quality
✅ **Stick to 3 minutes** ±15 seconds is OK
✅ **Show, don't just tell** - actually click through
✅ **Highlight key differentiators** - evidence, idempotency, transparency
✅ **End with your deployed URL visible**

---

## Software Recommendations

**Screen Recording:**
- **OBS Studio** (free, professional) - https://obsproject.com/
- **Loom** (easy, browser-based) - https://loom.com/
- **Windows Game Bar** (built-in) - Win+G
- **QuickTime** (Mac built-in) - Command+Control+N

**Editing (if needed):**
- **DaVinci Resolve** (free, powerful)
- **Loom** (auto-edits, adds captions)
- **Clipchamp** (Windows built-in)

**File Format:**
- MP4 (H.264 codec)
- 1080p resolution
- 30fps frame rate
- < 100MB file size

---

## Alternative: Shorter 90-Second Version

If you need a quick version:

**0:00-0:20** - Problem & solution overview
**0:20-0:50** - Show inbox with evidence-based routing
**0:50-1:20** - Import workflow and duplicate handling demo
**1:20-1:30** - Exports & closing with URL

---

## What NOT to Include

❌ Don't apologize for "limitations" - this is an intentional MVP
❌ Don't explain every technical detail - focus on business value
❌ Don't show bugs or errors - test thoroughly first
❌ Don't rush through - 3 minutes is plenty
❌ Don't forget to show your deployed URL at the end

---

## Practice Checklist

Before recording your final version:

- [ ] Practice the full script 2-3 times
- [ ] Time yourself (aim for 2:45-3:15)
- [ ] Test all clicks and transitions
- [ ] Verify sample data imports smoothly
- [ ] Rehearse your opening and closing
- [ ] Have your deployed URL ready to show
- [ ] Check that all text is readable on screen

---

## After Recording

1. **Watch it back** - check audio and video quality
2. **Test the file** - plays on different devices
3. **Add to your submission** - upload or link
4. **Share on LinkedIn** (optional) - "Just built and deployed..."
5. **Send to your portfolio** - great reference piece

---

## Key Messages to Convey

Throughout the demo, emphasize:

✅ **Reliability** - "No duplicates, idempotent imports"
✅ **Transparency** - "Every decision has evidence"
✅ **Practicality** - "Not a full CRM, solves one problem well"
✅ **Deployability** - "Live on Streamlit Cloud"
✅ **Testability** - "Comprehensive test suite"

These signal strong engineering and product thinking for a Growth Associate role.

---

## Demo URLs to Show

Make sure these are visible at some point:

**Your Live App:**
```
https://your-username-revenue-intelligence-inbox.streamlit.app
```

**Your GitHub:**
```
https://github.com/your-username/revenue-intelligence-inbox
```

**Sample Data:**
```
(Available in the GitHub repository)
```

---

## Timing Breakdown (Detailed)

| Time | Section | Key Points |
|------|---------|------------|
| 0:00-0:10 | Intro | Name, product name, problem |
| 0:10-0:25 | Value prop | Prioritized queue, explainable |
| 0:25-0:45 | Inbox demo | Show evidence and rationale |
| 0:45-1:05 | Routing example | Buying signal with quote |
| 1:05-1:25 | Difficult case | Needs review explanation |
| 1:25-1:40 | Transparency | Why it matters |
| 1:40-2:00 | First import | Upload and reconcile |
| 2:00-2:15 | Second import | No duplicates! |
| 2:15-2:30 | Manual override | Preserved on re-import |
| 2:30-2:45 | Exports | Manifest with checksums |
| 2:45-3:00 | Closing | Summary and URLs |

---

## Common Questions to Address

In your demo or slides, preemptively answer:

**"Why not use full AI?"**
→ "Deterministic rules are explainable and testable. Every decision is transparent."

**"What about duplicate conversations?"**
→ "Built-in reconciliation - same file imported twice creates zero duplicates."

**"Can users override the system?"**
→ "Yes, with full audit trail. Overrides persist across re-imports."

**"How do you verify exports?"**
→ "SHA256 checksums in manifest. Verification function included."

---

## You're Ready! 🎬

Follow this script, practice a few times, and you'll have a professional demo that showcases:
- Technical capability (built and deployed)
- Product thinking (focused MVP, explainable decisions)
- Data rigor (reconciliation, audit trail, verification)
- Business value (actionable insights for sales managers)

**Go record your demo and close out this assignment strong! 🚀**
