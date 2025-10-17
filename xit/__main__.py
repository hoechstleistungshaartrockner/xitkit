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
@click.argument('task_ids', nargs=-1, type=int, metavar='ID...')
@click.option('--open', 'status', flag_value='open', help='Mark tasks as open')
@click.option('--done', 'status', flag_value='done', help='Mark tasks as done')  
@click.option('--ongoing', 'status', flag_value='ongoing', help='Mark tasks as ongoing')
@click.option('--obsolete', 'status', flag_value='obsolete', help='Mark tasks as obsolete')
@click.option('--inquestion', 'status', flag_value='inquestion', help='Mark tasks as in question')
@click.pass_context
def mark(ctx, task_ids, status):
    """Mark one or more tasks with a specific status.
    
    Changes the status of tasks identified by their IDs. The task IDs can be found
    using the 'xit show --show-id' command. Use shell expansion for ranges like {3..21}.
    
    ID...: One or more task ID numbers to mark
    
    Examples:
        xit mark 5 --done                    # Mark task #5 as done
        xit mark 2 3 4 5 6 --done            # Mark multiple tasks as done
        xit mark {3..21} --ongoing            # Mark task range as ongoing (bash expansion)
        xit -f tasks.xit mark 3 --ongoing     # Mark task #3 as ongoing in specific file
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
        directory=ctx.obj['directory'],
        specified_files=ctx.obj['files']
    )


@xit.command()
@click.argument('task_ids', nargs=-1, type=int, metavar='ID...')
@click.argument('new_date', type=str, metavar='DATE')
@click.pass_context
def reschedule(ctx, task_ids, new_date):
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
        directory=ctx.obj['directory'],
        specified_files=ctx.obj['files']
    )


@xit.command()
@click.argument('task_ids', nargs=-1, type=int, metavar='ID...')
@click.pass_context
def rm(ctx, task_ids):
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
        xit -f tasks.xit rm 3       # Remove task #3 from specific file (with confirmation)
    """
    if not task_ids:
        click.echo("Error: Must specify at least one task ID", err=True)
        ctx.exit(1)
    
    # Create and execute command
    command = CommandFactory.create_remove_command()
    command.execute(
        task_ids=list(task_ids),
        directory=ctx.obj['directory'],
        specified_files=ctx.obj['files']
    )


@xit.command()
@click.argument('task_ids', nargs=-1, type=int, metavar='ID...')
@click.option('--target', '-t', required=True, 
              help='Target file to move the tasks to')
@click.pass_context
def move(ctx, task_ids, target):
    """Move one or more tasks to another file.
    
    Moves tasks from their current files to the specified target file.
    Use shell expansion for ranges like {3..21}.
    The task IDs can be found using the 'xit show --show-id' command.
    
    ID...: One or more task ID numbers to move
    
    Examples:
        xit move 5 --target other.xit          # Move task #5 to other.xit
        xit move 2 3 4 --target done.xit      # Move multiple tasks to done.xit
        xit move {3..21} --target archive.xit # Move task range to archive.xit (bash expansion)
        xit -f tasks.xit move 3 -t done.xit   # Move task #3 to done.xit
    """
    if not task_ids:
        click.echo("Error: Must specify at least one task ID", err=True)
        ctx.exit(1)
    
    # Create and execute command
    command = CommandFactory.create_move_command()
    command.execute(
        task_ids=list(task_ids),
        target_file=target,
        directory=ctx.obj['directory'],
        specified_files=ctx.obj['files']
    )


if __name__ == '__main__':
    xit()