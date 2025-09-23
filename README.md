# Figma to Shotstack Converter

Convert Figma designs into Shotstack templates for static image generation.

## Quick Start

1. **Set up credentials:**
   ```bash
   cp .env.example .env
   # Edit .env with your actual API credentials
   ```

2. **Run the converter:**
   ```bash
   # With placeholders (for templates)
   python figma_to_shotstack.py --image-only
   
   # With real Figma images (ready to render)
   python figma_to_shotstack.py --populate-images --image-only
   ```

## Files

- **`converter.py`** - Core conversion logic
- **`figma_to_shotstack.py`** - Main script
- **`.env`** - Configuration (not in git)

## Options

- `--populate-images` - Use real Figma images instead of placeholders
- `--image-only` - Optimize for static image output (recommended)
- `--video-mode` - Include video metadata (fps, longer duration)

## Output

Generates Shotstack JSON template optimized for static PNG image rendering.