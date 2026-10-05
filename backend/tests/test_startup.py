import os
import subprocess
import sys
import unittest
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "local-test-key-for-startup-tests-only")


class StartupTests(unittest.TestCase):
    def test_import_does_not_start_language_tool(self):
        with patch("language_tool_python.LanguageTool") as tool:
            from app.main import app
            self.assertEqual(app.title, "SpeakForge API")
            tool.assert_not_called()

    def test_language_tool_is_initialized_once(self):
        from app.services.ai_scoring import get_language_tool
        get_language_tool.cache_clear()
        self.addCleanup(get_language_tool.cache_clear)
        with patch("language_tool_python.LanguageTool") as tool:
            self.assertIs(get_language_tool(), tool.return_value)
            self.assertIs(get_language_tool(), tool.return_value)
            tool.assert_called_once_with("en-US", language_tool_download_version="6.6")

    def test_unavailable_grammar_is_not_a_fake_score(self):
        from app.services.ai_scoring import evaluate_answer
        with patch("app.services.ai_scoring.get_language_tool", side_effect=RuntimeError("offline")):
            with self.assertRaises(RuntimeError):
                evaluate_answer("Introduce yourself", "This is my response.", answer_type="text")

    def test_production_rejects_example_secret(self):
        result = subprocess.run([sys.executable,"-c","import app.config"],env=dict(os.environ,ENVIRONMENT="production",SECRET_KEY="generate-a-long-random-secret"),capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0)
        self.assertIn("random production SECRET_KEY",result.stderr)

    def test_production_rejects_example_admin_secret(self):
        result = subprocess.run([sys.executable,"-c","import app.config"],env=dict(os.environ,ENVIRONMENT="production",SECRET_KEY="a"*64,ADMIN_SECRET_KEY="generate-a-separate-admin-secret"),capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0)
        self.assertIn("random production ADMIN_SECRET_KEY",result.stderr)

    def test_production_accepts_long_secret(self):
        result = subprocess.run([sys.executable,"-c","import app.config"],env=dict(os.environ,ENVIRONMENT="production",SECRET_KEY="a"*64),capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
