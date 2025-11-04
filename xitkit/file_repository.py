"""
File Repository - Centralized file management for xitkit.

This module provides a singleton repository that manages parsed File objects,
eliminating redundant parsing and providing a consistent interface for file operations.
"""

from pathlib import Path
from typing import Dict, Optional, List
import xitkit.fileparser as fp 
import xitkit.task as task


class FileRepository:
    """Singleton repository for managing parsed File objects."""
    
    _instance: Optional['FileRepository'] = None
    _files: Dict[str, fp.File] = {}
    _parser: fp.FileParser = None
    _current_id: int = 1
    _tasks: Dict[int, task.Task] = {}
    
    def __new__(cls) -> 'FileRepository':
        """Ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._parser = fp.FileParser()
        return cls._instance
    
    def get_file(self, file_path: str) -> fp.File:
        """
        Get a File object for the given path, loading it if necessary.
        Assigns sequential IDs to tasks within the file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File object for the path with tasks having assigned IDs
        """
        # Normalize path to handle relative paths consistently
        normalized_path = str(Path(file_path).resolve())
        
        if normalized_path not in self._files:
            file_obj = self._parser.parse_file(normalized_path)
            self._files[normalized_path] = file_obj
        
        return self._files[normalized_path]
    
    def assign_id(self) -> None:
        """
        Return the next unique task ID and increment the internal counter.
        """
        task_id = self._current_id
        self._current_id += 1
        return task_id

    def reload_file(self, file_path: str) -> fp.File:
        """
        Force reload a file from disk, discarding any cached version.
        Assigns sequential IDs to tasks within the file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Newly loaded File object with tasks having assigned IDs
        """
        normalized_path = str(Path(file_path).resolve())
        file_obj = self._parser.parse_file(normalized_path)
        # Assign sequential IDs to tasks in this file
        self._assign_task_ids(file_obj)
        self._files[normalized_path] = file_obj
        return self._files[normalized_path]
    
    def save_file(self, file_path: str) -> None:
        """
        Save a file to disk if it's been loaded.
        
        Args:
            file_path: Path to the file to save
        """
        normalized_path = str(Path(file_path).resolve())
        if normalized_path in self._files:
            self._files[normalized_path].write()
    
    def save_all(self) -> None:
        """Save all loaded files to disk."""
        for file_obj in self._files.values():
            file_obj.write()
    
    def reset(self) -> None:
        """Clear all cached files, tasks, and reset ID counter."""
        self._files.clear()
        self._tasks.clear()
        self._current_id = 1

    def is_loaded(self, file_path: str) -> bool:
        """
        Check if a file is currently loaded in the repository.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file is loaded, False otherwise
        """
        normalized_path = str(Path(file_path).resolve())
        return normalized_path in self._files
    
    def get_loaded_files(self) -> List[str]:
        """
        Get list of all currently loaded file paths.
        
        Returns:
            List of file paths that are currently loaded
        """
        return list(self._files.keys())
    
    def update_task(self, task: task.Task) -> bool:
        """
        Update a task in its file using ID-based matching.
        
        Args:
            task: task.Task object to update
            
        Returns:
            True if task was found and updated, False otherwise
        """
        # get the according file and rewrite
        file = self.get_file(task.location.file_path)
        
        # make sure the task is in the file, add if necessary
        if not task in file.get_tasks():
            file.add_task(task)
        file.write()
        return True

    def unlink_task(self, task: task.Task) -> bool:
        """
        Unlink a task from its file without deleting it.

        Args:
            task: task.Task object to unlink

        Returns:
            True if task was unlinked successfully, False otherwise
        """
        file = self.get_file(task.location.file_path)
        if file:
            file.remove_task(task)
            return True
        return False

    def add_task_to_file(self, task: task.Task, file_path: str, section_name: Optional[str] = None) -> bool:
        """
        Add a task to a file, optionally in a specific section.
        
        Args:
            task: task.Task to add
            file_path: Path to the file
            section_name: Optional section name (defaults to "To Do")
            
        Returns:
            True if task was added successfully, False otherwise
        """
        file_obj = self.get_file(file_path)
        
        # Ensure we have a section to add to
        if section_name is None:
            section_name = "To Do"
        
        # Get or create the section
        if section_name not in file_obj.sections:
            # If no sections exist, ensure default section
            file_obj.ensure_default_section()
        
        section = file_obj.sections.get(section_name)
        if section:
            section.add_task(task)
            return True
        
        return False