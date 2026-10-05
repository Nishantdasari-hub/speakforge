import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import smtplib
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("helper", Path(__file__).parents[1] / "configure_azure_email.py")
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)
MAIL = "synthetic.fixture@gmail.com"
PASSWORD = "abcdefghijklmnop"


class AzureEmailTests(unittest.TestCase):
    def test_private_prompt_retries_and_normalizes(self):
        out = io.StringIO()
        with patch("builtins.input", side_effect=["bad", MAIL]), patch.object(helper.getpass, "getpass", side_effect=["abcdefghij", "abcd efgh ijkl mnop"]), contextlib.redirect_stdout(out):
            self.assertEqual(helper.capture_credentials(), (MAIL, PASSWORD))
        self.assertIn("10 non-space characters", out.getvalue())
        self.assertNotIn(PASSWORD, out.getvalue())

    def test_protected_parameters_and_success(self):
        outputs = [json.dumps({"ip": "192.0.2.1", "location": "centralindia"}), "", json.dumps({"executionState": "Succeeded", "exitCode": 0, "output": "SMTP_AUTH_OK; CONFIG_SAVED"})]
        out = io.StringIO()
        with patch.object(helper, "azure", side_effect=outputs) as az, patch.object(helper, "capture_credentials", return_value=(MAIL, PASSWORD)), contextlib.redirect_stdout(out):
            helper.configure("test-rg", "test-vm")
        args = az.call_args_list[1].args[0]
        protected = args.index("--protected-parameters")
        self.assertEqual(args[protected+1:protected+3], ["SF_MAIL="+MAIL, "SF_APP_PASSWORD="+PASSWORD])
        self.assertNotIn(PASSWORD, args[args.index("--script")+1])
        self.assertNotIn(PASSWORD, out.getvalue())
        self.assertIn("CONFIG_SAVED", out.getvalue())

    def test_failed_execution_does_not_claim_success(self):
        outputs = [json.dumps({"ip": "192.0.2.1", "location": "centralindia"}), "", json.dumps({"executionState": "Failed", "exitCode": 1, "error": "rejected " + PASSWORD})]
        out = io.StringIO()
        with patch.object(helper, "azure", side_effect=outputs), patch.object(helper, "capture_credentials", return_value=(MAIL, PASSWORD)), contextlib.redirect_stdout(out):
            with self.assertRaises(RuntimeError) as err:
                helper.configure("test-rg", "test-vm")
        self.assertNotIn(PASSWORD, str(err.exception))
        self.assertNotIn("CONFIG_SAVED", out.getvalue())

    def test_cli_error_redacts_credentials(self):
        result = subprocess.CompletedProcess([], 1, "", "failed " + PASSWORD + " " + MAIL)
        with patch.object(helper.subprocess, "run", return_value=result):
            with self.assertRaises(RuntimeError) as err:
                helper.azure(["unused"], (PASSWORD, MAIL))
        self.assertNotIn(PASSWORD, str(err.exception))
        self.assertNotIn(MAIL, str(err.exception))

    def test_remote_configuration_is_private_and_preserves_existing_file(self):
        remote = helper.REMOTE_SCRIPT.split("\n", 1)[1].rsplit("\nPY\n", 1)[0]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            code = remote.replace("/opt/speakforge/.env", str(path))
            env = {"SF_MAIL": MAIL, "SF_APP_PASSWORD": "abcd efgh ijkl mnop", "SF_IP": "192.0.2.1"}
            out = io.StringIO()
            with patch.dict(os.environ, env), patch("smtplib.SMTP") as smtp, contextlib.redirect_stdout(out):
                exec(compile(code, "remote", "exec"), {})
                smtp.return_value.__enter__.return_value.starttls.assert_called_once()
                smtp.return_value.__enter__.return_value.login.assert_called_once_with(MAIL, PASSWORD)
                content = path.read_text()
                self.assertEqual(path.stat().st_mode & 0o777, 0o600)
                self.assertIn("https://api.speakforge.192-0-2-1.sslip.io", content)
                self.assertNotIn(PASSWORD, out.getvalue())
                with self.assertRaisesRegex(SystemExit, "CONFIG_EXISTS"):
                    exec(compile(code, "remote", "exec"), {})
                self.assertEqual(content, path.read_text())
            path.unlink()
            with patch.dict(os.environ, env), patch("smtplib.SMTP", side_effect=smtplib.SMTPAuthenticationError(535, b"synthetic")):
                with self.assertRaisesRegex(SystemExit, "SMTP_CHECK_FAILED"):
                    exec(compile(code, "remote", "exec"), {})
                self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()
