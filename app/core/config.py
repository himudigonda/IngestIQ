from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Load settings from the .env file
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # OpenAI Credentials
    OPENAI_API_KEY: str
    OPENAI_ENDPOINT: str | None = None
    OPENAI_API_VERSION: str
    OPENAI_EMBEDDINGS_MODEL: str
    OPENAI_CHAT_MODEL: str

    # Database URLs
    DATABASE_URL: str
    MONGO_URL: str
    RABBITMQ_URL: str


# Create a single, reusable instance of the settings
settings = Settings()

# Log the loaded settings for verification (optional but good for debugging)
print("--- Settings Loaded ---")
print(f"Database URL: {settings.DATABASE_URL}")
print(f"RabbitMQ URL: {settings.RABBITMQ_URL}")
print(f"OpenAI Embeddings Model: {settings.OPENAI_EMBEDDINGS_MODEL}")
print("-----------------------")

