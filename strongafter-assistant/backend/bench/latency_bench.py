#!/usr/bin/env python3
"""
Latency Benchmark Infrastructure for StrongAfter Performance Optimization

Comprehensive benchmarking harness for measuring trauma recovery text processing performance.
Validates optimization effectiveness and tracks performance regressions.

Key features:
- Stratified test cases across content types (safe/sensitive) and lengths (short/long)
- Concurrent request processing for realistic load simulation
- P50/P95 latency measurement with timeout detection
- CSV output for performance tracking and analysis
- Health check validation before benchmark execution

Usage:
    python bench/latency_bench.py --runs 20
    
Target: P95 latency ≤3.5s (down from 25-30s baseline)
"""

import asyncio
import time
import requests
import json
import csv
import statistics
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

# Stratified test cases for comprehensive performance measurement
# Covers realistic trauma recovery scenarios across dimensions:
# - Content sensitivity: safe (general stress) vs sensitive (crisis/trauma)
# - Text length: short (3-5 words) vs long (paragraph-length)
# This stratification helps identify performance patterns and regression points
TEST_CASES = {
    'short_safe': [
        "I feel stressed",
        "Need help with anxiety", 
        "Feeling overwhelmed",
        "Having trouble sleeping",
        "Work is difficult"
    ],
    'short_sensitive': [
        "I want to hurt myself",
        "Thinking about suicide",
        "I was abused",
        "Can't stop the flashbacks",
        "Feel like ending it"
    ],
    'long_safe': [
        "I've been struggling with stress and anxiety for several months now. Work has been overwhelming and I'm having trouble maintaining my relationships. I feel like I'm constantly on edge and can't seem to relax even when I try.",
        "My therapist suggested I explore trauma recovery resources. I've been working on understanding my emotional responses and learning coping strategies. Sometimes I feel like I'm making progress but other days are really difficult.",
        "I'm trying to rebuild my sense of self after some difficult experiences. The process feels slow and sometimes discouraging. I'm looking for guidance on how to be patient with myself during this healing journey."
    ],
    'long_sensitive': [
        "I experienced childhood sexual abuse and I'm still dealing with the effects decades later. I have flashbacks, nightmares, and struggle with intimacy. Sometimes I wonder if I'll ever feel normal again and the pain feels unbearable.",
        "I've been having thoughts of suicide lately and I'm scared. The trauma from my past feels like it's consuming me and I don't know how to cope. I feel ashamed and isolated and worry that no one would understand.",
        "I was assaulted last year and I can't seem to move past it. Every day is a struggle and I alternate between feeling numb and feeling overwhelmed with rage and sadness. I don't know how to heal from this."
    ]
}

class LatencyBenchmark:
    """Comprehensive latency benchmarking system for performance validation.
    
    Measures end-to-end processing latency across stratified test cases.
    Validates optimization effectiveness and detects performance regressions.
    
    Key metrics:
    - P50/P95 latency percentiles
    - Success/timeout rates
    - Processing mode distribution
    - Category-specific performance patterns
    """
    
    def __init__(self, base_url: str = "http://localhost:5001"):
        """Initialize benchmark with target API endpoint."""
        self.base_url = base_url
        # Store all request results for comprehensive analysis
        self.results = []
        
    def make_request(self, text: str, test_id: str) -> Dict[str, Any]:
        """Execute single API request with precise latency measurement.
        
        Captures end-to-end processing time including network overhead.
        Records success/failure, timeout detection, and response metadata.
        
        Args:
            text: Test input text for processing
            test_id: Unique identifier for test case tracking
            
        Returns:
            Request result with timing and response metadata
        """
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{self.base_url}/api/process-text",
                json={"text": text},
                timeout=10.0
            )
            
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'test_id': test_id,
                    'text': text[:50] + "..." if len(text) > 50 else text,
                    'text_length': len(text.split()),
                    'latency_ms': latency_ms,
                    'mode': data.get('mode', 'unknown'),
                    'total_time_ms': data.get('total_time_ms', latency_ms),
                    'success': True,
                    'timeout': False,
                    'error': None,
                    'debug': data.get('debug', {})
                }
            else:
                return {
                    'test_id': test_id,
                    'text': text[:50] + "..." if len(text) > 50 else text,
                    'text_length': len(text.split()),
                    'latency_ms': latency_ms,
                    'success': False,
                    'timeout': False,
                    'error': f"HTTP {response.status_code}",
                    'mode': 'error'
                }
                
        except requests.Timeout:
            return {
                'test_id': test_id,
                'text': text[:50] + "..." if len(text) > 50 else text,
                'text_length': len(text.split()),
                'latency_ms': 10000,  # Timeout value
                'success': False,
                'timeout': True,
                'error': 'timeout',
                'mode': 'timeout'
            }
        except Exception as e:
            return {
                'test_id': test_id,
                'text': text[:50] + "..." if len(text) > 50 else text,
                'text_length': len(text.split()),
                'latency_ms': (time.time() - start_time) * 1000,
                'success': False,
                'timeout': False,
                'error': str(e),
                'mode': 'error'
            }
    
    def run_batch(self, test_cases: List[str], category: str, n_runs: int = 50) -> List[Dict[str, Any]]:
        """Run a batch of requests with specified number of runs."""
        all_requests = []
        
        # Generate N requests by cycling through test cases
        for i in range(n_runs):
            text = test_cases[i % len(test_cases)]
            test_id = f"{category}_{i}"
            all_requests.append((text, test_id))
        
        results = []
        
        # Run requests with ThreadPoolExecutor for parallelism
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {
                executor.submit(self.make_request, text, test_id): (text, test_id)
                for text, test_id in all_requests
            }
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    result['category'] = category
                    results.append(result)
                    print(f"Completed {result['test_id']}: {result['latency_ms']:.1f}ms ({result['mode']})")
                except Exception as e:
                    text, test_id = futures[future]
                    results.append({
                        'test_id': test_id,
                        'category': category,
                        'text': text[:50] + "..." if len(text) > 50 else text,
                        'success': False,
                        'error': str(e),
                        'mode': 'exception'
                    })
        
        return results
    
    def run_benchmark(self, n_runs_per_category: int = 50) -> Dict[str, Any]:
        """Run full benchmark across all categories."""
        print(f"Starting latency benchmark with {n_runs_per_category} runs per category...")
        
        all_results = []
        
        for category, test_cases in TEST_CASES.items():
            print(f"\nRunning {category} tests...")
            results = self.run_batch(test_cases, category, n_runs_per_category)
            all_results.extend(results)
        
        self.results = all_results
        return self.analyze_results()
    
    def analyze_results(self) -> Dict[str, Any]:
        """Analyze benchmark results and compute statistics."""
        if not self.results:
            return {}
        
        # Overall stats
        successful_results = [r for r in self.results if r.get('success', False)]
        latencies = [r['latency_ms'] for r in successful_results]
        
        overall_stats = {
            'total_requests': len(self.results),
            'successful_requests': len(successful_results),
            'success_rate': len(successful_results) / len(self.results) if self.results else 0,
            'timeout_rate': len([r for r in self.results if r.get('timeout', False)]) / len(self.results),
            'p50_latency_ms': statistics.median(latencies) if latencies else 0,
            'p95_latency_ms': statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else (max(latencies) if latencies else 0),
            'mean_latency_ms': statistics.mean(latencies) if latencies else 0,
            'min_latency_ms': min(latencies) if latencies else 0,
            'max_latency_ms': max(latencies) if latencies else 0
        }
        
        # Mode breakdown
        mode_stats = {}
        for result in successful_results:
            mode = result.get('mode', 'unknown')
            if mode not in mode_stats:
                mode_stats[mode] = []
            mode_stats[mode].append(result['latency_ms'])
        
        mode_breakdown = {}
        for mode, latencies in mode_stats.items():
            mode_breakdown[mode] = {
                'count': len(latencies),
                'percentage': len(latencies) / len(successful_results) * 100,
                'p50_latency_ms': statistics.median(latencies),
                'p95_latency_ms': statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies)
            }
        
        # Category breakdown
        category_stats = {}
        for category in TEST_CASES.keys():
            category_results = [r for r in successful_results if r.get('category') == category]
            if category_results:
                cat_latencies = [r['latency_ms'] for r in category_results]
                category_stats[category] = {
                    'count': len(category_results),
                    'p50_latency_ms': statistics.median(cat_latencies),
                    'p95_latency_ms': statistics.quantiles(cat_latencies, n=20)[18] if len(cat_latencies) >= 20 else max(cat_latencies)
                }
        
        return {
            'overall': overall_stats,
            'by_mode': mode_breakdown,
            'by_category': category_stats,
            'raw_results': self.results
        }
    
    def save_results(self, filename: str = "/tmp/bench_results.csv"):
        """Save detailed results to CSV."""
        if not self.results:
            return
        
        fieldnames = [
            'test_id', 'category', 'text', 'text_length', 'latency_ms', 
            'mode', 'success', 'timeout', 'error'
        ]
        
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in self.results:
                row = {field: result.get(field, '') for field in fieldnames}
                writer.writerow(row)
        
        print(f"Results saved to {filename}")
    
    def print_summary(self, stats: Dict[str, Any]):
        """Print benchmark summary."""
        overall = stats['overall']
        
        print("\n" + "="*60)
        print("LATENCY BENCHMARK SUMMARY")
        print("="*60)
        
        print(f"Total requests: {overall['total_requests']}")
        print(f"Success rate: {overall['success_rate']:.1%}")
        print(f"Timeout rate: {overall['timeout_rate']:.1%}")
        print(f"P50 latency: {overall['p50_latency_ms']:.1f}ms")
        print(f"P95 latency: {overall['p95_latency_ms']:.1f}ms")
        print(f"Mean latency: {overall['mean_latency_ms']:.1f}ms")
        
        print(f"\n🎯 TARGET P95: ≤3500ms")
        target_met = overall['p95_latency_ms'] <= 3500
        print(f"TARGET MET: {'✅ YES' if target_met else '❌ NO'}")
        
        print(f"\nMODE BREAKDOWN:")
        for mode, data in stats['by_mode'].items():
            print(f"  {mode}: {data['count']} requests ({data['percentage']:.1f}%) - P95: {data['p95_latency_ms']:.1f}ms")
        
        print(f"\nCATEGORY BREAKDOWN:")
        for category, data in stats['by_category'].items():
            print(f"  {category}: P50={data['p50_latency_ms']:.1f}ms P95={data['p95_latency_ms']:.1f}ms")


def main():
    """Main benchmark execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run latency benchmark')
    parser.add_argument('--url', default='http://localhost:5001', help='Base URL for API')
    parser.add_argument('--runs', type=int, default=50, help='Number of runs per category')
    parser.add_argument('--output', default='/tmp/bench_results.csv', help='Output CSV file')
    
    args = parser.parse_args()
    
    benchmark = LatencyBenchmark(args.url)
    
    try:
        # Check if server is running
        response = requests.get(f"{args.url}/api/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ Server health check failed: {response.status_code}")
            return 1
        print(f"✅ Server health check passed")
        
    except Exception as e:
        print(f"❌ Cannot reach server at {args.url}: {e}")
        return 1
    
    # Run benchmark
    stats = benchmark.run_benchmark(args.runs)
    
    # Print results
    benchmark.print_summary(stats)
    
    # Save detailed results
    benchmark.save_results(args.output)
    
    return 0

if __name__ == '__main__':
    exit(main())