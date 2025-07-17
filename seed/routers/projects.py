"""
Project Management API routes for CyberCorp Seed Server
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import os
import json
import subprocess
import shutil
import time
import fnmatch
import re
from pathlib import Path
from datetime import datetime
import asyncio

router = APIRouter()

# 项目根目录
PROJECTS_ROOT = Path("projects")
PROJECTS_ROOT.mkdir(exist_ok=True)

# Pydantic模型
class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    template: Optional[str] = "basic"

class FileCreate(BaseModel):
    path: str
    content: str
    encoding: Optional[str] = "utf-8"

class FileUpdate(BaseModel):
    content: str
    encoding: Optional[str] = "utf-8"

class DependencyInstall(BaseModel):
    packages: List[str]
    dev: Optional[bool] = False

class CodeTemplate(BaseModel):
    template_type: str  # 'function', 'class', 'fastapi_route', 'test_case', etc.
    language: str  # 'python', 'javascript', 'typescript', etc.
    name: str
    parameters: Optional[Dict[str, Any]] = {}

class CodeSnippet(BaseModel):
    language: str
    snippet_type: str  # 'import', 'function', 'class', 'decorator', etc.
    content: str
    description: Optional[str] = ""

class FileSearch(BaseModel):
    pattern: str  # 搜索模式
    file_types: Optional[List[str]] = []  # 文件类型过滤 ['.py', '.js']
    include_content: Optional[bool] = False  # 是否搜索文件内容
    max_results: Optional[int] = 100

class BatchFileOperation(BaseModel):
    operation: str  # 'copy', 'move', 'delete'
    files: List[str]  # 文件路径列表
    target_dir: Optional[str] = None  # 目标目录（copy/move时需要）

class DirectoryOperation(BaseModel):
    operation: str  # 'create', 'delete', 'move', 'copy'
    source_path: str
    target_path: Optional[str] = None

# 项目管理API
@router.post("/projects")
async def create_project(project: ProjectCreate) -> Dict[str, Any]:
    """
    创建新项目
    """
    try:
        project_path = PROJECTS_ROOT / project.name
        
        # 检查项目是否已存在
        if project_path.exists():
            raise HTTPException(status_code=400, detail=f"Project '{project.name}' already exists")
        
        # 创建项目目录
        project_path.mkdir(parents=True)
        
        # 创建项目配置文件
        project_config = {
            "name": project.name,
            "description": project.description,
            "template": project.template,
            "created_at": datetime.utcnow().isoformat(),
            "dependencies": []
        }
        
        config_file = project_path / "project.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(project_config, f, indent=2, ensure_ascii=False)
        
        # 根据模板创建初始文件
        if project.template == "python":
            # Python项目模板
            (project_path / "src").mkdir()
            (project_path / "tests").mkdir()
            
            # 创建基础文件
            with open(project_path / "README.md", 'w') as f:
                f.write(f"# {project.name}\n\n{project.description}\n")
            
            with open(project_path / "requirements.txt", 'w') as f:
                f.write("# Project dependencies\n")
            
            with open(project_path / "src" / "__init__.py", 'w') as f:
                f.write("")
                
            with open(project_path / "src" / "main.py", 'w') as f:
                f.write('def main():\n    print("Hello, World!")\n\nif __name__ == "__main__":\n    main()\n')
        
        elif project.template == "fastapi":
            # FastAPI项目模板
            (project_path / "app").mkdir()
            (project_path / "tests").mkdir()
            
            with open(project_path / "README.md", 'w') as f:
                f.write(f"# {project.name}\n\n{project.description}\n\nFastAPI应用\n")
            
            with open(project_path / "requirements.txt", 'w') as f:
                f.write("fastapi>=0.68.0\nuvicorn>=0.15.0\n")
            
            with open(project_path / "app" / "__init__.py", 'w') as f:
                f.write("")
            
            with open(project_path / "app" / "main.py", 'w') as f:
                f.write('from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get("/")\nasync def root():\n    return {"message": "Hello World"}\n')
        
        else:
            # 基础模板
            with open(project_path / "README.md", 'w') as f:
                f.write(f"# {project.name}\n\n{project.description}\n")
        
        return {
            "status": "success",
            "message": f"Project '{project.name}' created successfully",
            "project": {
                "name": project.name,
                "path": str(project_path),
                "template": project.template,
                "created_at": project_config["created_at"]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")

@router.get("/projects")
async def list_projects() -> Dict[str, Any]:
    """
    列出所有项目
    """
    try:
        projects = []
        
        for project_dir in PROJECTS_ROOT.iterdir():
            if project_dir.is_dir():
                config_file = project_dir / "project.json"
                if config_file.exists():
                    with open(config_file, 'r', encoding='utf-8') as f:
                        project_config = json.load(f)
                    projects.append({
                        "name": project_config["name"],
                        "description": project_config.get("description", ""),
                        "template": project_config.get("template", "basic"),
                        "created_at": project_config.get("created_at"),
                        "path": str(project_dir)
                    })
                else:
                    # 没有配置文件的目录
                    projects.append({
                        "name": project_dir.name,
                        "description": "Legacy project without config",
                        "template": "unknown",
                        "created_at": None,
                        "path": str(project_dir)
                    })
        
        return {
            "status": "success",
            "projects": projects,
            "total": len(projects)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list projects: {str(e)}")

@router.delete("/projects/{project_name}")
async def delete_project(project_name: str) -> Dict[str, Any]:
    """
    删除项目
    """
    try:
        project_path = PROJECTS_ROOT / project_name
        
        if not project_path.exists():
            raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found")
        
        # 删除项目目录
        shutil.rmtree(project_path)
        
        return {
            "status": "success",
            "message": f"Project '{project_name}' deleted successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete project: {str(e)}")

# 文件管理API
@router.post("/projects/{project_name}/files")
async def create_file(project_name: str, file_data: FileCreate) -> Dict[str, Any]:
    """
    在项目中创建文件
    """
    try:
        project_path = PROJECTS_ROOT / project_name
        
        if not project_path.exists():
            raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found")
        
        file_path = project_path / file_data.path
        
        # 确保父目录存在
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入文件
        with open(file_path, 'w', encoding=file_data.encoding) as f:
            f.write(file_data.content)
        
        return {
            "status": "success",
            "message": f"File '{file_data.path}' created successfully",
            "file": {
                "path": file_data.path,
                "full_path": str(file_path),
                "size": len(file_data.content.encode(file_data.encoding))
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create file: {str(e)}")

@router.get("/projects/{project_name}/files/{file_path:path}")
async def read_file(project_name: str, file_path: str) -> Dict[str, Any]:
    """
    读取项目文件
    """
    try:
        project_path = PROJECTS_ROOT / project_name
        full_file_path = project_path / file_path
        
        if not project_path.exists():
            raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found")
        
        if not full_file_path.exists():
            raise HTTPException(status_code=404, detail=f"File '{file_path}' not found")
        
        # 读取文件
        try:
            with open(full_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            encoding = 'utf-8'
        except UnicodeDecodeError:
            # 如果UTF-8解码失败，尝试其他编码
            with open(full_file_path, 'rb') as f:
                raw_content = f.read()
            content = raw_content.decode('utf-8', errors='replace')
            encoding = 'binary'
        
        return {
            "status": "success",
            "file": {
                "path": file_path,
                "content": content,
                "encoding": encoding,
                "size": len(content.encode('utf-8'))
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")

@router.put("/projects/{project_name}/files/{file_path:path}")
async def update_file(project_name: str, file_path: str, file_data: FileUpdate) -> Dict[str, Any]:
    """
    更新项目文件
    """
    try:
        project_path = PROJECTS_ROOT / project_name
        full_file_path = project_path / file_path
        
        if not project_path.exists():
            raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found")
        
        # 确保父目录存在
        full_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入文件
        with open(full_file_path, 'w', encoding=file_data.encoding) as f:
            f.write(file_data.content)
        
        return {
            "status": "success",
            "message": f"File '{file_path}' updated successfully",
            "file": {
                "path": file_path,
                "size": len(file_data.content.encode(file_data.encoding))
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update file: {str(e)}")

@router.delete("/projects/{project_name}/files/{file_path:path}")
async def delete_file(project_name: str, file_path: str) -> Dict[str, Any]:
    """
    删除项目文件
    """
    try:
        project_path = PROJECTS_ROOT / project_name
        full_file_path = project_path / file_path
        
        if not project_path.exists():
            raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found")
        
        if not full_file_path.exists():
            raise HTTPException(status_code=404, detail=f"File '{file_path}' not found")
        
        # 删除文件
        full_file_path.unlink()
        
        return {
            "status": "success",
            "message": f"File '{file_path}' deleted successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")

@router.get("/projects/{project_name}/tree")
async def get_file_tree(project_name: str) -> Dict[str, Any]:
    """
    获取项目文件树
    """
    try:
        project_path = PROJECTS_ROOT / project_name
        
        if not project_path.exists():
            raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found")
        
        def build_tree(path: Path, max_depth: int = 5, current_depth: int = 0):
            if current_depth >= max_depth:
                return {"name": path.name, "type": "dir", "truncated": True}
            
            if path.is_file():
                return {
                    "name": path.name,
                    "type": "file",
                    "size": path.stat().st_size
                }
            elif path.is_dir():
                children = []
                try:
                    for child in sorted(path.iterdir()):
                        if child.name.startswith('.'):
                            continue  # 跳过隐藏文件
                        children.append(build_tree(child, max_depth, current_depth + 1))
                except PermissionError:
                    children = [{"name": "Permission denied", "type": "error"}]
                
                return {
                    "name": path.name,
                    "type": "dir",
                    "children": children
                }
        
        tree = build_tree(project_path)
        
        return {
            "status": "success",
            "project": project_name,
            "tree": tree
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get file tree: {str(e)}")

# 依赖管理API
@router.post("/projects/{project_name}/dependencies/install")
async def install_dependencies(
    project_name: str, 
    dependencies: DependencyInstall,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    安装项目依赖
    """
    try:
        project_path = PROJECTS_ROOT / project_name
        
        if not project_path.exists():
            raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found")
        
        # 检查是否为Python项目（存在requirements.txt或setup.py）
        requirements_file = project_path / "requirements.txt"
        is_python_project = requirements_file.exists() or (project_path / "setup.py").exists()
        
        if is_python_project:
            # Python项目，使用pip安装
            cmd = ["pip", "install"] + dependencies.packages
            if dependencies.dev:
                # 开发依赖处理
                cmd.extend(["--upgrade", "--user"])
        else:
            # 检查是否为Node.js项目
            package_json = project_path / "package.json"
            if package_json.exists():
                # Node.js项目，使用npm安装
                cmd = ["npm", "install"] + dependencies.packages
                if dependencies.dev:
                    cmd.append("--save-dev")
            else:
                raise HTTPException(
                    status_code=400, 
                    detail="Unsupported project type. Only Python and Node.js projects are supported."
                )
        
        # 执行安装命令
        result = subprocess.run(
            cmd,
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )
        
        if result.returncode == 0:
            # 更新项目配置
            config_file = project_path / "project.json"
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    project_config = json.load(f)
                
                # 添加到依赖列表
                for package in dependencies.packages:
                    if package not in project_config.get("dependencies", []):
                        project_config.setdefault("dependencies", []).append(package)
                
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(project_config, f, indent=2, ensure_ascii=False)
            
            return {
                "status": "success",
                "message": f"Dependencies installed successfully",
                "packages": dependencies.packages,
                "output": result.stdout
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to install dependencies: {result.stderr}"
            )
        
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Installation timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to install dependencies: {str(e)}")

@router.get("/projects/{project_name}/dependencies")
async def list_dependencies(project_name: str) -> Dict[str, Any]:
    """
    列出项目依赖
    """
    try:
        project_path = PROJECTS_ROOT / project_name
        
        if not project_path.exists():
            raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found")
        
        dependencies = []
        
        # 检查Python依赖
        requirements_file = project_path / "requirements.txt"
        if requirements_file.exists():
            with open(requirements_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        dependencies.append({
                            "name": line.split('==')[0].split('>=')[0].split('<=')[0],
                            "version": line,
                            "type": "python"
                        })
        
        # 检查Node.js依赖
        package_json = project_path / "package.json"
        if package_json.exists():
            with open(package_json, 'r', encoding='utf-8') as f:
                package_data = json.load(f)
            
            for name, version in package_data.get("dependencies", {}).items():
                dependencies.append({
                    "name": name,
                    "version": version,
                    "type": "node"
                })
            
            for name, version in package_data.get("devDependencies", {}).items():
                dependencies.append({
                    "name": name,
                    "version": version,
                    "type": "node-dev"
                })
        
        return {
            "status": "success",
            "project": project_name,
            "dependencies": dependencies,
            "total": len(dependencies)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list dependencies: {str(e)}")

# 代码生成API
@router.post("/code/templates/generate")
async def generate_code_template(template: CodeTemplate) -> Dict[str, Any]:
    """
    生成代码模板
    """
    try:
        templates = {
            'python': {
                'function': '''def {name}({params}):
    """
    {description}
    """
    pass''',
                'class': '''class {name}:
    """
    {description}
    """
    
    def __init__(self{init_params}):
        pass''',
                'fastapi_route': '''@router.{method}("/{path}")
async def {name}({params}) -> {return_type}:
    """
    {description}
    """
    return {{"message": "Hello World"}}''',
                'test_case': '''def test_{name}():
    """
    测试 {description}
    """
    # Arrange
    
    # Act
    
    # Assert
    assert True''',
                'pydantic_model': '''class {name}(BaseModel):
    """
    {description}
    """
    id: Optional[int] = None
    name: str
    created_at: Optional[datetime] = None''',
                'async_function': '''async def {name}({params}):
    """
    {description}
    """
    pass''',
                'main_script': '''#!/usr/bin/env python3
"""
{description}
"""

def main():
    """主函数"""
    print("Hello, World!")

if __name__ == "__main__":
    main()'''
            },
            'javascript': {
                'function': '''function {name}({params}) {{
    // {description}
}}''',
                'arrow_function': '''const {name} = ({params}) => {{
    // {description}
}};''',
                'class': '''class {name} {{
    constructor({params}) {{
        // {description}
    }}
}}''',
                'react_component': '''import React from 'react';

const {name} = ({params}) => {{
    return (
        <div>
            <h1>{name}</h1>
        </div>
    );
}};

export default {name};''',
                'express_route': '''app.{method}('/{path}', (req, res) => {{
    // {description}
    res.json({{ message: 'Hello World' }});
}});'''
            },
            'typescript': {
                'interface': '''interface {name} {{
    // {description}
    id?: number;
    name: string;
    createdAt?: Date;
}}''',
                'type': '''type {name} = {{
    // {description}
    id?: number;
    name: string;
}};''',
                'function': '''function {name}({params}): {return_type} {{
    // {description}
}}'''
            }
        }
        
        # 获取模板
        language_templates = templates.get(template.language.lower())
        if not language_templates:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported language: {template.language}"
            )
        
        template_code = language_templates.get(template.template_type)
        if not template_code:
            available_types = list(language_templates.keys())
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported template type '{template.template_type}' for {template.language}. Available types: {available_types}"
            )
        
        # 设置默认参数
        params = {
            'name': template.name,
            'description': template.parameters.get('description', f'{template.name} function'),
            'params': template.parameters.get('params', ''),
            'init_params': template.parameters.get('init_params', ''),
            'method': template.parameters.get('method', 'get'),
            'path': template.parameters.get('path', template.name.lower().replace('_', '-')),
            'return_type': template.parameters.get('return_type', 'Dict[str, Any]'),
            **template.parameters
        }
        
        # 格式化模板
        generated_code = template_code.format(**params)
        
        return {
            "status": "success",
            "template": {
                "type": template.template_type,
                "language": template.language,
                "name": template.name,
                "code": generated_code
            }
        }
        
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing required parameter: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate template: {str(e)}")

@router.get("/code/templates")
async def list_code_templates() -> Dict[str, Any]:
    """
    列出所有可用的代码模板
    """
    try:
        templates = {
            "python": [
                "function", "class", "fastapi_route", "test_case", 
                "pydantic_model", "async_function", "main_script"
            ],
            "javascript": [
                "function", "arrow_function", "class", "react_component", "express_route"
            ],
            "typescript": [
                "interface", "type", "function"
            ]
        }
        
        return {
            "status": "success",
            "templates": templates,
            "total_languages": len(templates),
            "total_templates": sum(len(t) for t in templates.values())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list templates: {str(e)}")

@router.post("/code/snippets")
async def add_code_snippet(snippet: CodeSnippet) -> Dict[str, Any]:
    """
    添加代码片段到代码库
    """
    try:
        # 创建代码片段存储目录
        snippets_dir = Path("code_snippets")
        snippets_dir.mkdir(exist_ok=True)
        
        # 按语言分组存储
        language_dir = snippets_dir / snippet.language
        language_dir.mkdir(exist_ok=True)
        
        # 生成文件名
        snippet_file = language_dir / f"{snippet.snippet_type}_{int(time.time())}.json"
        
        # 保存代码片段
        snippet_data = {
            "language": snippet.language,
            "snippet_type": snippet.snippet_type,
            "content": snippet.content,
            "description": snippet.description,
            "created_at": datetime.utcnow().isoformat()
        }
        
        with open(snippet_file, 'w', encoding='utf-8') as f:
            json.dump(snippet_data, f, indent=2, ensure_ascii=False)
        
        return {
            "status": "success",
            "message": "Code snippet added successfully",
            "snippet": {
                "id": snippet_file.stem,
                "language": snippet.language,
                "type": snippet.snippet_type,
                "file": str(snippet_file)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add snippet: {str(e)}")

@router.get("/code/snippets/{language}")
async def get_code_snippets(language: str, snippet_type: Optional[str] = None) -> Dict[str, Any]:
    """
    获取指定语言的代码片段
    """
    try:
        snippets_dir = Path("code_snippets") / language
        
        if not snippets_dir.exists():
            return {
                "status": "success",
                "language": language,
                "snippets": [],
                "total": 0
            }
        
        snippets = []
        
        for snippet_file in snippets_dir.glob("*.json"):
            try:
                with open(snippet_file, 'r', encoding='utf-8') as f:
                    snippet_data = json.load(f)
                
                # 过滤类型
                if snippet_type and snippet_data.get("snippet_type") != snippet_type:
                    continue
                
                snippets.append({
                    "id": snippet_file.stem,
                    "type": snippet_data.get("snippet_type"),
                    "content": snippet_data.get("content"),
                    "description": snippet_data.get("description"),
                    "created_at": snippet_data.get("created_at")
                })
                
            except (json.JSONDecodeError, FileNotFoundError):
                continue  # 跳过无效文件
        
        return {
            "status": "success",
            "language": language,
            "filter_type": snippet_type,
            "snippets": snippets,
            "total": len(snippets)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get snippets: {str(e)}")

@router.post("/projects/{project_name}/generate")
async def generate_project_file(
    project_name: str, 
    template: CodeTemplate,
    target_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    在项目中生成代码文件
    """
    try:
        project_path = PROJECTS_ROOT / project_name
        
        if not project_path.exists():
            raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found")
        
        # 生成代码
        template_response = await generate_code_template(template)
        generated_code = template_response["template"]["code"]
        
        # 确定文件路径
        if not target_path:
            # 根据语言和类型自动确定路径
            extension_map = {
                'python': '.py',
                'javascript': '.js',
                'typescript': '.ts'
            }
            
            extension = extension_map.get(template.language, '.txt')
            target_path = f"{template.name}{extension}"
        
        file_path = project_path / target_path
        
        # 确保目录存在
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(generated_code)
        
        return {
            "status": "success",
            "message": f"Generated {template.template_type} file successfully",
            "file": {
                "path": target_path,
                "full_path": str(file_path),
                "template_type": template.template_type,
                "language": template.language,
                "size": len(generated_code.encode('utf-8'))
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate project file: {str(e)}")

# 高级文件系统操作API
@router.post("/projects/{project_name}/search")
async def search_files(project_name: str, search: FileSearch) -> Dict[str, Any]:
    """
    在项目中搜索文件
    """
    try:
        project_path = PROJECTS_ROOT / project_name
        
        if not project_path.exists():
            raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found")
        
        results = []
        searched_files = 0
        
        def should_include_file(file_path: Path) -> bool:
            # 文件类型过滤
            if search.file_types:
                if not any(str(file_path).endswith(ext) for ext in search.file_types):
                    return False
            
            # 跳过隐藏文件和常见的忽略目录
            ignore_patterns = ['.git', '__pycache__', 'node_modules', '.pytest_cache', '.venv']
            for part in file_path.parts:
                if any(fnmatch.fnmatch(part, pattern) for pattern in ignore_patterns):
                    return False
                if part.startswith('.') and part not in ['.', '..']:
                    return False
            
            return True
        
        # 搜索文件
        for file_path in project_path.rglob("*"):
            if len(results) >= search.max_results:
                break
                
            if file_path.is_file() and should_include_file(file_path):
                searched_files += 1
                relative_path = file_path.relative_to(project_path)
                
                # 文件名匹配
                filename_match = fnmatch.fnmatch(file_path.name.lower(), search.pattern.lower())
                path_match = fnmatch.fnmatch(str(relative_path).lower(), search.pattern.lower())
                
                content_matches = []
                if search.include_content:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # 使用正则表达式搜索内容
                            pattern = re.compile(re.escape(search.pattern), re.IGNORECASE)
                            matches = pattern.finditer(content)
                            
                            for match in matches:
                                # 找到匹配行号
                                line_num = content[:match.start()].count('\n') + 1
                                line_content = content.split('\n')[line_num - 1].strip()
                                content_matches.append({
                                    "line": line_num,
                                    "content": line_content,
                                    "position": match.start()
                                })
                                
                                if len(content_matches) >= 10:  # 限制每个文件最多10个匹配
                                    break
                    except (UnicodeDecodeError, PermissionError):
                        pass  # 跳过无法读取的文件
                
                if filename_match or path_match or content_matches:
                    results.append({
                        "path": str(relative_path),
                        "full_path": str(file_path),
                        "size": file_path.stat().st_size,
                        "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                        "match_type": "filename" if filename_match else "path" if path_match else "content",
                        "content_matches": content_matches if search.include_content else []
                    })
        
        return {
            "status": "success",
            "project": project_name,
            "pattern": search.pattern,
            "searched_files": searched_files,
            "results": results,
            "total_matches": len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search files: {str(e)}")

@router.post("/projects/{project_name}/batch")
async def batch_file_operations(project_name: str, operation: BatchFileOperation) -> Dict[str, Any]:
    """
    批量文件操作
    """
    try:
        project_path = PROJECTS_ROOT / project_name
        
        if not project_path.exists():
            raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found")
        
        results = []
        errors = []
        
        for file_path in operation.files:
            try:
                source_path = project_path / file_path
                
                if not source_path.exists():
                    errors.append(f"File not found: {file_path}")
                    continue
                
                if operation.operation == "delete":
                    if source_path.is_file():
                        source_path.unlink()
                    elif source_path.is_dir():
                        shutil.rmtree(source_path)
                    results.append(f"Deleted: {file_path}")
                
                elif operation.operation in ["copy", "move"]:
                    if not operation.target_dir:
                        errors.append(f"Target directory required for {operation.operation}")
                        continue
                    
                    target_dir = project_path / operation.target_dir
                    target_dir.mkdir(parents=True, exist_ok=True)
                    target_path = target_dir / source_path.name
                    
                    if operation.operation == "copy":
                        if source_path.is_file():
                            shutil.copy2(source_path, target_path)
                        elif source_path.is_dir():
                            shutil.copytree(source_path, target_path, dirs_exist_ok=True)
                        results.append(f"Copied: {file_path} -> {operation.target_dir}")
                    
                    elif operation.operation == "move":
                        shutil.move(str(source_path), str(target_path))
                        results.append(f"Moved: {file_path} -> {operation.target_dir}")
                
                else:
                    errors.append(f"Unsupported operation: {operation.operation}")
            
            except Exception as e:
                errors.append(f"Error processing {file_path}: {str(e)}")
        
        return {
            "status": "success" if not errors else "partial",
            "operation": operation.operation,
            "processed": len(results),
            "errors": len(errors),
            "results": results,
            "error_details": errors
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to perform batch operation: {str(e)}")

@router.post("/projects/{project_name}/directories")
async def directory_operations(project_name: str, operation: DirectoryOperation) -> Dict[str, Any]:
    """
    目录操作
    """
    try:
        project_path = PROJECTS_ROOT / project_name
        
        if not project_path.exists():
            raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found")
        
        source_path = project_path / operation.source_path
        
        if operation.operation == "create":
            source_path.mkdir(parents=True, exist_ok=True)
            return {
                "status": "success",
                "message": f"Directory created: {operation.source_path}",
                "path": str(source_path)
            }
        
        elif operation.operation == "delete":
            if not source_path.exists():
                raise HTTPException(status_code=404, detail=f"Directory not found: {operation.source_path}")
            
            if source_path.is_dir():
                shutil.rmtree(source_path)
            else:
                raise HTTPException(status_code=400, detail=f"Path is not a directory: {operation.source_path}")
            
            return {
                "status": "success",
                "message": f"Directory deleted: {operation.source_path}"
            }
        
        elif operation.operation in ["move", "copy"]:
            if not operation.target_path:
                raise HTTPException(status_code=400, detail="Target path required for move/copy operations")
            
            if not source_path.exists():
                raise HTTPException(status_code=404, detail=f"Source directory not found: {operation.source_path}")
            
            target_path = project_path / operation.target_path
            
            if operation.operation == "move":
                shutil.move(str(source_path), str(target_path))
                message = f"Directory moved: {operation.source_path} -> {operation.target_path}"
            
            elif operation.operation == "copy":
                shutil.copytree(source_path, target_path, dirs_exist_ok=True)
                message = f"Directory copied: {operation.source_path} -> {operation.target_path}"
            
            return {
                "status": "success",
                "message": message,
                "source": str(source_path),
                "target": str(target_path)
            }
        
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported operation: {operation.operation}")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to perform directory operation: {str(e)}")

@router.get("/projects/{project_name}/stats")
async def get_project_stats(project_name: str) -> Dict[str, Any]:
    """
    获取项目统计信息
    """
    try:
        project_path = PROJECTS_ROOT / project_name
        
        if not project_path.exists():
            raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found")
        
        stats = {
            "total_files": 0,
            "total_directories": 0,
            "total_size": 0,
            "file_types": {},
            "largest_files": [],
            "recent_files": []
        }
        
        files_info = []
        
        for item in project_path.rglob("*"):
            if item.is_file():
                try:
                    file_stat = item.stat()
                    file_size = file_stat.st_size
                    file_mtime = file_stat.st_mtime
                    relative_path = item.relative_to(project_path)
                    
                    stats["total_files"] += 1
                    stats["total_size"] += file_size
                    
                    # 文件类型统计
                    file_ext = item.suffix.lower()
                    if file_ext:
                        stats["file_types"][file_ext] = stats["file_types"].get(file_ext, 0) + 1
                    else:
                        stats["file_types"]["no_extension"] = stats["file_types"].get("no_extension", 0) + 1
                    
                    files_info.append({
                        "path": str(relative_path),
                        "size": file_size,
                        "modified": file_mtime
                    })
                    
                except (PermissionError, OSError):
                    continue
            
            elif item.is_dir():
                stats["total_directories"] += 1
        
        # 最大的文件
        stats["largest_files"] = sorted(files_info, key=lambda x: x["size"], reverse=True)[:10]
        
        # 最近修改的文件
        stats["recent_files"] = sorted(files_info, key=lambda x: x["modified"], reverse=True)[:10]
        
        # 转换时间戳
        for file_info in stats["recent_files"]:
            file_info["modified"] = datetime.fromtimestamp(file_info["modified"]).isoformat()
        
        # 格式化文件大小
        def format_size(size_bytes):
            if size_bytes < 1024:
                return f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                return f"{size_bytes / 1024:.1f} KB"
            elif size_bytes < 1024 * 1024 * 1024:
                return f"{size_bytes / (1024 * 1024):.1f} MB"
            else:
                return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
        
        stats["total_size_formatted"] = format_size(stats["total_size"])
        
        return {
            "status": "success",
            "project": project_name,
            "stats": stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get project stats: {str(e)}")

@router.get("/projects/{project_name}/backup")
async def backup_project(project_name: str, include_git: bool = False) -> Dict[str, Any]:
    """
    备份项目
    """
    try:
        project_path = PROJECTS_ROOT / project_name
        
        if not project_path.exists():
            raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found")
        
        # 创建备份目录
        backup_dir = Path("backups")
        backup_dir.mkdir(exist_ok=True)
        
        # 生成备份文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{project_name}_backup_{timestamp}"
        backup_path = backup_dir / backup_name
        
        def ignore_patterns(dir_path, names):
            ignore = []
            if not include_git:
                ignore.extend([name for name in names if name in ['.git', '__pycache__', '.pytest_cache', 'node_modules', '.venv']])
            return ignore
        
        # 复制项目
        shutil.copytree(project_path, backup_path, ignore=ignore_patterns)
        
        # 创建压缩包
        archive_path = backup_dir / f"{backup_name}.tar.gz"
        shutil.make_archive(str(backup_path), 'gztar', str(backup_path))
        
        # 删除临时目录
        shutil.rmtree(backup_path)
        
        # 获取备份信息
        backup_size = archive_path.stat().st_size
        
        return {
            "status": "success",
            "message": f"Project '{project_name}' backed up successfully",
            "backup": {
                "name": f"{backup_name}.tar.gz",
                "path": str(archive_path),
                "size": backup_size,
                "created_at": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to backup project: {str(e)}") 