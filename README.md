# telegrom-mcp

Own minimal Telegram MCP server (Telethon, personal account, stdio). Tools: `list_chats`, `read_messages`, `send_message`.
No delete/forward/edit/join/file access by design.

## Security model
- `deny` list wins over everything; `read.allow` optionally narrows reading; sending works **only** for `send.allow`.
- Denied and nonexistent chats produce the same error.
- Session and config live in `~/.config/telegrom-mcp` (dir 0700, session 0600). Secrets come from env only.
- Message length, read limit and send rate (10/min) are capped.
- Server instructions and tool docs mark message text as untrusted (prompt-injection defence). For extra safety keep
  `send.allow` tiny and leave Claude Code's per-call approval on for `send_message`.

## Setup
1. Get `api_id`/`api_hash` at https://my.telegram.org (use a separate account if you can).
2. `export TELEGRAM_API_ID=... TELEGRAM_API_HASH=...`
3. `uv run telegrom-mcp-login`
4. `cp config.example.toml ~/.config/telegrom-mcp/config.toml` and edit.
5. `claude mcp add telegram -s user -e TELEGRAM_API_ID=... -e TELEGRAM_API_HASH=... -- uv --directory /home/robot/projects/telegrom-mcp run telegrom-mcp`

## Dev
`uv run pytest && uv run ruff check . && uv run ruff format --check . && uv run mypy src tests`
