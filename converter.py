#!/usr/bin/env python3
"""
FigmaToShotstackConverter Class

Core converter class for transforming Figma designs into Shotstack templates.
Extracts text layers, images, and positioning to create video/image templates.
"""

import json
import re
from typing import Dict, List, Any, Optional, Tuple
from FigmaPy import FigmaPy


class FigmaToShotstackConverter:
    """Converts Figma designs to Shotstack templates"""
    
    def __init__(self, figma_token: str):
        """Initialize with Figma API token"""
        self.figma = FigmaPy(figma_token)
        
    def list_pages(self, file_key: str) -> List[Dict[str, str]]:
        """List all pages in a Figma file"""
        try:
            file_info = self.figma.get_file(file_key)
            pages = file_info.document['children']
            
            return [{'name': page['name'], 'id': page['id']} for page in pages]
            
        except Exception as e:
            raise Exception(f"Failed to list Figma pages: {str(e)}")
    
    def extract_page(self, file_key: str, page_name: Optional[str] = None) -> Dict[str, Any]:
        """Extract a specific page from Figma file"""
        try:
            file_info = self.figma.get_file(file_key)
            pages = file_info.document['children']
            
            # Get first page if no name specified
            if not page_name:
                target_page = pages[0] if pages else None
            else:
                target_page = next((p for p in pages if p['name'] == page_name), None)
                
            if not target_page:
                raise ValueError(f"Page '{page_name}' not found")
                
            return target_page
            
        except Exception as e:
            raise Exception(f"Failed to extract Figma page: {str(e)}")
    
    def extract_all_pages(self, file_key: str) -> List[Dict[str, Any]]:
        """Extract all pages from Figma file"""
        try:
            file_info = self.figma.get_file(file_key)
            return file_info.document['children']
            
        except Exception as e:
            raise Exception(f"Failed to extract all Figma pages: {str(e)}")
    
    def parse_node(self, node: Dict[str, Any], canvas_width: float, canvas_height: float) -> Optional[Dict[str, Any]]:
        """Parse a Figma node into Shotstack asset data"""
        node_type = node.get('type')
        
        if node_type == 'TEXT':
            return self._parse_text_node(node, canvas_width, canvas_height)
        elif node_type == 'RECTANGLE' and node.get('fills', []):
            # Check if it has image fill
            for fill in node.get('fills', []):
                if fill.get('type') == 'IMAGE':
                    return self._parse_image_node(node, canvas_width, canvas_height)
        elif node_type == 'FRAME':
            # For frames, we'll export as background images
            return self._parse_frame_node(node, canvas_width, canvas_height)
            
        return None
    
    def _parse_text_node(self, node: Dict[str, Any], canvas_width: float, canvas_height: float) -> Dict[str, Any]:
        """Parse text node to HTML asset"""
        bbox = node.get('absoluteBoundingBox', {})
        style = node.get('style', {})
        
        # Extract text content
        text_content = node.get('characters', 'Text')
        
        # Extract styling
        font_family = style.get('fontFamily', 'Arial')
        font_size = style.get('fontSize', 16)
        
        # Extract color from fills
        color = '#000000'  # default
        fills = node.get('fills', [])
        if fills and fills[0].get('type') == 'SOLID':
            color_obj = fills[0].get('color', {})
            r = int(color_obj.get('r', 0) * 255)
            g = int(color_obj.get('g', 0) * 255)
            b = int(color_obj.get('b', 0) * 255)
            color = f'#{r:02x}{g:02x}{b:02x}'
        
        # Calculate position relative to canvas
        x_offset, y_offset = self._calculate_offset(bbox, canvas_width, canvas_height)
        
        return {
            'type': 'text',
            'asset': {
                'type': 'html',
                'width': int(bbox.get('width', 200)),
                'height': int(bbox.get('height', 50)),
                'html': f'<p data-html-type="text">{text_content}</p>',
                'css': f'p {{ color: {color}; font-size: {int(font_size)}px; font-family: \'{font_family}\'; text-align: left; }}'
            },
            'position': 'center',
            'offset': {'x': x_offset, 'y': y_offset},
            'fit': 'none',
            'scale': 1
        }
    
    def _parse_image_node(self, node: Dict[str, Any], canvas_width: float, canvas_height: float) -> Dict[str, Any]:
        """Parse image node to image asset"""
        bbox = node.get('absoluteBoundingBox', {})
        x_offset, y_offset = self._calculate_offset(bbox, canvas_width, canvas_height)
        
        return {
            'type': 'image',
            'asset': {
                'type': 'image',
                'src': '{{ IMAGE_PLACEHOLDER }}'  # Will be replaced via merge
            },
            'position': 'center',
            'offset': {'x': x_offset, 'y': y_offset},
            'fit': 'none',
            'scale': 1
        }
    
    def _parse_frame_node(self, node: Dict[str, Any], canvas_width: float, canvas_height: float) -> Dict[str, Any]:
        """Parse frame node as background image"""
        return {
            'type': 'frame',
            'asset': {
                'type': 'image',
                'src': f'{{{{ FRAME_{node.get("name", "").upper().replace(" ", "_")} }}}}'
            },
            'position': 'center',
            'fit': 'none',
            'scale': 1
        }
    
    def _calculate_offset(self, bbox: Dict[str, Any], canvas_width: float, canvas_height: float) -> Tuple[float, float]:
        """Calculate Shotstack offset from Figma bounding box"""
        # Get center of the bounding box
        x = bbox.get('x', 0) + bbox.get('width', 0) / 2
        y = bbox.get('y', 0) + bbox.get('height', 0) / 2
        
        # Convert to Shotstack normalized coordinates (-1 to 1)
        # Figma: (0,0) top-left, Shotstack: (0,0) center
        x_offset = (x - canvas_width / 2) / (canvas_width / 2)
        y_offset = (y - canvas_height / 2) / (canvas_height / 2)
        
        # Clamp to reasonable bounds
        x_offset = max(-1, min(1, x_offset))
        y_offset = max(-1, min(1, y_offset))
        
        return round(x_offset, 3), round(y_offset, 3)
    
    def _extract_node_ids(self, node: Dict[str, Any]) -> List[str]:
        """Recursively extract all node IDs from a page for image fetching"""
        node_ids = []
        
        # Add current node ID if it has visual content
        if node.get('type') in ['FRAME', 'RECTANGLE', 'ELLIPSE', 'POLYGON', 'STAR', 'VECTOR', 'INSTANCE', 'COMPONENT']:
            node_ids.append(node['id'])
        
        # Recursively collect children
        for child in node.get('children', []):
            node_ids.extend(self._extract_node_ids(child))
        
        return node_ids
    
    def _fetch_figma_images(self, file_key: str, node_ids: List[str], format: str = 'png', scale: float = 2.0) -> Dict[str, str]:
        """Fetch image URLs from Figma for given node IDs"""
        try:
            if not node_ids:
                return {}
                
            print(f"Fetching images for {len(node_ids)} nodes...")
            images_response = self.figma.get_file_images(
                file_key=file_key,
                ids=node_ids,
                format=format,
                scale=scale
            )
            
            # Extract images from response object
            if hasattr(images_response, 'images') and images_response.images:
                images = images_response.images
            else:
                images = {}
            
            # Filter out None values and empty URLs
            valid_images = {k: v for k, v in images.items() if v and v.strip()}
            print(f"Successfully fetched {len(valid_images)} images")
            
            return valid_images
            
        except Exception as e:
            print(f"Warning: Failed to fetch images from Figma: {e}")
            return {}
    
    def _extract_all_nodes(self, node: Dict[str, Any], canvas_width: float, canvas_height: float) -> List[Dict[str, Any]]:
        """Recursively extract all nodes from a page"""
        nodes = []
        
        # Parse current node
        parsed = self.parse_node(node, canvas_width, canvas_height)
        if parsed:
            # Add node ID for image fetching
            parsed['node_id'] = node.get('id')
            nodes.append(parsed)
        
        # Recursively parse children
        for child in node.get('children', []):
            nodes.extend(self._extract_all_nodes(child, canvas_width, canvas_height))
        
        return nodes
    
    def convert_to_shotstack(self, file_key: str, page_name: Optional[str] = None, 
                           output_width: int = 1200, output_height: int = 1200,
                           duration: float = 5.0, populate_images: bool = False,
                           image_only: bool = False) -> Dict[str, Any]:
        """Convert Figma page to Shotstack template"""
        
        # Extract page data
        page = self.extract_page(file_key, page_name)
        
        # Get page dimensions (use first frame or default)
        canvas_width = output_width
        canvas_height = output_height
        
        # Find main frame if exists
        main_frame = None
        for child in page.get('children', []):
            if child.get('type') == 'FRAME':
                main_frame = child
                bbox = child.get('absoluteBoundingBox', {})
                canvas_width = bbox.get('width', output_width)
                canvas_height = bbox.get('height', output_height)
                break
        
        # Extract all design elements
        all_nodes = []
        if main_frame:
            all_nodes = self._extract_all_nodes(main_frame, canvas_width, canvas_height)
        else:
            # No main frame, process all children
            for child in page.get('children', []):
                all_nodes.extend(self._extract_all_nodes(child, canvas_width, canvas_height))
        
        # Fetch real images if requested
        figma_images = {}
        if populate_images:
            # Collect all node IDs that need images
            node_ids = [node['node_id'] for node in all_nodes if node.get('node_id') and node.get('type') in ['frame', 'image']]
            if node_ids:
                figma_images = self._fetch_figma_images(file_key, node_ids)
        
        # Adjust duration for image-only mode
        if image_only:
            duration = 1.0  # Minimal duration for static image output
        
        # Build Shotstack timeline
        tracks = []
        merge_variables = []
        variable_counter = 1
        
        for node_data in all_nodes:
            # Create asset for clip
            asset = node_data['asset'].copy()
            
            # Replace with real image URL if available and populate_images is True
            if populate_images and node_data.get('node_id') and node_data.get('node_id') in figma_images:
                real_image_url = figma_images[node_data['node_id']]
                if asset.get('type') == 'image':
                    asset['src'] = real_image_url
                    print(f"Using real image for node {node_data['node_id']}: {real_image_url[:50]}...")
            
            # Create clip for each element
            clip = {
                'asset': asset,
                'start': 0,
                'length': duration,
                'position': node_data['position'],
                'fit': node_data['fit'],
                'scale': node_data['scale']
            }
            
            if 'offset' in node_data:
                clip['offset'] = node_data['offset']
            
            # Handle template variables for images (only if not using real images)
            if '{{' in str(asset.get('src', '')):
                src = asset['src']
                var_match = re.search(r'\{\{\s*(\w+)\s*\}\}', src)
                if var_match:
                    var_name = var_match.group(1)
                    merge_variables.append({
                        'find': var_name,
                        'replace': ''
                    })
            
            tracks.append({'clips': [clip]})
        
        # Build complete Shotstack template
        template = {
            'timeline': {
                'background': '#ffffff',
                'tracks': tracks
            },
            'output': {
                'format': 'png',
                'size': {
                    'width': output_width,
                    'height': output_height
                }
            }
        }
        
        # Add fps only for video/gif output (not for image-only mode)
        if not image_only:
            template['output']['fps'] = 25
        
        if merge_variables:
            template['merge'] = merge_variables
        
        return template
    
    def convert_all_pages_to_shotstack(self, file_key: str, 
                                     output_width: int = 1200, output_height: int = 1200,
                                     duration: float = 5.0, populate_images: bool = False,
                                     image_only: bool = False) -> Dict[str, Dict[str, Any]]:
        """Convert all pages in a Figma file to Shotstack templates"""
        templates = {}
        
        try:
            # Get all pages
            pages = self.extract_all_pages(file_key)
            
            for page in pages:
                page_name = page['name']
                print(f"Converting page: {page_name}")
                
                # Convert this page to a template
                template = self.convert_to_shotstack(
                    file_key=file_key,
                    page_name=page_name,
                    output_width=output_width,
                    output_height=output_height,
                    duration=duration,
                    populate_images=populate_images,
                    image_only=image_only
                )
                
                # Use page name as key (sanitized for filename)
                safe_name = re.sub(r'[^\w\-_]', '_', page_name)
                templates[safe_name] = {
                    'original_name': page_name,
                    'template': template
                }
                
            return templates
            
        except Exception as e:
            raise Exception(f"Failed to convert all pages: {str(e)}")