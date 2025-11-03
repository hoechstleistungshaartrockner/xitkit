"""
File Repository - Centralized file management for xitkit.

This module provides a singleton repository that manages parsed File objects,
eliminating redundant parsing and providing a consistent interface for file operations.
"""

from pathlib import Path
from typing import Dict, Optional, List
from .fileparser import FileParser, File
from .task import Task


class FileRepository:
    """Singleton repository for managing parsed File objects."""
    
    _instance: Optional['FileRepository'] = None
    _files: Dict[str, File] = {}
    _parser: FileParser = None
    
    def __new__(cls) -> 'FileRepository':
        """Ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._parser = FileParser()
        return cls._instance
    
    def get_file(self, file_path: str) -> File:
        """
        Get a File object for the given path, loading it if necessary.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File object for the path
        """
        # Normalize path to handle relative paths consistently
        normalized_path = str(Path(file_path).resolve())
        
        if normalized_path not in self._files:
            self._files[normalized_path] = self._parser.parse_file(normalized_path)
        
        return self._files[normalized_path]
    
    def reload_file(self, file_path: str) -> File:
        """
        Force reload a file from disk, discarding any cached version.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Newly loaded File object
        """
        normalized_path = str(Path(file_path).resolve())
        self._files[normalized_path] = self._parser.parse_file(normalized_path)
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
    
    def clear_cache(self) -> None:
        """Clear all cached files."""
        self._files.clear()
    
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
    
    def find_task_by_content(self, file_path: str, description_text: str, section_name: Optional[str] = None) -> Optional[Task]:
        """
        Find a task by its description content within a file.
        
        Args:
            file_path: Path to the file containing the task
            description_text: Description text to match
            section_name: Optional section name to narrow search
            
        Returns:
            Task object if found, None otherwise
        """
        file_obj = self.get_file(file_path)
        
        # Search in specific section if provided, otherwise search all sections
        sections_to_search = [file_obj.sections[section_name]] if section_name and section_name in file_obj.sections else file_obj.sections.values()
        
        for section in sections_to_search:
            for task in section.tasks:
                if str(task.description) == description_text:
                    return task
        
        return None
    
    def update_task_by_content(self, file_path: str, old_description: str, updated_task: Task, section_name: Optional[str] = None) -> bool:
        """
        Update a task by finding it via description content.
        
        Args:
            file_path: Path to the file containing the task
            old_description: Original description text to find the task
            updated_task: Updated task object to replace with
            section_name: Optional section name to narrow search
            
        Returns:
            True if task was found and updated, False otherwise
        """
        file_obj = self.get_file(file_path)
        
        # Search in specific section if provided, otherwise search all sections  
        sections_to_search = [file_obj.sections[section_name]] if section_name and section_name in file_obj.sections else file_obj.sections.values()
        
        for section in sections_to_search:
            for i, task in enumerate(section.tasks):
                if str(task.description) == old_description:
                    section.tasks[i] = updated_task
                    return True
        
        return False
    
    def remove_task_by_content(self, file_path: str, description_text: str, section_name: Optional[str] = None) -> bool:
        """
        Remove a task by finding it via description content.
        
        Args:
            file_path: Path to the file containing the task
            description_text: Description text to match
            section_name: Optional section name to narrow search
            
        Returns:
            True if task was found and removed, False otherwise
        """
        file_obj = self.get_file(file_path)
        
        # Search in specific section if provided, otherwise search all sections
        sections_to_search = [file_obj.sections[section_name]] if section_name and section_name in file_obj.sections else file_obj.sections.values()
        
        for section in sections_to_search:
            for task in section.tasks:
                if str(task.description) == description_text:
                    file_obj.remove_task(task)
                    return True
        
        return False
    
    def update_task_by_identity(self, old_task: Task, new_task: Task) -> bool:
        """
        Update a task by finding the old task and replacing it with the new one.
        
        Args:
            old_task: Original task to find and replace
            new_task: New task to replace with
            
        Returns:
            True if task was found and updated, False otherwise
        """
        file_path = old_task.location.file_path
        section_name = getattr(old_task.location, 'section', None)
        
        return self.update_task_by_content(
            file_path=file_path,
            old_description=str(old_task.description),
            updated_task=new_task,
            section_name=section_name
        )
    
    def update_task(self, task: Task) -> bool:
        """
        Update a task in its file. Uses content matching.
        
        Args:
            task: Task object to update
            
        Returns:
            True if task was found and updated, False otherwise
        """
        # For now, assume the task description hasn't changed fundamentally
        # This is a limitation - we'd need to track original description for full support
        file_path = task.location.file_path
        section_name = getattr(task.location, 'section', None)
        
        # Try to find a task with the same base description (without status/priority markers)
        file_obj = self.get_file(file_path)
        
        sections_to_search = [file_obj.sections[section_name]] if section_name and section_name in file_obj.sections else file_obj.sections.values()
        
        for section in sections_to_search:
            for i, file_task in enumerate(section.tasks):
                # Compare the base description text (this is imperfect but works for most cases)
                task_base = str(task.description).strip()
                file_task_base = str(file_task.description).strip()
                
                # Remove priority indicators for comparison
                import re
                task_base = re.sub(r'^[!.]+\s*', '', task_base)
                file_task_base = re.sub(r'^[!.]+\s*', '', file_task_base)
                
                if task_base == file_task_base:
                    section.tasks[i] = task
                    return True
        
        return False
    
    def remove_task(self, task: Task) -> bool:
        """
        Remove a task from its file using content-based matching.
        
        Args:
            task: Task object to remove
            
        Returns:
            True if task was found and removed, False otherwise
        """
        file_path = task.location.file_path
        section_name = getattr(task.location, 'section', None)
        
        return self.remove_task_by_content(
            file_path=file_path,
            description_text=str(task.description),
            section_name=section_name
        )
    
    def add_task_to_file(self, task: Task, file_path: str, section_name: Optional[str] = None) -> bool:
        """
        Add a task to a file, optionally in a specific section.
        
        Args:
            task: Task to add
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


# Convenience function to get the singleton instance
def get_file_repository() -> FileRepository:
    """Get the FileRepository singleton instance."""
    return FileRepository()