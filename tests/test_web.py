"""Exercise the real FastAPI lifespan, security boundary and browser API."""
import json
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient
from aletheia_agora.server import create_app
from aletheia_core.service import Service


class BrowserApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="aletheia-web-")
        self.home = Path(self.temp.name).resolve()
        def cleanup():
            self.assertEqual(self.home.parent, Path(tempfile.gettempdir()).resolve())
            self.assertTrue(self.home.name.startswith("aletheia-web-"))
            self.temp.cleanup()
        self.addCleanup(cleanup)
        def factory(home):
            service = Service(home)
            service.config.save({**service.config.value, "autoStart": False})
            return service
        self.client = self.enterContext(TestClient(create_app(self.home, token="synthetic-access-token", service_factory=factory)))
        self.headers = {"Authorization": "Bearer synthetic-access-token"}
        import time
        for _ in range(100):
            if self.client.get("/api/state", headers=self.headers).json()["value"]["library"]["phase"] == "ready":
                break
            time.sleep(.01)

    def action(self, name, *args):
        return self.client.post("/api/actions/" + name, headers=self.headers, json=dict(args=list(args)))

    def test_static_interface_and_authentication(self):
        page = self.client.get("/")
        self.assertIn("Aletheia Agora", page.text)
        self.assertNotIn("synthetic-access-token", page.text)
        self.assertIn("frame-ancestors 'none'", page.headers["content-security-policy"])
        self.assertEqual(self.client.get("/api/state").status_code, 401)
        self.assertEqual(self.client.post("/api/actions/save", json=dict(args=["# Attack"])).status_code, 401)
        self.assertEqual(self.action("__dict__").status_code, 400)
        self.assertEqual(self.client.get("/static/../../settings.json").status_code, 404)
        self.assertIn("window.aletheia", self.client.get("/static/bridge.js").text)

    def test_import_title_edit_inventory_export_and_theme(self):
        content = "# Original note\n\nA blue bicycle.\n\n## Metadata\nID: web-note\n"
        result = self.action("importContents", [dict(name="note.md", content=content)]).json()
        self.assertEqual(result["value"]["imported"], 1)
        record = self.action("document", "web-note").json()["value"]
        updated = self.action("renameTitle", "web-note", "New title", record["revision"]).json()["value"]
        self.assertEqual(updated["title"], "New title")
        self.assertIn("A blue bicycle.", updated["content"])
        self.assertFalse(self.action("renameTitle", "web-note", "Stale", record["revision"]).json()["ok"])
        answer = self.action("ask", "What does my archive contain?").json()["value"]
        self.assertIn("contains 1 document.", answer["answer"])
        self.assertEqual(answer["sources"][0]["id"], "web-note")
        self.action("theme", "dark")
        self.assertEqual(json.loads((self.home / "settings.json").read_text())["theme"], "dark")

    def test_bad_model_upload_does_not_become_a_model(self):
        result = self.client.post("/api/model/upload", headers={**self.headers, "X-Model-Filename": "../invalid.gguf", "Content-Type": "application/octet-stream"}, content=b"not-a-gguf")
        self.assertEqual(result.status_code, 400)
        self.assertEqual(list((self.home / "models").iterdir()), [])


if __name__ == "__main__":
    unittest.main()
