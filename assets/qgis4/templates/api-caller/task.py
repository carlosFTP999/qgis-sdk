import urllib.request

from qgis.core import QgsTask


class FetchTask(QgsTask):
    def __init__(self, url):
        super().__init__("Fetch API data", QgsTask.Flag.CanCancel)
        self.url = url
        self.result = None
        self.error = None

    def run(self):
        try:
            with urllib.request.urlopen(self.url, timeout=15) as response:
                if self.isCanceled():
                    return False
                self.result = response.read().decode("utf-8", errors="replace")
            return True
        except Exception as exc:
            self.error = str(exc)
            return False
