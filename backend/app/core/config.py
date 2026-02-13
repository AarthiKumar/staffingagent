"""Application configuration using pydantic-settings"""
import os
from pathlib import Path
from typing import Optional

import yaml
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Main application settings"""

    # Support running backend from either repository root or backend/ directory.
    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = Field(default="dev", alias="APP_ENV")
    database_url: str = Field(alias="DATABASE_URL")

    minio_endpoint: str = Field(default="http://localhost:9000", alias="MINIO_ENDPOINT")
    minio_access_key: str = Field(default="minioadmin", alias="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(default="minioadmin", alias="MINIO_SECRET_KEY")
    minio_bucket: str = Field(default="originals", alias="MINIO_BUCKET")
    storage_local_path: str = Field(default="./data/originals", alias="STORAGE_LOCAL_PATH")

    embeddings_model: str = Field(default="text-embedding-3-small", alias="EMBEDDINGS_MODEL")
    embeddings_provider: str = Field(default="openai", alias="EMBEDDINGS_PROVIDER")
    llm_provider: str = Field(default="disabled", alias="LLM_PROVIDER")
    llm_api_key: Optional[str] = Field(default=None, alias="LLM_API_KEY")
    enable_llm_rerank: bool = Field(default=False, alias="ENABLE_LLM_RERANK")
    enable_nl_assist: bool = Field(default=False, alias="ENABLE_NL_ASSIST")

    # Auth0 Configuration
    auth0_domain: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("AUTH0_DOMAIN", "VITE_AUTH0_DOMAIN"),
    )
    auth0_audience: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("AUTH0_AUDIENCE", "VITE_AUTH0_AUDIENCE"),
    )
    auth0_client_id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("AUTH0_CLIENT_ID", "VITE_AUTH0_CLIENT_ID"),
    )

    prometheus_port: int = Field(default=9001, alias="PROMETHEUS_PORT")

    @property
    def is_dev(self) -> bool:
        return self.app_env == "dev"


class AgentConfig:
    """Per-agent configuration loaded from YAML"""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        config_path = Path(f"config/agents/{agent_id}.yaml")
        if not config_path.exists():
            # Fallback defaults
            self.data = self._default_config()
        else:
            with open(config_path, "r") as f:
                raw = yaml.safe_load(f)
                self.data = self._expand_env(raw)

    def _default_config(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "ranking": {
                "weights": {"cosine": 0.55, "skills": 0.25, "cert": 0.10, "recency": 0.10}
            },
            "filters": {"default_min_years": {}},
            "llm": {
                "provider": "disabled",
                "rerank": {"enabled": False, "top_k": 50, "timeout_ms": 700},
                "nl_assist": {"enabled": False},
            },
            "budgets": {"monthly_usd": 150.0},
            "ontology": {
                "skills_csv": "./config/skills.csv",
                "aliases_csv": "./config/aliases.csv",
                "certs_csv": "./config/certs.csv",
            },
            "storage": {"originals_bucket": "originals"},
        }

    def _expand_env(self, data: dict) -> dict:
        """Recursively expand ${VAR} references"""
        if isinstance(data, dict):
            return {k: self._expand_env(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._expand_env(item) for item in data]
        elif isinstance(data, str) and data.startswith("${") and data.endswith("}"):
            var = data[2:-1]
            val = os.getenv(var, "")
            if val.lower() in ("true", "false"):
                return val.lower() == "true"
            return val
        return data

    def get(self, path: str, default=None):
        """Get nested config value by dot path"""
        keys = path.split(".")
        val = self.data
        for key in keys:
            if isinstance(val, dict):
                val = val.get(key)
                if val is None:
                    return default
            else:
                return default
        return val


settings = Settings()
