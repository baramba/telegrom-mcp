from pathlib import Path

from telegrom_mcp.config import load_policy
from telegrom_mcp.policy import ChatRef, Policy, ResolvedChat

FRIEND = ResolvedChat(100, "Friend")
BANK = ResolvedChat(200, "bank_bot")


def refs(*values: str | int) -> frozenset[ChatRef]:
    return frozenset(ChatRef.parse(v) for v in values)


def test_default_policy_reads_everything_sends_nothing() -> None:
    p = Policy()
    assert p.can_read(FRIEND)
    assert not p.can_send(FRIEND)


def test_deny_wins_over_allow() -> None:
    p = Policy(deny=refs("@bank_bot"), read_allow=refs(200), send_allow=refs(200))
    assert not p.can_read(BANK)
    assert not p.can_send(BANK)


def test_read_allowlist_restricts() -> None:
    p = Policy(read_allow=refs("@friend"))
    assert p.can_read(FRIEND)
    assert not p.can_read(BANK)


def test_send_allowlist_by_id_and_username_case_insensitive() -> None:
    assert Policy(send_allow=refs(100)).can_send(FRIEND)
    assert Policy(send_allow=refs("@FRIEND")).can_send(FRIEND)
    assert not Policy(send_allow=refs("@friend")).can_send(BANK)


def test_chat_without_username_not_matched_by_username() -> None:
    assert Policy(deny=refs("@x")).can_read(ResolvedChat(1, None))


def test_parse_string_ids() -> None:
    assert ChatRef.parse("-1001234") == ChatRef(chat_id=-1001234)


def test_load_policy(tmp_path: Path) -> None:
    f = tmp_path / "config.toml"
    f.write_text('deny = ["@bank_bot"]\n[read]\nallow = []\n[send]\nallow = [100, "@me"]\n')
    p = load_policy(f)
    assert p.can_send(FRIEND) and not p.can_send(BANK) and not p.can_read(BANK)


def test_missing_config_file_is_safe(tmp_path: Path) -> None:
    p = load_policy(tmp_path / "nope.toml")
    assert not p.can_send(FRIEND)
