# Xit

A powerful command-line task management tool that parses and manages tasks from `.xit` and `.md` files using a simple, human-readable syntax.

## Features

- **Multiple Task States**: Open, checked, ongoing, obsolete, and in-question tasks
- **Priority Levels**: Support for multiple priority indicators (`!`, `!!`, `!!!`)
- **Due Dates**: Flexible date parsing with various formats
- **Tags**: Organize tasks with hashtags and optional values
- **Multi-line Descriptions**: Support for continued task descriptions
- **Groups & Headers**: Organize related tasks under headers
- **Rich Output**: Beautiful terminal output with colors and formatting
- **Flexible Filtering**: Filter tasks by status, priority, tags, and more
- **Statistics**: Get insights about your task distribution
- **🚀 Batch Processing**: Mark, reschedule, remove, or move multiple tasks at once
- **🔄 Recurring Tasks**: Create recurring instances with flexible intervals (daily, weekly, monthly, yearly)
- **Shell Integration**: Support for shell expansion (`{3..21}`) and sequences
- **Status Flags**: Intuitive `--done`, `--ongoing`, `--obsolete` flags instead of cryptic symbols
- **Smart Error Handling**: Individual task feedback with batch operation summaries

## Installation

### Prerequisites

- Python 3.14+
- Micromamba or Conda (recommended)

### Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd todo
   ```

2. Create the environment:
   ```bash
   micromamba create -f micromamba.yaml
   micromamba activate xit
   ```

3. Install dependencies:
   ```bash
   pip install -e .
   ```

## Usage

### Command Line Interface

#### Viewing Tasks

```bash
# Show all tasks in current directory
python -m xit show

# Show tasks from specific files
python -m xit -f tasks.xit show

# Show only open tasks
python -m xit show --status open

# Show tasks with IDs for reference
python -m xit show --show-id

# Show task statistics
python -m xit stats

# Show help
python -m xit --help
```

#### Managing Tasks

```bash
# Add a new task
xit add "Buy groceries"
xit add "!! Important meeting -> 2025-12-15 #work" -f work.xit

# Mark tasks with new status flags (supports batch processing)
xit mark 5 --done                      # Mark single task as done
xit mark 2 3 4 5 6 --done             # Mark multiple tasks as done
xit mark {3..21} --ongoing             # Mark task range as ongoing (bash expansion)
xit mark 1 --open                      # Reopen a task
xit mark 7 8 --obsolete               # Mark tasks as obsolete
xit mark 9 --inquestion               # Mark task as in question

# Reschedule tasks (supports batch processing)
xit reschedule 5 2025-12-31            # Set specific date for single task
xit reschedule 2 3 4 today             # Set multiple tasks to today
xit reschedule {3..21} tomorrow        # Set task range to tomorrow (bash expansion)
xit reschedule 1 2 "+1w"               # Add one week to multiple tasks

# Remove tasks (supports batch processing with confirmation)
xit rm 5                               # Remove single task (with confirmation)
xit rm 2 3 4 5                        # Remove multiple tasks (confirmation for each)
xit rm {3..21}                         # Remove task range (bash expansion)

# Move tasks between files (supports batch processing)
xit move 5 --target other.xit          # Move single task to another file
xit move 2 3 4 --target done.xit      # Move multiple tasks to done.xit
xit move {3..21} --target archive.xit  # Move task range to archive.xit

# Create recurring instances of tasks
xit recur 5 --interval 1w --count 4    # Create 4 weekly instances of task #5
xit recur 3 -i 2w -n 5                # Create 5 bi-weekly instances of task #3
xit recur 7 -i 1m -e 2026-12-31       # Monthly recurrence until end of 2026
xit recur 2 -i 1d -n 30 -t work.xit  # 30 daily instances in work.xit file
```

#### Key Features

- **Batch Processing**: All task modification commands support multiple task IDs
- **Shell Expansion**: Use `{3..21}` syntax for ranges or `$(seq 1 5)` for sequences
- **Order Preservation**: Tasks are processed in the order you specify
- **Individual Confirmations**: Remove operations ask for confirmation on each task
- **Progress Summaries**: Batch operations show success/failure counts
- **Error Handling**: Missing tasks are reported without stopping batch operations

### Task Syntax

XitFlow uses a simple, intuitive syntax for defining tasks:

#### Basic Task States

```xit
[ ] Open task
[x] Completed task
[@] Ongoing task
[~] Obsolete task
[?] Task in question
```

#### Priority Levels

```xit
! High priority task
!! Higher priority task
!!! Highest priority task
.! Mixed priority indicators
```

#### Due Dates

```xit
[ ] Task with due date -> 2025-12-31
[ ] Task due this month -> 2025-12
[ ] Task due next week -> W50
[ ] Task due next quarter -> Q4
```

#### Tags

```xit
[ ] Task with #simple #tags
[ ] Task with #tag=value #project="My Project"
[ ] Task with #priority=high #context='work'
```

#### Multi-line Descriptions

```xit
[ ] This is a longer task description ...
    that continues on the next line
    and can span multiple lines
```

#### Groups and Headers

```xit
Work Tasks
[ ] Review code
[ ] Update documentation

Personal Tasks
[ ] Buy groceries
[ ] Call dentist
```

## Available Commands

### Core Commands

| Command | Description | Batch Support |
|---------|-------------|---------------|
| `show` | Display tasks with filtering options | N/A |
| `stats` | Show task statistics and summaries | N/A |
| `add` | Create new tasks with metadata | ✅ Single |
| `mark` | Change task status with intuitive flags | ✅ **Batch** |
| `reschedule` | Update task due dates | ✅ **Batch** |
| `rm` | Remove tasks (with confirmation) | ✅ **Batch** |
| `move` | Move tasks between files | ✅ **Batch** |
| `recur` | Create recurring instances of tasks | ✅ Single |

### Status Flag Reference

All status changes use intuitive flags instead of cryptic symbols:

```bash
--open         # [ ] Reopen completed/ongoing tasks
--done         # [x] Mark tasks as completed  
--ongoing      # [@] Mark tasks as in progress
--obsolete     # [~] Mark tasks as no longer relevant
--inquestion   # [?] Mark tasks as needing clarification
```

### Batch Processing Examples

```bash
# Process multiple individual tasks
xit mark 1 3 5 7 9 --done
xit reschedule 2 4 6 8 "next friday"
xit move 10 12 14 --target archive.xit

# Use shell expansion for ranges
xit mark {1..10} --ongoing        # Tasks 1 through 10
xit rm {15..25}                   # Remove tasks 15 through 25
xit reschedule {5..8} tomorrow    # Reschedule tasks 5, 6, 7, 8

# Mixed approaches
xit mark 1 5 {10..15} 20 --done  # Tasks 1, 5, 10-15, and 20
xit move 3 7 {12..18} --target completed.xit
```

## Workflow Examples

### Daily Task Management

```bash
# Morning: Review what needs to be done
xit show --status open

# Work on urgent items
xit mark {1..5} --ongoing

# Complete some tasks throughout the day  
xit mark 1 3 --done

# Reschedule non-urgent items
xit reschedule 7 8 9 tomorrow

# End of day: Archive completed work
xit move {1..10} --target archive/$(date +%Y-%m-%d).xit
```

### Project Cleanup

```bash
# Find tasks with IDs for batch operations
xit show --show-id --tag project-alpha

# Mark entire project as obsolete
xit mark {15..28} --obsolete

# Or move to project archive
xit move {15..28} --target projects/alpha-archive.xit

# Remove truly unnecessary tasks (with confirmation)
xit rm {30..35}
```

### Weekly Review

```bash
# See what's overdue or due soon
xit show --due-by today
xit show --due-by "+1w"

# Batch reschedule overdue items
xit reschedule {1..12} "next monday"

# Clean up obsolete tasks
xit show --status obsolete
xit rm {20..35}  # Confirm each removal
```

### Recurring Tasks

The `recur` command allows you to create recurring instances of existing tasks with customizable intervals and limits:

```bash
# Create weekly recurring meeting
xit add "Team standup -> 2025-10-21"
xit show --show-id  # Find the task ID (e.g., #5)
xit recur 5 --interval 1w --count 8    # Create 8 weeks worth

# Monthly reports with end date
xit recur 3 --interval 1m --end-date 2026-12-31

# Daily tasks for a project sprint
xit recur 12 -i 1d -n 14 --target-file sprint.xit
```

#### Interval Formats

- **Days**: `1d`, `7d`, `30d` - Daily intervals
- **Weeks**: `1w`, `2w`, `4w` - Weekly intervals  
- **Months**: `1m`, `3m`, `6m` - Monthly intervals (30-day periods)
- **Years**: `1y`, `2y` - Yearly intervals (365-day periods)

#### Recurrence Options

| Option | Short | Description |
|--------|-------|-------------|
| `--interval` | `-i` | Recurrence interval (required) |
| `--count` | `-n` | Maximum number of instances |
| `--end-date` | `-e` | End date for recurrence (YYYY-MM-DD) |
| `--target-file` | `-t` | File for new tasks (default: original file) |

#### Recurring Task Behavior

- **Preserves Properties**: Priority, tags, and descriptions are copied
- **Updates Due Dates**: Each instance gets the calculated next due date
- **Original Unchanged**: Source task remains unmodified
- **Smart Scheduling**: Tasks without due dates start from tomorrow
- **Flexible Limits**: Use either count or end-date (mutually exclusive)

#### Examples by Use Case

**Weekly Meetings**:
```bash
xit recur 5 -i 1w -n 12  # 3 months of weekly meetings
```

**Monthly Reports**:
```bash  
xit recur 8 -i 1m -e 2026-06-30  # Until mid-2026
```

**Daily Standups (Sprint)**:
```bash
xit recur 3 -i 1d -n 10 -t sprint.xit  # 2-week sprint in separate file
```

**Quarterly Reviews**:
```bash
xit recur 15 -i 3m -n 4  # Full year of quarterly reviews
```

## File Structure

```
xit/
├── __init__.py          # Package initialization
├── __main__.py          # CLI entry point with batch processing
├── commands.py          # Command implementations with batch support
├── config.py            # Configuration management
├── dateutils.py         # Date parsing utilities
├── exceptions.py        # Custom exceptions
├── fileparser.py        # File parsing logic
├── formatter.py         # Output formatting
├── services.py          # Core business logic with task operations
├── task.py              # Task data model
└── tui.py               # Terminal UI components
```

## API Reference

### Core Classes

#### Task
Represents a single task with all its properties:
- `description`: Task description text
- `status`: One of OPEN, DONE, ONGOING, OBSOLETE, IN_QUESTION
- `priority`: Integer priority level (0 = normal, higher = more urgent)
- `tags`: List of hashtags
- `due_date`: Optional due date
- `file`: Source file path
- `line_number`: Line number in source file

#### FileParser
Parses `.xit` and `.md` files to extract tasks:
```python
from xit.fileparser import FileParser

parser = FileParser()
tasks = parser.parse_file('tasks.xit')
```

#### TaskService
High-level service for task operations:
```python
from xit.services import TaskService

service = TaskService()
tasks = service.get_tasks_from_directory('.')
filtered_tasks = service.filter_tasks(tasks, status='OPEN')
```

### Configuration

XitFlow supports configuration through:
- Command-line arguments
- Environment variables
- Configuration files (planned)

## Examples

### Example Task File

```xit
# Personal Tasks

Shopping
[ ] Buy milk #grocery #urgent
[ ] Get bread -> 2025-10-20 #grocery
[x] Pick up dry cleaning #errands

Work Projects  
[ ] Complete project proposal ...
    needs to include budget analysis
    and timeline estimates #work #deadline=2025-11-01
[@] Code review for PR #123 #work #development  
[!] Fix critical bug #work #priority=high

Health & Fitness
[ ] Schedule dentist appointment #health
[~] Old fitness goal #health
[?] Maybe try new gym #health #maybe
```

### Example Output

```bash
$ xit show --show-id --status open

📋 Open Tasks (4)

001 🔴 HIGH  Fix critical bug #work #priority=high
002 📝 NORMAL Buy milk #grocery #urgent  
003 📝 NORMAL Get bread (due: 2025-10-20) #grocery
004 📝 NORMAL Complete project proposal #work #deadline=2025-11-01
              needs to include budget analysis and timeline estimates
005 📝 NORMAL Schedule dentist appointment #health

$ xit mark 1 2 3 --done
✓ Marked task #1 as done in tasks.xit: "Fix critical bug #work #priority=high"
✓ Marked task #2 as done in tasks.xit: "Buy milk #grocery #urgent"
✓ Marked task #3 as done in tasks.xit: "Get bread (due: 2025-10-20) #grocery"
Processed 3 of 3 tasks.

$ xit reschedule 4 5 "next monday"
✓ Rescheduled task #4 to 2025-10-21 in tasks.xit: "Complete project proposal #work"
✓ Rescheduled task #5 to 2025-10-21 in tasks.xit: "Schedule dentist appointment #health"
Processed 2 of 2 tasks.
```

## Development

### Running Tests

```bash
# Run all tests (337 tests including batch processing)
python -m pytest

# Run with coverage
python -m pytest --cov=xit

# Run specific test file
python -m pytest tests/test_fileparser.py

# Test batch processing functionality specifically
python -m pytest tests/test_commands.py::TestBatchProcessing -v
```

### Test Coverage

- ✅ **337 total tests** with comprehensive batch processing coverage
- ✅ Unit tests for all command classes with batch support
- ✅ Integration tests for real file operations
- ✅ Error handling and edge case scenarios
- ✅ Content-based task matching for ID stability during batch operations
- ✅ Order preservation and shell expansion testing

### Code Style

```bash
# Format code
black xit/ tests/

# Sort imports
isort xit/ tests/

# Lint code  
flake8 xit/ tests/

# Type checking
mypy xit/
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`python -m pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Syntax Reference

For a complete syntax reference, see [`syntax_guide.txt`](syntax_guide.txt) which includes:
- Valid and invalid task formats
- Priority syntax rules
- Due date formats
- Tag syntax and values
- Multi-line description rules
- Group and header formatting
- UTF-8 encoding support

## Acknowledgments

- Inspired by various todo.txt and task management formats
- Built with [Rich](https://github.com/Textualize/rich) for beautiful terminal output
- Uses [Click](https://click.palletsprojects.com/) for the command-line interface

