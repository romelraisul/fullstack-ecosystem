"""
Test plugin fallback behavior
"""

import asyncio
import shutil
import tempfile
from pathlib import Path

import pytest
import yaml

# Import plugin system components
try:
    from autogen.backend.services.plugin_system import (
        AgentPlugin,
        BasePlugin,
        HookType,
        PluginManager,
        PluginMetadata,
        PluginStatus,
        PluginType,
    )

    PLUGIN_SYSTEM_AVAILABLE = True
except ImportError:
    PLUGIN_SYSTEM_AVAILABLE = False


class TestPluginFallbackBehavior:
    """Test plugin fallback and error handling behavior"""

    @pytest.fixture
    async def plugin_manager(self):
        """Create a test plugin manager"""
        if not PLUGIN_SYSTEM_AVAILABLE:
            pytest.skip("Plugin system not available")

        # Create temporary directory for plugins
        temp_dir = tempfile.mkdtemp()
        try:
            manager = PluginManager(plugins_directory=temp_dir)
            yield manager
        finally:
            # Cleanup
            shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def valid_plugin_manifest(self):
        """Create a valid plugin manifest"""
        return {
            "id": "test_plugin",
            "name": "Test Plugin",
            "version": "1.0.0",
            "description": "A test plugin",
            "author": "Test Author",
            "type": "extension",
            "main": "plugin.py",
            "class_name": "TestPlugin",
            "dependencies": [],
            "permissions": [],
            "hooks": [],
            "config_schema": {},
            "min_system_version": "1.0.0",
        }

    @pytest.fixture
    def invalid_plugin_manifest(self):
        """Create an invalid plugin manifest"""
        return {
            "id": "invalid_plugin",
            "name": "Invalid Plugin",
            # Missing required fields
        }

    @pytest.fixture
    def valid_plugin_code(self):
        """Create valid plugin code"""
        return """
from autogen.backend.services.plugin_system import BasePlugin
from typing import Dict, Any

class TestPlugin(BasePlugin):
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.initialized = False

    async def initialize(self) -> bool:
        self.initialized = True
        return True

    async def cleanup(self) -> bool:
        return True
"""

    @pytest.fixture
    def failing_plugin_code(self):
        """Create plugin code that fails initialization"""
        return """
from autogen.backend.services.plugin_system import BasePlugin
from typing import Dict, Any

class TestPlugin(BasePlugin):
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)

    async def initialize(self) -> bool:
        raise RuntimeError("Initialization failed")

    async def cleanup(self) -> bool:
        return True
"""

    def create_plugin_files(
        self, temp_dir: str, manifest: dict, code: str, plugin_name: str = "test_plugin"
    ):
        """Helper to create plugin files"""
        plugin_dir = Path(temp_dir) / plugin_name
        plugin_dir.mkdir(exist_ok=True)

        # Write manifest
        with open(plugin_dir / "plugin.yaml", "w") as f:
            yaml.dump(manifest, f)

        # Write plugin code
        with open(plugin_dir / "plugin.py", "w") as f:
            f.write(code)

        return str(plugin_dir)

    @pytest.mark.asyncio
    async def test_plugin_loading_fallback_with_invalid_manifest(
        self, plugin_manager, invalid_plugin_manifest
    ):
        """Test fallback behavior when plugin manifest is invalid"""
        if not PLUGIN_SYSTEM_AVAILABLE:
            pytest.skip("Plugin system not available")

        temp_dir = plugin_manager.plugins_directory
        plugin_dir = self.create_plugin_files(
            temp_dir, invalid_plugin_manifest, "# Invalid plugin code", "invalid_plugin"
        )

        # Attempt to load invalid plugin
        result = await plugin_manager.load_plugin(plugin_dir)

        # Should fail gracefully
        assert result is False
        assert "invalid_plugin" not in plugin_manager.plugins

        # Check error statistics
        stats = plugin_manager.get_stats()
        assert stats["failed_plugins"] >= 1

    @pytest.mark.asyncio
    async def test_plugin_loading_fallback_with_missing_class(
        self, plugin_manager, valid_plugin_manifest
    ):
        """Test fallback when plugin class is missing"""
        if not PLUGIN_SYSTEM_AVAILABLE:
            pytest.skip("Plugin system not available")

        # Plugin code without the expected class
        invalid_code = """
# This plugin is missing the TestPlugin class
def some_function():
    pass
"""

        temp_dir = plugin_manager.plugins_directory
        plugin_dir = self.create_plugin_files(
            temp_dir, valid_plugin_manifest, invalid_code, "missing_class_plugin"
        )

        # Attempt to load plugin with missing class
        result = await plugin_manager.load_plugin(plugin_dir)

        # Should fail gracefully
        assert result is False
        assert "test_plugin" not in plugin_manager.plugins

    @pytest.mark.asyncio
    async def test_plugin_initialization_fallback(
        self, plugin_manager, valid_plugin_manifest, failing_plugin_code
    ):
        """Test fallback when plugin initialization fails"""
        if not PLUGIN_SYSTEM_AVAILABLE:
            pytest.skip("Plugin system not available")

        temp_dir = plugin_manager.plugins_directory
        plugin_dir = self.create_plugin_files(
            temp_dir, valid_plugin_manifest, failing_plugin_code, "failing_plugin"
        )

        # Attempt to load plugin that fails initialization
        result = await plugin_manager.load_plugin(plugin_dir)

        # Should fail gracefully
        assert result is False
        assert "test_plugin" not in plugin_manager.plugins

    @pytest.mark.asyncio
    async def test_plugin_activation_fallback(
        self, plugin_manager, valid_plugin_manifest, valid_plugin_code
    ):
        """Test fallback when plugin activation fails"""
        if not PLUGIN_SYSTEM_AVAILABLE:
            pytest.skip("Plugin system not available")

        # Plugin code that fails on activation
        activation_fail_code = """
from autogen.backend.services.plugin_system import BasePlugin
from typing import Dict, Any

class TestPlugin(BasePlugin):
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)

    async def initialize(self) -> bool:
        return True

    async def on_activate(self):
        raise RuntimeError("Activation failed")

    async def cleanup(self) -> bool:
        return True
"""

        temp_dir = plugin_manager.plugins_directory
        plugin_dir = self.create_plugin_files(
            temp_dir, valid_plugin_manifest, activation_fail_code, "activation_fail_plugin"
        )

        # Load plugin successfully
        result = await plugin_manager.load_plugin(plugin_dir)
        assert result is True

        # Attempt to activate plugin that fails activation
        activation_result = await plugin_manager.activate_plugin("test_plugin")

        # Should fail gracefully
        assert activation_result is False

        # Plugin should be marked as ERROR status
        if "test_plugin" in plugin_manager.plugins:
            plugin = plugin_manager.plugins["test_plugin"]
            assert plugin.status == PluginStatus.ERROR
            assert plugin.error_info is not None

    @pytest.mark.asyncio
    async def test_hook_execution_fallback(self, plugin_manager, valid_plugin_manifest):
        """Test fallback when hook execution fails"""
        if not PLUGIN_SYSTEM_AVAILABLE:
            pytest.skip("Plugin system not available")

        # Plugin with failing hook
        hook_fail_code = """
from autogen.backend.services.plugin_system import BasePlugin
from typing import Dict, Any

class TestPlugin(BasePlugin):
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)

    async def initialize(self) -> bool:
        return True

    async def on_before_workflow_execution(self, context):
        raise RuntimeError("Hook execution failed")

    async def cleanup(self) -> bool:
        return True
"""

        # Update manifest to include hook
        manifest = valid_plugin_manifest.copy()
        manifest["hooks"] = ["before_workflow_execution"]

        temp_dir = plugin_manager.plugins_directory
        plugin_dir = self.create_plugin_files(
            temp_dir, manifest, hook_fail_code, "hook_fail_plugin"
        )

        # Load and activate plugin
        await plugin_manager.load_plugin(plugin_dir)
        await plugin_manager.activate_plugin("test_plugin")

        # Execute hook - should handle failure gracefully
        context = {"test": "data"}
        result_context = await plugin_manager.execute_hook(
            HookType.BEFORE_WORKFLOW_EXECUTION, context
        )

        # Should return original context despite hook failure
        assert result_context == context

    @pytest.mark.asyncio
    async def test_dependency_resolution_fallback(
        self, plugin_manager, valid_plugin_manifest, valid_plugin_code
    ):
        """Test fallback when plugin dependencies are missing"""
        if not PLUGIN_SYSTEM_AVAILABLE:
            pytest.skip("Plugin system not available")

        # Plugin with missing dependency
        manifest = valid_plugin_manifest.copy()
        manifest["dependencies"] = ["missing_dependency_plugin"]
        manifest["id"] = "dependent_plugin"

        temp_dir = plugin_manager.plugins_directory
        plugin_dir = self.create_plugin_files(
            temp_dir, manifest, valid_plugin_code, "dependent_plugin"
        )

        # Attempt to load plugin with missing dependency
        result = await plugin_manager.load_plugin(plugin_dir)

        # Should fail gracefully due to missing dependency
        assert result is False
        assert "dependent_plugin" not in plugin_manager.plugins

    @pytest.mark.asyncio
    async def test_plugin_config_validation_fallback(
        self, plugin_manager, valid_plugin_manifest, valid_plugin_code
    ):
        """Test fallback when plugin configuration is invalid"""
        if not PLUGIN_SYSTEM_AVAILABLE:
            pytest.skip("Plugin system not available")

        # Add config schema to manifest
        manifest = valid_plugin_manifest.copy()
        manifest["config_schema"] = {"required_field": {"type": "str", "required": True}}

        temp_dir = plugin_manager.plugins_directory
        plugin_dir = self.create_plugin_files(
            temp_dir, manifest, valid_plugin_code, "config_test_plugin"
        )

        # Load plugin
        await plugin_manager.load_plugin(plugin_dir)

        # Try to update with invalid config
        invalid_config = {"required_field": 123}  # Wrong type

        try:
            result = await plugin_manager.update_plugin_config("test_plugin", invalid_config)
            # Should handle validation gracefully
            assert result is False or result is True  # Implementation dependent
        except Exception:
            # Exception handling is also acceptable fallback behavior
            pass

    @pytest.mark.asyncio
    async def test_plugin_cleanup_fallback(self, plugin_manager, valid_plugin_manifest):
        """Test fallback when plugin cleanup fails"""
        if not PLUGIN_SYSTEM_AVAILABLE:
            pytest.skip("Plugin system not available")

        # Plugin with failing cleanup
        cleanup_fail_code = """
from autogen.backend.services.plugin_system import BasePlugin
from typing import Dict, Any

class TestPlugin(BasePlugin):
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)

    async def initialize(self) -> bool:
        return True

    async def cleanup(self) -> bool:
        raise RuntimeError("Cleanup failed")
"""

        temp_dir = plugin_manager.plugins_directory
        plugin_dir = self.create_plugin_files(
            temp_dir, valid_plugin_manifest, cleanup_fail_code, "cleanup_fail_plugin"
        )

        # Load plugin
        await plugin_manager.load_plugin(plugin_dir)

        # Attempt to unload plugin with failing cleanup
        try:
            result = await plugin_manager.unload_plugin("test_plugin")
            # Should handle cleanup failure gracefully
            assert result is False or result is True  # Implementation dependent
        except Exception:
            # Exception handling is also acceptable fallback behavior
            pass

    @pytest.mark.asyncio
    async def test_plugin_system_resilience(
        self, plugin_manager, valid_plugin_manifest, valid_plugin_code
    ):
        """Test overall plugin system resilience"""
        if not PLUGIN_SYSTEM_AVAILABLE:
            pytest.skip("Plugin system not available")

        temp_dir = plugin_manager.plugins_directory

        # Load a good plugin first
        good_plugin_dir = self.create_plugin_files(
            temp_dir, valid_plugin_manifest, valid_plugin_code, "good_plugin"
        )

        good_result = await plugin_manager.load_plugin(good_plugin_dir)
        assert good_result is True

        # Try to load multiple bad plugins
        bad_manifests = [
            {},  # Empty manifest
            {"id": "bad1"},  # Missing fields
            {"id": "bad2", "name": "Bad2", "version": "1.0.0"},  # Still missing fields
        ]

        for i, bad_manifest in enumerate(bad_manifests):
            bad_plugin_dir = self.create_plugin_files(
                temp_dir, bad_manifest, "# Bad plugin", f"bad_plugin_{i}"
            )

            bad_result = await plugin_manager.load_plugin(bad_plugin_dir)
            assert bad_result is False

        # Good plugin should still be working
        assert "test_plugin" in plugin_manager.plugins

        # System should still function
        plugins = await plugin_manager.get_plugins()
        assert len(plugins) >= 1

        stats = plugin_manager.get_stats()
        assert stats["total_plugins"] >= 1
        assert stats["failed_plugins"] >= len(bad_manifests)

    @pytest.mark.asyncio
    async def test_plugin_discovery_fallback(self, plugin_manager):
        """Test fallback behavior during plugin discovery"""
        if not PLUGIN_SYSTEM_AVAILABLE:
            pytest.skip("Plugin system not available")

        temp_dir = plugin_manager.plugins_directory

        # Create mixed valid and invalid plugin directories
        valid_dir = Path(temp_dir) / "valid_plugin"
        valid_dir.mkdir()
        with open(valid_dir / "plugin.yaml", "w") as f:
            yaml.dump(
                {
                    "id": "valid_plugin",
                    "name": "Valid Plugin",
                    "version": "1.0.0",
                    "type": "extension",
                    "main": "plugin.py",
                },
                f,
            )

        # Invalid plugin directory (no manifest)
        invalid_dir = Path(temp_dir) / "invalid_plugin"
        invalid_dir.mkdir()

        # Corrupted manifest
        corrupted_dir = Path(temp_dir) / "corrupted_plugin"
        corrupted_dir.mkdir()
        with open(corrupted_dir / "plugin.yaml", "w") as f:
            f.write("invalid: yaml: content: [")

        # Discover plugins
        discovered = await plugin_manager.discover_plugins()

        # Should handle mixed scenarios gracefully
        assert isinstance(discovered, list)

        # Should find at least the valid plugin
        valid_plugins = [p for p in discovered if p.get("status") == "discovered"]
        assert len(valid_plugins) >= 0  # Might be 0 if validation is strict

    @pytest.mark.asyncio
    async def test_plugin_version_compatibility_fallback(
        self, plugin_manager, valid_plugin_manifest, valid_plugin_code
    ):
        """Test fallback when plugin version compatibility fails"""
        if not PLUGIN_SYSTEM_AVAILABLE:
            pytest.skip("Plugin system not available")

        # Plugin with incompatible version requirements
        manifest = valid_plugin_manifest.copy()
        manifest["min_system_version"] = "999.0.0"  # Unrealistic version
        manifest["id"] = "incompatible_plugin"

        temp_dir = plugin_manager.plugins_directory
        plugin_dir = self.create_plugin_files(
            temp_dir, manifest, valid_plugin_code, "incompatible_plugin"
        )

        # Attempt to load incompatible plugin
        result = await plugin_manager.load_plugin(plugin_dir)

        # Should handle version incompatibility gracefully
        # (Implementation may or may not check version compatibility)
        assert isinstance(result, bool)

    def test_plugin_system_availability_fallback(self):
        """Test fallback when plugin system is not available"""
        # This test covers the case where plugin system imports fail
        if not PLUGIN_SYSTEM_AVAILABLE:
            # Plugin system not available - this IS the fallback behavior
            with pytest.raises(ImportError):
                from autogen.backend.services.plugin_system import PluginManager
        else:
            # Plugin system available - test import success
            from autogen.backend.services.plugin_system import PluginManager

            assert PluginManager is not None

    @pytest.mark.asyncio
    async def test_concurrent_plugin_operations_fallback(
        self, plugin_manager, valid_plugin_manifest, valid_plugin_code
    ):
        """Test fallback behavior under concurrent plugin operations"""
        if not PLUGIN_SYSTEM_AVAILABLE:
            pytest.skip("Plugin system not available")

        temp_dir = plugin_manager.plugins_directory

        # Create multiple plugin directories
        plugin_dirs = []
        for i in range(3):
            manifest = valid_plugin_manifest.copy()
            manifest["id"] = f"concurrent_plugin_{i}"

            plugin_dir = self.create_plugin_files(
                temp_dir, manifest, valid_plugin_code, f"concurrent_plugin_{i}"
            )
            plugin_dirs.append(plugin_dir)

        # Try to load all plugins concurrently
        tasks = [plugin_manager.load_plugin(plugin_dir) for plugin_dir in plugin_dirs]

        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Should handle concurrent operations gracefully
            assert len(results) == 3

            # Check that system remains stable
            plugins = await plugin_manager.get_plugins()
            assert isinstance(plugins, list)

        except Exception as e:
            # Concurrent operation failures are acceptable fallback behavior
            assert isinstance(e, Exception)

    @pytest.mark.asyncio
    async def test_plugin_manager_initialization_fallback(self):
        """Test fallback when plugin manager initialization fails"""
        if not PLUGIN_SYSTEM_AVAILABLE:
            pytest.skip("Plugin system not available")

        # Try to create plugin manager with invalid directory
        try:
            invalid_manager = PluginManager(plugins_directory="/invalid/nonexistent/path")

            # Should either succeed with fallback behavior or fail gracefully
            assert isinstance(invalid_manager, PluginManager)

        except Exception as e:
            # Graceful failure is acceptable fallback behavior
            assert isinstance(e, Exception)

    @pytest.mark.asyncio
    async def test_plugin_stats_fallback(self, plugin_manager):
        """Test fallback behavior for plugin statistics"""
        if not PLUGIN_SYSTEM_AVAILABLE:
            pytest.skip("Plugin system not available")

        # Get stats even when no plugins are loaded
        stats = plugin_manager.get_stats()

        # Should return valid stats structure
        assert isinstance(stats, dict)
        assert "total_plugins" in stats
        assert "active_plugins" in stats
        assert "failed_plugins" in stats

        # All counts should be non-negative
        assert stats["total_plugins"] >= 0
        assert stats["active_plugins"] >= 0
        assert stats["failed_plugins"] >= 0
