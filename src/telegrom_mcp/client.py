"""Telethon wrapper that enforces the policy on every operation."""

import time
from collections import deque
from dataclasses import dataclass
from typing import Any

from telethon import TelegramClient, utils
from telethon.tl.custom import Dialog
from telethon.tl.types import Message, User

from telegrom_mcp.config import Settings
from telegrom_mcp.policy import ResolvedChat


class AccessDenied(Exception):
    """Raised when policy forbids an operation. Message is safe to show to the model."""


@dataclass(frozen=True)
class ChatInfo:
    id: int
    name: str
    username: str | None
    unread: int


@dataclass(frozen=True)
class MessageInfo:
    id: int
    date: str
    sender: str
    outgoing: bool
    text: str


def _resolved(entity: Any) -> ResolvedChat:
    return ResolvedChat(utils.get_peer_id(entity), getattr(entity, "username", None))


def _sender_name(entity: Any) -> str:
    if isinstance(entity, User):
        return " ".join(p for p in (entity.first_name, entity.last_name) if p) or entity.username or str(entity.id)
    return getattr(entity, "title", None) or str(getattr(entity, "id", "?"))


class GuardedTelegram:
    def __init__(self, settings: Settings) -> None:
        self._s = settings
        self._client = TelegramClient(str(settings.session_path), settings.api_id, settings.api_hash)
        self._sent: deque[float] = deque()

    async def connect(self) -> None:
        await self._client.connect()
        if not await self._client.is_user_authorized():
            raise SystemExit("Not logged in. Run: uv run telegrom-mcp-login")

    async def disconnect(self) -> None:
        await self._client.disconnect()

    async def _entity(self, chat: str | int) -> Any:
        if isinstance(chat, str) and chat.lstrip("-").isdigit():
            chat = int(chat)
        try:
            return await self._client.get_entity(chat)
        except (ValueError, TypeError):
            # Unknown and denied chats look identical to the caller.
            raise AccessDenied("Chat not found or access denied") from None

    def _trim(self, text: str) -> str:
        limit = self._s.max_message_chars
        return text if len(text) <= limit else text[:limit] + "…[truncated]"

    async def list_chats(self, limit: int) -> list[ChatInfo]:
        limit = max(1, min(limit, self._s.max_read_limit))
        result: list[ChatInfo] = []
        async for d in self._client.iter_dialogs():
            dialog: Dialog = d
            if self._s.policy.can_read(_resolved(dialog.entity)):
                result.append(
                    ChatInfo(
                        dialog.id,
                        dialog.name,
                        getattr(dialog.entity, "username", None),
                        dialog.unread_count,
                    )
                )
                if len(result) >= limit:
                    break
        return result

    async def read_messages(self, chat: str | int, limit: int, search: str | None = None) -> list[MessageInfo]:
        entity = await self._entity(chat)
        if not self._s.policy.can_read(_resolved(entity)):
            raise AccessDenied("Chat not found or access denied")
        limit = max(1, min(limit, self._s.max_read_limit))
        out: list[MessageInfo] = []
        async for m in self._client.iter_messages(entity, limit=limit, search=search or None):
            msg: Message = m
            sender = await msg.get_sender()
            out.append(
                MessageInfo(
                    msg.id,
                    msg.date.isoformat() if msg.date else "",
                    _sender_name(sender),
                    bool(msg.out),
                    self._trim(msg.message or "[non-text message]"),
                )
            )
        return out

    async def send_message(self, chat: str | int, text: str, reply_to: int | None = None) -> int:
        entity = await self._entity(chat)
        if not self._s.policy.can_send(_resolved(entity)):
            raise AccessDenied("Sending to this chat is not allowed")
        if not text.strip() or len(text) > self._s.max_message_chars:
            raise ValueError(f"Text must be 1..{self._s.max_message_chars} characters")
        now = time.monotonic()
        while self._sent and now - self._sent[0] > 60:
            self._sent.popleft()
        if len(self._sent) >= self._s.send_rate_per_minute:
            raise AccessDenied("Send rate limit reached, try again later")
        self._sent.append(now)
        sent = await self._client.send_message(entity, text, reply_to=reply_to, link_preview=False)
        return int(sent.id)
