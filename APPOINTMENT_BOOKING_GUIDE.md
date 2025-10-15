# Appointment Booking System - User Guide

## Overview

The appointment booking system now has an interactive, step-by-step flow that guides visitors through booking appointments.

## How It Works

### For Visitors

1. **Start Booking**

   - Click the "Book Appointment" button in Quick Actions
   - Or type "book appointment" in the chat

2. **Step-by-Step Process**
   The system will guide you through 5 steps with visual indicators:

   **Step 1: Name**

   - Enter your full name
   - Example: "John Smith"

   **Step 2: Phone Number**

   - Enter your phone number (minimum 8 digits)
   - Accepts formats: 1234567890, 123-456-7890, +1 (123) 456-7890
   - Validation ensures proper phone format

   **Step 3: Date**

   - Enter preferred appointment date
   - Example: "2024-12-25" or "December 25, 2024"

   **Step 4: Time**

   - Enter preferred appointment time
   - Example: "10:00 AM" or "14:30"

   **Step 5: Reason**

   - Enter reason for appointment
   - Example: "General checkup" or "Follow-up consultation"

3. **Visual Indicators**

   - Progress bar showing current step (1-5)
   - Each completed step shows a green checkmark (✓)
   - Current step is highlighted in blue
   - Dynamic placeholder text guides you for each step

4. **Cancel Anytime**
   - Click the "Cancel" button in the yellow banner to exit the booking flow

### For Admin

1. **View Appointments**

   - Click "Admin Dashboard" button in header
   - Navigate to "Appointments" tab
   - See all appointments with:
     - Visitor name
     - Phone number (clickable to call)
     - Preferred date and time
     - Reason for visit

2. **Accept & Call**
   - Click "Accept & Call" button
   - Opens phone dialer with visitor's number automatically
   - Marks appointment as accepted

## Features

### Visual Flow Indicator

- **Yellow banner** appears during booking process
- **Progress steps** (1-5) show where you are in the process
- **Step names**: Name → Phone → Date → Time → Reason
- **Checkmarks** (✓) for completed steps
- **Blue highlight** for current step

### Input Validation

- **Name**: Required, cannot be empty
- **Phone**: Must be 8+ digits, allows formatting characters (spaces, dashes, parentheses)
- **Date & Time**: Required fields
- **Reason**: Required, describes appointment purpose

### Error Handling

- Invalid phone numbers show error message: "Invalid phone number. Please enter at least 8 digits."
- Empty inputs are caught with appropriate error messages
- Failed submissions show: "Failed to book appointment. Please try again."

### Success Confirmation

- Success message displays all entered information
- Confirmation includes: name, phone, date, time, and reason
- Appointment appears immediately in admin dashboard

## Technical Details

### API Endpoint

```
POST /api/appointments
```

### Request Body

```json
{
  "name": "John Smith",
  "phone": "1234567890",
  "preferred_date": "2024-12-25",
  "preferred_time": "10:00 AM",
  "reason": "General checkup"
}
```

### State Management

- `appointmentFlow.active`: Boolean indicating if flow is active
- `appointmentFlow.step`: Current step (0-4)
- `appointmentFlow.data`: Object containing collected information

## Testing Checklist

- [ ] Click "Book Appointment" button
- [ ] Verify yellow banner appears with step indicators
- [ ] Enter name and verify progression to step 2
- [ ] Enter phone number (test valid and invalid formats)
- [ ] Enter date and time
- [ ] Enter reason and verify submission
- [ ] Check appointment appears in admin dashboard
- [ ] Test "Accept & Call" button opens dialer
- [ ] Test "Cancel" button exits flow properly
- [ ] Verify placeholder text changes for each step

## Troubleshooting

### Phone Number Issues

- Ensure at least 8 digits are entered
- Formatting characters are allowed: spaces, dashes, +, ( )
- If validation fails, re-enter with just digits

### Appointment Not Appearing

- Check browser console for errors
- Verify backend is running (port 8000)
- Check if GROQ_API_KEY is set in backend .env file

### Flow Not Starting

- Ensure Quick Actions panel is visible (appears after 3 messages)
- Try typing "book appointment" directly in chat
- Refresh page if issue persists

## Example Flow

```
User clicks "Book Appointment"
↓
Bot: "Great! Let's book your appointment. What is your name?"
User: "John Smith"
↓
Bot: "Thank you, John Smith! What is your phone number?"
User: "555-123-4567"
↓
Bot: "Got it! What date would you prefer?"
User: "2024-12-25"
↓
Bot: "And what time works best for you?"
User: "10:00 AM"
↓
Bot: "Finally, what is the reason for your appointment?"
User: "Annual checkup"
↓
Bot: "✅ Appointment booked successfully! Name: John Smith, Phone: 555-123-4567, Date: 2024-12-25, Time: 10:00 AM, Reason: Annual checkup"
```

## Notes

- The system uses visual cues (emojis, colors, animations) for better UX
- All appointment data is stored and accessible through admin dashboard
- Phone numbers are clickable links that open the device's phone dialer
- The booking flow prevents accidental exits with a cancel confirmation
