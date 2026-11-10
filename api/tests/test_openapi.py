from app.main import app

ERROR_REF = "#/components/schemas/ErrorResponse"


def _ref(path: str, method: str, code: str) -> str:
  response = app.openapi()["paths"][path][method]["responses"][code]
  return response["content"]["application/json"]["schema"]["$ref"]


def test_error_responses_are_typed():
  assert _ref("/api/todos/{item_id}", "get", "404") == ERROR_REF
  assert _ref("/api/todos/{item_id}", "patch", "404") == ERROR_REF
  assert _ref("/api/todos/{item_id}", "patch", "409") == ERROR_REF
  assert _ref("/api/todos/{item_id}", "delete", "404") == ERROR_REF
  assert _ref("/api/auth/me", "get", "401") == ERROR_REF
  assert _ref("/api/auth/login", "post", "401") == ERROR_REF
  assert _ref("/api/auth/register", "post", "409") == ERROR_REF
