import pytest

from app.core.config import Settings
from app.core.logging_config import configure_logging


@pytest.fixture(autouse=True)
def use_test_logging_directory(tmp_path):
    """Route test logs to a temporary folder instead of the real logs directory."""
    configure_logging(
        Settings(
            log_directory=str(tmp_path / "logs"),
            log_file="app-test.log",
            error_log_file="error-test.log",
        )
    )
