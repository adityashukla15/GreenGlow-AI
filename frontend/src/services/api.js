const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000"
).replace(/\/+$/, "");

export class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function messageForStatus(status) {
  if (status === 404) {
    return "No existing user record was found. Entering an email does not register you; completing a quiz may create a profile.";
  }
  if (status === 422) {
    return "Some information was not accepted. Check it and try again.";
  }
  if (status === 503 || status >= 500) {
    return "GreenGlow is temporarily unavailable. Please try again shortly.";
  }
  return "The request could not be completed. Please try again.";
}

export async function request(path, options = {}) {
  const { body, headers = {}, ...requestOptions } = options;
  const requestHeaders = new Headers(headers);
  let requestBody = body;

  if (body !== undefined && body !== null && typeof body !== "string") {
    requestHeaders.set("Content-Type", "application/json");
    requestBody = JSON.stringify(body);
  }

  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...requestOptions,
      headers: requestHeaders,
      body: requestBody,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw error;
    }
    throw new ApiError(
      0,
      "Unable to reach GreenGlow. Check your connection and try again.",
    );
  }

  const responseText = await response.text();
  let data = null;
  if (responseText) {
    try {
      data = JSON.parse(responseText);
    } catch {
      data = null;
    }
  }

  if (!response.ok) {
    throw new ApiError(response.status, messageForStatus(response.status));
  }

  return data;
}
