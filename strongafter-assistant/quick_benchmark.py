#!/usr/bin/env python3
"""
Quick Benchmark Test for StrongAfter Therapy Assistant
Focused performance testing with key scenarios
"""

import time
import requests
import statistics
from datetime import datetime

def test_endpoint(query, description):
    """Test a single query and return performance metrics"""
    print(f"Testing: {description}")
    print(f"Query: {query}")

    start_time = time.time()

    try:
        response = requests.post(
            "http://127.0.0.1:5001/api/process-text",
            json={"text": query},
            timeout=130
        )

        response_time = time.time() - start_time

        if response.status_code == 200:
            data = response.json()

            themes_count = len(data.get('themes', []))
            summary_length = len(data.get('summary', ''))
            has_citations = bool(data.get('summary', '').count('⁽'))

            print(f"  ✅ Success: {response_time:.2f}s")
            print(f"  📊 Themes: {themes_count}, Summary: {summary_length} chars")
            print(f"  🔗 Citations: {'Yes' if has_citations else 'No'}")

            return {
                'success': True,
                'response_time': response_time,
                'themes_count': themes_count,
                'summary_length': summary_length,
                'has_citations': has_citations
            }
        else:
            print(f"  ❌ Failed: HTTP {response.status_code}")
            return {'success': False, 'response_time': response_time, 'error': f"HTTP {response.status_code}"}

    except Exception as e:
        response_time = time.time() - start_time
        print(f"  ❌ Error: {e}")
        return {'success': False, 'response_time': response_time, 'error': str(e)}

def main():
    print("🚀 Quick Benchmark Test - StrongAfter Therapy Assistant")
    print("=" * 60)

    # Test scenarios
    test_cases = [
        # Trauma-related queries
        ("I'm having flashbacks from my childhood trauma", "Trauma - Flashbacks"),
        ("I struggle with PTSD symptoms after my accident", "Trauma - PTSD"),
        ("I use alcohol to cope with my trauma memories", "Trauma - Substance Use"),

        # General wellness
        ("I'm feeling stressed about work lately", "Wellness - Work Stress"),
        ("I want to improve my self-confidence", "Wellness - Self-confidence"),

        # Non-trauma content
        ("What's your favorite pizza topping?", "Non-trauma - Pizza"),
        ("Tell me about quantum physics", "Non-trauma - Physics"),

        # Edge cases
        ("", "Edge - Empty Query"),
        ("yes", "Edge - Single Word"),
    ]

    results = []

    for query, description in test_cases:
        print(f"\n{len(results) + 1}. {description}")
        print("-" * 40)

        result = test_endpoint(query, description)
        result['description'] = description
        result['query'] = query
        results.append(result)

        time.sleep(1)  # Brief pause between requests

    # Analysis
    print(f"\n" + "=" * 60)
    print("📈 BENCHMARK RESULTS SUMMARY")
    print("=" * 60)

    successful_results = [r for r in results if r['success']]
    failed_results = [r for r in results if not r['success']]

    if successful_results:
        response_times = [r['response_time'] for r in successful_results]
        themes_counts = [r.get('themes_count', 0) for r in successful_results]
        citation_count = sum(1 for r in successful_results if r.get('has_citations', False))

        print(f"Success Rate: {len(successful_results)}/{len(results)} ({len(successful_results)/len(results)*100:.1f}%)")
        print(f"")
        print(f"⏱️  Response Times:")
        print(f"   Average: {statistics.mean(response_times):.2f}s")
        print(f"   Median:  {statistics.median(response_times):.2f}s")
        print(f"   Range:   {min(response_times):.2f}s - {max(response_times):.2f}s")
        print(f"")
        print(f"📊 Content Quality:")
        print(f"   Avg Themes: {statistics.mean(themes_counts):.1f}")
        print(f"   Citations:  {citation_count}/{len(successful_results)} responses")

        # Trauma vs non-trauma analysis
        trauma_results = [r for r in successful_results if 'Trauma' in r['description']]
        non_trauma_results = [r for r in successful_results if 'Non-trauma' in r['description']]

        if trauma_results:
            trauma_times = [r['response_time'] for r in trauma_results]
            trauma_themes = [r.get('themes_count', 0) for r in trauma_results]
            print(f"")
            print(f"🔍 Trauma Queries ({len(trauma_results)} tests):")
            print(f"   Avg Time: {statistics.mean(trauma_times):.2f}s")
            print(f"   Avg Themes: {statistics.mean(trauma_themes):.1f}")

        if non_trauma_results:
            non_trauma_times = [r['response_time'] for r in non_trauma_results]
            non_trauma_themes = [r.get('themes_count', 0) for r in non_trauma_results]
            print(f"")
            print(f"🔍 Non-trauma Queries ({len(non_trauma_results)} tests):")
            print(f"   Avg Time: {statistics.mean(non_trauma_times):.2f}s")
            print(f"   Avg Themes: {statistics.mean(non_trauma_themes):.1f}")

    if failed_results:
        print(f"")
        print(f"❌ Failed Tests: {len(failed_results)}")
        for result in failed_results:
            print(f"   {result['description']}: {result.get('error', 'Unknown error')}")

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"quick_benchmark_{timestamp}.json"

    import json
    with open(filename, 'w') as f:
        json.dump({
            'timestamp': timestamp,
            'total_tests': len(results),
            'successful_tests': len(successful_results),
            'results': results
        }, f, indent=2)

    print(f"")
    print(f"💾 Results saved to: {filename}")
    print(f"")
    print("🎉 Benchmark completed!")

if __name__ == "__main__":
    main()