"""Regression tests for offline-safe imports of the models package."""

import os
import sqlite3
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FALLBACK_WARNING = "tiktoken encoder unavailable; using approximate token counts"


def _subprocess_env(tmp_path: Path) -> dict[str, str]:
    db_path = tmp_path / "import_safety.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE financials (panel_vintage TEXT, life_stage TEXT, leverage REAL, year INTEGER)"
    )
    conn.execute("CREATE TABLE companies (company_code INTEGER, industry_group TEXT)")
    conn.commit()
    conn.close()
    env = os.environ.copy()
    env["PROFSUR_DB_PATH"] = str(db_path)
    return env


def _run(script: str, tmp_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", script],
        cwd=PROJECT_ROOT,
        env=_subprocess_env(tmp_path),
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_models_import_survives_tiktoken_runtime_failure(tmp_path):
    result = _run(
        """
import logging
import tiktoken
logging.basicConfig(level=logging.WARNING)
tiktoken.get_encoding = lambda name: (_ for _ in ()).throw(RuntimeError("network unreachable"))
import models
from models import llm_adapters
assert llm_adapters.count_tokens("abcdefgh") == 2
assert llm_adapters.count_tokens("abcdefgh") == 2
assert llm_adapters.count_tokens("") == 1
""",
        tmp_path,
    )
    assert result.returncode == 0, result.stderr
    assert result.stderr.count(FALLBACK_WARNING) == 1


def test_models_import_does_not_initialize_tiktoken_until_counting(tmp_path):
    result = _run(
        """
import tiktoken
calls = []
class FakeEncoder:
    def encode(self, text):
        return [1, 2, 3]
def fake_get_encoding(name):
    calls.append(name)
    return FakeEncoder()
tiktoken.get_encoding = fake_get_encoding
import models
assert calls == []
from models import llm_adapters
assert llm_adapters.count_tokens("anything") == 3
assert calls == ["cl100k_base"]
""",
        tmp_path,
    )
    assert result.returncode == 0, result.stderr


def test_import_models_does_not_eagerly_import_llm_adapter(tmp_path):
    result = _run(
        """
import sys
import models
assert "models.llm_adapters" not in sys.modules
from models import llm_adapters
assert "models.llm_adapters" in sys.modules
""",
        tmp_path,
    )
    assert result.returncode == 0, result.stderr


def test_count_tokens_falls_back_when_encoder_itself_is_broken(tmp_path):
    result = _run(
        """
import logging
import tiktoken
logging.basicConfig(level=logging.WARNING)
class BrokenEncoder:
    def encode(self, text):
        raise ValueError("corrupted encoder cache")
tiktoken.get_encoding = lambda name: BrokenEncoder()
import models
from models import llm_adapters
assert llm_adapters.count_tokens("abcdefghijkl") == 3
assert llm_adapters.count_tokens("abcdefghijkl") == 3
""",
        tmp_path,
    )
    assert result.returncode == 0, result.stderr
    assert result.stderr.count(FALLBACK_WARNING) == 1


def test_docker_image_precaches_cl100k_base_at_stable_path():
    dockerfile = (PROJECT_ROOT / "Dockerfile").read_text(encoding="utf-8")
    env_line = "ENV TIKTOKEN_CACHE_DIR=/opt/tiktoken-cache"
    prefetch = "tiktoken.get_encoding('cl100k_base')"
    assert env_line in dockerfile
    assert prefetch in dockerfile
    assert dockerfile.index(env_line) < dockerfile.index(prefetch)


def test_import_db_does_not_open_or_create_database(tmp_path):
    missing_db = tmp_path / "missing" / "database.db"
    env = os.environ.copy()
    env["PROFSUR_DB_PATH"] = str(missing_db)
    result = subprocess.run(
        [sys.executable, "-c", "import db"],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert not missing_db.exists()


def test_import_model_cache_does_not_create_directory(tmp_path):
    result = _run(
        """
import os
os.makedirs = lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("mkdir at import"))
import models.cache
""",
        tmp_path,
    )
    assert result.returncode == 0, result.stderr
