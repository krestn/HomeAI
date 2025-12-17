"use client";

import {
  FormEvent,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import {
  fetchWelcomeMessage,
  sendChat,
  type AgentTask,
  type ChatResponse,
  type PropertySummary,
} from "../lib/api";
import { useAuth } from "./AuthContext";

type Message = {
  id: string;
  role: "user" | "assistant";
  text: string;
};

type ServiceLinkHandlers = {
  onAddressClick?: (payload: { name: string; address: string }) => void;
  onPhoneClick?: (payload: { name: string; phone: string; dial: string }) => void;
  onWebsiteClick?: (payload: { name: string; website: string }) => void;
  onRatingClick?: (payload: { name: string; address: string; rating: string }) => void;
};

type PanelView =
  | {
      type: "maps";
      name: string;
      address: string;
      embedUrl: string;
      externalUrl: string;
    }
  | { type: "website"; name: string; embedUrl: string }
  | { type: "call"; name: string; phone: string; dial: string }
  | {
      type: "reviews";
      name: string;
      embedUrl: string;
      externalUrl: string;
    };

let messageCounter = 0;
const linkRegex =
  /((https?:\/\/[^\s]+)|(www\.[^\s]+)|([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})|(\+?\d[\d().\s-]{6,}\d))/gi;

function linkifyTextSegment(segment: string, keyPrefix: string) {
  const elements: ReactNode[] = [];
  let lastIndex = 0;

  segment.replace(linkRegex, (match) => {
    const index = segment.indexOf(match, lastIndex);
    if (index > lastIndex) {
      elements.push(segment.slice(lastIndex, index));
    }

    let href = "";
    if (match.includes("@") && !match.toLowerCase().startsWith("http")) {
      href = `mailto:${match}`;
    } else if (match.toLowerCase().startsWith("http")) {
      href = match;
    } else if (match.toLowerCase().startsWith("www.")) {
      href = `https://${match}`;
    } else {
      const digits = match.replace(/[^\d+]/g, "");
      href = `tel:${digits}`;
    }

    elements.push(
      <a
        key={`${keyPrefix}-${match}-${index}`}
        href={href}
        target="_blank"
        rel="noreferrer"
      >
        {match}
      </a>
    );
    lastIndex = index + match.length;
    return match;
  });

  if (lastIndex < segment.length) {
    elements.push(segment.slice(lastIndex));
  }

  return elements;
}

function buildMapsLink(address: string) {
  return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
    address
  )}`;
}

function buildMapsEmbedUrl(address: string) {
  return `https://www.google.com/maps?q=${encodeURIComponent(address)}&output=embed`;
}

function buildReviewsEmbedUrl(name: string, address: string) {
  const query = `${name} ${address} reviews`;
  return `https://www.google.com/maps?q=${encodeURIComponent(query)}&output=embed`;
}

function buildReviewsExternalUrl(name: string, address: string) {
  const query = `${name} ${address} reviews`;
  return `https://www.google.com/search?q=${encodeURIComponent(query)}`;
}

function ensureWebsiteUrl(website: string) {
  if (!website) {
    return "";
  }
  return website.toLowerCase().startsWith("http")
    ? website
    : `https://${website}`;
}

function formatMessageText(text: string, handlers?: ServiceLinkHandlers) {
  const serviceRegex =
    /([^\n]+)\n\s+- Address: ([^\n]+)\n\s+- Phone: ([^\n]+)\n\s+- Website: ([^\n]+)\n\s+- Rating: ([^\n]+)/g;

  const elements: React.ReactNode[] = [];
  let lastIndex = 0;

  text.replace(
    serviceRegex,
    (
      match,
      name,
      address,
      phone,
      website,
      rating,
      offset
    ) => {
      if (offset > lastIndex) {
        const before = text.slice(lastIndex, offset);
        elements.push(
          ...linkifyTextSegment(before, `text-${lastIndex}-${offset}`)
        );
      }

      const hasAddressLink = address !== "Address unavailable";
      const hasPhoneLink = phone !== "N/A";
      const hasWebsite = website !== "N/A" && Boolean(website.trim());
      const hasRating = rating !== "N/A";
      const trimmedName = name.trim();
      const sanitizedDial = phone.replace(/[^\d+]/g, "");
      const normalizedWebsite = ensureWebsiteUrl(website);

      const addressNode = hasAddressLink
        ? handlers?.onAddressClick
          ? (
              <button
                type="button"
                className="service-link"
                onClick={() =>
                  handlers.onAddressClick?.({
                    name: trimmedName,
                    address,
                  })
                }
              >
                {address}
              </button>
            )
          : (
              <a
                href={buildMapsLink(address)}
                target="_blank"
                rel="noreferrer"
              >
                {address}
              </a>
            )
        : address;

      const phoneNode = hasPhoneLink
        ? handlers?.onPhoneClick
          ? (
              <button
                type="button"
                className="service-link"
                onClick={() =>
                  handlers.onPhoneClick?.({
                    name: trimmedName,
                    phone,
                    dial: sanitizedDial,
                  })
                }
              >
                {phone}
              </button>
            )
          : (
              <a href={`tel:${sanitizedDial}`}>{phone}</a>
            )
        : phone;

      const websiteNode = hasWebsite
        ? handlers?.onWebsiteClick
          ? (
              <button
                type="button"
                className="service-link"
                onClick={() =>
                  handlers.onWebsiteClick?.({
                    name: trimmedName,
                    website: normalizedWebsite,
                  })
                }
              >
                {website}
              </button>
            )
          : (
              <a href={normalizedWebsite} target="_blank" rel="noreferrer">
                {website}
              </a>
            )
        : website;

      const ratingNode = hasRating
        ? handlers?.onRatingClick
          ? (
              <button
                type="button"
                className="service-link"
                onClick={() =>
                  handlers.onRatingClick?.({
                    name: trimmedName,
                    address,
                    rating,
                  })
                }
              >
                {`${rating} ⭐`}
              </button>
            )
          : `${rating} ⭐`
        : rating;

      elements.push(
        <div key={`service-${offset}`} className="service-result">
          <div className="service-name">{name.trim()}</div>
          <ul>
            <li>
              <span>Address:</span>{" "}
              {addressNode}
            </li>
            <li>
              <span>Phone:</span>{" "}
              {phoneNode}
            </li>
            <li>
              <span>Website:</span>{" "}
              {websiteNode}
            </li>
            <li>
              <span>Rating:</span> {ratingNode}
            </li>
          </ul>
        </div>
      );

      lastIndex = offset + match.length;
      return match;
    }
  );

  if (elements.length === 0) {
    return linkifyTextSegment(text, "plain");
  }

  if (lastIndex < text.length) {
    const remaining = text.slice(lastIndex);
    elements.push(...linkifyTextSegment(remaining, `tail-${lastIndex}`));
  }

  return elements;
}

export default function ChatPanel({
  sideContent,
  onTasksUpdate,
  sidebarKey,
}: {
  sideContent?: ReactNode;
  onTasksUpdate?: (tasks: AgentTask[]) => void;
  sidebarKey?: string;
}) {
  const { token } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [sendError, setSendError] = useState<string | null>(null);
  const [properties, setProperties] = useState<PropertySummary[]>([]);
  const [activePropertyId, setActivePropertyId] = useState<number | null>(null);
  const [requiresSelection, setRequiresSelection] = useState(false);
  const [hasLoadedWelcome, setHasLoadedWelcome] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const typingDelayRef = useRef<number | null>(null);
  const [panelView, setPanelView] = useState<PanelView | null>(null);

  const activeProperty = useMemo(
    () =>
      properties.find((property) => property.id === activePropertyId) ?? null,
    [properties, activePropertyId]
  );

  const handleSend = async (
    event: FormEvent<HTMLFormElement> | null = null
  ) => {
    event?.preventDefault();
    if (!hasLoadedWelcome) {
      return;
    }
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
      await handleChatResponse(response);
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
    return new Promise<void>((resolve) => {
      if (typingDelayRef.current) {
        window.clearTimeout(typingDelayRef.current);
      }
      typingDelayRef.current = window.setTimeout(() => {
        const incomingMessage: Message = {
          id: `msg-${messageCounter++}`,
          role: "assistant",
          text: response.reply,
        };

        setMessages((prev) => [...prev, incomingMessage]);
        setProperties(response.available_properties ?? []);
        onTasksUpdate?.(response.tasks ?? []);
        setActivePropertyId(response.active_property?.id ?? null);
        setRequiresSelection(response.requires_property_selection ?? false);
        typingDelayRef.current = null;
        resolve();
      }, 2000);
    });
  };

  const handleSelectProperty = (propertyId: number) => {
    setActivePropertyId(propertyId);
    setRequiresSelection(false);
  };

  useEffect(() => {
    if (!token) {
      setMessages([]);
      setHasLoadedWelcome(false);
      setPanelView(null);
      onTasksUpdate?.([]);
      messageCounter = 0;
    }
  }, [token, onTasksUpdate]);

  useEffect(() => {
    if (!token || hasLoadedWelcome) {
      return;
    }

    let cancelled = false;
    const loadWelcome = async () => {
      try {
        const response = await fetchWelcomeMessage(token);
        if (cancelled) {
          return;
        }
        const intro: Message = {
          id: `msg-${messageCounter++}`,
          role: "assistant",
          text: response.reply,
        };
        setMessages([intro]);
        onTasksUpdate?.(response.tasks ?? []);
        setSendError(null);
      } catch (error) {
        if (!cancelled) {
          setSendError(
            error instanceof Error
              ? error.message
              : "Unable to load welcome message."
          );
        }
      } finally {
        if (!cancelled) {
          setHasLoadedWelcome(true);
        }
      }
    };

    void loadWelcome();

    return () => {
      cancelled = true;
    };
  }, [token, hasLoadedWelcome, onTasksUpdate]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isSending]);

  useEffect(
    () => () => {
      if (typingDelayRef.current) {
        window.clearTimeout(typingDelayRef.current);
      }
    },
    []
  );

  useEffect(() => {
    if (sidebarKey !== undefined) {
      setPanelView(null);
    }
  }, [sidebarKey]);

  const serviceHandlers: ServiceLinkHandlers = {
    onAddressClick: ({ name, address }) => {
      setPanelView({
        type: "maps",
        name,
        address,
        embedUrl: buildMapsEmbedUrl(address),
        externalUrl: buildMapsLink(address),
      });
    },
    onPhoneClick: ({ name, phone, dial }) => {
      setPanelView({
        type: "call",
        name,
        phone,
        dial,
      });
    },
    onWebsiteClick: ({ name, website }) => {
      setPanelView({
        type: "website",
        name,
        embedUrl: website,
      });
    },
    onRatingClick: ({ name, address }) => {
      setPanelView({
        type: "reviews",
        name,
        embedUrl: buildReviewsEmbedUrl(name, address),
        externalUrl: buildReviewsExternalUrl(name, address),
      });
    },
  };

  const isButtonDisabled = isSending || !hasLoadedWelcome;
  const buttonAriaLabel = !hasLoadedWelcome
    ? "Loading assistant"
    : isSending
    ? "Sending message"
    : "Send message";
  const buttonContent =
    !hasLoadedWelcome || isSending ? (
      <span className="send-icon send-icon--loading">...</span>
    ) : (
      <span className="send-icon" aria-hidden="true">
        ↑
      </span>
    );

  if (!token) {
    return null;
  }

  const renderSidePanelContent = () => {
    if (!panelView) {
      if (sideContent) {
        return sideContent;
      }
      return (
        <div className="panel-placeholder">
          <p>Select a tab or tap a link in chat to preview it here.</p>
        </div>
      );
    }

    const closeButton = (
      <button
        type="button"
        className="panel-close"
        onClick={() => setPanelView(null)}
      >
        Close
      </button>
    );

    if (panelView.type === "maps") {
      return (
        <div className="panel-embed">
          <div className="panel-embed__header">
            <div>
              <p className="panel-eyebrow">Google Maps Preview</p>
              <h3>{panelView.name}</h3>
              <p className="panel-subtitle">{panelView.address}</p>
            </div>
            {closeButton}
          </div>
          <iframe
            title={`Map for ${panelView.name}`}
            src={panelView.embedUrl}
            className="panel-iframe"
            loading="lazy"
            allowFullScreen
          />
          <a
            className="panel-link"
            href={panelView.externalUrl}
            target="_blank"
            rel="noreferrer"
          >
            Open in Google Maps
          </a>
        </div>
      );
    }

    if (panelView.type === "website") {
      return (
        <div className="panel-embed">
          <div className="panel-embed__header">
            <div>
              <p className="panel-eyebrow">Website Preview</p>
              <h3>{panelView.name}</h3>
            </div>
            {closeButton}
          </div>
          <iframe
            title={`Website for ${panelView.name}`}
            src={panelView.embedUrl}
            className="panel-iframe"
            sandbox="allow-same-origin allow-scripts allow-popups allow-forms"
          />
          <p className="panel-note">
            Some websites block in-app previews.{" "}
            <a href={panelView.embedUrl} target="_blank" rel="noreferrer">
              Open in new tab.
            </a>
          </p>
        </div>
      );
    }

    if (panelView.type === "call") {
      return (
        <div className="panel-call">
          <div className="panel-embed__header">
            <div>
              <p className="panel-eyebrow">Call Provider</p>
              <h3>{panelView.name}</h3>
            </div>
            {closeButton}
          </div>
          <p className="panel-subtitle">Tap below to start a call:</p>
          <a className="call-link" href={`tel:${panelView.dial}`}>
            {panelView.phone}
          </a>
          <p className="panel-note">
            We'll open your default phone app when you tap the number.
          </p>
        </div>
      );
    }

    return (
      <div className="panel-embed">
        <div className="panel-embed__header">
          <div>
            <p className="panel-eyebrow">Google Reviews</p>
            <h3>{panelView.name}</h3>
          </div>
          {closeButton}
        </div>
        <iframe
          title={`Reviews for ${panelView.name}`}
          src={panelView.embedUrl}
          className="panel-iframe"
          loading="lazy"
        />
        <a
          className="panel-link"
          href={panelView.externalUrl}
          target="_blank"
          rel="noreferrer"
        >
          View full Google reviews
        </a>
      </div>
    );
  };

  return (
    <>
      <div className="chat-wrapper">
        <section className="chat-box">
          <div className="chat-messages">
            {messages.length === 0 && (
              <div className="message assistant">
                Ask about your property, local services, or value estimates to
                get started.
              </div>
            )}
            {messages.map((message) => (
              <div key={message.id} className={`message ${message.role}`}>
                <strong>{message.role === "user" ? "" : "HomeAI"}</strong>
                <div className="chat-message">
                  {formatMessageText(message.text, serviceHandlers)}
                </div>
              </div>
            ))}
            {isSending && (
              <div className="message assistant typing">
                <strong>HomeAI</strong>
                <div className="chat-message typing-indicator">
                  <span />
                  <span />
                  <span />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
          <form className="chat-input" onSubmit={handleSend}>
            <textarea
              placeholder={
                hasLoadedWelcome
                  ? "Type your question…"
                  : "Loading your assistant…"
              }
              value={input}
              onChange={(event) => setInput(event.target.value)}
              disabled={isButtonDisabled}
            />
            <button
              type="submit"
              disabled={isButtonDisabled}
              aria-label={buttonAriaLabel}
              title={buttonAriaLabel}
            >
              {buttonContent}
            </button>
          </form>
        </section>

        <aside className="side-panel">{renderSidePanelContent()}</aside>
      </div>
      {/* {sendError && <p className="error-text">{sendError}</p>} */}
    </>
  );
}
