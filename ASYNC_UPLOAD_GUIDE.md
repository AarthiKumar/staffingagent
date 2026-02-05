# Asynchronous CV Upload System

## Overview

The CV upload system has been completely upgraded to use asynchronous processing with real-time progress tracking and user notifications. Users no longer need to wait while CVs are being processed - they can upload multiple files and see live progress updates.

## Key Features

### 1. **Non-Blocking Uploads**
- Upload returns immediately with a job ID
- Processing happens in the background
- Users can navigate away and come back
- Multiple CVs can be uploaded simultaneously

### 2. **Real-Time Progress Tracking**
- Progress bar shows 0-100% completion
- Step-by-step updates (e.g., "Extracting text from document")
- Color-coded status indicators:
  - 🔵 Blue = Processing
  - 🟢 Green = Completed successfully
  - 🔴 Red = Failed with error
  - 🟠 Orange = Needs user input

### 3. **Missing Fields Notification**
- Automatic detection when name/email/phone cannot be extracted
- Modal dialog prompts user to provide missing information
- Clean, user-friendly form
- Validation ensures all required fields are filled
- Processing continues automatically after submission

### 4. **Visual Feedback**
- Spinner animation while processing
- Checkmark icon on success
- Error icon with detailed message on failure
- Warning icon when manual input needed
- File icons and names for easy identification

## User Flow

### Normal Upload Flow
```
1. User drops/selects CV files
2. Files appear in upload queue with "Queued" status
3. Processing begins automatically
4. Progress bar updates every second
5. Current step shows what's happening
6. On completion:
   - Green checkmark appears
   - "View Profile" button shows
   - User can click to see candidate details
```

### Missing Fields Flow
```
1. CV processing detects missing name/email/phone
2. Status changes to "Requires Input" (orange)
3. User sees "Provide Information" button
4. User clicks button → Modal dialog opens
5. User fills in name, email, phone
6. User clicks "Submit"
7. Processing completes automatically
8. Candidate profile is created
```

### Error Flow
```
1. If processing fails (parsing error, etc.)
2. Status changes to "Failed" (red)
3. Error icon appears
4. Detailed error message is displayed
5. User can retry by re-uploading
```

## API Endpoints

### POST `/api/v1/async/upload-async`
**Start async CV upload**

Request:
```json
{
  "agent_id": "staffing",
  "document_type": "resume",
  "filename": "john_doe_cv.pdf",
  "content_base64": "base64_encoded_content...",
  "use_ocr": false
}
```

Response:
```json
{
  "job_id": "uuid-here",
  "status": "queued",
  "message": "Upload queued successfully"
}
```

### GET `/api/v1/async/upload-status/{job_id}`
**Poll for upload status**

Response:
```json
{
  "job_id": "uuid-here",
  "status": "processing",
  "progress": 45,
  "current_step": "Extracting text from document",
  "document_id": null,
  "candidate_id": null,
  "missing_fields": null,
  "error_message": null,
  "sections_count": 0,
  "embeddings_count": 0,
  "merge_proposal": null,
  "requires_approval": false,
  "created_at": "2026-02-05T21:00:00Z",
  "completed_at": null
}
```

### POST `/api/v1/async/complete-upload`
**Submit missing manual data**

Request:
```json
{
  "job_id": "uuid-here",
  "manual_name": "John Doe",
  "manual_email": "john@example.com",
  "manual_phone": "+1-555-123-4567"
}
```

Response:
```json
{
  "success": true,
  "candidate_id": "uuid-here",
  "document_id": "uuid-here",
  "message": "CV processed successfully"
}
```

## Processing Steps

The background processor updates progress at each step:

| Step | Progress | Description |
|------|----------|-------------|
| Queued | 0% | Waiting to start |
| Decoding | 5% | Decoding file content |
| Hashing | 10% | Computing file hash |
| Duplicate check | 15% | Checking for existing files |
| Agent validation | 20% | Validating agent |
| Storing file | 25% | Storing original file |
| Converting | 30% | Converting Word → PDF if needed |
| Extracting text | 40% | Extracting text from document |
| Creating document | 60% | Creating document record |
| Processing sections | 70% | Processing document sections |
| Normalizing | 80% | Normalizing skills/certifications |
| Creating embeddings | 85% | Creating vector embeddings |
| Validating | 90% | Validating extracted data |
| Duplicate check | 95% | Checking for duplicate candidates |
| Creating candidate | 98% | Creating candidate profile |
| Completed | 100% | Processing complete |

## Database Schema

### upload_jobs Table
```sql
CREATE TABLE upload_jobs (
    id UUID PRIMARY KEY,
    filename VARCHAR(500) NOT NULL,
    agent_id VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'queued',
    progress INTEGER DEFAULT 0,
    current_step VARCHAR(200),
    document_id UUID,
    candidate_id UUID,
    missing_fields JSON,
    error_message TEXT,
    error_details JSON,
    sections_count INTEGER DEFAULT 0,
    embeddings_count INTEGER DEFAULT 0,
    merge_proposal JSON,
    requires_approval BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX ix_upload_jobs_status ON upload_jobs(status);
CREATE INDEX ix_upload_jobs_created_at ON upload_jobs(created_at);
```

## Status Values

| Status | Description | User Action |
|--------|-------------|-------------|
| `queued` | Waiting to start | Wait |
| `processing` | Currently processing | Wait and watch progress |
| `completed` | Successfully completed | View candidate profile |
| `failed` | Processing failed | Check error, retry |
| `requires_input` | Missing required fields | Provide name/email/phone |

## Frontend Components

### UploadCVAsync Component
Main upload interface with:
- Drag-and-drop zone
- File selection button
- OCR toggle checkbox
- Upload queue with progress bars
- Status indicators
- Manual input modal

### Features
- **Auto-polling**: Checks status every 1 second
- **Auto-cleanup**: Stops polling when done
- **Memory management**: Clears intervals on unmount
- **Error handling**: Graceful degradation on network issues
- **Responsive UI**: Works on all screen sizes

## Migration

To enable this feature, run the database migration:

```bash
cd backend
alembic upgrade head
```

This will create the `upload_jobs` table.

## Testing

### Test Scenarios

1. **Normal Upload**
   - Upload a well-formed CV with name, email, phone
   - Verify progress updates smoothly
   - Verify candidate is created
   - Verify "View Profile" button works

2. **Missing Fields**
   - Upload a CV without contact info
   - Verify orange warning status
   - Click "Provide Information"
   - Fill in name, email, phone
   - Submit and verify completion

3. **Multiple Uploads**
   - Upload 3-5 CVs at once
   - Verify all show independent progress
   - Verify polling works for all
   - Verify all complete successfully

4. **Error Handling**
   - Upload corrupt file
   - Verify red error status
   - Verify error message is shown

5. **Navigation**
   - Upload CV
   - Navigate to another page
   - Come back to upload page
   - Verify status is still tracked (if job ID persisted)

## Performance

### Polling Interval
- **Frequency**: 1000ms (1 second)
- **Auto-stop**: Stops when status is completed/failed/requires_input
- **Concurrency**: Each upload has independent polling
- **Resource usage**: Minimal - only HTTP requests, no websockets

### Processing Time
- **PDF extraction**: 2-5 seconds
- **Word conversion**: 3-7 seconds
- **LLM extraction** (if enabled): 5-15 seconds
- **Embedding generation**: 2-5 seconds
- **Total**: 10-30 seconds typical

### Scalability
- **Concurrent uploads**: Limited by FastAPI worker threads
- **Background tasks**: Uses FastAPI BackgroundTasks (non-blocking)
- **Database**: Indexed by status and created_at
- **Cleanup**: Manual cleanup of old jobs recommended (30+ days)

## Configuration

### Backend Settings
Located in upload_async.py:
```python
POLLING_INTERVAL = 1000  # ms between status checks (frontend)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB (not enforced yet)
```

### Frontend Settings
Located in UploadCVAsync.tsx:
```typescript
const POLL_INTERVAL = 1000;  // Poll every 1 second
const AUTO_CLEANUP = true;    // Auto-cleanup intervals
```

## Troubleshooting

### "Job not found" Error
- Job ID is invalid or expired
- Database migration not run
- Backend service restarted (in-memory jobs lost)

### Progress Stuck at X%
- Check backend logs for errors
- Background task may have crashed
- Database connection lost
- LLM API timeout

### Missing Fields Not Detected
- CV validation may have passed
- Manual data was provided in initial upload
- Check cv_validation.py for validation logic

### Polling Not Working
- Network connectivity issues
- Backend service down
- CORS issues (check browser console)
- Frontend polling interval not set up

## Best Practices

1. **User Communication**
   - Show clear progress indicators
   - Provide meaningful step descriptions
   - Display helpful error messages
   - Guide users when input needed

2. **Error Recovery**
   - Allow retry without re-upload
   - Preserve manual input on errors
   - Show detailed error information
   - Provide support contact for persistent issues

3. **Performance**
   - Limit concurrent uploads (suggest 5 max)
   - Show file size limits
   - Warn about OCR processing time
   - Consider batch upload for large quantities

4. **Cleanup**
   - Archive completed jobs after 30 days
   - Delete failed jobs after 7 days
   - Clean up orphaned documents
   - Monitor database growth

## Future Enhancements

- [ ] WebSocket support for real-time updates (instead of polling)
- [ ] Batch upload with ZIP file support
- [ ] Job history page (see all past uploads)
- [ ] Resume failed jobs
- [ ] Email notifications when processing completes
- [ ] Estimated time remaining
- [ ] Pause/cancel uploads
- [ ] Priority queue for urgent uploads
- [ ] Admin dashboard for job management

## Conclusion

The async upload system provides a modern, user-friendly experience for CV processing. Users no longer wait for processing - they get immediate feedback, can upload multiple files, and are notified when manual input is needed. This dramatically improves the user experience and makes the system feel fast and responsive even when processing takes 30+ seconds.
