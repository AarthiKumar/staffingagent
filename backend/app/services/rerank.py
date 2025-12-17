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
        self._openai_client = None

        if self.enabled and settings.llm_provider == "openai":
            self._init_openai_client()

    def _init_openai_client(self):
        """Initialize OpenAI client"""
        if not settings.llm_api_key:
            logger.warning("OpenAI API key not configured, reranking will be disabled")
            self.enabled = False
            return

        try:
            from openai import OpenAI
            self._openai_client = OpenAI(
                api_key=settings.llm_api_key,
                timeout=self.timeout_ms / 1000.0  # Convert to seconds
            )
            logger.info("OpenAI client initialized for reranking")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            self.enabled = False

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

            if not evidence:
                return results, False

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
        provider = settings.llm_provider

        if provider == "disabled":
            raise ValueError("LLM provider disabled")

        if provider == "openai":
            return self._call_openai_rerank(query, evidence)
        else:
            logger.warning(f"Unsupported LLM provider: {provider}, returning original order")
            return list(range(len(evidence)))

    def _call_openai_rerank(self, query: str, evidence: List[Dict[str, Any]]) -> List[int]:
        """Call OpenAI API to rerank candidates"""
        if not self._openai_client:
            raise RuntimeError("OpenAI client not initialized")

        # Build prompt for reranking
        prompt = self._build_rerank_prompt(query, evidence)

        try:
            response = self._openai_client.chat.completions.create(
                model="gpt-4o-mini",  # Fast and cost-effective for reranking
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert technical recruiter. Analyze candidates and rerank them based on how well they match the search query and requirements. Return ONLY a JSON array of candidate ranks in order of best match to worst match."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.1,  # Low temperature for consistent ranking
            )

            # Parse response
            result_text = response.choices[0].message.content
            result_json = json.loads(result_text)

            # Extract ranking - expect {"ranking": [1, 3, 2, ...]}
            if "ranking" in result_json:
                ranking = result_json["ranking"]
                # Convert from 1-indexed to 0-indexed
                return [r - 1 for r in ranking if isinstance(r, int) and 1 <= r <= len(evidence)]
            else:
                logger.warning("OpenAI response missing 'ranking' key")
                return list(range(len(evidence)))

        except Exception as e:
            logger.error(f"OpenAI rerank call failed: {e}")
            raise

    def _build_rerank_prompt(self, query: str, evidence: List[Dict[str, Any]]) -> str:
        """Build prompt for reranking"""
        candidates_text = "\n\n".join([
            f"Candidate {c['rank']}:\n"
            f"- Location: {c['location']}\n"
            f"- Matched Skills: {', '.join(c['matched_skills']) if c['matched_skills'] else 'None'}\n"
            f"- Matched Certifications: {', '.join(c['matched_certs']) if c['matched_certs'] else 'None'}\n"
            f"- Experience Snippets: {' | '.join(c['snippets']) if c['snippets'] else 'None'}\n"
            f"- Current Score: {c['score']:.3f}"
            for c in evidence
        ])

        prompt = f"""Search Query: "{query}"

Candidates to rank:
{candidates_text}

Task: Rerank these {len(evidence)} candidates based on how well they match the search query. Consider:
1. Relevance of skills to the query
2. Quality and depth of experience
3. Certifications that demonstrate expertise
4. Overall fit for the role described in the query

Return your ranking as a JSON object with a "ranking" array containing the candidate numbers in order from best match to worst match.

Example response format:
{{"ranking": [3, 1, 5, 2, 4]}}

Your ranking:"""

        return prompt

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
