#!/usr/bin/env python3
"""
Script to generate API documentation from Python docstrings.
"""

import os
import inspect
import importlib
from pathlib import Path
from typing import List, Dict, Any

def extract_module_info(module_path: str) -> Dict[str, Any]:
    """Extract documentation from a Python module."""
    try:
        spec = importlib.util.spec_from_file_location("module", module_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            info = {
                "name": module.__name__ if hasattr(module, '__name__') else Path(module_path).stem,
                "doc": module.__doc__ or "",
                "classes": [],
                "functions": []
            }
            
            for name, obj in inspect.getmembers(module):
                if name.startswith('_'):
                    continue
                    
                if inspect.isclass(obj) and obj.__module__ == module.__name__:
                    class_info = {
                        "name": name,
                        "doc": obj.__doc__ or "",
                        "methods": []
                    }
                    
                    for method_name, method in inspect.getmembers(obj, inspect.ismethod):
                        if not method_name.startswith('_'):
                            class_info["methods"].append({
                                "name": method_name,
                                "doc": method.__doc__ or "",
                                "signature": str(inspect.signature(method))
                            })
                    
                    info["classes"].append(class_info)
                
                elif inspect.isfunction(obj) and obj.__module__ == module.__name__:
                    info["functions"].append({
                        "name": name,
                        "doc": obj.__doc__ or "",
                        "signature": str(inspect.signature(obj))
                    })
            
            return info
    except Exception as e:
        print(f"Error processing {module_path}: {e}")
        return None

def generate_markdown_for_module(module_info: Dict[str, Any]) -> str:
    """Generate markdown documentation for a module."""
    if not module_info:
        return ""
    
    md = f"# {module_info['name']}\n\n"
    
    if module_info['doc']:
        md += f"{module_info['doc']}\n\n"
    
    # Classes
    if module_info['classes']:
        md += "## Classes\n\n"
        for cls in module_info['classes']:
            md += f"### {cls['name']}\n\n"
            if cls['doc']:
                md += f"{cls['doc']}\n\n"
            
            if cls['methods']:
                md += "#### Methods\n\n"
                for method in cls['methods']:
                    md += f"##### {method['name']}{method['signature']}\n\n"
                    if method['doc']:
                        md += f"{method['doc']}\n\n"
    
    # Functions
    if module_info['functions']:
        md += "## Functions\n\n"
        for func in module_info['functions']:
            md += f"### {func['name']}{func['signature']}\n\n"
            if func['doc']:
                md += f"{func['doc']}\n\n"
    
    return md

def main():
    """Generate API documentation for the MetaMCP project."""
    project_root = Path(__file__).parent.parent
    metamcp_dir = project_root / "metamcp"
    docs_api_dir = project_root / "docs" / "api"
    
    # Create docs/api directory if it doesn't exist
    docs_api_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate index file
    index_content = """# API Reference

This section contains the complete API reference for MetaMCP.

## Modules

"""
    
    generated_files = []
    
    # Process each Python file in metamcp/
    for py_file in metamcp_dir.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue
            
        relative_path = py_file.relative_to(metamcp_dir)
        module_name = str(relative_path.with_suffix("")).replace("/", ".")
        
        module_info = extract_module_info(str(py_file))
        if module_info:
            # Generate markdown file
            md_content = generate_markdown_for_module(module_info)
            
            # Create subdirectories if needed
            md_file_path = docs_api_dir / relative_path.with_suffix(".md")
            md_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(md_file_path, "w") as f:
                f.write(md_content)
            
            generated_files.append((module_name, relative_path.with_suffix(".md")))
            print(f"Generated documentation for {module_name}")
    
    # Update index file
    for module_name, file_path in sorted(generated_files):
        index_content += f"- [{module_name}]({file_path})\n"
    
    with open(docs_api_dir / "index.md", "w") as f:
        f.write(index_content)
    
    print(f"Generated API documentation for {len(generated_files)} modules")

if __name__ == "__main__":
    main()