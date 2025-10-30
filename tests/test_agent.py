"""
Unit tests for Agent class.
"""

import unittest
from hsim.core.core.env import Environment
from hsim.core.agent.agent import Agent, dotdict


class TestAgent(unittest.TestCase):
    """Test cases for Agent class."""
    
    def test_agent_creation(self):
        """Test basic agent creation."""
        env = Environment()
        agent = Agent(env, "test_agent")
        
        self.assertEqual(agent.name, "test_agent")
        self.assertEqual(agent.env, env)
        self.assertIsNotNone(agent.stateMachine)
    
    def test_agent_without_name(self):
        """Test agent creation without explicit name."""
        env = Environment()
        agent = Agent(env)
        
        # Agent should still be created successfully
        self.assertIsNotNone(agent)
        self.assertEqual(agent.env, env)
    
    def test_agent_registered_in_environment(self):
        """Test that agent is registered in environment."""
        env = Environment()
        agent = Agent(env, "test_agent")
        
        self.assertIn("test_agent", env._agents)
        self.assertEqual(env._agents["test_agent"], agent)
    
    def test_agent_connections(self):
        """Test agent connections dictionary."""
        env = Environment()
        agent1 = Agent(env, "agent1")
        agent2 = Agent(env, "agent2")
        
        agent1.connections["next"] = agent2
        
        self.assertEqual(agent1.connections["next"], agent2)
    
    def test_agent_variables(self):
        """Test agent variable storage using dotdict."""
        env = Environment()
        agent = Agent(env, "test_agent")
        
        # dotdict should allow attribute-style access
        agent.var.custom_value = 42
        
        self.assertEqual(agent.var.custom_value, 42)
        self.assertIn("custom_value", agent.var.keys())


class TestDotDict(unittest.TestCase):
    """Test cases for dotdict class."""
    
    def test_dotdict_creation(self):
        """Test dotdict creation."""
        d = dotdict()
        self.assertIsInstance(d, dict)
    
    def test_dotdict_attribute_access(self):
        """Test attribute-style access."""
        d = dotdict()
        d.name = "test"
        d.value = 42
        
        self.assertEqual(d.name, "test")
        self.assertEqual(d.value, 42)
    
    def test_dotdict_dict_access(self):
        """Test dictionary-style access."""
        d = dotdict()
        d["name"] = "test"
        d["value"] = 42
        
        self.assertEqual(d["name"], "test")
        self.assertEqual(d["value"], 42)
    
    def test_dotdict_mixed_access(self):
        """Test that both access styles work together."""
        d = dotdict()
        d.name = "test"
        d["value"] = 42
        
        self.assertEqual(d["name"], "test")
        self.assertEqual(d.value, 42)
    
    def test_dotdict_deletion(self):
        """Test attribute deletion."""
        d = dotdict()
        d.name = "test"
        
        del d.name
        
        with self.assertRaises(AttributeError):
            _ = d.name


if __name__ == '__main__':
    unittest.main()
