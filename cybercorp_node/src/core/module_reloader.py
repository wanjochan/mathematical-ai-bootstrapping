"""
Module dynamic reloading utility for hot-reload functionality
Safely reloads Python modules and updates references
"""

import sys
import importlib
import logging
import types
import inspect
from typing import Dict, Set, Optional, Any, List
from pathlib import Path

logger = logging.getLogger('ModuleReloader')

class ModuleReloader:
    """Handles dynamic module reloading"""
    
    def __init__(self):
        """Initialize module reloader"""
        self.reloadable_modules: Set[str] = set()
        self.module_dependencies: Dict[str, Set[str]] = {}
        self.protected_modules: Set[str] = {
            'sys', 'os', 'asyncio', 'websockets', 'logging',
            'importlib', 'types', 'inspect', '__main__'
        }
        
    def add_reloadable_module(self, module_name: str):
        """Mark a module as reloadable"""
        if module_name not in self.protected_modules:
            self.reloadable_modules.add(module_name)
            logger.info(f"Added reloadable module: {module_name}")
    
    def remove_reloadable_module(self, module_name: str):
        """Remove module from reloadable list"""
        self.reloadable_modules.discard(module_name)
        logger.info(f"Removed reloadable module: {module_name}")
    
    def _get_module_from_path(self, file_path: str) -> Optional[str]:
        """Get module name from file path"""
        try:
            path = Path(file_path)
            
            # Find the module name by checking sys.modules
            for name, module in sys.modules.items():
                if hasattr(module, '__file__') and module.__file__:
                    module_path = Path(module.__file__).resolve()
                    if module_path == path.resolve():
                        return name
            
            # Try to construct module name from path
            # This is a fallback for modules not yet loaded
            if path.suffix == '.py':
                # Find the nearest __init__.py to determine package root
                parts = []
                current = path.parent
                
                while current.parent != current:
                    if (current / '__init__.py').exists():
                        parts.append(current.name)
                        current = current.parent
                    else:
                        break
                
                parts.reverse()
                parts.append(path.stem)
                return '.'.join(parts)
                
        except Exception as e:
            logger.error(f"Error getting module from path {file_path}: {e}")
        
        return None
    
    def _find_dependent_modules(self, module_name: str) -> Set[str]:
        """Find modules that depend on the given module"""
        dependents = set()
        
        for name, module in sys.modules.items():
            if name == module_name or module is None:
                continue
                
            # Check if module imports the target module
            try:
                if hasattr(module, '__dict__'):
                    for attr_name, attr_value in module.__dict__.items():
                        if isinstance(attr_value, types.ModuleType):
                            if attr_value.__name__ == module_name:
                                dependents.add(name)
                        elif hasattr(attr_value, '__module__'):
                            if attr_value.__module__ == module_name:
                                dependents.add(name)
            except Exception:
                pass
        
        return dependents & self.reloadable_modules
    
    def reload_module(self, module_name: str) -> bool:
        """
        Reload a specific module
        
        Returns:
            True if successful, False otherwise
        """
        if module_name not in sys.modules:
            logger.warning(f"Module not loaded: {module_name}")
            return False
        
        if module_name in self.protected_modules:
            logger.warning(f"Cannot reload protected module: {module_name}")
            return False
        
        try:
            # Get the module
            module = sys.modules[module_name]
            
            # Save references to update later
            old_dict = module.__dict__.copy()
            
            # Reload the module
            logger.info(f"Reloading module: {module_name}")
            importlib.reload(module)
            
            # Update references in dependent modules
            self._update_references(module_name, old_dict, module.__dict__)
            
            logger.info(f"Successfully reloaded: {module_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error reloading module {module_name}: {e}")
            return False
    
    def _update_references(self, module_name: str, old_dict: dict, new_dict: dict):
        """Update references to reloaded module objects"""
        # Find objects that were replaced
        updated_objects = {}
        
        for name, old_obj in old_dict.items():
            if name in new_dict and old_obj is not new_dict[name]:
                if callable(old_obj) or isinstance(old_obj, type):
                    updated_objects[name] = (old_obj, new_dict[name])
        
        if not updated_objects:
            return
        
        # Update references in dependent modules
        dependents = self._find_dependent_modules(module_name)
        
        for dependent_name in dependents:
            if dependent_name not in sys.modules:
                continue
                
            dependent = sys.modules[dependent_name]
            
            try:
                # Update direct imports
                for attr_name in dir(dependent):
                    attr = getattr(dependent, attr_name)
                    
                    for obj_name, (old_obj, new_obj) in updated_objects.items():
                        if attr is old_obj:
                            setattr(dependent, attr_name, new_obj)
                            logger.debug(f"Updated {dependent_name}.{attr_name}")
                            
            except Exception as e:
                logger.error(f"Error updating references in {dependent_name}: {e}")
    
    def reload_from_path(self, file_path: str) -> bool:
        """Reload module from file path"""
        module_name = self._get_module_from_path(file_path)
        
        if not module_name:
            logger.warning(f"Could not determine module name for: {file_path}")
            return False
        
        return self.reload_module(module_name)
    
    def reload_all(self) -> Dict[str, bool]:
        """
        Reload all reloadable modules
        
        Returns:
            Dict of module_name -> success status
        """
        results = {}
        
        # Sort modules by dependency order (simple approach)
        modules_to_reload = list(self.reloadable_modules & set(sys.modules.keys()))
        
        for module_name in modules_to_reload:
            results[module_name] = self.reload_module(module_name)
        
        return results
    
    def get_reloadable_modules(self) -> List[str]:
        """Get list of modules marked as reloadable"""
        return sorted(self.reloadable_modules)
    
    def get_loaded_modules(self) -> List[str]:
        """Get list of currently loaded modules"""
        return sorted([
            name for name in sys.modules.keys()
            if name not in self.protected_modules
        ])