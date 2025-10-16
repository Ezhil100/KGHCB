# Mobile Responsive & Feature Updates Guide

## Features to Implement:

### 1. Quick Actions Button - Minimize After 3 Attempts

### 2. Calendar for Date Selection

### 3. Mobile Responsive Design

### 4. "book appointment" text trigger

---

## Implementation Steps:

### Step 1: Add New State Variables

After line 785 in App.jsx, add:

```jsx
const [showQuickActions, setShowQuickActions] = useState(true);
const [quickActionsMinimized, setQuickActionsMinimized] = useState(false);
const [messageCount, setMessageCount] = useState(0);
```

### Step 2: Update the useEffect for message count

Replace lines 814-818 with:

```jsx
useEffect(() => {
  if (messageCount >= 3 && !quickActionsMinimized) {
    setQuickActionsMinimized(true);
  }
}, [messageCount]);
```

### Step 3: Add Calendar Input for Date Selection

In the appointment flow handling (around line 1020), update the date step:

```jsx
case 2: // Date
  newFlow.data.date = currentInput;
  newFlow.step = 3;
  setMessages(prev => [...prev, {
    type: 'bot',
    content: '🕐 What time would you prefer? (e.g., 10:00 AM, 2:30 PM, or morning/afternoon/evening)',
    timestamp: formatTime(new Date())
  }]);
  break;
```

Add this HTML date input before the message (search for the date step UI):

```jsx
<input
  type="date"
  min={new Date().toISOString().split("T")[0]}
  onChange={(e) => handleDateSelect(e.target.value)}
  style={{
    padding: "12px",
    fontSize: "16px",
    border: "2px solid #007bff",
    borderRadius: "8px",
    width: "100%",
    marginBottom: "10px",
  }}
/>
```

### Step 4: Add "book appointment" Text Trigger

In the handleSendMessage function (around line 920), add this check:

```jsx
const handleSendMessage = async (customMessage = null) => {
  const messageToSend = (customMessage || input).trim();
  if (!messageToSend) return;

  // Check if user is trying to book appointment
  const appointmentTriggers = [
    "book appointment",
    "book an appointment",
    "make appointment",
    "schedule appointment",
  ];
  if (
    appointmentTriggers.some((trigger) =>
      messageToSend.toLowerCase().includes(trigger)
    ) &&
    !appointmentFlow.active
  ) {
    startAppointmentFlow();
    setInput("");
    return;
  }

  // ... rest of the function
};
```

### Step 5: Update Quick Actions Button with Minimize/Expand

Replace the Quick Actions section (around line 1525) with:

```jsx
{
  quickActionsMinimized ? (
    <button
      onClick={() => setQuickActionsMinimized(false)}
      style={{
        position: "fixed",
        bottom: "20px",
        right: "20px",
        width: "60px",
        height: "60px",
        borderRadius: "50%",
        backgroundColor: "#007bff",
        color: "white",
        border: "none",
        boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
        cursor: "pointer",
        fontSize: "24px",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1000,
      }}
      title="Show Quick Actions"
    >
      ⚡
    </button>
  ) : (
    showQuickActions && (
      <div
        style={{
          ...styles.quickActionsContainer,
          animation: "slideIn 0.3s ease-out",
        }}
      >
        <div style={styles.quickActionsHeader}>
          <span>Quick Actions</span>
          <button
            onClick={() => setQuickActionsMinimized(true)}
            style={{
              background: "none",
              border: "none",
              color: "#666",
              cursor: "pointer",
              fontSize: "20px",
              padding: "0 5px",
            }}
            title="Minimize"
          >
            ✕
          </button>
        </div>
        {/* ... rest of quick actions content ... */}
      </div>
    )
  );
}
```

### Step 6: Add Mobile Responsive CSS

Add this to your styles object (around line 1600):

```jsx
// Add media query styles
const isMobile = window.innerWidth <= 768;

// Update styles dynamically
const responsiveStyles = {
  container: {
    ...styles.container,
    padding: isMobile ? "10px" : "20px",
    height: isMobile ? "calc(100vh - 60px)" : "100vh",
  },
  header: {
    ...styles.header,
    padding: isMobile ? "12px 10px" : "20px",
    flexDirection: isMobile ? "row" : "row",
    height: isMobile ? "auto" : "80px",
    minHeight: isMobile ? "56px" : "80px",
  },
  headerTitle: {
    fontSize: isMobile ? "0" : "24px", // Hide text on mobile
    width: isMobile ? "0" : "auto",
    overflow: "hidden",
  },
  hospitalIcon: {
    fontSize: isMobile ? "32px" : "40px",
    marginRight: isMobile ? "0" : "15px",
  },
  chatLog: {
    ...styles.chatLog,
    padding: isMobile ? "10px" : "20px",
    maxHeight: isMobile ? "calc(100vh - 200px)" : "calc(100vh - 280px)",
  },
  inputContainer: {
    ...styles.inputContainer,
    padding: isMobile ? "10px" : "15px",
  },
  input: {
    ...styles.input,
    fontSize: isMobile ? "16px" : "16px", // Prevent zoom on iOS
    padding: isMobile ? "12px" : "15px",
  },
  sendButton: {
    ...styles.sendButton,
    padding: isMobile ? "10px 20px" : "15px 30px",
    fontSize: isMobile ? "14px" : "16px",
  },
  quickActionsContainer: {
    position: "fixed",
    bottom: isMobile ? "10px" : "20px",
    right: isMobile ? "10px" : "20px",
    width: isMobile ? "calc(100% - 20px)" : "300px",
    maxWidth: isMobile ? "400px" : "300px",
  },
};
```

### Step 7: Add Window Resize Handler

Add this useEffect:

```jsx
useEffect(() => {
  const handleResize = () => {
    setIsMobile(window.innerWidth <= 768);
  };

  window.addEventListener("resize", handleResize);
  return () => window.removeEventListener("resize", handleResize);
}, []);
```

### Step 8: Add Calendar Picker Component

Install date picker (in terminal):

```bash
npm install react-datepicker
```

At the top of App.jsx, add:

```jsx
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
```

Then use it in the appointment flow:

```jsx
{
  appointmentFlow.active && appointmentFlow.step === 2 && (
    <div
      style={{
        padding: "15px",
        backgroundColor: "#f8f9fa",
        borderRadius: "8px",
        marginBottom: "15px",
      }}
    >
      <p style={{ marginBottom: "10px", fontWeight: "600" }}>
        📅 Select appointment date:
      </p>
      <DatePicker
        selected={
          appointmentFlow.data.date ? new Date(appointmentFlow.data.date) : null
        }
        onChange={(date) => {
          const formattedDate = date.toLocaleDateString("en-US", {
            year: "numeric",
            month: "long",
            day: "numeric",
          });
          setAppointmentFlow((prev) => ({
            ...prev,
            data: { ...prev.data, date: formattedDate },
            step: 3,
          }));
          setMessages((prev) => [
            ...prev,
            {
              type: "user",
              content: formattedDate,
              timestamp: formatTime(new Date()),
            },
            {
              type: "bot",
              content: "🕐 What time would you prefer?",
              timestamp: formatTime(new Date()),
            },
          ]);
        }}
        minDate={new Date()}
        inline
        dateFormat="MMMM d, yyyy"
      />
    </div>
  );
}
```

---

## CSS Media Queries (Add to index.css or App.css)

```css
/* Mobile Responsive Styles */
@media only screen and (max-width: 768px) {
  body {
    font-size: 14px;
  }

  /* Hide title text on mobile, keep icon */
  .hospital-title-text {
    display: none !important;
  }

  /* Adjust header for mobile */
  header {
    padding: 10px !important;
    min-height: 56px !important;
  }

  /* Full width chat on mobile */
  .chat-container {
    width: 100% !important;
    height: calc(100vh - 60px) !important;
    padding: 0 !important;
  }

  /* Optimize chat log for mobile */
  .chat-log {
    padding: 10px !important;
    max-height: calc(100vh - 180px) !important;
  }

  /* Adjust input area for mobile */
  .input-container {
    padding: 10px !important;
  }

  input,
  textarea {
    font-size: 16px !important; /* Prevent iOS zoom */
  }

  /* Quick actions full width on mobile */
  .quick-actions {
    width: calc(100% - 20px) !important;
    left: 10px !important;
    right: 10px !important;
  }

  /* Adjust message bubbles */
  .message {
    max-width: 85% !important;
  }
}

/* Tablet styles */
@media only screen and (min-width: 769px) and (max-width: 1024px) {
  .chat-container {
    width: 95% !important;
  }
}

/* Animation for slide in */
@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}
```

---

## Testing Checklist:

- [ ] Quick actions minimizes after 3 messages
- [ ] Clicking minimized icon expands quick actions
- [ ] Calendar appears for date selection in appointment booking
- [ ] "book appointment" text starts appointment flow
- [ ] Mobile view shows only hospital icon (no title text)
- [ ] Mobile chat log is scrollable and readable
- [ ] All content visible on mobile devices
- [ ] Desktop layout unchanged
- [ ] Works on iPhone, Android, tablets
- [ ] Input doesn't cause zoom on mobile

---

## Quick Implementation Summary:

1. Add state for `quickActionsMinimized`
2. Update useEffect to minimize after 3 messages
3. Add minimize/expand button to quick actions
4. Install and integrate react-datepicker
5. Add appointment trigger detection in handleSendMessage
6. Add responsive CSS media queries
7. Update styles object with mobile checks
8. Test on multiple devices

Would you like me to generate the complete modified App.jsx file, or implement these changes step by step?
