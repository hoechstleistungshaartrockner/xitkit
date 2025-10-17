# XitFlow

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

```bash
# Show all tasks in current directory
python -m xit show

# Show tasks from specific files
python -m xit -f tasks.xit show

# Show only open tasks
python -m xit show --status open

# Show task statistics
python -m xit stats

# Show help
python -m xit --help
```

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

## File Structure

```
xit/
├── __init__.py          # Package initialization
├── __main__.py          # CLI entry point
├── commands.py          # Command implementations
├── config.py            # Configuration management
├── dateutils.py         # Date parsing utilities
├── exceptions.py        # Custom exceptions
├── fileparser.py        # File parsing logic
├── formatter.py         # Output formatting
├── services.py          # Core business logic
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
$ python -m xit show --status open

📋 Open Tasks (4)

🔴 HIGH  Fix critical bug #work #priority=high
📝 NORMAL Buy milk #grocery #urgent  
📝 NORMAL Get bread (due: 2025-10-20) #grocery
📝 NORMAL Complete project proposal #work #deadline=2025-11-01
         needs to include budget analysis and timeline estimates
📝 NORMAL Schedule dentist appointment #health
```

## Development

### Running Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=xit

# Run specific test file
python -m pytest tests/test_fileparser.py
```

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