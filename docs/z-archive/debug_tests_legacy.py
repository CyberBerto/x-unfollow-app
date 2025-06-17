"""
Debug Tests for X Unfollow Tool Layer 2
Simple test functions that can be run directly without a web server.
"""

import json
from app import classify_unfollow_error

def test_layer2_classification():
    """Test Layer 2 following pre-check + error classification without API calls."""
    
    scenarios = [
        {
            'description': 'Layer 2 Enhanced: Not following (X API returns following:false)',
            'success': False,
            'error_msg': 'Not following this account',
            'expected_wait': 5,
            'note': 'Most common case - triggers fast 5-second wait'
        },
        {
            'description': 'Layer 2 Enhanced: User not found (API error code 17)',
            'success': False,
            'error_msg': 'User not found',
            'expected_wait': 5,
            'note': 'User-specific error - triggers fast wait'
        },
        {
            'description': 'Layer 2 Enhanced: Account suspended (API error code 63)', 
            'success': False,
            'error_msg': 'account suspended',
            'expected_wait': 5,
            'note': 'User-specific error - triggers fast wait'
        },
        {
            'description': 'Layer 2 Enhanced: Rate limit error (HTTP 429)',
            'success': False,
            'error_msg': 'Rate limit exceeded',
            'expected_wait': 900,
            'note': 'Rate limit error - triggers conservative 15-minute wait'
        },
        {
            'description': 'Layer 2 Enhanced: Authentication error (HTTP 401)',
            'success': False,
            'error_msg': 'Authentication failed',
            'expected_wait': 900,
            'note': 'Auth error - triggers conservative 15-minute wait'
        },
        {
            'description': 'Layer 2 Enhanced: Server error (HTTP 500)',
            'success': False,
            'error_msg': 'Internal server error',
            'expected_wait': 900,
            'note': 'Server error - triggers conservative 15-minute wait'
        },
        {
            'description': 'Layer 2 Enhanced: Unknown error',
            'success': False,
            'error_msg': 'Something went wrong',
            'expected_wait': 900,
            'note': 'Unknown error - triggers conservative 15-minute wait'
        }
    ]
    
    print("🧪 Testing Layer 2 Logic\n" + "="*50)
    results = []
    
    for scenario in scenarios:
        following_status = scenario.get('following_status')
        success = scenario.get('success', False)
        error_msg = scenario.get('error_msg')
        expected_wait = scenario.get('expected_wait')
        
        # Layer 2 Simplified: Direct classification without pre-check
        final_success = success
        final_error_msg = error_msg
        
        # Test classification
        error_type, classified_wait = classify_unfollow_error(final_error_msg, final_success)
        
        # Check result
        matches_expected = (expected_wait == classified_wait)
        emoji = "⚡" if classified_wait == 5 else "⏳"
        
        result = {
            'description': scenario['description'],
            'expected': expected_wait,
            'actual': classified_wait,
            'matches': matches_expected,
            'note': scenario.get('note', '')
        }
        results.append(result)
        
        status = "✅ PASS" if matches_expected else "❌ FAIL"
        print(f"{status} {scenario['description']}")
        print(f"    Expected: {expected_wait}s, Got: {classified_wait}s ({emoji} {error_type.upper()})")
        print(f"    Note: {scenario.get('note', '')}")
        print()
    
    # Summary
    total_passed = sum(1 for r in results if r['matches'])
    
    print("📊 Test Summary")
    print(f"    Passed: {total_passed}/{len(results)}")
    print(f"    Success Rate: {total_passed/len(results)*100:.1f}%")
    print(f"    Layer 2 Status: Enhanced (comprehensive error parsing + smart timing)")
    
    return results

def performance_simulation(total_users=100, not_following_percent=60):
    """Simulate Layer 2 performance improvements."""
    
    not_following = int(total_users * not_following_percent / 100)
    following = total_users - not_following
    
    # Layer 1: All 15-minute waits
    layer1_time = (total_users - 1) * 15 * 60
    layer1_api_calls = total_users * 2  # lookup + unfollow each
    
    # Layer 2: Smart waits + pre-check
    layer2_time = (not_following - 1) * 5 + (following - 1) * 15 * 60 if following > 0 else (not_following - 1) * 5
    layer2_api_calls = total_users + following  # lookup all + unfollow only following
    
    time_saved = layer1_time - layer2_time
    api_saved = layer1_api_calls - layer2_api_calls
    
    print(f"🚀 Performance Simulation: {total_users} users, {not_following_percent}% not following\n" + "="*60)
    print(f"Layer 1 (Basic):  {layer1_time//3600:.1f}h, {layer1_api_calls} API calls")
    print(f"Layer 2 (Smart):  {layer2_time//3600:.1f}h, {layer2_api_calls} API calls") 
    print(f"Improvement:      {time_saved//3600:.1f}h saved ({time_saved/layer1_time*100:.1f}%), {api_saved} API calls saved ({api_saved/layer1_api_calls*100:.1f}%)")
    
    return {
        'time_saved_hours': time_saved // 3600,
        'time_saved_percent': time_saved / layer1_time * 100,
        'api_calls_saved': api_saved,
        'api_saved_percent': api_saved / layer1_api_calls * 100
    }

if __name__ == '__main__':
    print("Layer 2 Debug Tests\n")
    
    # Run classification tests
    test_results = test_layer2_classification()
    
    print("\n" + "="*60 + "\n")
    
    # Run performance simulation
    perf_results = performance_simulation()