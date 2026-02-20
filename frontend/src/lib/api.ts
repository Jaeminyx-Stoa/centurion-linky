const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface FetchOptions extends RequestInit {
  token?: string;
}

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

const MAX_RETRIES = 3;
const BASE_DELAY_MS = 500;

async function request<T>(
  path: string,
  options: FetchOptions = {},
): Promise<T> {
  const { token, headers, ...rest } = options;

  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
    try {
      const res = await fetch(`${API_BASE_URL}${path}`, {
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
          ...headers,
        },
        ...rest,
      });

      if (res.status >= 500 && attempt < MAX_RETRIES) {
        lastError = new ApiError(res.status, `Server error ${res.status}`);
        await new Promise((r) => setTimeout(r, BASE_DELAY_MS * 2 ** attempt));
        continue;
      }

      if (!res.ok) {
        const body = await res.json().catch(() => ({ detail: res.statusText }));
        throw new ApiError(res.status, body.detail || res.statusText);
      }

      if (res.status === 204) {
        return undefined as T;
      }

      return res.json();
    } catch (err) {
      if (err instanceof ApiError && err.status < 500) {
        throw err;
      }
      lastError = err as Error;
      if (attempt < MAX_RETRIES) {
        await new Promise((r) => setTimeout(r, BASE_DELAY_MS * 2 ** attempt));
      }
    }
  }

  throw lastError || new Error("Request failed");
}

export function buildPaginationParams(
  page: number,
  pageSize: number,
): string {
  const offset = (page - 1) * pageSize;
  return `limit=${pageSize}&offset=${offset}`;
}

export const api = {
  get: <T>(path: string, options?: FetchOptions) =>
    request<T>(path, { ...options, method: "GET" }),

  post: <T>(path: string, body: unknown, options?: FetchOptions) =>
    request<T>(path, { ...options, method: "POST", body: JSON.stringify(body) }),

  patch: <T>(path: string, body: unknown, options?: FetchOptions) =>
    request<T>(path, { ...options, method: "PATCH", body: JSON.stringify(body) }),

  delete: <T>(path: string, options?: FetchOptions) =>
    request<T>(path, { ...options, method: "DELETE" }),
};

export { ApiError };
