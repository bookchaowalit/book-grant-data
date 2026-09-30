"""Offline guardrails for the source registry, packaged source configs and CLI."""
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from importlib.resources import files
from pathlib import Path
from urllib.parse import urlsplit

from book_grant_data import capture
from book_grant_data.capture import normalize, source_config
from book_grant_data.cli import main, resource, validate

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = json.loads((ROOT / "sources.json").read_text(encoding="utf-8"))
LINEAGE = {"raw_object_key": "landing/test", "bronze_manifest_key": "control/manifests/test"}
CHECKED_AT = "2026-09-07T00:00:00Z"


def schema_for(version):
    for name in ("schema.json", "schema-v2.json"):
        try:
            schema = resource(name)
        except FileNotFoundError:
            continue
        if schema["properties"]["schema_version"]["const"] == version:
            return schema
    raise AssertionError("no packaged schema for " + version)


def category_enum(schema):
    return schema["properties"]["items"]["items"]["properties"]["category"]["enum"]


def marker_text(source):
    """Return the drift markers a marker-driven adapter requires, or None."""
    if source.get("generic_html"):
        return " ".join(source.get("required_markers") or [source["title"]])
    table = getattr(capture, "REQUIRED_MARKERS", None)
    if isinstance(table, dict) and source["id"] in table:
        return " ".join(table[source["id"]])
    return None


def synthetic_raw(source, text, title=None):
    title = source["title"] if title is None else title
    if source.get("access") == "govuk-api":
        return json.dumps({
            "base_path": source["source_url"].removeprefix("https://www.gov.uk"),
            "title": title,
            "description": text,
            "details": {"body": text},
        }).encode("utf-8")
    return ("<main><h1>" + title + "</h1><p>" + text + "</p></main>").encode("utf-8")


class RegistryTests(unittest.TestCase):
    def test_enabled_sources_resolve_to_consistent_configs(self):
        product = resource("schema.json")["properties"]["source"]["const"]
        self.assertEqual(REGISTRY["policy_file"], "src/book_grant_data/source.json")
        self.assertTrue((ROOT / REGISTRY["policy_file"]).is_file())
        for source_id in REGISTRY["enabled_sources"]:
            with self.subTest(source_id=source_id):
                source = source_config(source_id)
                self.assertEqual(source["id"], source_id)
                self.assertEqual(source["product"], product)
                self.assertEqual(source["domain"], REGISTRY["domain"])
                self.assertIs(source["enabled"], True)
                self.assertGreaterEqual(source["min_interval_seconds"], 3600)
                self.assertTrue(source["reviewed_at"] and source["permission_status"])
                self.assertIn(source["category"], category_enum(schema_for(source["schema_version"])))
                self.assertIn(source["category"], REGISTRY["enabled_category_capabilities"])
                for key in ("source_url", "fetch_url"):
                    url = urlsplit(source[key])
                    self.assertEqual(url.scheme, "https")
                    self.assertFalse(url.username or url.password or url.fragment)
                self.assertFalse(urlsplit(source["source_url"]).query)

    def test_every_packaged_source_is_registered(self):
        package = files("book_grant_data")
        for entry in package.iterdir():
            name = entry.name
            if name.startswith("source-") and name.endswith(".json"):
                with self.subTest(file=name):
                    source = json.loads(entry.read_text(encoding="utf-8"))
                    self.assertEqual(name, "source-" + source["id"] + ".json")
                    self.assertIn(source["id"], REGISTRY["enabled_sources"])

    def test_category_capabilities_exist_in_contract(self):
        allowed = set()
        for source_id in REGISTRY["enabled_sources"]:
            allowed.update(category_enum(schema_for(source_config(source_id)["schema_version"])))
        self.assertLessEqual(set(REGISTRY["enabled_category_capabilities"]), allowed)

    def test_source_id_selector_rejects_paths_and_unknown_ids(self):
        for bad in ("../schema", "source/../../x", "SCHEMA", "", "a b", "unknown-source-id"):
            with self.subTest(source_id=bad), self.assertRaises(ValueError):
                source_config(bad)


class AdapterTests(unittest.TestCase):
    def test_marker_driven_sources_normalize_to_valid_live_records(self):
        covered = 0
        for source_id in REGISTRY["enabled_sources"]:
            source = source_config(source_id)
            text = marker_text(source)
            if text is None:
                continue
            covered += 1
            with self.subTest(source_id=source_id):
                data = normalize(synthetic_raw(source, text), source, CHECKED_AT)
                with self.assertRaises(ValueError):
                    validate(data)  # live records need captured lake lineage first
                for item in data["items"]:
                    item["provenance"].update(LINEAGE)
                    self.assertEqual(item["category"], source["category"])
                    self.assertEqual(item["provenance"]["source_id"], source_id)
                    self.assertEqual(item["provenance"]["checked_at"], CHECKED_AT)
                    self.assertNotEqual(item["status"], "open", "marker-only pages must not assert availability")
                self.assertEqual(validate(data)["data_status"], "live")

    def test_marker_driven_sources_reject_drift(self):
        for source_id in REGISTRY["enabled_sources"]:
            source = source_config(source_id)
            if marker_text(source) is None:
                continue
            with self.subTest(source_id=source_id), self.assertRaises(ValueError):
                raw = synthetic_raw(source, "Please verify you are human to continue.", title="Access denied")
                normalize(raw, source, CHECKED_AT)

    def test_json_sources_reject_non_object_payloads(self):
        for source_id in REGISTRY["enabled_sources"]:
            source = source_config(source_id)
            if source["access"] == "html":
                continue
            for raw in (b"[]", b"null", b"\"text\"", b"not json"):
                with self.subTest(source_id=source_id, raw=raw), self.assertRaises(ValueError):
                    normalize(raw, source, CHECKED_AT)


class CliTests(unittest.TestCase):
    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_contract_command_prints_v1_schema(self):
        code, out, _ = self.run_cli("contract")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["properties"]["schema_version"], resource("schema.json")["properties"]["schema_version"])

    def test_validate_command_accepts_packaged_demo(self):
        code, out, _ = self.run_cli("validate", str(ROOT / "src" / "book_grant_data" / "demo.json"))
        self.assertEqual(code, 0)
        summary = json.loads(out)
        self.assertTrue(summary["valid"])
        self.assertEqual(summary["count"], len(resource("demo.json")["items"]))

    def test_validate_command_rejects_without_echoing_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            for body in ("{not json", json.dumps({"schema_version": "x", "secret": "synthetic-canary"})):
                path = Path(tmp) / "payload.json"
                path.write_text(body, encoding="utf-8")
                with self.subTest(body=body[:10]):
                    code, out, err = self.run_cli("validate", str(path))
                    self.assertEqual(code, 2)
                    self.assertEqual(out, "")
                    self.assertNotIn("synthetic-canary", err)
            code, _, _ = self.run_cli("validate", str(Path(tmp) / "missing.json"))
            self.assertEqual(code, 2)

    def test_demo_rejects_invalid_clock_and_negative_age(self):
        self.assertEqual(self.run_cli("demo", "--as-of", "2026-09-07")[0], 2)
        self.assertEqual(self.run_cli("demo", "--max-age-hours", "-1")[0], 2)


if __name__ == "__main__":
    unittest.main()
