# 📊 Excel & CSV Support Guide

## ✅ What's New

Your chatbot now supports **THREE file formats**:

- 📄 **PDF** - For policies, procedures, guides (long-form content)
- 📊 **Excel (.xlsx, .xls)** - For structured data (doctors, departments, services)
- 📋 **CSV** - For simple tabular data (contacts, schedules)

---

## 🎯 When to Use Each Format

### **Use Excel/CSV for:**

✅ Doctor lists with specialties
✅ Department information with contacts
✅ Service directories
✅ Appointment schedules
✅ Contact directories
✅ Pricing tables
✅ Any structured, tabular data

### **Use PDF for:**

✅ Hospital policies and procedures
✅ Patient care guidelines
✅ Medical protocols
✅ Informational brochures
✅ FAQs with detailed explanations
✅ Any narrative, long-form content

---

## 📋 Excel/CSV Format Examples

### **Example 1: Doctors List**

Create a file named `doctors.xlsx` or `doctors.csv`:

| Doctor Name       | Specialty            | Department      | Phone        | Email                    | Availability |
| ----------------- | -------------------- | --------------- | ------------ | ------------------------ | ------------ |
| Dr. Kumudhini .D  | Microbiologist       | Laboratory      | 0422-2324105 | lab@kghospital.com       | Mon-Fri      |
| Dr. LATHA.R       | Transfusion Medicine | Blood Bank      | 0422-2324106 | bloodbank@kghospital.com | 24/7         |
| Dr. Sarah Roberts | Cardiologist         | KG Heart Centre | 0422-2324107 | cardio@kghospital.com    | Mon-Sat      |
| Dr. John Smith    | Neurologist          | Brain & Spine   | 0422-2324108 | neuro@kghospital.com     | Mon-Fri      |

**What happens:**

- Each row becomes ONE complete document
- No information splitting across chunks
- Perfect for queries like: "blood bank doctors", "cardiologists", "contact for neurologist"

---

### **Example 2: Departments Directory**

Create `departments.csv`:

| Department | Services                                          | Location  | Phone        | Hours       | Emergency |
| ---------- | ------------------------------------------------- | --------- | ------------ | ----------- | --------- |
| Blood Bank | Blood donation, Transfusion, Testing              | Block A-2 | 0422-2324106 | 24/7        | Yes       |
| Cardiology | ECG, Echo, Angiography, Pacemaker                 | Block B-1 | 0422-2324107 | 8 AM - 8 PM | Yes       |
| Orthopedic | Joint replacement, Fracture care, Sports medicine | Block C-3 | 0422-2324109 | 9 AM - 6 PM | No        |
| Pediatrics | Child care, Vaccination, Growth monitoring        | Block A-1 | 0422-2324110 | 24/7        | Yes       |

**Perfect for queries:**

- "What services does cardiology offer?"
- "Where is the blood bank located?"
- "Is orthopedic department available 24/7?"

---

### **Example 3: Service Pricing**

Create `services_pricing.xlsx`:

| Service                     | Department | Price (₹) | Duration | Insurance |
| --------------------------- | ---------- | --------- | -------- | --------- |
| ECG                         | Cardiology | 500       | 15 min   | Yes       |
| Echo                        | Cardiology | 2000      | 30 min   | Yes       |
| Blood Test - CBC            | Laboratory | 300       | 2 hours  | Yes       |
| X-Ray Chest                 | Radiology  | 800       | 10 min   | Yes       |
| Consultation - Cardiologist | Cardiology | 1000      | 30 min   | Yes       |

---

### **Example 4: Appointment Slots**

Create `appointment_slots.csv`:

| Doctor            | Department | Day       | Available Times           | Duration |
| ----------------- | ---------- | --------- | ------------------------- | -------- |
| Dr. Sarah Roberts | Cardiology | Monday    | 9 AM - 12 PM, 2 PM - 5 PM | 30 min   |
| Dr. Sarah Roberts | Cardiology | Wednesday | 9 AM - 1 PM               | 30 min   |
| Dr. John Smith    | Neurology  | Tuesday   | 10 AM - 1 PM, 3 PM - 6 PM | 45 min   |
| Dr. John Smith    | Neurology  | Thursday  | 10 AM - 2 PM              | 45 min   |

---

## 🚀 How to Upload Files

### **Step 1: Prepare Your Files**

1. Create Excel (.xlsx) or CSV files with clear column headers
2. Each row should be one complete record (doctor, department, service, etc.)
3. Include all relevant information in columns

### **Step 2: Upload via Admin Panel**

1. Go to **Admin Panel** in your chatbot
2. Click **"Upload Documents"** section
3. Drag & drop or browse for files
4. Supported formats: `.pdf`, `.csv`, `.xlsx`, `.xls`
5. Click **"Upload"** button

### **Step 3: Reload Vector Store**

1. After uploading new files, click **"Reload Documents"**
2. This will process all files (PDF + Excel + CSV)
3. Each Excel/CSV row becomes a structured document
4. Wait for "Documents reloaded successfully!" message

---

## 🔄 How Excel/CSV Processing Works

### **Backend Processing:**

**Input (Excel/CSV row):**

```
| Doctor Name: Dr. Kumudhini .D | Specialty: Microbiologist | Department: Laboratory | Phone: 0422-2324105 |
```

**Converted to Document:**

```
"Doctor Name: Dr. Kumudhini .D | Specialty: Microbiologist | Department: Laboratory | Phone: 0422-2324105"
```

**Stored in Vector Database:**

- Each row = one searchable document
- RAG retrieves relevant rows based on query
- LLM formats the answer naturally

---

## 💡 Best Practices

### **1. Column Naming**

✅ Use clear, descriptive column names
✅ Examples: "Doctor Name", "Specialty", "Phone", "Email", "Department"
❌ Avoid: "Name", "Type", "Info", "Data"

### **2. Complete Information**

✅ Include ALL relevant info in one row
✅ Each row should be self-contained
❌ Don't split information across multiple rows

### **3. Data Consistency**

✅ Use consistent formats (phone numbers, dates, times)
✅ Example: "0422-2324105" not "0422 2324105" or "04222324105"

### **4. File Organization**

✅ One topic per file (doctors.xlsx, departments.csv, services.xlsx)
✅ Clear file names
✅ Regular updates

---

## 📈 Expected Performance Improvements

### **Before (PDF Only):**

**Query:** "blood bank doctors list"
**Result:** Shows all doctors or vague information (RAG struggles with unstructured text)

### **After (Excel/CSV Added):**

**Query:** "blood bank doctors list"
**Result:** Precise list of blood bank doctors with:

- Doctor names
- Specialties
- Contact information
- Availability
- Department details

---

## 🧪 Testing Your Setup

### **Test Queries After Upload:**

1. **Doctor Queries:**

   - "list all cardiologists"
   - "blood bank doctors contact"
   - "who is the neurologist?"
   - "Dr. Sarah Roberts contact information"

2. **Department Queries:**

   - "cardiology department location"
   - "is blood bank open 24/7?"
   - "what services does orthopedic offer?"
   - "emergency departments list"

3. **Service Queries:**

   - "how much does an ECG cost?"
   - "services in cardiology department"
   - "available diagnostic tests"

4. **Scheduling Queries:**
   - "when is Dr. Sarah Roberts available?"
   - "appointment slots for cardiologist"
   - "Tuesday available doctors"

---

## ⚙️ Technical Details

### **Supported Formats:**

- ✅ `.csv` - UTF-8 encoded CSV files
- ✅ `.xlsx` - Modern Excel format (Excel 2007+)
- ✅ `.xls` - Legacy Excel format (Excel 97-2003)
- ✅ `.pdf` - Portable Document Format

### **Processing:**

- **CSV/Excel**: Each row → One document with structured key-value pairs
- **PDF**: Text extraction → Chunked into 1000-character segments with 200-character overlap
- **Vector Store**: FAISS with sentence-transformers embeddings
- **Retrieval**: MMR with K=10 for diverse, relevant results

### **Packages Used:**

- `pandas` - Data processing
- `openpyxl` - Excel (.xlsx) reading
- `xlrd` - Excel (.xls) reading
- `langchain-community` - Document loaders

---

## 🔧 Troubleshooting

### **Issue: "Excel loading failed"**

**Solution:**

- Ensure file is not corrupted
- Check if file has proper column headers
- Try saving as CSV instead

### **Issue: "CSV processing failed"**

**Solution:**

- Ensure UTF-8 encoding
- Check for special characters
- Remove empty rows

### **Issue: "Answers not specific enough"**

**Solution:**

- Add more columns with detailed information
- Ensure each row is complete
- Reload documents after changes

---

## 📝 Example Files Included

Check the `Backend/sample_data/` folder for:

- `sample_doctors.xlsx` - Example doctors list
- `sample_departments.csv` - Example departments directory
- `sample_services.xlsx` - Example services pricing

---

## 🎉 Summary

You now have a **hybrid system**:

- 📊 **Structured data** (Excel/CSV) for precise lookups
- 📄 **Unstructured content** (PDF) for detailed information
- 🤖 **Smart RAG** that handles both seamlessly

**Result:** Better answers, more accurate information, happier users! 🚀

---

**Need Help?**

- Check if files uploaded successfully in Admin Panel
- Verify documents reloaded after upload
- Test with simple queries first
- Review the logs for any errors
