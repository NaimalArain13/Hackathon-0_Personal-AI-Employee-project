# Email MCP Server API Contract

## Overview
This contract defines the API for the Email MCP Server that enables Claude Code to send emails with attachments and search for files in the attachment directory.

## Tools

### 1. send_email
Sends emails based on the provided subject, body, and receiver.

**Parameters**:
- `receiver` (array of strings, required): List of recipient email addresses
- `body` (string, required): The main content of the email
- `subject` (string, required): The subject line of the email
- `attachments` (array of strings or string, optional): Email attachments (filenames)

**Example Request**:
```json
{
  "receiver": ["recipient@example.com"],
  "subject": "Test Email from MCP Server",
  "body": "This is a test email sent via the MCP Email Server.",
  "attachments": ["document.pdf", "image.jpg"]
}
```

**Expected Response**:
```json
{
  "success": true,
  "message_id": "unique-message-id",
  "sent_timestamp": "2026-02-05T10:30:00Z",
  "recipients": ["recipient@example.com"]
}
```

**Error Response**:
```json
{
  "success": false,
  "error_code": "SEND_FAILED",
  "error_message": "Detailed error message",
  "recipients": ["recipient@example.com"]
}
```

### 2. search_attachments
Searches for files in a specified directory that match a given pattern.

**Parameters**:
- `pattern` (string, required): The text pattern to search for in file names

**Example Request**:
```json
{
  "pattern": "report"
}
```

**Expected Response**:
```json
{
  "success": true,
  "matches": [
    {
      "filename": "monthly_report.pdf",
      "path": "/path/to/attachments/monthly_report.pdf",
      "size": 1024000,
      "modified_date": "2026-02-01T14:30:00Z"
    },
    {
      "filename": "sales_report.xlsx",
      "path": "/path/to/attachments/sales_report.xlsx",
      "size": 512000,
      "modified_date": "2026-02-03T09:15:00Z"
    }
  ]
}
```

**Error Response**:
```json
{
  "success": false,
  "error_code": "SEARCH_FAILED",
  "error_message": "Detailed error message"
}
```

## Authentication
The server requires the following environment variables:
- `SENDER`: The sender's email address
- `PASSWORD`: The app password for the email account

## Supported Attachment Types
The server supports these attachment file types for security reasons:
- Documents: doc, docx, xls, xlsx, ppt, pptx, pdf
- Archives: zip, rar, 7z, tar, gz
- Text files: txt, log, csv, json, xml
- Images: jpg, jpeg, png, gif, bmp
- Other: md

## Error Codes
- `AUTH_ERROR`: Authentication failed
- `SEND_FAILED`: Email sending failed
- `ATTACHMENT_INVALID`: Invalid attachment type
- `SEARCH_FAILED`: File search failed
- `NETWORK_ERROR`: Network connectivity issue
- `CONFIG_ERROR`: Server configuration issue