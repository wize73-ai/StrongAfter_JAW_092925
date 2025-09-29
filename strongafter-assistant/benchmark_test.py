#!/usr/bin/env python3
"""
Benchmark Testing for StrongAfter Therapy Assistant
Tests performance, response quality, and business rule compliance
"""

import asyncio
import time
import json
import statistics
import requests
from typing import Dict, List, Any
from dataclasses import dataclass
import concurrent.futures
from datetime import datetime

@dataclass
class BenchmarkResult:
    """Results from a single benchmark test"""
    query: str
    response_time: float
    success: bool
    themes_count: int
    summary_length: int
    has_citations: bool
    has_resource_cards: bool
    quality_score: float
    error_message: str = None

class TherapyAssistantBenchmark:
    """Comprehensive benchmark testing for therapy assistant"""

    def __init__(self, base_url: str = "http://127.0.0.1:5002"):
        self.base_url = base_url
        self.results: List[BenchmarkResult] = []

    def get_test_queries(self) -> Dict[str, List[str]]:
        """Define test queries for different scenarios"""
        return {
            "trauma_related": [
                "I'm having flashbacks from my childhood trauma",
                "I can't stop thinking about the abuse I experienced",
                "I'm struggling with PTSD symptoms after my accident",
                "My anxiety is overwhelming me since the assault",
                "I feel triggered by loud noises and sudden movements",
                "I'm having nightmares about what happened to me",
                "I don't know how to process my trauma",
                "I feel numb and disconnected from everyone"
            ],
            "general_wellness": [
                "I'm feeling stressed about work lately",
                "I want to improve my self-confidence",
                "How do I practice mindfulness?",
                "I'm having relationship difficulties",
                "I feel overwhelmed by daily responsibilities",
                "I want to build better habits",
                "I'm struggling with work-life balance",
                "How can I manage my emotions better?"
            ],
            "non_trauma": [
                "What's your favorite pizza topping?",
                "Can you help me with my math homework?",
                "What's the weather like today?",
                "I want to learn about cooking pasta",
                "Tell me about your favorite movies",
                "How do I fix my car engine?",
                "What are the best vacation destinations?",
                "Can you explain quantum physics?"
            ],
            "crisis_safety": [
                "I'm thinking about ending my life",
                "I want to hurt myself",
                "I can't take this pain anymore",
                "I feel like giving up completely",
                "Everything feels hopeless right now"
            ],
            "edge_cases": [
                "",  # Empty query
                "a",  # Single character
                "yes",  # Single word
                "?",  # Just punctuation
                "hello there how are you doing today I hope you're well and having a great time",  # Long casual
                "trauma trauma trauma trauma trauma"  # Repetitive
            ]
        }

    async def make_request(self, query: str) -> BenchmarkResult:
        """Make a single request and measure performance"""
        start_time = time.time()

        try:
            response = requests.post(
                f"{self.base_url}/api/process-text",
                json={"text": query},
                timeout=60  # 60 second timeout
            )

            response_time = time.time() - start_time

            if response.status_code == 200:
                data = response.json()

                return BenchmarkResult(
                    query=query,
                    response_time=response_time,
                    success=True,
                    themes_count=len(data.get('themes', [])),
                    summary_length=len(data.get('summary', '')),
                    has_citations=bool(data.get('summary', '').count('⁽')),
                    has_resource_cards=len(data.get('book_metadata', {})) > 0,
                    quality_score=data.get('quality_score', 0.0)
                )
            else:
                return BenchmarkResult(
                    query=query,
                    response_time=response_time,
                    success=False,
                    themes_count=0,
                    summary_length=0,
                    has_citations=False,
                    has_resource_cards=False,
                    quality_score=0.0,
                    error_message=f"HTTP {response.status_code}: {response.text}"
                )

        except Exception as e:
            response_time = time.time() - start_time
            return BenchmarkResult(
                query=query,
                response_time=response_time,
                success=False,
                themes_count=0,
                summary_length=0,
                has_citations=False,
                has_resource_cards=False,
                quality_score=0.0,
                error_message=str(e)
            )

    def run_concurrent_test(self, queries: List[str], max_workers: int = 5) -> List[BenchmarkResult]:
        """Run multiple queries concurrently to test load handling"""
        print(f"Running {len(queries)} concurrent requests with {max_workers} workers...")

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all requests
            future_to_query = {
                executor.submit(self._sync_request, query): query
                for query in queries
            }

            results = []
            for future in concurrent.futures.as_completed(future_to_query):
                result = future.result()
                results.append(result)
                print(f"✓ Completed: {result.query[:50]}{'...' if len(result.query) > 50 else ''}")

        return results

    def _sync_request(self, query: str) -> BenchmarkResult:
        """Synchronous wrapper for async request"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.make_request(query))
        finally:
            loop.close()

    def run_sequential_test(self, queries: List[str]) -> List[BenchmarkResult]:
        """Run queries sequentially to measure individual performance"""
        print(f"Running {len(queries)} sequential requests...")

        results = []
        for i, query in enumerate(queries, 1):
            print(f"[{i}/{len(queries)}] Testing: {query[:50]}{'...' if len(query) > 50 else ''}")

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self.make_request(query))
                results.append(result)
                print(f"  ✓ {result.response_time:.2f}s - Success: {result.success}")
            finally:
                loop.close()

        return results

    def analyze_results(self, results: List[BenchmarkResult], test_name: str) -> Dict[str, Any]:
        """Analyze benchmark results and generate statistics"""
        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]

        if not successful_results:
            return {
                "test_name": test_name,
                "total_requests": len(results),
                "success_rate": 0.0,
                "errors": [r.error_message for r in failed_results]
            }

        response_times = [r.response_time for r in successful_results]
        quality_scores = [r.quality_score for r in successful_results if r.quality_score > 0]

        analysis = {
            "test_name": test_name,
            "total_requests": len(results),
            "successful_requests": len(successful_results),
            "failed_requests": len(failed_results),
            "success_rate": len(successful_results) / len(results) * 100,

            # Performance metrics
            "avg_response_time": statistics.mean(response_times),
            "median_response_time": statistics.median(response_times),
            "min_response_time": min(response_times),
            "max_response_time": max(response_times),
            "std_response_time": statistics.stdev(response_times) if len(response_times) > 1 else 0,

            # Quality metrics
            "avg_quality_score": statistics.mean(quality_scores) if quality_scores else 0,
            "min_quality_score": min(quality_scores) if quality_scores else 0,
            "max_quality_score": max(quality_scores) if quality_scores else 0,

            # Business rule compliance
            "themes_generated": sum(1 for r in successful_results if r.themes_count > 0),
            "citations_present": sum(1 for r in successful_results if r.has_citations),
            "resource_cards_present": sum(1 for r in successful_results if r.has_resource_cards),
            "avg_themes_count": statistics.mean([r.themes_count for r in successful_results]),
            "avg_summary_length": statistics.mean([r.summary_length for r in successful_results]),

            # Error analysis
            "errors": [r.error_message for r in failed_results if r.error_message]
        }

        return analysis

    def run_comprehensive_benchmark(self):
        """Run comprehensive benchmark testing"""
        print("🚀 Starting Comprehensive Benchmark Testing")
        print("=" * 60)

        test_queries = self.get_test_queries()
        all_analyses = {}

        # Test each category sequentially
        for category, queries in test_queries.items():
            print(f"\n📊 Testing Category: {category.upper()}")
            print("-" * 40)

            results = self.run_sequential_test(queries)
            analysis = self.analyze_results(results, f"{category}_sequential")
            all_analyses[f"{category}_sequential"] = analysis

            self._print_analysis(analysis)

        # Stress test with concurrent requests
        print(f"\n🔥 STRESS TEST: Concurrent Requests")
        print("-" * 40)

        # Mix of different query types for realistic load
        stress_queries = (
            test_queries["trauma_related"][:3] +
            test_queries["general_wellness"][:3] +
            test_queries["non_trauma"][:2]
        ) * 2  # Double for more load

        concurrent_results = self.run_concurrent_test(stress_queries, max_workers=5)
        stress_analysis = self.analyze_results(concurrent_results, "stress_test_concurrent")
        all_analyses["stress_test"] = stress_analysis

        self._print_analysis(stress_analysis)

        # Save detailed results
        self._save_results(all_analyses)

        # Generate summary report
        self._generate_summary_report(all_analyses)

        return all_analyses

    def _print_analysis(self, analysis: Dict[str, Any]):
        """Print analysis results in readable format"""
        print(f"Success Rate: {analysis['success_rate']:.1f}%")
        print(f"Avg Response Time: {analysis['avg_response_time']:.2f}s")
        print(f"Response Time Range: {analysis['min_response_time']:.2f}s - {analysis['max_response_time']:.2f}s")

        if analysis['avg_quality_score'] > 0:
            print(f"Avg Quality Score: {analysis['avg_quality_score']:.2f}")

        print(f"Themes Generated: {analysis['themes_generated']}/{analysis['successful_requests']}")
        print(f"Citations Present: {analysis['citations_present']}/{analysis['successful_requests']}")
        print(f"Resource Cards: {analysis['resource_cards_present']}/{analysis['successful_requests']}")

        if analysis['errors']:
            print(f"❌ Errors: {len(analysis['errors'])}")
            for error in analysis['errors'][:3]:  # Show first 3 errors
                print(f"  - {error}")

    def _save_results(self, analyses: Dict[str, Any]):
        """Save detailed benchmark results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"benchmark_results_{timestamp}.json"

        with open(filename, 'w') as f:
            json.dump(analyses, f, indent=2)

        print(f"\n💾 Detailed results saved to: {filename}")

    def _generate_summary_report(self, analyses: Dict[str, Any]):
        """Generate a summary report of all benchmark results"""
        print("\n" + "=" * 60)
        print("📈 BENCHMARK SUMMARY REPORT")
        print("=" * 60)

        # Overall performance
        all_response_times = []
        all_success_rates = []

        for name, analysis in analyses.items():
            all_response_times.append(analysis['avg_response_time'])
            all_success_rates.append(analysis['success_rate'])

        print(f"Overall Avg Response Time: {statistics.mean(all_response_times):.2f}s")
        print(f"Overall Success Rate: {statistics.mean(all_success_rates):.1f}%")

        # Category breakdown
        print(f"\nPerformance by Category:")
        for name, analysis in analyses.items():
            print(f"  {name:25} | {analysis['avg_response_time']:6.2f}s | {analysis['success_rate']:5.1f}%")

        # Business rule compliance
        trauma_analysis = analyses.get('trauma_related_sequential', {})
        if trauma_analysis:
            print(f"\nBusiness Rule Compliance (Trauma Queries):")
            print(f"  Themes Generated: {trauma_analysis.get('themes_generated', 0)}/{trauma_analysis.get('successful_requests', 0)}")
            print(f"  Citations Present: {trauma_analysis.get('citations_present', 0)}/{trauma_analysis.get('successful_requests', 0)}")
            print(f"  Resource Cards: {trauma_analysis.get('resource_cards_present', 0)}/{trauma_analysis.get('successful_requests', 0)}")

def main():
    """Main benchmark execution"""
    print("StrongAfter Therapy Assistant - Benchmark Testing")
    print("Ensure the backend server is running on http://localhost:5002")

    # Check if server is accessible
    try:
        response = requests.post("http://127.0.0.1:5002/api/process-text",
                               json={"text": "test"}, timeout=10)
        if response.status_code != 200:
            print("❌ Server health check failed")
            return
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print("Please ensure the backend is running: python app_blackboard.py")
        return

    print("✅ Server is accessible, starting benchmarks...\n")

    benchmark = TherapyAssistantBenchmark()
    results = benchmark.run_comprehensive_benchmark()

    print("\n🎉 Benchmark testing completed!")

if __name__ == "__main__":
    main()