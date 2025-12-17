"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import ChatPanel from "../components/ChatPanel";
import { useAuth } from "../components/AuthContext";
import { LogOut } from "lucide-react";
import type { AgentTask, UserDocument } from "../lib/api";
import {
  deleteDocument,
  downloadDocument,
  fetchDocuments,
  uploadDocument,
} from "../lib/api";

export default function HomePage() {
  const { token, isReady, logout } = useAuth();
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<
    "home" | "service" | "documents" | "tasks"
  >("home");
  const [tasks, setTasks] = useState<AgentTask[]>([]);
  const [documents, setDocuments] = useState<UserDocument[]>([]);
  const [documentsLoading, setDocumentsLoading] = useState(false);
  const [docError, setDocError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [documentsVersion, setDocumentsVersion] = useState(0);
  const [docPreviews, setDocPreviews] = useState<Record<string, string>>({});
  const previewRef = useRef<Record<string, string>>({});

  useEffect(() => {
    if (isReady && !token) {
      router.replace("/login");
    }
  }, [isReady, token, router]);

  useEffect(() => {
    previewRef.current = docPreviews;
  }, [docPreviews]);

  useEffect(() => {
    return () => {
      Object.values(previewRef.current).forEach((url) => {
        URL.revokeObjectURL(url);
      });
    };
  }, []);

  const loadDocuments = useCallback(async () => {
    if (!token) {
      return;
    }
    try {
      setDocumentsLoading(true);
      setDocError(null);
      const data = await fetchDocuments(token);
      setDocuments(data);
      setDocPreviews((prev) => {
        const allowed = new Set(data.map((doc) => doc.id));
        const next: Record<string, string> = {};
        Object.entries(prev).forEach(([id, url]) => {
          if (allowed.has(id)) {
            next[id] = url;
          } else {
            URL.revokeObjectURL(url);
          }
        });
        return next;
      });
    } catch (error) {
      setDocError(
        error instanceof Error ? error.message : "Unable to load documents."
      );
    } finally {
      setDocumentsLoading(false);
    }
  }, [token]);

  useEffect(() => {
    if (token && activeTab === "documents") {
      void loadDocuments();
    }
  }, [token, activeTab, documentsVersion, loadDocuments]);

  useEffect(() => {
    if (!token || activeTab !== "documents") {
      return;
    }
    let cancelled = false;

    const loadPreviews = async () => {
      for (const doc of documents) {
        if (previewRef.current[doc.id]) {
          continue;
        }
        try {
          const blob = await downloadDocument(doc.id, token);
          if (cancelled) {
            return;
          }
          const objectUrl = URL.createObjectURL(blob);
          setDocPreviews((prev) => ({
            ...prev,
            [doc.id]: objectUrl,
          }));
        } catch (error) {
          if (!cancelled) {
            setDocError(
              error instanceof Error
                ? error.message
                : "Unable to load preview."
            );
          }
        }
      }
    };

    void loadPreviews();

    return () => {
      cancelled = true;
    };
  }, [documents, token, activeTab]);

  const handleDocumentUpload = async (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    if (!token) {
      return;
    }
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    if (file.type !== "application/pdf") {
      setDocError("Only PDF files are supported right now.");
      event.target.value = "";
      return;
    }

    setIsUploading(true);
    setDocError(null);
    try {
      await uploadDocument(file, token);
      setDocumentsVersion((prev) => prev + 1);
    } catch (error) {
      setDocError(
        error instanceof Error ? error.message : "Unable to upload document."
      );
    } finally {
      setIsUploading(false);
      event.target.value = "";
    }
  };

  const handleDeleteDocument = async (documentId: string) => {
    if (!token) {
      return;
    }
    try {
      await deleteDocument(documentId, token);
      setDocumentsVersion((prev) => prev + 1);
      setDocPreviews((prev) => {
        const { [documentId]: removed, ...rest } = prev;
        if (removed) {
          URL.revokeObjectURL(removed);
        }
        return rest;
      });
    } catch (error) {
      setDocError(
        error instanceof Error ? error.message : "Unable to delete document."
      );
    }
  };

  const sideContent = useMemo(() => {
    switch (activeTab) {
      case "service":
        return (
          <div>
            <h3>Service Center</h3>
            <p>Schedule repairs, manage vendors, and monitor open tickets.</p>
            <p>This placeholder will be replaced with live service tools.</p>
          </div>
        );
      case "documents":
        return (
          <div className="documents-panel">
            <h3>Documents</h3>
            <p>
              Upload inspection reports, appraisals, and receipts for HomeAI to
              reference.
            </p>
            <div className="document-upload">
              <label
                className={`upload-button${isUploading ? " disabled" : ""}`}
              >
                <input
                  type="file"
                  accept="application/pdf"
                  onChange={handleDocumentUpload}
                  disabled={isUploading}
                />
                {isUploading ? "Uploading…" : "Upload PDF"}
              </label>
            </div>
              {docError && <p className="document-error">{docError}</p>}
              {documentsLoading ? (
                <p>Loading documents…</p>
              ) : documents.length === 0 ? (
                <p className="task-empty">
                  No documents yet. Upload a PDF or ask HomeAI to analyze one.
                </p>
              ) : (
                <ul className="document-list">
                  {documents.map((doc) => (
                    <li key={doc.id} className="document-card">
                      <button
                        type="button"
                        className="document-delete"
                        aria-label={`Delete ${doc.original_name}`}
                        onClick={() => handleDeleteDocument(doc.id)}
                      >
                        ×
                      </button>
                      <div className="document-card__meta">
                        <strong>{doc.original_name}</strong>
                        <span>
                          {new Date(doc.uploaded_at).toLocaleDateString("en-US", {
                            month: "short",
                            day: "numeric",
                            year: "numeric",
                          })}
                        </span>
                      </div>
                      <div className="document-frame-wrapper">
                        {docPreviews[doc.id] ? (
                          <iframe
                            src={docPreviews[doc.id]}
                            title={doc.original_name}
                            className="document-frame"
                          />
                        ) : (
                          <p>Preparing preview…</p>
                        )}
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>
        );
      case "tasks":
        return (
          <div>
            <h3>Tasks</h3>
            {tasks.length === 0 ? (
              <p className="task-empty">No tasks yet. Ask HomeAI to remind you about something!</p>
            ) : (
              <ul className="task-list">
                {tasks.map((task) => (
                  <li
                    key={task.description}
                    className={`task-item${task.completed ? " completed" : ""}`}
                  >
                    <span>{task.description}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        );
      default:
        return (
          <div>
            <h3>Home Overview</h3>
            <p>Use the chat on the left to talk with your HomeAI assistant.</p>
            <p>Select a different tab to preview upcoming workflows.</p>
          </div>
        );
    }
  }, [
    activeTab,
    tasks,
    docError,
    documents,
    documentsLoading,
    isUploading,
    docPreviews,
  ]);

  const tabs = [
    { id: "home", label: "Home" },
    { id: "service", label: "Service" },
    { id: "documents", label: "Documents" },
    { id: "tasks", label: "Tasks" },
  ] as const;

  if (!isReady || !token) {
    return null;
  }

  return (
    <main className="home-container">
      <div className="app-shell">
        <nav className="top-nav">
          <div className="nav-logo" aria-label="HomeAI logo">
            <img src="/homeai.png" alt="HomeAI" style={{ height: 24 }} />
          </div>
          <div className="nav-links">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                className={`nav-link${activeTab === tab.id ? " active" : ""}`}
                onClick={() => setActiveTab(tab.id)}
                type="button"
              >
                {tab.label}
              </button>
            ))}
            <button
              className="nav-logout"
              onClick={logout}
              type="button"
              aria-label="Log out"
            >
              <LogOut size={20} />
            </button>
          </div>
        </nav>
        <div className="card">
          <ChatPanel
            sideContent={sideContent}
            onTasksUpdate={setTasks}
            sidebarKey={activeTab}
          />
        </div>
      </div>
    </main>
  );
}
