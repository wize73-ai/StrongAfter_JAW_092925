#!/usr/bin/env python3
"""
Backward Compatibility Test for StrongAfter Therapy Assistant
Tests both original and blackboard architectures side-by-side
"""

import requests
import json
import time
from datetime import datetime

def test_service(base_url, service_name, query):
    """Test a service and return structured results"""
    print(f"\n📡 Testing {service_name}")
    print(f"🔗 URL: {base_url}")
    print(f"📝 Query: {query}")

    start_time = time.time()

    try:
        response = requests.post(
            f"{base_url}/api/process-text",
            json={"text": query},
            timeout=30
        )

        response_time = time.time() - start_time

        if response.status_code == 200:
            data = response.json()

            result = {
                'service': service_name,
                'success': True,
                'response_time': response_time,
                'status_code': response.status_code,
                'themes_count': len(data.get('themes', [])),
                'summary_length': len(data.get('summary', '')),
                'has_citations': bool(data.get('summary', '').count('⁽')),
                'has_book_metadata': len(data.get('book_metadata', {})) > 0,
                'response_structure': list(data.keys()),
                'sample_theme': data.get('themes', [{}])[0] if data.get('themes') else None,
                'data': data  # Store full response for comparison
            }

            print(f"  ✅ Success: {response_time:.2f}s")
            print(f"  📊 Themes: {result['themes_count']}")
            print(f"  📝 Summary: {result['summary_length']} chars")
            print(f"  🔗 Citations: {'Yes' if result['has_citations'] else 'No'}")
            print(f"  📚 Book metadata: {'Yes' if result['has_book_metadata'] else 'No'}")

            return result

        else:
            print(f"  ❌ Failed: HTTP {response.status_code}")
            return {
                'service': service_name,
                'success': False,
                'response_time': response_time,
                'status_code': response.status_code,
                'error': f"HTTP {response.status_code}: {response.text}"
            }

    except Exception as e:
        response_time = time.time() - start_time
        print(f"  ❌ Error: {e}")
        return {
            'service': service_name,
            'success': False,
            'response_time': response_time,
            'error': str(e)
        }

def compare_responses(original_result, blackboard_result):
    """Compare responses for backward compatibility"""
    print(f"\n🔍 COMPATIBILITY ANALYSIS")
    print("=" * 50)

    if not original_result['success'] or not blackboard_result['success']:
        print("❌ Cannot compare - one or both services failed")
        return {'compatible': False, 'reason': 'Service failure'}

    compatibility = {
        'compatible': True,
        'differences': [],
        'similarities': [],
        'performance_diff': blackboard_result['response_time'] - original_result['response_time']
    }

    # Check API structure compatibility
    orig_keys = set(original_result['response_structure'])
    bb_keys = set(blackboard_result['response_structure'])

    if orig_keys == bb_keys:
        compatibility['similarities'].append("✅ Identical API response structure")
    else:
        missing_in_bb = orig_keys - bb_keys
        extra_in_bb = bb_keys - orig_keys
        if missing_in_bb:
            compatibility['differences'].append(f"❌ Missing in blackboard: {missing_in_bb}")
        if extra_in_bb:
            compatibility['similarities'].append(f"✅ Enhanced in blackboard: {extra_in_bb}")

    # Check data types and format compatibility
    if original_result['themes_count'] > 0 and blackboard_result['themes_count'] > 0:
        orig_theme = original_result['sample_theme']
        bb_theme = blackboard_result['sample_theme']

        if orig_theme and bb_theme:
            orig_theme_keys = set(orig_theme.keys())
            bb_theme_keys = set(bb_theme.keys())

            if orig_theme_keys.issubset(bb_theme_keys):
                compatibility['similarities'].append("✅ Theme structure backward compatible")
            else:
                missing = orig_theme_keys - bb_theme_keys
                compatibility['differences'].append(f"❌ Missing theme fields: {missing}")

    # Check business logic compatibility
    both_have_themes = original_result['themes_count'] > 0 and blackboard_result['themes_count'] > 0
    both_have_no_themes = original_result['themes_count'] == 0 and blackboard_result['themes_count'] == 0

    if both_have_themes or both_have_no_themes:
        compatibility['similarities'].append("✅ Theme selection logic consistent")
    else:
        compatibility['differences'].append("❌ Different theme selection behavior")

    # Check citation compatibility
    if original_result['has_citations'] == blackboard_result['has_citations']:
        compatibility['similarities'].append("✅ Citation behavior consistent")
    else:
        compatibility['differences'].append("❌ Different citation behavior")

    # Performance comparison
    if compatibility['performance_diff'] < 0:
        improvement = abs(compatibility['performance_diff'])
        compatibility['similarities'].append(f"✅ Performance improved by {improvement:.2f}s")
    else:
        degradation = compatibility['performance_diff']
        compatibility['differences'].append(f"❌ Performance degraded by {degradation:.2f}s")

    # Overall compatibility assessment
    if len(compatibility['differences']) == 0:
        compatibility['compatible'] = True
        compatibility['assessment'] = "100% backward compatible"
    elif len(compatibility['differences']) <= 2 and 'Performance degraded' not in str(compatibility['differences']):
        compatibility['compatible'] = True
        compatibility['assessment'] = "Mostly backward compatible with enhancements"
    else:
        compatibility['compatible'] = False
        compatibility['assessment'] = "Breaking changes detected"

    return compatibility

def print_compatibility_report(compatibility):
    """Print detailed compatibility report"""
    print(f"\n📋 COMPATIBILITY REPORT")
    print("=" * 50)
    print(f"Overall Assessment: {compatibility['assessment']}")
    print(f"Backward Compatible: {'✅ YES' if compatibility['compatible'] else '❌ NO'}")

    if compatibility['similarities']:
        print(f"\n✅ SIMILARITIES & ENHANCEMENTS:")
        for similarity in compatibility['similarities']:
            print(f"   {similarity}")

    if compatibility['differences']:
        print(f"\n❌ DIFFERENCES & ISSUES:")
        for difference in compatibility['differences']:
            print(f"   {difference}")

    print(f"\n⏱️ Performance Impact: {compatibility['performance_diff']:.2f}s")

def main():
    """Main compatibility testing function"""
    print("🔄 StrongAfter Therapy Assistant - Backward Compatibility Test")
    print("=" * 70)

    # Services configuration
    services = {
        'Original': 'http://127.0.0.1:5001',
        'Blackboard': 'http://127.0.0.1:5002'
    }

    # Test queries covering different scenarios
    test_cases = [
        "I'm having flashbacks from my childhood trauma",
        "What's your favorite pizza topping?",
        "I struggle with PTSD symptoms",
        "How do I fix my car?",
        "I feel overwhelmed by anxiety from my past"
    ]

    all_results = []

    for i, query in enumerate(test_cases, 1):
        print(f"\n{'='*70}")
        print(f"🧪 TEST CASE {i}/{len(test_cases)}")
        print(f"📝 Query: {query}")
        print(f"{'='*70}")

        # Test both services
        original_result = test_service(services['Original'], 'Original', query)
        blackboard_result = test_service(services['Blackboard'], 'Blackboard', query)

        # Compare compatibility
        compatibility = compare_responses(original_result, blackboard_result)
        print_compatibility_report(compatibility)

        # Store results
        test_result = {
            'query': query,
            'original': original_result,
            'blackboard': blackboard_result,
            'compatibility': compatibility
        }
        all_results.append(test_result)

        time.sleep(1)  # Brief pause between tests

    # Overall summary
    print(f"\n{'='*70}")
    print(f"📊 OVERALL COMPATIBILITY SUMMARY")
    print(f"{'='*70}")

    compatible_count = sum(1 for r in all_results if r['compatibility']['compatible'])
    total_tests = len(all_results)
    compatibility_percentage = (compatible_count / total_tests) * 100

    print(f"Compatible Tests: {compatible_count}/{total_tests} ({compatibility_percentage:.1f}%)")

    if compatibility_percentage >= 95:
        print("🎉 RESULT: 100% Backward Compatible")
    elif compatibility_percentage >= 80:
        print("✅ RESULT: Mostly Backward Compatible")
    else:
        print("❌ RESULT: Breaking Changes Detected")

    # Performance summary
    performance_improvements = [r['compatibility']['performance_diff'] for r in all_results
                              if r['compatibility']['performance_diff'] < 0]

    if performance_improvements:
        avg_improvement = abs(sum(performance_improvements) / len(performance_improvements))
        print(f"⚡ Average Performance Improvement: {avg_improvement:.2f}s")

    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"compatibility_test_{timestamp}.json"

    with open(filename, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)

    print(f"\n💾 Detailed results saved to: {filename}")
    print("🎉 Compatibility testing completed!")

if __name__ == "__main__":
    main()