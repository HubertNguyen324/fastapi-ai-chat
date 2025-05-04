from pydantic_settings import BaseSettings, SettingsConfigDict
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env file.
    """

    session_timeout_minutes: int = 30  # Default timeout if not set in .env

    # Configuration for loading settings
    model_config = SettingsConfigDict(
        env_file=".env",  # Specify the .env file name
        env_file_encoding="utf-8",  # Encoding of the .env file
        extra="ignore",  # Ignore extra fields not defined in the model
    )


# Create a single, importable instance of the settings
try:
    settings = Settings()
    logger.info(
        f"Settings loaded: Session timeout = {settings.session_timeout_minutes} minutes"
    )
except Exception as e:
    logger.error(f"Failed to load settings: {e}", exc_info=True)
    # Fallback to defaults if loading fails critically
    settings = Settings(session_timeout_minutes=30)
    logger.warning("Using default settings due to loading error.")

# Example usage elsewhere: from app.config import settings
# print(settings.session_timeout_minutes)
