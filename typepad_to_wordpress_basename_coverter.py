#!/usr/bin/env python3

import sys
import re
import string
from typing import Dict, List, Tuple, Any
from collections import defaultdict

def process_file(input_file: str, output_file: str, original_base_url: str = "gumption.typepad.com", new_base_url: str = "interrelativity.com"):
    """
    Process an input file to:
    1. Find all TITLE and BASENAME strings
    2. Create new BASENAME strings from TITLE strings
    3. Replace old BASENAME strings with new ones
    4. Replace URLs from original_base_url to new_base_url
    5. Track all replacements made
    
    Args:
        input_file (str): Path to the input file
        output_file (str): Path to the output file
        original_base_url (str): Original base URL to be replaced (default: "gumption.typepad.com")
        new_base_url (str): New base URL to replace with (default: "interrelativity.com")
        
    Returns:
        Tuple[List[Dict], List[Dict]]: A tuple containing:
            - List of dictionaries with title, old_basename, and new_basename
            - List of dictionaries with title, old_url, and new_url for each URL replacement
    """
    # Lists to store mappings and replacements
    basename_mappings = []
    url_replacements = []
    
    # Variables to track current state
    current_title = None
    current_old_basename = None
    current_new_basename = None
    
    # Dictionary to store basename mappings for faster lookup
    basename_mapping_dict = {}
    
    # Escape dots and other special characters in the URLs for regex
    original_base_url_escaped = re.escape(original_base_url)
    
    # Pattern to match original URLs
    # This pattern will match http or https, followed by the escaped original base URL,
    # followed by /blog/YYYY/MM/basename.html
    url_pattern = re.compile(f'(https?://{original_base_url_escaped}/blog/(\d{{4}})/(\d{{2}})/([^.]+)\.html)')
    
    # Function to create new_basename from title
    def create_new_basename(title):
        if not title:
            return None
        
        # Convert to lowercase
        result = title.lower()
        
        # Create a custom punctuation set that excludes hyphens
        custom_punctuation = ''.join(char for char in string.punctuation if char != '-')
        
        # Remove all punctuation except hyphens
        result = ''.join(char for char in result if char not in custom_punctuation)
        
        # Replace whitespace with hyphens
        result = re.sub(r'\s+', '-', result.strip())
        
        return result
    
    try:
        # First pass: Collect all TITLE and BASENAME pairs and create mappings
        with open(input_file, 'r') as infile:
            for line in infile:
                # Check if line starts with 'TITLE: '
                if line.startswith('TITLE: '):
                    # Extract the title
                    current_title = line[len('TITLE: '):].strip()
                    # Create new basename from the title
                    current_new_basename = create_new_basename(current_title)
                
                # Check if line starts with 'BASENAME: '
                elif line.startswith('BASENAME: '):
                    # Extract the old basename
                    current_old_basename = line[len('BASENAME: '):].strip()
                    
                    # If we have both title and new_basename, store the mapping
                    if current_title and current_new_basename:
                        # Only store if old and new are different
                        if current_old_basename != current_new_basename:
                            mapping = {
                                'title': current_title,
                                'old_basename': current_old_basename,
                                'new_basename': current_new_basename
                            }
                            basename_mappings.append(mapping)
                            basename_mapping_dict[current_old_basename] = current_new_basename
        
        # Reset tracking variables for second pass
        current_title = None
        current_old_basename = None
        current_new_basename = None
        
        # Second pass: Process the file and make replacements
        with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
            for line in infile:
                # Check if line starts with 'TITLE: '
                if line.startswith('TITLE: '):
                    current_title = line[len('TITLE: '):].strip()
                    current_new_basename = create_new_basename(current_title)
                    outfile.write(line)  # Write original line
                
                # Check if line starts with 'BASENAME: '
                elif line.startswith('BASENAME: '):
                    current_old_basename = line[len('BASENAME: '):].strip()
                    
                    # Write the new basename line
                    if current_new_basename:
                        outfile.write(f'BASENAME: {current_new_basename}\n')
                    else:
                        outfile.write(line)  # Keep original if no new basename
                
                # Check if line starts with 'UNIQUE URL: '
                elif line.startswith('UNIQUE URL: '):
                    outfile.write(line)  # Preserve original UNIQUE URL lines
                
                # Process other lines for URL replacements
                else:
                    modified_line = line
                    
                    # Find all URL matches in the line
                    matches = url_pattern.finditer(line)
                    
                    for match in matches:
                        full_match = match.group(1)
                        year = match.group(2)
                        month = match.group(3)
                        path = match.group(4)
                        
                        # Check if this path is in our basename mapping
                        new_path = path
                        if path in basename_mapping_dict:
                            new_path = basename_mapping_dict[path]
                        
                        # Create the replacement URL (always using https)
                        new_url = f"https://{new_base_url}/{year}/{month}/{new_path}"
                        
                        # Store the replacement
                        url_replacements.append({
                            'title': current_title,
                            'old_url': full_match,
                            'new_url': new_url
                        })
                        
                        # Replace in the line
                        modified_line = modified_line.replace(full_match, new_url)
                    
                    # Write the modified line
                    outfile.write(modified_line)
        
        print(f"Successfully processed {input_file} and wrote results to {output_file}")
        print(f"Created {len(basename_mappings)} basename mappings")
        print(f"Made {len(url_replacements)} URL replacements")
        print(f"Replaced URLs from '{original_base_url}' to '{new_base_url}'")
        
        return basename_mappings, url_replacements
    
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
        return [], []
    except Exception as e:
        print(f"Error occurred: {e}")
        return [], []

def main():
    # Parse command line arguments
    if len(sys.argv) < 3 or len(sys.argv) > 5:
        print("Usage: python url_basename_processor.py <input_file> <output_file> [original_base_url] [new_base_url]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    # Set default values for base URLs
    original_base_url = "gumption.typepad.com"
    new_base_url = "interrelativity.com"
    
    # Override defaults if provided as arguments
    if len(sys.argv) >= 4:
        original_base_url = sys.argv[3]
    if len(sys.argv) >= 5:
        new_base_url = sys.argv[4]
    
    # Process the file
    basename_mappings, url_replacements = process_file(
        input_file, 
        output_file, 
        original_base_url, 
        new_base_url
    )
    
    # Print summary of basename mappings
    if basename_mappings:
        print("\nBasename Mapping Summary:")
        for i, mapping in enumerate(basename_mappings[:5], 1):
            print(f"\n{i:3d}. Title: {mapping['title']}")
            print(f"     Old Basename: '{mapping['old_basename']}'")
            print(f"     New Basename: '{mapping['new_basename']}'")
        
        if len(basename_mappings) > 5:
            print(f"\n... and {len(basename_mappings) - 5} more mappings")
    
    # Print summary of URL replacements
    if url_replacements:
        print("\nURL Replacement Summary:")
        for i, replacement in enumerate(url_replacements[:5], 1):
            print(f"\n{i:3d}. Title: {replacement['title'] or '(No title available)'}")
            print(f"     Old URL: {replacement['old_url']}")
            print(f"     New URL: {replacement['new_url']}")
        
        if len(url_replacements) > 5:
            print(f"\n... and {len(url_replacements) - 5} more replacements")

if __name__ == "__main__":
    main()
