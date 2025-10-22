# :clipboard: XitKit

A powerful command-line task management tool that parses and manages tasks from `.xit` and `.md` files using the [x]it! format (https://xit.jotaen.net/)

## :sparkles: Features

- **:arrows_counterclockwise: Multiple Task States**: Open, checked, ongoing, obsolete, and in-question tasks
- **:zap: Priority Levels**: Support for multiple priority indicators (`!`, `!!`, `!!!`)
- **:calendar: Due Dates**: Flexible date parsing with various formats
- **:label: Tags**: Organize tasks with hashtags and optional values
- **:memo: Multi-line Descriptions**: Support for continued task descriptions
- **:file_folder: Groups & Headers**: Organize related tasks under headers
- **:art: Rich Output**: Beautiful terminal output with colors and formatting
- **:mag: Flexible Filtering**: Filter tasks by status, priority, tags, and more
- **:bar_chart: Statistics**: Get insights about your task distribution
- **:rocket: Batch Processing**: Mark, reschedule, remove, or move multiple tasks at once
- **:repeat: Recurring Tasks**: Create recurring instances with flexible intervals (daily, weekly, monthly, yearly)
- **:shell: Shell Integration**: Support for shell expansion (`{3..21}`) and sequences
- **:triangular_flag_on_post: Status Flags**: Intuitive `--done`, `--ongoing`, `--obsolete` flags instead of cryptic symbols
- **:shield: Smart Error Handling**: Individual task feedback with batch operation summaries
- **:tomato: Pomodoro timer**: simple, textual-based pomodoro timer

## :package: Installation

### :warning: Prerequisites

- Python 3.14+
- Micromamba or Conda (recommended)

### :gear: Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/hoechstleistungshaartrockner/xitkit.git
   cd xitkit
   ```

2. Create the environment:
   ```bash
   micromamba create -f micromamba.yaml
   micromamba activate xitkit
   ```

3. Install dependencies:
   ```bash
   poetry install
   poetry install --extras dev
   ```

## :computer: Usage
Two command-line entry points are provided: `xitkit` and `xit`. Both commands function identically.

```bash
xit --help
xitkit --help
```

### :toolbox: Available Subcommands

| Command    | Description                                               |
|------------|-----------------------------------------------------------|
| add        | Add a new task.                                           |
| edit       | Edit the description of a task.                           |
| mark       | Mark one or more tasks with a specific status.            |
| move       | Move one or more tasks to another file.                   |
| pomodoro   | A simple Pomodoro Timer App to run in the terminal.       |
| prio       | Set the priority of a task.                               |
| recur      | Create recurring instances of a task.                     |
| reschedule | Reschedule one or more tasks to a new due date.           |
| rm         | Remove one or more tasks by their IDs with confirmation.  |
| show       | Show tasks from .md and .xit files.                       |
| stats      | Show statistics about tasks.                              |
| tag        | Add a tag to a task.                                      |
| untag      | Remove a tag from a task.                                 |


### :bulb: Command Examples

```bash
# Show all tasks in current directory
xit show

# Show tasks from specific files
xit -f tasks.xit show

# Show only open tasks
xit show --status open

# Show tasks with IDs for reference
xit show --show-id

# Show task statistics
xit stats

# Show help
xit --help

# Add a new task
xit add "Buy groceries"
xit add "!! Important meeting -> 2025-12-15 #work" -f work.xit

# Mark tasks with new status flags (supports batch processing)
xit mark 5 --done                     # Mark task #5 as done
xit mark 2 3 4 5 6 --done             # Mark multiple tasks as done
xit mark {3..21} --ongoing            # Mark task range as ongoing (bash expansion)
xit mark 1 --open                     # Reopen a task
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

# Edit task properties
xit edit 5 "Updated task description"   # Change the description of task #5
xit prio 3 2                          # Set priority level 2 (!!) for task #3
xit prio 7 0                          # Remove priority from task #7
xit tag 5 urgent                      # Add #urgent tag to task #5
xit tag 3 "work"                      # Add #work tag to task #3
xit untag 5 urgent                    # Remove #urgent tag from task #5
```


## :wrench: Development

### :test_tube: Running Tests

```bash
python -m pytest

# Run with coverage
python -m pytest --cov=xit

# Run specific test file
python -m pytest tests/test_fileparser.py

# Test batch processing functionality specifically
python -m pytest tests/test_commands.py::TestBatchProcessing -v
```

## :page_facing_up: License

This project is licensed under the MIT License - see the LICENSE file for details.

## :pray: Acknowledgments

- Developer of the [x]it! format: [Jotaen](https://github.com/Jotaen/xit)
- Built with [Rich](https://github.com/Textualize/rich) for beautiful terminal output
- Uses [Click](https://click.palletsprojects.com/) for the command-line interface

