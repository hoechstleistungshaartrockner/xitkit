#!/usr/bin/env python3
"""Command line interface for the xit task management tool.

This module provides a simplified CLI that delegates operations to command classes,
following the command pattern for better separation of concerns.
"""

import click
from pathlib import Path
import sys
import os

# Add the current directory to the path to import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from xit.commands import CommandFactory
from xit.services import TaskFilter
from xit.formatter import TaskFormatter


@click.group(invoke_without_command=True)
@click.pass_context
def xit(ctx):
    """Xit - A command line task management tool for .md and .xit files.
    
    This tool parses task files and provides various commands for viewing and managing tasks.
    
    Examples:
        xit show                           # Show all tasks from current directory
        xit show --status open             # Show only open tasks  
        xit show --status done             # Show only completed tasks
        xit show --files tasks.xit         # Show tasks from specific file
        xit add "Buy groceries"            # Add task to default todo.xit
        xit mark 1 2 3 --done             # Mark multiple tasks as done
    """
    # Initialize context for subcommands
    ctx.ensure_object(dict)
    
    # If no subcommand is provided, show help
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@xit.command()
@click.argument('path', type=click.Path(), required=False)
@click.option('--status', '-s', 
              type=click.Choice(['open', 'done', 'ongoing', 'obsolete', 'inquestion'], 
                               case_sensitive=False),
              help='Filter tasks by status')
@click.option('--priority', '-p', type=int,
              help='Filter tasks by minimum priority level')
@click.option('--tag', '-t', multiple=True,
              help='Filter tasks containing specific tags (can be used multiple times)')
@click.option('--due-on', type=str,
              help='Filter tasks due exactly on the specified date. Supports: "today", "tomorrow", "1d", "2w", "3m", "1y", or date formats like "2025-12-31"')
@click.option('--due-by', type=str,
              help='Filter tasks due on or before the specified date. Supports: "today", "tomorrow", "1d", "2w", "3m", "1y", or date formats like "2025-12-31"')
@click.option('--show-line', '-l', is_flag=True,
              help='Show line numbers for each task')
@click.option('--no-id', is_flag=True,
              help='Hide task IDs')
@click.option('--count', '-c', is_flag=True,
              help='Show only the count of matching tasks')
@click.option('--directory', '-d', type=click.Path(exists=True, file_okay=False), 
              help='Directory to search for task files (default: current directory)')
@click.option('--files', '-f', multiple=True, type=click.Path(exists=True),
              help='Specific files to parse (can be used multiple times)')
@click.option('--sort', type=click.Choice(['priority', 'due_date'], case_sensitive=False),
              help='Sort tasks by the specified attribute (priority or due_date)')
@click.option('--order', type=click.Choice(['asc', 'desc'], case_sensitive=False),
              help='Sort order: asc (ascending) or desc (descending). Defaults to asc if not specified')
@click.pass_context
def show(ctx, path, status, priority, tag, due_on, due_by, show_line, no_id, count, directory, files, sort, order):
    """Show tasks from .md and .xit files.
    
    This command displays tasks with optional filtering by status, priority, tags, and due dates.
    Tasks are grouped by file with colored syntax highlighting.
    
    PATH: Optional file or directory path to parse. If not provided, uses current directory
          or files specified with --files option.
    
    Examples:
        xit show                           # Show all tasks from current directory
        xit show tasks.xit                 # Show tasks from specific file
        xit show /path/to/project          # Show tasks from specific directory
        xit show --status open             # Show only open tasks
        xit show --directory tasks/ --status done --priority 2 # Show completed high-priority tasks from tasks/ directory
        xit show --tag work --tag urgent   # Show tasks with both 'work' and 'urgent' tags
        xit show --due-by 2025             # Show tasks due on or before 2025
        xit show --due-on today            # Show tasks due exactly today
        xit show --count                   # Show count of all tasks
        xit show --show-line               # Include line numbers
        xit show --files work.xit personal.xit --status open  # Show open tasks from multiple files
        xit show --sort priority --order desc  # Show tasks sorted by priority (highest first)
        xit show --sort due_date --order asc   # Show tasks sorted by due date (earliest first)
    """
    # Create filter object from CLI arguments
    from xit.status import Status, StatusType
    from xit.priority import Priority
    from xit.tags import Tag
    
    # Convert CLI arguments to proper objects
    status_obj = None
    if status:
        status_mapping = {
            'open': StatusType.OPEN,
            'done': StatusType.CHECKED,
            'ongoing': StatusType.ONGOING,
            'obsolete': StatusType.OBSOLETE,
            'inquestion': StatusType.IN_QUESTION
        }
        if status in status_mapping:
            status_obj = Status(status_mapping[status])
    
    priority_obj = None
    if priority is not None:
        priority_obj = Priority(priority)
    
    tag_objects = None
    if tag:
        tag_objects = [Tag(t) for t in tag]
    
    # Convert date strings to DueDate objects
    from xit.duedate import DueDate
    
    due_on_obj = None
    if due_on:
        due_on_obj = DueDate.from_string(due_on)
    
    due_by_obj = None  
    if due_by:
        due_by_obj = DueDate.from_string(due_by)

    filters = TaskFilter(
        status=status_obj,
        priority=priority_obj,
        tags=tag_objects,
        due_on=due_on_obj,
        due_by=due_by_obj
    )
    
    # Create and execute command
    command = CommandFactory.create_show_command()
    command.execute(
        path=path,
        directory=Path(directory) if directory else Path.cwd(),
        specified_files=list(files) if files else [],
        filters=filters,
        show_line=show_line,
        no_id=no_id,
        count_only=count,
        sort_by=sort,
        sort_order=order or 'asc' if sort else None
    )


@xit.command()
@click.argument('path', type=click.Path(), required=False)
@click.option('--directory', '-d', type=click.Path(exists=True, file_okay=False), 
              help='Directory to search for task files (default: current directory)')
@click.option('--files', '-f', multiple=True, type=click.Path(exists=True),
              help='Specific files to parse (can be used multiple times)')
@click.pass_context
def stats(ctx, path, directory, files):
    """Show statistics about tasks.
    
    Displays a summary of task counts by status, priority levels, and other metrics.
    
    PATH: Optional file or directory path to analyze. If not provided, uses current directory
          or files specified with --files option.
    
    Examples:
        xit stats                          # Show stats for all tasks in current directory
        xit stats tasks.xit                # Show stats for specific file
        xit stats --directory /path/to/project  # Show stats for tasks in specific directory
        xit stats --files work.xit personal.xit  # Show stats for multiple specific files
    """
    # Create and execute command
    command = CommandFactory.create_stats_command()
    command.execute(
        path=path,
        directory=Path(directory) if directory else Path.cwd(),
        specified_files=list(files) if files else []
    )


@xit.command()
@click.argument('description', type=str)
@click.option('--file', '-f', type=click.Path(), 
              help='File to add the task to (default: todo.xit)')
@click.pass_context
def add(ctx, description, file):
    """Add a new task.
    
    Creates a new task with the specified description and appends it to the target file.
    If no file is specified, the task will be added to 'todo.xit' in the current directory.
    
    The description can include priority markers (!), due dates (-> YYYY-MM-DD), and tags (#tag).
    
    DESCRIPTION: The task description text
    
    Examples:
        xit add "Buy groceries"
        xit add "!! Important meeting -> 2025-12-15 #work" -f work.xit
        xit add "Review code #urgent #dev" --file tasks.md
    """
    # Create and execute command
    command = CommandFactory.create_add_command()
    command.execute(
        description=description,
        file_path=file or "todo.xit",
        directory=Path.cwd()
    )


@xit.command()
@click.argument('task_ids', nargs=-1, type=int, metavar='ID...')
@click.option('--open', 'status', flag_value='open', help='Mark tasks as open')
@click.option('--done', 'status', flag_value='done', help='Mark tasks as done')  
@click.option('--ongoing', 'status', flag_value='ongoing', help='Mark tasks as ongoing')
@click.option('--obsolete', 'status', flag_value='obsolete', help='Mark tasks as obsolete')
@click.option('--inquestion', 'status', flag_value='inquestion', help='Mark tasks as in question')
@click.option('--directory', '-d', type=click.Path(exists=True, file_okay=False), 
              help='Directory to search for task files (default: current directory)')
@click.option('--files', '-f', multiple=True, type=click.Path(exists=True),
              help='Specific files to parse (can be used multiple times)')
@click.pass_context
def mark(ctx, task_ids, status, directory, files):
    """Mark one or more tasks with a specific status.
    
    Changes the status of tasks identified by their IDs. The task IDs can be found
    using the 'xit show --show-id' command. Use shell expansion for ranges like {3..21}.
    
    ID...: One or more task ID numbers to mark
    
    Examples:
        xit mark 5 --done                    # Mark task #5 as done
        xit mark 2 3 4 5 6 --done            # Mark multiple tasks as done
        xit mark {3..21} --ongoing            # Mark task range as ongoing (bash expansion)
        xit mark 3 --ongoing --files tasks.xit  # Mark task #3 as ongoing in specific file
        xit mark 5 --done --directory /path/to/project  # Mark task in specific directory
    """
    if not task_ids:
        click.echo("Error: Must specify at least one task ID", err=True)
        ctx.exit(1)
    
    if not status:
        click.echo("Error: Must specify a status flag (--done, --open, --ongoing, --obsolete, --inquestion)", err=True)
        ctx.exit(1)
    
    # Create and execute command
    command = CommandFactory.create_mark_command()
    command.execute(
        task_ids=list(task_ids),
        status=status.upper(),
        directory=Path(directory) if directory else Path.cwd(),
        specified_files=list(files) if files else []
    )


@xit.command()
@click.argument('task_ids', nargs=-1, type=int, metavar='ID...')
@click.argument('new_date', type=str, metavar='DATE')
@click.option('--directory', '-d', type=click.Path(exists=True, file_okay=False), 
              help='Directory to search for task files (default: current directory)')
@click.option('--files', '-f', multiple=True, type=click.Path(exists=True),
              help='Specific files to parse (can be used multiple times)')
@click.pass_context
def reschedule(ctx, task_ids, new_date, directory, files):
    """Reschedule one or more tasks to a new due date.
    
    Changes the due date of tasks identified by their IDs. The task IDs can be found
    using the 'xit show --show-id' command. Use shell expansion for ranges like {3..21}.
    
    Supports natural language dates and relative date expressions.
    
    ID...: One or more task ID numbers to reschedule
    DATE: New due date (supports various formats)
    
    Examples:
        xit reschedule 5 2025-12-31         # Set specific date for task #5
        xit reschedule 2 3 4 today          # Set multiple tasks to today
        xit reschedule {3..21} tomorrow     # Set task range to tomorrow (bash expansion)
        xit reschedule 2 "+1w"              # Add one week to task #2
        xit reschedule 4 5 6 1w             # Add one week to multiple tasks
        xit reschedule 8 2d-                # Subtract two days from task #8
        xit reschedule 9 "+3m"              # Add three months to task #9
    """
    if not task_ids:
        click.echo("Error: Must specify at least one task ID", err=True)
        ctx.exit(1)
    
    # Create and execute command
    command = CommandFactory.create_reschedule_command()
    command.execute(
        task_ids=list(task_ids),
        new_date=new_date,
        directory=Path(directory) if directory else Path.cwd(),
        specified_files=list(files) if files else []
    )


@xit.command()
@click.argument('task_ids', nargs=-1, type=int, metavar='ID...')
@click.option('--directory', '-d', type=click.Path(exists=True, file_okay=False), 
              help='Directory to search for task files (default: current directory)')
@click.option('--files', '-f', multiple=True, type=click.Path(exists=True),
              help='Specific files to parse (can be used multiple times)')
@click.pass_context
def rm(ctx, task_ids, directory, files):
    """Remove one or more tasks by their IDs with confirmation.
    
    Shows each task and asks for confirmation before permanently deleting it.
    Answering 'n' will mark the task as obsolete instead of deleting it.
    Use shell expansion for ranges like {3..21}.
    The task IDs can be found using the 'xit show --show-id' command.
    
    ID...: One or more task ID numbers to remove
    
    Examples:
        xit rm 5                     # Remove task #5 (with confirmation)
        xit rm 2 3 4 5              # Remove multiple tasks (with confirmation for each)
        xit rm {3..21}              # Remove task range (bash expansion, with confirmation for each)
        xit rm 3 --files tasks.xit  # Remove task #3 from specific file (with confirmation)
        xit rm 5 --directory /path/to/project  # Remove task from specific directory
    """
    if not task_ids:
        click.echo("Error: Must specify at least one task ID", err=True)
        ctx.exit(1)
    
    # Create and execute command
    command = CommandFactory.create_remove_command()
    command.execute(
        task_ids=list(task_ids),
        directory=Path(directory) if directory else Path.cwd(),
        specified_files=list(files) if files else []
    )


@xit.command()
@click.argument('task_ids', nargs=-1, type=int, metavar='ID...')
@click.option('--target', '-t', required=True, 
              help='Target file to move the tasks to')
@click.option('--directory', '-d', type=click.Path(exists=True, file_okay=False), 
              help='Directory to search for task files (default: current directory)')
@click.option('--files', '-f', multiple=True, type=click.Path(exists=True),
              help='Specific files to parse (can be used multiple times)')
@click.pass_context
def move(ctx, task_ids, target, directory, files):
    """Move one or more tasks to another file.
    
    Moves tasks from their current files to the specified target file.
    Use shell expansion for ranges like {3..21}.
    The task IDs can be found using the 'xit show --show-id' command.
    
    ID...: One or more task ID numbers to move
    
    Examples:
        xit move 5 --target other.xit          # Move task #5 to other.xit
        xit move 2 3 4 --target done.xit      # Move multiple tasks to done.xit
        xit move {3..21} --target archive.xit # Move task range to archive.xit (bash expansion)
        xit move 3 -t done.xit --files tasks.xit  # Move task #3 to done.xit from specific file
        xit move 5 --target archive.xit --directory /path/to/project  # Move task from specific directory
    """
    if not task_ids:
        click.echo("Error: Must specify at least one task ID", err=True)
        ctx.exit(1)
    
    # Create and execute command
    command = CommandFactory.create_move_command()
    command.execute(
        task_ids=list(task_ids),
        target_file=target,
        directory=Path(directory) if directory else Path.cwd(),
        specified_files=list(files) if files else []
    )


@xit.command()
@click.argument('task_id', type=int, metavar='ID')
@click.option('--interval', '-i', required=True, type=str,
              help='Recurrence interval (e.g., "1d", "1w", "2w", "1m", "3m", "1y")')
@click.option('--end-date', '-e', type=str,
              help='End date for recurrence in YYYY-MM-DD format')
@click.option('--count', '-n', type=int,
              help='Maximum number of recurring instances to create')
@click.option('--target-file', '-t', type=str,
              help='Target file for recurring tasks (default: same as original task)')
@click.option('--directory', '-d', type=click.Path(exists=True, file_okay=False), 
              help='Directory to search for task files (default: current directory)')
@click.option('--files', '-f', multiple=True, type=click.Path(exists=True),
              help='Specific files to parse (can be used multiple times)')
@click.pass_context
def recur(ctx, task_id, interval, end_date, count, target_file, directory, files):
    """Create recurring instances of a task.
    
    Creates multiple recurring instances of an existing task based on the specified interval.
    The original task remains unchanged, and new tasks are created with updated due dates.
    
    ID: Task ID number to make recurring (use 'xit show --show-id' to find IDs)
    
    Examples:
        xit recur 5 --interval 1w                    # Create weekly recurrence of task #5
        xit recur 3 -i 2w -n 5                      # Create 5 bi-weekly instances of task #3
        xit recur 7 -i 1m -e 2026-12-31             # Monthly recurrence until end of 2026
        xit recur 2 -i 1d -n 30 -t work.xit        # 30 daily instances in work.xit file
        xit recur 4 -i 3m --files personal.xit     # Quarterly recurrence from specific file
    
    Interval formats:
        1d, 7d    - Days (1 day, 7 days)
        1w, 2w    - Weeks (1 week, 2 weeks)  
        1m, 3m    - Months (1 month, 3 months)
        1y        - Years (1 year)
    """
    # Validate mutual exclusivity
    if end_date and count:
        click.echo("Error: Cannot specify both --end-date and --count. Choose one.", err=True)
        ctx.exit(1)
    
    if not end_date and not count:
        click.echo("Error: Must specify either --end-date or --count for recurrence limit.", err=True)
        ctx.exit(1)
    
    # Create and execute command
    command = CommandFactory.create_recur_command()
    command.execute(
        task_id=task_id,
        interval=interval,
        end_date=end_date,
        count=count,
        target_file=target_file,
        directory=Path(directory) if directory else Path.cwd(),
        specified_files=list(files) if files else []
    )


@xit.command()
@click.argument('task_id', type=int, metavar='ID')
@click.argument('description', type=str, metavar='DESCRIPTION')
@click.option('--directory', '-d', type=click.Path(exists=True, file_okay=False), 
              help='Directory to search for task files (default: current directory)')
@click.option('--files', '-f', multiple=True, type=click.Path(exists=True),
              help='Specific files to parse (can be used multiple times)')
@click.pass_context
def edit(ctx, task_id, description, directory, files):
    """Edit the description of a task.
    
    Changes the description text of an existing task while preserving its priority,
    tags, and due date.
    
    ID: Task ID number to edit (use 'xit show --show-id' to find IDs)
    DESCRIPTION: New description text for the task
    
    Examples:
        xit edit 5 "Updated task description"        # Edit task #5 description
        xit edit 3 "New text" --files work.xit      # Edit task in specific file
        xit edit 7 "Revised task" -d ~/projects     # Edit task in project directory
    """
    # Create and execute command
    command = CommandFactory.create_edit_command()
    command.execute(
        task_id=task_id,
        description=description,
        directory=Path(directory) if directory else Path.cwd(),
        specified_files=list(files) if files else []
    )


@xit.command()
@click.argument('task_id', type=int, metavar='ID')
@click.argument('priority', type=int, metavar='PRIORITY')
@click.option('--directory', '-d', type=click.Path(exists=True, file_okay=False), 
              help='Directory to search for task files (default: current directory)')
@click.option('--files', '-f', multiple=True, type=click.Path(exists=True),
              help='Specific files to parse (can be used multiple times)')
@click.pass_context
def prio(ctx, task_id, priority, directory, files):
    """Set the priority of a task.
    
    Assigns or changes the priority level of an existing task.
    Priority is an integer where 0 = no priority, 1+ = number of exclamation marks.
    
    ID: Task ID number to modify (use 'xit show --show-id' to find IDs)
    PRIORITY: Priority level (0, 1, 2, etc.)
    
    Examples:
        xit prio 5 1                                 # Set task #5 to priority 1 (!)
        xit prio 3 3 --files work.xit               # Set priority 3 (!!!) in specific file
        xit prio 7 0 -d ~/projects                  # Remove priority from task #7
    """
    # Create and execute command
    command = CommandFactory.create_priority_command()
    command.execute(
        task_id=task_id,
        priority=priority,
        directory=Path(directory) if directory else Path.cwd(),
        specified_files=list(files) if files else []
    )


@xit.command()
@click.argument('task_id', type=int, metavar='ID')
@click.argument('tag', type=str, metavar='TAG')
@click.option('--directory', '-d', type=click.Path(exists=True, file_okay=False), 
              help='Directory to search for task files (default: current directory)')
@click.option('--files', '-f', multiple=True, type=click.Path(exists=True),
              help='Specific files to parse (can be used multiple times)')
@click.pass_context
def tag(ctx, task_id, tag, directory, files):
    """Add a tag to a task.
    
    Adds a hashtag to an existing task. The # symbol is optional - it will
    be added automatically if not provided.
    
    ID: Task ID number to modify (use 'xit show --show-id' to find IDs)
    TAG: Tag name (without # prefix)
    
    Examples:
        xit tag 5 urgent                            # Add #urgent tag to task #5
        xit tag 3 work --files todo.xit            # Add #work tag in specific file
        xit tag 7 "#meeting" -d ~/projects         # Add #meeting tag (# optional)
    """
    # Create and execute command
    command = CommandFactory.create_tag_command()
    command.execute(
        task_id=task_id,
        tag=tag,
        directory=Path(directory) if directory else Path.cwd(),
        specified_files=list(files) if files else []
    )


@xit.command()
@click.argument('task_id', type=int, metavar='ID')
@click.argument('tag', type=str, metavar='TAG')
@click.option('--directory', '-d', type=click.Path(exists=True, file_okay=False), 
              help='Directory to search for task files (default: current directory)')
@click.option('--files', '-f', multiple=True, type=click.Path(exists=True),
              help='Specific files to parse (can be used multiple times)')
@click.pass_context
def untag(ctx, task_id, tag, directory, files):
    """Remove a tag from a task.
    
    Removes a hashtag from an existing task. The # symbol is optional.
    If the tag doesn't exist, the command succeeds silently.
    
    ID: Task ID number to modify (use 'xit show --show-id' to find IDs)
    TAG: Tag name to remove (without # prefix)
    
    Examples:
        xit untag 5 urgent                          # Remove #urgent tag from task #5
        xit untag 3 work --files todo.xit          # Remove #work tag in specific file
        xit untag 7 "#meeting" -d ~/projects       # Remove #meeting tag (# optional)
    """
    # Create and execute command
    command = CommandFactory.create_untag_command()
    command.execute(
        task_id=task_id,
        tag=tag,
        directory=Path(directory) if directory else Path.cwd(),
        specified_files=list(files) if files else []
    )


if __name__ == '__main__':
    xit()