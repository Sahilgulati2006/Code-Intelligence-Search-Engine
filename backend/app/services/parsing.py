from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, TYPE_CHECKING
import os

if TYPE_CHECKING:
    from tree_sitter import Parser

try:
    from tree_sitter import Language, Parser, Node
    import tree_sitter_languages
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    Parser = None  # type: ignore
    print("Warning: tree-sitter not available. Install with: pip install tree-sitter tree-sitter-languages")

# For parser caching (initialized after imports)
_parser_cache: Dict[str, Optional["Parser"]] = {}

SKIP_DIRS = {"tests", "test", "docs", "examples", "scripts", ".venv", "venv", "build", "dist", "node_modules", ".git"}

# Language configuration: file extensions -> language names
LANGUAGE_CONFIG = {
    "python": [".py"],
    "javascript": [".js", ".jsx"],
    "typescript": [".ts", ".tsx"],
    "java": [".java"],
    "go": [".go"],
    "rust": [".rs"],
    "cpp": [".cpp", ".cc", ".cxx", ".c++", ".hpp", ".h"],
    "c": [".c", ".h"],
    "ruby": [".rb"],
    "php": [".php"],
    "kotlin": [".kt"],
    "swift": [".swift"],
    "scala": [".scala"],
}

# Reverse mapping: extension -> language
EXT_TO_LANG = {ext: lang for lang, exts in LANGUAGE_CONFIG.items() for ext in exts}


def _get_language_parser(language: str) -> Optional[Parser]:
    """
    Get a tree-sitter parser for the given language.
    Returns None if the language is not supported or parser cannot be created.
    Uses caching to avoid recreating parsers.
    """
    if not TREE_SITTER_AVAILABLE:
        return None
    
    # Check cache
    if language in _parser_cache:
        return _parser_cache[language]
    
    parser = None
    try:
        # Try using tree-sitter-languages
        # Note: There may be API compatibility issues with some versions
        # This will work if tree-sitter-languages is properly configured
        lang_path = os.path.dirname(tree_sitter_languages.__file__)
        languages_so = os.path.join(lang_path, "languages.so")
        
        if os.path.exists(languages_so):
            try:
                # Try the standard API (may fail due to version compatibility)
                lang_obj = Language(languages_so, language)
                parser = Parser(lang_obj)
            except (TypeError, AttributeError, ValueError) as e:
                # API compatibility issue - tree-sitter-languages API may differ
                # For now, we'll fall back to Python AST for Python files
                # Other languages will be skipped until tree-sitter-languages API is fixed
                parser = None
    except Exception as e:
        parser = None
    
    _parser_cache[language] = parser
    return parser


def _get_source_code(node: Node, source_bytes: bytes) -> str:
    """Extract source code for a tree-sitter node."""
    return source_bytes[node.start_byte:node.end_byte].decode("utf-8")


def _find_all_nodes(node: Node, node_type: str) -> List[Node]:
    """Find all nodes of a given type in the tree."""
    results = []
    if node.type == node_type:
        results.append(node)
    for child in node.children:
        results.extend(_find_all_nodes(child, node_type))
    return results


def _get_function_name(node: Node, source_bytes: bytes) -> Optional[str]:
    """Extract function name from a function definition node."""
    # Look for identifier or similar nodes that represent the function name
    for child in node.children:
        if child.type in ("identifier", "function_name", "name"):
            return _get_source_code(child, source_bytes).strip()
        # For some languages, name might be in a different structure
        if child.type in ("name", "function_signature"):
            for grandchild in child.children:
                if grandchild.type in ("identifier", "name"):
                    return _get_source_code(grandchild, source_bytes).strip()
    return None


def _extract_call_sites(node: Node, source_bytes: bytes, start_line: int) -> List[Dict[str, Any]]:
    """Extract call sites from a function body node."""
    calls = []
    
    def find_calls(n: Node):
        if n.type in ("call", "call_expression", "invocation_expression"):
            # Try to get the function name being called
            func_name = None
            for child in n.children:
                if child.type in ("identifier", "member_expression", "field_expression"):
                    # For method calls like obj.method(), get the method name
                    if child.type == "member_expression":
                        for gc in child.children:
                            if gc.type == "property_identifier" or (gc.type == "identifier" and gc.start_byte > child.children[0].end_byte):
                                func_name = _get_source_code(gc, source_bytes).strip()
                                break
                    else:
                        func_name = _get_source_code(child, source_bytes).strip()
                    if func_name:
                        break
                
                # Sometimes the function name is directly in the call
                if child.type in ("identifier", "property_identifier") and not func_name:
                    func_name = _get_source_code(child, source_bytes).strip()
            
            if func_name:
                call_text = _get_source_code(n, source_bytes)
                call_line = n.start_point[0] + 1  # tree-sitter uses 0-indexed
                calls.append({
                    "name": func_name,
                    "line": call_line,
                    "code": call_text,
                })
        
        for child in n.children:
            find_calls(child)
    
    find_calls(node)
    return calls


def _parse_with_tree_sitter(file_path: Path, language: str, source_bytes: bytes) -> List[Dict[str, Any]]:
    """Parse a file using tree-sitter and extract functions and call sites."""
    chunks = []
    parser = _get_language_parser(language)
    
    if not parser:
        return chunks
    
    try:
        tree = parser.parse(source_bytes)
        root = tree.root_node
        
        # Language-specific function definition node types
        function_node_types = {
            "python": ["function_definition"],
            "javascript": ["function_declaration", "function_expression", "method_definition"],
            "typescript": ["function_declaration", "function_expression", "method_definition"],
            "java": ["method_declaration"],
            "go": ["function_declaration", "method_declaration"],
            "rust": ["function_item"],
            "cpp": ["function_definition"],
            "c": ["function_definition"],
            "ruby": ["method", "singleton_method"],
            "php": ["function_definition", "method_declaration"],
        }
        
        func_types = function_node_types.get(language, ["function_definition", "function_declaration", "method"])
        
        # Find all function definitions
        functions = []
        for func_type in func_types:
            functions.extend(_find_all_nodes(root, func_type))
        
        rel_path = file_path
        if isinstance(file_path, Path):
            # Get relative path if we can determine the repo root
            rel_path = str(file_path.name)  # Fallback to just filename
        
        for func_node in functions:
            func_name = _get_function_name(func_node, source_bytes)
            if not func_name:
                continue
            
            start_line = func_node.start_point[0] + 1  # tree-sitter uses 0-indexed
            end_line = func_node.end_point[0] + 1
            func_code = _get_source_code(func_node, source_bytes)
            
            # Add function definition chunk
            chunks.append({
                "language": language,
                "symbol_type": "function",
                "symbol_name": func_name,
                "file_path": str(rel_path),
                "start_line": start_line,
                "end_line": end_line,
                "code": func_code,
            })
            
            # Extract call sites from function body
            call_sites = _extract_call_sites(func_node, source_bytes, start_line)
            for call in call_sites:
                chunks.append({
                    "language": language,
                    "symbol_type": "call",
                    "symbol_name": call["name"],
                    "file_path": str(rel_path),
                    "start_line": call["line"],
                    "end_line": call["line"],
                    "code": call["code"],
                })
    
    except Exception as e:
        print(f"Error parsing {file_path} with tree-sitter: {e}")
    
    return chunks


def _parse_python_with_ast(file_path: Path, source: str, rel_path: Path) -> List[Dict[str, Any]]:
    """Fallback: Parse Python using AST (original implementation)."""
    import ast as python_ast
    chunks = []
    lines = source.splitlines()
    
    try:
        tree = python_ast.parse(source)
    except (SyntaxError, Exception):
        return chunks
    
    for node in python_ast.walk(tree):
        if isinstance(node, (python_ast.FunctionDef, python_ast.AsyncFunctionDef)):
            start_line = getattr(node, "lineno", None)
            end_line = getattr(node, "end_lineno", None)
            if not start_line or not end_line:
                continue
            
            symbol_name = node.name
            code_text = "\n".join(lines[start_line - 1 : end_line])
            
            # Extract docstring and signature for better semantic matching
            docstring = python_ast.get_docstring(node) or ""
            
            # Build function signature with parameter types if available
            args = node.args
            param_names = [arg.arg for arg in args.args]
            param_str = ", ".join(param_names) if param_names else ""
            signature = f"{symbol_name}({param_str})"
            
            # Combine docstring + signature for semantic context
            semantic_context = f"{signature}. {docstring}".strip() if docstring else signature
            
            chunks.append({
                "language": "python",
                "symbol_type": "function",
                "symbol_name": symbol_name,
                "file_path": str(rel_path),
                "start_line": start_line,
                "end_line": end_line,
                "code": code_text,
                "signature": signature,
                "docstring": docstring,
                "semantic_context": semantic_context,
            })
            
            # Call-site chunks inside this function
            for inner in python_ast.walk(node):
                if isinstance(inner, python_ast.Call):
                    try:
                        call_text = python_ast.get_source_segment(source, inner)
                    except Exception:
                        continue
                    if not call_text:
                        continue
                    
                    func_name = None
                    if isinstance(inner.func, python_ast.Name):
                        func_name = inner.func.id
                    elif isinstance(inner.func, python_ast.Attribute):
                        func_name = inner.func.attr
                    
                    if not func_name:
                        continue
                    
                    call_line = getattr(inner, "lineno", start_line)
                    chunks.append({
                        "language": "python",
                        "symbol_type": "call",
                        "symbol_name": func_name,
                        "file_path": str(rel_path),
                        "start_line": call_line,
                        "end_line": call_line,
                        "code": call_text,
                        "signature": None,
                        "docstring": None,
                        "semantic_context": call_text,
                    })
    
    return chunks


def extract_code_chunks(repo_path: str) -> List[Dict[str, Any]]:
    """
    Extract code chunks (functions and call sites) from a repository.
    Supports multiple languages using tree-sitter, with fallback to Python AST for Python files.
    
    Args:
        repo_path: Path to the repository root
        
    Returns:
        List of code chunk dictionaries with keys: language, symbol_type, symbol_name,
        file_path, start_line, end_line, code
    """
    repo = Path(repo_path)
    chunks: List[Dict[str, Any]] = []
    
    # ✅ If repo uses src-layout, prefer indexing only src/
    src_root = repo / "src"
    index_root = src_root if src_root.exists() and src_root.is_dir() else repo
    
    # Stats tracking
    total_files = 0
    parsed_files = 0
    skipped_read = 0
    skipped_syntax = 0
    skipped_other = 0
    language_counts = {}
    
    # Collect all files by language
    files_by_lang: Dict[str, List[Path]] = {}
    for ext, lang in EXT_TO_LANG.items():
        files_by_lang[lang] = []
    
    # Find all supported files
    for file_path in index_root.rglob("*"):
        if not file_path.is_file():
            continue
        
        total_files += 1
        rel_path = file_path.relative_to(repo)
        
        # Skip noisy dirs
        if any(part in SKIP_DIRS for part in rel_path.parts):
            continue
        
        # Skip common test naming
        if rel_path.name.startswith("test_") or rel_path.name.endswith("_test.py") or rel_path.name.endswith(".test.js"):
            continue
        
        # Determine language from extension
        file_ext = file_path.suffix.lower()
        language = EXT_TO_LANG.get(file_ext)
        if not language:
            continue
        
        files_by_lang[language].append((file_path, rel_path))
    
    # Process files by language
    for language, file_list in files_by_lang.items():
        if not file_list:
            continue
        
        language_counts[language] = 0
        
        for file_path, rel_path in file_list:
            try:
                source_bytes = file_path.read_bytes()
                source = source_bytes.decode("utf-8", errors="ignore")
            except Exception:
                skipped_read += 1
                continue
            
            file_chunks = []

            # If it's a Markdown/README file, add a document chunk so natural language queries can match repo docs
            if language == "markdown":
                lines = source.splitlines()
                file_chunks.append({
                    "language": "markdown",
                    "symbol_type": "doc",
                    "symbol_name": str(rel_path.name),
                    "file_path": str(rel_path),
                    "start_line": 1,
                    "end_line": len(lines) or 1,
                    "code": source,
                })
                parsed_files += 1
                language_counts[language] = language_counts.get(language, 0) + 1
                chunks.extend(file_chunks)
                continue

            # Try tree-sitter first
            if TREE_SITTER_AVAILABLE:
                try:
                    file_chunks = _parse_with_tree_sitter(file_path, language, source_bytes)
                    if file_chunks:
                        parsed_files += 1
                        language_counts[language] += len([c for c in file_chunks if c["symbol_type"] == "function"])
                except Exception as e:
                    skipped_other += 1
                    # Fall through to fallback
            
            # Fallback: For Python, use AST if tree-sitter didn't work
            if not file_chunks and language == "python":
                try:
                    file_chunks = _parse_python_with_ast(file_path, source, rel_path)
                    if file_chunks:
                        parsed_files += 1
                        language_counts[language] += len([c for c in file_chunks if c["symbol_type"] == "function"])
                except Exception:
                    skipped_syntax += 1

            # Additionally, extract module and function docstrings for Python to help natural language queries
            if language == "python":
                try:
                    import ast as python_ast
                    tree = python_ast.parse(source)
                    module_doc = python_ast.get_docstring(tree)
                    if module_doc:
                        file_chunks.append({
                            "language": "python",
                            "symbol_type": "doc",
                            "symbol_name": str(rel_path.name) + ":module_doc",
                            "file_path": str(rel_path),
                            "start_line": 1,
                            "end_line": 1,
                            "code": module_doc,
                        })
                    # function-level docstrings will be added by _parse_python_with_ast as separate call-site chunks if present
                except Exception:
                    pass

            chunks.extend(file_chunks)
    
    print(
        f"[parsing] total_files={total_files}, parsed_files={parsed_files}, "
        f"skipped_read={skipped_read}, skipped_syntax={skipped_syntax}, skipped_other={skipped_other}"
    )
    print(f"[parsing] languages: {dict(language_counts)}")
    
    return chunks


# Backward compatibility alias
def extract_python_functions(repo_path: str) -> List[Dict[str, Any]]:
    """Backward compatibility alias for extract_code_chunks."""
    return extract_code_chunks(repo_path)
