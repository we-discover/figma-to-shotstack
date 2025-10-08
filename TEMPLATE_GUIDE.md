# Figma to Shotstack Template Guide

## Overview

This tool converts Figma designs into Shotstack video/image templates. The generated templates are designed to work with dynamic image substitution via MediaGraph or Shotstack's template system.

## How It Works

The converter:
1. Reads Figma frame structures and positions
2. Extracts images from frames (exported at 2x resolution)
3. Calculates proper positioning and scaling for Shotstack
4. Generates JSON templates with merge fields for dynamic content

## Dynamic Image Handling

### Fit Modes

The template uses different fit modes based on element type:

- **Logos/Small Elements**: `fit: "contain"`
  - Shows the full image/logo without cropping
  - May have letterboxing (padding) if aspect ratio doesn't match
  - Best for logos where you want to ensure full visibility

- **Regular Images**: `fit: "crop"`
  - Center crops the image to fill the frame
  - Maintains aspect ratio but may crop edges
  - Works well with varied aspect ratios

### Expected Aspect Ratios

For best results when passing images via MediaGraph, use these target aspect ratios:

| Slot | Frame Size | Target Aspect Ratio | Notes |
|------|-----------|---------------------|-------|
| Background | 1080x1080 | 1:1 (square) | Full frame, no issues |
| Image 2 | 720x720 | ~1.23:1 (slightly wide) | Will center crop if different |
| Image 1 | 720x360 | ~1.33:1 (landscape) | Will center crop if different |
| Logo | 230x97 | ~2.3:1 (very wide) | Uses 'contain' - any aspect works |

### Handling Different Aspect Ratios

**If you provide images with different aspect ratios:**

1. **Logos** (contain mode): Full logo will show, may have padding/letterboxing
2. **Images** (crop mode): Will center crop to fill frame
   - Taller images: Top/bottom edges may be cropped
   - Wider images: Left/right edges may be cropped

**For exact Figma design match:**

Use MediaGraph or image preprocessing to resize/crop images to target aspect ratios **before** passing to template.

Example preprocessing pipeline:
```
Input Image → Detect Aspect Ratio → Smart Crop/Resize → Pass to Template
```

## Usage

### Generate Template

```bash
# With image population
python figma_to_shotstack.py --populate-images --image-only

# JSON only (for clipboard)
python figma_to_shotstack.py --populate-images --image-only --json-only | pbcopy
```

### Template Structure

The generated template has this track order (bottom to top):
1. **Track 0**: Logo (front layer)
2. **Track 1**: Background (back layer)
3. **Track 2**: Image 2
4. **Track 3**: Image 1

## Best Practices

### For Development/Testing
- Use the current template as-is
- Accept that center crop may differ slightly from Figma
- Document aspect ratio expectations for content team

### For Production
1. **Option A**: Strict aspect ratio enforcement
   - Require exact aspect ratios from content sources
   - Reject images that don't match

2. **Option B**: Preprocessing pipeline (Recommended)
   - Use MediaGraph/Workflows to preprocess images
   - Smart crop/resize to target aspect ratios
   - Pass processed images to template

3. **Option C**: Multiple template variants
   - Create templates for common aspect ratios
   - Route images to appropriate template variant

## Limitations

- No explicit crop regions (uses center crop for images)
- Assumes similar aspect ratios to Figma design
- Extreme aspect ratio differences may produce unexpected results
- Text elements are converted but may need manual adjustment

## Future Enhancements

Potential improvements for production use:

1. **Add explicit crop values** - Calculate exact crop regions from Figma
2. **Smart crop detection** - Detect focal points for better cropping
3. **Aspect ratio validation** - Warn when images don't match expected ratios
4. **MediaGraph integration** - Built-in preprocessing pipeline
5. **Multiple variants** - Generate templates for different aspect ratios
