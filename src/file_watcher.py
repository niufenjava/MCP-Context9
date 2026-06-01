import watchdog.events
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
from typing import Optional
from src.index_service import IndexService

ALLOWED_DIRS = {"github", "idea", "Knowledge", "manuals"}
EXCLUDED_DIRS = {"_archive", "raw", "archive", "_meta", "node_modules", ".git"}

class MarkdownFileHandler(FileSystemEventHandler):
    def __init__(self, index_service: IndexService):
        self.index_service = index_service
        self._indexing_lock = threading.Lock()
        self._currently_indexing: set = set()

    def _should_index(self, path: str) -> bool:
        rel = os.path.relpath(path, os.path.expanduser("~/my-claw"))
        parts = rel.split(os.sep)
        if len(parts) < 2:
            return False
        top_dir = parts[0]
        if top_dir not in ALLOWED_DIRS:
            return False
        for part in parts:
            if part in EXCLUDED_DIRS:
                return False
        return True

    def on_modified(self, event):
        if event.is_directory or not event.src_path.endswith(".md"):
            return
        if not self._should_index(event.src_path):
            return
        self._index_file(event.src_path)

    def on_created(self, event):
        if event.is_directory or not event.src_path.endswith(".md"):
            return
        if not self._should_index(event.src_path):
            return
        self._index_file(event.src_path)

    def on_deleted(self, event):
        if event.is_directory or not event.src_path.endswith(".md"):
            return
        doc_id = self._path_to_doc_id(event.src_path)
        self.index_service.delete_document(doc_id)
        self.index_service.remove_file_mtime(event.src_path)

    def _index_file(self, path: str):
        with self._indexing_lock:
            if path in self._currently_indexing:
                return
            self._currently_indexing.add(path)
        try:
            mtime = os.path.getmtime(path)
            if self.index_service.is_file_indexed(path, mtime):
                return
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            doc_id = self._path_to_doc_id(path)
            title = os.path.basename(path).replace(".md", "")
            self.index_service.add_document({
                "doc_id": doc_id,
                "title": title,
                "source": "local",
                "url": path,
                "content": content
            })
            self.index_service.save_file_mtime(path, mtime)
        except Exception as e:
            print(f"Error indexing {path}: {e}")
        finally:
            with self._indexing_lock:
                self._currently_indexing.discard(path)

    def _path_to_doc_id(self, path: str) -> str:
        return f"local-{path.replace('/', '-').replace(' ', '-')}"

class FileWatcher:
    def __init__(self, root_dir: str, index_service: Optional[IndexService] = None):
        self.root_dir = root_dir
        self.index_service = index_service or IndexService()
        self.observer = Observer()
        self.handler = MarkdownFileHandler(self.index_service)

    def start(self):
        self.observer.schedule(self.handler, self.root_dir, recursive=True)
        self.observer.start()

    def stop(self):
        self.observer.stop()
        self.observer.join()

    def index_existing(self):
        """索引现有所有文件，跳过未修改的"""
        count = 0
        skipped = 0
        for root, dirs, files in os.walk(self.root_dir):
            rel = os.path.relpath(root, self.root_dir)
            parts = [p for p in rel.split(os.sep) if p]
            if rel == "." or not parts:
                dirs[:] = [d for d in dirs if d in ALLOWED_DIRS]
                continue
            top_dir = parts[0]
            if top_dir not in ALLOWED_DIRS:
                dirs[:] = []
                continue
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
            for file in files:
                if not file.endswith(".md"):
                    continue
                path = os.path.join(root, file)
                if not self.handler._should_index(path):
                    continue
                try:
                    mtime = os.path.getmtime(path)
                    if self.index_service.is_file_indexed(path, mtime):
                        skipped += 1
                        continue
                    self.handler._index_file(path)
                    count += 1
                    if count % 50 == 0:
                        print(f"[Watcher] Indexed {count} new files...")
                except Exception as e:
                    print(f"Error checking {path}: {e}")
        print(f"[Watcher] Done. Indexed {count} new files, skipped {skipped} unchanged.")
