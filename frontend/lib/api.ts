export type PropertySummary = {
  id: number;
  address: string;
  city_state: string;
};

export type AgentTask = {
  description: string;
  completed: boolean;
};

export type UserDocument = {
  id: string;
  original_name: string;
  uploaded_at: string;
  preview: string;
  preview_url: string;
};

export type ChatResponse = {
  reply: string;
  user_id: number;
  user_name: string;
  active_property: PropertySummary | null;
  available_properties: PropertySummary[];
  requires_property_selection: boolean;
  tasks: AgentTask[];
};

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export const WELCOME_TRIGGER_MESSAGE = "__homeai_welcome__";

async function parseResponse<T>(response: Response): Promise<T> {
  const text = await response.text();
  let data: any = {};

  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
  }

  if (!response.ok) {
    const detail =
      (typeof data === "object" && data && (data.detail || data.message)) ||
      "Request failed";
    throw new Error(detail);
  }

  return data as T;
}

export async function loginRequest(identifier: string, password: string) {
  const payload = new URLSearchParams();
  payload.set("username", identifier);
  payload.set("password", password);

  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: payload.toString(),
  });

  return parseResponse<{ access_token: string; token_type: string }>(response);
}

export async function sendChat(
  message: string,
  token: string,
  propertyId?: number | null,
) {
  const response = await fetch(`${API_BASE_URL}/agent/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      message,
      property_id: propertyId ?? null,
    }),
  });

  return parseResponse<ChatResponse>(response);
}

export async function fetchWelcomeMessage(token: string) {
  const welcomeResponse = await fetch(`${API_BASE_URL}/agent/welcome`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (welcomeResponse.ok) {
    return parseResponse<ChatResponse>(welcomeResponse);
  }

  const fallbackResponse = await fetch(`${API_BASE_URL}/agent/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      message: WELCOME_TRIGGER_MESSAGE,
      property_id: null,
    }),
  });

  return parseResponse<ChatResponse>(fallbackResponse);
}

export async function fetchDocuments(token: string) {
  const response = await fetch(`${API_BASE_URL}/documents`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  return parseResponse<UserDocument[]>(response);
}

export async function uploadDocument(file: File, token: string) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/documents/upload`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: formData,
  });

  return parseResponse<UserDocument>(response);
}

export async function deleteDocument(documentId: string, token: string) {
  const response = await fetch(`${API_BASE_URL}/documents/${documentId}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "Unable to delete document.");
  }
}

export async function downloadDocument(documentId: string, token: string) {
  const response = await fetch(`${API_BASE_URL}/documents/${documentId}/file`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "Unable to load document preview.");
  }

  return response.blob();
}
