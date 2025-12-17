from __future__ import annotations

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import List

from pypdf import PdfReader

STORAGE_ROOT = Path(os.getenv("DOCUMENT_STORAGE_PATH", "storage/documents"))


class DocumentStore:
    def __init__(self, root: Path = STORAGE_ROOT) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def _user_dir(self, user_id: int) -> Path:
        path = self.root / str(user_id)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _index_path(self, user_id: int) -> Path:
        return self._user_dir(user_id) / "index.json"

    def _load_index(self, user_id: int) -> list[dict]:
        index_path = self._index_path(user_id)
        if not index_path.exists():
            return []
        try:
            return json.loads(index_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []

    def _save_index(self, user_id: int, docs: List[dict]) -> None:
        index_path = self._index_path(user_id)
        index_path.write_text(json.dumps(docs, indent=2), encoding="utf-8")

    def _extract_text(self, pdf_path: Path) -> str:
        try:
            reader = PdfReader(str(pdf_path))
            output = []
            for page in reader.pages:
                text = page.extract_text() or ""
                output.append(text.strip())
            return "\n".join(output).strip()
        except Exception:
            return ""

    def save_document(self, user_id: int, filename: str, content: bytes) -> dict:
        docs = self._load_index(user_id)
        document_id = str(uuid.uuid4())
        stored_name = f"{document_id}.pdf"
        user_dir = self._user_dir(user_id)
        pdf_path = user_dir / stored_name

        with pdf_path.open("wb") as buffer:
            buffer.write(content)

        text_content = self._extract_text(pdf_path)
        text_path = pdf_path.with_suffix(".txt")
        text_path.write_text(text_content, encoding="utf-8")

        preview = text_content[:800] if text_content else "Text preview unavailable."

        metadata = {
            "id": document_id,
            "original_name": filename or "document.pdf",
            "stored_name": stored_name,
            "uploaded_at": datetime.utcnow().isoformat(),
            "preview": preview,
        }

        docs.append(metadata)
        self._save_index(user_id, docs)
        return metadata

    def list_documents(self, user_id: int) -> list[dict]:
        docs = self._load_index(user_id)
        return sorted(docs, key=lambda d: d.get("uploaded_at", ""), reverse=True)

    def get_document(self, user_id: int, document_id: str) -> dict | None:
        for doc in self._load_index(user_id):
            if doc.get("id") == document_id:
                return doc
        return None

    def get_pdf_path(self, user_id: int, document_id: str) -> Path | None:
        doc = self.get_document(user_id, document_id)
        if not doc:
            return None
        pdf_path = self._user_dir(user_id) / doc["stored_name"]
        if pdf_path.exists():
            return pdf_path
        return None

    def get_document_text(self, user_id: int, document_id: str) -> str:
        doc = self.get_document(user_id, document_id)
        if not doc:
            return ""
        pdf_path = self._user_dir(user_id) / doc["stored_name"]
        text_path = pdf_path.with_suffix(".txt")
        if text_path.exists():
            return text_path.read_text(encoding="utf-8")
        if pdf_path.exists():
            text = self._extract_text(pdf_path)
            text_path.write_text(text, encoding="utf-8")
            return text
        return ""

    def delete_document(self, user_id: int, document_id: str) -> bool:
        docs = self._load_index(user_id)
        remaining: list[dict] = []
        deleted_doc = None

        for doc in docs:
            if doc.get("id") == document_id:
                deleted_doc = doc
            else:
                remaining.append(doc)

        if not deleted_doc:
            return False

        self._save_index(user_id, remaining)
        pdf_path = self._user_dir(user_id) / deleted_doc["stored_name"]
        text_path = pdf_path.with_suffix(".txt")
        if pdf_path.exists():
            pdf_path.unlink()
        if text_path.exists():
            text_path.unlink()
        return True


document_store = DocumentStore()

