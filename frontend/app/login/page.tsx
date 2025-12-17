"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import LoginForm from "../../components/LoginForm";
import { useAuth } from "../../components/AuthContext";

export default function LoginPage() {
  const { token, isReady } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isReady && token) {
      router.replace("/");
    }
  }, [isReady, token, router]);

  if (!isReady || token) {
    return null;
  }

  return (
    <main className="home-container">
      <div className="card">
        <header>
          <img src="/homeai.png" alt="HomeAI" style={{ height: 48 }} />{" "}
          <p>Log in to chat with your HomeAI assistant.</p>
        </header>
        <LoginForm />
      </div>
    </main>
  );
}
