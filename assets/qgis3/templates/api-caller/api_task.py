import json
import urllib.request

from qgis.core import QgsTask


class ApiTask(QgsTask):
    def __init__(self, url, timeout=20):
        super().__init__("Fetch API response", QgsTask.CanCancel)
        self.url = url
        self.timeout = timeout
        self.result = None
        self.error = None

    def run(self):
        try:
            request = urllib.request.Request(
                self.url, headers={"Accept": "application/json"}
            )
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = response.read().decode("utf-8")
            self.result = json.loads(payload)
            return True
        except Exception as exc:
            self.error = str(exc)
            return False
