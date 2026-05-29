# UI Plan

## Design Principles

1. **Local-first transparency** – File paths, versions, and data location always visible
2. **Approval-focused** – Users approve style rules before they're used
3. **Evidence-based** – Every generated rule shows source snippets from documents
4. **Progressive disclosure** – Show complexity only when needed
5. **Keyboard-friendly** – Power users can navigate with keyboard alone
6. **Minimal, no fluff** – No animations, no decorative elements (focus on content)

---

## Page Structure

```
/
├── Home (Profile Selector)
├── Profile Dashboard
│   ├── Documents
│   ├── Skills
│   └── Outputs
├── Document Upload & Extraction
├── Style Analyzer (Rule Review)
├── Skill Approval
├── Write / Rewrite
└── Settings
```

---

## 1. Home – Profile Selector

### Purpose
User selects or creates their profile.

### Layout
```
┌─────────────────────────────────────┐
│  Hermes Writer                      │
│  Local-First Writing Assistant      │
├─────────────────────────────────────┤
│                                     │
│  My Profiles:                       │
│  ┌─────────────────────────────┐   │
│  │ Muhammad                    │   │
│  │ Created: May 29, 2026       │   │
│  │ Skills: 2 | Documents: 5    │   │
│  │ [Select]                    │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─ New Profile ─────────────────┐ │
│  │ Profile ID: ________          │ │
│  │ Display Name: ________        │ │
│  │ [Create]                      │ │
│  └───────────────────────────────┘ │
│                                     │
└─────────────────────────────────────┘
```

### Interactions
- Click profile card → go to Profile Dashboard
- Click [Create] → validate inputs, create profile, redirect to Dashboard

---

## 2. Profile Dashboard

### Purpose
Overview of profile, documents, skills, and recent outputs.

### Layout
```
┌────────────────────────────────────────────────────┐
│ Muhammad                              [Settings]   │
│ Created: May 29, 2026                              │
├────────────────────────────────────────────────────┤
│                                                    │
│ Documents (5)                  Skills (2)          │
│ ┌──────────────┐               ┌──────────────┐   │
│ │ sample.pdf   │               │ Legal        │   │
│ │ Extracted    │               │ Draft v2     │   │
│ │ [Preview]    │               │ [Use] [Edit] │   │
│ └──────────────┘               │              │   │
│ [Upload New]                   └──────────────┘   │
│                                 [New Skill]       │
│                                                    │
├────────────────────────────────────────────────────┤
│ Recent Outputs (3)                                 │
│ ┌────────────────────────────────────────────┐    │
│ │ draft-001 | Write | May 29, 11:00 AM       │    │
│ │ Preview: "Dear Client, We appreciate..."   │    │
│ │ [View] [Export] [Delete]                   │    │
│ └────────────────────────────────────────────┘    │
│                                                    │
└────────────────────────────────────────────────────┘
```

### Components
- **Header:** Profile name, settings link
- **Documents Panel:** List of uploaded documents, extract status, preview button
- **Skills Panel:** List of approved skills, version, actions (Use, Edit, Delete)
- **Outputs Panel:** Recent generated/rewritten content with quick actions

---

## 3. Document Upload & Extraction

### Purpose
Upload files (PDF, DOCX, TXT) and preview extracted text.

### Layout (Multipart View)

#### Part A: Upload
```
┌────────────────────────────────────────┐
│ Upload Document                   [←]  │
├────────────────────────────────────────┤
│                                        │
│  ┌──────────────────────────────┐    │
│  │ Drag files here or           │    │
│  │ [Select Files]               │    │
│  │                              │    │
│  │ Supported: PDF, DOCX, TXT    │    │
│  │ Max size: 50 MB              │    │
│  └──────────────────────────────┘    │
│                                        │
│  Selected file:                        │
│  📄 sample.pdf (2.5 MB)               │
│  [Upload] [Cancel]                    │
│                                        │
└────────────────────────────────────────┘
```

#### Part B: Extraction Status
```
┌────────────────────────────────────────┐
│ Extracting...                     [←]  │
├────────────────────────────────────────┤
│                                        │
│  Processing: sample.pdf                │
│  ████████░░░░ 60%                      │
│  Estimated: 10 seconds                 │
│                                        │
│  [Cancel]                              │
│                                        │
└────────────────────────────────────────┘
```

#### Part C: Preview & Approve
```
┌────────────────────────────────────────┐
│ sample.pdf (Extracted)            [←]  │
├────────────────────────────────────────┤
│                                        │
│ Word Count: 1,250 | Chars: 8,500      │
│                                        │
│ ┌──────────────────────────────┐     │
│ │ Text Preview (Read-only)     │     │
│ │                              │     │
│ │ Dear Client, we appreciate   │     │
│ │ your business and want to    │     │
│ │ ensure...                    │     │
│ │                              │     │
│ │ [Scroll]                     │     │
│ └──────────────────────────────┘     │
│                                        │
│ [ ] Edit text manually                 │
│ (Click to unlock editing)              │
│                                        │
│ [Done] [Discard] [Upload Another]     │
│                                        │
└────────────────────────────────────────┘
```

### Interactions
- Drag files → auto-upload
- Upload progress shown in real-time
- After extraction: show preview, allow manual text edits
- [Done] → add document to profile, return to Dashboard
- [Upload Another] → return to Part A

---

## 4. Style Analyzer – Rule Review

### Purpose
User reviews LLM-extracted style rules and approves/rejects them.

### Layout (Multi-Step)

#### Step 1: Analysis in Progress
```
┌────────────────────────────────────────┐
│ Analyzing Style...                [←]  │
├────────────────────────────────────────┤
│                                        │
│ Documents: sample.pdf, email.txt       │
│ ████████████░░░░░░░ 40%                │
│ Estimated: 30 seconds                  │
│                                        │
│ [Cancel]                               │
│                                        │
└────────────────────────────────────────┘
```

#### Step 2: Rule Review
```
┌──────────────────────────────────────────────┐
│ Approve Style Rules                      [←] │
├──────────────────────────────────────────────┤
│                                              │
│ New Skill: "Muhammad Legal Drafting"         │
│ Proposed: 18 rules | From: 2 documents       │
│                                              │
│ ┌─ Rule 1: Tone (90% confidence) ──────────┐ │
│ │ [✓] ☐ Approve  ☐ Reject  [✎ Edit]       │ │
│ │                                           │ │
│ │ Use professional but approachable tone    │ │
│ │                                           │ │
│ │ ✓ Good: "We appreciate your business"    │ │
│ │ ✗ Bad: "You must comply immediately"     │ │
│ │                                           │ │
│ │ Evidence (2 snippets):                    │ │
│ │ • "We appreciate your business and..."   │ │
│ │ • "Thank you for your continued trust..." │ │
│ │                                           │ │
│ └───────────────────────────────────────────┘ │
│                                              │
│ ┌─ Rule 2: Structure (85% confidence) ────┐ │
│ │ ☐ Approve  ☐ Reject  [✎ Edit]           │ │
│ │                                           │ │
│ │ Always include greeting and closing       │ │
│ │                                           │ │
│ │ ✓ Good: "Dear Client, ... Best regards"  │ │
│ │ ✗ Bad: "Here's the content..."           │ │
│ │                                           │ │
│ │ Evidence (1 snippet):                     │ │
│ │ • "Dear Muhammad, We value..."            │ │
│ │                                           │ │
│ └───────────────────────────────────────────┘ │
│                                              │
│ [Approve All] [Add Custom Rule] [Next]      │
│                                              │
└──────────────────────────────────────────────┘
```

### Interactions
- Scroll through all rules
- [✓] checkbox → approve rule
- ☐ checkbox → mark for review
- [✎ Edit] → open edit modal to tweak description/examples
- [Add Custom Rule] → modal to add manual rule
- [Approve All] → shortcut for power users
- [Next] → go to Skill Approval

---

## 5. Skill Approval

### Purpose
Final confirmation and skill creation.

### Layout
```
┌──────────────────────────────────────────────┐
│ Confirm Skill                            [←] │
├──────────────────────────────────────────────┤
│                                              │
│ Skill Name: Muhammad Legal Drafting          │
│ Description: (optional)                      │
│                                              │
│ Approved Rules: 17                           │
│ Rejected Rules: 1                            │
│ Custom Rules Added: 0                        │
│                                              │
│ Files Stored At:                             │
│ data/profiles/muhammad/skills/               │
│   legal-drafting/skill.json                  │
│ data/profiles/muhammad/skills/               │
│   legal-drafting/audit.jsonl                 │
│                                              │
│ This skill will be:                          │
│ ✓ Saved locally (no cloud upload)            │
│ ✓ Version 1 (rollback available)             │
│ ✓ Ready to use for write/rewrite             │
│                                              │
│ ┌──────────────────────────────┐             │
│ │ View Full Skill JSON         │             │
│ │ (for advanced users)         │             │
│ └──────────────────────────────┘             │
│                                              │
│ [Create Skill] [Cancel] [Back]               │
│                                              │
└──────────────────────────────────────────────┘
```

### Interactions
- [View Full Skill JSON] → expand to show raw JSON
- [Create Skill] → save skill, go to Dashboard
- [Back] → return to rule review

---

## 6. Write / Rewrite

### Purpose
Generate new content or apply style to existing text.

### Layout (Tab: Write)

```
┌──────────────────────────────────────────────┐
│ [Write] [Rewrite]                        [←] │
├──────────────────────────────────────────────┤
│                                              │
│ Skill: [Select Skill ▼]                      │
│         Legal Drafting v2                    │
│                                              │
│ Prompt:                                      │
│ ┌──────────────────────────────────────────┐ │
│ │ Draft a thank you letter to a client    │ │
│ │ for referring new business.             │ │
│ │                                          │ │
│ │ (max 500 chars)                          │ │
│ └──────────────────────────────────────────┘ │
│ 87 / 500                                     │
│                                              │
│ Context (optional):                          │
│ ┌──────────────────────────────────────────┐ │
│ │ Referral was John Smith, met at         │ │
│ │ conference in May.                       │ │
│ │                                          │ │
│ │ (max 200 chars)                          │ │
│ └──────────────────────────────────────────┘ │
│ 45 / 200                                     │
│                                              │
│ Advanced Options [▼ Show]                    │
│   Temperature: [0.5 ⊙───⊙ 1.0]              │
│   Max Tokens: 500                            │
│                                              │
│ [Generate] [Clear]                           │
│                                              │
│ ─────────────────────────────────────────── │
│                                              │
│ Output:                                      │
│ ┌──────────────────────────────────────────┐ │
│ │ (empty)                                  │ │
│ │                                          │ │
│ │                                          │ │
│ └──────────────────────────────────────────┘ │
│                                              │
│ [Save] [Copy] [Discard]                      │
│                                              │
└──────────────────────────────────────────────┘
```

### Layout (Tab: Rewrite)

```
┌──────────────────────────────────────────────┐
│ [Write] [Rewrite]                        [←] │
├──────────────────────────────────────────────┤
│                                              │
│ Skill: [Select Skill ▼]                      │
│         Legal Drafting v2                    │
│                                              │
│ Original Text:                               │
│ ┌──────────────────────────────────────────┐ │
│ │ Hey John, thanks so much for sending   │ │
│ │ that client our way. Really helped us  │ │
│ │ close the deal!                         │ │
│ │                                          │ │
│ │ (max 5000 chars)                         │ │
│ └──────────────────────────────────────────┘ │
│ 105 / 5000                                   │
│                                              │
│ Instructions (optional):                     │
│ ┌──────────────────────────────────────────┐ │
│ │ Make it more formal and professional    │ │
│ └──────────────────────────────────────────┘ │
│                                              │
│ Advanced Options [▼ Show]                    │
│   Temperature: [0.3 ⊙─────⊙ 0.7]            │
│   Max Tokens: 300                            │
│                                              │
│ [Rewrite] [Clear]                            │
│                                              │
│ ─────────────────────────────────────────── │
│                                              │
│ Output (Rewritten):                          │
│ ┌──────────────────────────────────────────┐ │
│ │ (empty)                                  │ │
│ │                                          │ │
│ └──────────────────────────────────────────┘ │
│                                              │
│ [Side-by-Side Diff] [Copy] [Save] [Discard] │
│                                              │
└──────────────────────────────────────────────┘
```

### Interactions
- Select skill from dropdown
- Enter prompt/text
- Click [Generate] or [Rewrite]
- Show progress bar during generation
- Output appears in panel below
- [Copy] → copy to clipboard
- [Save] → save to outputs folder
- [Side-by-Side Diff] (rewrite only) → show original vs rewritten

---

## 7. Settings

### Purpose
Configure providers, privacy mode, storage location.

### Layout
```
┌────────────────────────────────────────┐
│ Settings                           [←] │
├────────────────────────────────────────┤
│                                        │
│ LLM Providers                          │
│                                        │
│ Privacy Mode:                          │
│ ☑ Ollama Only (Recommended)            │
│ ☐ Ollama + Fallback                    │
│ ☐ Cloud Only                           │
│                                        │
│ Available Providers:                   │
│ ✓ Ollama (Connected)                   │
│   Model: mistral-7b                    │
│   URL: http://localhost:11434          │
│   [Test Connection]                    │
│                                        │
│ ☐ Groq                                 │
│   API Key: ________________             │
│   [Save] [Test Connection]             │
│                                        │
│ ☐ Mistral                              │
│   API Key: ________________             │
│   [Save] [Test Connection]             │
│                                        │
│ Storage                                │
│ Location: ./data                       │
│ Used: 125 MB / 5000 MB                 │
│ ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    │
│                                        │
│ Backup & Export                        │
│ [Export All Data] [Backup Now]         │
│                                        │
│ About                                  │
│ Hermes Writer v1.0                     │
│ Local-First, Open Source                │
│                                        │
└────────────────────────────────────────┘
```

---

## Component Specs

### Rule Card
- **Title:** Rule category + confidence %
- **Description:** 1-2 sentence rule
- **Examples:** One positive, one negative (side-by-side)
- **Evidence:** 2-3 snippets from source documents
- **Actions:** Approve/Reject checkboxes, Edit button

### Skill Card
- **Title:** Skill name
- **Version:** Current version
- **Stats:** Rules count, creation date
- **Actions:** Use (generate), Edit, View Versions, Delete

### Output Card
- **Title:** Output ID + type (Write/Rewrite)
- **Preview:** First 100 chars of output
- **Metadata:** Skill used, date created
- **Actions:** View Full, Copy, Export, Delete

### Progress Indicator
- Animated progress bar
- Percentage + estimated time
- Animated dots (● ● ● cycling)
- Cancel button

---

## Navigation

### Global Header
- Profile name (top left)
- Active page title (center)
- Settings link (top right)
- Back button (contextual)

### Breadcrumbs
Not needed initially (only 2-3 levels deep)

### Keyboard Shortcuts (Optional Phase 2)
- `Ctrl+K` → Command palette (jump to page)
- `Ctrl+S` → Save output
- `Escape` → Close modal/go back
- `Enter` → Submit form

---

## Responsive Design

### Breakpoints
- **Desktop:** 1024px+ (full layout)
- **Tablet:** 768px-1023px (single-column, adjusted panels)
- **Mobile:** <768px (stacked layout, careful with large text areas)

**Note:** Phase 1 optimizes for Desktop. Tablet/Mobile in Phase 2 if needed.

---

## Accessibility (WCAG 2.1 AA)

- All form inputs labeled
- Focus indicators visible
- Color not sole indicator (use icons + text)
- Min contrast ratio 4.5:1
- Screen reader support for dynamic content
- Keyboard-only navigation possible

---

## Error States

### Network Error
```
┌─────────────────────────────────┐
│ ⚠ Connection Lost              │
│                                 │
│ Could not reach backend server. │
│ Retrying in 5s...               │
│ [Retry Now] [Offline Mode]      │
└─────────────────────────────────┘
```

### Validation Error
```
Field: Skill Name
Error: ⚠ Skill name already exists
Help: Choose a unique name like "Legal Drafting v2"
```

### File Upload Error
```
┌─────────────────────────────────┐
│ ❌ Upload Failed                │
│                                 │
│ sample.pdf (5.2 MB)             │
│ Reason: File size exceeds 50 MB │
│ [Try Again] [Upload Different]  │
└─────────────────────────────────┘
```
