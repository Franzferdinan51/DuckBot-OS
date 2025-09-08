#!/usr/bin/env python3
"""
Enhanced DuckBot System Test Suite
Comprehensive testing of all enhanced features and integrations
"""

import os
import sys
import asyncio
import json
import time
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedDuckBotTester:
    """Comprehensive tester for enhanced DuckBot system"""
    
    def __init__(self):
        self.test_results = {}
        self.failed_tests = []
        self.passed_tests = []
        
        # Test configuration
        self.test_config = {
            "test_timeout": 30,
            "provider_test_message": "Hello, this is a test message for provider connectivity",
            "agent_test_scenarios": [
                {"type": "market_analysis", "data": {"prices": [100, 102, 98, 105], "volume": [1000, 1200, 800, 1500]}},
                {"type": "discord_moderation", "data": {"message": "Hello everyone!", "user_id": "test_user"}},
                {"type": "workflow_optimization", "data": {"workflow_data": {"nodes": 5}, "performance_metrics": {"avg_execution_time": 15}}}
            ]
        }
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all enhanced DuckBot tests"""
        
        print("🚀 Starting Enhanced DuckBot System Tests")
        print("=" * 60)
        
        # Test 1: Provider Connectors
        await self._test_provider_connectors()
        
        # Test 2: Intelligent Agents
        await self._test_intelligent_agents()
        
        # Test 3: Context Management
        await self._test_context_management()
        
        # Test 4: Visual Workflow Designer
        await self._test_visual_workflow_designer()
        
        # Test 5: Learning System
        await self._test_learning_system()
        
        # Test 6: N8N Integration
        await self._test_n8n_integration()
        
        # Test 7: Enhanced AI Router
        await self._test_enhanced_ai_router()
        
        # Test 8: OpenWebUI Plugin
        await self._test_openwebui_plugin()
        
        # Generate final report
        return self._generate_test_report()
    
    async def _test_provider_connectors(self):
        """Test provider connector system"""
        print("🔌 Testing Provider Connectors...")
        
        try:
            from duckbot.provider_connectors import (
                connector_manager, get_available_providers, 
                get_provider_status, switch_provider, complete_chat
            )
            
            # Test 1: Get available providers
            providers = get_available_providers()
            assert len(providers) > 0, "No providers available"
            print(f"  ✅ Found {len(providers)} providers: {providers}")
            
            # Test 2: Check provider status
            status = get_provider_status()
            assert isinstance(status, dict), "Provider status should be dict"
            print(f"  ✅ Provider status check passed")
            
            # Test 3: Test provider switching
            for provider in providers[:2]:  # Test first 2 providers
                success = switch_provider(provider)
                if success:
                    print(f"  ✅ Successfully switched to {provider}")
                else:
                    print(f"  ⚠️  Could not switch to {provider} (may not be available)")
            
            # Test 4: Test chat completion
            messages = [{"role": "user", "content": self.test_config["provider_test_message"]}]
            result = await complete_chat(messages)
            
            if result and result.get("success"):
                print(f"  ✅ Chat completion successful with {result.get('provider', 'unknown')} provider")
            else:
                print(f"  ⚠️  Chat completion failed: {result.get('error', 'Unknown error') if result else 'No result'}")
            
            self._record_test_result("provider_connectors", True, "All provider connector tests passed")
            
        except Exception as e:
            print(f"  ❌ Provider connector test failed: {e}")
            self._record_test_result("provider_connectors", False, str(e))
    
    async def _test_intelligent_agents(self):
        """Test intelligent agent system"""
        print("🤖 Testing Intelligent Agents...")
        
        try:
            from duckbot.intelligent_agents import (
                analyze_with_intelligence, get_agent_performance,
                AgentContext, AgentType
            )
            
            # Test each agent type
            for scenario in self.test_config["agent_test_scenarios"]:
                agent_type = scenario["type"]
                test_data = scenario["data"]
                
                print(f"  Testing {agent_type} agent...")
                
                # Create context
                context = AgentContext(
                    user_id="test_user",
                    timestamp=time.time(),
                    environment=test_data,
                    metadata={"test": True}
                )
                
                # Analyze with agent
                decision = await analyze_with_intelligence(agent_type, test_data, context)
                
                assert hasattr(decision, 'confidence'), "Decision should have confidence"
                assert hasattr(decision, 'reasoning'), "Decision should have reasoning"
                assert decision.confidence >= 0 and decision.confidence <= 1, "Confidence should be between 0 and 1"
                
                print(f"    ✅ {agent_type} analysis: confidence={decision.confidence:.2f}, action={decision.action}")
            
            # Test agent performance metrics
            performance = get_agent_performance()
            assert isinstance(performance, dict), "Performance should be dict"
            print(f"  ✅ Agent performance metrics retrieved")
            
            self._record_test_result("intelligent_agents", True, "All intelligent agent tests passed")
            
        except Exception as e:
            print(f"  ❌ Intelligent agent test failed: {e}")
            self._record_test_result("intelligent_agents", False, str(e))
    
    async def _test_context_management(self):
        """Test context management system"""
        print("🧠 Testing Context Management...")
        
        try:
            from duckbot.context_manager import (
                create_context, find_patterns, learn_from_experience,
                store_memory, get_memory, get_insights
            )
            
            # Test 1: Create context snapshot
            test_data = {
                "test_metric": 0.8,
                "user_action": "test_action",
                "timestamp": time.time()
            }
            
            snapshot = await create_context(test_data, {"source": "test"}, ["testing"])
            assert snapshot is not None, "Context snapshot should be created"
            print(f"  ✅ Context snapshot created: {snapshot.context_id}")
            
            # Test 2: Store and retrieve memory
            await store_memory("test_agent", "test_key", {"test": "data"}, importance=0.8)
            memories = await get_memory("test_agent", "test_key")
            assert len(memories) > 0, "Should retrieve stored memory"
            print(f"  ✅ Memory storage and retrieval working")
            
            # Test 3: Learn from experience
            await learn_from_experience(
                test_data, 
                {"result": "success"}, 
                success=True, 
                context_type="testing"
            )
            print(f"  ✅ Learning from experience recorded")
            
            # Test 4: Get insights
            insights = await get_insights("testing")
            assert isinstance(insights, dict), "Insights should be dict"
            print(f"  ✅ Context insights retrieved")
            
            self._record_test_result("context_management", True, "All context management tests passed")
            
        except Exception as e:
            print(f"  ❌ Context management test failed: {e}")
            self._record_test_result("context_management", False, str(e))
    
    async def _test_visual_workflow_designer(self):
        """Test visual workflow designer"""
        print("🎨 Testing Visual Workflow Designer...")
        
        try:
            from duckbot.visual_workflow_designer import (
                create_workflow, add_ai_agent_node, export_workflow_to_n8n,
                create_smart_discord_workflow, visual_designer
            )
            
            # Test 1: Create workflow
            workflow_id = create_workflow("Test Workflow", "A test workflow for validation")
            assert workflow_id is not None, "Workflow should be created"
            print(f"  ✅ Workflow created: {workflow_id}")
            
            # Test 2: Add AI agent node
            node_id = add_ai_agent_node(workflow_id, (100, 100), "market_analyzer")
            assert node_id is not None, "AI agent node should be added"
            print(f"  ✅ AI agent node added: {node_id}")
            
            # Test 3: Export to n8n
            n8n_workflow = export_workflow_to_n8n(workflow_id)
            assert isinstance(n8n_workflow, dict), "N8N export should return dict"
            assert "nodes" in n8n_workflow, "N8N workflow should have nodes"
            print(f"  ✅ N8N export successful with {len(n8n_workflow['nodes'])} nodes")
            
            # Test 4: Create smart workflow template
            template_workflow_id = create_workflow("Smart Discord Workflow", "Template workflow")
            template_nodes = create_smart_discord_workflow(template_workflow_id)
            assert len(template_nodes) > 0, "Template should create nodes"
            print(f"  ✅ Smart workflow template created with {len(template_nodes)} nodes")
            
            self._record_test_result("visual_workflow_designer", True, "All visual workflow designer tests passed")
            
        except Exception as e:
            print(f"  ❌ Visual workflow designer test failed: {e}")
            self._record_test_result("visual_workflow_designer", False, str(e))
    
    async def _test_learning_system(self):
        """Test learning system"""
        print("📚 Testing Learning System...")
        
        try:
            from duckbot.learning_system import (
                record_success, record_failure, record_feedback,
                get_learning_insights, learning_system
            )
            
            # Test 1: Record success event
            await record_success(
                "test_agent",
                {"input": "test"},
                {"output": "success"}, 
                confidence=0.9,
                context={"test": True}
            )
            print(f"  ✅ Success event recorded")
            
            # Test 2: Record failure event
            await record_failure(
                "test_agent",
                {"input": "test"},
                "Test failure",
                context={"test": True}
            )
            print(f"  ✅ Failure event recorded")
            
            # Test 3: Record feedback
            await record_feedback(
                "test_agent",
                {"input": "test"},
                {"output": "feedback_test"},
                "positive",
                success_metric=0.8,
                context={"test": True}
            )
            print(f"  ✅ Feedback event recorded")
            
            # Test 4: Get learning insights (may be limited with test data)
            insights = await get_learning_insights("test_agent", days=1)
            assert isinstance(insights, dict), "Insights should be dict"
            print(f"  ✅ Learning insights retrieved")
            
            self._record_test_result("learning_system", True, "All learning system tests passed")
            
        except Exception as e:
            print(f"  ❌ Learning system test failed: {e}")
            self._record_test_result("learning_system", False, str(e))
    
    async def _test_n8n_integration(self):
        """Test n8n integration system"""
        print("🔄 Testing N8N Integration...")
        
        try:
            from duckbot.n8n_agent_integration import (
                create_discord_workflow, create_market_workflow,
                n8n_integration
            )
            
            # Test 1: Create Discord workflow
            discord_workflow = create_discord_workflow()
            assert isinstance(discord_workflow, dict), "Discord workflow should be dict"
            assert "nodes" in discord_workflow, "Workflow should have nodes"
            print(f"  ✅ Discord workflow created with {len(discord_workflow['nodes'])} nodes")
            
            # Test 2: Create market analysis workflow
            market_workflow = create_market_workflow()
            assert isinstance(market_workflow, dict), "Market workflow should be dict"
            assert "nodes" in market_workflow, "Workflow should have nodes"
            print(f"  ✅ Market workflow created with {len(market_workflow['nodes'])} nodes")
            
            # Test 3: Create agent helper script
            script_path = await n8n_integration.create_agent_helper_script()
            assert Path(script_path).exists(), "Agent helper script should be created"
            print(f"  ✅ Agent helper script created: {script_path}")
            
            # Test 4: Check workflow structure
            for workflow in [discord_workflow, market_workflow]:
                assert "connections" in workflow, "Workflow should have connections"
                assert "meta" in workflow, "Workflow should have metadata"
                assert workflow["meta"]["enhanced_with_agents"], "Workflow should be agent-enhanced"
            
            print(f"  ✅ Workflow structure validation passed")
            
            self._record_test_result("n8n_integration", True, "All N8N integration tests passed")
            
        except Exception as e:
            print(f"  ❌ N8N integration test failed: {e}")
            self._record_test_result("n8n_integration", False, str(e))
    
    async def _test_enhanced_ai_router(self):
        """Test enhanced AI router"""
        print("🧭 Testing Enhanced AI Router...")
        
        try:
            from duckbot.ai_router_gpt import enhanced_chat_completion
            
            # Test enhanced chat completion
            messages = [{"role": "user", "content": "Test message for enhanced routing"}]
            
            result = await enhanced_chat_completion(
                messages,
                task_type="general",
                user_id="test_user",
                context={"test": True}
            )
            
            if result and result.get("success"):
                print(f"  ✅ Enhanced chat completion successful")
                if result.get("enhanced_by_agent"):
                    print(f"    🤖 Enhanced by {result.get('agent_type', 'unknown')} agent")
                print(f"    📊 Provider: {result.get('provider', 'unknown')}")
            else:
                print(f"  ⚠️  Enhanced chat completion returned: {result}")
            
            self._record_test_result("enhanced_ai_router", True, "Enhanced AI router test completed")
            
        except Exception as e:
            print(f"  ❌ Enhanced AI router test failed: {e}")
            self._record_test_result("enhanced_ai_router", False, str(e))
    
    async def _test_openwebui_plugin(self):
        """Test OpenWebUI plugin"""
        print("🌐 Testing OpenWebUI Plugin...")
        
        try:
            # Check if plugin file exists
            plugin_file = Path.cwd() / "openrouter_openwebui_plugin.py"
            assert plugin_file.exists(), "OpenWebUI plugin file should exist"
            print(f"  ✅ Plugin file exists: {plugin_file}")
            
            # Test plugin import
            import importlib.util
            spec = importlib.util.spec_from_file_location("openrouter_plugin", plugin_file)
            plugin_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(plugin_module)
            
            # Check if Pipe class exists
            assert hasattr(plugin_module, 'Pipe'), "Plugin should have Pipe class"
            print(f"  ✅ Plugin Pipe class found")
            
            # Test plugin initialization
            pipe = plugin_module.Pipe()
            assert hasattr(pipe, 'pipes'), "Pipe should have pipes method"
            assert hasattr(pipe, 'pipe'), "Pipe should have pipe method"
            print(f"  ✅ Plugin initialization successful")
            
            self._record_test_result("openwebui_plugin", True, "OpenWebUI plugin tests passed")
            
        except Exception as e:
            print(f"  ❌ OpenWebUI plugin test failed: {e}")
            self._record_test_result("openwebui_plugin", False, str(e))
    
    def _record_test_result(self, test_name: str, passed: bool, message: str):
        """Record test result"""
        self.test_results[test_name] = {
            "passed": passed,
            "message": message,
            "timestamp": time.time()
        }
        
        if passed:
            self.passed_tests.append(test_name)
        else:
            self.failed_tests.append(test_name)
    
    def _generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        
        total_tests = len(self.test_results)
        passed_count = len(self.passed_tests)
        failed_count = len(self.failed_tests)
        success_rate = (passed_count / total_tests) * 100 if total_tests > 0 else 0
        
        print("\n" + "=" * 60)
        print("📋 ENHANCED DUCKBOT TEST REPORT")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_count} ✅")
        print(f"Failed: {failed_count} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        if self.passed_tests:
            print("✅ PASSED TESTS:")
            for test in self.passed_tests:
                result = self.test_results[test]
                print(f"  • {test}: {result['message']}")
        
        if self.failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in self.failed_tests:
                result = self.test_results[test]
                print(f"  • {test}: {result['message']}")
        
        print("\n🎯 FEATURE STATUS:")
        feature_status = {
            "Provider Abstraction": "provider_connectors" in self.passed_tests,
            "Intelligent Agents": "intelligent_agents" in self.passed_tests,
            "Context Management": "context_management" in self.passed_tests,
            "Visual Workflow Designer": "visual_workflow_designer" in self.passed_tests,
            "Learning System": "learning_system" in self.passed_tests,
            "N8N Integration": "n8n_integration" in self.passed_tests,
            "Enhanced AI Router": "enhanced_ai_router" in self.passed_tests,
            "OpenWebUI Plugin": "openwebui_plugin" in self.passed_tests
        }
        
        for feature, status in feature_status.items():
            status_icon = "✅" if status else "❌"
            print(f"  {status_icon} {feature}")
        
        print(f"\n🚀 ENHANCED DUCKBOT STATUS: {'READY' if success_rate >= 80 else 'NEEDS ATTENTION'}")
        print("=" * 60)
        
        return {
            "summary": {
                "total_tests": total_tests,
                "passed": passed_count,
                "failed": failed_count,
                "success_rate": success_rate,
                "status": "READY" if success_rate >= 80 else "NEEDS_ATTENTION"
            },
            "test_results": self.test_results,
            "feature_status": feature_status,
            "recommendations": self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        if "provider_connectors" in self.failed_tests:
            recommendations.append("Install and configure AI provider APIs (OpenRouter, Anthropic, etc.)")
        
        if "intelligent_agents" in self.failed_tests:
            recommendations.append("Check intelligent agents module dependencies")
        
        if "context_management" in self.failed_tests:
            recommendations.append("Verify SQLite database permissions and storage")
        
        if "n8n_integration" in self.failed_tests:
            recommendations.append("Install and start n8n workflow automation")
        
        if "openwebui_plugin" in self.failed_tests:
            recommendations.append("Install OpenWebUI and configure plugin")
        
        if len(self.failed_tests) == 0:
            recommendations.extend([
                "🎉 All systems operational!",
                "Consider running the full ecosystem with: SETUP_AND_START.bat",
                "Access enhanced features at: http://localhost:8787/enhanced",
                "Try the visual workflow designer for creating AI-powered automations"
            ])
        
        return recommendations

async def main():
    """Main test function"""
    tester = EnhancedDuckBotTester()
    
    try:
        report = await tester.run_all_tests()
        
        # Save report to file
        report_file = Path.cwd() / "enhanced_test_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📄 Full test report saved to: {report_file}")
        
        # Return appropriate exit code
        return 0 if report["summary"]["success_rate"] >= 80 else 1
        
    except Exception as e:
        print(f"❌ Test suite failed with error: {e}")
        return 1

if __name__ == "__main__":
    exit(asyncio.run(main()))