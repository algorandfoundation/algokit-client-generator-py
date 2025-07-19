"""
Approval tests for generated clients to ensure both full and minimal clients are properly generated.
This is similar to the TypeScript approval-tests.spec.ts.
"""

import importlib
import pathlib
from typing import Any

import pytest

# All contract names and their extensions
ARC32_APPS = [
    "duplicate_structs",
    "hello_world",
    "life_cycle",
    "minimal",
    "state",
    "voting_round",
]

ARC56_APPS = [
    "arc56_test",
    "structs",
    "state",
    "nested",
    "nfd",
    "reti",
    "zero_coupon_bond",
]


def get_artifacts_path() -> pathlib.Path:
    """Get the path to the artifacts directory."""
    return pathlib.Path(__file__).parent.parent / "smart_contracts" / "artifacts"


def import_client_module(app_name: str, extension: str, mode: str = "full") -> Any:
    """Dynamically import a client module."""
    if mode == "minimal":
        # For minimal clients, we need to construct a proper module name
        # The file is named {app}_{extension}_client.minimal.py
        # but we import it as {app}_{extension}_client_minimal
        module_name = f"{app_name}_{extension}_client_minimal"
        module_path = f"examples.smart_contracts.artifacts.{app_name}.{module_name}"
    else:
        module_name = f"{app_name}_{extension}_client"
        module_path = f"examples.smart_contracts.artifacts.{app_name}.{module_name}"

    try:
        return importlib.import_module(module_path)
    except ImportError as e:
        pytest.fail(f"Failed to import {module_path}: {e}")


def get_client_class_name(module: object) -> str:
    """Get the client class name from a module."""
    # Look for a class that ends with 'Client'
    for name in dir(module):
        obj = getattr(module, name)
        if isinstance(obj, type) and name.endswith("Client") and not name.endswith("Factory"):
            return name
    raise ValueError("No client class found in module")


def get_factory_class_name(module: object) -> str:
    """Get the factory class name from a module."""
    # Look for a class that ends with 'Factory' but not 'ParamsFactory'
    for name in dir(module):
        obj = getattr(module, name)
        if isinstance(obj, type) and name.endswith("Factory") and not name.endswith("ParamsFactory"):
            return name
    raise ValueError("No factory class found in module")


class TestClientApproval:
    """Test class for client approval tests."""

    @pytest.mark.parametrize("app_name", ARC32_APPS)
    def test_arc32_full_client_exists(self, app_name: str) -> None:
        """Test that full ARC32 clients exist and can be imported."""
        module = import_client_module(app_name, "arc32", "full")
        client_class_name = get_client_class_name(module)
        assert client_class_name.endswith("Client")

        # Full clients should have a factory
        factory_class_name = get_factory_class_name(module)
        assert factory_class_name.endswith("Factory")

    @pytest.mark.parametrize("app_name", ARC32_APPS)
    def test_arc32_minimal_client_exists(self, app_name: str) -> None:
        """Test that minimal ARC32 clients exist and can be imported."""
        module = import_client_module(app_name, "arc32", "minimal")
        client_class_name = get_client_class_name(module)
        assert client_class_name.endswith("Client")

        # Minimal clients should NOT have a factory
        try:
            get_factory_class_name(module)
            pytest.fail("Minimal clients should not have factory classes")
        except ValueError:
            pass  # This is expected

    @pytest.mark.parametrize("app_name", ARC56_APPS)
    def test_arc56_full_client_exists(self, app_name: str) -> None:
        """Test that full ARC56 clients exist and can be imported."""
        module = import_client_module(app_name, "arc56", "full")
        client_class_name = get_client_class_name(module)
        assert client_class_name.endswith("Client")

        # Full clients should have a factory
        factory_class_name = get_factory_class_name(module)
        assert factory_class_name.endswith("Factory")

    @pytest.mark.parametrize("app_name", ARC56_APPS)
    def test_arc56_minimal_client_exists(self, app_name: str) -> None:
        """Test that minimal ARC56 clients exist and can be imported."""
        module = import_client_module(app_name, "arc56", "minimal")
        client_class_name = get_client_class_name(module)
        assert client_class_name.endswith("Client")

        # Minimal clients should NOT have a factory
        try:
            get_factory_class_name(module)
            pytest.fail("Minimal clients should not have factory classes")
        except ValueError:
            pass  # This is expected


class TestClientDifferences:
    """Test the differences between full and minimal clients."""

    def get_module_attributes(self, module: object) -> list[str]:
        """Get all public attributes from a module."""
        attrs = []
        for name in dir(module):
            if name.startswith("_"):
                continue
            attrs.append(name)
        return sorted(attrs)

    @pytest.mark.parametrize(
        ("app_name", "extension"), [(app, "arc32") for app in ARC32_APPS] + [(app, "arc56") for app in ARC56_APPS]
    )
    def test_full_vs_minimal_differences(self, app_name: str, extension: str) -> None:
        """Test the differences between full and minimal clients."""
        full_module = import_client_module(app_name, extension, "full")
        minimal_module = import_client_module(app_name, extension, "minimal")

        full_attrs = set(self.get_module_attributes(full_module))
        minimal_attrs = set(self.get_module_attributes(minimal_module))

        # Attributes only in full client (these should include Factory classes)
        only_in_full = full_attrs - minimal_attrs

        # There should be differences (at minimum, Factory classes should be missing from minimal)
        assert len(only_in_full) > 0, f"No differences found between full and minimal clients for {app_name}"

        # Factory classes should only be in full clients
        factory_attrs = [
            attr for attr in only_in_full if attr.endswith("Factory") and not attr.endswith("ParamsFactory")
        ]
        assert len(factory_attrs) > 0, f"Factory class missing from full client for {app_name}"

        # APP_SPEC should be present in both
        assert "APP_SPEC" in full_attrs, f"APP_SPEC missing from full client for {app_name}"
        assert "APP_SPEC" in minimal_attrs, f"APP_SPEC missing from minimal client for {app_name}"

        # Client class should be present in both
        full_client_classes = [attr for attr in full_attrs if attr.endswith("Client") and not attr.endswith("Factory")]
        minimal_client_classes = [
            attr for attr in minimal_attrs if attr.endswith("Client") and not attr.endswith("Factory")
        ]

        assert len(full_client_classes) == 1, f"Expected exactly one client class in full module for {app_name}"
        assert len(minimal_client_classes) == 1, f"Expected exactly one client class in minimal module for {app_name}"

        # Client class names should be the same
        assert full_client_classes[0] == minimal_client_classes[0], f"Client class names differ for {app_name}"
