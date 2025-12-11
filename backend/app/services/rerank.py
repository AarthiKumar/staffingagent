"""LLM reranking service with timeouts and fallback"""
import json
import time
from typing import Any, Dict, List, Optional

from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import AgentConfig, settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class RerankService:
    """Rerank search results using LLM"""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.config = AgentConfig(agent_id)
        self.timeout_ms = self.config.get("llm.rerank.timeout_ms", 700)
        self.enabled = self.config.get("llm.rerank.enabled", False)

    def rerank(
        self,
        results: List[Dict[str, Any]],
        query: str,
        filters: Dict[str, Any],
    ) -> tuple[List[Dict[str, Any]], bool]:
        """Rerank results using LLM. Returns (results, reranked_flag)"""

        if not self.enabled or settings.llm_provider == "disabled":
            logger.info("LLM reranking disabled")
            return results, False

        try:
            start_time = time.time()

            # Build structured evidence (no full CVs, no emails)
            evidence = self._build_evidence(results, filters)

            # Call LLM with timeout
            reranked_order = self._call_llm_rerank(query, evidence)

            elapsed_ms = int((time.time() - start_time) * 1000)

            if elapsed_ms > self.timeout_ms:
                logger.warning(f"Rerank exceeded timeout: {elapsed_ms}ms > {self.timeout_ms}ms")
                return results, False

            # Apply reranking
            reranked_results = self._apply_reranking(results, reranked_order)

            logger.info(f"Rerank completed in {elapsed_ms}ms")
            return reranked_results, True

        except Exception as e:
            logger.error(f"Rerank failed, falling back to baseline: {e}")
            return results, False

    def _build_evidence(self, results: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build structured evidence for LLM (no PII, no full CVs)"""
        evidence = []

        for idx, result in enumerate(results[:10]):
            candidate = result.get("candidate")
            if not candidate:
                continue

            # Build safe evidence
            item = {
                "rank": idx + 1,
                "name": candidate.name if candidate.name != "Unknown" else f"Candidate {idx + 1}",
                "location": candidate.location or "Unknown",
                "score": result.get("score", 0.0),
                "matched_skills": result.get("why", {}).get("skills", []),
                "matched_certs": result.get("why", {}).get("certs", []),
                "snippets": [
                    s.get("text", "")[:150] for s in result.get("why", {}).get("snippets", [])[:3]
                ],
            }
            evidence.append(item)

        return evidence

    def _call_llm_rerank(self, query: str, evidence: List[Dict[str, Any]]) -> List[int]:
        """Call LLM API to get reranked order"""
        # This is a stub implementation
        # In production, call actual LLM API (OpenAI, Anthropic, etc.)

        provider = settings.llm_provider

        if provider == "disabled":
            raise ValueError("LLM provider disabled")

        # TODO: Implement actual LLM API calls
        # For now, return original order
        logger.warning("LLM rerank not implemented, returning original order")
        return list(range(len(evidence)))

    def _apply_reranking(self, results: List[Dict[str, Any]], reranked_order: List[int]) -> List[Dict[str, Any]]:
        """Apply reranked order to results"""
        if not reranked_order or len(reranked_order) != len(results[:len(reranked_order)]):
            return results

        reranked = []
        for idx in reranked_order:
            if 0 <= idx < len(results):
                reranked.append(results[idx])

        # Append remaining results not in reranked order
        reranked_ids = set(id(results[idx]) for idx in reranked_order if idx < len(results))
        for result in results:
            if id(result) not in reranked_ids:
                reranked.append(result)

        return reranked


def get_rerank_service(agent_id: str) -> RerankService:
    """Get rerank service for agent"""
    return RerankService(agent_id)
