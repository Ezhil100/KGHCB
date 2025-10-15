# Doctor Profile Icons - Feature Documentation

## 🎯 Overview

Each doctor listed in the chatbot now has a **clickable profile icon (👤)** that redirects to their individual profile page on the KG Hospital website.

## 🔗 URL Structure

**Pattern:** `https://www.kghospital.com/doctors/{specialty}/{doctor-slug}`

**Example:**

- Dr. Amirthalingam (General Surgeon) → `https://www.kghospital.com/doctors/general-surgeon/dr-amirthalingam`
- Dr. John Smith (Cardiologist) → `https://www.kghospital.com/doctors/cardiologist/dr-john-smith`

## 🎨 Visual Design

### Profile Icon Features:

- **Appearance:** Small circular button with 👤 emoji
- **Color:** Blue gradient (matches hospital branding)
- **Position:** Next to each doctor's name
- **Size:** 24x24 pixels
- **Hover Effect:** Scales up slightly with enhanced shadow
- **Tooltip:** "View doctor profile"

### Example Display:

```
Dr. John Smith [👤]
Dr. Sarah Johnson [👤]
Dr. Michael Brown [👤]
```

## 🛠️ Technical Implementation

### Backend (`main.py`)

**Function:** `add_actionable_elements()`

**Key Features:**

1. **Specialty Detection:** Automatically detects doctor specialties from context
2. **Name Conversion:** Converts doctor names to URL-friendly slugs
3. **Marker Format:** `[DOCTORPROFILE:Dr. Name|specialty-slug|dr-name-slug]`

**Specialty Mapping:**

```python
specialty_map = {
    'cardiologist': 'cardiologist',
    'neurologist': 'neurologist',
    'orthopedic': 'orthopedic-surgeon',
    'general surgeon': 'general-surgeon',
    'oncologist': 'oncologist',
    'gynecologist': 'gynecologist',
    'dermatologist': 'dermatologist',
    'ent': 'ent-specialist',
    'ophthalmologist': 'ophthalmologist',
    'psychiatrist': 'psychiatrist',
    'urologist': 'urologist',
    'gastroenterologist': 'gastroenterologist',
    'pulmonologist': 'pulmonologist',
    'endocrinologist': 'endocrinologist',
    'nephrologist': 'nephrologist',
    'anesthesiologist': 'anesthesiologist'
    # ... and more
}
```

**Algorithm:**

1. Parse text line by line
2. Detect specialty keywords to establish context
3. Find doctor name patterns
4. Extract specialty from inline text or use context
5. Convert names to URL slugs (lowercase, hyphenated, with "dr-" prefix)
6. Create marker with all components

**Example Transformation:**

```
Input: "Dr. John Smith - Cardiologist"
Output: "[DOCTORPROFILE:Dr. John Smith|cardiologist|dr-john-smith]"
```

### Frontend (`App.jsx`)

**Component:** `processActionableText()`

**Pattern Matching:**

```javascript
{
  regex: /\[DOCTORPROFILE:([^\|]+)\|([^\|]+)\|([^\]]+)\]/g,
  type: 'doctorprofile'
}
```

**Rendering:**

```jsx
<span style={{ display: "inline-flex", alignItems: "center", gap: "6px" }}>
  <span>{doctorName}</span>
  <a href={profileUrl}>👤 (profile icon)</a>
</span>
```

**URL Construction:**

```javascript
const doctorProfileUrl = `https://www.kghospital.com/doctors/${specialty}/${slug}`;
```

## 📋 Supported Specialties

| Specialty Keyword         | URL Slug             | Example                               |
| ------------------------- | -------------------- | ------------------------------------- |
| Cardiologist/Cardiology   | `cardiologist`       | `/doctors/cardiologist/dr-name`       |
| Neurologist/Neurology     | `neurologist`        | `/doctors/neurologist/dr-name`        |
| Orthopedic/Orthopedics    | `orthopedic-surgeon` | `/doctors/orthopedic-surgeon/dr-name` |
| General Surgeon/Surgery   | `general-surgeon`    | `/doctors/general-surgeon/dr-name`    |
| Oncologist/Oncology       | `oncologist`         | `/doctors/oncologist/dr-name`         |
| Gynecologist/Gynecology   | `gynecologist`       | `/doctors/gynecologist/dr-name`       |
| Dermatologist/Dermatology | `dermatologist`      | `/doctors/dermatologist/dr-name`      |
| ENT Specialist            | `ent-specialist`     | `/doctors/ent-specialist/dr-name`     |
| Ophthalmologist           | `ophthalmologist`    | `/doctors/ophthalmologist/dr-name`    |
| Psychiatrist/Psychiatry   | `psychiatrist`       | `/doctors/psychiatrist/dr-name`       |
| Urologist/Urology         | `urologist`          | `/doctors/urologist/dr-name`          |
| Gastroenterologist        | `gastroenterologist` | `/doctors/gastroenterologist/dr-name` |
| Pulmonologist/Pulmonology | `pulmonologist`      | `/doctors/pulmonologist/dr-name`      |
| Endocrinologist           | `endocrinologist`    | `/doctors/endocrinologist/dr-name`    |
| Nephrologist/Nephrology   | `nephrologist`       | `/doctors/nephrologist/dr-name`       |
| Anesthesiologist          | `anesthesiologist`   | `/doctors/anesthesiologist/dr-name`   |

## 🎯 Context Detection

The system uses **contextual specialty detection** to handle various response formats:

### Format 1: Inline Specialty

```
Dr. John Smith - Cardiologist
Dr. Sarah Johnson (Neurologist)
Dr. Michael Brown, Orthopedic Surgeon
```

### Format 2: Specialty Header

```
Cardiologists:
- Dr. John Smith
- Dr. Sarah Johnson

Neurologists:
- Dr. Michael Brown
```

### Format 3: Mixed

```
Our cardiology department has:
Dr. John Smith - Senior Cardiologist
Dr. Sarah Johnson
```

## 🚀 User Experience Flow

1. **User asks:** "Who are the cardiologists?"

2. **Bot responds:**

   ```
   Here are our cardiologists:
   - Dr. John Smith [👤]
   - Dr. Sarah Johnson [👤]
   - Dr. Michael Brown [👤]

   [For complete doctors list, visit our website →]
   ```

3. **User clicks profile icon** next to "Dr. John Smith"

4. **Opens:** `https://www.kghospital.com/doctors/cardiologist/dr-john-smith`

5. **User views:** Complete profile with qualifications, experience, schedule, etc.

## ✨ Features

### Profile Icon Benefits:

- ✅ **Direct Access:** One click to detailed doctor profile
- ✅ **Visual Clarity:** Clean, professional icon design
- ✅ **Non-Intrusive:** Doesn't clutter the doctor's name
- ✅ **Hover Feedback:** Clear interaction cues
- ✅ **Mobile Friendly:** Large enough to tap easily
- ✅ **Maintains Context:** Name remains readable, icon supplements

### Combined with Existing Features:

- **Multiple doctors (3+):** Shows profile icons + "complete list" button at bottom
- **Few doctors (1-2):** Shows profile icons only
- **No specialty detected:** Falls back to general doctors list

## 🧪 Testing Scenarios

### Test 1: Single Doctor

**Ask:** "Who is the head of cardiology?"

**Expected:**

```
Dr. John Smith is the head of cardiology. [👤]
```

**Test:** Click icon → Should open specific profile

---

### Test 2: Multiple Doctors with Specialty

**Ask:** "List all neurologists"

**Expected:**

```
Neurologists:
- Dr. Jane Doe [👤]
- Dr. Mark Wilson [👤]
- Dr. Emily Chen [👤]

[For complete doctors list, visit our website →]
```

**Test:**

- Click any profile icon → Opens specific doctor page
- Click bottom button → Opens general doctors list

---

### Test 3: Mixed Specialties

**Ask:** "Show me doctors in surgery and cardiology"

**Expected:**

```
Surgery:
- Dr. David Lee [👤]
- Dr. Anna Martinez [👤]

Cardiology:
- Dr. John Smith [👤]
- Dr. Sarah Johnson [👤]

[For complete doctors list, visit our website →]
```

**Test:** Each icon should link to correct specialty page

## 🔧 Customization

### Add New Specialty:

In `main.py`, add to `specialty_map`:

```python
'new-specialty-name': 'url-slug',
'alternative-name': 'url-slug',
```

### Change Icon:

In `App.jsx`, modify the emoji:

```javascript
// Change from 👤 to any other emoji/icon
<a>👨‍⚕️</a>  // Use doctor emoji
<a>📋</a>    // Use clipboard
<a>🔍</a>    // Use magnifying glass
```

### Adjust Icon Size:

```javascript
width: '28px',   // Increase from 24px
height: '28px',
fontSize: '16px'  // Adjust emoji size
```

## ⚠️ Important Notes

### URL Validation:

- System assumes the profile URL pattern is correct
- If a doctor profile doesn't exist on the website, the link will lead to 404
- Consider adding URL validation or fallback to general doctors list

### Name Slug Generation:

- Converts to lowercase
- Replaces spaces with hyphens
- Adds "dr-" prefix automatically
- Examples:
  - "Dr. John Smith" → "dr-john-smith"
  - "Dr. A.K. Sharma" → "dr-a.k.-sharma" (keeps dots)

### Specialty Context:

- Uses previous line context if specialty not inline
- Falls back to generic handling if no specialty detected
- Most recent specialty keyword takes precedence

## 📊 Performance

- **Regex Complexity:** O(n) where n = text length
- **No API Calls:** Pure client-side rendering
- **Instant Loading:** No network delay for icons
- **Cached Links:** Browser caches opened profiles

## 🎓 Future Enhancements

1. **Smart URL Validation:** Check if profile exists before linking
2. **Fallback Handling:** If profile 404s, redirect to doctors list
3. **Department Filtering:** Link to filtered doctors list by department
4. **Appointment Booking:** Add quick "Book Appointment" next to profile icon
5. **Preview Tooltip:** Show doctor photo/specialty on hover
6. **Analytics:** Track which doctor profiles are most viewed
