"""Configuration: credentials from the environment, access policy from a TOML file."""

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

from telegrom_mcp.policy import ChatRef, Policy

CONFIG_DIR = Path(os.environ.get("TELEGROM_HOME", "~/.config/telegrom-mcp")).expanduser()


@dataclass(frozen=True)
class Settings:
    api_id: int
    api_hash: str
    session_path: Path
    policy: Policy
    max_message_chars: int = 4000
    max_read_limit: int = 50
    send_rate_per_minute: int = 10


def _refs(values: list[str | int]) -> frozenset[ChatRef]:
    return frozenset(ChatRef.parse(v) for v in values)


def load_policy(path: Path) -> Policy:
    """Missing file -> read-only for every chat, sending disabled."""
    if not path.exists():
        return Policy()
    with path.open("rb") as f:
        raw = tomllib.load(f)
    read, send = raw.get("read", {}), raw.get("send", {})
    return Policy(
        deny=_refs(raw.get("deny", [])),
        read_allow=_refs(read.get("allow", [])),
        send_allow=_refs(send.get("allow", [])),
    )


def load_settings() -> Settings:
    try:
        api_id = int(os.environ["TELEGRAM_API_ID"])
        api_hash = os.environ["TELEGRAM_API_HASH"]
    except KeyError as exc:
        raise SystemExit(f"Environment variable {exc.args[0]} is required") from exc
    CONFIG_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    return Settings(
        api_id=api_id,
        api_hash=api_hash,
        session_path=CONFIG_DIR / "session",
        policy=load_policy(CONFIG_DIR / "config.toml"),
    )
