from __future__ import annotations

from typing import List

from app.services.document_store import document_store


def list_documents_for_agent(user_id: int) -> dict:
    docs = document_store.list_documents(user_id)
    simplified = [
        {
            "id": doc["id"],
            "name": doc.get("original_name", "document.pdf"),
            "uploaded_at": doc.get("uploaded_at"),
            "preview": doc.get("preview", ""),
        }
        for doc in docs
    ]
    return {"documents": simplified}


def summarize_document_for_agent(user_id: int, document_id: str) -> dict:
    doc = document_store.get_document(user_id, document_id)
    if not doc:
        return {"error": "Document not found."}

    text = document_store.get_document_text(user_id, document_id)
    excerpt = text[:1200] if text else doc.get("preview", "")
    return {
        "document": doc.get("original_name", "document"),
        "summary": excerpt or "Unable to extract text from this PDF.",
    }


def search_documents_for_agent(user_id: int, query: str) -> dict:
    if not query:
        return {"results": [], "note": "No query provided."}

    docs = document_store.list_documents(user_id)
    query_lower = query.lower()
    results: List[dict] = []

    for doc in docs:
        text = document_store.get_document_text(user_id, doc["id"])
        if not text:
            continue
        lower_text = text.lower()
        idx = lower_text.find(query_lower)
        if idx == -1:
            continue

        start = max(0, idx - 160)
        end = min(len(text), idx + len(query) + 160)
        snippet = text[start:end].strip()
        results.append(
            {
                "document": doc.get("original_name", "document"),
                "snippet": snippet or doc.get("preview", ""),
            }
        )

    if not results:
        return {"results": [], "note": "No matching passages found."}

    return {"results": results}


DOCUMENT_FUNCTION_DEFINITIONS = [
    {
        "name": "list_user_documents",
        "description": "List PDFs the user has uploaded, including previews.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "summarize_user_document",
        "description": "Summarize a specific PDF the user uploaded.",
        "parameters": {
            "type": "object",
            "properties": {
                "document_id": {"type": "string", "description": "ID from list_user_documents"},
            },
            "required": ["document_id"],
        },
    },
    {
        "name": "search_user_documents",
        "description": "Search across all uploaded PDFs for a query.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "What to search for in documents."}
            },
            "required": ["query"],
        },
    },
]
