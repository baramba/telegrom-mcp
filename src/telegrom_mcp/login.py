"""One-time interactive login. Creates the session file with 0600 permissions."""

import asyncio
import os

from telethon import TelegramClient

from telegrom_mcp.config import load_settings


async def _login() -> None:
    s = load_settings()
    client = TelegramClient(str(s.session_path), s.api_id, s.api_hash)
    await client.start()  # prompts for phone, code, 2FA
    await client.disconnect()
    for f in s.session_path.parent.glob(s.session_path.name + "*"):
        os.chmod(f, 0o600)
    print(f"Logged in. Session stored at {s.session_path}.session")


def main() -> None:
    asyncio.run(_login())
