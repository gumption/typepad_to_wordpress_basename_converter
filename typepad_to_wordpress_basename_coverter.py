#!/usr/bin/env python3

import sys
import re
import string
from typing import Dict, List, Tuple, Any
from collections import defaultdict

def process_file(input_file: str, output_file: str, 
                original_base_url: str = "gumption.typepad.com", 
                new_base_url: str = "interrelativity.com",
                basename_mappings_file: str = "basename_mappings.txt",
                url_replacements_file: str = "url_replacements.txt"):
    """
    Process an input file to:
    1. Find all TITLE and BASENAME strings
    2. Create new BASENAME strings from TITLE strings
    3. Replace old BASENAME strings with new ones
    4. Replace URLs from original_base_url to new_base_url
    5. Track all replacements made
    6. Save mappings and replacements to specified files
    
    Args:
        input_file (str): Path to the input file
        output_file (str): Path to the output file
        original_base_url (str): Original base URL to be replaced (default: "gumption.typepad.com")
        new_base_url (str): New base URL to replace with (default: "interrelativity.com")
        basename_mappings_file (str): File to save basename mappings (default: "basename_mappings.txt")
        url_replacements_file (str): File to save URL replacements (default: "url_replacements.txt")
        
    Returns:
        Tuple[List[Dict], List[Dict]]: A tuple containing:
            - List of dictionaries with title, old_basename, and new_basename
            - List of dictionaries with title, old_url, and new_url for each URL replacement
    """
    # Lists to store mappings and replacements
    basename_mappings = []
    url_replacements = []
    
    # Dictionary to store basename mappings for faster lookup
    basename_mapping_dict = {}
    
    # Dictionary to track title by old_basename
    title_by_basename = {}
    
    # Escape dots and other special characters in the URLs for regex
    original_base_url_escaped = re.escape(original_base_url)
    
    # Pattern to match original URLs
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
        # First pass: Collect all title-basename pairs
        title_basename_pairs = []
        current_title = None
        
        with open(input_file, 'r') as infile:
            for line in infile:
                # Check if line starts with 'TITLE: '
                if line.startswith('TITLE: '):
                    # Extract the title
                    current_title = line[len('TITLE: '):].strip()
                
                # Check if line starts with 'BASENAME: '
                elif line.startswith('BASENAME: '):
                    # Extract the old basename
                    old_basename = line[len('BASENAME: '):].strip()
                    
                    # If we have a title, store the pair
                    if current_title:
                        title_basename_pairs.append((current_title, old_basename))
                        # Reset title to avoid duplicates
                        current_title = None
        
        # Second pass: Create all mappings
        for title, old_basename in title_basename_pairs:
            # Create new basename from title
            new_basename = create_new_basename(title)
            
            # Store mappings
            basename_mapping_dict[old_basename] = new_basename
            title_by_basename[old_basename] = title
            
            # Only add to mappings list if old and new are different
            if old_basename != new_basename:
                mapping = {
                    'title': title,
                    'old_basename': old_basename,
                    'new_basename': new_basename
                }
                basename_mappings.append(mapping)
        
        # Third pass: Apply mappings to the file
        current_title = None
        with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
            for line in infile:
                # Check if line starts with 'TITLE: '
                if line.startswith('TITLE: '):
                    current_title = line[len('TITLE: '):].strip()
                    outfile.write(line)  # Write original line
                
                # Check if line starts with 'BASENAME: '
                elif line.startswith('BASENAME: '):
                    old_basename = line[len('BASENAME: '):].strip()
                    
                    # Get the new basename from our mapping
                    if old_basename in basename_mapping_dict:
                        new_basename = basename_mapping_dict[old_basename]
                        outfile.write(f'BASENAME: {new_basename}\n')
                    else:
                        # If no mapping exists, keep the original
                        outfile.write(line)
                
                # Check if line starts with 'UNIQUE URL: '
                elif line.startswith('UNIQUE URL: '):
                    outfile.write(line)  # Preserve original UNIQUE URL lines
                
                # Process other lines for URL replacements
                else:
                    modified_line = line
                    
                    # Find all URL matches in the line
                    matches = list(url_pattern.finditer(line))
                    
                    # Process matches in reverse order to avoid offset issues when replacing
                    for match in reversed(matches):
                        full_match = match.group(1)
                        year = match.group(2)
                        month = match.group(3)
                        old_path = match.group(4)
                        
                        # Get the title for this URL (if available)
                        url_title = None
                        if old_path in title_by_basename:
                            url_title = title_by_basename[old_path]
                        
                        # Get the new path from our mapping
                        if old_path in basename_mapping_dict:
                            new_path = basename_mapping_dict[old_path]
                            
                            # Create the replacement URL (always using https)
                            new_url = f"https://{new_base_url}/{year}/{month}/{new_path}"
                            
                            # Store the replacement
                            url_replacements.append({
                                'title': url_title,
                                'old_url': full_match,
                                'new_url': new_url
                            })
                            
                            # Replace in the line
                            modified_line = modified_line.replace(full_match, new_url)
                    
                    # Write the modified line
                    outfile.write(modified_line)
        
        # Save basename mappings to file
        with open(basename_mappings_file, 'w') as f:
            for mapping in basename_mappings:
                f.write(f"{mapping['old_basename']},{mapping['new_basename']}\n")
        
        # Save URL replacements to file
        with open(url_replacements_file, 'w') as f:
            for replacement in url_replacements:
                title = replacement['title'] or ''
                # Escape any commas in the title with a backslash
                title = title.replace(',', '\\,')
                f.write(f"{title},{replacement['old_url']},{replacement['new_url']}\n")
        
        print(f"Successfully processed {input_file} and wrote results to {output_file}")
        print(f"Created {len(basename_mappings)} basename mappings (saved to {basename_mappings_file})")
        print(f"Made {len(url_replacements)} URL replacements (saved to {url_replacements_file})")
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
    if len(sys.argv) < 3 or len(sys.argv) > 7:
        print("Usage: python url_basename_processor.py <input_file> <output_file> [original_base_url] [new_base_url] [basename_mappings_file] [url_replacements_file]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    # Set default values
    original_base_url = "gumption.typepad.com"
    new_base_url = "interrelativity.com"
    basename_mappings_file = "basename_mappings.txt"
    url_replacements_file = "url_replacements.txt"
    
    # Override defaults if provided as arguments
    if len(sys.argv) >= 4:
        original_base_url = sys.argv[3]
    if len(sys.argv) >= 5:
        new_base_url = sys.argv[4]
    if len(sys.argv) >= 6:
        basename_mappings_file = sys.argv[5]
    if len(sys.argv) >= 7:
        url_replacements_file = sys.argv[6]
    
    # Process the file
    basename_mappings, url_replacements = process_file(
        input_file, 
        output_file, 
        original_base_url, 
        new_base_url,
        basename_mappings_file,
        url_replacements_file
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
