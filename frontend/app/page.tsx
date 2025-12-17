"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import ChatPanel from "../components/ChatPanel";
import { useAuth } from "../components/AuthContext";
import { LogOut } from "lucide-react";
import type { AgentTask } from "../lib/api";

export default function HomePage() {
  const { token, isReady, logout } = useAuth();
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<
    "home" | "service" | "documents" | "tasks"
  >("home");
  const [tasks, setTasks] = useState<AgentTask[]>([]);

  useEffect(() => {
    if (isReady && !token) {
      router.replace("/login");
    }
  }, [isReady, token, router]);

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
          <div>
            <h3>Documents</h3>
            <p>Review contracts, closing docs, and receipts in one place.</p>
            <p>Document storage is coming soon.</p>
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
  }, [activeTab, tasks]);

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
