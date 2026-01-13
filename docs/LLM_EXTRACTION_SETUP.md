# LLM-Based CV Data Extraction Setup Guide

## Overview

The Staffing Agent now supports **LLM-based CV data extraction** for consistent and accurate extraction of candidate information from uploaded resumes.

When enabled, all uploaded CVs are automatically processed using OpenAI's GPT-4o-mini to extract:

### Basic Information
- **Name**: Candidate's full name
- **Email**: Email address
- **Location**: City, State/Country

### CV Sections
- **Summary**: Professional summary or objective (2-3 sentences)
- **Skills**: Keywords only (e.g., "python", "react", "aws")
- **Experience**: Work history with organization, role, dates, and achievements
- **Certifications**: Certification keywords (e.g., "AWS Certified", "PMP", "CKA")

## Benefits

✅ **Consistent extraction** across all CV formats and layouts
✅ **More accurate** than regex-based parsing
✅ **Better context understanding** for semantic search
✅ **Handles varied formats** (traditional, modern, creative layouts)
✅ **Automatic fallback** to regex extraction if LLM is unavailable

## Setup Instructions

### 1. Get OpenAI API Key

1. Sign up at [OpenAI Platform](https://platform.openai.com/)
2. Navigate to API Keys section
3. Create a new API key
4. Copy the key (starts with `sk-...`)

### 2. Configure Backend

1. Create or edit `backend/.env` file:

```bash
cd backend
cp .env.example .env
```

2. Edit the `.env` file and set:

```bash
# Enable OpenAI as the LLM provider
LLM_PROVIDER=openai

# Add your OpenAI API key
LLM_API_KEY=sk-your-actual-api-key-here
```

3. Save the file

### 3. Restart Backend

If using Docker:
```bash
docker-compose restart backend
```

If running locally:
```bash
cd backend
# Stop the current process (Ctrl+C)
# Then restart
uvicorn app.main:app --reload
```

### 4. Test the Extraction

Run the test script to verify LLM extraction is working:

```bash
cd /path/to/staffingagent
python scripts/test_llm_extraction.py
```

Expected output:
```
================================================================================
Testing LLM-based CV Extraction
================================================================================

✓ LLM extraction is ENABLED

Extracting data from sample CV...
--------------------------------------------------------------------------------

EXTRACTION RESULTS:
================================================================================

📋 BASIC INFORMATION:
  Name:     John Doe
  Email:    john.doe@example.com
  Location: San Francisco, CA

📝 SUMMARY:
  Experienced software engineer with 8+ years building scalable web applications...

🔧 SKILLS (25 total):
  1. python
  2. javascript
  3. react
  ...

✅ LLM extraction completed successfully!
```

### 5. Upload a CV

1. Go to your Staffing Agent frontend
2. Navigate to "Upload CV" page
3. Upload a resume (PDF, DOCX, or TXT)
4. Check the backend logs to see LLM extraction in action:

```
INFO: Attempting LLM-based CV extraction
INFO: LLM extraction successful for: John Doe
```

## Cost Considerations

LLM extraction uses **GPT-4o-mini**, which is very cost-effective:

- **Model**: gpt-4o-mini
- **Cost**: ~$0.00015 per CV (assuming 1000 tokens input + 500 tokens output)
- **Processing**: 100 CVs ≈ $0.015 (less than 2 cents)

For typical usage (uploading 10-50 CVs per month), the cost is **negligible** (< $1/month).

## Fallback Behavior

The system is designed to be resilient:

1. **LLM Enabled**: Attempts LLM extraction first
2. **LLM Fails**: Falls back to regex-based extraction automatically
3. **LLM Disabled**: Uses regex-based extraction directly

No uploads will fail due to LLM unavailability.

## Validation

The system validates LLM extraction results:

- Ensures name is extracted (not "Unknown")
- Verifies skills or experience are present
- Falls back to regex if validation fails

## Troubleshooting

### "LLM extraction is DISABLED"

**Cause**: Either `LLM_PROVIDER` is not set to `openai` or `LLM_API_KEY` is missing.

**Solution**:
1. Check `backend/.env` file exists
2. Verify `LLM_PROVIDER=openai`
3. Verify `LLM_API_KEY=sk-...` (starts with sk-)
4. Restart backend

### "OpenAI API key not configured"

**Cause**: `LLM_API_KEY` is missing or empty in `.env`

**Solution**: Add valid OpenAI API key to `backend/.env`

### "LLM extraction failed, falling back to regex"

**Cause**: Network issue, API rate limit, or invalid API key

**Solution**:
1. Check API key is valid
2. Check internet connectivity
3. Check OpenAI API status: https://status.openai.com/
4. Check backend logs for detailed error

### CVs still upload but data is incomplete

**Cause**: Regex extraction is being used (fallback)

**Solution**:
1. Verify LLM extraction is enabled (check logs)
2. Run test script: `python scripts/test_llm_extraction.py`
3. Check for errors in backend logs

## Monitoring

To monitor LLM extraction:

1. **Check backend logs** for messages like:
   - `"Attempting LLM-based CV extraction"`
   - `"LLM extraction successful for: [Name]"`
   - `"LLM extraction disabled, using regex-based extraction"`

2. **Review candidate data** in the frontend to ensure all fields are populated correctly

3. **Track API usage** in your OpenAI dashboard

## Disabling LLM Extraction

To disable LLM extraction and use regex-based extraction:

1. Edit `backend/.env`:
   ```bash
   LLM_PROVIDER=disabled
   ```

2. Restart backend

The system will seamlessly fall back to regex-based extraction.

## Additional Resources

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [OpenAI Pricing](https://openai.com/pricing)
- [Backend README](../backend/README.md)
