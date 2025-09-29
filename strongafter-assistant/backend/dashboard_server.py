#!/usr/bin/env python3
"""
Performance Dashboard Server for StrongAfter Optimization Comparison

Serves the performance dashboard and provides real-time metrics endpoints
for comparing original vs optimized StrongAfter text processing performance.
"""

from flask import Flask, render_template_string, jsonify, send_from_directory
from flask_cors import CORS
import os
import requests
import time
import threading
import statistics
from collections import deque
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

# Performance data storage
performance_data = {
    'original': {
        'latencies': deque(maxlen=100),  # Keep last 100 requests
        'token_rates': deque(maxlen=100),  # Keep last 100 token rates (tokens/sec)
        'total_tokens': deque(maxlen=100),  # Keep last 100 total token counts
        'success_count': 0,
        'total_count': 0,
        'last_update': None
    },
    'optimized': {
        'latencies': deque(maxlen=100),
        'token_rates': deque(maxlen=100),
        'total_tokens': deque(maxlen=100),
        'success_count': 0,
        'total_count': 0,
        'last_update': None
    }
}

# Service endpoints
ORIGINAL_URL = 'http://localhost:5001/api'
OPTIMIZED_URL = 'http://localhost:5002/api'

def estimate_token_count(text):
    """Estimate token count (rough approximation: ~4 chars per token)"""
    return len(text) // 4

def extract_response_text(response_data):
    """Extract text content from API response for token counting"""
    try:
        if 'summary' in response_data:
            return response_data['summary']
        elif 'themes' in response_data and response_data['themes']:
            # Combine theme descriptions and any excerpt summaries
            text_parts = []
            for theme in response_data['themes']:
                if theme.get('excerpt_summary'):
                    text_parts.append(theme['excerpt_summary'])
                if theme.get('description'):
                    text_parts.append(theme['description'])
            return ' '.join(text_parts)
        return str(response_data)  # Fallback to full response
    except:
        return ""

def check_service_health(url):
    """Check if a service is healthy and responding"""
    try:
        response = requests.get(f"{url}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

@app.route('/')
def dashboard():
    """Serve the performance dashboard"""
    try:
        with open('dashboard.html', 'r', encoding='utf-8') as f:
            dashboard_html = f.read()
        return dashboard_html
    except FileNotFoundError:
        return "Dashboard HTML file not found", 404

@app.route('/api/health')
def health_check():
    """Health check for both services"""
    original_healthy = check_service_health(ORIGINAL_URL)
    optimized_healthy = check_service_health(OPTIMIZED_URL)
    
    return jsonify({
        'dashboard_healthy': True,
        'original_service': {
            'healthy': original_healthy,
            'url': ORIGINAL_URL
        },
        'optimized_service': {
            'healthy': optimized_healthy,
            'url': OPTIMIZED_URL
        }
    })

@app.route('/api/metrics')
def get_metrics():
    """Get current performance metrics"""
    def calculate_stats(latencies):
        if not latencies:
            return {'p50': 0, 'p95': 0, 'mean': 0, 'count': 0}
        
        sorted_latencies = sorted(latencies)
        return {
            'p50': sorted_latencies[int(len(sorted_latencies) * 0.5)],
            'p95': sorted_latencies[int(len(sorted_latencies) * 0.95)],
            'mean': statistics.mean(latencies),
            'count': len(latencies)
        }
    
    original_stats = calculate_stats(list(performance_data['original']['latencies']))
    optimized_stats = calculate_stats(list(performance_data['optimized']['latencies']))
    
    # Calculate token rate statistics
    original_token_rates = calculate_stats(list(performance_data['original']['token_rates']))
    optimized_token_rates = calculate_stats(list(performance_data['optimized']['token_rates']))
    
    # Calculate average total tokens
    original_avg_tokens = statistics.mean(list(performance_data['original']['total_tokens'])) if performance_data['original']['total_tokens'] else 0
    optimized_avg_tokens = statistics.mean(list(performance_data['optimized']['total_tokens'])) if performance_data['optimized']['total_tokens'] else 0
    
    # Calculate success rates
    original_success_rate = (
        performance_data['original']['success_count'] / 
        max(performance_data['original']['total_count'], 1) * 100
    )
    
    optimized_success_rate = (
        performance_data['optimized']['success_count'] / 
        max(performance_data['optimized']['total_count'], 1) * 100
    )
    
    # Calculate improvement percentages
    improvement = {}
    if original_stats['p95'] > 0:
        improvement['p95'] = (
            (original_stats['p95'] - optimized_stats['p95']) / 
            original_stats['p95'] * 100
        )
    
    if original_stats['p50'] > 0:
        improvement['p50'] = (
            (original_stats['p50'] - optimized_stats['p50']) / 
            original_stats['p50'] * 100
        )
    
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'original': {
            'stats': original_stats,
            'token_rates': original_token_rates,
            'avg_tokens': original_avg_tokens,
            'success_rate': original_success_rate,
            'last_update': performance_data['original']['last_update']
        },
        'optimized': {
            'stats': optimized_stats,
            'token_rates': optimized_token_rates,
            'avg_tokens': optimized_avg_tokens,
            'success_rate': optimized_success_rate,
            'last_update': performance_data['optimized']['last_update']
        },
        'improvement': improvement,
        'services_healthy': {
            'original': check_service_health(ORIGINAL_URL),
            'optimized': check_service_health(OPTIMIZED_URL)
        }
    })

@app.route('/api/test', methods=['POST'])
def run_test():
    """Run a test against both services and record metrics"""
    from flask import request
    
    test_text = request.json.get('text', 'I feel stressed and need help')
    
    results = {
        'original': None,
        'optimized': None,
        'timestamp': datetime.now().isoformat()
    }
    
    # Test original service
    try:
        start_time = time.time()
        response = requests.post(
            f"{ORIGINAL_URL}/process-text",
            json={'text': test_text},
            timeout=45
        )
        latency = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        performance_data['original']['total_count'] += 1
        performance_data['original']['last_update'] = datetime.now().isoformat()
        
        if response.status_code == 200:
            performance_data['original']['success_count'] += 1
            performance_data['original']['latencies'].append(latency)
            
            # Extract and count tokens
            response_data = response.json()
            response_text = extract_response_text(response_data)
            total_tokens = estimate_token_count(response_text)
            token_rate = (total_tokens / (latency / 1000)) if latency > 0 else 0  # tokens per second
            
            performance_data['original']['total_tokens'].append(total_tokens)
            performance_data['original']['token_rates'].append(token_rate)
            
            results['original'] = {
                'success': True,
                'latency': latency,
                'status_code': response.status_code,
                'total_tokens': total_tokens,
                'token_rate': token_rate
            }
        else:
            results['original'] = {
                'success': False,
                'latency': latency,
                'status_code': response.status_code,
                'error': 'HTTP Error'
            }
            
    except Exception as e:
        performance_data['original']['total_count'] += 1
        performance_data['original']['last_update'] = datetime.now().isoformat()
        results['original'] = {
            'success': False,
            'latency': 45000,  # Timeout latency
            'error': str(e)
        }
    
    # Test optimized service
    try:
        start_time = time.time()
        response = requests.post(
            f"{OPTIMIZED_URL}/process-text",
            json={'text': test_text},
            timeout=45
        )
        latency = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        performance_data['optimized']['total_count'] += 1
        performance_data['optimized']['last_update'] = datetime.now().isoformat()
        
        if response.status_code == 200:
            performance_data['optimized']['success_count'] += 1
            performance_data['optimized']['latencies'].append(latency)
            
            # Extract and count tokens
            response_data = response.json()
            response_text = extract_response_text(response_data)
            total_tokens = estimate_token_count(response_text)
            token_rate = (total_tokens / (latency / 1000)) if latency > 0 else 0  # tokens per second
            
            performance_data['optimized']['total_tokens'].append(total_tokens)
            performance_data['optimized']['token_rates'].append(token_rate)
            
            results['optimized'] = {
                'success': True,
                'latency': latency,
                'status_code': response.status_code,
                'total_tokens': total_tokens,
                'token_rate': token_rate
            }
        else:
            results['optimized'] = {
                'success': False,
                'latency': latency,
                'status_code': response.status_code,
                'error': 'HTTP Error'
            }
            
    except Exception as e:
        performance_data['optimized']['total_count'] += 1
        performance_data['optimized']['last_update'] = datetime.now().isoformat()
        results['optimized'] = {
            'success': False,
            'latency': 45000,  # Timeout latency
            'error': str(e)
        }
    
    return jsonify(results)

@app.route('/api/clear', methods=['POST'])
def clear_metrics():
    """Clear all performance metrics"""
    global performance_data
    
    performance_data = {
        'original': {
            'latencies': deque(maxlen=100),
            'token_rates': deque(maxlen=100),
            'total_tokens': deque(maxlen=100),
            'success_count': 0,
            'total_count': 0,
            'last_update': None
        },
        'optimized': {
            'latencies': deque(maxlen=100),
            'token_rates': deque(maxlen=100),
            'total_tokens': deque(maxlen=100),
            'success_count': 0,
            'total_count': 0,
            'last_update': None
        }
    }
    
    return jsonify({'status': 'cleared', 'timestamp': datetime.now().isoformat()})

@app.route('/api/latency-data')
def get_latency_data():
    """Get latency data for charting"""
    return jsonify({
        'original': list(performance_data['original']['latencies']),
        'optimized': list(performance_data['optimized']['latencies']),
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("🚀 Starting StrongAfter Performance Dashboard")
    print(f"📊 Dashboard: http://localhost:8080")
    print(f"🔗 Original API: {ORIGINAL_URL}")
    print(f"⚡ Optimized API: {OPTIMIZED_URL}")
    print("✨ Dashboard features:")
    print("   - Real-time performance comparison")
    print("   - P50/P95 latency tracking")
    print("   - Success rate monitoring") 
    print("   - Live charting and metrics")
    print("   - Single test, burst test, and continuous testing")
    
    app.run(
        host='0.0.0.0',
        port=8080,
        debug=True,
        threaded=True
    )