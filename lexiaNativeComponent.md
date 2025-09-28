# Lexia Native Components

## Image Components

Lexia provides native components for handling images in AI agent conversations. These components enable seamless image generation, loading states, and display within the Lexia interface.

### `lexia.loading.image`

The `lexia.loading.image` component is used to indicate when an image is being generated or processed. This creates a loading state that provides visual feedback to users while image generation is in progress.

#### Usage

```python
# Start loading indicator
lexia_handler.stream_chunk(data, "[lexia.loading.image.start]")

# Perform image generation (e.g., with DALL-E)
image_url = await generate_image_with_dalle(
    prompt=args.get("prompt"),
    variables=data.variables,
    size=args.get("size", "1024x1024"),
    quality=args.get("quality", "standard"),
    style=args.get("style", "vivid")
)

# End loading indicator
lexia_handler.stream_chunk(data, "[lexia.loading.image.end]")
```

#### When to Use

- **Image Generation**: When calling AI image generation services like DALL-E, Midjourney, or Stable Diffusion
- **Image Processing**: When applying filters, resizing, or other transformations to images
- **Image Upload**: When uploading and processing user-provided images
- **Any Image Operation**: Any operation that takes time and involves images

#### Benefits

- **User Experience**: Provides clear visual feedback that something is happening
- **Expectation Management**: Users understand that image generation takes time
- **Professional Feel**: Creates a polished, responsive interface experience

### `lexia.image`

The `lexia.image` component is used to display images within the conversation interface. It wraps image URLs with special markdown tags that Lexia recognizes and renders appropriately.

#### Usage

```python
# Wrap image URL with lexia.image tags
image_result = f"Image URL: [lexia.image.start]{image_url}[lexia.image.end]"

# Or include in a more detailed response
image_result = f"""
🎨 **Image Generated Successfully!**

**Prompt:** {args.get('prompt')}
**Image URL:** [lexia.image.start]{image_url}[lexia.image.end]

*Image created with DALL-E 3*
"""
```

#### When to Use

- **Display Generated Images**: Show images created by AI services
- **Reference Images**: Display images referenced in conversations
- **Visual Results**: Present any visual content as part of agent responses
- **Image Sharing**: Share images between different parts of the conversation

#### Benefits

- **Native Rendering**: Images are displayed natively within the Lexia interface
- **Consistent Formatting**: Ensures proper image display across different contexts
- **Rich Content**: Enhances conversations with visual elements
- **User Engagement**: Visual content makes interactions more engaging

## Complete Example

Here's a complete example showing how both components work together:

```python
async def generate_image_function(args, data, lexia_handler):
    try:
        # Stream function execution start
        execution_msg = f"\n🚀 **Executing function:** generate_image"
        lexia_handler.stream_chunk(data, execution_msg)
        
        # Start loading indicator
        lexia_handler.stream_chunk(data, "[lexia.loading.image.start]")
        
        # Generate the image
        image_url = await generate_image_with_dalle(
            prompt=args.get("prompt"),
            variables=data.variables,
            size=args.get("size", "1024x1024"),
            quality=args.get("quality", "standard"),
            style=args.get("style", "vivid")
        )
        
        # End loading indicator
        lexia_handler.stream_chunk(data, "[lexia.loading.image.end]")
        
        # Stream function completion
        completion_msg = f"\n✅ **Function completed successfully:** generate_image"
        lexia_handler.stream_chunk(data, completion_msg)
        
        # Create response with image
        image_result = f"""
🎨 **Image Generated Successfully!**

**Prompt:** {args.get('prompt')}
**Image URL:** [lexia.image.start]{image_url}[lexia.image.end]

*Image created with DALL-E 3*
"""
        
        # Stream the final result
        lexia_handler.stream_chunk(data, image_result)
        
        return {
            "success": True,
            "message": "Image generated successfully",
            "image_url": image_url
        }
        
    except Exception as e:
        # Handle errors appropriately
        lexia_handler.stream_chunk(data, f"❌ **Error:** {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
```

## Best Practices

1. **Always Use Loading States**: For any operation that takes more than a few seconds, use the loading component
2. **Wrap Image URLs**: Always wrap image URLs with `lexia.image` tags for proper display
3. **Provide Context**: Include relevant information about the image (prompt, source, etc.)
4. **Handle Errors**: Implement proper error handling for image generation failures
5. **Stream Progress**: Use streaming to provide real-time feedback to users

## Integration with AI Services

These components work seamlessly with various AI image generation services:

- **OpenAI DALL-E**: For creating images from text prompts
- **Stable Diffusion**: For open-source image generation
- **Midjourney**: For artistic image creation
- **Custom Models**: Any image generation or processing service

The components provide a consistent interface regardless of the underlying image service being used.
