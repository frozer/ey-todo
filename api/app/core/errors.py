from typing import Any

from pydantic import BaseModel


class ErrorItem(BaseModel):
  msg: str


class ErrorResponse(BaseModel):
  """Body of every non-validation error: {"detail": [{"msg": "..."}]}."""
  detail: list[ErrorItem]


def error_responses(*codes: tuple[int, str]) -> dict[int | str, dict[str, Any]]:
  """OpenAPI `responses` for the given (status_code, description) pairs."""
  return {
    code: {"model": ErrorResponse, "description": description}
    for code, description in codes
  }
