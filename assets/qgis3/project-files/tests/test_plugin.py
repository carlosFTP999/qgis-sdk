from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parents[1] / "my_plugin"


def test_metadata_targets_qgis_three():
    metadata = (PLUGIN / "metadata.txt").read_text(encoding="utf-8").lower()
    assert "qgisminimumversion=3." in metadata
    assert "supportsqt6=true" not in metadata


def test_package_exposes_class_factory():
    init = (PLUGIN / "__init__.py").read_text(encoding="utf-8")
    assert "def classFactory(iface):" in init
    assert "from PyQt5" not in init
    assert "from PyQt6" not in init


@pytest.mark.qgis
def test_plugin_module_imports_with_qgis(qgis_app):
    pytest.importorskip("qgis.core", reason="QGIS bindings are not importable")
    from my_plugin import classFactory
    from my_plugin import plugin as plugin_module

    assert callable(classFactory)
    assert plugin_module is not None
