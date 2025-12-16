"use client";

import ChatPanel from "../components/ChatPanel";
import LoginForm from "../components/LoginForm";
import { useAuth } from "../components/AuthContext";

export default function HomePage() {
  const { token } = useAuth();

  return (
    <main className="home-container">
      <div className="card">
        <header>
          <h1>HomeAI Assistant</h1>
          <p>Log in to chat about your properties.</p>
        </header>
        {token ? <ChatPanel /> : <LoginForm />}
      </div>
    </main>
  );
}
