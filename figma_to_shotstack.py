#!/usr/bin/env python3
"""
Figma to Shotstack Converter

Main script for converting Figma page designs into Shotstack template JSON.
Uses the FigmaToShotstackConverter class from converter.py module.
"""

import json
import os
from converter import FigmaToShotstackConverter
from dotenv import load_dotenv


load_dotenv()


def main():
    """Example usage of the converter"""
    # Get API credentials from environment
    figma_token = os.getenv('FIGMA_TOKEN')
    figma_file_key = os.getenv('FIGMA_FILE_KEY')
    
    if not figma_token:
        print("Please set FIGMA_TOKEN in .env file")
        return
        
    if not figma_file_key:
        print("Please set FIGMA_FILE_KEY in .env file")
        return
    
    # Get default settings from environment
    output_width = int(os.getenv('DEFAULT_OUTPUT_WIDTH', 1200))
    output_height = int(os.getenv('DEFAULT_OUTPUT_HEIGHT', 1200))
    duration = float(os.getenv('DEFAULT_DURATION', 5.0))
    populate_images = os.getenv('POPULATE_IMAGES', 'false').lower() == 'true'
    image_only = os.getenv('IMAGE_ONLY', 'false').lower() == 'true'
    
    # Check for command line arguments
    import sys
    if '--populate-images' in sys.argv:
        populate_images = True
    elif '--no-populate-images' in sys.argv:
        populate_images = False

    if '--image-only' in sys.argv:
        image_only = True
    elif '--video-mode' in sys.argv:
        image_only = False

    json_only = '--json-only' in sys.argv

    if not json_only:
        print(f"Using populate_images: {populate_images}")
        print(f"Using image_only: {image_only}")
    
    # Example usage
    converter = FigmaToShotstackConverter(figma_token)
    
    try:
        template = converter.convert_to_shotstack(
            file_key=figma_file_key,
            page_name="Template 1",  # Use RFD page
            output_width=output_width,
            output_height=output_height,
            duration=duration,
            populate_images=populate_images,
            image_only=image_only,
            quiet=json_only
        )

        if json_only:
            print(json.dumps(template, indent=2))
        else:
            print("Shotstack Template JSON:")
            print(json.dumps(template, indent=2))

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
