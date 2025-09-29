import time
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class MetricsService:
    def __init__(self):
        self.request_metrics = []
        
    def log_request(self, event: Dict[str, Any]):
        """Log structured request metrics."""
        event['timestamp'] = time.time()
        self.request_metrics.append(event)
        
        # Log as structured JSON
        logger.info(f"REQUEST_METRICS: {json.dumps(event)}")
        
        # Keep only last 1000 requests in memory
        if len(self.request_metrics) > 1000:
            self.request_metrics = self.request_metrics[-1000:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get aggregated stats from recent requests."""
        if not self.request_metrics:
            return {}
            
        total_requests = len(self.request_metrics)
        modes = {}
        avg_latency = 0
        timeout_hits = 0
        cache_hits = 0
        
        for req in self.request_metrics:
            mode = req.get('mode', 'unknown')
            modes[mode] = modes.get(mode, 0) + 1
            avg_latency += req.get('total_ms', 0)
            if req.get('timeout_hit'):
                timeout_hits += 1
            if req.get('cache_hit'):
                cache_hits += 1
                
        return {
            'total_requests': total_requests,
            'modes': modes,
            'avg_latency_ms': avg_latency / total_requests if total_requests > 0 else 0,
            'timeout_rate': timeout_hits / total_requests if total_requests > 0 else 0,
            'cache_hit_rate': cache_hits / total_requests if total_requests > 0 else 0
        }

# Global instance
metrics_service = MetricsService()