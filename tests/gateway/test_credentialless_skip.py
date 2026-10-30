"""Regression: secondary profiles must not connect tokenless adapters.

Bug: with gateway.multiplex_profiles on, every secondary profile loaded
config with platforms: {} yet still ended up with telegram enabled=True
(registry enablement probes is_connected() against UNSCOPED env, while the
token itself is filled through the SCOPED _getenv and resolves to None).
The tokenless adapter failed connect and its _mark_disconnected wrote
"disconnected" over the healthy primary adapter's state in the shared
gateway_state.json — dashboards then reported Telegram down while messages
flowed fine.

Runs standalone (no pytest needed):
    python3 tests/gateway/test_credentialless_skip.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from gateway.config import PlatformConfig
from gateway.run import _is_credentialless


def check(label, got, want):
    ok = got == want
    print(f"{'OK  ' if ok else 'FAIL'} {label} -> {got}")
    return ok


def main() -> int:
    results = [
        # A credential on the canonical field means "let it connect".
        check("token set", _is_credentialless(PlatformConfig(enabled=True, token="abc")), False),
        check("api_key set", _is_credentialless(PlatformConfig(enabled=True, api_key="k")), False),
        # Nothing at all -> must be skipped, not connected.
        check("bare config", _is_credentialless(PlatformConfig(enabled=True)), True),
        check("whitespace token", _is_credentialless(PlatformConfig(enabled=True, token="   ")), True),
        # Credentials that live in `extra` (sms, google_chat, webhook-ish).
        check("extra token", _is_credentialless(PlatformConfig(enabled=True, extra={"token": "x"})), False),
        check("extra bot_token", _is_credentialless(PlatformConfig(enabled=True, extra={"bot_token": "x"})), False),
        check(
            "extra username/password",
            _is_credentialless(PlatformConfig(enabled=True, extra={"username": "u", "password": "p"})),
            False,
        ),
        # Unknown extra keys must NOT be treated as a credential -> conservative skip.
        check("extra irrelevant", _is_credentialless(PlatformConfig(enabled=True, extra={"foo": "bar"})), True),
    ]
    print(f"\nHASIL: {'SEMUA PASS' if all(results) else 'ADA YANG GAGAL'}")
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())