"""Tests for Prompt Loader Service"""

import pytest
from pathlib import Path


class TestPromptLoader:
    """Test suite for PromptLoader class"""
    
    def test_prompt_loader_imports(self):
        """Test PromptLoader can be imported"""
        from app.services.prompt_loader import PromptLoader, PromptConfig
        assert PromptLoader is not None
        assert PromptConfig is not None

    def test_prompt_config_creation(self):
        """Test PromptConfig model creation"""
        from app.services.prompt_loader import PromptConfig
        
        config = PromptConfig(
            name="Test Mode",
            description="A test mode",
            system_instruction="You are a test assistant",
            output_format="markdown",
            guidelines=["Be helpful"]
        )
        
        assert config.name == "Test Mode"
        assert config.description == "A test mode"
        assert len(config.guidelines) == 1

    def test_prompt_config_defaults(self):
        """Test PromptConfig default values"""
        from app.services.prompt_loader import PromptConfig
        
        config = PromptConfig(
            name="Minimal",
            description="Minimal config",
            system_instruction="Hello",
            output_format="markdown"
        )
        
        assert config.guidelines == []
        assert config.output_format == "markdown"

    def test_list_available_modes(self):
        """Test listing available modes from actual prompts directory"""
        from app.services.prompt_loader import PromptLoader
        
        loader = PromptLoader()
        modes = loader.list_available_modes()
        
        assert isinstance(modes, list)
        assert len(modes) >= 1
        # Should have at least bug_report mode
        assert "bug_report" in modes

    def test_load_prompt_bug_report(self):
        """Test loading bug_report prompt"""
        from app.services.prompt_loader import PromptLoader
        
        loader = PromptLoader()
        config = loader.load_prompt("bug_report")
        
        assert config.name is not None
        assert len(config.system_instruction) > 0

    def test_load_prompt_with_context(self):
        """Test loading prompt with context interpolation"""
        from app.services.prompt_loader import PromptLoader
        
        loader = PromptLoader()
        context = {
            "meeting_title": "Design Review",
            "attendees": "Alice, Bob",
            "keywords": "UI, UX"
        }
        
        config = loader.load_prompt("bug_report", context=context)
        
        # Context should be interpolated if prompt has placeholders
        assert config is not None

    def test_prompt_not_found_error(self):
        """Test error handling for non-existent prompt"""
        from app.services.prompt_loader import PromptLoader, PromptLoadError
        
        loader = PromptLoader()
        
        with pytest.raises(PromptLoadError):
            loader.load_prompt("nonexistent_mode_xyz123")

    def test_get_modes_metadata(self):
        """Test getting modes metadata"""
        from app.services.prompt_loader import PromptLoader
        
        loader = PromptLoader()
        metadata = loader.get_modes_metadata()
        
        assert isinstance(metadata, list)
        assert len(metadata) >= 1
        # Each item should have mode, name, description
        for item in metadata:
            assert "mode" in item
            assert "name" in item
            assert "description" in item

    def test_cache_behavior(self):
        """Test prompt caching"""
        from app.services.prompt_loader import PromptLoader
        
        loader = PromptLoader()
        
        # Load same prompt twice
        config1 = loader.load_prompt("bug_report")
        config2 = loader.load_prompt("bug_report")
        
        # Should return same cached object
        assert config1 is config2
        
        # Clear cache
        loader.clear_cache()
        
        # Load again
        config3 = loader.load_prompt("bug_report")
        
        # Should be a new object (same content, different instance)
        assert config3 is not config1
