# Lexia SDK Functions Reference

## Installation

```bash
pip install lexia
```

---

## Core Components

### 1. LexiaHandler

Main interface for all Lexia communication.

```python
from lexia import LexiaHandler

# Initialize
lexia = LexiaHandler(dev_mode=True)  # or False for production
```

#### Methods

**`begin(data) -> Session`**
- Start a streaming session (recommended API)
- Returns session object with streaming methods
```python
session = lexia.begin(data)
session.stream("Hello ")
session.stream("World!")
full_text = session.close()
```

---

### 2. Session Object (from `begin()`)

Convenient wrapper for streaming within a single response.

```python
session = lexia.begin(data)
```

#### Methods

**`stream(content: str)`**
- Stream a chunk
```python
session.stream("Hello World")
```

**`close(usage_info=None, file_url=None) -> str`**
- Finalize and return full text
```python
full_text = session.close(usage_info={...})
```

**`error(error_message: str, exception=None, trace=None)`**
- Send error
```python
session.error("Something failed", exception=e)
```

**`start_loading(kind: str = "thinking")`**
- Show loading indicator
- Types: `"thinking"`, `"code"`, `"image"`, `"search"`
```python
session.start_loading("code")
```

**`end_loading(kind: str = "thinking")`**
- Hide loading indicator
```python
session.end_loading("code")
```

**`image(url: str)`**
- Display image
```python
session.image("https://example.com/image.png")
```

**`tracing(content: str, visibility: str = "all")`**
- Send trace/debug info
- Visibility: `"all"` or `"admin"`
```python
session.tracing("Debug: Processing step 1", visibility="admin")
```

**`tracing_begin(message: str, visibility: str = "all")`**
- Start progressive trace block
```python
session.tracing_begin("Processing items:", "all")
```

**`tracing_append(message: str)`**
- Append to progressive trace
```python
session.tracing_append("\n  - Item 1 done")
```

**`tracing_end(message: str = None)`**
- Complete and send progressive trace
```python
session.tracing_end("\n✅ Complete!")
```

---

### 3. Data Models

**ChatMessage** (Request from Lexia)
```python
from lexia import ChatMessage

data: ChatMessage  # Received in your endpoint
# Key fields:
data.message           # User message
data.thread_id         # Thread identifier
data.response_uuid     # Unique response ID
data.conversation_id   # Conversation ID
data.channel           # Streaming channel
data.variables         # Environment variables
data.memory            # User memory data
data.force_tools       # Forced tools list
data.file_url          # File URL (if provided)
data.file_base64       # Base64 file (if provided)
data.file_name         # Original filename
data.system_message    # Custom system message
data.project_system_message  # Project system message
```

**ChatResponse** (Response to Lexia)
```python
from lexia import create_success_response

response = create_success_response(
    response_uuid=data.response_uuid,
    thread_id=data.thread_id,
    message="Processing started"
)
```

---

### 4. Variables Helper

Easy access to environment variables.

```python
from lexia import Variables

vars = Variables(data.variables)

# Get any variable
openai_key = vars.get("OPENAI_API_KEY")
custom_var = vars.get("MY_CUSTOM_VAR")

# Check if exists
if vars.has("OPENAI_API_KEY"):
    key = vars.get("OPENAI_API_KEY")

# List all variable names
names = vars.list_names()  # ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", ...]

# Convert to dict
vars_dict = vars.to_dict()  # {"OPENAI_API_KEY": "sk-...", ...}
```

---

### 5. Memory Helper

Access user memory data.

```python
from lexia import MemoryHelper

memory = MemoryHelper(data.memory)

# Get user information
user_name = memory.get_name()
user_goals = memory.get_goals()  # List[str]
user_location = memory.get_location()
user_interests = memory.get_interests()  # List[str]
user_preferences = memory.get_preferences()  # List[str]
user_experiences = memory.get_past_experiences()  # List[str]

# Check if data exists
if memory.has_name():
    print(f"User: {memory.get_name()}")
if memory.has_goals():
    print(f"Goals: {memory.get_goals()}")

# Convert to dict
memory_dict = memory.to_dict()

# Check if empty
if not memory.is_empty():
    # Process memory
    pass
```

---

### 6. Force Tools Helper

Check which tools are forced by user.

```python
from lexia import ForceToolsHelper

tools = ForceToolsHelper(data.force_tools)

# Check if tool is forced
if tools.has("search"):
    # Perform search
    pass
if tools.has("code"):
    # Use code tool
    pass

# Get all forced tools
all_tools = tools.get_all()  # ["search", "code", ...]

# Check if empty
if not tools.is_empty():
    print(f"{tools.count()} tools forced")
```

---

### 7. File Utilities

Decode base64 files.

```python
from lexia import decode_base64_file

# Decode base64 file to temporary file
file_path, is_temp = decode_base64_file(data.file_base64, data.file_name)

# Use the file
with open(file_path, 'rb') as f:
    content = f.read()

# Clean up if temporary
if is_temp:
    os.unlink(file_path)
```

---

### 8. FastAPI Integration

Add standard Lexia endpoints to your FastAPI app.

```python
from fastapi import FastAPI
from lexia import LexiaHandler, ChatMessage, create_lexia_app, add_standard_endpoints

# Create app
app = create_lexia_app(
    title="My AI Agent",
    version="1.0.0",
    description="AI agent with Lexia"
)

# Initialize handler
lexia = LexiaHandler(dev_mode=True)

# Define processing function
async def process_message(data: ChatMessage):
    session = lexia.begin(data)
    
    # Your AI logic here
    session.stream("Hello from AI")
    
    session.close()

# Add standard endpoints
add_standard_endpoints(
    app,
    lexia_handler=lexia,
    process_message_func=process_message
)

# Run
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

Standard endpoints added:
- `POST /api/v1/send_message` - Main chat endpoint
- `GET /api/v1/health` - Health check
- `GET /api/v1/stream/{channel}` - SSE streaming (dev mode)
- `GET /api/v1/poll/{channel}` - Polling endpoint (dev mode)

---

## Complete Example

```python
from lexia import LexiaHandler, ChatMessage, Variables, MemoryHelper, ForceToolsHelper
from openai import OpenAI

# Initialize
lexia = LexiaHandler(dev_mode=True)

async def process_message(data: ChatMessage):
    try:
        # Start session
        session = lexia.begin(data)
        
        # Get variables
        vars = Variables(data.variables)
        api_key = vars.get("OPENAI_API_KEY")
        
        if not api_key:
            session.error("OpenAI API key not found")
            return
        
        # Get user memory
        memory = MemoryHelper(data.memory)
        user_name = memory.get_name() if memory.has_name() else "there"
        
        # Check forced tools
        tools = ForceToolsHelper(data.force_tools)
        must_search = tools.has("search")
        
        # Show loading
        session.start_loading("thinking")
        
        # Call OpenAI
        client = OpenAI(api_key=api_key)
        stream = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": f"You are helpful. User name: {user_name}"},
                {"role": "user", "content": data.message}
            ],
            stream=True
        )
        
        session.end_loading("thinking")
        
        # Stream response
        for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                session.stream(content)
        
        # Complete
        session.close(usage_info={"prompt_tokens": 10, "completion_tokens": 50})
        
    except Exception as e:
        session.error(f"Error: {str(e)}", exception=e)
```

---

## Dev Mode vs Production Mode

**Dev Mode** (`dev_mode=True`):
- Streams directly to HTTP response (SSE)
- No Centrifugo needed
- File uploads handled locally
- Perfect for development and testing

**Production Mode** (`dev_mode=False`):
- Uses Centrifugo for real-time streaming
- Returns immediate HTTP response
- Processing happens in background
- Scalable for production use

---

## Usage Info Format

```python
usage_info = {
    "prompt_tokens": 100,
    "completion_tokens": 50,
    "total_tokens": 150
}

session.close(usage_info=usage_info)
```

If not provided, Lexia SDK will estimate token counts.

---

## Loading Markers

Send loading indicators to frontend:

```python
# Semantic commands (auto-converted to markers)
session.stream("show thinking load")  # Start thinking
session.stream("end thinking load")   # End thinking

# Or use helper methods
session.start_loading("thinking")
session.end_loading("thinking")

# Types: "thinking", "code", "image", "search"
```

---

## Image Display

Show images in the response:

```python
session.image("https://example.com/image.png")

# Or manually
session.stream("[lexia.image.start]https://example.com/image.png[lexia.image.end]")
```

---

## Error Handling

```python
try:
    # Your code
    pass
except Exception as e:
    # Automatic trace logging with session
    session.error("Failed to process", exception=e)
```

Errors are:
1. Displayed to user in frontend
2. Logged to Lexia backend with trace
3. Persisted in conversation

---

## Environment Variables

Set from request variables:

```python
from lexia.utils import set_env_variables

# Auto-set all variables as env vars
set_env_variables(data.variables)

# Now accessible via os.environ
import os
api_key = os.environ.get("OPENAI_API_KEY")
```

---

## Version

```python
from lexia import __version__
print(__version__)  # "1.2.9"
```

