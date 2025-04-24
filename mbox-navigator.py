#!/usr/bin/env python3
"""
mbox_navigator.py
–––––––––––––––––
Interactive command-line navigator for large Unix-style .mbox files.

USAGE
    python mbox_navigator.py /path/to/mailbox.mbox

DEPENDENCIES
    • Python 3.8+ (stdlib: mailbox, cmd, email, textwrap, argparse)
    • pandas
    • tabulate
"""

import argparse
import mailbox
import cmd
import textwrap
import email
from email.header import decode_header, make_header
from datetime import datetime
import shutil
import sys
import os
import pandas as pd
from tabulate import tabulate

WRAP = shutil.get_terminal_size((120, 30)).columns


def clean_header(raw):
    """Decode RFC-2047 encoded headers to readable UTF-8."""
    if raw is None:
        return ""
    try:
        return str(make_header(decode_header(raw)))
    except Exception:  # some encodings are broken – fallback
        return raw


class MboxNavigator(cmd.Cmd):
    intro = "\nType 'help' for command list, 'quit' to exit\n"
    prompt = "(mbox) "

    def __init__(self, path):
        super().__init__()
        self.path = os.path.abspath(path)
        self.mbox = mailbox.mbox(self.path)
        self.df = None         # pandas DataFrame
        self._build_index()
        self.cursor = 0        # current list position (for paging)
        self.display_cols = ['date', 'from', 'subject']  # Default columns to display

    # ──────────────────────────────────────────────────────────────
    #  Indexing
    # ──────────────────────────────────────────────────────────────
    def _build_index(self):
        print("Indexing… (this may take a minute on very large files)")
        data = []
        for key in self.mbox.iterkeys():
            msg = self.mbox.get(key)
            subj = clean_header(msg.get('subject'))
            frm = clean_header(msg.get('from'))
            date = clean_header(msg.get('date'))
            to = clean_header(msg.get('to'))
            data.append({
                'key': key,
                'from': frm,
                'date': date,
                'subject': subj,
                'to': to
            })
        
        self.df = pd.DataFrame(data)
        # Try to convert date to datetime for better sorting
        try:
            self.df['date_parsed'] = pd.to_datetime(self.df['date'], errors='coerce', utc=True)
            # Create a shorter date format for display
            self.df['date'] = self.df['date_parsed'].dt.strftime('%Y-%m-%d')
        except:
            pass  # If conversion fails, we'll use string dates
            
        print(f"Loaded {len(self.df):,} messages from {self.path}\n")

    # ──────────────────────────────────────────────────────────────
    #  Helper utilities
    # ──────────────────────────────────────────────────────────────
    def _display_table(self, df_subset, title=None):
        """Display a pandas DataFrame as a formatted table"""
        # Add index column for message reference
        display_df = df_subset.copy()
        
        # Truncate long strings to fit in terminal
        for col in ['from', 'subject']:
            if col in display_df.columns:
                max_width = 30 if col == 'from' else WRAP - 60
                display_df[col] = display_df[col].str.slice(0, max_width)
        
        # Display the table
        if title:
            print(f"\n{title}")
        
        # Use tabulate for pretty display with row indices
        print(tabulate(
            display_df[self.display_cols], 
            headers=self.display_cols,
            showindex=True,
            tablefmt='psql'
        ))

    def _get_msg(self, idx):
        try:
            key = self.df.iloc[idx]['key']
            return self.mbox.get(key)
        except IndexError:
            print("Index out of range.")
            return None

    # ──────────────────────────────────────────────────────────────
    #  CLI commands
    # ──────────────────────────────────────────────────────────────
    def do_ls(self, arg):
        """ls [N]   – list the next N messages (default 20)"""
        try:
            n = int(arg.strip()) if arg else 20
        except ValueError:
            n = 20
        
        end = min(self.cursor + n, len(self.df))
        display_slice = self.df.iloc[self.cursor:end]
        
        self._display_table(display_slice, f"Messages {self.cursor} to {end-1}")
        
        self.cursor = end if end < len(self.df) else 0

    def do_next(self, arg):
        """next     – alias for ls"""
        self.do_ls(arg)

    def do_prev(self, arg):
        """prev     – page backward by N (default 20)"""
        try:
            n = int(arg.strip()) if arg else 20
        except ValueError:
            n = 20
        self.cursor = max(self.cursor - 2 * n, 0)
        self.do_ls(str(n))

    def do_cols(self, arg):
        """cols <col1,col2,...>   – set columns to display (from,date,subject,to)"""
        if not arg:
            print(f"Current display columns: {','.join(self.display_cols)}")
            print("Available columns: from,date,subject,to")
            return
            
        cols = [col.strip() for col in arg.split(',')]
        valid_cols = [col for col in cols if col in self.df.columns and col != 'key']
        
        if not valid_cols:
            print("No valid columns specified. Available columns: from,date,subject,to")
            return
            
        self.display_cols = valid_cols
        print(f"Display columns set to: {','.join(self.display_cols)}")
        # Show the current page with new columns
        self.do_ls('')

    def do_show(self, arg):
        """show <index>   – display full message at that index"""
        if not arg.isdigit():
            print("Usage: show <index>")
            return
        idx = int(arg)
        msg = self._get_msg(idx)
        if not msg:
            return
        print("=" * WRAP)
        for h in ('From', 'To', 'Cc', 'Date', 'Subject'):
            print(f"{h}: {clean_header(msg.get(h))}")
        print("-" * WRAP)
        body = self._get_body(msg)
        print(textwrap.fill(body, WRAP))
        print("=" * WRAP)

    def do_search(self, arg):
        """search <text>  – case-insensitive search in From / Subject"""
        q = arg.strip().lower()
        if not q:
            print("search <text>")
            return
            
        # Pandas-based search
        mask = (
            self.df['from'].str.lower().str.contains(q, na=False) | 
            self.df['subject'].str.lower().str.contains(q, na=False)
        )
        results = self.df[mask]
        
        if len(results) == 0:
            print("No matches found")
            return
            
        # Display results with tabulate
        self._display_table(results.head(100), f"Found {len(results)} matches (showing first 100)")

    def do_save(self, arg):
        """save <index> <outfile.eml>   – save raw message to disk"""
        parts = arg.split()
        if len(parts) != 2 or not parts[0].isdigit():
            print("Usage: save <index> <outfile.eml>")
            return
        idx, outfile = int(parts[0]), parts[1]
        msg = self._get_msg(idx)
        if not msg:
            return
        with open(outfile, "wb") as f:
            f.write(bytes(msg))
        print(f"Saved → {outfile}")

    def do_info(self, _):
        """info      – show mailbox statistics"""
        print(f"Path        : {self.path}")
        print(f"Messages    : {len(self.df):,}")
        sizes = os.path.getsize(self.path) / (1024 ** 2)
        print(f"Size (MB)   : {sizes:,.2f}")
        
        # Add pandas-specific info
        if 'date_parsed' in self.df.columns:
            try:
                earliest = self.df['date_parsed'].min().strftime("%Y-%m-%d")
                latest = self.df['date_parsed'].max().strftime("%Y-%m-%d")
                print(f"Date Range  : {earliest} to {latest}")
            except:
                pass
        
        # Show data statistics
        print("\nMessage Sources:")
        domains = self.df['from'].str.extract(r'@([\w.-]+)', expand=False)
        domain_counts = domains.value_counts().head(5)
        for domain, count in domain_counts.items():
            if pd.notna(domain):
                print(f"  @{domain}: {count} messages")

    def do_sort(self, arg):
        """sort <field> [desc]  – sort by field (from/date/subject), optionally descending"""
        args = arg.strip().split()
        if not args or args[0] not in ('from', 'date', 'subject'):
            print("Usage: sort <field> [desc] - where field is one of: from, date, subject")
            return
            
        field = args[0]
        ascending = len(args) < 2 or args[1].lower() != 'desc'
        
        # Use date_parsed for sorting if available
        if field == 'date' and 'date_parsed' in self.df.columns:
            sort_field = 'date_parsed'
        else:
            sort_field = field
            
        self.df = self.df.sort_values(by=sort_field, ascending=ascending)
        print(f"Sorted by {field} {'ascending' if ascending else 'descending'}")
        self.cursor = 0  # Reset cursor to beginning
        self.do_ls('')  # Show first page

    def do_quit(self, _):
        """quit      – leave the navigator"""
        print("Good-bye!")
        return True

    def do_EOF(self, _):
        return self.do_quit(_)

    # ──────────────────────────────────────────────────────────────
    #  Static helpers
    # ──────────────────────────────────────────────────────────────
    @staticmethod
    def _get_body(msg):
        if msg.is_multipart():
            for part in msg.walk():
                ctype = part.get_content_type()
                disp = part.get("Content-Disposition", "")
                if ctype == "text/plain" and "attachment" not in disp:
                    return part.get_payload(decode=True).decode(
                        part.get_content_charset("utf-8"), "ignore"
                    )
        else:
            return msg.get_payload(decode=True).decode(
                msg.get_content_charset("utf-8", "ignore"), "ignore"
            )
        return "[No plain-text body found]"


def main():
    parser = argparse.ArgumentParser(description="Navigate a .mbox file interactively")
    parser.add_argument("mbox_file", help="Path to the mbox file")
    args = parser.parse_args()

    if not os.path.exists(args.mbox_file):
        sys.exit(f"File not found: {args.mbox_file}")

    try:
        MboxNavigator(args.mbox_file).cmdloop()
    except KeyboardInterrupt:
        print("\nInterrupted. Bye!")


if __name__ == "__main__":
    main()
