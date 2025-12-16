export type PropertySummary = {
  id: number;
  address: string;
  city_state: string;
};

export type ChatResponse = {
  reply: string;
  user_id: number;
  active_property: PropertySummary | null;
  available_properties: PropertySummary[];
  requires_property_selection: boolean;
};

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

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
