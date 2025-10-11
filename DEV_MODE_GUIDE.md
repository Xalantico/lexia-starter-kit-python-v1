# Lexia Starter Kit - Dev Mode Guide

## Overview

The Lexia Starter Kit now supports **Dev Mode** for local development without requiring Centrifugo infrastructure.

## Running the Starter Kit

### Dev Mode (Local Development)
```bash
# Option 1: CLI flag
python main.py --dev

# Option 2: Environment variable
export LEXIA_DEV_MODE=true
python main.py

# Option 3: In venv
source lexia_env/bin/activate
python main.py --dev
```

### Production Mode (Default)
```bash
# Option 1: Explicit flag
python main.py --prod

# Option 2: Default (no flags)
python main.py

# Option 3: Environment variable
export LEXIA_DEV_MODE=false
python main.py
```

## What You'll See

### Dev Mode Output:
```
🚀 Starting Lexia AI Agent Starter Kit...
============================================================
🔧 DEV MODE ACTIVE - No Centrifugo required!
   Use --prod flag or LEXIA_DEV_MODE=false for production
============================================================
📖 API Documentation: http://localhost:8005/docs
🔍 Health Check: http://localhost:8005/api/v1/health
💬 Chat Endpoint: http://localhost:8005/api/v1/send_message
📡 SSE Stream: http://localhost:8005/api/v1/stream/{channel}
📊 Poll Stream: http://localhost:8005/api/v1/poll/{channel}
============================================================

✨ This starter kit demonstrates:
   - Clean integration with Lexia package
   - Inherited endpoints for common functionality
   - Customizable AI message processing
   - Conversation memory management
   - File processing (PDFs, images)
   - Function calling with DALL-E 3
   - Proper data structure for Lexia communication
   - Comprehensive error handling and logging
   - Dev mode streaming (SSE, no Centrifugo)

🔧 Customize the process_message() function to add your AI logic!

💡 Mode Selection:
   python main.py --dev   # Local development (SSE streaming)
   python main.py --prod  # Production (Centrifugo)
============================================================
```

### Production Mode Output:
```
🚀 Starting Lexia AI Agent Starter Kit...
============================================================
🟢 PRODUCTION MODE - Centrifugo/WebSocket streaming
   Use --dev flag or LEXIA_DEV_MODE=true for local development
============================================================
📖 API Documentation: http://localhost:8005/docs
🔍 Health Check: http://localhost:8005/api/v1/health
💬 Chat Endpoint: http://localhost:8005/api/v1/send_message
============================================================

✨ This starter kit demonstrates:
   ... (features list)
   - Production streaming (Centrifugo/WebSocket)

💡 Mode Selection:
   python main.py --dev   # Local development (SSE streaming)
   python main.py --prod  # Production (Centrifugo)
============================================================
```

## Key Differences

| Feature | Dev Mode | Production Mode |
|---------|----------|-----------------|
| **Streaming** | SSE (Server-Sent Events) | Centrifugo WebSocket |
| **Response** | Direct HTTP stream | Background task + WebSocket |
| **Infrastructure** | None needed | Centrifugo server required |
| **Console Output** | ✅ Real-time | ❌ No |
| **Setup Complexity** | Low | Medium |
| **Best For** | Local testing | Production deployment |

## What Changed in the Code

### 1. Mode Detection (Lines 77-89)
```python
# Determine dev/prod mode from CLI flags or env var (default: prod)
dev_mode_flag = None
if '--dev' in sys.argv:
    dev_mode_flag = True
elif '--prod' in sys.argv:
    dev_mode_flag = False
else:
    env_val = os.environ.get('LEXIA_DEV_MODE', 'false').lower()
    dev_mode_flag = env_val in ('true', '1', 'yes', 'y', 'on')
```

### 2. LexiaHandler Initialization (Line 93)
```python
# Initialize with selected mode
lexia = LexiaHandler(dev_mode=dev_mode_flag)
```

### 3. Async OpenAI in Dev Mode (Line 165)
```python
# Use AsyncOpenAI in dev mode for proper event loop handling
async_client = AsyncOpenAI(api_key=openai_api_key) if getattr(lexia, 'dev_mode', False) else None
```

### 4. Conditional Streaming Logic
- **Dev mode**: Uses `async for chunk in stream` with `await asyncio.sleep(0)`
- **Production**: Uses regular `for chunk in stream`

## Testing Dev Mode

### 1. Start the Server
```bash
cd /Users/xalanticosl/projects/Lexia/lexia-starter-kit-python-v1
source lexia_env/bin/activate
python main.py --dev
```

### 2. Test with Frontend
Point your frontend to:
```
http://localhost:8005/api/v1/send_message
```

The response will stream in real-time!

### 3. Test Endpoints
```bash
# Health check
curl http://localhost:8005/api/v1/health

# API documentation
open http://localhost:8005/docs

# SSE stream (for a specific channel)
curl -N http://localhost:8005/api/v1/stream/your-channel-id

# Poll endpoint
curl http://localhost:8005/api/v1/poll/your-channel-id
```

## Features Working in Dev Mode

✅ **All features work identically in both modes:**
- ✅ Conversation memory
- ✅ PDF processing
- ✅ Image analysis (vision models)
- ✅ Function calling (DALL-E 3)
- ✅ Streaming responses
- ✅ Error handling
- ✅ Logging

**The only difference is HOW streaming is delivered to the frontend!**

## Upgrading from Previous Version

No code changes needed! Just update lexia package:

```bash
pip install --upgrade lexia
```

Then you can use:
```bash
python main.py --dev  # New dev mode
python main.py        # Same as before (production)
```

## Requirements Update

Make sure you have:
```bash
pip install lexia>=1.2.4
```

The lexia 1.2.4 package includes:
- DevStreamClient
- SSE endpoints
- Async queue support
- Dev mode support

## Troubleshooting

### Issue: "lexia module has no attribute 'dev_mode'"
**Solution:** Upgrade lexia package
```bash
pip install --upgrade lexia
```

### Issue: Streaming not working in dev mode
**Solution:** Make sure you're using `--dev` flag or set env var
```bash
python main.py --dev  # Should show "🔧 DEV MODE ACTIVE"
```

### Issue: Frontend still shows "Thinking..." then full response
**Solution:** Make sure frontend is parsing SSE format:
```javascript
// SSE format: "data: content\n\n"
const lines = buffer.split('\n\n');
for (const line of lines) {
  if (line.startsWith('data: ')) {
    const chunk = line.substring(6);
    // Process chunk...
  }
}
```

## Examples

### Test with curl
```bash
# Send a message and watch it stream
curl -N -X POST http://localhost:8005/api/v1/send_message \
  -H "Content-Type: application/json" \
  -d '{
    "thread_id": "test-123",
    "channel": "test-channel",
    "message": "Write a short poem about AI",
    "response_uuid": "uuid-123",
    "message_uuid": "msg-123",
    "conversation_id": 1,
    "model": "gpt-4o",
    "variables": [{"name": "OPENAI_API_KEY", "value": "sk-..."}],
    "url": "",
    "headers": {}
  }'
```

The `-N` flag makes curl show streaming output in real-time!

## Summary

**Dev Mode Benefits:**
- ✅ No infrastructure setup
- ✅ Real-time console output
- ✅ Easy testing
- ✅ Same code works in production

**To Use:**
1. Run with `--dev` flag
2. Frontend gets SSE streaming
3. See responses in console
4. When ready, remove `--dev` for production!

That's it! Happy developing! 🚀

