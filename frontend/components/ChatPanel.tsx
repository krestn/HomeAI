"use client";

import { FormEvent, useMemo, useState } from "react";
import { sendChat, type ChatResponse, type PropertySummary } from "../lib/api";
import { useAuth } from "./AuthContext";

type Message = {
  id: string;
  role: "user" | "assistant";
  text: string;
};

let messageCounter = 0;

export default function ChatPanel() {
  const { token, logout } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [sendError, setSendError] = useState<string | null>(null);
  const [properties, setProperties] = useState<PropertySummary[]>([]);
  const [activePropertyId, setActivePropertyId] = useState<number | null>(null);
  const [requiresSelection, setRequiresSelection] = useState(false);

  const activeProperty = useMemo(
    () => properties.find((property) => property.id === activePropertyId) ?? null,
    [properties, activePropertyId],
  );

  if (!token) {
    return null;
  }

  const handleSend = async (event: FormEvent<HTMLFormElement> | null = null) => {
    event?.preventDefault();
    if (!input.trim()) {
      setSendError("Say something to your assistant first.");
      return;
    }

    setSendError(null);
    const outgoingMessage: Message = {
      id: `msg-${messageCounter++}`,
      role: "user",
      text: input.trim(),
    };

    setMessages((prev) => [...prev, outgoingMessage]);
    const currentInput = input;
    setInput("");
    setIsSending(true);

    try {
      const response = await sendChat(currentInput, token, activePropertyId);
      handleChatResponse(response);
    } catch (error) {
      if (error instanceof Error) {
        setSendError(error.message);
      } else {
        setSendError("Unable to reach HomeAI.");
      }
    } finally {
      setIsSending(false);
    }
  };

  const handleChatResponse = (response: ChatResponse) => {
    const incomingMessage: Message = {
      id: `msg-${messageCounter++}`,
      role: "assistant",
      text: response.reply,
    };

    setMessages((prev) => [...prev, incomingMessage]);
    setProperties(response.available_properties ?? []);
    setActivePropertyId(response.active_property?.id ?? null);
    setRequiresSelection(response.requires_property_selection ?? false);
  };

  const handleSelectProperty = (propertyId: number) => {
    setActivePropertyId(propertyId);
    setRequiresSelection(false);
  };

  return (
    <>
      <div className="chat-wrapper">
        <section className="chat-box">
          <div className="chat-messages">
            {messages.length === 0 && (
              <div className="message assistant">
                Ask about your property, local services, or value estimates to get
                started.
              </div>
            )}
            {messages.map((message) => (
              <div key={message.id} className={`message ${message.role}`}>
                <strong>{message.role === "user" ? "You" : "HomeAI"}</strong>
                <div>{message.text}</div>
              </div>
            ))}
          </div>
          <form className="chat-input" onSubmit={handleSend}>
            <textarea
              placeholder="Type your question…"
              value={input}
              onChange={(event) => setInput(event.target.value)}
              disabled={isSending}
            />
            <button type="submit" disabled={isSending}>
              {isSending ? "Sending…" : "Send"}
            </button>
          </form>
        </section>

        <aside className="properties-panel">
          <div>
            <h3>Properties</h3>
            {requiresSelection && (
              <p className="error-text">
                Please select a property before asking again.
              </p>
            )}
          </div>
          {properties.length === 0 ? (
            <p>No properties returned yet. Send a message to get started.</p>
          ) : (
            properties.map((property) => (
              <article
                key={property.id}
                className={`property-card${
                  property.id === activePropertyId ? " active" : ""
                }`}
                onClick={() => handleSelectProperty(property.id)}
              >
                <p>
                  <strong>#{property.id}</strong>
                </p>
                <p>{property.address}</p>
                <p>{property.city_state}</p>
              </article>
            ))
          )}
        </aside>
      </div>
      {sendError && <p className="error-text">{sendError}</p>}
      <div className="chat-actions">
        <div>
          {activeProperty ? (
            <p>
              Chatting about: <strong>{activeProperty.address}</strong>
            </p>
          ) : (
            <p>No property selected.</p>
          )}
        </div>
        <button className="logout-button" onClick={logout}>
          Logout
        </button>
      </div>
    </>
  );
}
