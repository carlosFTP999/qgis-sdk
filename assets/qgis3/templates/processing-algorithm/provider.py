from qgis.core import QgsProcessingProvider

from .algorithm import {{ALGORITHM_CLASS}}


class {{PROVIDER_CLASS}}(QgsProcessingProvider):
    def id(self):
        return "{{PLUGIN_NAME}}"

    def name(self):
        return "{{PLUGIN_TITLE}}"

    def loadAlgorithms(self):
        self.addAlgorithm({{ALGORITHM_CLASS}}())
