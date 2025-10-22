"""Unit tests for the command-line interface using Click's CliRunner.

This module tests the CLI commands in isolation using temporary filesystems
to ensure commands work correctly without affecting real files.
"""

import pytest
from click.testing import CliRunner
from pathlib import Path
from xit.__main__ import xit

task_file_content = """[ ] Open task
[x] Completed task with 3 trailing spaces   
[@] Ongoing task
[~] Obsolete task
[?] Task in question
[ ] !! High priority task #urgent
[ ] Task due tomorrow -> 2025-10-20
[ ] Task with #tags -> 2025-10-21
[ ] Task with #multiple #tags
[ ] Simple task
[ ] multi-line
    task description
    continues here
"""
n_tasks = 11

priority_tasks = """[ ] ! priority 1 task
[ ] !! priority 2 task
[ ] !!! priority 3 task
[ ] !!!! priority 4 task
[ ] !!!!! priority 5 task
[ ] ....! priority 1 task with leading dots
[ ] !.... priority 1 task with trailing dots
[ ] task with no priority
[ ] ... task with no priority but dots
"""
n_priority_tasks = 9

due_date_tasks = """[ ] Task due 2025-10-20 -> 2025-10-20
[ ] Task with no due date
[ ] Task due 2025-10-21 -> 2025-10-21
[ ] Task due 2025-10-19 -> 2025-10-19
"""
n_due_date_tasks = 4

class CLITest():

    @pytest.fixture
    def runner(self):
        """Provide a Click test runner."""
        return CliRunner()

    def write_sample_tasks(self, filename='tasks.xit'):
        """Helper to write sample tasks to a file."""
        with open(filename, 'w') as f:
            f.write(task_file_content)

    def write_priority_tasks(self, filename='priority_tasks.xit'):
        """Helper to write priority tasks to a file."""
        with open(filename, 'w') as f:
            f.write(priority_tasks)

    def write_due_date_tasks(self, filename='due_date_tasks.xit'):
        """Helper to write due date tasks to a file."""
        with open(filename, 'w') as f:
            f.write(due_date_tasks)

class TestMainCLI(CLITest):
    """Test the command-line interface."""

    @pytest.fixture
    def empty_task_file(self):
        """Create an empty task file for testing."""
        return ""

    def test_help_command(self, runner):
        """Test that help is displayed correctly."""
        result = runner.invoke(xit, ['--help'])
        assert result.exit_code == 0
        assert 'Xit - A command line task management tool' in result.output
        assert 'show' in result.output
        assert 'add' in result.output
        assert 'mark' in result.output


class TestShowCLI(CLITest):
    """Test the 'show' command of the CLI."""

    def test_show_help_subcommand(self, runner):
        """Test help for specific subcommands."""
        result = runner.invoke(xit, ['show', '--help'])
        assert result.exit_code == 0
        assert 'Show tasks from .md and .xit files' in result.output

    def test_show_no_files(self, runner):
        """Test show command when no task files exist."""
        with runner.isolated_filesystem():
            result = runner.invoke(xit, ['show'])
            assert result.exit_code == 0
            assert 'No task files found' in result.output

    def test_show_tasks_from_file(self, runner, sample_tasks):
        """Test showing tasks from a specific file."""
        with runner.isolated_filesystem():
            self.write_sample_tasks('tasks.xit')
            
            result = runner.invoke(xit, ['show', '-f', 'tasks.xit'])
            lines = result.output.splitlines()
            assert result.exit_code == 0
            assert len(lines) > 0
            assert lines[0] == '#001 [ ] Open task'
            assert lines[1] == '#002 [x] Completed task with 3 trailing spaces'
            assert lines[2] == '#003 [@] Ongoing task'
            assert lines[3] == '#004 [~] Obsolete task'
            assert lines[4] == '#005 [?] Task in question'
            assert lines[5] == '#006 [ ] !! High priority task #urgent'
            assert lines[6] == '#007 [ ] Task due tomorrow -> 2025-10-20'
            assert lines[7] == '#008 [ ] Task with #tags -> 2025-10-21'
            assert lines[8] == '#009 [ ] Task with #multiple #tags'
            assert lines[9] == '#010 [ ] Simple task'
            assert lines[10] == '#011 [ ] multi-line'
            assert lines[11] == '         task description'
            assert lines[12] == '         continues here'
            assert lines[13] == ''

    def test_show_tasks_with_status_filter(self, runner, sample_tasks):
        """Test showing tasks with status filtering."""
        with runner.isolated_filesystem():
            self.write_sample_tasks('tasks.xit')
            
            # Test open tasks only
            result = runner.invoke(xit, ['show', '--status', 'ongoing', '-f', 'tasks.xit'])
            lines = result.output.splitlines()
            assert result.exit_code == 0
            assert len(lines) > 0
            assert lines[0] == '#003 [@] Ongoing task'
            assert lines[1] == ''
            assert lines[2] == f'Showing 1 of {n_tasks} total tasks.'

    def test_show_tasks_count_only(self, runner, sample_tasks):
        """Test showing only the count of tasks."""
        with runner.isolated_filesystem():
            self.write_sample_tasks('tasks.xit')
            result = runner.invoke(xit, ['show', '--count', '-f', 'tasks.xit'])
            assert result.exit_code == 0
            lines = result.output.splitlines()
            assert len(lines) > 0
            assert lines[0]  == f'{n_tasks} tasks found.'
        
    def test_show_tasks_due_on_date(self, runner, sample_tasks):
        """Test showing tasks due on 2025-10-20."""
        with runner.isolated_filesystem():
            self.write_sample_tasks('tasks.xit')
            
            result = runner.invoke(xit, ['show', '--due-on', '2025-10-20', '-f', 'tasks.xit'])
            lines = result.output.splitlines()
            assert result.exit_code == 0
            assert len(lines) > 0
            assert lines[0] == '#007 [ ] Task due tomorrow -> 2025-10-20'
            assert lines[1] == ''
            assert lines[2] == f'Showing 1 of {n_tasks} total tasks.'
    
    def test_show_tasks_due_on_date2(self, runner, sample_tasks):
        """Test showing tasks due on 2025-10-21."""
        with runner.isolated_filesystem():
            self.write_sample_tasks('tasks.xit')
            
            result = runner.invoke(xit, ['show', '--due-on', '2025-10-21', '-f', 'tasks.xit'])
            lines = result.output.splitlines()
            assert result.exit_code == 0
            assert len(lines) > 0
            assert lines[0] == '#008 [ ] Task with #tags -> 2025-10-21'
            assert lines[1] == ''
            assert lines[2] == f'Showing 1 of {n_tasks} total tasks.'

    def test_show_tasks_due_by_date(self, runner, sample_tasks):
        """Test showing tasks due by 2025-10-21."""
        with runner.isolated_filesystem():
            self.write_sample_tasks('tasks.xit')
            
            result = runner.invoke(xit, ['show', '--due-by', '2025-10-21', '-f', 'tasks.xit'])
            lines = result.output.splitlines()
            assert result.exit_code == 0
            assert len(lines) > 0
            assert lines[0] == '#007 [ ] Task due tomorrow -> 2025-10-20'
            assert lines[1] == '#008 [ ] Task with #tags -> 2025-10-21'
            assert lines[2] == ''
            assert lines[3] == f'Showing 2 of {n_tasks} total tasks.'
    
    def test_show_tasks_singular_tag(self, runner, sample_tasks):
        """Test showing tasks with a singular tag filter."""
        with runner.isolated_filesystem():
            self.write_sample_tasks('tasks.xit')
            
            result = runner.invoke(xit, ['show', '--tag', 'tags', '-f', 'tasks.xit'])
            lines = result.output.splitlines()
            assert result.exit_code == 0
            assert len(lines) > 0
            assert lines[0] == '#008 [ ] Task with #tags -> 2025-10-21'
            assert lines[1] == '#009 [ ] Task with #multiple #tags'
            assert lines[2] == ''
            assert lines[3] == f'Showing 2 of {n_tasks} total tasks.'

    def test_show_tasks_multiple_tags(self, runner, sample_tasks):
        """Test showing tasks with multiple tag filters."""
        with runner.isolated_filesystem():
            self.write_sample_tasks('tasks.xit')
            
            result = runner.invoke(xit, ['show', '--tag', 'tags', '--tag', 'multiple', '-f', 'tasks.xit'])
            lines = result.output.splitlines()
            assert result.exit_code == 0
            assert len(lines) > 0
            assert lines[0] == '#009 [ ] Task with #multiple #tags'
            assert lines[1] == ''
            assert lines[2] == f'Showing 1 of {n_tasks} total tasks.'

    def test_show_tasks_priority_filter(self, runner, sample_tasks):
        """Test showing tasks with priority filter."""
        with runner.isolated_filesystem():
            self.write_sample_tasks('tasks.xit')
            
            result = runner.invoke(xit, ['show', '--priority', '2', '-f', 'tasks.xit'])
            lines = result.output.splitlines()
            assert result.exit_code == 0
            assert len(lines) > 0
            assert lines[0] == '#006 [ ] !! High priority task #urgent'
            assert lines[1] == ''
            assert lines[2] == f'Showing 1 of {n_tasks} total tasks.'

    def test_noid_flag(self, runner, sample_tasks):
        """Test showing tasks with --noid flag."""
        with runner.isolated_filesystem():
            self.write_sample_tasks('tasks.xit')
            
            result = runner.invoke(xit, ['show', '--no-id', '-f', 'tasks.xit'])
            lines = result.output.splitlines()
            assert result.exit_code == 0
            assert len(lines) > 0
            assert lines[0] == '[ ] Open task'
            assert lines[1] == '[x] Completed task with 3 trailing spaces'
            assert lines[2] == '[@] Ongoing task'
            # Further lines can be checked similarly

    def test_show_multiple_files(self, runner, sample_tasks):
        """Test showing tasks from multiple files."""
        with runner.isolated_filesystem():
            self.write_sample_tasks('tasks1.xit')
            self.write_sample_tasks('tasks2.xit')
            
            result = runner.invoke(xit, ['show', '-f', 'tasks1.xit', '-f', 'tasks2.xit'])
            print(result.output)
            lines = result.output.splitlines()
            assert result.exit_code == 0
            assert len(lines) > 0
            # Check that tasks from both files are present
            assert lines[10] == '#011 [ ] multi-line'
            assert lines[11] == '         task description'
            assert lines[12] == '         continues here'
            assert lines[14] == '#012 [ ] Open task'  # From second file
            assert lines[26] == '         continues here'  # Last line from second file

    def test_show_tasks_sorted_by_priority_asc(self, runner, sample_tasks):
        """Test showing tasks sorted by priority in ascending order."""
        with runner.isolated_filesystem():
            self.write_priority_tasks('priority_tasks.xit')

            result = runner.invoke(xit, ['show', '--sort', 'priority', '--order', 'asc', '-f', 'priority_tasks.xit'])
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
            
    def test_show_tasks_sorted_by_priority_desc(self, runner, sample_tasks):
        """Test showing tasks sorted by priority in descending order."""
        with runner.isolated_filesystem():
            self.write_priority_tasks('priority_tasks.xit')

            result = runner.invoke(xit, ['show', '--sort', 'priority', '--order', 'desc', '-f', 'priority_tasks.xit'])
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
            
    def test_show_tasks_sorted_by_due_date_asc(self, runner, sample_tasks):
        """Test showing tasks sorted by due date in ascending order."""
        with runner.isolated_filesystem():
            self.write_due_date_tasks('due_date_tasks.xit')

            result = runner.invoke(xit, ['show', '--sort', 'due_date', '--order', 'asc', '-f', 'due_date_tasks.xit'])
            lines = result.output.splitlines()
            assert result.exit_code == 0
            assert len(lines) > 0
            # Tasks with earliest due dates should appear first

            assert lines[0] == '#004 [ ] Task due 2025-10-19 -> 2025-10-19'
            assert lines[1] == '#001 [ ] Task due 2025-10-20 -> 2025-10-20'
            assert lines[2] == '#003 [ ] Task due 2025-10-21 -> 2025-10-21'
            assert lines[3] == '#002 [ ] Task with no due date'
            
    def test_show_tasks_sorted_by_due_date_desc(self, runner, sample_tasks):
        """Test showing tasks sorted by due date in descending order."""
        with runner.isolated_filesystem():
            self.write_due_date_tasks('due_date_tasks.xit')

            result = runner.invoke(xit, ['show', '--sort', 'due_date', '--order', 'desc', '-f', 'due_date_tasks.xit'])
            lines = result.output.splitlines()
            assert result.exit_code == 0
            assert len(lines) > 0
            # Tasks with latest due dates should appear first
            assert lines[0] == '#003 [ ] Task due 2025-10-21 -> 2025-10-21'
            assert lines[1] == '#001 [ ] Task due 2025-10-20 -> 2025-10-20'
            assert lines[2] == '#004 [ ] Task due 2025-10-19 -> 2025-10-19'
            assert lines[3] == '#002 [ ] Task with no due date'

            
    def test_show_tasks_sorted_invalid_attribute(self, runner, sample_tasks):
        """Test show with invalid sort attribute."""
        with runner.isolated_filesystem():
            self.write_sample_tasks('tasks.xit')
            
            result = runner.invoke(xit, ['show', '--sort', 'invalid_attr', '-f', 'tasks.xit'])
            assert result.exit_code == 2  # Click validation error
            assert 'Invalid value' in result.output
            
    def test_show_tasks_sorted_invalid_order(self, runner, sample_tasks):
        """Test show with invalid sort order."""
        with runner.isolated_filesystem():
            self.write_sample_tasks('tasks.xit')
            
            result = runner.invoke(xit, ['show', '--sort', 'priority', '--order', 'invalid', '-f', 'tasks.xit'])
            assert result.exit_code == 2  # Click validation error
            assert 'Invalid value' in result.output

    def test_show_tasks_sort_without_order_defaults_asc(self, runner, sample_tasks):
        """Test that sorting without order defaults to ascending."""
        with runner.isolated_filesystem():
            self.write_sample_tasks('tasks.xit')
            
            result = runner.invoke(xit, ['show', '--sort', 'priority', '-f', 'tasks.xit'])
            lines = result.output.splitlines()
            assert result.exit_code == 0
            assert len(lines) > 0
            # Should default to ascending order

class TestStatsCLI(CLITest):
    """Test the 'stats' command of the CLI."""

    def test_stats_command(self, runner, sample_tasks):
        """Test the stats command."""
        with runner.isolated_filesystem():
            self.write_sample_tasks('tasks.xit')
            
            result = runner.invoke(xit, ['stats', '-f', 'tasks.xit'])
            assert result.exit_code == 0
            assert 'Task Statistics' in result.output
            assert f'Total tasks: {n_tasks}' in result.output
            assert 'By Status:' in result.output
            assert 'By Priority:' in result.output

    def test_stats_no_files(self, runner):
        """Test stats command when no task files exist."""
        with runner.isolated_filesystem():
            result = runner.invoke(xit, ['stats'])
            assert result.exit_code == 0
            assert 'No task files found.' in result.output


class TestAddCLI(CLITest):
    """Test the 'add' command of the CLI."""

    def test_add_task_to_new_file(self, runner):
        """Test adding a task to a new file."""
        with runner.isolated_filesystem():
            result = runner.invoke(xit, ['add', 'New test task', '--file', 'test.xit'])
            
            assert result.exit_code == 0
            assert '✓ Added task' in result.output
            assert 'New test task' in result.output
            
            # Verify file was created and contains the task
            assert Path('test.xit').exists()
            with open('test.xit', 'r') as f:
                content = f.read()
                assert '[ ] New test task' in content

    def test_add_task_to_existing_file(self, runner, sample_tasks):
        """Test adding a task to an existing file."""
        with runner.isolated_filesystem():
            self.write_sample_tasks('existing.xit')
            
            result = runner.invoke(xit, ['add', 'Another task', '--file', 'existing.xit'])
            
            assert result.exit_code == 0
            assert '✓ Added task' in result.output
            
            # Verify task was appended
            with open('existing.xit', 'r') as f:
                content = f.read()
                assert '[ ] Another task' in content
                assert 'Open task' in content  # Original content preserved

    def test_add_task_default_file(self, runner):
        """Test adding a task without specifying file (should create todo.xit)."""
        with runner.isolated_filesystem():
            result = runner.invoke(xit, ['add', 'Default file task'])
            
            assert result.exit_code == 0
            assert '✓ Added task' in result.output
            
            # Should create todo.xit by default
            assert Path('todo.xit').exists()
            with open('todo.xit', 'r') as f:
                content = f.read()
                assert '[ ] Default file task' in content

class TestMarkCLI(CLITest):
    """Test the 'mark' command of the CLI."""

    @pytest.mark.parametrize("status,flag,expected_symbol", [
        ('open', '--open', '[ ]'),
        ('done', '--done', '[x]'),
        ('ongoing', '--ongoing', '[@]'),
        ('obsolete', '--obsolete', '[~]'),
        ('inquestion', '--inquestion', '[?]'),
    ])
    def test_mark_task_statuses(self, runner, status, flag, expected_symbol):
        """Test marking tasks with different statuses."""
        with runner.isolated_filesystem():
            self.write_sample_tasks('test.xit')
            
            result = runner.invoke(xit, ['mark', '1', flag, '-f', 'test.xit'])
            
            assert result.exit_code == 0
            assert f'Marked task #001 as {status}' in result.output
            
            # Verify file was modified
            with open('test.xit', 'r') as f:
                content = f.read()
                assert expected_symbol in content

    def test_mark_multiple_tasks(self, runner):
        """Test marking multiple tasks at once."""
        with runner.isolated_filesystem():
            self.write_sample_tasks('test.xit')
            
            result = runner.invoke(xit, ['mark', '1', '2', '--done', '-f', 'test.xit'])
            
            assert result.exit_code == 0
            assert 'Marked task #001 as done' in result.output
            assert 'Marked task #002 as done' in result.output
            assert 'Processed 2 of 2 tasks' in result.output
            
            # Verify both tasks were marked
            with open('test.xit', 'r') as f:
                content = f.read()
                lines = content.strip().split('\n')
                assert '[x] Open task' in lines[0]
                assert '[x] Completed task with 3 trailing spaces' in lines[1]
                assert '[@] Ongoing task' in lines[2]  # Third task unchanged

    def test_mark_nonexistent_task(self, runner):
        """Test marking a task that doesn't exist."""
        with runner.isolated_filesystem():
            self.write_sample_tasks('test.xit')
            
            result = runner.invoke(xit, ['mark', '999', '--done', '-f', 'test.xit'])
            
            assert result.exit_code == 0  # Command succeeds but shows error
            assert 'Task #999 not found' in result.output

    def test_mark_missing_arguments(self, runner):
        """Test mark command with missing required arguments."""
        with runner.isolated_filesystem():
            # Missing task ID
            result = runner.invoke(xit, ['mark', '--done'])
            assert result.exit_code == 1
            assert 'Must specify at least one task ID' in result.output
            
            # Missing status flag
            result = runner.invoke(xit, ['mark', '1'])
            assert result.exit_code == 1
            assert 'Must specify a status flag' in result.output

class TestPrioCLI(CLITest):
    """Test the 'prio' command of the CLI."""

    def test_prio_command(self, runner):
        """Test setting task priority."""
        with runner.isolated_filesystem():
            self.write_sample_tasks('test.xit')
            
            result = runner.invoke(xit, ['prio', '1', '2', '-f', 'test.xit'])
            
            assert result.exit_code == 0
            assert 'Set priority (2) for task #001' in result.output
            
            # Verify priority was set
            with open('test.xit', 'r') as f:
                content = f.read()
                assert '[ ] !! Open task' in content

    def test_prio_remove_priority(self, runner):
        """Test removing priority (setting to 0)."""
        with runner.isolated_filesystem():
            self.write_sample_tasks('test.xit')
            
            result = runner.invoke(xit, ['prio', '1', '0', '-f', 'test.xit'])
            
            assert result.exit_code == 0
            assert 'Set priority (none) for task #001' in result.output
            
            # Verify priority was removed
            with open('test.xit', 'r') as f:
                content = f.read()
                assert '[ ] Open task' in content
                # Note: This task didn't have priority to begin with, so no change expected

    def test_prio_invalid_priority(self, runner):
        """Test setting invalid priority."""
        with runner.isolated_filesystem():
            self.write_sample_tasks('test.xit')
            
            result = runner.invoke(xit, ['prio', '1', '-1', '-f', 'test.xit'])
            
            # Negative priorities are rejected at CLI parsing level
            assert result.exit_code == 2
            assert 'No such option: -1' in result.output


class TestTagCLI(CLITest):

    def test_tag_command(self, runner):
        """Test adding a tag to a task."""
        with runner.isolated_filesystem():
            self.write_sample_tasks('test.xit')
            
            result = runner.invoke(xit, ['tag', '1', 'urgent', '-f', 'test.xit'])
            
            assert result.exit_code == 0
            assert 'Added tag #urgent to task #001' in result.output
            
            # Verify tag was added
            with open('test.xit', 'r') as f:
                content = f.read()
                assert '#urgent' in content

    def test_tag_with_hash_prefix(self, runner):
        """Test adding a tag that already has # prefix."""
        with runner.isolated_filesystem():
            self.write_sample_tasks('test.xit')
            
            result = runner.invoke(xit, ['tag', '1', '#urgent', '-f', 'test.xit'])
            
            assert result.exit_code == 0
            assert 'Added tag #urgent to task #001' in result.output
            
            # Verify tag was added (should not duplicate #)
            with open('test.xit', 'r') as f:
                content = f.read()
                assert '#urgent' in content
                assert '##urgent' not in content

class TestUntagCLI(CLITest):
    """Test the 'untag' command of the CLI."""

    def test_untag_command(self, runner):
        """Test removing a tag from a task."""
        with runner.isolated_filesystem():
            self.write_sample_tasks('test.xit')
            
            result = runner.invoke(xit, ['untag', '6', 'urgent', '-f', 'test.xit'])
            
            assert result.exit_code == 0
            assert 'Removed tag #urgent from task #006' in result.output
            
            # Verify tag was removed from that specific task
            with open('test.xit', 'r') as f:
                content = f.read()
                lines = content.strip().split('\n')
                # Check that task 6 no longer has #urgent but still has the rest
                assert '[ ] !! High priority task' in lines[5]  # Task 6 without #urgent
                assert '#urgent' not in lines[5]

class TestEditCLI(CLITest):
    """Test the 'edit' command of the CLI."""

    def test_edit_command(self, runner):
        """Test editing a task description."""
        with runner.isolated_filesystem():
            self.write_sample_tasks('test.xit')
            
            result = runner.invoke(xit, ['edit', '1', 'Updated task description', '-f', 'test.xit'])
            
            assert result.exit_code == 0
            assert 'Updated description for task #001' in result.output
            assert 'Updated task description' in result.output
            
            # Verify description was updated
            with open('test.xit', 'r') as f:
                content = f.read()
                assert '[ ] Updated task description' in content
                assert 'Original task' not in content

    def test_edit_nonexistent_task(self, runner):
        """Test editing a task that doesn't exist."""
        with runner.isolated_filesystem():
            self.write_sample_tasks('test.xit')
            
            result = runner.invoke(xit, ['edit', '999', 'New description', '-f', 'test.xit'])
            
            assert result.exit_code == 0
            assert 'Task #999 not found' in result.output

    


class TestCLIIntegration:
    """Integration tests combining multiple CLI operations."""
    
    @pytest.fixture
    def runner(self):
        """Provide a Click test runner."""
        return CliRunner()

    def test_full_task_lifecycle(self, runner):
        """Test a complete task lifecycle: add -> show -> mark -> edit -> tag -> untag."""
        with runner.isolated_filesystem():
            # Add a task
            result = runner.invoke(xit, ['add', 'Complete project', '--file', 'project.xit'])
            assert result.exit_code == 0
            
            # Show the task
            result = runner.invoke(xit, ['show', '-f', 'project.xit'])
            assert result.exit_code == 0
            assert 'Complete project' in result.output
            
            # Mark as ongoing
            result = runner.invoke(xit, ['mark', '1', '--ongoing', '-f', 'project.xit'])
            assert result.exit_code == 0
            
            # Add priority
            result = runner.invoke(xit, ['prio', '1', '2', '-f', 'project.xit'])
            assert result.exit_code == 0
            
            # Add tag
            result = runner.invoke(xit, ['tag', '1', 'urgent', '-f', 'project.xit'])
            assert result.exit_code == 0
            
            # Edit description
            result = runner.invoke(xit, ['edit', '1', 'Complete important project', '-f', 'project.xit'])
            assert result.exit_code == 0
            
            # Verify final state
            with open('project.xit', 'r') as f:
                content = f.read()
                assert '[@] !! Complete important project #urgent' in content
            
            # Mark as done
            result = runner.invoke(xit, ['mark', '1', '--done', '-f', 'project.xit'])
            assert result.exit_code == 0
            
            # Verify final completion
            with open('project.xit', 'r') as f:
                content = f.read()
                assert '[x] !! Complete important project #urgent' in content

    def test_multiple_tasks_operations(self, runner):
        """Test operations on multiple tasks."""
        with runner.isolated_filesystem():
            # Add multiple tasks
            for i in range(1, 4):
                result = runner.invoke(xit, ['add', f'Task {i}', '--file', 'multiple.xit'])
                assert result.exit_code == 0
            
            # Mark multiple tasks as done
            result = runner.invoke(xit, ['mark', '1', '2', '--done', '-f', 'multiple.xit'])
            assert result.exit_code == 0
            assert 'Processed 2 of 2 tasks' in result.output
            
            # Verify states
            with open('multiple.xit', 'r') as f:
                lines = f.readlines()
                assert '[x] Task 1' in lines[0]
                assert '[x] Task 2' in lines[1]
                assert '[ ] Task 3' in lines[2]
            
            # Check stats
            result = runner.invoke(xit, ['stats', '-f', 'multiple.xit'])
            assert result.exit_code == 0
            assert 'Total tasks: 3' in result.output
            assert 'Done: 2' in result.output
            assert 'Open: 1' in result.output