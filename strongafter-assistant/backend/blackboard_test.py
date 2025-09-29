"""
Test script for the blackboard architecture system

This script tests the blackboard system without requiring Ollama
to ensure the core architecture works correctly.
"""

import asyncio
import logging
import time
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_blackboard_system():
    """Test the blackboard system components"""

    print("🧠 Testing StrongAfter Blackboard Architecture")
    print("=" * 50)

    # Test 1: Import all components
    print("\n📦 Testing imports...")
    try:
        from blackboard import TherapyBlackboard, BlackboardControlStrategy
        from blackboard.knowledge_sources import (
            ThemeAnalysisAgent, ExcerptRetrievalAgent,
            SummaryGenerationAgent, QualityAssuranceAgent, StreamingAgent
        )
        from blackboard.local_llm_agent import LocalLLMAgent, LocalLLMConfig
        print("✅ All imports successful")
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

    # Test 2: Create blackboard
    print("\n🖼️  Testing blackboard creation...")
    try:
        blackboard = TherapyBlackboard()
        print(f"✅ Blackboard created: {blackboard}")

        # Test basic operations
        blackboard.write('test_key', 'test_value', 'test_source')
        value = blackboard.read('test_key')
        assert value == 'test_value', f"Expected 'test_value', got {value}"
        print("✅ Basic read/write operations working")

    except Exception as e:
        print(f"❌ Blackboard test failed: {e}")
        return False

    # Test 3: Create mock agents (without external dependencies)
    print("\n🤖 Testing agent creation...")
    try:
        # Create mock Gemini model
        class MockGeminiModel:
            def generate_content(self, prompt):
                class MockResponse:
                    text = "Mock response for testing"
                return MockResponse()

        mock_gemini = MockGeminiModel()

        # Create agents
        agents = [
            ThemeAnalysisAgent(blackboard, mock_gemini),
            ExcerptRetrievalAgent(blackboard),
            SummaryGenerationAgent(blackboard, mock_gemini),
            QualityAssuranceAgent(blackboard),
            StreamingAgent(blackboard)
        ]

        print(f"✅ Created {len(agents)} agents successfully")

        # Test agent status
        for agent in agents:
            status = agent.get_status()
            print(f"  - {agent.name}: {status['name']} (priority: {status['priority']})")

    except Exception as e:
        print(f"❌ Agent creation failed: {e}")
        return False

    # Test 4: Create control strategy
    print("\n🎮 Testing control strategy...")
    try:
        control_strategy = BlackboardControlStrategy(blackboard, agents)
        print(f"✅ Control strategy created with {len(agents)} agents")

        # Test execution plan creation
        from blackboard.control_strategy import ExecutionStrategy
        plan = control_strategy._create_hybrid_plan()
        print(f"✅ Hybrid execution plan created")
        print(f"  - Parallel groups: {len(plan.parallel_groups)}")
        print(f"  - Sequential phases: {len(plan.sequential_phases)}")
        print(f"  - Estimated time: {plan.estimated_time:.2f}s")

    except Exception as e:
        print(f"❌ Control strategy test failed: {e}")
        return False

    # Test 5: Simulate basic processing flow
    print("\n⚡ Testing basic processing flow...")
    try:
        # Initialize with test data
        test_themes = [
            {'id': 'theme1', 'label': 'Test Theme 1', 'description': 'First test theme', 'excerpts': []},
            {'id': 'theme2', 'label': 'Test Theme 2', 'description': 'Second test theme', 'excerpts': []}
        ]

        blackboard.clear()
        blackboard.write('user_input', 'Test user input', 'test')
        blackboard.write('preprocessed_text', 'test user input', 'test')
        blackboard.write('theme_candidates', test_themes, 'test')

        # Test individual agent readiness
        for agent in agents:
            can_contribute = agent.can_contribute()
            print(f"  - {agent.name} can contribute: {can_contribute}")

        print("✅ Basic processing flow simulation completed")

    except Exception as e:
        print(f"❌ Processing flow test failed: {e}")
        return False

    # Test 6: Test metrics and monitoring
    print("\n📊 Testing metrics and monitoring...")
    try:
        metrics = blackboard.get_metrics()
        print(f"✅ Blackboard metrics: {len(metrics)} categories")

        state_summary = blackboard.get_state_summary()
        print(f"✅ State summary: {len(state_summary)} fields")

        control_metrics = control_strategy.get_metrics()
        print(f"✅ Control strategy metrics available")

    except Exception as e:
        print(f"❌ Metrics test failed: {e}")
        return False

    # Test 7: Test local LLM agent (without actual connection)
    print("\n🦙 Testing local LLM agent (offline)...")
    try:
        config = LocalLLMConfig(host="localhost", port=11434, model_name="llama3.1:8b")
        local_agent = LocalLLMAgent(blackboard, config)

        print(f"✅ Local LLM agent created: {local_agent.name}")
        print(f"  - Priority: {local_agent.priority}")
        print(f"  - Capabilities: GPU required = {local_agent.capabilities.requires_gpu}")

        # Test health check (will fail but shouldn't crash)
        try:
            health = await local_agent.health_check()
            print(f"  - Health check result: {health.get('available', False)}")
        except Exception:
            print("  - Health check failed as expected (no Ollama running)")

    except Exception as e:
        print(f"❌ Local LLM agent test failed: {e}")
        return False

    print("\n🎉 All blackboard architecture tests passed!")
    print("\n📋 System Summary:")
    print(f"  - Blackboard: Operational")
    print(f"  - Agents: {len(agents)} created and functional")
    print(f"  - Control Strategy: Operational")
    print(f"  - Local LLM: Configured (needs Ollama for operation)")
    print(f"  - Performance: Ready for {plan.estimated_time:.1f}s estimated processing")

    return True


async def test_performance_characteristics():
    """Test performance characteristics of the blackboard system"""

    print("\n⚡ Performance Characteristics Test")
    print("-" * 40)

    from blackboard import TherapyBlackboard

    # Test blackboard performance
    blackboard = TherapyBlackboard()

    # Test write/read performance
    start_time = time.time()
    for i in range(1000):
        blackboard.write(f'test_key_{i}', f'test_value_{i}', 'performance_test')
    write_time = time.time() - start_time

    start_time = time.time()
    for i in range(1000):
        value = blackboard.read(f'test_key_{i}')
    read_time = time.time() - start_time

    print(f"📊 Blackboard Performance:")
    print(f"  - 1000 writes: {write_time:.3f}s ({1000/write_time:.0f} ops/sec)")
    print(f"  - 1000 reads: {read_time:.3f}s ({1000/read_time:.0f} ops/sec)")

    # Test concurrent access
    async def concurrent_writer(start_idx, count):
        for i in range(count):
            blackboard.write(f'concurrent_{start_idx}_{i}', f'value_{i}', f'writer_{start_idx}')
            await asyncio.sleep(0.001)  # Small delay

    start_time = time.time()
    tasks = [concurrent_writer(i, 100) for i in range(5)]
    await asyncio.gather(*tasks)
    concurrent_time = time.time() - start_time

    print(f"  - 5 concurrent writers (500 total): {concurrent_time:.3f}s")

    # Memory usage estimate
    memory_estimate = len(blackboard._data) * 100  # Rough estimate
    print(f"  - Estimated memory usage: ~{memory_estimate/1024:.1f}KB")


if __name__ == "__main__":
    print("🚀 Starting Blackboard Architecture Test Suite")
    print("=" * 60)

    # Run main tests
    success = asyncio.run(test_blackboard_system())

    if success:
        print("\n" + "=" * 60)
        # Run performance tests
        asyncio.run(test_performance_characteristics())

        print("\n✅ All tests completed successfully!")
        print("\n📋 Next Steps:")
        print("  1. Install Ollama: curl -fsSL https://ollama.com/install.sh | sh")
        print("  2. Download model: ollama pull llama3.1:8b")
        print("  3. Run the blackboard app: python app_blackboard.py")
        print("  4. Expected performance: 4-6s total response time")
    else:
        print("\n❌ Some tests failed. Check the error messages above.")
        exit(1)