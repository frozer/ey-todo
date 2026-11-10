import type { HttpValidationError } from "../api";

export function isHttpValidationError(item: any): item is HttpValidationError {
  return item && typeof item === 'object' && 'detail' in item && Array.isArray(item.detail);
}

export function convertApiError(error: unknown): Error {
  if (error instanceof Error) {
    return error;
  } else {
    return new Error(String(error))
  }
}