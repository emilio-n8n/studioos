import os
import logging

logger = logging.getLogger("studioos.file_manager")


class PathTraversalError(Exception):
    pass


class FileManager:
    def __init__(self, base_dir: str = "output"):
        self.base_dir = os.path.abspath(base_dir)

    def _safe_path(self, project_id: int, relative_path: str) -> str:
        project_dir = os.path.join(self.base_dir, str(project_id))
        full_path = os.path.normpath(os.path.join(project_dir, relative_path))
        if not full_path.startswith(os.path.normpath(project_dir) + os.sep) and full_path != os.path.normpath(project_dir):
            raise PathTraversalError(f"Path traversal blocked: {relative_path}")
        return full_path

    def _get_project_dir(self, project_id: int, output_path: str | None = None) -> str:
        if output_path:
            return os.path.abspath(output_path)
        return os.path.join(self.base_dir, str(project_id))

    def save_website(self, project_id: int, files: list[dict], output_path: str | None = None) -> str:
        project_dir = self._get_project_dir(project_id, output_path)
        os.makedirs(project_dir, exist_ok=True)
        for file_entry in files:
            full_path = os.path.join(project_dir, file_entry["path"])
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(file_entry["content"])
        return project_dir

    def list_files(self, project_id: int, output_path: str | None = None) -> list[dict]:
        project_dir = self._get_project_dir(project_id, output_path)
        if not os.path.exists(project_dir):
            return []
        result = []
        for root, dirs, files in os.walk(project_dir):
            for f in files:
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, project_dir)
                if rel_path.startswith(".."):
                    continue
                with open(full_path, "r", encoding="utf-8") as fh:
                    content = fh.read()
                result.append({"path": rel_path, "content": content})
        return result

    def get_output_url(self, project_id: int, output_path: str | None = None) -> str:
        project_dir = self._get_project_dir(project_id, output_path)
        index_path = os.path.join(project_dir, "index.html")
        if os.path.exists(index_path):
            return f"/output/{project_id}/index.html"
        return f"/output/{project_id}/"


file_manager = FileManager()
