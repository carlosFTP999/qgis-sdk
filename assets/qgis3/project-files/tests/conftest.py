import os

import pytest


@pytest.fixture(scope="session")
def qgis_app():
    pytest.importorskip("qgis.core", reason="QGIS bindings are not importable")
    from qgis.core import QgsApplication

    prefix = os.environ.get("QGIS_PREFIX_PATH")
    if prefix:
        QgsApplication.setPrefixPath(prefix, True)

    app = QgsApplication([], False)
    app.initQgis()
    try:
        yield app
    finally:
        app.exitQgis()
