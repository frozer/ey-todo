import type { HttpValidationError } from "../api";

export function isHttpValidationError(item: any): item is HttpValidationError {
  return item && typeof item === 'object' && 'detail' in item && Array.isArray(item.detail);
}