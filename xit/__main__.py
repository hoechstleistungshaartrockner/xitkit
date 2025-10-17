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
@click.option('--directory', '-d', type=click.Path(exists=True, file_okay=False), 
              help='Directory to search for task files (default: current directory)')
@click.option('--files', '-f', multiple=True, type=click.Path(exists=True),
              help='Specific files to parse (can be used multiple times)')
@click.pass_context
def xit(ctx, directory, files):
    """Xit - A command line task management tool for .md and .xit files.
    
    This tool parses task files and provides various commands for viewing and managing tasks.
    
    Examples:
        xit show                    # Show all tasks
        xit show --status open      # Show only open tasks  
        xit show --status done      # Show only completed tasks
        xit -f tasks.xit show       # Show tasks from specific file
    """
    # Store options in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj['directory'] = Path(directory) if directory else Path.cwd()
    ctx.obj['files'] = list(files) if files else []
    
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
@click.option('--show-id', '-id', is_flag=True,
              help='Show task IDs with zero padding and reduced opacity')
@click.option('--count', '-c', is_flag=True,
              help='Show only the count of matching tasks')
@click.pass_context
def show(ctx, path, status, priority, tag, due_on, due_by, show_line, show_id, count):
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
        xit show tasks/ --status done --priority 2 # Show completed high-priority tasks from tasks/ directory
        xit show --tag work --tag urgent   # Show tasks with both 'work' and 'urgent' tags
        xit show --due-by 2025             # Show tasks due on or before 2025
        xit show --due-on today            # Show tasks due exactly today
        xit show --count                   # Show count of all tasks
        xit show --show-line               # Include line numbers
    """
    # Create filter object from CLI arguments
    filters = TaskFilter(
        status=status,
        priority=priority,
        tags=list(tag) if tag else None,
        due_on=due_on,
        due_by=due_by
    )
    
    # Create and execute command
    command = CommandFactory.create_show_command()
    command.execute(
        path=path,
        directory=ctx.obj['directory'],
        specified_files=ctx.obj['files'],
        filters=filters,
        show_line=show_line,
        show_id=show_id,
        count_only=count
    )


@xit.command()
@click.argument('path', type=click.Path(), required=False)
@click.pass_context
def stats(ctx, path):
    """Show statistics about tasks.
    
    Displays a summary of task counts by status, priority levels, and other metrics.
    
    PATH: Optional file or directory path to analyze. If not provided, uses current directory
          or files specified with --files option.
    """
    # Create and execute command
    command = CommandFactory.create_stats_command()
    command.execute(
        path=path,
        directory=ctx.obj['directory'],
        specified_files=ctx.obj['files']
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
        directory=ctx.obj['directory']
    )


@xit.command()
@click.argument('task_id', type=int, metavar='ID')
@click.argument('status', type=click.Choice(['open', 'done', 'ongoing', 'obsolete', 'inquestion'], 
                                          case_sensitive=False))
@click.pass_context
def mark(ctx, task_id, status):
    """Mark a task with a specific status.
    
    Changes the status of a task identified by its ID. The task ID can be found
    using the 'xit show --show-id' command.
    
    ID: The task ID number
    STATUS: New status for the task (open, done, ongoing, obsolete, inquestion)
    
    Examples:
        xit mark 5 done         # Mark task #5 as done
        xit mark 12 ongoing     # Mark task #12 as ongoing
        xit mark 3 open         # Mark task #3 as open
    """
    # Create and execute command
    command = CommandFactory.create_mark_command()
    command.execute(
        task_id=task_id,
        status=status.upper(),
        directory=ctx.obj['directory'],
        specified_files=ctx.obj['files']
    )


@xit.command()
@click.argument('task_id', type=int, metavar='ID')
@click.argument('new_date', type=str, metavar='DATE')
@click.pass_context
def reschedule(ctx, task_id, new_date):
    """Reschedule a task to a new due date.
    
    Changes the due date of a task identified by its ID. The task ID can be found
    using the 'xit show --show-id' command.
    
    Supports natural language dates and relative date expressions.
    
    ID: The task ID number
    DATE: New due date (supports various formats)
    
    Examples:
        xit reschedule 5 2025-12-31     # Set specific date
        xit reschedule 3 today          # Set to today
        xit reschedule 7 tomorrow       # Set to tomorrow
        xit reschedule 2 "+1w"          # Add one week
        xit reschedule 4 1w             # Add one week (alternative)
        xit reschedule 8 2d-            # Subtract two days
        xit reschedule 9 "+3m"          # Add three months
    """
    # Create and execute command
    command = CommandFactory.create_reschedule_command()
    command.execute(
        task_id=task_id,
        new_date=new_date,
        directory=ctx.obj['directory'],
        specified_files=ctx.obj['files']
    )


@xit.command()
@click.argument('task_id', type=int, metavar='ID')
@click.pass_context
def rm(ctx, task_id):
    """Remove a task by its ID with confirmation.
    
    Shows the task and asks for confirmation before permanently deleting it.
    Answering 'n' will mark the task as obsolete instead of deleting it.
    The task ID can be found using the 'xit show --show-id' command.
    
    ID: The task ID number to remove
    
    Examples:
        xit rm 5               # Remove task #5 (with confirmation)
        xit -f tasks.xit rm 3  # Remove task #3 from specific file (with confirmation)
    """
    # Create and execute command
    command = CommandFactory.create_remove_command()
    command.execute(
        task_id=task_id,
        directory=ctx.obj['directory'],
        specified_files=ctx.obj['files']
    )


@xit.command()
@click.argument('task_id', type=int, metavar='ID')
@click.option('--target', '-t', required=True, 
              help='Target file to move the task to')
@click.pass_context
def move(ctx, task_id, target):
    """Move a task to another file.
    
    Moves a task from its current file to the specified target file.
    The task ID can be found using the 'xit show --show-id' command.
    
    ID: The task ID number to move
    
    Examples:
        xit move 5 --target other.xit     # Move task #5 to other.xit
        xit -f tasks.xit move 3 -t done.xit  # Move task #3 to done.xit
    """
    # Create and execute command
    command = CommandFactory.create_move_command()
    command.execute(
        task_id=task_id,
        target_file=target,
        directory=ctx.obj['directory'],
        specified_files=ctx.obj['files']
    )


if __name__ == '__main__':
    xit()