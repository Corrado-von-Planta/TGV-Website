#!/usr/bin/env python3

import os
import re
import requests
from pathlib import Path
import sys

def download_image(image_path):
    """Download image from tgv4plus.com and save locally."""
    # Remove leading _/ from path
    remote_path = image_path[2:] if image_path.startswith('_/') else image_path
    
    # Try PNG first, then JPG
    for ext in ['.png', '.jpg', '.jpeg']:
        url = f"https://tgv4plus.com/{remote_path}{ext}"
        print(f"  Trying to download: {url}")
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                # Create local directory structure
                local_path = Path(f"_/{remote_path}{ext}")
                local_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Save the image
                with open(local_path, 'wb') as f:
                    f.write(response.content)
                print(f"  ✓ Downloaded and saved to: {local_path}")
                
                # Return the relative path for HTML
                return f"./{remote_path}{ext}"
        except Exception as e:
            print(f"  ✗ Failed to download {ext}: {e}")
    
    return None

def process_html_file(filepath):
    """Process a single HTML file to download and update background images."""
    print(f"\nProcessing: {filepath}")
    
    # Read the HTML file
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Keep original content for comparison
    original_content = content
    
    # Find all occurrences of wsite-section-bg-image class and their style attributes
    # This pattern finds the class and captures everything until the closing of style attribute
    pattern = r'class="[^"]*wsite-section-bg-image[^"]*"[^>]*?style="([^"]*?background-image:\s*url\((_/uploads/[^)]+?)\.html\)[^"]*?)"'
    
    matches = re.findall(pattern, content)
    
    if not matches:
        print("  No elements with class 'wsite-section-bg-image' and background-image found")
        return False
    
    modified = False
    replacements = []
    
    for full_style, image_path in matches:
        print(f"  Found background image: {image_path}.html")
        
        # Download the image
        new_path = download_image(image_path)
        
        if new_path:
            # Prepare the replacement
            old_url = f"url({image_path}.html)"
            new_url = f"url({new_path})"
            new_style = full_style.replace(old_url, new_url)
            
            # Store the replacement
            replacements.append((full_style, new_style))
            print(f"  ✓ Will update background-image URL to: {new_url}")
            modified = True
    
    if modified:
        # Apply all replacements
        for old_style, new_style in replacements:
            # Use exact string replacement to avoid any other changes
            content = content.replace(f'style="{old_style}"', f'style="{new_style}"', 1)
        
        # Verify we only changed what we intended
        changes = 0
        for i, (old_char, new_char) in enumerate(zip(original_content, content)):
            if old_char != new_char:
                changes += 1
        
        # Save the modified HTML
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✓ Saved modified HTML to: {filepath}")
        print(f"  Total character changes: {len(replacements)} URLs modified")
        return True
    
    return False

def main():
    """Main function to process HTML files."""
    html_dir = Path('_')
    
    if not html_dir.exists():
        print("Error: _/ directory not found")
        sys.exit(1)
    
    # Find all HTML files
    html_files = list(html_dir.glob('*.html'))
    
    if not html_files:
        print("No HTML files found in _/ directory")
        sys.exit(1)
    
    print(f"Found {len(html_files)} HTML files")
    print(f"\n=== Processing all HTML files ===\n")
    
    processed_count = 0
    modified_count = 0
    
    for html_file in html_files:
        # Quick check if file contains our target class
        with open(html_file, 'r', encoding='utf-8') as f:
            if 'wsite-section-bg-image' in f.read():
                processed_count += 1
                success = process_html_file(html_file)
                if success:
                    modified_count += 1
    
    print(f"\n=== Summary ===")
    print(f"Total HTML files: {len(html_files)}")
    print(f"Files with target class: {processed_count}")
    print(f"Files modified: {modified_count}")
    print(f"✓ Processing complete!")

if __name__ == "__main__":
    main()