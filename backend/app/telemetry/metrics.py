"""Prometheus metrics"""
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry

# Create registry
registry = CollectorRegistry()

# Request metrics
request_count = Counter(
    "staffing_requests_total",
    "Total number of requests",
    ["agent_id", "endpoint", "status"],
    registry=registry,
)

request_latency = Histogram(
    "staffing_request_latency_seconds",
    "Request latency in seconds",
    ["agent_id", "endpoint"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    registry=registry,
)

# Search metrics
search_results_count = Histogram(
    "staffing_search_results",
    "Number of search results returned",
    ["agent_id"],
    buckets=[0, 1, 5, 10, 20, 50, 100],
    registry=registry,
)

zero_result_rate = Counter(
    "staffing_zero_results_total",
    "Number of searches with zero results",
    ["agent_id"],
    registry=registry,
)

# LLM metrics
llm_tokens_in = Counter(
    "staffing_llm_tokens_in_total",
    "Total input tokens",
    ["agent_id", "feature", "model"],
    registry=registry,
)

llm_tokens_out = Counter(
    "staffing_llm_tokens_out_total",
    "Total output tokens",
    ["agent_id", "feature", "model"],
    registry=registry,
)

llm_cost_usd = Counter(
    "staffing_llm_cost_usd_total",
    "Total LLM cost in USD",
    ["agent_id", "feature", "model"],
    registry=registry,
)

llm_latency = Histogram(
    "staffing_llm_latency_ms",
    "LLM API latency in milliseconds",
    ["agent_id", "feature", "model"],
    buckets=[50, 100, 200, 500, 1000, 2000, 5000],
    registry=registry,
)

llm_timeouts = Counter(
    "staffing_llm_timeouts_total",
    "Number of LLM timeouts",
    ["agent_id", "feature"],
    registry=registry,
)

llm_cache_hits = Counter(
    "staffing_llm_cache_hits_total",
    "Number of LLM cache hits",
    ["agent_id", "feature"],
    registry=registry,
)

# Budget metrics
current_month_spend = Gauge(
    "staffing_current_month_spend_usd",
    "Current month spend in USD",
    ["agent_id"],
    registry=registry,
)

budget_exceeded = Gauge(
    "staffing_budget_exceeded",
    "Budget exceeded flag (1=exceeded, 0=ok)",
    ["agent_id"],
    registry=registry,
)


class MetricsCollector:
    """Helper to collect and export metrics"""

    def __init__(self):
        self.registry = registry

    def track_request(self, agent_id: str, endpoint: str, status: int, latency: float):
        """Track API request"""
        request_count.labels(agent_id=agent_id, endpoint=endpoint, status=status).inc()
        request_latency.labels(agent_id=agent_id, endpoint=endpoint).observe(latency)

    def track_search(self, agent_id: str, results_count: int):
        """Track search results"""
        search_results_count.labels(agent_id=agent_id).observe(results_count)
        if results_count == 0:
            zero_result_rate.labels(agent_id=agent_id).inc()

    def track_llm_event(
        self, agent_id: str, feature: str, model: str, tokens_in_val: int, tokens_out_val: int,
        cost: float, latency_ms: int, cache_hit: bool, timeout: bool
    ):
        """Track LLM event"""
        llm_tokens_in.labels(agent_id=agent_id, feature=feature, model=model).inc(tokens_in_val)
        llm_tokens_out.labels(agent_id=agent_id, feature=feature, model=model).inc(tokens_out_val)
        llm_cost_usd.labels(agent_id=agent_id, feature=feature, model=model).inc(cost)
        llm_latency.labels(agent_id=agent_id, feature=feature, model=model).observe(latency_ms)

        if cache_hit:
            llm_cache_hits.labels(agent_id=agent_id, feature=feature).inc()
        if timeout:
            llm_timeouts.labels(agent_id=agent_id, feature=feature).inc()

    def update_budget_metrics(self, agent_id: str, spend: float, exceeded: bool):
        """Update budget metrics"""
        current_month_spend.labels(agent_id=agent_id).set(spend)
        budget_exceeded.labels(agent_id=agent_id).set(1 if exceeded else 0)


metrics = MetricsCollector()
