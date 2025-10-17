import React, { useState, useEffect, useRef, useCallback } from 'react';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';

const API_BASE_URL = 'http://172.16.53.40:8000'; // WiFi network access

// Time formatting helpers (no seconds)
const formatTime = (date) => {
  try {
    const d = date instanceof Date ? date : new Date(date);
    return d.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
  } catch {
    return '';
  }
};

const formatDateTime = (date) => {
  try {
    const d = date instanceof Date ? date : new Date(date);
    return d.toLocaleString([], { year: 'numeric', month: 'numeric', day: 'numeric', hour: 'numeric', minute: '2-digit' });
  } catch {
    return '';
  }
};

// Icons Component (keeping same as original)
const Icons = {
  Hospital: () => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <rect x="3" y="3" width="18" height="18" rx="2"/>
      <path d="M12 8v8M8 12h8"/>
    </svg>
  ),
  
  HospitalLarge: () => (
    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <rect x="3" y="3" width="18" height="18" rx="3"/>
      <path d="M12 7v10M7 12h10"/>
      <circle cx="12" cy="12" r="1" fill="currentColor"/>
    </svg>
  ),

  Upload: () => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <rect x="3" y="8" width="18" height="12" rx="2"/>
      <path d="M7 8V6a2 2 0 0 1 2-2h6a2 2 0 0 1 2 2v2"/>
      <path d="M12 11v6M9 14l3-3 3 3"/>
    </svg>
  ),

  Document: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
      <path d="M14 2v6h6M16 13H8M16 17H8M10 9H8"/>
    </svg>
  ),

  Check: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
      <circle cx="12" cy="12" r="10"/>
      <path d="M9 12l2 2 4-4"/>
    </svg>
  ),

  Error: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
      <circle cx="12" cy="12" r="10"/>
      <path d="M15 9l-6 6M9 9l6 6"/>
    </svg>
  ),

  Reload: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
      <path d="M1 4v6h6M23 20v-6h-6"/>
      <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"/>
    </svg>
  ),

  Settings: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="3"/>
      <path d="M12 1v6M12 17v6M4.22 4.22l4.24 4.24M15.54 15.54l4.24 4.24M1 12h6M17 12h6M4.22 19.78l4.24-4.24M15.54 8.46l4.24-4.24"/>
    </svg>
  ),

  Dashboard: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <rect x="3" y="3" width="7" height="7"/>
      <rect x="14" y="3" width="7" height="7"/>
      <rect x="14" y="14" width="7" height="7"/>
      <rect x="3" y="14" width="7" height="7"/>
    </svg>
  ),

  Close: () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
      <path d="M18 6L6 18M6 6l12 12"/>
    </svg>
  ),

  Send: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M22 2L11 13M22 2l-7 20-4-9-9-4z"/>
    </svg>
  ),

  StatusDot: ({ status }) => (
    <div style={{
      width: '8px',
      height: '8px',
      borderRadius: '50%',
      background: status === 'success' ? '#28a745' : 
                  status === 'error' ? '#dc3545' : 
                  status === 'warning' ? '#ffc107' : '#6c757d',
      position: 'relative'
    }}>
      <div style={{
        width: '12px',
        height: '12px',
        borderRadius: '50%',
        border: `2px solid ${status === 'success' ? '#28a745' : 
                              status === 'error' ? '#dc3545' : 
                              status === 'warning' ? '#ffc107' : '#6c757d'}`,
        position: 'absolute',
        top: '-4px',
        left: '-4px',
        opacity: 0.3
      }}/>
    </div>
  ),

  FileUpload: () => (
    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
      <rect x="3" y="3" width="18" height="18" rx="4"/>
      <path d="M12 8v8M8 12h8"/>
      <circle cx="8" cy="8" r="1" fill="currentColor"/>
      <circle cx="16" cy="8" r="1" fill="currentColor"/>
      <circle cx="8" cy="16" r="1" fill="currentColor"/>
      <circle cx="16" cy="16" r="1" fill="currentColor"/>
    </svg>
  ),

  Remove: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
      <path d="M18 6L6 18M6 6l12 12"/>
    </svg>
  ),

  Analysis: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M3 3v18h18"/>
      <path d="M7 12l4-4 4 4 4-4"/>
    </svg>
  )
};

// Helper function to process actionable elements in text
const processActionableText = (text) => {
  if (!text || typeof text !== 'string') return text;
  
  const parts = [];
  let lastIndex = 0;
  
  // Process all actionable markers
  const patterns = [
    { regex: /\[TEL:([\d\s\-\+\(\)]+)\]/g, type: 'phone' },
    { regex: /\[DOCTOR:([^\]]+)\]/g, type: 'doctor' },
    { regex: /\[DOCTORPROFILE:([^\|]+)\|([^\|]+)\|([^\]]+)\]/g, type: 'doctorprofile' },
    { regex: /\[DOCTORSLIST:([^\]]+)\]/g, type: 'doctorslist' },
    { regex: /\[LOCATION:([^\]]+)\]/g, type: 'location' },
    { regex: /\[EMERGENCY:([\d\s\-\+]+)\]/g, type: 'emergency' },
    { regex: /\[DEPARTMENT:([^\]]+)\]/g, type: 'department' }
  ];
  
  // Find all matches
  const allMatches = [];
  patterns.forEach(({regex, type}) => {
    let match;
    const regexCopy = new RegExp(regex.source, regex.flags);
    while ((match = regexCopy.exec(text)) !== null) {
      // For doctorprofile, capture all three groups: name, specialty, slug
      if (type === 'doctorprofile') {
        allMatches.push({ 
          index: match.index, 
          length: match[0].length, 
          content: match[1], 
          specialty: match[2],
          slug: match[3],
          type 
        });
      } else {
        allMatches.push({ index: match.index, length: match[0].length, content: match[1], type });
      }
    }
  });
  
  // Sort by position
  allMatches.sort((a, b) => a.index - b.index);
  
  // Build result with React elements
  allMatches.forEach((match, idx) => {
    // Add text before match
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }
    
    // Add actionable element
    const key = `action-${idx}`;
    switch (match.type) {
      case 'phone':
        const cleanPhone = match.content.replace(/\s/g, '');
        parts.push(
          <a key={key} href={`tel:${cleanPhone}`} style={{
            color: '#28a745',
            fontWeight: '600',
            textDecoration: 'none',
            borderBottom: '2px dotted #28a745',
            cursor: 'pointer'
          }} title="Click to call">
            📞 {match.content}
          </a>
        );
        break;
      case 'doctorprofile':
        // Build URL: https://www.kghospital.com/doctors/{specialty}/{dr-name}
        const doctorProfileUrl = `https://www.kghospital.com/doctors/${match.specialty}/${match.slug}`;
        parts.push(
          <span key={key} style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
            <span>{match.content}</span>
            <a 
              href={doctorProfileUrl} 
              target="_blank" 
              rel="noopener noreferrer" 
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: '18px',
                height: '18px',
                textDecoration: 'none',
                transition: 'all 0.3s',
                cursor: 'pointer',
                opacity: 0.7
              }}
              title="View doctor profile"
              onMouseOver={(e) => {
                e.currentTarget.style.opacity = '1';
                e.currentTarget.style.transform = 'scale(1.15)';
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.opacity = '0.7';
                e.currentTarget.style.transform = 'scale(1)';
              }}
            >
              <svg 
                viewBox="0 0 24 24" 
                width="18" 
                height="18" 
                fill="none" 
                stroke="#2E4AC7" 
                strokeWidth="2.5" 
                strokeLinecap="round" 
                strokeLinejoin="round"
              >
                <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
                <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
              </svg>
            </a>
          </span>
        );
        break;
      case 'doctor':
        const doctorName = match.content.replace(/^(Dr\.?\s*|Doctor\s*)/, '');
        const profileUrl = `https://www.kghospital.com/doctors-list`;
        parts.push(
          <a key={key} href={profileUrl} target="_blank" rel="noopener noreferrer" style={{
            color: '#1F3A9E',
            fontWeight: '600',
            textDecoration: 'none',
            borderBottom: '2px solid #1F3A9E',
            cursor: 'pointer'
          }} title="View doctor profile">
            👨‍⚕️ {match.content}
          </a>
        );
        break;
      case 'location':
        const mapsUrl = `https://www.google.com/maps/search/?api=1&query=KG+Hospital+Coimbatore`;
        parts.push(
          <a key={key} href={mapsUrl} target="_blank" rel="noopener noreferrer" style={{
            color: '#dc3545',
            fontWeight: '600',
            textDecoration: 'none',
            borderBottom: '2px solid #dc3545',
            cursor: 'pointer'
          }} title="Open in Google Maps">
            📍 {match.content}
          </a>
        );
        break;
      case 'emergency':
        const emergencyPhone = match.content.replace(/\s/g, '');
        parts.push(
          <a key={key} href={`tel:${emergencyPhone}`} style={{
            color: '#dc3545',
            fontWeight: '700',
            textDecoration: 'none',
            padding: '4px 8px',
            background: '#fee2e2',
            borderRadius: '6px',
            cursor: 'pointer',
            display: 'inline-block'
          }} title="Emergency - Click to call">
            🚨 {match.content}
          </a>
        );
        break;
      case 'doctorslist':
        const doctorsListUrl = `https://www.kghospital.com/doctors-list`;
        parts.push(
          <a key={key} href={doctorsListUrl} target="_blank" rel="noopener noreferrer" style={{
            color: '#1F3A9E',
            fontWeight: '700',
            textDecoration: 'none',
            padding: '8px 16px',
            background: 'linear-gradient(135deg, #e8f1ff 0%, #d1e4ff 100%)',
            border: '2px solid #1F3A9E',
            borderRadius: '8px',
            cursor: 'pointer',
            display: 'inline-block',
            marginTop: '8px',
            transition: 'all 0.3s'
          }} title="View complete doctors list">
            👨‍⚕️ {match.content} →
          </a>
        );
        break;
      case 'department':
        parts.push(
          <span key={key} style={{
            color: '#1F3A9E',
            fontWeight: '400',
            padding: '2px 8px',
            background: '#e8f1ff',
            borderRadius: '6px',
            cursor: 'pointer',
            display: 'inline-block'
          }} title="Hospital Department">
            {match.content}
          </span>
        );
        break;
      default:
        parts.push(match.content);
    }
    
    lastIndex = match.index + match.length;
  });
  
  // Add remaining text
  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }
  
  return parts.length > 0 ? parts : text;
};

// Component to format text with proper line breaks, bullet points, and tables
const FormattedMessage = ({ content }) => {
  if (!content || typeof content !== 'string') {
    return <span>{content}</span>;
  }

  // Check if content contains a table
  if (content.includes('|') && content.includes('---')) {
    return <TableRenderer content={content} />;
  }

  // Helper: render inline **bold** segments and actionable elements
  const renderInline = (text) => {
    if (text == null) return text;
    if (typeof text !== 'string') return text;
    
    // First process actionable elements
    let processed = processActionableText(text);
    
    // If processActionableText returned an array (with React elements), handle bold within text parts
    if (Array.isArray(processed)) {
      const result = [];
      processed.forEach((part, idx) => {
        if (typeof part === 'string') {
          // Process bold markdown in string parts
          const out = [];
          let last = 0;
          const regex = /\*\*(.+?)\*\*/g;
          let m;
          while ((m = regex.exec(part)) !== null) {
            if (m.index > last) out.push(part.slice(last, m.index));
            out.push(<strong key={`b-${idx}-${out.length}`} style={{ color: '#1F3A9E' }}>{m[1]}</strong>);
            last = regex.lastIndex;
          }
          if (last < part.length) out.push(part.slice(last));
          result.push(...out);
        } else {
          // Keep React elements as-is
          result.push(part);
        }
      });
      return result.length > 0 ? result : processed;
    }
    
    // Handle bold markdown for plain strings
    if (typeof processed === 'string') {
      const out = [];
      let last = 0;
      const regex = /\*\*(.+?)\*\*/g;
      let m;
      while ((m = regex.exec(processed)) !== null) {
        if (m.index > last) out.push(processed.slice(last, m.index));
        out.push(<strong key={`b-${out.length}`} style={{ color: '#1F3A9E' }}>{m[1]}</strong>);
        last = regex.lastIndex;
      }
      if (last < processed.length) out.push(processed.slice(last));
      return out.length ? out : processed;
    }
    
    return processed;
  };

  // Split by lines and process each line
  const lines = content.split('\n');
  
  return (
    <div style={{ lineHeight: '1.6', fontSize: '15px' }}>
      {lines.map((line, index) => {
        const trimmedLine = line.trim();
        
        // Skip empty lines but preserve spacing
        if (!trimmedLine) {
          return <div key={index} style={{ height: '8px' }} />;
        }
        
        // Check if line is a header (wrapped in **)
        if (trimmedLine.startsWith('**') && trimmedLine.endsWith('**')) {
          const headerText = trimmedLine.slice(2, -2);
          return (
            <div key={index} style={{ 
              fontWeight: '600', 
              fontSize: '17px', 
              color: '#1F3A9E', 
              marginTop: index > 0 ? '16px' : '0',
              marginBottom: '12px',
              borderBottom: '2px solid #e8f1ff',
              paddingBottom: '6px'
            }}>
              {headerText}
            </div>
          );
        }
        
        // Check if line is a bullet point (supports '• ', '* ', '- ')
        if (trimmedLine.startsWith('• ') || /^[-*]\s+/.test(trimmedLine)) {
          const bulletText = trimmedLine.startsWith('• ')
            ? trimmedLine.slice(2)
            : trimmedLine.replace(/^[-*]\s+/, '');
          return (
            <div key={index} style={{ 
              marginLeft: '20px', 
              marginBottom: '8px',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '12px'
            }}>
              <span style={{ 
                color: '#FF8C00', 
                fontWeight: 'bold',
                marginTop: '2px',
                fontSize: '16px',
                minWidth: '16px'
              }}>•</span>
              <span style={{ flex: 1, lineHeight: '1.5' }}>{renderInline(bulletText)}</span>
            </div>
          );
        }
        
        // Check if line is numbered list
        if (/^\d+\.\s/.test(trimmedLine)) {
          const match = trimmedLine.match(/^(\d+\.\s*)(.+)/);
          const number = match ? match[1] : '';
          let content = match ? match[2] : trimmedLine;
          
          // IMPORTANT: Process actionable elements FIRST before any other formatting
          content = renderInline(content);
          
          // If the entire content is wrapped in **bold**, treat it as a header (category title)
          if (typeof content === 'string' && /^\*\*(.+)\*\*$/.test(content)) {
            const headerText = content.replace(/^\*\*(.+)\*\$/, '**$1**');
            return (
              <div key={index} style={{ 
                fontWeight: '600', 
                fontSize: '17px', 
                color: '#1F3A9E', 
                marginTop: index > 0 ? '16px' : '0',
                marginBottom: '10px',
                borderBottom: '2px solid #e8f1ff',
                paddingBottom: '6px'
              }}>
                {headerText.slice(2, -2)}
              </div>
            );
          }

          // If content is already processed (array of React elements), just render it
          if (Array.isArray(content)) {
            return (
              <div key={index} style={{ 
                marginLeft: '12px', 
                marginBottom: '8px',
                display: 'flex',
                alignItems: 'flex-start',
                gap: '10px',
                padding: '6px 0'
              }}>
                <span style={{ 
                  color: '#FF8C00', 
                  fontWeight: '700',
                  fontSize: '15px',
                  minWidth: '24px',
                  textAlign: 'right'
                }}>{number.trim()}</span>
                <span style={{ 
                  flex: 1, 
                  lineHeight: '1.6',
                  fontSize: '15px'
                }}>
                  {content}
                </span>
              </div>
            );
          }

          // Parse tokens separated by ' - ' and treat the LAST employment-type token specially.
          // This lets us merge compound names like "Cardiac - Anesthesiology" -> "Cardiac Anesthesiology".
          let formattedContent = content;
          if (content.includes(' - ')) {
            const tokens = content.split(' - ').map(t => t.trim()).filter(Boolean);
            if (tokens.length >= 2) {
              // Detect employment token in the last position
              const last = tokens[tokens.length - 1];
              const isEmployment = /(full\s*time|part\s*time|visiting|locum|consultant)/i.test(last);
              const isNoCategory = /no\s*category\s*mentioned/i.test(last);

              if (isEmployment) {
                const employmentType = last;
                const nameJoined = tokens.slice(0, -1).join(' '); // merge all prior tokens into the name
                formattedContent = (
                  <span>
                    <strong style={{ color: '#1F3A9E' }}>{nameJoined}</strong>
                    <span style={{ color: '#666', margin: '0 8px' }}>-</span>
                    <span style={{ 
                      color: employmentType.toLowerCase().includes('full time') ? '#28a745' :
                             employmentType.toLowerCase().includes('part time') ? '#856404' : '#0c5460',
                      marginLeft: '0',
                      fontSize: '13px',
                      fontWeight: '600',
                      padding: '2px 6px',
                      borderRadius: '4px',
                      backgroundColor: employmentType.toLowerCase().includes('full time') ? '#d4edda' :
                                      employmentType.toLowerCase().includes('part time') ? '#fff3cd' : '#d1ecf1'
                    }}>
                      {employmentType}
                    </span>
                  </span>
                );
              } else if (isNoCategory) {
                const nameJoined = tokens.slice(0, -1).join(' ');
                formattedContent = (
                  <span>
                    <strong style={{ color: '#1F3A9E' }}>{nameJoined}</strong>
                    <span style={{ color: '#666', marginLeft: '8px' }}>-</span>
                    <span style={{ color: '#555', marginLeft: '8px' }}>{last}</span>
                  </span>
                );
              } else {
                // Default: keep first part as name and show remainder as plain text
                const name = tokens[0];
                const rest = tokens.slice(1).join(' - ');
                formattedContent = (
                  <span>
                    <strong style={{ color: '#1F3A9E' }}>{name}</strong>
                    <span style={{ color: '#666', marginLeft: '8px' }}>-</span>
                    <span style={{ marginLeft: '8px' }}>{rest}</span>
                  </span>
                );
              }
            }
          }
          // Note: renderInline already called at the beginning of numbered list handling
          
          return (
            <div key={index} style={{ 
              marginLeft: '12px', 
              marginBottom: '8px',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '10px',
              padding: '6px 0'
            }}>
              <span style={{ 
                color: '#FF8C00', 
                fontWeight: '700',
                fontSize: '15px',
                minWidth: '24px',
                textAlign: 'right'
              }}>{number.trim()}</span>
              <span style={{ 
                flex: 1, 
                lineHeight: '1.6',
                fontSize: '15px'
              }}>
                {formattedContent}
              </span>
            </div>
          );
        }
        
        // Regular line
        return (
          <div key={index} style={{ 
            marginBottom: '8px',
            lineHeight: '1.5'
          }}>
            {renderInline(trimmedLine)}
          </div>
        );
      })}
    </div>
  );
};

// Component to render tables (supports multiple tables and malformed rows)
const TableRenderer = ({ content }) => {
  const lines = content.split('\n');

  // Split content into blocks of tables and non-table text
  const blocks = [];
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    const isTableLine = line.trim().startsWith('|');
    if (!isTableLine) {
      // accumulate non-table text until next table
      const textBuf = [];
      while (i < lines.length && !lines[i].trim().startsWith('|')) {
        if (lines[i].trim()) textBuf.push(lines[i]);
        i++;
      }
      if (textBuf.length) blocks.push({ type: 'text', lines: textBuf });
    } else {
      // accumulate table lines until a non-table line
      const tableBuf = [];
      while (i < lines.length && lines[i].trim().startsWith('|')) {
        // ignore stray lines like "||||" (no cell content)
        const raw = lines[i].trim();
        const cells = raw.split('|').map(c => c.trim()).filter(Boolean);
        if (cells.length > 0) tableBuf.push(lines[i]);
        i++;
      }
      if (tableBuf.length) blocks.push({ type: 'table', lines: tableBuf });
    }
  }

  const renderTable = (tableLines, key) => {
    if (!tableLines || tableLines.length < 2) return null;

    // Find header and separator; if missing, synthesize a header with generic columns
    let headerIdx = 0;
    let sepIdx = 1;
    // If no explicit separator, try to detect by presence of --- or create one
    if (!tableLines[1] || !tableLines[1].includes('---')) {
      // infer columns from first row
      const inferredCols = tableLines[0].split('|').map(c => c.trim()).filter(Boolean).length || 4;
      const sep = Array(inferredCols).fill('---').join(' | ');
      tableLines = [tableLines[0], `| ${sep} |`, ...tableLines.slice(1)];
    }

    const headerLine = tableLines[headerIdx];
    const dataLines = tableLines.slice(2);

  const headers = headerLine.split('|').map(h => h.trim()).filter(Boolean);
  // Clean headers (fallback to Column N for blanks)
  const headerCount = headers.length || 4;
  const cleanHeaders = headers.length ? headers : Array.from({ length: headerCount }, (_, i) => `Column ${i + 1}`);

    const rows = dataLines
      .map(line => line.split('|').map(c => c.trim()))
      .map(cells => cells.filter(Boolean))
      .filter(row => row.length > 0);

    // Normalize row lengths to headers length
    const normalizedRows = rows.map(row => {
      if (row.length === cleanHeaders.length) return row;
      if (row.length < cleanHeaders.length) {
        return [...row, ...Array(cleanHeaders.length - row.length).fill('')];
      }
      return row.slice(0, cleanHeaders.length);
    });

    return (
      <div key={key} style={{ 
        margin: '16px 0',
        border: '1px solid #e8f1ff',
        borderRadius: '8px',
        overflow: 'hidden',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
      }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
          <thead>
            <tr style={{ background: 'linear-gradient(135deg, #2E4AC7 0%, #1F3A9E 100%)', color: 'white' }}>
              {cleanHeaders.map((header, index) => (
                <th key={index} style={{
                  padding: '12px 8px',
                  textAlign: 'left',
                  fontWeight: '600',
                  fontSize: '13px',
                  borderRight: index < cleanHeaders.length - 1 ? '1px solid rgba(255,255,255,0.2)' : 'none'
                }}>
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {normalizedRows.map((row, rowIndex) => (
              <tr key={rowIndex} style={{ background: rowIndex % 2 === 0 ? '#fafcff' : 'white', borderBottom: '1px solid #f0f4f8' }}>
                {row.map((cell, cellIndex) => (
                  <td key={cellIndex} style={{ padding: '10px 8px', borderRight: cellIndex < row.length - 1 ? '1px solid #f0f4f8' : 'none', color: '#2d3748', lineHeight: '1.4' }}>
                    {cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  // Render blocks
  return (
    <div style={{ fontSize: '15px', lineHeight: '1.6' }}>
      {blocks.map((block, idx) => {
        if (block.type === 'text') {
          return <FormattedMessage key={`text-${idx}`} content={block.lines.join('\n')} />;
        }
        if (block.type === 'table') {
          return renderTable(block.lines, `table-${idx}`);
        }
        return null;
      })}
    </div>
  );
};

const App = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [userRole, setUserRole] = useState('visitor');
  const [isTyping, setIsTyping] = useState(false);
  const [showAdminModal, setShowAdminModal] = useState(false);
  const [adminTab, setAdminTab] = useState('dashboard');
  const [chatHistory, setChatHistory] = useState([]);
  const [appointments, setAppointments] = useState([]);
  const [statistics, setStatistics] = useState({});
  const [historyFilter, setHistoryFilter] = useState('all');
  const [appointmentFilter, setAppointmentFilter] = useState('pending');
  const [notifications, setNotifications] = useState([]);
  const [unreadNotifications, setUnreadNotifications] = useState(0);
  const [documents, setDocuments] = useState([]);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [systemStatus, setSystemStatus] = useState({});
  const [connectionStatus, setConnectionStatus] = useState('connecting');
  const [loading, setLoading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [messageCount, setMessageCount] = useState(0);
  const [showRoleSelector, setShowRoleSelector] = useState(true);
  const [userId, setUserId] = useState(null);
  
  // Appointment booking flow states
  const [appointmentFlow, setAppointmentFlow] = useState({
    active: false,
    step: 0, // 0: name, 1: phone, 2: date, 3: time, 4: reason
    data: {
      name: '',
      phone: '',
      date: '',
      time: '',
      reason: ''
    }
  });
  const [selectedDate, setSelectedDate] = useState(null);

  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const uploadIntervalRef = useRef(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const api = {
    sendMessage: async (message, userRole) => {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          message, 
          user_role: userRole,
          user_id: userId
        })
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to send message');
      }
      return await response.json();
    },

    uploadDocument: async (file) => {
      const formData = new FormData();
      formData.append('file', file);
      const response = await fetch(`${API_BASE_URL}/upload-document`, {
        method: 'POST',
        body: formData
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Upload failed');
      }
      return await response.json();
    },

    getDocuments: async () => {
      const response = await fetch(`${API_BASE_URL}/documents`);
      if (!response.ok) throw new Error('Failed to fetch documents');
      return await response.json();
    },

    reloadDocuments: async () => {
      const response = await fetch(`${API_BASE_URL}/reload-documents`, {
        method: 'POST'
      });
      if (!response.ok) throw new Error('Failed to reload documents');
      return await response.json();
    },

    getSystemStatus: async () => {
      const response = await fetch(`${API_BASE_URL}/system/status`);
      if (!response.ok) throw new Error('Failed to fetch status');
      return await response.json();
    },

    // Admin APIs
    getChatHistory: async (role = null) => {
      const url = role && role !== 'all'
        ? `${API_BASE_URL}/admin/chat-history?user_role=${role}`
        : `${API_BASE_URL}/admin/chat-history`;
      const response = await fetch(url);
      if (!response.ok) throw new Error('Failed to fetch chat history');
      return await response.json();
    },

    getAppointments: async (status = null) => {
      const url = status
        ? `${API_BASE_URL}/admin/appointments?status=${status}`
        : `${API_BASE_URL}/admin/appointments`;
      const response = await fetch(url);
      if (!response.ok) throw new Error('Failed to fetch appointments');
      return await response.json();
    },

    handleAppointment: async (appointmentId, action, notes = '') => {
      const response = await fetch(`${API_BASE_URL}/admin/appointments/action`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ appointment_id: appointmentId, action, admin_notes: notes })
      });
      if (!response.ok) throw new Error('Failed to update appointment');
      return await response.json();
    },

    getStatistics: async () => {
      const response = await fetch(`${API_BASE_URL}/admin/statistics`);
      if (!response.ok) throw new Error('Failed to fetch statistics');
      return await response.json();
    },

    getNotifications: async () => {
      const response = await fetch(`${API_BASE_URL}/admin/notifications`);
      if (!response.ok) throw new Error('Failed to fetch notifications');
      return await response.json();
    },

    markNotificationRead: async (notificationId) => {
      const response = await fetch(`${API_BASE_URL}/admin/notifications/mark-read`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ notification_id: notificationId })
      });
      if (!response.ok) throw new Error('Failed to mark notification as read');
      return await response.json();
    },

    bookAppointment: async (appointmentData) => {
      const message = `Book appointment for ${appointmentData.name} (${appointmentData.phone}) on ${appointmentData.date} at ${appointmentData.time}. Reason: ${appointmentData.reason}`;
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          message,
          user_role: userRole,
          user_id: userId
        })
      });
      if (!response.ok) throw new Error('Failed to book appointment');
      return await response.json();
    }
  };

  useEffect(() => {
    testBackendConnection();
  }, []);

  const testBackendConnection = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/`);
      if (response.ok) {
        setConnectionStatus('connected');
      } else {
        setConnectionStatus('error');
      }
    } catch (error) {
      setConnectionStatus('error');
    }
  };

  // Helper function to create message with unique ID
  const createMessage = (type, content) => ({
    type,
    content,
    timestamp: formatTime(new Date()),
    id: `msg-${Date.now()}-${Math.random()}`
  });

  const handleRoleSelection = (role) => {
    setUserRole(role);
    setShowRoleSelector(false);
    // generate a simple client-side user id
    const genId = `uid-${Date.now()}-${Math.random().toString(36).slice(2,8)}`;
    setUserId(genId);
    setMessages([createMessage('bot', `Welcome! You are accessing as a ${role}. How can I help you today?`)]);
  };

  // Handle date selection from calendar
  const handleDateSelect = (date) => {
    if (!date || appointmentFlow.step !== 2) return;
    
    // Format date as user-friendly string
    const formattedDate = date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
    
    // Add user message showing selected date
    setMessages(prev => [...prev, {
      type: 'user',
      content: formattedDate,
      timestamp: formatTime(new Date())
    }]);
    
    // Update appointment flow with date
    const newFlow = { ...appointmentFlow };
    newFlow.data.date = formattedDate;
    newFlow.step = 3;
    setAppointmentFlow(newFlow);
    
    // Clear selected date
    setSelectedDate(null);
    
    // Add bot response for time
    setTimeout(() => {
      setMessages(prev => [...prev, {
        type: 'bot',
        content: 'What time would you prefer? (e.g., 10:00 AM, 2:30 PM)',
        timestamp: formatTime(new Date())
      }]);
    }, 300);
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isTyping) return;

    const currentInput = inputMessage.trim();
    
    // Check for appointment booking trigger
    const appointmentTriggers = ['book appointment', 'book an appointment', 'make appointment', 'schedule appointment'];
    const isAppointmentRequest = appointmentTriggers.some(trigger => 
      currentInput.toLowerCase().includes(trigger)
    );
    
    if (isAppointmentRequest && !appointmentFlow.active) {
      const userMsg = createMessage('user', inputMessage);
      setMessages(prev => [...prev, userMsg]);
      setInputMessage('');
      setIsTyping(true);
      
      setTimeout(() => {
        setMessages(prev => [...prev, {
          type: 'bot',
          content: 'I\'ll help you book an appointment. Please provide your full name:',
          timestamp: formatTime(new Date())
        }]);
        setAppointmentFlow({ active: true, step: 0, data: { name: '', phone: '', date: '', time: '', reason: '' } });
        setIsTyping(false);
      }, 500);
      return;
    }

    const userMsg = createMessage('user', inputMessage);
    setMessages(prev => [...prev, userMsg]);
    setMessageCount(prev => prev + 1);
    
    setInputMessage('');
    setIsTyping(true);
    
    try {
      // Handle appointment booking flow
      if (appointmentFlow.active) {
        const newFlow = { ...appointmentFlow };
        
        switch (appointmentFlow.step) {
          case 0: // Name
            newFlow.data.name = currentInput;
            newFlow.step = 1;
            setAppointmentFlow(newFlow);
            setMessages(prev => [...prev, {
              type: 'bot',
              content: 'Great! What\'s your phone number?',
              timestamp: formatTime(new Date())
            }]);
            setIsTyping(false);
            return;
            
          case 1: // Phone
            if (!/^[\d\s\-\+\(\)]{8,}$/.test(currentInput)) {
              setMessages(prev => [...prev, {
                type: 'bot',
                content: 'Please enter a valid phone number (e.g., 9876543210 or +91 98765 43210)',
                timestamp: formatTime(new Date())
              }]);
              setIsTyping(false);
              return;
            }
            newFlow.data.phone = currentInput;
            newFlow.step = 2;
            setAppointmentFlow(newFlow);
            setMessages(prev => [...prev, {
              type: 'bot',
              content: 'When would you like to schedule your appointment? (e.g., tomorrow, 25/10/2025, next Monday)',
              timestamp: formatTime(new Date())
            }]);
            setIsTyping(false);
            return;
            
          case 2: // Date
            newFlow.data.date = currentInput;
            newFlow.step = 3;
            setAppointmentFlow(newFlow);
            setMessages(prev => [...prev, {
              type: 'bot',
              content: 'What time works best for you? (e.g., 10:00 AM, 3:30 PM, morning, afternoon)',
              timestamp: formatTime(new Date())
            }]);
            setIsTyping(false);
            return;
            
          case 3: // Time
            newFlow.data.time = currentInput;
            newFlow.step = 4;
            setAppointmentFlow(newFlow);
            setMessages(prev => [...prev, {
              type: 'bot',
              content: 'What is the reason for your visit? (e.g., general checkup, consultation, follow-up)',
              timestamp: formatTime(new Date())
            }]);
            setIsTyping(false);
            return;
            
          case 4: // Reason - Final step
            newFlow.data.reason = currentInput;
            
            // Book the appointment
            try {
              const response = await api.bookAppointment(newFlow.data);
              setMessages(prev => [...prev, {
                type: 'bot',
                content: response.response || 'Your appointment has been submitted to our team. You will be contacted shortly for confirmation.',
                timestamp: formatTime(new Date())
              }]);
              
              if (response.is_appointment_request) {
                setNotifications(prev => [{
                  id: `local-${Date.now()}`,
                  title: 'Appointment Booked',
                  message: `Appointment for ${newFlow.data.name} on ${newFlow.data.date}`,
                  type: 'appointment_request',
                  read: false,
                  created_at: new Date().toISOString()
                }, ...(prev || [])]);
                setUnreadNotifications(prev => (prev || 0) + 1);
              }
            } catch (error) {
              setMessages(prev => [...prev, {
                type: 'bot',
                content: 'Sorry, there was an error booking your appointment. Please try again or contact us directly.',
                timestamp: formatTime(new Date())
              }]);
            }
            
            // Reset flow
            setAppointmentFlow({
              active: false,
              step: 0,
              data: { name: '', phone: '', date: '', time: '', reason: '' }
            });
            setIsTyping(false);
            return;
        }
      }
      
      // Normal chat flow
      const response = await api.sendMessage(currentInput, userRole);
      const botMsg = createMessage('bot', response.response || 'No response generated.');
      
      // Add appointment button fields if backend suggests it
      if (response.show_appointment_button) {
        botMsg.showAppointmentButton = true;
        botMsg.suggestedReason = response.suggested_reason || '';
      }
      
      setMessages(prev => [...prev, botMsg]);
      
      if (response.is_appointment_request) {
        setNotifications(prev => [{
          id: `local-${Date.now()}`,
          title: 'Appointment Request Captured',
          message: `We saved your request. Reference: ${response.appointment_id || 'N/A'}`,
          type: 'appointment_request',
          read: false,
          created_at: new Date().toISOString()
        }, ...(prev || [])]);
        setUnreadNotifications(prev => (prev || 0) + 1);
      }
    } catch (error) {
      setMessages(prev => [...prev, {
        type: 'bot',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: formatTime(new Date())
      }]);
    } finally {
      setIsTyping(false);
    }
  };

  const loadDocuments = async () => {
    try {
      const response = await api.getDocuments();
      setDocuments(response.documents || []);
    } catch (error) {
      console.error('Failed to load documents:', error);
    }
  };

  const loadSystemStatus = async () => {
    try {
      const status = await api.getSystemStatus();
      setSystemStatus(status);
    } catch (error) {
      console.error('Failed to load system status:', error);
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.type === 'application/pdf') {
        setUploadFile(file);
      } else {
        alert('Please select a PDF file only.');
        e.target.value = '';
      }
    }
  };

  const removeSelectedFile = () => {
    setUploadFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleFileUpload = async () => {
    if (!uploadFile || uploading) return;
    
    setUploading(true);
    setUploadProgress(0);
    
    if (uploadIntervalRef.current) {
      clearInterval(uploadIntervalRef.current);
    }
    
    uploadIntervalRef.current = setInterval(() => {
      setUploadProgress(prev => {
        if (prev >= 90) {
          if (uploadIntervalRef.current) {
            clearInterval(uploadIntervalRef.current);
          }
          return 90;
        }
        return prev + 10;
      });
    }, 200);
    
    try {
      const response = await api.uploadDocument(uploadFile);
      
      setUploadProgress(100);
      
      setMessages(prev => [...prev, {
        type: 'bot',
        content: (
          <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Icons.Check />
            Document "{uploadFile.name}" uploaded successfully!
          </span>
        ),
        timestamp: formatTime(new Date())
      }]);
      
      setUploadFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      
      await loadDocuments();
      await loadSystemStatus();
      
    } catch (error) {
      setMessages(prev => [...prev, {
        type: 'bot',
        content: (
          <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Icons.Error />
            Upload failed: {error.message}
          </span>
        ),
        timestamp: formatTime(new Date())
      }]);
    } finally {
      if (uploadIntervalRef.current) {
        clearInterval(uploadIntervalRef.current);
      }
      setTimeout(() => {
        setUploading(false);
        setUploadProgress(0);
      }, 1000);
    }
  };

  const handleReloadDocuments = async () => {
    setLoading(true);
    
    try {
      await api.reloadDocuments();
      setMessages(prev => [...prev, {
        type: 'bot',
        content: (
          <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Icons.Reload />
            Documents reloaded successfully!
          </span>
        ),
        timestamp: formatTime(new Date())
      }]);
      await loadDocuments();
      await loadSystemStatus();
    } catch (error) {
      setMessages(prev => [...prev, {
        type: 'bot',
        content: (
          <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Icons.Error />
            Reload failed: {error.message}
          </span>
        ),
        timestamp: formatTime(new Date())
      }]);
    } finally {
      setLoading(false);
    }
  };

  // Admin data loaders
  const loadChatHistory = async () => {
    try {
      const response = await api.getChatHistory(historyFilter === 'all' ? null : historyFilter);
      setChatHistory(response.history || []);
    } catch (error) {
      console.error('Failed to load chat history:', error);
    }
  };

  const loadAppointments = async (statusOverride = null) => {
    try {
      const response = await api.getAppointments(statusOverride ?? appointmentFilter);
      setAppointments(response.appointments || []);
    } catch (error) {
      console.error('Failed to load appointments:', error);
    }
  };

  const loadStatistics = async () => {
    try {
      const stats = await api.getStatistics();
      setStatistics(stats);
    } catch (error) {
      console.error('Failed to load statistics:', error);
    }
  };

  const loadNotifications = async () => {
    try {
      const response = await api.getNotifications();
      setNotifications(response.notifications || []);
      const unread = (response.notifications || []).filter(n => !n.read).length;
      setUnreadNotifications(unread);
    } catch (error) {
      console.error('Failed to load notifications:', error);
    }
  };

  const handleMarkNotificationRead = async (notificationId) => {
    try {
      await api.markNotificationRead(notificationId);
      await loadNotifications();
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  };

  const handleAppointmentAction = async (appointmentId, action) => {
    const notes = action === 'accept'
      ? prompt('Add notes (optional):')
      : prompt('Reason for rejection (optional):');
    if (notes === null) return;
    try {
      await api.handleAppointment(appointmentId, action, notes || '');
      await loadAppointments();
      await loadStatistics();
      await loadNotifications();
      alert(`Appointment ${action}ed successfully!`);
    } catch (error) {
      alert(`Failed to ${action} appointment: ${error.message}`);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (showRoleSelector) {
    return (
      <div style={styles.loginContainer}>
        <div style={styles.loginCard}>
          <div style={styles.hospitalLogo}>
            <div style={styles.logoIcon}>
              <Icons.HospitalLarge />
            </div>
            <div style={styles.logoText}>
              <h2 style={styles.logoTitle}>Hospital AI Assistant</h2>
              <p style={styles.logoSubtitle}>Select your role to continue</p>
            </div>
          </div>
          
          <div style={{...styles.connectionStatus, ...styles[connectionStatus]}}>
            <Icons.StatusDot status={
              connectionStatus === 'connected' ? 'success' :
              connectionStatus === 'error' ? 'error' : 'warning'
            } />
            {connectionStatus === 'connecting' && 'Connecting...'}
            {connectionStatus === 'connected' && 'Connected'}
            {connectionStatus === 'error' && 'Connection Error'}
          </div>
          
          <div style={styles.roleButtons}>
            <button 
              style={styles.roleButton}
              onClick={() => handleRoleSelection('visitor')}
              disabled={connectionStatus === 'error'}
            >
              <div style={styles.roleIcon}>🚶</div>
              <div>
                <h3 style={styles.roleTitle}>Visitor</h3>
                <p style={styles.roleDesc}>Visiting hours, directions</p>
              </div>
            </button>

            <button 
              style={styles.roleButton}
              onClick={() => handleRoleSelection('staff')}
              disabled={connectionStatus === 'error'}
            >
              <div style={styles.roleIcon}>👨‍⚕️</div>
              <div>
                <h3 style={styles.roleTitle}>Staff</h3>
                <p style={styles.roleDesc}>General inquiries, protocols</p>
              </div>
            </button>

            <button 
              style={styles.roleButton}
              onClick={() => handleRoleSelection('admin')}
              disabled={connectionStatus === 'error'}
            >
              <div style={styles.roleIcon}>⚙️</div>
              <div>
                <h3 style={styles.roleTitle}>Admin</h3>
                <p style={styles.roleDesc}>Manage documents, system</p>
              </div>
            </button>
          </div>
          
          {connectionStatus === 'error' && (
            <div style={styles.connectionError}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Icons.Error />
                Cannot connect to server. Please ensure backend is running.
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <>
      <style>{`
        /* Ultra-compact header for mobile browsers */
        @media (max-width: 768px) {
          .chatbot-header {
            padding: 6px 10px !important;
            padding-top: max(6px, env(safe-area-inset-top, 6px)) !important;
            min-height: 50px !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
          }
          
          .header-content {
            gap: 10px !important;
          }
          
          .header-logo-icon {
            width: 36px !important;
            height: 36px !important;
            font-size: 16px !important;
            border-radius: 8px !important;
          }
          
          .header-title {
            font-size: 14px !important;
            line-height: 1.2 !important;
            font-weight: 600 !important;
            white-space: nowrap !important;
          }
          
          .header-subtitle {
            display: none !important;
          }
          
          .header-controls {
            gap: 6px !important;
          }
          
          .user-role-badge {
            padding: 4px 8px !important;
            font-size: 11px !important;
            border-radius: 5px !important;
          }
          
          .switch-role-btn {
            padding: 7px 10px !important;
            font-size: 12px !important;
            border-radius: 6px !important;
            white-space: nowrap !important;
          }
          
          .admin-panel-btn {
            padding: 7px 8px !important;
            font-size: 12px !important;
            min-width: 36px !important;
            border-radius: 6px !important;
          }
          
          .admin-panel-btn span {
            display: none !important;
          }
          
          .admin-panel-btn svg {
            width: 20px !important;
            height: 20px !important;
          }
        }
        
        /* Extra small phones */
        @media (max-width: 480px) {
          .chatbot-header {
            padding: 5px 8px !important;
            padding-top: max(5px, env(safe-area-inset-top, 5px)) !important;
            min-height: 46px !important;
          }
          
          .header-logo-icon {
            width: 32px !important;
            height: 32px !important;
            font-size: 14px !important;
            border-radius: 6px !important;
          }
          
          .header-title {
            font-size: 13px !important;
          }
          
          .user-role-badge {
            padding: 3px 6px !important;
            font-size: 10px !important;
          }
          
          .switch-role-btn {
            padding: 6px 8px !important;
            font-size: 11px !important;
          }
          
          .admin-panel-btn {
            padding: 6px 7px !important;
            min-width: 32px !important;
          }
          
          .admin-panel-btn svg {
            width: 18px !important;
            height: 18px !important;
          }
        }
        
        /* Force minimal height on all screen sizes */
        .chatbot-header {
          flex-shrink: 0 !important;
        }
      `}</style>
      <div style={styles.chatbotContainer}>
        <div style={styles.chatbotHeader} className="chatbot-header">
          <div style={styles.headerContent} className="header-content">
            <div style={styles.hospitalLogo}>
              <div style={styles.logoIconSmall} className="header-logo-icon">
                <Icons.Hospital />
              </div>
              <div style={styles.logoText}>
                <h3 style={styles.headerTitle} className="header-title">Hospital AI Assistant</h3>
                <p style={styles.headerSubtitle} className="header-subtitle">24/7 Healthcare Support</p>
              </div>
            </div>
            <div style={styles.headerControls} className="header-controls">
              <div style={styles.userInfo}>
                <span style={styles.userRole} className="user-role-badge">{userRole}</span>
              </div>
              {userRole === 'admin' && (
                <button 
                  style={styles.adminPanelBtn}
                  className="admin-panel-btn"
                  onClick={() => {
                    setShowAdminModal(true);
                    loadDocuments();
                    loadSystemStatus();
                  }}
                >
                  <Icons.Dashboard />
                  <span>Dashboard</span>
                </button>
              )}
              <button 
                style={styles.logoutBtn} 
                className="switch-role-btn"
                onClick={() => {
                  setShowRoleSelector(true);
                  setMessages([]);
                  setMessageCount(0);
                }}
              >
                Switch Role
              </button>
            </div>
          </div>
        </div>

        <div style={styles.chatMessages}>
          {messages.map((message, index) => (
            <div key={message.id || `msg-${index}-${message.timestamp}`} style={{...styles.message, ...(message.type === 'user' ? styles.messageUser : styles.messageBot)}}>
              <div style={styles.messageContent}>
                {typeof message.content === 'string' ? (
                  <FormattedMessage key={`fmt-${message.id || index}`} content={message.content} />
                ) : (
                  message.content
                )}
              </div>
              <div style={styles.messageTime}>{message.timestamp}</div>
              
              {/* Show appointment booking button if suggested by backend */}
              {message.showAppointmentButton && message.type === 'bot' && (
                <button
                  style={styles.inlineAppointmentBtn}
                  onClick={() => {
                    const suggestedReason = message.suggestedReason || '';
                    setAppointmentFlow({
                      active: true,
                      step: 0,
                      data: { name: '', phone: '', date: '', time: '', reason: suggestedReason }
                    });
                    setMessages(prev => [...prev, {
                      type: 'bot',
                      content: `Great! Let's book your appointment${suggestedReason ? ` for ${suggestedReason.toLowerCase()}` : ''}.\n\nFirst, what's your name?`,
                      timestamp: formatTime(new Date())
                    }]);
                  }}
                >
                  📅 Book Appointment
                </button>
              )}
            </div>
          ))}
          
          {isTyping && (
            <div style={{...styles.message, ...styles.messageBot}}>
              <div style={styles.messageContent}>
                <div style={styles.typingIndicator}>
                  <span style={styles.typingDot}></span>
                  <span style={{...styles.typingDot, animationDelay: '0.2s'}}></span>
                  <span style={{...styles.typingDot, animationDelay: '0.4s'}}></span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {appointmentFlow.active && (
          <div style={styles.appointmentFlowBanner}>
            <div style={styles.flowProgress}>
              <span style={styles.flowIcon}>📅</span>
              <div style={styles.flowInfo}>
                <strong>Booking Appointment - Step {appointmentFlow.step + 1} of 5</strong>
                <div style={styles.flowSteps}>
                  {['Name', 'Phone', 'Date', 'Time', 'Reason'].map((step, idx) => (
                    <span 
                      key={idx}
                      style={{
                        ...styles.flowStep,
                        ...(idx === appointmentFlow.step ? styles.flowStepActive : {}),
                        ...(idx < appointmentFlow.step ? styles.flowStepComplete : {})
                      }}
                    >
                      {idx < appointmentFlow.step ? '✓' : idx + 1}
                    </span>
                  ))}
                </div>
              </div>
            </div>
            <button 
              style={styles.flowCancelBtn}
              onClick={() => {
                setAppointmentFlow({ active: false, step: 0, data: {} });
                setSelectedDate(null);
                addMessage('Appointment booking cancelled. How else can I help you?', 'bot');
              }}
            >
              Cancel
            </button>
          </div>
        )}

        {appointmentFlow.active && appointmentFlow.step === 2 && (
          <div style={styles.datePickerContainer}>
            <div style={styles.datePickerLabel}>
              Select your preferred appointment date:
            </div>
            <DatePicker
              selected={selectedDate}
              onChange={handleDateSelect}
              minDate={new Date()}
              inline
              calendarClassName="custom-calendar"
              dateFormat="MMMM d, yyyy"
            />
            <div style={styles.datePickerHint}>
              Or type your preferred date below (e.g., "tomorrow", "next Monday")
            </div>
          </div>
        )}

        <div style={styles.chatInput}>
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage();
              }
            }}
            placeholder={
              appointmentFlow.active 
                ? ['Enter your full name...', 'Enter your phone number...', 'Enter preferred date (e.g., 2024-12-25)...', 'Enter preferred time (e.g., 10:00 AM)...', 'Enter reason for appointment...'][appointmentFlow.step]
                : 'Type your message...'
            }
            style={styles.messageInput}
            disabled={isTyping}
            rows={1}
          />
          <button 
            onClick={handleSendMessage} 
            style={{...styles.sendButton, ...(!inputMessage.trim() || isTyping ? styles.sendButtonDisabled : {})}}
            disabled={!inputMessage.trim() || isTyping}
          >
            {isTyping ? (
              <div style={styles.loadingSpinner}></div>
            ) : (
              <Icons.Send />
            )}
          </button>
        </div>
      </div>

      {showAdminModal && (
        <div style={styles.modalOverlay} onClick={(e) => {
          if (e.target === e.currentTarget) setShowAdminModal(false);
        }}>
          <div style={styles.modalContainer}>
            <div style={styles.modalHeader}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <Icons.Settings />
                <h2 style={styles.modalTitle}>Admin Dashboard</h2>
              </div>
              <button 
                style={styles.modalClose}
                onClick={() => setShowAdminModal(false)}
              >
                <Icons.Close />
              </button>
            </div>
            <div style={styles.adminTabs}>
              <button 
                style={{...styles.tabBtn, ...(adminTab === 'dashboard' ? styles.tabBtnActive : {})}}
                onClick={() => setAdminTab('dashboard')}
              >
                Dashboard
              </button>
              <button 
                style={{...styles.tabBtn, ...(adminTab === 'appointments' ? styles.tabBtnActive : {})}}
                onClick={() => { setAdminTab('appointments'); loadAppointments(); loadStatistics(); }}
              >
                Appointments {statistics.pending_appointments > 0 && (<span style={styles.badge}>{statistics.pending_appointments}</span>)}
              </button>
              <button 
                style={{...styles.tabBtn, ...(adminTab === 'history' ? styles.tabBtnActive : {})}}
                onClick={() => { setAdminTab('history'); loadChatHistory(); }}
              >
                Chat History
              </button>
              <button 
                style={{...styles.tabBtn, ...(adminTab === 'notifications' ? styles.tabBtnActive : {})}}
                onClick={() => { setAdminTab('notifications'); loadNotifications(); }}
              >
                Notifications {unreadNotifications > 0 && (<span style={styles.badge}>{unreadNotifications}</span>)}
              </button>
            </div>
            
            <div style={styles.modalContent}>
              {adminTab === 'dashboard' && (
              <>
              <div style={styles.adminCard}>
                <h3 style={styles.cardTitle}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Icons.Analysis />
                    System Status
                  </div>
                </h3>
                <div style={styles.statusGrid}>
                  <div style={styles.statusItem}>
                    <span>Firebase:</span>
                    <span style={systemStatus.firebase_initialized ? styles.statusSuccess : styles.statusError}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        {systemStatus.firebase_initialized ? <Icons.Check /> : <Icons.Error />}
                        {systemStatus.firebase_initialized ? 'Connected' : 'Disconnected'}
                      </div>
                    </span>
                  </div>
                  <div style={styles.statusItem}>
                    <span>Documents:</span>
                    <span style={styles.statusSuccess}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <Icons.Document />
                        {systemStatus.documents_loaded || 0} loaded
                      </div>
                    </span>
                  </div>
                  <div style={styles.statusItem}>
                    <span>Vector Store:</span>
                    <span style={systemStatus.vectorstore_ready ? styles.statusSuccess : styles.statusError}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        {systemStatus.vectorstore_ready ? <Icons.Check /> : <Icons.Error />}
                        {systemStatus.vectorstore_ready ? 'Ready' : 'Not Ready'}
                      </div>
                    </span>
                  </div>
                </div>
              </div>

              <div style={styles.adminCard}>
                <h3 style={styles.cardTitle}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Icons.Upload />
                    Upload Document
                  </div>
                </h3>
                <div 
                  style={{...styles.uploadArea, ...(dragOver ? styles.uploadAreaDragOver : {})}}
                  onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                  onDragLeave={(e) => { e.preventDefault(); setDragOver(false); }}
                  onDrop={(e) => {
                    e.preventDefault();
                    setDragOver(false);
                    const files = e.dataTransfer.files;
                    if (files.length > 0 && files[0].type === 'application/pdf') {
                      setUploadFile(files[0]);
                    }
                  }}
                  onClick={() => fileInputRef.current?.click()}
                >
                  <Icons.FileUpload />
                  <p style={styles.uploadText}>Drag & Drop PDF, Excel, or CSV files or Click to Browse</p>
                </div>

                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.csv,.xlsx,.xls"
                  onChange={handleFileSelect}
                  style={styles.fileInput}
                />

                {uploadFile && (
                  <div style={styles.selectedFile}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Icons.Document />
                      <span>{uploadFile.name} ({formatFileSize(uploadFile.size)})</span>
                    </div>
                    <button onClick={removeSelectedFile} style={styles.removeFileBtn}>
                      <Icons.Remove />
                    </button>
                  </div>
                )}

                <button 
                  onClick={handleFileUpload}
                  disabled={!uploadFile || uploading}
                  style={{...styles.uploadBtn, ...(!uploadFile || uploading ? styles.uploadBtnDisabled : {})}}
                >
                  {uploading ? (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <div style={styles.loadingSpinner}></div>
                      Uploading {uploadProgress}%
                    </div>
                  ) : (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Icons.Upload />
                      Upload PDF
                    </div>
                  )}
                </button>

                {uploading && (
                  <div style={styles.progressBar}>
                    <div style={{...styles.progressFill, width: `${uploadProgress}%`}}></div>
                  </div>
                )}
              </div>

              <div style={styles.adminCard}>
                <div style={styles.cardHeader}>
                  <h3 style={styles.cardTitle}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Icons.Document />
                      Documents ({documents.length})
                    </div>
                  </h3>
                  <button onClick={handleReloadDocuments} style={styles.reloadBtn}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <Icons.Reload />
                      Reload
                    </div>
                  </button>
                </div>
                <div style={styles.documentsList}>
                  {documents.length === 0 ? (
                    <p style={styles.noDocuments}>No documents uploaded yet</p>
                  ) : (
                    documents.map((doc, index) => (
                      <div key={index} style={styles.documentItem}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <Icons.Document />
                          <span>{doc.name}</span>
                        </div>
                        <span style={styles.docSize}>{formatFileSize(doc.size)}</span>
                      </div>
                    ))
                  )}
                </div>
              </div>
              </>
              )}

              {adminTab === 'appointments' && (
                <>
                  <div style={styles.statsGrid}>
                    <div style={styles.statCard}><div style={styles.statIcon}>📊</div><div><div style={styles.statValue}>{statistics.total_conversations || 0}</div><div style={styles.statLabel}>Total Chats</div></div></div>
                    <div style={styles.statCard}><div style={styles.statIcon}>⏳</div><div><div style={styles.statValue}>{statistics.pending_appointments || 0}</div><div style={styles.statLabel}>Pending</div></div></div>
                    <div style={styles.statCard}><div style={styles.statIcon}>✅</div><div><div style={styles.statValue}>{statistics.accepted_appointments || 0}</div><div style={styles.statLabel}>Accepted</div></div></div>
                    <div style={styles.statCard}><div style={styles.statIcon}>❌</div><div><div style={styles.statValue}>{statistics.rejected_appointments || 0}</div><div style={styles.statLabel}>Rejected</div></div></div>
                  </div>
                  <div style={styles.adminCard}>
                    <div style={styles.cardHeader}>
                      <h3 style={styles.cardTitle}>Appointment Requests</h3>
                      <select 
                        value={appointmentFilter}
                        onChange={(e) => { const v = e.target.value; setAppointmentFilter(v); loadAppointments(v); }}
                        style={styles.filterSelect}
                      >
                        <option value="pending">Pending</option>
                        <option value="accepted">Accepted</option>
                        <option value="rejected">Rejected</option>
                      </select>
                    </div>
                    <div style={styles.appointmentsList}>
                      {appointments.length === 0 ? (
                        <p style={styles.noData}>No {appointmentFilter} appointments</p>
                      ) : (
                        appointments.map((apt, index) => (
                          <div key={index} style={styles.appointmentCard}>
                            <div style={styles.appointmentHeader}>
                              <div>
                                <h4 style={styles.appointmentName}>Appointment Request</h4>
                                <span style={{...styles.appointmentBadge,
                                  background: apt.status === 'pending' ? '#fff3cd' : apt.status === 'accepted' ? '#d4edda' : '#f8d7da',
                                  color: apt.status === 'pending' ? '#856404' : apt.status === 'accepted' ? '#155724' : '#721c24'
                                }}>{apt.status}</span>
                              </div>
                              <span style={styles.appointmentTime}>{formatDateTime(apt.created_at)}</span>
                            </div>
                            <div style={styles.appointmentDetails}>
                              {apt.phone_number && apt.phone_number !== 'Not provided' && (
                                <div style={styles.appointmentRow}>
                                  <span>�</span>
                                  <a href={`tel:${apt.phone_number.replace(/\s/g, '')}`} style={styles.phoneLink}>
                                    {apt.phone_number}
                                  </a>
                                </div>
                              )}
                              <div style={styles.appointmentRow}><span>�📅</span><span>{apt.preferred_date} at {apt.preferred_time}</span></div>
                              <div style={styles.appointmentReason}><strong>Reason:</strong> {apt.reason}</div>
                              <div style={styles.appointmentMessage}><strong>Original Message:</strong> {apt.original_message}</div>
                              {apt.admin_notes && (<div style={styles.adminNotes}><strong>Admin Notes:</strong> {apt.admin_notes}</div>)}
                            </div>
                            {apt.status === 'pending' && (
                              <div style={styles.appointmentActions}>
                                {apt.phone_number && apt.phone_number !== 'Not provided' ? (
                                  <a href={`tel:${apt.phone_number.replace(/\s/g, '')}`} style={styles.acceptBtnLink}>
                                    <button style={styles.acceptBtn} onClick={(e) => { 
                                      handleAppointmentAction(apt.appointment_id, 'accept');
                                    }}>✅ Accept & Call</button>
                                  </a>
                                ) : (
                                  <button style={styles.acceptBtn} onClick={() => handleAppointmentAction(apt.appointment_id, 'accept')}>✅ Accept</button>
                                )}
                                <button style={styles.rejectBtn} onClick={() => handleAppointmentAction(apt.appointment_id, 'reject')}>❌ Reject</button>
                              </div>
                            )}
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                </>
              )}

              {adminTab === 'history' && (
                <div style={styles.adminCard}>
                  <div style={styles.cardHeader}>
                    <h3 style={styles.cardTitle}>Chat History</h3>
                    <select 
                      value={historyFilter}
                      onChange={(e) => { setHistoryFilter(e.target.value); setTimeout(() => loadChatHistory(), 100); }}
                      style={styles.filterSelect}
                    >
                      <option value="all">All Roles</option>
                      <option value="visitor">Visitors</option>
                      <option value="staff">Staff</option>
                      <option value="admin">Admins</option>
                    </select>
                  </div>
                  <div style={styles.historyList}>
                    {chatHistory.length === 0 ? (
                      <p style={styles.noData}>No chat history available</p>
                    ) : (
                      chatHistory.map((chat, index) => (
                        <div key={index} style={styles.historyCard}>
                          <div style={styles.historyHeader}>
                            <div style={styles.historyUserInfo}>
                              <strong style={styles.historyUser}>{chat.user_id || 'Anonymous'}</strong>
                              <span style={styles.historyRole}>{chat.user_role}</span>
                              {chat.is_appointment_request && (<span style={styles.appointmentTag}>📅 Appointment</span>)}
                            </div>
                            <span style={styles.historyTime}>{formatDateTime(chat.created_at)}</span>
                          </div>
                          <div style={styles.historyMessage}>
                            <div style={styles.historyQuestion}><strong>Q:</strong> {chat.message}</div>
                            <div style={styles.historyAnswer}><strong>A:</strong> {chat.response}</div>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}

              {adminTab === 'notifications' && (
                <div style={styles.adminCard}>
                  <div style={styles.cardHeader}>
                    <h3 style={styles.cardTitle}>Notifications ({notifications.length})</h3>
                    <button onClick={loadNotifications} style={styles.reloadBtn}>↻ Refresh</button>
                  </div>
                  <div style={styles.notificationsList}>
                    {notifications.length === 0 ? (
                      <p style={styles.noData}>No notifications</p>
                    ) : (
                      notifications.map((n, index) => (
                        <div key={index}
                             style={{ ...styles.notificationCard, background: n.read ? '#f8f9fa' : '#e8f1ff' }}
                             onClick={() => !n.read && handleMarkNotificationRead(n.id)}>
                          <div style={styles.notificationHeader}>
                            <h4 style={styles.notificationTitle}>{n.title}</h4>
                            {!n.read && (<span style={styles.unreadBadge}>New</span>)}
                          </div>
                          <p style={styles.notificationMessage}>{n.message}</p>
                          <div style={styles.notificationTime}>{formatDateTime(n.created_at)}</div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
};

const styles = {
  loginContainer: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: '100vh',
    background: 'linear-gradient(135deg, #2E4AC7 0%, #1F3A9E 100%)',
    padding: '20px'
  },
  loginCard: {
    background: 'white',
    borderRadius: '20px',
    padding: '40px',
    width: '100%',
    maxWidth: '550px',
    boxShadow: '0 20px 60px rgba(0,0,0,0.3)'
  },
  hospitalLogo: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    marginBottom: '30px',
    flex: '1 1 auto',
    minWidth: '0'
  },
  logoIcon: {
    width: '60px',
    height: '60px',
    background: 'linear-gradient(135deg, #2E4AC7 0%, #1F3A9E 100%)',
    borderRadius: '15px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: 'white',
    fontSize: '24px',
    fontWeight: 'bold'
  },
  logoIconSmall: {
    width: '40px',
    height: '40px',
    background: 'linear-gradient(135deg, #2E4AC7 0%, #1F3A9E 100%)',
    borderRadius: '10px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: 'white',
    fontSize: '16px',
    fontWeight: 'bold',
    flexShrink: 0
  },
  logoText: {
    flex: 1,
    minWidth: 0,
    display: 'flex',
    flexDirection: 'column',
    gap: '2px'
  },
  logoTitle: {
    margin: 0,
    fontSize: '24px',
    color: '#2d3748'
  },
  logoSubtitle: {
    margin: '5px 0 0 0',
    color: '#718096',
    fontSize: '14px'
  },
  connectionStatus: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '12px 16px',
    borderRadius: '10px',
    fontSize: '14px',
    marginBottom: '20px',
    fontWeight: '500'
  },
  connecting: {
    background: '#fef3c7',
    color: '#92400e'
  },
  connected: {
    background: '#d1fae5',
    color: '#065f46'
  },
  error: {
    background: '#fee2e2',
    color: '#991b1b'
  },
  roleButtons: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
    marginTop: '20px'
  },
  roleButton: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
    padding: '18px 20px',
    background: 'linear-gradient(135deg, #fafcff 0%, #f5f9ff 100%)',
    border: '2px solid #e8f1ff',
    borderRadius: '14px',
    cursor: 'pointer',
    transition: 'all 0.3s',
    textAlign: 'left',
    width: '100%',
    fontFamily: 'inherit'
  },
  roleIcon: {
    fontSize: '32px',
    width: '50px',
    height: '50px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'linear-gradient(135deg, #2E4AC7 0%, #1F3A9E 100%)',
    borderRadius: '12px',
    flexShrink: 0
  },
  roleTitle: {
    margin: 0,
    fontSize: '18px',
    color: '#2d3748',
    fontWeight: '600'
  },
  roleDesc: {
    margin: '4px 0 0 0',
    fontSize: '13px',
    color: '#718096'
  },
  connectionError: {
    marginTop: '15px',
    padding: '12px 16px',
    background: '#fee2e2',
    color: '#991b1b',
    borderRadius: '10px',
    fontSize: '14px'
  },
  chatbotContainer: {
    display: 'flex',
    flexDirection: 'column',
    height: '100dvh',
    background: '#f7fafc',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    maxWidth: '100vw',
    overflow: 'hidden'
  },
  chatbotHeader: {
    background: 'linear-gradient(135deg, #2E4AC7 0%, #1F3A9E 100%)',
    color: 'white',
    padding: '12px 15px',
    boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
    paddingTop: 'max(12px, env(safe-area-inset-top))',
    position: 'sticky',
    top: 0,
    zIndex: 100
  },
  headerContent: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: '8px',
    maxWidth: '100%'
  },
  headerTitle: {
    margin: 0,
    fontSize: 'clamp(15px, 3.5vw, 20px)',
    lineHeight: '1.2'
  },
  headerSubtitle: {
    margin: '3px 0 0 0',
    fontSize: 'clamp(10px, 2.5vw, 13px)',
    opacity: 0.9,
    lineHeight: '1.2'
  },
  headerControls: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    flexWrap: 'wrap'
  },
  userInfo: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'flex-end',
    gap: '4px'
  },
  userRole: {
    fontSize: 'clamp(12px, 3vw, 14px)',
    fontWeight: '600',
    textTransform: 'capitalize',
    padding: '6px 10px',
    background: 'rgba(255,255,255,0.2)',
    borderRadius: '8px'
  },
  adminPanelBtn: {
    padding: '8px 12px',
    background: 'rgba(255,255,255,0.2)',
    border: '1px solid rgba(255,255,255,0.3)',
    color: 'white',
    borderRadius: '8px',
    cursor: 'pointer',
    fontSize: 'clamp(12px, 3vw, 14px)',
    fontWeight: '500',
    transition: 'all 0.3s',
    display: 'flex',
    alignItems: 'center',
    gap: '6px'
  },
  logoutBtn: {
    padding: '8px 12px',
    background: 'rgba(255,255,255,0.9)',
    border: 'none',
    color: '#1F3A9E',
    borderRadius: '8px',
    cursor: 'pointer',
    fontSize: 'clamp(12px, 3vw, 14px)',
    fontWeight: 'bold',
    transition: 'all 0.3s'
  },
  chatMessages: {
    flex: 1,
    overflowY: 'auto',
    padding: '15px',
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
    background: 'linear-gradient(135deg, #fafcff 0%, #f5f9ff 100%)',
    overflowX: 'hidden'
  },
  message: {
    maxWidth: '75%',
    padding: '12px 16px',
    borderRadius: '16px',
    animation: 'fadeIn 0.3s ease-in',
    wordWrap: 'break-word',
    wordBreak: 'break-word',
    overflowWrap: 'break-word'
  },
  messageUser: {
    alignSelf: 'flex-end',
    background: 'linear-gradient(135deg, #FF8C00 0%, #FFA500 100%)',
    color: 'white'
  },
  messageBot: {
    alignSelf: 'flex-start',
    background: 'linear-gradient(135deg, #e8f1ff 0%, #f0f8ff 100%)',
    color: '#1F3A9E',
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
    border: '1px solid #d1e4ff'
  },
  messageContent: {
    fontSize: 'clamp(13px, 3.5vw, 15px)',
    lineHeight: '1.5',
    marginBottom: '6px'
  },
  messageTime: {
    fontSize: 'clamp(10px, 2.5vw, 11px)',
    opacity: 0.7
  },
  inlineAppointmentBtn: {
    marginTop: '12px',
    padding: '12px 20px',
    background: 'linear-gradient(135deg, #FF8C00 0%, #FFA500 100%)',
    color: 'white',
    border: 'none',
    borderRadius: '10px',
    cursor: 'pointer',
    fontSize: 'clamp(13px, 3.5vw, 15px)',
    fontWeight: '600',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
    transition: 'all 0.3s',
    boxShadow: '0 4px 8px rgba(255, 140, 0, 0.3)',
    width: '100%',
    maxWidth: '250px'
  },
  typingIndicator: {
    display: 'flex',
    gap: '4px',
    alignItems: 'center'
  },
  typingDot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    background: '#2E4AC7',
    animation: 'bounce 1.4s infinite ease-in-out'
  },
  chatInput: {
    display: 'flex',
    gap: '12px',
    padding: '20px 24px',
    background: '#f7fafc',
    justifyContent: 'center',
    alignItems: 'center'
  },
  messageInput: {
    flex: 'none',
    width: '1000px',
    maxWidth: '90%',
    padding: '14px 22px',
    border: '1px solid #d0d0d0',
    borderRadius: '30px',
    fontSize: 'clamp(15px, 3.5vw, 16px)',
    resize: 'none',
    outline: 'none',
    fontFamily: 'inherit',
    maxHeight: '120px',
    transition: 'border-color 0.3s',
    background: '#f5f5f5',
    minHeight: '50px'
  },
  sendButton: {
    padding: '14px 14px',
    background: 'linear-gradient(135deg, #FF8C00 0%, #FFA500 100%)',
    color: 'white',
    border: 'none',
    borderRadius: '50%',
    cursor: 'pointer',
    fontSize: '18px',
    fontWeight: 'bold',
    transition: 'all 0.3s',
    whiteSpace: 'nowrap',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    minWidth: '52px',
    minHeight: '52px',
    width: '52px',
    height: '52px'
  },
  sendButtonDisabled: {
    opacity: 0.5,
    cursor: 'not-allowed'
  },
  loadingSpinner: {
    width: '16px',
    height: '16px',
    border: '2px solid rgba(255,255,255,0.3)',
    borderTop: '2px solid white',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite'
  },
  modalOverlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: 'rgba(0,0,0,0.5)',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    padding: '10px',
    zIndex: 1000,
    animation: 'fadeIn 0.3s ease-in'
  },
  modalContainer: {
    background: 'linear-gradient(135deg, #ffffff 0%, #f8fafe 100%)',
    borderRadius: '16px',
    width: '100%',
    maxWidth: '900px',
    maxHeight: '95vh',
    display: 'flex',
    flexDirection: 'column',
    boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
    animation: 'slideUp 0.3s ease-out'
  },
  modalHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '16px 20px',
    borderBottom: '1px solid #e2e8f0',
    background: 'linear-gradient(135deg, #2E4AC7 0%, #1F3A9E 100%)',
    color: 'white',
    borderTopLeftRadius: '16px',
    borderTopRightRadius: '16px'
  },
  modalTitle: {
    margin: 0,
    fontSize: 'clamp(18px, 4vw, 24px)',
    color: 'white',
    fontWeight: '600'
  },
  modalClose: {
    width: '40px',
    height: '40px',
    border: 'none',
    background: 'rgba(255,255,255,0.2)',
    borderRadius: '10px',
    cursor: 'pointer',
    fontSize: '18px',
    color: 'white',
    transition: 'all 0.3s',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0
  },
  modalContent: {
    flex: 1,
    overflowY: 'auto',
    padding: '20px',
    display: 'flex',
    flexDirection: 'column',
    gap: '20px',
    background: 'linear-gradient(135deg, #fafcff 0%, #f5f9ff 100%)'
  },
  adminCard: {
    background: 'linear-gradient(135deg, #ffffff 0%, #f8fafe 100%)',
    borderRadius: '12px',
    padding: '16px',
    border: '1px solid #e8f1ff'
  },
  cardTitle: {
    margin: '0 0 16px 0',
    fontSize: 'clamp(16px, 4vw, 18px)',
    color: '#1F3A9E',
    fontWeight: '600'
  },
  cardHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '20px'
  },
  statusGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
    gap: '16px'
  },
  statusItem: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '16px 20px',
    background: 'linear-gradient(135deg, #f8fafe 0%, #f0f8ff 100%)',
    borderRadius: '12px',
    fontSize: '14px',
    border: '1px solid #e8f1ff'
  },
  statusSuccess: {
    color: '#28a745',
    fontWeight: '600'
  },
  statusError: {
    color: '#dc3545',
    fontWeight: '600'
  },
  uploadArea: {
    border: '2px dashed #d1e4ff',
    borderRadius: '16px',
    padding: '48px 24px',
    textAlign: 'center',
    cursor: 'pointer',
    transition: 'all 0.3s',
    background: 'linear-gradient(135deg, #fafcff 0%, #f5f9ff 100%)'
  },
  uploadAreaDragOver: {
    borderColor: '#2E4AC7',
    background: '#eef2ff'
  },
  uploadText: {
    margin: '16px 0 0 0',
    color: '#718096',
    fontSize: '15px',
    fontWeight: '500'
  },
  fileInput: {
    display: 'none'
  },
  selectedFile: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '16px 20px',
    background: 'linear-gradient(135deg, #e8f1ff 0%, #f0f8ff 100%)',
    borderRadius: '12px',
    marginTop: '16px',
    border: '1px solid #d1e4ff'
  },
  removeFileBtn: {
    width: '32px',
    height: '32px',
    border: 'none',
    background: '#fee2e2',
    color: '#dc2626',
    borderRadius: '10px',
    cursor: 'pointer',
    fontSize: '16px',
    fontWeight: 'bold',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'all 0.3s'
  },
  uploadBtn: {
    width: '100%',
    padding: '14px 20px',
    background: 'linear-gradient(135deg, #FF8C00 0%, #FFA500 100%)',
    color: 'white',
    border: 'none',
    borderRadius: '12px',
    cursor: 'pointer',
    fontSize: '15px',
    fontWeight: 'bold',
    marginTop: '16px',
    transition: 'all 0.3s',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px'
  },
  uploadBtnDisabled: {
    opacity: 0.5,
    cursor: 'not-allowed'
  },
  progressBar: {
    width: '100%',
    height: '8px',
    background: '#e8f1ff',
    borderRadius: '4px',
    marginTop: '16px',
    overflow: 'hidden'
  },
  progressFill: {
    height: '100%',
    background: 'linear-gradient(90deg, #FF8C00, #FFA500)',
    transition: 'width 0.3s ease-in-out'
  },
  reloadBtn: {
    padding: '10px 16px',
    background: '#28a745',
    color: 'white',
    border: 'none',
    borderRadius: '10px',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: '500',
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    transition: 'all 0.3s'
  },
  documentsList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
    maxHeight: '300px',
    overflowY: 'auto'
  },
  noDocuments: {
    textAlign: 'center',
    color: '#718096',
    padding: '32px',
    fontSize: '15px'
  },
  documentItem: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '16px 20px',
    background: 'linear-gradient(135deg, #f8fafe 0%, #f0f8ff 100%)',
    borderRadius: '12px',
    border: '1px solid #e8f1ff'
  },
  docSize: {
    fontSize: '12px',
    color: '#718096',
    fontWeight: '500'
  },
  adminTabs: {
    display: 'flex',
    gap: '10px',
    padding: '12px 20px',
    borderBottom: '1px solid #e2e8f0',
    background: 'linear-gradient(135deg, #ffffff 0%, #f8fafe 100%)'
  },
  tabBtn: {
    padding: '10px 14px',
    background: '#f1f5ff',
    border: '1px solid #d1e4ff',
    color: '#1F3A9E',
    borderRadius: '10px',
    cursor: 'pointer',
    fontSize: '13px',
    fontWeight: '600'
  },
  tabBtnActive: {
    background: '#2E4AC7',
    color: 'white',
    borderColor: '#1F3A9E'
  },
  badge: {
    marginLeft: '6px',
    background: '#fff3cd',
    color: '#856404',
    borderRadius: '10px',
    padding: '2px 6px',
    fontSize: '12px',
    fontWeight: '700'
  },
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
    gap: '12px',
    marginBottom: '16px'
  },
  statCard: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    padding: '14px',
    background: 'linear-gradient(135deg, #f8fafe 0%, #f0f8ff 100%)',
    borderRadius: '12px',
    border: '1px solid #e8f1ff'
  },
  statIcon: { fontSize: '18px' },
  statValue: { fontWeight: '800', fontSize: '18px' },
  statLabel: { color: '#718096', fontSize: '12px' },
  filterSelect: {
    padding: '8px 10px',
    borderRadius: '8px',
    border: '1px solid #d1e4ff',
    background: 'white',
    color: '#1F3A9E',
    fontWeight: '600'
  },
  appointmentsList: { display: 'flex', flexDirection: 'column', gap: '12px' },
  appointmentCard: { border: '1px solid #e8f1ff', borderRadius: '12px', padding: '16px', background: '#fff' },
  appointmentHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' },
  appointmentName: { margin: 0, fontSize: '16px', color: '#1F3A9E' },
  appointmentBadge: { marginLeft: '8px', borderRadius: '8px', padding: '2px 6px', fontSize: '12px', fontWeight: '700' },
  appointmentTime: { fontSize: '12px', color: '#718096' },
  appointmentDetails: { display: 'flex', flexDirection: 'column', gap: '6px', color: '#2d3748' },
  appointmentRow: { display: 'flex', gap: '8px', alignItems: 'center' },
  phoneNumber: { fontWeight: '700', color: '#2d3748' },
  phoneLink: { 
    color: '#28a745', 
    fontWeight: '700', 
    textDecoration: 'none', 
    borderBottom: '2px dotted #28a745',
    cursor: 'pointer',
    transition: 'all 0.3s'
  },
  appointmentReason: {},
  appointmentMessage: { background: '#f8fafc', padding: '8px', borderRadius: '8px', border: '1px solid #e8f1ff' },
  adminNotes: { background: '#fffbea', padding: '8px', borderRadius: '8px', border: '1px solid #fff3cd' },
  appointmentActions: { display: 'flex', gap: '10px', marginTop: '10px', flexWrap: 'wrap' },
  acceptBtn: { padding: '8px 12px', background: '#d4edda', color: '#155724', border: '1px solid #c3e6cb', borderRadius: '8px', cursor: 'pointer', fontWeight: '700', fontSize: '14px' },
  acceptBtnLink: { textDecoration: 'none', display: 'inline-block' },
  rejectBtn: { padding: '8px 12px', background: '#f8d7da', color: '#721c24', border: '1px solid #f5c6cb', borderRadius: '8px', cursor: 'pointer', fontWeight: '700', fontSize: '14px' },
  historyList: { display: 'flex', flexDirection: 'column', gap: '12px' },
  historyCard: { border: '1px solid #e8f1ff', borderRadius: '12px', padding: '16px', background: '#fff' },
  historyHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' },
  historyUserInfo: { display: 'flex', alignItems: 'center', gap: '8px' },
  historyUser: { color: '#1F3A9E' },
  historyRole: { background: '#eef2ff', color: '#1F3A9E', borderRadius: '8px', padding: '2px 6px', fontSize: '12px', fontWeight: '700' },
  appointmentTag: { marginLeft: '8px' },
  historyTime: { fontSize: '12px', color: '#718096' },
  historyMessage: { display: 'flex', flexDirection: 'column', gap: '6px' },
  notificationsList: { display: 'flex', flexDirection: 'column', gap: '12px' },
  notificationCard: { border: '1px solid #e8f1ff', borderRadius: '12px', padding: '12px', cursor: 'pointer' },
  notificationHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
  notificationTitle: { margin: 0, color: '#1F3A9E' },
  unreadBadge: { background: '#2E4AC7', color: 'white', borderRadius: '8px', padding: '2px 6px', fontSize: '11px', fontWeight: '700' },
  notificationMessage: { margin: '8px 0', color: '#2d3748' },
  notificationTime: { fontSize: '12px', color: '#718096' },
  noData: { textAlign: 'center', color: '#718096', padding: '16px' },
  appointmentFlowBanner: {
    background: 'linear-gradient(135deg, #fff9e6 0%, #fff3cd 100%)',
    border: '2px solid #ffd966',
    borderRadius: '12px',
    padding: '12px',
    margin: '0 0 12px 0',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    boxShadow: '0 2px 8px rgba(255, 193, 7, 0.15)',
    animation: 'slideUp 0.3s ease-out',
    flexWrap: 'wrap',
    gap: '10px'
  },
  flowProgress: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    flex: '1 1 auto',
    minWidth: '200px'
  },
  flowIcon: {
    fontSize: 'clamp(20px, 5vw, 24px)',
    animation: 'bounce 1.5s infinite',
    flexShrink: 0
  },
  flowInfo: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
    minWidth: 0
  },
  flowSteps: {
    display: 'flex',
    gap: '6px',
    alignItems: 'center',
    flexWrap: 'wrap'
  },
  flowStep: {
    width: 'clamp(24px, 6vw, 28px)',
    height: 'clamp(24px, 6vw, 28px)',
    borderRadius: '50%',
    background: '#fff',
    border: '2px solid #e0e0e0',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: 'clamp(10px, 3vw, 12px)',
    fontWeight: '700',
    color: '#999',
    transition: 'all 0.3s',
    flexShrink: 0
  },
  flowStepActive: {
    background: '#2E4AC7',
    border: '2px solid #2E4AC7',
    color: 'white',
    transform: 'scale(1.1)',
    boxShadow: '0 2px 8px rgba(46, 74, 199, 0.3)'
  },
  flowStepComplete: {
    background: '#28a745',
    border: '2px solid #28a745',
    color: 'white'
  },
  flowCancelBtn: {
    padding: '8px 14px',
    background: '#fff',
    color: '#dc3545',
    border: '2px solid #dc3545',
    borderRadius: '8px',
    cursor: 'pointer',
    fontWeight: '700',
    fontSize: 'clamp(12px, 3vw, 14px)',
    transition: 'all 0.3s',
    fontFamily: 'inherit',
    whiteSpace: 'nowrap'
  },
  datePickerContainer: {
    padding: '15px',
    background: 'linear-gradient(135deg, #f0f7ff 0%, #e8f4ff 100%)',
    borderTop: '2px solid #2E4AC7',
    borderBottom: '2px solid #2E4AC7',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '12px',
    overflowX: 'auto'
  },
  datePickerLabel: {
    fontSize: 'clamp(14px, 3.5vw, 16px)',
    fontWeight: '600',
    color: '#2d3748',
    textAlign: 'center'
  },
  datePickerHint: {
    fontSize: 'clamp(11px, 3vw, 13px)',
    color: '#718096',
    textAlign: 'center',
    fontStyle: 'italic'
  }
};

const styleSheet = document.createElement('style');
styleSheet.textContent = `
  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }
  
  @keyframes slideUp {
    from { transform: translateY(20px); opacity: 0; }
    to { transform: translateY(0); opacity: 1; }
  }
  
  @keyframes bounce {
    0%, 80%, 100% { transform: scale(0); }
    40% { transform: scale(1); }
  }
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
  
  button:hover:not(:disabled) {
    transform: translateY(-1px);
    filter: brightness(1.1);
  }

  /* Calendar Styles */
  .react-datepicker {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
    border: 2px solid #2E4AC7 !important;
    border-radius: 15px !important;
    box-shadow: 0 10px 30px rgba(46, 74, 199, 0.2) !important;
  }

  .react-datepicker__header {
    background: linear-gradient(135deg, #2E4AC7 0%, #1F3A9E 100%) !important;
    border-bottom: none !important;
    border-radius: 13px 13px 0 0 !important;
    padding: 15px 0 !important;
  }

  .react-datepicker__current-month {
    color: white !important;
    font-weight: 700 !important;
    font-size: 16px !important;
    margin-bottom: 10px !important;
  }

  .react-datepicker__day-name {
    color: white !important;
    font-weight: 600 !important;
    width: 40px !important;
    line-height: 40px !important;
    margin: 2px !important;
  }

  .react-datepicker__day {
    width: 40px !important;
    line-height: 40px !important;
    margin: 2px !important;
    border-radius: 8px !important;
    transition: all 0.3s !important;
    font-weight: 600 !important;
  }

  .react-datepicker__day:hover {
    background: #e8f1ff !important;
    border-radius: 8px !important;
  }

  .react-datepicker__day--selected {
    background: #2E4AC7 !important;
    color: white !important;
    font-weight: 700 !important;
  }

  .react-datepicker__day--keyboard-selected {
    background: #e8f1ff !important;
    color: #2E4AC7 !important;
  }

  .react-datepicker__day--disabled {
    color: #ccc !important;
    cursor: not-allowed !important;
  }

  .react-datepicker__day--today {
    font-weight: 700 !important;
    color: #2E4AC7 !important;
    border: 2px solid #2E4AC7 !important;
  }

  .react-datepicker__navigation {
    top: 18px !important;
  }

  .react-datepicker__navigation--previous {
    border-right-color: white !important;
  }

  .react-datepicker__navigation--next {
    border-left-color: white !important;
  }

  .react-datepicker__month {
    margin: 15px !important;
  }
  
  /* Mobile Responsive Styles */
  @media (max-width: 768px) {
    /* Prevent zooming on input focus */
    input, textarea, select {
      font-size: 16px !important;
    }
    
    /* Calendar mobile adjustments */
    .react-datepicker {
      font-size: 0.85rem !important;
      transform: scale(0.85);
      transform-origin: center center;
      margin: 0 auto;
    }
    
    .react-datepicker__day-name,
    .react-datepicker__day {
      width: 32px !important;
      line-height: 32px !important;
      margin: 1px !important;
    }
    
    .react-datepicker__current-month {
      font-size: 14px !important;
    }
    
    .react-datepicker__header {
      padding: 12px 0 !important;
    }
    
    /* General mobile styles */
    .chat-messages { 
      padding: 10px !important; 
      gap: 10px !important;
    }
    
    .message { 
      max-width: 90% !important;
      padding: 10px 12px !important;
      font-size: 14px !important;
      border-radius: 12px !important;
    }
    
    .quick-actions { 
      padding: 10px !important; 
    }
    
    .action-buttons { 
      gap: 6px !important;
      justify-content: flex-start !important;
    }
    
    .action-btn { 
      padding: 10px 12px !important; 
      font-size: 13px !important;
      flex: 1 1 calc(50% - 3px) !important;
      min-width: 0 !important;
      white-space: normal !important;
      text-align: center !important;
      line-height: 1.3 !important;
    }
    
    .modal-container { 
      margin: 5px !important;
      max-height: 95vh !important;
      border-radius: 12px !important;
      max-width: calc(100vw - 10px) !important;
    }
    
    .modal-header {
      padding: 14px 16px !important;
    }
    
    .modal-content { 
      padding: 12px !important; 
    }
    
    .admin-card { 
      padding: 12px !important; 
    }
    
    .status-grid { 
      grid-template-columns: 1fr !important;
      gap: 10px !important;
    }
    
    /* Mobile touch improvements */
    button, .action-btn, input, textarea {
      -webkit-tap-highlight-color: rgba(0, 0, 0, 0.1);
    }
  }
  
  @media (max-width: 480px) {
    /* Extra small devices */
    .react-datepicker {
      transform: scale(0.75) !important;
    }
    
    .message {
      max-width: 95% !important;
      padding: 8px 10px !important;
      font-size: 13px !important;
    }
    
    .action-btn {
      font-size: 12px !important;
      padding: 8px 10px !important;
    }
  }
`;
document.head.appendChild(styleSheet);

export default App;