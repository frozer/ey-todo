import type { HttpValidationError } from "../api";

export function isHttpValidationError(item: unknown): item is HttpValidationError {
  return typeof item === 'object' && item !== null && 'detail' in item && Array.isArray(item.detail);
}

// API errors look like {"detail": [{"msg": "..."}, ...]} (ErrorResponse and HTTPValidationError)
export function convertApiError(error: unknown): Error {
  if (error instanceof Error) {
    return error;
  }

  if (isHttpValidationError(error)) {
    const messages = (error.detail ?? []).map(item => item.msg).filter(Boolean);
    if (messages.length) {
      return new Error(messages.join(', '));
    }
  }

  return new Error(typeof error === 'string' ? error : JSON.stringify(error));
}
