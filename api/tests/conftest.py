import pytest
from src.config import Settings
import src.config

@pytest.fixture(autouse=True)
def mock_config(monkeypatch):
  fake_settings = Settings(database_path = ".", jwt_secret = "my_test_jwt_secret_aaaabbbbcccc_dddd_eeee")
  
  def fake_get_settings(*args, **kwargs):
        return fake_settings
  
  monkeypatch.setattr(src.auth.security, "get_settings", lambda *args, **kwargs: fake_settings)
