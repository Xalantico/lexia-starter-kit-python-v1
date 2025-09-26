# Lexia AI Agent Starter Kit

A clean, minimal example showing how to build AI agents that integrate with the Lexia platform. This starter kit demonstrates best practices for creating AI agents with proper memory management, streaming responses, and file processing capabilities.

## ✨ Features

- **Clean Architecture**: Well-structured, maintainable code with clear separation of concerns
- **Memory Management**: Built-in conversation history and thread management
- **File Processing**: Support for PDF text extraction and image analysis
- **Streaming Responses**: Real-time response streaming via Lexia's infrastructure
- **Function Calling**: Built-in DALL-E 3 image generation capabilities with Lexia image markdown
- **Variables Helper**: Modern Variables class for clean API key and configuration management
- **Error Handling**: Robust error handling and logging throughout
- **Standard Endpoints**: Inherited endpoints from Lexia package for consistency

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- OpenAI API key
- Access to Lexia platform

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Xalantico/lexia-starter-kit-python-v1
   cd lexia-starter-kit-python-v1
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```


4. **Run the starter kit**
   ```bash
   python main.py
   ```

The server will start on `http://localhost:8000`

## 📚 API Documentation

Once running, you can access:

- **Health Check**: `http://localhost:8000/api/v1/health`
- **Chat Endpoint**: `http://localhost:8000/api/v1/send_message`

## 🏗️ Architecture

### Core Components

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Lexia         │───▶│  Starter Kit     │───▶│   OpenAI        │
│  Platform       │    │                  │    │     API         │
└─────────────────┘    └──────────────────┘    └─────────────────┘
       ▲                        │                        │
       │                        ▼                        │
       │               ┌──────────────────┐               │
       │               │  Memory          │               │
       │               │  Manager        │               │
       │               └──────────────────┘               │
       │                        │                        │
       └────────────────────────┼────────────────────────┘
                                │
                       ┌──────────────────┐
                       │  Response        │
                       │  Handler        │
                       └──────────────────┘
```

### Key Modules

- **`main.py`**: Main application entry point with AI processing logic
- **`memory/`**: Conversation history and thread management
- **`agent_utils.py`**: Utility functions for OpenAI integration
- **`function_handler.py`**: Function calling capabilities including DALL-E 3 image generation

## 🔧 Customization

### Modify AI Behavior

Edit the `process_message()` function in `main.py` to customize:

- System prompts and context
- Model parameters (temperature, max_tokens, etc.)
- Response processing logic
- Error handling strategies

### Add New Capabilities

The starter kit includes function calling support. Add new functions by extending the `available_functions` list:

```python
available_functions = [
    {
        "type": "function",
        "function": {
            "name": "your_function",
            "description": "Description of what your function does",
            "parameters": {
                "type": "object",
                "properties": {
                    "param1": {"type": "string", "description": "Parameter description"}
                },
                "required": ["param1"]
            }
        }
    }
]
```

### Memory Management

Customize conversation storage in the `memory/` module:

- Adjust `max_history` for conversation length
- Implement persistent storage (database, files)
- Add conversation analytics and insights

## 📁 File Processing

The starter kit supports:

- **PDF Processing**: Automatic text extraction and token counting
- **Image Analysis**: Vision capabilities for image-based queries
- **File Size Limits**: Built-in token limits to prevent API overload

## 🔑 Configuration Management

### Variables Helper Class

The starter kit uses the modern Variables helper class from the Lexia package for clean configuration management:

```python
from lexia import Variables

# Initialize variables helper
vars = Variables(data.variables)

# Get API keys and configuration
openai_key = vars.get("OPENAI_API_KEY")
custom_config = vars.get("CUSTOM_CONFIG")
database_url = vars.get("DATABASE_URL")

# Convenience methods
openai_key = vars.get_openai_key()
anthropic_key = vars.get_anthropic_key()
groq_key = vars.get_groq_key()
```

### Benefits of Variables Helper

- **Clean API**: Object-oriented approach instead of utility functions
- **Better Performance**: Built-in caching for faster lookups
- **Flexible**: Easy to change variable names without code changes
- **Consistent**: Same pattern across all Lexia integrations

## 🖼️ Image Generation with Lexia Markdown

The starter kit includes DALL-E 3 image generation with Lexia's new image markdown functionality:

### How It Works

When generating images, the system automatically wraps the process with Lexia's image markdown tags:

```python
# Before image generation
lexia_handler.stream_chunk(data, "[lexia.image.start]")

# Generate image with DALL-E 3
image_url = await generate_image_with_dalle(...)

# After image generation
lexia_handler.stream_chunk(data, "[lexia.image.end]")

# Include image URL in response
image_result = f"Image URL: [lexia.image.start]{image_url}[lexia.image.end]"
```

### Features

- **Automatic Markdown**: Images are automatically wrapped with Lexia image tags
- **Real-time Streaming**: Users see progress during image generation
- **Error Handling**: Graceful fallback if image generation fails
- **Customizable**: Easy to modify image parameters (size, quality, style)

## 🧪 Testing

### 1. Setup ngrok for External Access

To test your agent from the Lexia platform, you'll need to expose your local server to the internet using ngrok:

1. **Install ngrok**
   ```bash
   # On macOS with Homebrew
   brew install ngrok
   
   # Or download from https://ngrok.com/download
   ```

2. **Start your local server**
   ```bash
   python main.py
   ```

3. **Expose your server with ngrok**
   ```bash
   ngrok http 8000
   ```

4. **Copy the ngrok URL**
   ngrok will display a URL like: `https://abc123.ngrok-free.app`

### 2. Configure Agent in Lexia Platform

1. Go to the [Lexia Platform](https://app.lexiaplatform.com)
2. Navigate to **Agents** → **Create New Agent**
3. In the **Agent Configuration** section:
   - Set **Agent Type** to "Custom Agent"
   - Set **Message Endpoint** to `https://abc123.ngrok-free.app/api/v1/send_message`
4. Save your agent configuration

### 3. Test Your Agent

Once configured, test your setup by sending a message through the Lexia platform or directly via curl:

```bash
curl -X POST "https://your-ngrok-url.ngrok-free.app/api/v1/send_message" \
     -H "Content-Type: application/json" \
     -d '{
       "thread_id": "test_thread",
       "message": "Hello, how are you?",
       "model": "gpt-3.5-turbo"
     }'
```

**Note**: Replace `your-ngrok-url` with your actual ngrok URL. The ngrok URL will change each time you restart ngrok unless you have a paid account.

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed correctly
2. **API Key Issues**: The starter kit now provides helpful error messages when the OpenAI API key is missing:
   - "Sorry, the OpenAI API key is missing or empty. From menu right go to admin mode, then agents and edit the agent in last section you can set the openai key."
   - This guides users to the correct location in the Lexia platform to configure their API key
3. **Port Conflicts**: Change the port in `main.py` if 8000 is already in use
4. **Variables Not Found**: Use the Variables helper class to access configuration values from Lexia requests

### Debug Mode

Enable detailed logging by modifying the log level in `main.py`:

```python
logging.basicConfig(level=logging.DEBUG)
```

## 📖 Code Structure

```
lexia-starter-kit/
├── main.py                 # Main application entry point
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── .gitignore             # Git ignore patterns
├── memory/                # Memory management module
│   ├── __init__.py
│   └── conversation_manager.py
├── agent_utils.py         # AI agent utilities
└── function_handler.py    # Function calling capabilities (DALL-E 3)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This starter kit is provided as-is for development and educational purposes.

## 🆘 Support

For issues and questions:

1. Check the logs for detailed error messages
2. Review the Lexia platform documentation
3. Open an issue in this repository

---

**Happy coding! 🚀**
