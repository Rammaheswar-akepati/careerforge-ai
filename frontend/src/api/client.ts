export class ApiError extends Error {
  readonly status: number | null;

  constructor(message: string, status: number | null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

interface ApiRequestOptions {
  method?: "GET" | "POST" | "PUT" | "DELETE";
  token?: string;
  jsonBody?: unknown;
  formData?: FormData;
  onUnauthorized?: () => void;
}

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL?.replace(/\/+$/, "");

export async function apiRequest<T>(
  path: string,
  options: ApiRequestOptions = {},
): Promise<T> {
  if (!apiBaseUrl) {
    throw new ApiError("The API address is not configured.", null);
  }

  const headers = new Headers({ Accept: "application/json" });
  if (options.token) {
    headers.set("Authorization", `Bearer ${options.token}`);
  }

  let body: BodyInit | undefined;
  if (options.formData) {
    body = options.formData;
  } else if (options.jsonBody !== undefined) {
    headers.set("Content-Type", "application/json");
    body = JSON.stringify(options.jsonBody);
  }

  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl}${path}`, {
      method: options.method ?? "GET",
      headers,
      body,
    });
  } catch (error) {
    if (error instanceof TypeError) {
      throw new ApiError("Unable to connect. Check your connection and try again.", null);
    }
    throw error;
  }

  if (response.status === 401) {
    options.onUnauthorized?.();
  }

  if (!response.ok) {
    throw new ApiError(await getErrorMessage(response), response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

async function getErrorMessage(response: Response): Promise<string> {
  if (response.status >= 500) {
    return "The service is temporarily unavailable. Please try again later.";
  }

  const responseText = await response.text();
  if (responseText) {
    try {
      const payload: unknown = JSON.parse(responseText);
      if (typeof payload === "object" && payload !== null && "detail" in payload) {
        const detail = (payload as { detail: unknown }).detail;
        if (typeof detail === "string" && detail.trim()) {
          return detail;
        }
        if (Array.isArray(detail)) {
          return "Some submitted information is invalid. Review the fields and try again.";
        }
      }
    } catch (error) {
      if (!(error instanceof SyntaxError)) {
        throw error;
      }
    }
  }

  return "The request could not be completed. Please review your information and try again.";
}
