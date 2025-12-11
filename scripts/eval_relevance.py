#!/usr/bin/env python3
"""Evaluate search relevance with P@5 and Recall@20"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import requests

API_BASE = "http://localhost:8000/api/v1"


def load_labels():
    """Load evaluation labels"""
    labels_path = Path(__file__).parent.parent / "data/eval/labels.json"
    if not labels_path.exists():
        print("Warning: labels.json not found, using empty labels")
        return []

    with open(labels_path) as f:
        return json.load(f)


def search(filters: dict, text: str = None, use_llm_rerank: bool = False):
    """Execute search"""
    payload = {
        "agent_id": "staffing",
        "filters": filters,
        "text": text,
        "use_llm_rerank": use_llm_rerank,
        "top_k": 50,
    }

    response = requests.post(f"{API_BASE}/search/", json=payload)
    response.raise_for_status()
    return response.json()


def compute_precision_at_k(results: list, relevant: list, k: int) -> float:
    """Compute Precision@K"""
    if not results or not relevant:
        return 0.0

    top_k = [r["candidate_id"] for r in results[:k]]
    relevant_set = set(relevant)
    hits = sum(1 for cid in top_k if cid in relevant_set)

    return hits / k if k > 0 else 0.0


def compute_recall_at_k(results: list, relevant: list, k: int) -> float:
    """Compute Recall@K"""
    if not results or not relevant:
        return 0.0

    top_k = [r["candidate_id"] for r in results[:k]]
    relevant_set = set(relevant)
    hits = sum(1 for cid in top_k if cid in relevant_set)

    return hits / len(relevant_set) if relevant_set else 0.0


def evaluate():
    """Run evaluation"""
    labels = load_labels()

    if not labels:
        print("No labels found, cannot evaluate")
        return

    print(f"Evaluating {len(labels)} queries...")
    print()

    baseline_p5_scores = []
    baseline_r20_scores = []
    rerank_p5_scores = []
    rerank_r20_scores = []

    for label in labels:
        query_text = label.get("query")
        filters = label.get("filters", {})
        relevant = label.get("relevant_candidate_ids", [])

        # Baseline search
        baseline_results = search(filters, query_text, use_llm_rerank=False)
        p5 = compute_precision_at_k(baseline_results["results"], relevant, 5)
        r20 = compute_recall_at_k(baseline_results["results"], relevant, 20)
        baseline_p5_scores.append(p5)
        baseline_r20_scores.append(r20)

        print(f"Query: {query_text[:50]}...")
        print(f"  Baseline P@5: {p5:.3f}, R@20: {r20:.3f}")

        # LLM rerank (if enabled)
        try:
            rerank_results = search(filters, query_text, use_llm_rerank=True)
            if rerank_results["flags"]["reranked"]:
                p5_rerank = compute_precision_at_k(rerank_results["results"], relevant, 5)
                r20_rerank = compute_recall_at_k(rerank_results["results"], relevant, 20)
                rerank_p5_scores.append(p5_rerank)
                rerank_r20_scores.append(r20_rerank)
                print(f"  Rerank P@5: {p5_rerank:.3f}, R@20: {r20_rerank:.3f}")
        except Exception as e:
            print(f"  Rerank failed: {e}")

    # Print summary
    print()
    print("=== Summary ===")
    avg_p5 = sum(baseline_p5_scores) / len(baseline_p5_scores)
    avg_r20 = sum(baseline_r20_scores) / len(baseline_r20_scores)
    print(f"Baseline P@5: {avg_p5:.3f}")
    print(f"Baseline R@20: {avg_r20:.3f}")

    if rerank_p5_scores:
        avg_p5_rerank = sum(rerank_p5_scores) / len(rerank_p5_scores)
        avg_r20_rerank = sum(rerank_r20_scores) / len(rerank_r20_scores)
        delta_p5 = avg_p5_rerank - avg_p5
        delta_r20 = avg_r20_rerank - avg_r20
        print(f"Rerank P@5: {avg_p5_rerank:.3f} (Δ {delta_p5:+.3f})")
        print(f"Rerank R@20: {avg_r20_rerank:.3f} (Δ {delta_r20:+.3f})")

    # Write metrics
    metrics = {
        "baseline": {"p@5": avg_p5, "r@20": avg_r20},
        "rerank": {
            "p@5": avg_p5_rerank if rerank_p5_scores else None,
            "r@20": avg_r20_rerank if rerank_r20_scores else None,
        },
    }

    metrics_path = Path(__file__).parent.parent / "metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"\nMetrics saved to {metrics_path}")


if __name__ == "__main__":
    evaluate()
