"""Allow/deny policy. Pure logic, no Telegram I/O.

Rules:
  * `deny` always wins, for reading and sending.
  * Reading: if `read_allow` is empty every chat is readable except denied ones, otherwise only `read_allow`.
  * Sending: only chats in `send_allow` (empty = sending disabled).
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ChatRef:
    """A chat identified by numeric id or by lowercase username (without '@')."""

    chat_id: int | None = None
    username: str | None = None

    @classmethod
    def parse(cls, value: str | int) -> "ChatRef":
        if isinstance(value, int):
            return cls(chat_id=value)
        value = value.strip()
        if value.lstrip("-").isdigit():
            return cls(chat_id=int(value))
        return cls(username=value.removeprefix("@").lower())


@dataclass(frozen=True)
class ResolvedChat:
    chat_id: int  # marked peer id (as in Bot API / Telethon get_peer_id)
    username: str | None = None

    def matches(self, refs: frozenset[ChatRef]) -> bool:
        return any(
            (r.chat_id is not None and r.chat_id == self.chat_id)
            or (r.username is not None and self.username is not None and r.username == self.username.lower())
            for r in refs
        )


@dataclass(frozen=True)
class Policy:
    deny: frozenset[ChatRef] = field(default_factory=frozenset)
    read_allow: frozenset[ChatRef] = field(default_factory=frozenset)
    send_allow: frozenset[ChatRef] = field(default_factory=frozenset)

    def can_read(self, chat: ResolvedChat) -> bool:
        if chat.matches(self.deny):
            return False
        return not self.read_allow or chat.matches(self.read_allow)

    def can_send(self, chat: ResolvedChat) -> bool:
        return not chat.matches(self.deny) and chat.matches(self.send_allow)
