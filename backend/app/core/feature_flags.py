"""Feature flags management"""
from typing import Dict

from .config import AgentConfig, settings


class FeatureFlags:
    """Feature flags for LLM and optional features"""

    def __init__(self, agent_config: AgentConfig):
        self.agent_config = agent_config
        self._llm_enabled_cache = None

    @property
    def llm_provider(self) -> str:
        """Get LLM provider from config"""
        provider = self.agent_config.get("llm.provider", settings.llm_provider)
        return provider if provider != "disabled" else "disabled"

    @property
    def llm_enabled(self) -> bool:
        """Check if LLM features are enabled"""
        if self._llm_enabled_cache is not None:
            return self._llm_enabled_cache

        provider = self.llm_provider
        self._llm_enabled_cache = provider != "disabled" and settings.llm_api_key is not None
        return self._llm_enabled_cache

    @property
    def rerank_enabled(self) -> bool:
        """Check if LLM reranking is enabled"""
        if not self.llm_enabled:
            return False
        return self.agent_config.get("llm.rerank.enabled", settings.enable_llm_rerank)

    @property
    def nl_assist_enabled(self) -> bool:
        """Check if NL assist is enabled"""
        if not self.llm_enabled:
            return False
        return self.agent_config.get("llm.nl_assist.enabled", settings.enable_nl_assist)

    def to_dict(self) -> Dict[str, bool]:
        """Export flags as dict"""
        return {
            "llm_enabled": self.llm_enabled,
            "rerank_enabled": self.rerank_enabled,
            "nl_assist_enabled": self.nl_assist_enabled,
            "llm_provider": self.llm_provider,
        }


def get_feature_flags(agent_id: str) -> FeatureFlags:
    """Get feature flags for an agent"""
    agent_config = AgentConfig(agent_id)
    return FeatureFlags(agent_config)
