from qgis.core import QgsProcessingProvider

from .algorithm import BufferAlgorithm


class {{PROVIDER_CLASS}}(QgsProcessingProvider):
    def id(self):
        return "{{PLUGIN_NAME}}"

    def name(self):
        return "{{PLUGIN_TITLE}}"

    def loadAlgorithms(self):
        self.addAlgorithm(BufferAlgorithm())
