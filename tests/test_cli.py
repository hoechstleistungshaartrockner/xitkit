"""Unit tests for the command-line interface using Click's CliRunner.

This module tests the CLI commands in isolation using temporary filesystems
to ensure commands work correctly without affecting real files.
"""

import pytest
from click.testing import CliRunner
from pathlib import Path
from xitkit.__main__ import xitkit
from datetime import datetime, timedelta
import os

# Define date variables before they're used in f-strings
yesterday_date = (datetime.now() - timedelta(days=1)).date()
today_date = datetime.now().date()
tomorrow_date = (datetime.now() + timedelta(days=1)).date()
one_week_date = (datetime.now() + timedelta(weeks=1)).date()


class CLITest():

    @pytest.fixture
    def runner(self):
        """Provide a Click test runner."""
        return CliRunner()

class TestMainCLI(CLITest):
    """Test the command-line interface."""

    @pytest.fixture
    def empty_task_file(self):
        """Create an empty task file for testing."""
        return ""

    def test_help_command(self, runner):
        """Test that help is displayed correctly."""
        result = runner.invoke(xitkit, ['--help'])
        assert result.exit_code == 0
        assert 'Xit - A command line task management tool' in result.output
        assert 'show' in result.output
        assert 'add' in result.output
        assert 'mark' in result.output


class TestShowCLI(CLITest):
    """Test the 'show' command of the CLI."""

    def test_show_help_subcommand(self, runner):
        """Test help for specific subcommands."""
        result = runner.invoke(xitkit, ['show', '--help'])
        assert result.exit_code == 0
        assert 'Show tasks from .md and .xit files' in result.output

    def test_show_no_files(self, runner):
        """Test show command when no task files exist."""
        with runner.isolated_filesystem():
            result = runner.invoke(xitkit, ['show'])
            assert result.exit_code == 0
            assert 'No task files found' in result.output

    def test_show_tasks_from_file(self, runner, isolated_test_files):
        """Test showing tasks from a specific file."""
        os.chdir(isolated_test_files)
            
        result = runner.invoke(xitkit, ['show', '-f', 'valid_mixed.xit'])
        lines = result.output.splitlines()
        print(lines)
        assert result.exit_code == 0
        assert len(lines) > 0
        assert lines[0] == '#001 [ ] Open task'
        assert lines[1] == '#003 [@] Ongoing task'
        assert lines[2] == '#004 [~] Obsolete task'
        assert lines[3] == '#005 [?] Task in question'
        assert lines[4] == '#006 [ ] !! High priority task #urgent'
        assert lines[5] == f'#007 [ ] Task due tomorrow -> {tomorrow_date}'
        assert lines[6] == '#008 [ ] Task with #tags -> 2024-10-21'
        assert lines[7] == '#009 [ ] Task with #multiple #tags'
        assert lines[8] == '#010 [ ] Simple task'
        assert lines[9] == '#011 [ ] multi-line'
        assert lines[10] == '         task description'
        assert lines[11] == '         continues here'
        assert lines[12] == '#002 [x] Completed task with 3 trailing spaces   '
        assert lines[13] == ''

    def test_show_tasks_with_status_filter(self, isolated_test_files, runner):
        """Test showing tasks with status filtering."""
        os.chdir(isolated_test_files)
        
        # Test open tasks only
        result = runner.invoke(xitkit, ['show', '--status', 'ongoing', '-f', 'valid_mixed.xit'])
        lines = result.output.splitlines()
        assert result.exit_code == 0
        assert len(lines) > 0
        assert lines[0] == '#003 [@] Ongoing task'
        assert lines[1] == ''
        assert lines[2].startswith('Showing 1 of 11')

    def test_show_tasks_count_only(self, isolated_test_files, runner):
        """Test showing only the count of tasks."""
        os.chdir(isolated_test_files)
        
        result = runner.invoke(xitkit, ['show', '--count', '-f', 'valid_mixed.xit'])
        assert result.exit_code == 0
        lines = result.output.splitlines()
        assert len(lines) > 0
        assert lines[0]  == f'11 tasks found.'
            
    def test_show_tasks_due_on_date(self, isolated_test_files, runner):
        """Test showing tasks due on 2024-10-21."""
        os.chdir(isolated_test_files)
            
        result = runner.invoke(xitkit, ['show', '--due-on', '2024-10-21', '-f', 'valid_mixed.xit'])
        lines = result.output.splitlines()
        assert result.exit_code == 0
        assert len(lines) > 0
        assert lines[0] == '#008 [ ] Task with #tags -> 2024-10-21'
        assert lines[1] == ''
        assert lines[2] == f'Showing 1 of 11 total tasks.'
    
    def test_show_tasks_due_on_date_natural_language1(self, isolated_test_files, runner):
        """Test showing tasks due on tomorrow using natural language."""
        os.chdir(isolated_test_files)
        
        result = runner.invoke(xitkit, ['show', '--due-on', 'tomorrow', '-f', 'valid_due_dates.xit'])
        lines = result.output.splitlines()
        assert result.exit_code == 0
        assert len(lines) > 0
        assert lines[0] == f'#011 [ ] Task due tomorrow -> {tomorrow_date}'
        assert lines[1] == ''
        assert lines[2].startswith('Showing 1 of')
        
    def test_show_tasks_due_on_date_natural_language2(self, isolated_test_files, runner):
        """Test showing tasks due on next week using natural language."""
        os.chdir(isolated_test_files)
        
        result = runner.invoke(xitkit, ['show', '--due-on', '1w', '-f', 'valid_due_dates.xit'])
        lines = result.output.splitlines()
        assert result.exit_code == 0
        assert len(lines) > 0
        assert lines[0] == f'#012 [ ] Task due next week -> {one_week_date}'
        assert lines[1] == ''
        assert lines[2].startswith('Showing 1 of')

    def test_show_tasks_due_by_date(self, isolated_test_files, runner):
        """Test showing tasks due by 2024-10-21."""
        os.chdir(isolated_test_files)
            
        result = runner.invoke(xitkit, ['show', '--due-by', '2024-10-21', '-f', 'valid_mixed.xit'])
        lines = result.output.splitlines()
        assert result.exit_code == 0
        assert len(lines) > 0
        assert lines[0] == '#008 [ ] Task with #tags -> 2024-10-21'
        assert lines[1] == ''
        assert lines[2].startswith('Showing 1 of')

    def test_show_tasks_due_by_date_natural_language(self, isolated_test_files, runner):
        """Test showing tasks due by tomorrow using natural language."""
        os.chdir(isolated_test_files)
        result = runner.invoke(xitkit, ['show', '--due-by', 'tomorrow', '-f', 'valid_due_dates.xit'])
        lines = result.output.splitlines()
        assert result.exit_code == 0
        assert len(lines) > 0

        assert lines[0] == "#001 [ ] Task -> 2024-12-31"
        assert lines[1] == "#002 [ ] Task -> 2024-12-31"
        assert lines[2] == "#003 [ ] Task -> 2024-12-31"
        assert lines[3] == "#004 [ ] Task -> 2024-10-20"
        assert lines[4] == "#005 [ ] Task -> 2024-12-31"
        assert lines[5] == "#006 [ ] Task -> 2024-12-31"
        assert lines[6] == "#007 [ ] Task -> 2024-10-20"
        assert lines[7] == "#008 [ ] Task with description -> 2024-12-31 and more text"
        assert lines[8] == f'#009 [ ] Task due yesterday -> {yesterday_date}'
        assert lines[9] == f'#010 [ ] Task due today -> {today_date}'
        assert lines[10] == f'#011 [ ] Task due tomorrow -> {tomorrow_date}'
        assert lines[11] == ''
        assert lines[12].startswith('Showing 3 of')

    def test_show_tasks_due_by_date_natural_language2(self, isolated_test_files, runner):
        """Test showing tasks due by next week using natural language."""
        os.chdir(isolated_test_files)
        
        result = runner.invoke(xitkit, ['show', '--due-by', '1w', '-f', 'valid_due_dates.xit'])
        lines = result.output.splitlines()
        assert result.exit_code == 0
        assert len(lines) > 0
        assert lines[11] == f'#012 [ ] Task due next week -> {one_week_date}'
        assert lines[12] == ''
    
    def test_show_tasks_singular_tag(self, isolated_test_files, runner):
        """Test showing tasks with a singular tag filter."""
        os.chdir(isolated_test_files)
            
        result = runner.invoke(xitkit, ['show', '--tag', 'tags', '-f', 'valid_mixed.xit'])
        lines = result.output.splitlines()
        assert result.exit_code == 0
        assert len(lines) > 0
        assert lines[0] == '#008 [ ] Task with #tags -> 2024-10-21'
        assert lines[1] == '#009 [ ] Task with #multiple #tags'
        assert lines[2] == ''
        assert lines[3] == f'Showing 2 of 11 total tasks.'

    def test_show_tasks_multiple_tags(self, isolated_test_files, runner):
        """Test showing tasks with multiple tag filters."""
        os.chdir(isolated_test_files)
            
        result = runner.invoke(xitkit, ['show', '--tag', 'tags', '--tag', 'multiple', '-f', 'valid_mixed.xit'])
        lines = result.output.splitlines()
        assert result.exit_code == 0
        assert len(lines) > 0
        assert lines[0] == '#009 [ ] Task with #multiple #tags'
        assert lines[1] == ''
        assert lines[2] == f'Showing 1 of 11 total tasks.'

    def test_show_tasks_priority_filter(self, isolated_test_files, runner):
        """Test showing tasks with priority filter."""
        os.chdir(isolated_test_files)
            
        result = runner.invoke(xitkit, ['show', '--priority', '2', '-f', 'valid_mixed.xit'])
        lines = result.output.splitlines()
        assert result.exit_code == 0
        assert len(lines) > 0
        assert lines[0] == '#006 [ ] !! High priority task #urgent'
        assert lines[1] == ''
        assert lines[2] == f'Showing 1 of 11 total tasks.'

    def test_noid_flag(self, isolated_test_files, runner):
        """Test showing tasks with --noid flag."""
        os.chdir(isolated_test_files)
            
        result = runner.invoke(xitkit, ['show', '--no-id', '-f', 'valid_mixed.xit'])
        lines = result.output.splitlines()
        assert result.exit_code == 0
        assert len(lines) > 0
        assert lines[0] == '[ ] Open task'
        assert lines[1] == '[@] Ongoing task'
        # Further lines can be checked similarly

    def test_show_multiple_files(self, isolated_test_files, runner):
        """Test showing tasks from multiple files."""
        os.chdir(isolated_test_files)

        result = runner.invoke(xitkit, ['show', '-f', 'valid_status.xit', '-f', 'valid_mixed.xit'])
        print(result.output)
        lines = result.output.splitlines()
        assert result.exit_code == 0
        assert len(lines) > 0
        # Check that tasks from both files are present
        assert lines[0] == '#001 [ ] Open task'  # From valid_mixed.xit
        assert lines[11] == '         continues here' # last non-checked task from first file
        assert lines[12] == '#012 [ ] Open Task'  # From second file
        assert lines[16] == '#002 [x] Completed task with 3 trailing spaces   '  # From first file
        assert lines[17] == '#015 [x] Done Task'  # From second file

    def test_show_tasks_sorted_by_priority_asc(self, isolated_test_files, runner):
        """Test showing tasks sorted by priority in ascending order."""
        os.chdir(isolated_test_files)

        result = runner.invoke(xitkit, ['show', '--sort', 'priority', '--order', 'asc', '-f', 'valid_another_priority.xit'])
        print(result.output)
        
        lines = result.output.splitlines()
        assert result.exit_code == 0
        assert len(lines) > 0
        assert lines[0] == '#008 [ ] task with no priority'
        assert lines[1] == '#009 [ ] ... task with no priority but dots'
        assert lines[2] == '#001 [ ] ! priority 1 task'
        assert lines[3] == '#006 [ ] ....! priority 1 task with leading dots'
        assert lines[4] == '#007 [ ] !.... priority 1 task with trailing dots'
        assert lines[5] == '#002 [ ] !! priority 2 task'
        assert lines[6] == '#003 [ ] !!! priority 3 task'
        assert lines[7] == '#004 [ ] !!!! priority 4 task'
        assert lines[8] == '#005 [ ] !!!!! priority 5 task'
            
    def test_show_tasks_sorted_by_priority_desc(self, isolated_test_files, runner):
        """Test showing tasks sorted by priority in descending order."""
        os.chdir(isolated_test_files)

        result = runner.invoke(xitkit, ['show', '--sort', 'priority', '--order', 'desc', '-f', 'valid_another_priority.xit'])
        lines = result.output.splitlines()
        assert result.exit_code == 0
        assert len(lines) > 0
        assert lines[0] == '#005 [ ] !!!!! priority 5 task'
        assert lines[1] == '#004 [ ] !!!! priority 4 task'
        assert lines[2] == '#003 [ ] !!! priority 3 task'
        assert lines[3] == '#002 [ ] !! priority 2 task'
        assert lines[4] == '#001 [ ] ! priority 1 task'
        assert lines[5] == '#006 [ ] ....! priority 1 task with leading dots'
        assert lines[6] == '#007 [ ] !.... priority 1 task with trailing dots'
        assert lines[7] == '#008 [ ] task with no priority'
        assert lines[8] == '#009 [ ] ... task with no priority but dots'
            
    def test_show_tasks_sorted_by_due_date_asc(self, isolated_test_files, runner):
        """Test showing tasks sorted by due date in ascending order."""
        os.chdir(isolated_test_files)

        result = runner.invoke(xitkit, ['show', '--sort', 'due_date', '--order', 'asc', '-f', 'valid_another_due_dates.xit'])
        lines = result.output.splitlines()
        assert result.exit_code == 0
        assert len(lines) > 0
        # Tasks with earliest due dates should appear first

        assert lines[0] == '#004 [ ] Task due 2024-10-19 -> 2024-10-19'
        assert lines[1] == '#001 [ ] Task due 2024-10-20 -> 2024-10-20'
        assert lines[2] == '#003 [ ] Task due 2024-10-21 -> 2024-10-21'
        assert lines[3] == '#002 [ ] Task with no due date'
            
    def test_show_tasks_sorted_by_due_date_desc(self, isolated_test_files, runner):
        """Test showing tasks sorted by due date in descending order."""
        os.chdir(isolated_test_files)

        result = runner.invoke(xitkit, ['show', '--sort', 'due_date', '--order', 'desc', '-f', 'valid_another_due_dates.xit'])
        lines = result.output.splitlines()
        assert result.exit_code == 0
        assert len(lines) > 0
        # Tasks with latest due dates should appear first
        assert lines[0] == '#003 [ ] Task due 2024-10-21 -> 2024-10-21'
        assert lines[1] == '#001 [ ] Task due 2024-10-20 -> 2024-10-20'
        assert lines[2] == '#004 [ ] Task due 2024-10-19 -> 2024-10-19'
        assert lines[3] == '#002 [ ] Task with no due date'

            
    def test_show_tasks_sorted_invalid_attribute(self, isolated_test_files, runner):
        """Test show with invalid sort attribute."""
        os.chdir(isolated_test_files)
        
        
        result = runner.invoke(xitkit, ['show', '--sort', 'invalid_attr', '-f', 'valid_mixed.xit'])
        assert result.exit_code == 2  # Click validation error
        assert 'Invalid value' in result.output
            
    def test_show_tasks_sorted_invalid_order(self, isolated_test_files, runner):
        """Test show with invalid sort order."""
        os.chdir(isolated_test_files)
        
        
        result = runner.invoke(xitkit, ['show', '--sort', 'priority', '--order', 'invalid', '-f', 'valid_mixed.xit'])
        assert result.exit_code == 2  # Click validation error
        assert 'Invalid value' in result.output

    def test_show_tasks_sort_without_order_defaults_asc(self, isolated_test_files, runner):
        """Test that sorting without order defaults to ascending."""
        os.chdir(isolated_test_files)
        
        
        result = runner.invoke(xitkit, ['show', '--sort', 'priority', '-f', 'valid_mixed.xit'])
        lines = result.output.splitlines()
        assert result.exit_code == 0
        assert len(lines) > 0
        # Should default to ascending order

class TestStatsCLI(CLITest):
    """Test the 'stats' command of the CLI."""

    def test_stats_command(self, isolated_test_files, runner):
        """Test the stats command."""
        os.chdir(isolated_test_files)
        
        
        result = runner.invoke(xitkit, ['stats', '-f', 'valid_mixed.xit'])
        assert result.exit_code == 0
        assert 'Task Statistics' in result.output
        assert f'Total tasks: 11' in result.output
        assert 'By Status:' in result.output
        assert 'By Priority:' in result.output

    def test_stats_no_files(self, runner, tmpdir):
        """Test stats command when no task files exist."""
        os.chdir(tmpdir)
        result = runner.invoke(xitkit, ['stats'])
        assert result.exit_code == 0
        assert 'No task files found.' in result.output


class TestAddCLI(CLITest):
    """Test the 'add' command of the CLI."""

    def test_add_task_to_new_file(self, isolated_test_files, runner):
        """Test adding a task to a new file."""
        os.chdir(isolated_test_files)
        result = runner.invoke(xitkit, ['add', 'New test task', '--file', 'test.xit'])
        
        assert result.exit_code == 0
        assert '✓ Added task' in result.output
        assert 'New test task' in result.output
        
        # Verify file was created and contains the task
        assert Path('test.xit').exists()
        with open('test.xit', 'r') as f:
            content = f.read()
            assert '[ ] New test task' in content

    def test_add_task_to_existing_file(self, isolated_test_files, runner):
        """Test adding a task to an existing file."""
        os.chdir(isolated_test_files)
        
        result = runner.invoke(xitkit, ['add', 'Another task', '--file', 'valid_mixed.xit'])
        
        assert result.exit_code == 0
        assert '✓ Added task' in result.output
        
        # Verify task was appended
        with open('valid_mixed.xit', 'r') as f:
            content = f.read()
            assert '[ ] Another task' in content
            assert 'Open task' in content  # Original content preserved

    def test_add_task_default_file(self, isolated_test_files, runner):
        """Test adding a task without specifying file (should create todo.xit)."""
        os.chdir(isolated_test_files)
        result = runner.invoke(xitkit, ['add', 'Default file task'])
        
        assert result.exit_code == 0
        assert '✓ Added task' in result.output
        
        # Should create todo.xit by default
        assert Path('todo.xit').exists()
        with open('todo.xit', 'r') as f:
            content = f.read()
            assert '[ ] Default file task' in content

    def test_add_task_with_priority(self, isolated_test_files, runner):
        """Test adding a task with priority."""
        os.chdir(isolated_test_files)
        result = runner.invoke(xitkit, ['add', 'Priority task', '--priority', '3', '--file', 'prio_test.xit'])
        
        assert result.exit_code == 0
        assert '✓ Added task' in result.output
        
        # Verify task was added with correct priority
        with open('prio_test.xit', 'r') as f:
            content = f.read()
            assert '[ ] !!! Priority task' in content

    def test_add_task_with_due_date(self, isolated_test_files, runner):
        """Test adding a task with due date."""
        os.chdir(isolated_test_files)
        result = runner.invoke(xitkit, ['add', 'Due date task', '--due', '2024-12-31', '--file', 'due_test.xit'])
        
        assert result.exit_code == 0
        assert '✓ Added task' in result.output
        
        # Verify task was added with correct due date
        with open('due_test.xit', 'r') as f:
            content = f.read()
            assert '[ ] Due date task -> 2024-12-31' in content
        
    def test_add_task_with_tags(self, isolated_test_files, runner):
        """Test adding a task with tags."""
        os.chdir(isolated_test_files)
        result = runner.invoke(xitkit, ['add', 'Tagged task', '--tag', 'work', '--tag', 'urgent', '--file', 'tag_test.xit'])
        
        assert result.exit_code == 0
        assert '✓ Added task' in result.output
        
        # Verify task was added with correct tags
        with open('tag_test.xit', 'r') as f:
            content = f.read()
            assert '[ ] Tagged task #work #urgent' in content

    def test_add_task_due_date_in_description(self, isolated_test_files, runner):
        """Test adding a task with due date specified in description."""
        os.chdir(isolated_test_files)
        result = runner.invoke(xitkit, ['add', 'Task with due date -> 2024-11-15', '--file', 'due_in_desc.xit'])
        
        assert result.exit_code == 0
        assert '✓ Added task' in result.output
        
        # Verify task was added with correct due date
        with open('due_in_desc.xit', 'r') as f:
            content = f.read()
            assert '[ ] Task with due date -> 2024-11-15' in content

    def test_add_task_due_date_natural_language1(self, isolated_test_files, runner):
        """Test adding a task with natural language due date 'tomorrow'."""
        os.chdir(isolated_test_files)
        result = runner.invoke(xitkit, ['add', 'Task due tomorrow', '--due', 'tomorrow', '--file', 'due_nl1.xit'])
        
        assert result.exit_code == 0
        assert '✓ Added task' in result.output
        tomorrow_date = datetime.now().date() + timedelta(days=1)
        
        # Verify task was added with correct due date
        with open('due_nl1.xit', 'r') as f:
            content = f.read()
            assert f'[ ] Task due tomorrow -> {tomorrow_date}' in content
    
    def test_add_task_due_date_natural_language2(self, isolated_test_files, runner):
        """Test adding a task with natural language due date."""
        os.chdir(isolated_test_files)
        result = runner.invoke(xitkit, ['add', 'Task due in 9 days', '--due', '1w2d', '--file', 'due_nl2.xit'])

        assert result.exit_code == 0
        assert '✓ Added task' in result.output
        next_week_date = datetime.now().date() + timedelta(weeks=1) + timedelta(days=2)

        # Verify task was added with correct due date
        with open('due_nl2.xit', 'r') as f:
            content = f.read()
            assert f'[ ] Task due in 9 days -> {next_week_date}' in content
    
    def test_add_task_due_date_natural_language3(self, isolated_test_files, runner):
        """Test adding a task with natural language due date yesterday."""
        os.chdir(isolated_test_files)
        result = runner.invoke(xitkit, ['add', 'Task due yesterday', '--due', 'yesterday', '--file', 'due_nl3.xit'])

        assert result.exit_code == 0
        assert '✓ Added task' in result.output
        yesterday_date = datetime.now().date() - timedelta(days=1)

        # Verify task was added with correct due date
        with open('due_nl3.xit', 'r') as f:
            content = f.read()
            assert f'[ ] Task due yesterday -> {yesterday_date}' in content

    def test_add_task_tags_in_description(self, isolated_test_files, runner):
        """Test adding a task with tags specified in description."""
        os.chdir(isolated_test_files)
        result = runner.invoke(xitkit, ['add', 'Task with #tag1 #tag2 in description', '--file', 'tags_in_desc.xit'])
        
        assert result.exit_code == 0
        assert '✓ Added task' in result.output
        
        # Verify task was added with correct tags
        with open('tags_in_desc.xit', 'r') as f:
            content = f.read()
            assert '[ ] Task with #tag1 #tag2 in description' in content

    def test_add_task_line_breaks_in_description(self, isolated_test_files, runner):
        """Test adding a task with line breaks in description."""
        os.chdir(isolated_test_files)
        result = runner.invoke(xitkit, ['add', 'Multi-line task description\\nContinues here\\nAnd here', '--file', 'multiline_desc.xit'])
        
        assert result.exit_code == 0
        assert '✓ Added task' in result.output
        
        # Verify task was added with correct multi-line description
        with open('multiline_desc.xit', 'r') as f:
            content = f.read()
            assert '[ ] Multi-line task description' in content
            assert '    Continues here' in content
            assert '    And here' in content

class TestMarkCLI(CLITest):
    """Test the 'mark' command of the CLI."""

    @pytest.mark.parametrize("status,flag,expected_symbol", [
        ('OPEN', '--open', '[ ]'),
        ('CHECKED', '--done', '[x]'),
        ('ONGOING', '--ongoing', '[@]'),
        ('OBSOLETE', '--obsolete', '[~]'),
        ('IN_QUESTION', '--inquestion', '[?]'),
    ])
    def test_mark_task_statuses(self, isolated_test_files, runner, status, flag, expected_symbol):
        """Test marking tasks with different statuses."""
        os.chdir(isolated_test_files)
        
        result = runner.invoke(xitkit, ['mark', '1', flag, '-f', 'valid_mixed.xit', '--debug'])
        print(result)
        assert result.exit_code == 0
        assert f'Marked task #001 as {status}' in result.output
        
        # Verify file was modified
        with open('valid_mixed.xit', 'r') as f:
            content = f.read()
            assert expected_symbol in content

    def test_mark_multiple_tasks(self, isolated_test_files, runner):
        """Test marking multiple tasks at once."""
        os.chdir(isolated_test_files)

        result = runner.invoke(xitkit, ['mark', '1', '2', '--done', '-f', 'valid_mixed.xit'])
        
        assert result.exit_code == 0
        assert 'Marked task #001 as CHECKED' in result.output
        assert 'Marked task #002 as CHECKED' in result.output
        assert 'Processed 2 of 2 tasks' in result.output
        
        # Verify both tasks were marked
        with open('valid_mixed.xit', 'r') as f:
            content = f.read()
            lines = content.strip().split('\n')
            assert '[x] Open task' in lines[1]
            assert '[x] Completed task with 3 trailing spaces' in lines[2]
            assert '[@] Ongoing task' in lines[3]  # Third task unchanged

    def test_mark_nonexistent_task(self, isolated_test_files, runner):
        """Test marking a task that doesn't exist."""
        os.chdir(isolated_test_files)
        
        result = runner.invoke(xitkit, ['mark', '999', '--done', '-f', 'valid_mixed.xit'])
        
        assert result.exit_code == 0  # Command succeeds but shows error
        assert 'No matching tasks found for the specified IDs.' in result.output

    def test_mark_missing_arguments(self, isolated_test_files, runner):
        """Test mark command with missing required arguments."""
        os.chdir(isolated_test_files)
        # Missing task ID
        result = runner.invoke(xitkit, ['mark', '--done'])
        assert result.exit_code == 1
        assert 'Must specify at least one task ID' in result.output
        
        # Missing status flag
        result = runner.invoke(xitkit, ['mark', '1'])
        assert result.exit_code == 1
        assert 'Must specify a status flag' in result.output

class TestPrioCLI(CLITest):
    """Test the 'prio' command of the CLI."""

    def test_prio_command(self, isolated_test_files, runner):
        """Test setting task priority."""
        os.chdir(isolated_test_files)
        
        result = runner.invoke(xitkit, ['prio', '-t', '1', '-p', '5', '-f', 'valid_mixed.xit'])
        print(result.output)
        
        assert result.exit_code == 0
        assert 'Set priority (5) for task #001' in result.output
        
        # Verify priority was set
        with open('valid_mixed.xit', 'r') as f:
            content = f.read()
            assert '[ ] !!!!! Open task' in content

    def test_prio_remove_priority(self, isolated_test_files, runner):
        """Test removing priority (setting to 0)."""
        os.chdir(isolated_test_files)

        result = runner.invoke(xitkit, ['prio', '-t', '1', '-p', '0', '-f', 'valid_mixed.xit'])

        assert result.exit_code == 0
        assert 'Set priority (none) for task #001' in result.output
        
        # Verify priority was removed
        with open('valid_mixed.xit', 'r') as f:
            content = f.read()
            assert '[ ] Open task' in content
            # Note: This task didn't have priority to begin with, so no change expected

    def test_prio_invalid_priority(self, isolated_test_files, runner):
        """Test setting invalid priority."""
        os.chdir(isolated_test_files)

        result = runner.invoke(xitkit, ['prio', '-t', '1', '-p', '-1', '-f', 'valid_mixed.xit'])
        print(result.output
              )
        # Negative priorities are rejected at CLI parsing level
        assert result.exit_code == 0
        assert 'Priority level cannot be negative' in result.output


class TestTagCLI(CLITest):

    def test_tag_command(self, isolated_test_files, runner):
        """Test adding a tag to a task."""
        os.chdir(isolated_test_files)

        result = runner.invoke(xitkit, ['tag', '-t', '1', '--tag', 'urgent', '-f', 'valid_mixed.xit'])

        assert result.exit_code == 0
        assert 'Added tag #urgent to task #001' in result.output
        
        # Verify tag was added
        with open('valid_mixed.xit', 'r') as f:
            content = f.read()
            assert '#urgent' in content

    def test_tag_with_hash_prefix(self, isolated_test_files, runner):
        """Test adding a tag that already has # prefix."""
        os.chdir(isolated_test_files)

        result = runner.invoke(xitkit, ['tag', '-t', '1', '--tag', '#urgent', '-f', 'valid_mixed.xit'])

        assert result.exit_code == 0
        assert 'Added tag #urgent to task #001' in result.output
        
        # Verify tag was added (should not duplicate #)
        with open('valid_mixed.xit', 'r') as f:
            content = f.read()
            assert '#urgent' in content
            assert '##urgent' not in content
        
    def test_tag_with_multi_line_task(self, isolated_test_files, runner):
        """Test adding a tag to a multi-line task."""
        os.chdir(isolated_test_files)

        result = runner.invoke(xitkit, ['tag', '-t', '11', '--tag', 'important', '-f', 'valid_mixed.xit'])

        assert result.exit_code == 0
        assert 'Added tag #important to task #011' in result.output

        # Verify tag was added to the correct task
        with open('valid_mixed.xit', 'r') as f:
            content = f.read()
            lines = content.strip().split('\n')
            for i, line in enumerate(lines):
                print(f"line {i}: {line}")
            assert lines[11] == "[ ] multi-line"
            assert lines[12] == "    task description"
            assert lines[13] == "    continues here #important"
            assert len(lines) == 14  # Ensure no extra lines were added

class TestUntagCLI(CLITest):
    """Test the 'untag' command of the CLI."""

    def test_untag_command(self, isolated_test_files, runner):
        """Test removing a tag from a task."""
        os.chdir(isolated_test_files)
        
        result = runner.invoke(xitkit, ['untag', '6', 'urgent', '-f', 'valid_mixed.xit'])
        
        assert result.exit_code == 0
        assert 'Removed tag #urgent from task #006' in result.output
        
        # Verify tag was removed from that specific task
        with open('valid_mixed.xit', 'r') as f:
            content = f.read()
            lines = content.strip().split('\n')
            # Check that task 6 no longer has #urgent but still has the rest
            assert '[ ] !! High priority task' in lines[6]  # Task 6 without #urgent
            assert '#urgent' not in lines[6]

class TestEditCLI(CLITest):
    """Test the 'edit' command of the CLI."""

    def test_edit_command(self, isolated_test_files, runner):
        """Test editing a task description."""
        os.chdir(isolated_test_files)
        
        result = runner.invoke(xitkit, ['edit', '1', 'Updated task description', '-f', 'valid_mixed.xit'])
        
        assert result.exit_code == 0
        assert 'Updated description for task #001' in result.output
        assert 'Updated task description' in result.output
        
        # Verify description was updated
        with open('valid_mixed.xit', 'r') as f:
            content = f.read()
            assert '[ ] Updated task description' in content
            assert 'Original task' not in content

    def test_edit_nonexistent_task(self, isolated_test_files, runner):
        """Test editing a task that doesn't exist."""
        os.chdir(isolated_test_files)
        
        result = runner.invoke(xitkit, ['edit', '999', 'New description', '-f', 'valid_mixed.xit'])
        
        assert result.exit_code == 0
        assert 'Task #999 not found' in result.output

    


class TestCLIIntegration:
    """Integration tests combining multiple CLI operations."""
    
    @pytest.fixture
    def runner(self):
        """Provide a Click test runner."""
        return CliRunner()

    # def test_full_task_lifecycle(self, isolated_test_files, runner):
    #     """Test a complete task lifecycle: add -> show -> mark -> edit -> tag -> untag."""
    #     os.chdir(isolated_test_files)
    #         # Add a task
    #         result = runner.invoke(xitkit, ['add', 'Complete project', '--file', 'project.xit'])
    #         assert result.exit_code == 0
            
    #         # Show the task
    #         result = runner.invoke(xitkit, ['show', '-f', 'project.xit'])
    #         assert result.exit_code == 0
    #         assert 'Complete project' in result.output
            
    #         # Mark as ongoing
    #         result = runner.invoke(xitkit, ['mark', '1', '--ongoing', '-f', 'project.xit'])
    #         assert result.exit_code == 0
            
    #         # Add priority
    #         result = runner.invoke(xitkit, ['prio', '1', '2', '-f', 'project.xit'])
    #         assert result.exit_code == 0
            
    #         # Add tag
    #         result = runner.invoke(xitkit, ['tag', '1', 'urgent', '-f', 'project.xit'])
    #         assert result.exit_code == 0
            
    #         # Edit description
    #         result = runner.invoke(xitkit, ['edit', '1', 'Complete important project', '-f', 'project.xit'])
    #         assert result.exit_code == 0
            
    #         # Verify final state
    #         with open('project.xit', 'r') as f:
    #             content = f.read()
    #             assert '[@] !! Complete important project #urgent' in content
            
    #         # Mark as done
    #         result = runner.invoke(xitkit, ['mark', '1', '--done', '-f', 'project.xit'])
    #         assert result.exit_code == 0
            
    #         # Verify final completion
    #         with open('project.xit', 'r') as f:
    #             content = f.read()
    #             assert '[x] !! Complete important project #urgent' in content

    def test_multiple_tasks_operations(self, isolated_test_files, runner):
        """Test operations on multiple tasks."""
        os.chdir(isolated_test_files)
        # Add multiple tasks
        for i in range(1, 4):
            result = runner.invoke(xitkit, ['add', f'Task {i}', '--file', 'multiple.xit'])
            assert result.exit_code == 0
        
        # Mark multiple tasks as done
        result = runner.invoke(xitkit, ['mark', '1', '2', '--done', '-f', 'multiple.xit'])
        assert result.exit_code == 0
        assert 'Processed 2 of 2 tasks' in result.output
        
        # Verify states
        with open('multiple.xit', 'r') as f:
            lines = f.readlines()
            assert "To Do" in lines[0]
            assert '[x] Task 1' in lines[1]
            assert '[x] Task 2' in lines[2]
            assert '[ ] Task 3' in lines[3]
        
        # Check stats
        result = runner.invoke(xitkit, ['stats', '-f', 'multiple.xit'])
        assert result.exit_code == 0
        assert 'Total tasks: 3' in result.output
        assert 'Done: 2' in result.output
        assert 'Open: 1' in result.output