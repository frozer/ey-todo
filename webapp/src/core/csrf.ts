// CSRF synchronizer token of the current session. Kept in memory only:
// the root loader refreshes it from /auth/me on every page load.
let csrfToken: string | null = null;

export const CSRF_HEADER = 'X-CSRF-Token';

const UNSAFE_METHODS = new Set(['POST', 'PUT', 'PATCH', 'DELETE']);

export function getCsrfToken(): string | null {
  return csrfToken;
}

export function setCsrfToken(token: string | null): void {
  csrfToken = token;
}

export function withCsrfHeader(request: Request): Request {
  if (csrfToken && UNSAFE_METHODS.has(request.method.toUpperCase())) {
    request.headers.set(CSRF_HEADER, csrfToken);
  }
  return request;
}
