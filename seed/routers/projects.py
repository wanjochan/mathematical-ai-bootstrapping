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

class DependencyUninstall(BaseModel):
    packages: List[str]

class DependencyUpdate(BaseModel):
    packages: Optional[List[str]] = None  # 如果为None则更新所有包
    check_only: Optional[bool] = False  # 只检查更新，不实际更新

class CodeTemplate(BaseModel):
    template_type: str  # 'function', 'class', 'fastapi_route', 'test_case', etc.
    language: str  # 'python', 'javascript', 'typescript', etc.
    name: str
    parameters: Optional[Dict[str, Any]] = {}

# Git操作相关模型
class GitInit(BaseModel):
    remote_url: Optional[str] = None
    branch: Optional[str] = "main"

class GitCommit(BaseModel):
    message: str
    add_all: Optional[bool] = True
    files: Optional[List[str]] = None

class GitPush(BaseModel):
    remote: Optional[str] = "origin"
    branch: Optional[str] = None
    force: Optional[bool] = False

class GitClone(BaseModel):
    url: str
    project_name: Optional[str] = None
    branch: Optional[str] = None

# 代码格式化相关模型
class FormatCode(BaseModel):
    files: Optional[List[str]] = None  # 如果为None则格式化所有支持的文件
    language: Optional[str] = None  # 自动检测或指定语言
    options: Optional[Dict[str, Any]] = {}  # 格式化选项

class FormatResult(BaseModel):
    file: str
    status: str  # 'success', 'error', 'skipped'
    message: str
    changes_made: bool = False

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


# Git操作API
@router.post("/projects/{project_name}/git/init")
async def git_init(project_name: str, git_init: GitInit) -> Dict[str, Any]:
    """
    初始化Git仓库
    """
    try:
        project_path = PROJECTS_ROOT / project_name
        
        if not project_path.exists():
            raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found")
        
        # 检查是否已经是git仓库
        git_dir = project_path / ".git"
        if git_dir.exists():
            return {
                "status": "warning", 
                "message": f"Project '{project_name}' is already a Git repository"
            }
        
        # 初始化git仓库
        result = subprocess.run(
            ["git", "init", "-b", git_init.branch],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Git init failed: {result.stderr}")
        
        responses = [f"Git repository initialized with branch '{git_init.branch}'"]
        
        # 添加远程仓库（如果提供）
        if git_init.remote_url:
            remote_result = subprocess.run(
                ["git", "remote", "add", "origin", git_init.remote_url],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            if remote_result.returncode == 0:
                responses.append(f"Remote 'origin' added: {git_init.remote_url}")
            else:
                responses.append(f"Warning: Failed to add remote: {remote_result.stderr}")
        
        # 创建.gitignore文件
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*.pyo
*.pyd
*.so
.Python
*.egg-info/
dist/
build/
.env
.venv/
venv/

# Node.js
node_modules/
npm-debug.log*
*.tgz

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
"""
        gitignore_path = project_path / ".gitignore"
        if not gitignore_path.exists():
            with open(gitignore_path, 'w', encoding='utf-8') as f:
                f.write(gitignore_content)
            responses.append("Created .gitignore file")
        
        return {
            "status": "success",
            "message": "; ".join(responses),
            "branch": git_init.branch,
            "remote": git_init.remote_url
        }
        
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Git init timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize Git: {str(e)}")


@router.post("/projects/git/clone")
async def git_clone(git_clone: GitClone) -> Dict[str, Any]:
    """
    克隆Git仓库
    """
    try:
        # 确定项目名称
        if git_clone.project_name:
            project_name = git_clone.project_name
        else:
            # 从URL提取项目名称
            url_parts = git_clone.url.rstrip('/').split('/')
            project_name = url_parts[-1].replace('.git', '')
        
        project_path = PROJECTS_ROOT / project_name
        
        # 检查项目是否已存在
        if project_path.exists():
            raise HTTPException(status_code=400, detail=f"Project '{project_name}' already exists")
        
        # 构建git clone命令
        cmd = ["git", "clone"]
        if git_clone.branch:
            cmd.extend(["-b", git_clone.branch])
        cmd.extend([git_clone.url, str(project_path)])
        
        # 执行克隆
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )
        
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Git clone failed: {result.stderr}")
        
        # 创建项目配置文件
        project_config = {
            "name": project_name,
            "description": f"Cloned from {git_clone.url}",
            "template": "git_clone",
            "created_at": datetime.utcnow().isoformat(),
            "git": {
                "origin_url": git_clone.url,
                "branch": git_clone.branch or "main"
            }
        }
        
        config_file = project_path / "project.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(project_config, f, indent=2, ensure_ascii=False)
        
        return {
            "status": "success",
            "message": f"Repository cloned successfully",
            "project": {
                "name": project_name,
                "path": str(project_path),
                "url": git_clone.url,
                "branch": git_clone.branch
            }
        }
        
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Git clone timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clone repository: {str(e)}")


@router.get("/projects/{project_name}/git/status")
async def git_status(project_name: str) -> Dict[str, Any]:
    """
    查看Git状态
    """
    try:
        project_path = PROJECTS_ROOT / project_name
        
        if not project_path.exists():
            raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found")
        
        # 检查是否为git仓库
        git_dir = project_path / ".git"
        if not git_dir.exists():
            raise HTTPException(status_code=400, detail=f"Project '{project_name}' is not a Git repository")
        
        # 获取git状态
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if status_result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Git status failed: {status_result.stderr}")
        
        # 获取当前分支
        branch_result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        current_branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "unknown"
        
        # 解析状态
        status_lines = status_result.stdout.strip().split('\n') if status_result.stdout.strip() else []
        
        modified = []
        added = []
        deleted = []
        untracked = []
        
        for line in status_lines:
            if len(line) >= 3:
                status_code = line[:2]
                filename = line[3:]
                
                if status_code == "??":
                    untracked.append(filename)
                elif status_code[0] == "M" or status_code[1] == "M":
                    modified.append(filename)
                elif status_code[0] == "A" or status_code[1] == "A":
                    added.append(filename)
                elif status_code[0] == "D" or status_code[1] == "D":
                    deleted.append(filename)
        
        # 获取远程信息
        remote_result = subprocess.run(
            ["git", "remote", "-v"],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        remotes = {}
        if remote_result.returncode == 0:
            for line in remote_result.stdout.strip().split('\n'):
                if line:
                    parts = line.split()
                    if len(parts) >= 2:
                        remote_name = parts[0]
                        remote_url = parts[1]
                        remotes[remote_name] = remote_url
        
        return {
            "status": "success",
            "git_status": {
                "branch": current_branch,
                "clean": len(status_lines) == 0,
                "files": {
                    "modified": modified,
                    "added": added,
                    "deleted": deleted,
                    "untracked": untracked
                },
                "remotes": remotes
            }
        }
        
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Git status timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get Git status: {str(e)}")


@router.post("/projects/{project_name}/git/add")
async def git_add(project_name: str, files: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    添加文件到Git暂存区
    """
    try:
        project_path = PROJECTS_ROOT / project_name
        
        if not project_path.exists():
            raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found")
        
        # 检查是否为git仓库
        git_dir = project_path / ".git"
        if not git_dir.exists():
            raise HTTPException(status_code=400, detail=f"Project '{project_name}' is not a Git repository")
        
        # 构建git add命令
        cmd = ["git", "add"]
        if files:
            # 添加指定文件
            cmd.extend(files)
            message = f"Added {len(files)} file(s) to staging area"
        else:
            # 添加所有文件
            cmd.append(".")
            message = "Added all files to staging area"
        
        # 执行添加
        result = subprocess.run(
            cmd,
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Git add failed: {result.stderr}")
        
        return {
            "status": "success",
            "message": message,
            "files": files or ["all files"]
        }
        
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Git add timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add files: {str(e)}")


@router.post("/projects/{project_name}/git/commit")
async def git_commit(project_name: str, commit_data: GitCommit) -> Dict[str, Any]:
    """
    提交更改到Git仓库
    """
    try:
        project_path = PROJECTS_ROOT / project_name
        
        if not project_path.exists():
            raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found")
        
        # 检查是否为git仓库
        git_dir = project_path / ".git"
        if not git_dir.exists():
            raise HTTPException(status_code=400, detail=f"Project '{project_name}' is not a Git repository")
        
        # 如果需要，先添加文件
        if commit_data.add_all:
            add_result = subprocess.run(
                ["git", "add", "."],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            if add_result.returncode != 0:
                raise HTTPException(status_code=500, detail=f"Git add failed: {add_result.stderr}")
        elif commit_data.files:
            cmd = ["git", "add"] + commit_data.files
            add_result = subprocess.run(
                cmd,
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            if add_result.returncode != 0:
                raise HTTPException(status_code=500, detail=f"Git add failed: {add_result.stderr}")
        
        # 提交更改
        commit_result = subprocess.run(
            ["git", "commit", "-m", commit_data.message],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if commit_result.returncode != 0:
            # 检查是否是"nothing to commit"的情况
            if "nothing to commit" in commit_result.stdout:
                return {
                    "status": "warning",
                    "message": "Nothing to commit, working tree clean"
                }
            else:
                raise HTTPException(status_code=500, detail=f"Git commit failed: {commit_result.stderr}")
        
        # 获取commit信息
        log_result = subprocess.run(
            ["git", "log", "-1", "--oneline"],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        commit_info = log_result.stdout.strip() if log_result.returncode == 0 else "unknown"
        
        return {
            "status": "success",
            "message": f"Changes committed successfully",
            "commit": {
                "message": commit_data.message,
                "info": commit_info
            }
        }
        
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Git commit timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to commit changes: {str(e)}")


@router.post("/projects/{project_name}/git/push")
async def git_push(project_name: str, push_data: GitPush) -> Dict[str, Any]:
    """
    推送更改到远程仓库
    """
    try:
        project_path = PROJECTS_ROOT / project_name
        
        if not project_path.exists():
            raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found")
        
        # 检查是否为git仓库
        git_dir = project_path / ".git"
        if not git_dir.exists():
            raise HTTPException(status_code=400, detail=f"Project '{project_name}' is not a Git repository")
        
        # 获取当前分支（如果没有指定）
        if not push_data.branch:
            branch_result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            if branch_result.returncode == 0 and branch_result.stdout.strip():
                push_data.branch = branch_result.stdout.strip()
            else:
                push_data.branch = "main"
        
        # 构建push命令
        cmd = ["git", "push"]
        if push_data.force:
            cmd.append("--force")
        cmd.extend([push_data.remote, push_data.branch])
        
        # 执行推送
        result = subprocess.run(
            cmd,
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )
        
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Git push failed: {result.stderr}")
        
        return {
            "status": "success",
            "message": f"Successfully pushed to {push_data.remote}/{push_data.branch}",
            "push": {
                "remote": push_data.remote,
                "branch": push_data.branch,
                "force": push_data.force,
                "output": result.stdout
            }
        }
        
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Git push timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to push changes: {str(e)}")


@router.get("/projects/{project_name}/git/log")
async def git_log(project_name: str, limit: int = 10) -> Dict[str, Any]:
    """
    查看Git提交历史
    """
    try:
        project_path = PROJECTS_ROOT / project_name
        
        if not project_path.exists():
            raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found")
        
        # 检查是否为git仓库
        git_dir = project_path / ".git"
        if not git_dir.exists():
            raise HTTPException(status_code=400, detail=f"Project '{project_name}' is not a Git repository")
        
        # 获取提交历史
        result = subprocess.run(
            ["git", "log", f"--max-count={limit}", "--pretty=format:%H|%an|%ae|%ad|%s", "--date=iso"],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Git log failed: {result.stderr}")
        
        commits = []
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split('|', 4)
                if len(parts) == 5:
                    commits.append({
                        "hash": parts[0],
                        "author_name": parts[1],
                        "author_email": parts[2],
                        "date": parts[3],
                        "message": parts[4]
                    })
        
        return {
            "status": "success",
            "commits": commits,
            "total": len(commits)
        }
        
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Git log timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get Git log: {str(e)}")


# 代码格式化API
@router.post("/projects/{project_name}/format")
async def format_code(project_name: str, format_request: FormatCode) -> Dict[str, Any]:
    """
    格式化项目中的代码文件
    """
    try:
        project_path = PROJECTS_ROOT / project_name
        
        if not project_path.exists():
            raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found")
        
        # 定义支持的文件类型和对应的格式化工具
        formatters = {
            '.py': {
                'tool': 'black',
                'command': ['python', '-m', 'black'],
                'check_cmd': ['python', '-c', 'import black; print("black available")']
            },
            '.js': {
                'tool': 'prettier',
                'command': ['npx', 'prettier', '--write'],
                'check_cmd': ['npx', 'prettier', '--version']
            },
            '.ts': {
                'tool': 'prettier',
                'command': ['npx', 'prettier', '--write'],
                'check_cmd': ['npx', 'prettier', '--version']
            },
            '.json': {
                'tool': 'prettier',
                'command': ['npx', 'prettier', '--write'],
                'check_cmd': ['npx', 'prettier', '--version']
            },
            '.html': {
                'tool': 'prettier',
                'command': ['npx', 'prettier', '--write'],
                'check_cmd': ['npx', 'prettier', '--version']
            },
            '.css': {
                'tool': 'prettier',
                'command': ['npx', 'prettier', '--write'],
                'check_cmd': ['npx', 'prettier', '--version']
            }
        }
        
        results = []
        files_to_format = []
        
        # 确定要格式化的文件
        if format_request.files:
            # 使用指定的文件列表
            for file_path in format_request.files:
                full_path = project_path / file_path
                if full_path.exists() and full_path.is_file():
                    files_to_format.append(full_path)
                else:
                    results.append({
                        "file": file_path,
                        "status": "error",
                        "message": f"File not found: {file_path}",
                        "changes_made": False
                    })
        else:
            # 自动发现支持的文件类型
            for ext in formatters.keys():
                for file_path in project_path.rglob(f"*{ext}"):
                    # 跳过常见的忽略目录
                    if any(part in ['.git', '__pycache__', 'node_modules', '.pytest_cache', '.venv'] 
                           for part in file_path.parts):
                        continue
                    files_to_format.append(file_path)
        
        if not files_to_format:
            return {
                "status": "warning",
                "message": "No supported files found for formatting",
                "results": [],
                "total_files": 0,
                "successful": 0,
                "failed": 0
            }
        
        # 按文件类型分组并格式化
        formatter_availability = {}
        
        for file_path in files_to_format:
            file_ext = file_path.suffix.lower()
            relative_path = str(file_path.relative_to(project_path))
            
            if file_ext not in formatters:
                results.append({
                    "file": relative_path,
                    "status": "skipped",
                    "message": f"Unsupported file type: {file_ext}",
                    "changes_made": False
                })
                continue
            
            formatter_config = formatters[file_ext]
            tool_name = formatter_config['tool']
            
            # 检查格式化工具是否可用（缓存结果）
            if tool_name not in formatter_availability:
                try:
                    check_result = subprocess.run(
                        formatter_config['check_cmd'],
                        cwd=project_path,
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    formatter_availability[tool_name] = check_result.returncode == 0
                except:
                    formatter_availability[tool_name] = False
            
            if not formatter_availability[tool_name]:
                results.append({
                    "file": relative_path,
                    "status": "error",
                    "message": f"Formatter '{tool_name}' not available. Please install it first.",
                    "changes_made": False
                })
                continue
            
            # 读取文件内容（用于检查是否有变化）
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    original_content = f.read()
            except Exception as e:
                results.append({
                    "file": relative_path,
                    "status": "error", 
                    "message": f"Failed to read file: {str(e)}",
                    "changes_made": False
                })
                continue
            
            # 执行格式化
            try:
                cmd = formatter_config['command'] + [str(file_path)]
                
                # 添加用户指定的选项
                if format_request.options:
                    if tool_name == 'black':
                        if 'line_length' in format_request.options:
                            cmd.extend(['--line-length', str(format_request.options['line_length'])])
                        if 'skip_string_normalization' in format_request.options:
                            if format_request.options['skip_string_normalization']:
                                cmd.append('--skip-string-normalization')
                    elif tool_name == 'prettier':
                        if 'tab_width' in format_request.options:
                            cmd.extend(['--tab-width', str(format_request.options['tab_width'])])
                        if 'use_tabs' in format_request.options:
                            cmd.extend(['--use-tabs', str(format_request.options['use_tabs']).lower()])
                
                result = subprocess.run(
                    cmd,
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode == 0:
                    # 检查文件是否有变化
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            new_content = f.read()
                        changes_made = original_content != new_content
                    except:
                        changes_made = True  # 假设有变化，如果无法检测
                    
                    results.append({
                        "file": relative_path,
                        "status": "success",
                        "message": f"Formatted with {tool_name}" + (" (changes made)" if changes_made else " (no changes needed)"),
                        "changes_made": changes_made
                    })
                else:
                    results.append({
                        "file": relative_path,
                        "status": "error",
                        "message": f"Formatting failed: {result.stderr.strip() or result.stdout.strip()}",
                        "changes_made": False
                    })
            
            except subprocess.TimeoutExpired:
                results.append({
                    "file": relative_path,
                    "status": "error",
                    "message": "Formatting timeout",
                    "changes_made": False
                })
            except Exception as e:
                results.append({
                    "file": relative_path,
                    "status": "error",
                    "message": f"Formatting error: {str(e)}",
                    "changes_made": False
                })
        
        # 统计结果
        successful = len([r for r in results if r["status"] == "success"])
        failed = len([r for r in results if r["status"] == "error"])
        skipped = len([r for r in results if r["status"] == "skipped"])
        changes_made = len([r for r in results if r["changes_made"]])
        
        return {
            "status": "success" if failed == 0 else "partial",
            "message": f"Formatted {successful} files successfully, {failed} failed, {skipped} skipped",
            "results": results,
            "summary": {
                "total_files": len(results),
                "successful": successful,
                "failed": failed,
                "skipped": skipped,
                "changes_made": changes_made
            },
            "available_formatters": {
                tool: available for tool, available in formatter_availability.items()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to format code: {str(e)}")


@router.get("/projects/{project_name}/format/check")
async def check_formatters(project_name: str) -> Dict[str, Any]:
    """
    检查可用的代码格式化工具
    """
    try:
        project_path = PROJECTS_ROOT / project_name
        
        if not project_path.exists():
            raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found")
        
        formatters = {
            'black': {
                'description': 'Python code formatter',
                'install_cmd': 'pip install black',
                'check_cmd': ['python', '-c', 'import black; print(black.__version__)']
            },
            'prettier': {
                'description': 'JavaScript/TypeScript/JSON/HTML/CSS formatter',
                'install_cmd': 'npm install -g prettier',
                'check_cmd': ['npx', 'prettier', '--version']
            }
        }
        
        status = {}
        
        for tool_name, config in formatters.items():
            try:
                result = subprocess.run(
                    config['check_cmd'],
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    version = result.stdout.strip()
                    status[tool_name] = {
                        "available": True,
                        "version": version,
                        "description": config['description']
                    }
                else:
                    status[tool_name] = {
                        "available": False,
                        "error": result.stderr.strip() or "Command failed",
                        "description": config['description'],
                        "install_cmd": config['install_cmd']
                    }
            except subprocess.TimeoutExpired:
                status[tool_name] = {
                    "available": False,
                    "error": "Check timeout",
                    "description": config['description'],
                    "install_cmd": config['install_cmd']
                }
            except Exception as e:
                status[tool_name] = {
                    "available": False,
                    "error": str(e),
                    "description": config['description'],
                    "install_cmd": config['install_cmd']
                }
        
        available_count = len([s for s in status.values() if s["available"]])
        
        return {
            "status": "success",
            "message": f"{available_count}/{len(formatters)} formatters available",
            "formatters": status,
            "supported_extensions": {
                "black": [".py"],
                "prettier": [".js", ".ts", ".json", ".html", ".css"]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check formatters: {str(e)}")


@router.post("/projects/{project_name}/format/install")
async def install_formatters(project_name: str, tools: List[str]) -> Dict[str, Any]:
    """
    安装代码格式化工具
    """
    try:
        project_path = PROJECTS_ROOT / project_name
        
        if not project_path.exists():
            raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found")
        
        install_commands = {
            'black': ['python', '-m', 'pip', 'install', 'black'],
            'prettier': ['npm', 'install', '-g', 'prettier']
        }
        
        results = []
        
        for tool in tools:
            if tool not in install_commands:
                results.append({
                    "tool": tool,
                    "status": "error",
                    "message": f"Unknown formatter: {tool}"
                })
                continue
            
            try:
                cmd = install_commands[tool]
                result = subprocess.run(
                    cmd,
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5分钟超时
                )
                
                if result.returncode == 0:
                    results.append({
                        "tool": tool,
                        "status": "success",
                        "message": f"{tool} installed successfully",
                        "output": result.stdout
                    })
                else:
                    results.append({
                        "tool": tool,
                        "status": "error",
                        "message": f"Installation failed: {result.stderr}",
                        "output": result.stdout
                    })
                    
            except subprocess.TimeoutExpired:
                results.append({
                    "tool": tool,
                    "status": "error",
                    "message": "Installation timeout"
                })
            except Exception as e:
                results.append({
                    "tool": tool,
                    "status": "error",
                    "message": f"Installation error: {str(e)}"
                })
        
        successful = len([r for r in results if r["status"] == "success"])
        failed = len([r for r in results if r["status"] == "error"])
        
        return {
            "status": "success" if failed == 0 else "partial",
            "message": f"Installed {successful}/{len(tools)} formatters successfully",
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to install formatters: {str(e)}")


# 扩展依赖管理API
@router.post("/projects/{project_name}/dependencies/uninstall")
async def uninstall_dependencies(project_name: str, dependencies: DependencyUninstall) -> Dict[str, Any]:
    """
    卸载项目依赖
    """
    try:
        project_path = PROJECTS_ROOT / project_name
        
        if not project_path.exists():
            raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found")
        
        # 检查项目类型
        requirements_file = project_path / "requirements.txt"
        package_json = project_path / "package.json"
        is_python_project = requirements_file.exists() or (project_path / "setup.py").exists()
        is_node_project = package_json.exists()
        
        if not (is_python_project or is_node_project):
            raise HTTPException(
                status_code=400, 
                detail="Unsupported project type. Only Python and Node.js projects are supported."
            )
        
        results = []
        
        for package in dependencies.packages:
            try:
                if is_python_project:
                    cmd = ["pip", "uninstall", package, "-y"]
                else:  # Node.js project
                    cmd = ["npm", "uninstall", package]
                
                result = subprocess.run(
                    cmd,
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                if result.returncode == 0:
                    results.append({
                        "package": package,
                        "status": "success",
                        "message": f"Successfully uninstalled {package}",
                        "output": result.stdout
                    })
                    
                    # 从项目配置中移除
                    config_file = project_path / "project.json"
                    if config_file.exists():
                        with open(config_file, 'r', encoding='utf-8') as f:
                            project_config = json.load(f)
                        
                        deps = project_config.get("dependencies", [])
                        if package in deps:
                            deps.remove(package)
                            project_config["dependencies"] = deps
                            
                            with open(config_file, 'w', encoding='utf-8') as f:
                                json.dump(project_config, f, indent=2, ensure_ascii=False)
                else:
                    results.append({
                        "package": package,
                        "status": "error",
                        "message": f"Failed to uninstall {package}: {result.stderr}",
                        "output": result.stdout
                    })
            
            except subprocess.TimeoutExpired:
                results.append({
                    "package": package,
                    "status": "error",
                    "message": f"Uninstall timeout for {package}"
                })
            except Exception as e:
                results.append({
                    "package": package,
                    "status": "error",
                    "message": f"Uninstall error for {package}: {str(e)}"
                })
        
        successful = len([r for r in results if r["status"] == "success"])
        failed = len([r for r in results if r["status"] == "error"])
        
        return {
            "status": "success" if failed == 0 else "partial",
            "message": f"Uninstalled {successful}/{len(dependencies.packages)} packages successfully",
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to uninstall dependencies: {str(e)}")


@router.post("/projects/{project_name}/dependencies/update")
async def update_dependencies(project_name: str, update_request: DependencyUpdate) -> Dict[str, Any]:
    """
    更新项目依赖
    """
    try:
        project_path = PROJECTS_ROOT / project_name
        
        if not project_path.exists():
            raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found")
        
        # 检查项目类型
        requirements_file = project_path / "requirements.txt"
        package_json = project_path / "package.json"
        is_python_project = requirements_file.exists() or (project_path / "setup.py").exists()
        is_node_project = package_json.exists()
        
        if not (is_python_project or is_node_project):
            raise HTTPException(
                status_code=400, 
                detail="Unsupported project type. Only Python and Node.js projects are supported."
            )
        
        results = []
        packages_to_update = update_request.packages or []
        
        # 如果没有指定包，则获取所有已安装的包
        if not packages_to_update:
            if is_python_project:
                # 从requirements.txt读取
                if requirements_file.exists():
                    with open(requirements_file, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                # 提取包名（去除版本号）
                                package_name = line.split('==')[0].split('>=')[0].split('<=')[0].split('>')[0].split('<')[0]
                                packages_to_update.append(package_name)
            else:  # Node.js
                # 从package.json读取
                if package_json.exists():
                    with open(package_json, 'r') as f:
                        package_data = json.load(f)
                        deps = package_data.get("dependencies", {})
                        dev_deps = package_data.get("devDependencies", {})
                        packages_to_update.extend(list(deps.keys()) + list(dev_deps.keys()))
        
        if not packages_to_update:
            return {
                "status": "warning",
                "message": "No packages found to update",
                "results": []
            }
        
        if update_request.check_only:
            # 只检查可用更新，不实际更新
            if is_python_project:
                cmd = ["pip", "list", "--outdated", "--format=json"]
            else:
                cmd = ["npm", "outdated", "--json"]
            
            try:
                result = subprocess.run(
                    cmd,
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode == 0:
                    if is_python_project:
                        outdated = json.loads(result.stdout) if result.stdout.strip() else []
                        outdated_packages = {pkg["name"]: {"current": pkg["version"], "latest": pkg["latest_version"]} 
                                           for pkg in outdated if pkg["name"] in packages_to_update}
                    else:
                        outdated_data = json.loads(result.stdout) if result.stdout.strip() else {}
                        outdated_packages = {name: {"current": info.get("current"), "latest": info.get("wanted")} 
                                           for name, info in outdated_data.items() if name in packages_to_update}
                    
                    return {
                        "status": "success",
                        "message": f"Found {len(outdated_packages)} packages with available updates",
                        "outdated_packages": outdated_packages,
                        "check_only": True
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Failed to check for updates: {result.stderr}",
                        "check_only": True
                    }
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Failed to check for updates: {str(e)}",
                    "check_only": True
                }
        
        # 实际更新包
        for package in packages_to_update:
            try:
                if is_python_project:
                    cmd = ["pip", "install", "--upgrade", package]
                else:
                    cmd = ["npm", "update", package]
                
                result = subprocess.run(
                    cmd,
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if result.returncode == 0:
                    results.append({
                        "package": package,
                        "status": "success",
                        "message": f"Successfully updated {package}",
                        "output": result.stdout
                    })
                else:
                    results.append({
                        "package": package,
                        "status": "error",
                        "message": f"Failed to update {package}: {result.stderr}",
                        "output": result.stdout
                    })
            
            except subprocess.TimeoutExpired:
                results.append({
                    "package": package,
                    "status": "error",
                    "message": f"Update timeout for {package}"
                })
            except Exception as e:
                results.append({
                    "package": package,
                    "status": "error",
                    "message": f"Update error for {package}: {str(e)}"
                })
        
        successful = len([r for r in results if r["status"] == "success"])
        failed = len([r for r in results if r["status"] == "error"])
        
        return {
            "status": "success" if failed == 0 else "partial",
            "message": f"Updated {successful}/{len(packages_to_update)} packages successfully",
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update dependencies: {str(e)}")


@router.get("/projects/{project_name}/dependencies/list")
async def list_project_dependencies(project_name: str, include_dev: bool = True) -> Dict[str, Any]:
    """
    列出项目依赖详细信息
    """
    try:
        project_path = PROJECTS_ROOT / project_name
        
        if not project_path.exists():
            raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found")
        
        dependencies = {}
        
        # 检查Python项目
        requirements_file = project_path / "requirements.txt"
        if requirements_file.exists():
            dependencies["python"] = {
                "type": "Python",
                "file": "requirements.txt",
                "packages": []
            }
            
            with open(requirements_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        dependencies["python"]["packages"].append(line)
        
        # 检查Node.js项目
        package_json = project_path / "package.json"
        if package_json.exists():
            with open(package_json, 'r') as f:
                package_data = json.load(f)
            
            dependencies["nodejs"] = {
                "type": "Node.js",
                "file": "package.json",
                "dependencies": package_data.get("dependencies", {}),
                "devDependencies": package_data.get("devDependencies", {}) if include_dev else {}
            }
        
        # 获取已安装包的详细信息
        installed_info = {}
        
        # Python包信息
        if "python" in dependencies:
            try:
                result = subprocess.run(
                    ["pip", "list", "--format=json"],
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    installed_packages = json.loads(result.stdout)
                    installed_info["python"] = {pkg["name"]: pkg["version"] for pkg in installed_packages}
            except:
                installed_info["python"] = {}
        
        # Node.js包信息
        if "nodejs" in dependencies:
            try:
                result = subprocess.run(
                    ["npm", "list", "--json", "--depth=0"],
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    npm_data = json.loads(result.stdout)
                    installed_info["nodejs"] = npm_data.get("dependencies", {})
            except:
                installed_info["nodejs"] = {}
        
        return {
            "status": "success",
            "project_name": project_name,
            "dependencies": dependencies,
            "installed": installed_info,
            "summary": {
                "has_python": "python" in dependencies,
                "has_nodejs": "nodejs" in dependencies,
                "python_count": len(dependencies.get("python", {}).get("packages", [])),
                "nodejs_count": len(dependencies.get("nodejs", {}).get("dependencies", {})),
                "nodejs_dev_count": len(dependencies.get("nodejs", {}).get("devDependencies", {}))
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list dependencies: {str(e)}")


@router.get("/projects/{project_name}/dependencies/check")
async def check_dependency_health(project_name: str) -> Dict[str, Any]:
    """
    检查依赖健康状况（安全漏洞、过时版本等）
    """
    try:
        project_path = PROJECTS_ROOT / project_name
        
        if not project_path.exists():
            raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found")
        
        health_report = {}
        
        # Python安全检查
        requirements_file = project_path / "requirements.txt"
        if requirements_file.exists():
            try:
                # 检查安全漏洞（如果安装了safety）
                safety_result = subprocess.run(
                    ["python", "-m", "safety", "check", "--json"],
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if safety_result.returncode == 0:
                    vulnerabilities = json.loads(safety_result.stdout) if safety_result.stdout.strip() else []
                    health_report["python_security"] = {
                        "vulnerabilities": vulnerabilities,
                        "vulnerable_count": len(vulnerabilities),
                        "status": "secure" if len(vulnerabilities) == 0 else "vulnerable"
                    }
                else:
                    health_report["python_security"] = {
                        "status": "check_failed",
                        "error": "Safety tool not available or failed"
                    }
            except:
                health_report["python_security"] = {
                    "status": "not_available",
                    "message": "Install 'safety' package to enable security checks"
                }
        
        # Node.js安全检查
        package_json = project_path / "package.json"
        if package_json.exists():
            try:
                audit_result = subprocess.run(
                    ["npm", "audit", "--json"],
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if audit_result.returncode in [0, 1]:  # 0 = no vulnerabilities, 1 = vulnerabilities found
                    audit_data = json.loads(audit_result.stdout) if audit_result.stdout.strip() else {}
                    vulnerabilities = audit_data.get("vulnerabilities", {})
                    health_report["nodejs_security"] = {
                        "vulnerabilities": vulnerabilities,
                        "vulnerable_count": len(vulnerabilities),
                        "status": "secure" if len(vulnerabilities) == 0 else "vulnerable",
                        "metadata": audit_data.get("metadata", {})
                    }
                else:
                    health_report["nodejs_security"] = {
                        "status": "check_failed",
                        "error": audit_result.stderr
                    }
            except:
                health_report["nodejs_security"] = {
                    "status": "check_failed",
                    "error": "npm audit failed"
                }
        
        # 检查过时的包
        outdated_info = {}
        
        # Python过时检查
        if requirements_file.exists():
            try:
                result = subprocess.run(
                    ["pip", "list", "--outdated", "--format=json"],
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    outdated_packages = json.loads(result.stdout) if result.stdout.strip() else []
                    outdated_info["python"] = {
                        "outdated_packages": outdated_packages,
                        "count": len(outdated_packages)
                    }
            except:
                outdated_info["python"] = {"status": "check_failed"}
        
        # Node.js过时检查
        if package_json.exists():
            try:
                result = subprocess.run(
                    ["npm", "outdated", "--json"],
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                # npm outdated returns exit code 1 when outdated packages are found
                if result.returncode in [0, 1]:
                    outdated_packages = json.loads(result.stdout) if result.stdout.strip() else {}
                    outdated_info["nodejs"] = {
                        "outdated_packages": outdated_packages,
                        "count": len(outdated_packages)
                    }
            except:
                outdated_info["nodejs"] = {"status": "check_failed"}
        
        # 总体健康评分
        total_vulnerabilities = 0
        total_outdated = 0
        
        if "python_security" in health_report:
            total_vulnerabilities += health_report["python_security"].get("vulnerable_count", 0)
        if "nodejs_security" in health_report:
            total_vulnerabilities += health_report["nodejs_security"].get("vulnerable_count", 0)
        
        for platform in outdated_info.values():
            if isinstance(platform, dict) and "count" in platform:
                total_outdated += platform["count"]
        
        # 计算健康评分 (0-100)
        health_score = 100
        health_score -= min(total_vulnerabilities * 20, 80)  # 每个漏洞扣20分，最多扣80分
        health_score -= min(total_outdated * 2, 20)  # 每个过时包扣2分，最多扣20分
        health_score = max(health_score, 0)
        
        return {
            "status": "success",
            "health_score": health_score,
            "summary": {
                "total_vulnerabilities": total_vulnerabilities,
                "total_outdated": total_outdated,
                "overall_status": "healthy" if health_score >= 80 else "needs_attention" if health_score >= 50 else "critical"
            },
            "security": health_report,
            "outdated": outdated_info,
            "recommendations": [
                "Update outdated packages to latest versions",
                "Fix security vulnerabilities immediately",
                "Consider using dependency management tools like Poetry or Pipenv for Python",
                "Run security audits regularly",
                "Pin dependency versions for production deployments"
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check dependency health: {str(e)}") 