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
@click.option('--show-id', is_flag=True,
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


if __name__ == '__main__':
    xit()