"""Core service classes for task management operations.

This module provides high-level services that orchestrate the various components
of the task management system, separating business logic from CLI concerns.
"""

from typing import List, Optional, Dict, Any
from pathlib import Path
from dataclasses import dataclass

from .fileparser import FileParser
from .task import Task
from .dateutils import DateParser
from .config import get_config
from .exceptions import FileNotSupportedError, TaskFilterError


@dataclass
class TaskFilter:
    """Configuration for filtering tasks."""
    status: Optional[str] = None
    priority: Optional[int] = None
    tags: Optional[List[str]] = None
    due_on: Optional[str] = None
    due_by: Optional[str] = None


class TaskService:
    """High-level service for task operations.
    
    This service orchestrates parsing, filtering, and data operations
    while keeping the CLI layer focused on user interaction.
    """
    
    def __init__(self):
        """Initialize the task service."""
        self.parser = FileParser()
        self.date_parser = DateParser()
    
    def find_task_files(self, directory: Path = None) -> List[str]:
        """Find all .md and .xit files in the specified directory.
        
        Args:
            directory: Directory to search (defaults to current directory)
            
        Returns:
            List of task file paths
        """
        if directory is None:
            directory = Path.cwd()
        
        task_files = []
        for pattern in ['**/*.xit', '**/*.md']:
            task_files.extend(str(p) for p in directory.glob(pattern))
        
        return sorted(task_files)
    
    def load_tasks(self, file_paths: List[str]) -> List[Task]:
        """Load tasks from the specified files.
        
        Files are processed in alphabetical order, and tasks are assigned
        sequential IDs starting from 1.
        
        Args:
            file_paths: List of file paths to parse
            
        Returns:
            List of parsed tasks with assigned IDs
            
        Raises:
            FileNotFoundError: If a file doesn't exist
            ValueError: If a file has an unsupported format
        """
        # Sort file paths alphabetically to ensure consistent ID assignment
        sorted_file_paths = sorted(file_paths)
        
        # Parse all tasks from all files
        all_tasks = self.parser.parse_files(sorted_file_paths)
        
        # Assign sequential IDs starting from 1
        for i, task in enumerate(all_tasks, start=1):
            task.id = i
        
        return all_tasks
    
    def filter_tasks(self, tasks: List[Task], filters: TaskFilter) -> List[Task]:
        """Apply filters to a list of tasks.
        
        Args:
            tasks: List of tasks to filter
            filters: Filter configuration
            
        Returns:
            Filtered list of tasks
        """
        filtered = tasks.copy()
        
        # Apply status filter
        if filters.status:
            status_upper = filters.status.upper()
            filtered = [t for t in filtered if t.status == status_upper]
        
        # Apply priority filter
        if filters.priority is not None:
            filtered = [t for t in filtered if t.priority >= filters.priority]
        
        # Apply tag filters
        if filters.tags:
            normalized_tags = self._normalize_tags(filters.tags)
            filtered = [t for t in filtered if self._has_all_tags(t.tags, normalized_tags)]
        
        # Apply date filters
        if filters.due_on:
            filtered = [t for t in filtered if self.date_parser.matches_date_filter_on(t.due_date, filters.due_on)]
        
        if filters.due_by:
            filtered = [t for t in filtered if self.date_parser.matches_date_filter_by(t.due_date, filters.due_by)]
        
        return filtered
    
    def _normalize_tags(self, tags: List[str]) -> List[str]:
        """Normalize tag list to include # prefix."""
        normalized = []
        for tag in tags:
            if not tag.startswith('#'):
                normalized.append(f'#{tag}')
            else:
                normalized.append(tag)
        return normalized
    
    def _has_all_tags(self, task_tags: List[str], required_tags: List[str]) -> bool:
        """Check if task has all required tags."""
        task_tag_names = []
        for task_tag in task_tags:
            if '=' in task_tag:
                task_tag_names.append(task_tag.split('=')[0])
            else:
                task_tag_names.append(task_tag)
        
        return all(req_tag in task_tag_names for req_tag in required_tags)
    
    def get_task_statistics(self, tasks: List[Task]) -> Dict[str, Any]:
        """Calculate statistics for a list of tasks.
        
        Args:
            tasks: List of tasks to analyze
            
        Returns:
            Dictionary containing various statistics
        """
        stats = {
            'total_tasks': len(tasks),
            'status_counts': {},
            'priority_counts': {},
            'files_with_tasks': set(),
            'tasks_with_due_dates': 0,
            'tasks_with_tags': 0
        }
        
        for task in tasks:
            # Count by status
            stats['status_counts'][task.status] = stats['status_counts'].get(task.status, 0) + 1
            
            # Count by priority
            stats['priority_counts'][task.priority] = stats['priority_counts'].get(task.priority, 0) + 1
            
            # Track files
            stats['files_with_tasks'].add(task.file)
            
            # Count tasks with due dates and tags
            if task.due_date:
                stats['tasks_with_due_dates'] += 1
            if task.tags:
                stats['tasks_with_tags'] += 1
        
        return stats
    
    def add_task_to_file(self, description: str, file_path: str) -> None:
        """Add a new task to the specified file.
        
        Args:
            description: The task description text
            file_path: Path to the file where task should be added
            
        Raises:
            FileNotSupportedError: If file extension is not supported
        """
        file_path_obj = Path(file_path)
        
        # Validate file extension
        if file_path_obj.suffix not in ['.md', '.xit']:
            raise FileNotSupportedError(file_path, {'.md', '.xit'})
        
        # Create directory if it doesn't exist
        file_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        # Format the task line (always create as open task)
        task_line = f"[ ] {description}\n"
        
        # Check if file exists and has content
        file_exists = file_path_obj.exists()
        needs_newline = False
        
        if file_exists and file_path_obj.stat().st_size > 0:
            # Check if file ends with newline
            with open(file_path, 'rb') as f:
                f.seek(-1, 2)  # Go to last byte
                last_char = f.read(1)
                needs_newline = last_char != b'\n'
        
        # Append the task to the file
        with open(file_path, 'a', encoding='utf-8') as f:
            if needs_newline:
                f.write('\n')
            f.write(task_line)
    
    def mark_task_by_id(self, task_id: int, new_status: str, file_paths: List[str]) -> Optional[Task]:
        """Find and update a task's status by its ID.
        
        Args:
            task_id: The ID of the task to update
            new_status: The new status to set
            file_paths: List of file paths to search
            
        Returns:
            The updated Task object if found, None otherwise
            
        Raises:
            ValueError: If the new status is invalid
        """
        from .task import Task
        
        # Validate status
        if new_status not in Task._VALID_STATUSES:
            raise ValueError(f"Invalid status: {new_status}. Must be one of {Task._VALID_STATUSES}")
        
        # Load all tasks and assign IDs
        all_tasks = self.load_tasks(file_paths)
        
        # Find the task with the matching ID
        target_task = None
        for task in all_tasks:
            if task.id == task_id:
                target_task = task
                break
        
        if not target_task:
            return None
        
        # Update the task in the file
        self._update_task_in_file(target_task, new_status)
        
        # Update the task object and return it
        target_task.status = new_status
        return target_task
    
    def _update_task_in_file(self, task: Task, new_status: str) -> None:
        """Update a task's status in its source file.
        
        Args:
            task: The task to update
            new_status: The new status to set
        """
        # Map status to the character used in files
        status_char_map = {
            'OPEN': ' ',
            'DONE': 'x',
            'ONGOING': '@',
            'OBSOLETE': '~',
            'INQUESTION': '?'
        }
        
        new_char = status_char_map[new_status]
        
        # Read the entire file
        with open(task.file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Update the specific line (convert to 0-based index)
        line_index = task.line_number - 1
        if 0 <= line_index < len(lines):
            original_line = lines[line_index].rstrip('\n\r')
            
            # Simple approach: if line starts with [ and has ] as third character, update
            if len(original_line) >= 3 and original_line.startswith('[') and original_line[2] == ']':
                # Replace the status character (at index 1)
                updated_line = f"[{new_char}]{original_line[3:]}\n"
                lines[line_index] = updated_line
                
                # Write the file back
                with open(task.file, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
    
    def reschedule_task_by_id(self, task_id: int, new_date: str, file_paths: List[str]) -> Optional[Task]:
        """Find and update a task's due date by its ID.
        
        Args:
            task_id: The ID of the task to update
            new_date: The new due date string
            file_paths: List of file paths to search
            
        Returns:
            The updated Task object if found, None otherwise
        """
        from .task import Task
        
        # Load all tasks and assign IDs
        all_tasks = self.load_tasks(file_paths)
        
        # Find the task with the matching ID
        target_task = None
        for task in all_tasks:
            if task.id == task_id:
                target_task = task
                break
        
        if not target_task:
            return None
        
        # Update the task in the file
        self._update_due_date_in_file(target_task, new_date)
        
        # Update the task object and return it
        target_task.due_date = new_date
        return target_task
    
    def _update_due_date_in_file(self, task: Task, new_date: str) -> None:
        """Update a task's due date in its source file.
        
        Args:
            task: The task to update
            new_date: The new due date to set
        """
        # Read the entire file
        with open(task.file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Update the specific line (convert to 0-based index)
        line_index = task.line_number - 1
        if 0 <= line_index < len(lines):
            original_line = lines[line_index].rstrip('\n\r')
            
            # Parse the line to update or add due date
            import re
            
            # Pattern to match existing due dates
            due_date_pattern = r'->\s*\d{4}(?:[-/](?:W\d{2}|Q[1-4]|\d{1,2}(?:[-/]\d{1,2})?))?'
            
            # Pattern to match "-> None" or similar invalid dates  
            invalid_date_pattern = r'->\s*None'
            
            # Remove any invalid dates first
            cleaned_line = re.sub(invalid_date_pattern, '', original_line).strip()
            
            if re.search(due_date_pattern, cleaned_line):
                # Replace only the first valid due date occurrence
                updated_line = re.sub(due_date_pattern, f'-> {new_date}', cleaned_line, count=1) + '\n'
            else:
                # Add new due date at the end of the line
                updated_line = f"{cleaned_line} -> {new_date}\n"
            
            lines[line_index] = updated_line
            
            # Write the file back
            with open(task.file, 'w', encoding='utf-8') as f:
                f.writelines(lines)

    def remove_task_by_id(self, task_id: int, file_paths: List[str]) -> Optional[Task]:
        """Remove a task by its ID from the files.
        
        Args:
            task_id: The ID of the task to remove
            file_paths: List of file paths to search
            
        Returns:
            The removed Task object if found, None otherwise
        """
        # Load all tasks and assign IDs
        all_tasks = self.load_tasks(file_paths)
        
        # Find the task with the matching ID
        target_task = None
        for task in all_tasks:
            if task.id == task_id:
                target_task = task
                break
        
        if not target_task:
            return None
        
        # Remove the task from its file
        self._remove_task_from_file(target_task)
        
        return target_task
    
    def _remove_task_from_file(self, task: Task) -> None:
        """Remove a task from its source file.
        
        Args:
            task: The task to remove
        """
        # Read the entire file
        with open(task.file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Remove the task line and any continuation lines
        line_index = task.line_number - 1  # Convert to 0-based
        
        if 0 <= line_index < len(lines):
            # Remove the main task line
            del lines[line_index]
            
            # Remove any continuation lines that follow (lines starting with 4 spaces)
            while (line_index < len(lines) and 
                   lines[line_index].startswith('    ') and 
                   lines[line_index].strip()):
                del lines[line_index]
        
        # Write the file back
        with open(task.file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
    
    def move_task_by_id(self, task_id: int, source_files: List[str], target_file: str) -> Optional[Task]:
        """Move a task by its ID from source files to a target file.
        
        Args:
            task_id: The ID of the task to move
            source_files: List of source file paths to search
            target_file: Path to the target file
            
        Returns:
            The moved Task object if found, None otherwise
            
        Raises:
            FileNotSupportedError: If target file extension is not supported
        """
        from pathlib import Path
        
        # Validate target file extension
        target_path = Path(target_file)
        if target_path.suffix not in ['.md', '.xit']:
            from .exceptions import FileNotSupportedError
            raise FileNotSupportedError(target_file, {'.md', '.xit'})
        
        # Load all tasks and assign IDs
        all_tasks = self.load_tasks(source_files)
        
        # Find the task with the matching ID
        target_task = None
        for task in all_tasks:
            if task.id == task_id:
                target_task = task
                break
        
        if not target_task:
            return None
        
        # Get the original task description (including due date, priority, etc.)
        original_description = self._extract_task_description(target_task)
        
        # Add the task to the target file
        self.add_task_to_file(original_description, target_file)
        
        # Remove the task from the source file
        self._remove_task_from_file(target_task)
        
        # Update task file path for return
        target_task.file = str(target_path)
        
        return target_task
    
    def _extract_task_description(self, task: Task) -> str:
        """Extract the complete task description including priority, tags, and due date.
        
        Args:
            task: The task to extract description from
            
        Returns:
            Complete task description string
        """
        # Read the task line from file to preserve original formatting
        with open(task.file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        line_index = task.line_number - 1
        if 0 <= line_index < len(lines):
            task_line = lines[line_index].strip()
            
            # Remove the checkbox part [x] or [ ] etc.
            import re
            checkbox_match = re.match(r'^\[.\]\s*(.*)', task_line)
            if checkbox_match:
                return checkbox_match.group(1)
            else:
                return task_line
        
        # Fallback to constructing from task properties
        description = task.description
        if task.due_date and task.due_date != "None":
            description += f" -> {task.due_date}"
        
        return description


class FileDiscoveryService:
    """Service for discovering and validating task files."""
    
    SUPPORTED_EXTENSIONS = {'.md', '.xit'}
    
    def resolve_file_paths(self, path: Optional[str], directory: Optional[Path], 
                          specified_files: Optional[List[str]]) -> List[str]:
        """Resolve file paths based on various input options.
        
        Args:
            path: Optional path argument
            directory: Default directory to search
            specified_files: Explicitly specified files
            
        Returns:
            List of resolved file paths
            
        Raises:
            FileNotFoundError: If path doesn't exist
            ValueError: If file type is not supported
        """
        if path:
            return self._resolve_path_argument(path)
        elif specified_files:
            return list(specified_files)
        else:
            service = TaskService()
            return service.find_task_files(directory)
    
    def _resolve_path_argument(self, path: str) -> List[str]:
        """Resolve a single path argument to a list of files."""
        path_obj = Path(path)
        
        if not path_obj.exists():
            raise FileNotFoundError(f"Path '{path}' does not exist.")
        
        if path_obj.is_file():
            if path_obj.suffix not in self.SUPPORTED_EXTENSIONS:
                raise ValueError(f"File '{path}' is not a supported file type. "
                               f"Supported: {', '.join(self.SUPPORTED_EXTENSIONS)}")
            return [str(path_obj)]
        elif path_obj.is_dir():
            service = TaskService()
            return service.find_task_files(path_obj)
        else:
            raise ValueError(f"Path '{path}' is neither a file nor a directory.")