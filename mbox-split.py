#!/usr/bin/env python3
"""
mbox-split.py - Split mbox files by message year
Usage: python mbox-split.py source.mbox year output.mbox
Example: python mbox-split.py full.mbox 2024 split-2024.mbox
"""

import mailbox
import sys
import os
import email
import argparse
import re
from email.header import decode_header, make_header
from datetime import datetime

def clean_header(raw):
    if raw is None:
        return ''
    try:
        return str(make_header(decode_header(raw)))
    except Exception:
        return raw

def get_year_from_date(date_str, debug=False):
    if not date_str:
        return None
        
    if debug:
        print(f"Parsing date: {date_str}")
    
    # Try regex pattern for year first (most reliable)
    year_patterns = [
        r'20\d\d',       # Match 20xx
        r'19\d\d',       # Match 19xx
    ]
    
    for pattern in year_patterns:
        matches = re.findall(pattern, date_str)
        if matches:
            if debug:
                print(f"  Found year via regex: {matches[0]}")
            return matches[0]
    
    # Try various date formats
    date_formats = [
        '%a, %d %b %Y',
        '%d %b %Y',
        '%b %d %Y',
        '%Y-%m-%d',
        '%a, %d %b %Y %H:%M:%S',
        '%a %b %d %H:%M:%S %Y',
        '%d %b %Y %H:%M:%S',
    ]
    
    # For each format, try parsing with various lengths of the date string
    for fmt in date_formats:
        for length in [25, 30, len(date_str)]:
            try:
                if length > len(date_str):
                    length = len(date_str)
                dt = datetime.strptime(date_str[:length], fmt)
                if debug:
                    print(f"  Parsed with format {fmt}: {dt.year}")
                return str(dt.year)
            except ValueError:
                continue
    
    # Last resort: try to find any 4-digit number that looks like a year
    words = date_str.split()
    for word in words:
        if word.isdigit() and len(word) == 4:
            if debug:
                print(f"  Found possible year: {word}")
            return word
    
    if debug:
        print("  Failed to parse date")
    return None

def main():
    parser = argparse.ArgumentParser(description='Split mbox file by message year')
    parser.add_argument('source', help='Source mbox file')
    parser.add_argument('year', help='Year to filter by')
    parser.add_argument('output', help='Output mbox file')
    parser.add_argument('--debug', action='store_true', help='Show debug information')
    parser.add_argument('--sample', type=int, default=0, 
                       help='Show sample of N messages and their parsed dates')
    
    args = parser.parse_args()
    
    source = args.source
    year_filter = args.year
    output = args.output
    debug = args.debug
    
    if not os.path.exists(source):
        sys.exit(f"Error: Source file '{source}' not found.")
    
    if os.path.exists(output):
        os.remove(output)
    
    source_mbox = mailbox.mbox(source)
    output_mbox = mailbox.mbox(output)
    output_mbox.lock()
    
    try:
        count = 0
        total = len(source_mbox)
        print(f"Processing {total} messages...")
        
        # Sample mode - show date parsing for a few messages
        if args.sample > 0:
            sample_count = min(args.sample, total)
            print(f"\nSAMPLE MODE: Showing date parsing for {sample_count} messages")
            for i, key in enumerate(list(source_mbox.iterkeys())[:sample_count]):
                msg = source_mbox.get(key)
                date = clean_header(msg.get('date'))
                subject = clean_header(msg.get('subject'))
                print(f"\nMessage {i+1}:")
                print(f"  Subject: {subject[:50]}...")
                print(f"  Date header: {date}")
                msg_year = get_year_from_date(date, debug=True)
                print(f"  Extracted year: {msg_year}")
            return
        
        for key in source_mbox.iterkeys():
            msg = source_mbox.get(key)
            date = clean_header(msg.get('date'))
            
            msg_year = get_year_from_date(date, debug=debug)
            if date and msg_year and year_filter == msg_year:
                output_mbox.add(msg)
                count += 1
                if debug and count <= 5:
                    print(f"Matched: {date} -> {msg_year}")
                    
        print(f'Processed {total} messages')
        print(f'Extracted {count} messages from year {year_filter} to {output}')
    except KeyboardInterrupt:
        print("\nOperation interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        output_mbox.unlock()
        output_mbox.close()
        source_mbox.close()
    
    print("Done.")

if __name__ == "__main__":
    main() 