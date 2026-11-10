from qgis.core import QgsApplication


class {{PLUGIN_CLASS}}:
    def __init__(self, iface):
        self.iface = iface
        self.provider = None

    def initGui(self):
        from .provider import {{PROVIDER_CLASS}}

        self.provider = {{PROVIDER_CLASS}}()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def unload(self):
        if self.provider is not None:
            QgsApplication.processingRegistry().removeProvider(self.provider)
            self.provider = None
