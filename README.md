# MBox Navigator

MBox Navigator is a command-line tool for interactive navigation and exploration of Unix-style `.mbox` email files. It allows you to browse, search, and extract information from large mailbox archives efficiently. I created this when using Google's Takeout feature to backup entire Google Suite mail accounts and then to verify the integrity of the export. No implied warranty. 

## Features

- Browse messages with pagination
- Search emails by content
- Sort by date, sender, or subject
- Display formatted message content
- Export individual messages
- View mailbox statistics
- Customizable column display

## Dependencies

The tool requires:

- Python 3.8+
- pandas
- tabulate

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/randelsr/mbox-navigator.git
   cd mbox-navigator
   ```

2. (Optional) Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required dependencies:
   ```
   pip install pandas tabulate
   ```

## Usage

### MBox Navigator

Run the navigator with:

```
python mbox_navigator.py /path/to/your/mailbox.mbox
```

#### Commands

Once running, the following commands are available:

| Command | Description | Example |
|---------|-------------|---------|
| `ls [N]` | List the next N messages (default 20) | `ls 30` |
| `next [N]` | Alias for `ls` | `next 10` |
| `prev [N]` | Page backward by N messages (default 20) | `prev` |
| `show <index>` | Display the full contents of the message at the specified index | `show 5` |
| `search <text>` | Case-insensitive search in From/Subject fields | `search important` |
| `sort <field> [desc]` | Sort messages by field (from/date/subject), optionally descending | `sort date desc` |
| `cols <col1,col2,...>` | Customize which columns to display | `cols from,subject,date` |
| `save <index> <file.eml>` | Save a specific message to a file | `save 10 message.eml` |
| `info` | Display mailbox statistics | `info` |
| `help` | List available commands | `help` |
| `quit` | Exit the navigator | `quit` |

#### Example Session

```
$ python mbox_navigator.py ~/Downloads/archive.mbox
Indexing… (this may take a minute on very large files)
Loaded 2,345 messages from /home/user/Downloads/archive.mbox

Type 'help' for command list, 'quit' to exit

(mbox) ls
Messages 0 to 19
+----+------------+------------------------------+------------------------------------------+
|    | date       | from                         | subject                                  |
|----+------------+------------------------------+------------------------------------------|
|  0 | 2023-05-20 | John Smith <john@example.co  | Project kickoff meeting                  |
|  1 | 2023-05-21 | Sarah Jones <sarah@example.  | Re: Project kickoff meeting             |
...

(mbox) search important
Found 3 matches (showing first 100)
+-----+------------+------------------------------+------------------------------------------+
|     | date       | from                         | subject                                  |
|-----+------------+------------------------------+------------------------------------------|
|  12 | 2023-06-01 | Manager <boss@example.com>   | IMPORTANT: Deadline reminder            |
|  24 | 2023-06-14 | System <noreply@example.com> | Important security update               |
| 145 | 2023-07-22 | HR <hr@example.com>          | Important: Policy changes               |
+-----+------------+------------------------------+------------------------------------------+

(mbox) show 12
================================================================================
From: Manager <boss@example.com>
To: Team <team@example.com>
Cc: Executives <exec@example.com>
Date: Thu, 01 Jun 2023 09:15:33 -0700
Subject: IMPORTANT: Deadline reminder
--------------------------------------------------------------------------------
Hello team,

This is a reminder that the project deadline is next Friday. Please make sure 
all deliverables are completed by end of day Thursday.

Best regards,
Your Manager
================================================================================
```

# MBox Split

The `mbox-split.py` tool helps you extract messages from a specific year from an mbox file. This is useful when you need to filter large mailbox archives by date.

```
python mbox-split.py source.mbox year output.mbox [options]
```

#### Arguments

| Argument | Description |
|----------|-------------|
| `source.mbox` | Source mbox file to read from |
| `year` | Year to filter by (e.g., 2023) |
| `output.mbox` | Output file to save filtered messages |

#### Options

| Option | Description |
|--------|-------------|
| `--debug` | Show detailed debug information during processing |
| `--sample N` | Show sample of N messages and their parsed dates without creating output file |

#### Examples

Extract all messages from 2023:
```
python mbox-split.py archive.mbox 2023 archive-2023.mbox
```

Check date parsing for 10 sample messages without creating an output file:
```
python mbox-split.py archive.mbox 2023 output.mbox --sample 10
```

Run with debug information to see detailed date parsing:
```
python mbox-split.py archive.mbox 2022 archive-2022.mbox --debug
```

The tool uses multiple strategies to extract the year from email date headers, making it robust against different date formats.


