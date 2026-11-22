# telegrom-mcp

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE) [![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](pyproject.toml)

A **policy-guarded Telegram MCP server** for your **personal** Telegram account (Telethon, stdio).
It gives an AI coding agent exactly three abilities — **list chats, read messages, send messages** —
under an access policy you control. There is deliberately **no** delete, forward, edit, join, or
file access: those tools simply do not exist.

> **Easiest path:** install the [telegrom-skill](https://github.com/baramba/telegrom-skill) — an
> agent skill that walks your agent through the whole setup and teaches it the safety rules:
>
> ```bash
> npx skills add baramba/telegrom-skill
> ```
>
> Then just ask your agent: *"Set up telegrom-mcp and connect me to Telegram."*
> This README is the canonical reference and a manual installation guide.

## How it works

```
You ──▶ Your agent (Claude Code, Cursor, Codex, Gemini, Copilot, …)
              │  MCP (stdio)
              ▼
        telegrom-mcp ── checks your policy (~/.config/telegrom-mcp/config.toml)
              │
              ▼
        Telegram (your personal account)
```

## Tools

| Tool | Arguments | What it does |
|---|---|---|
| `list_chats` | `limit` (default 20, capped at 50) | Recent chats visible under the policy: id, name, username, unread count |
| `read_messages` | `chat` (numeric id or `@username`), `limit` (default 20, capped at 50), `search` (optional text filter) | Latest messages of a chat: id, date, sender, outgoing flag, text |
| `send_message` | `chat`, `text` (1–4000 characters), `reply_to` (optional message id) | Sends a text message — **only** to chats listed in `send.allow` |

## Requirements

| What you need | Why | Where to get it |
|---|---|---|
| `uv` | installs and runs the server as an isolated tool | `curl -LsSf https://astral.sh/uv/install.sh \| sh` (macOS/Linux) or `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 \| iex"` (Windows) |
| Python 3.12+ | runtime — handled automatically by `uv` | nothing to do |
| `TELEGRAM_API_ID` / `TELEGRAM_API_HASH` | free API keys from Telegram | [my.telegram.org](https://my.telegram.org) → **API development tools** |
| A Telegram account | the account the agent connects to | any personal account; a **spare** one is recommended |
| An MCP-capable agent | the thing you talk to | Claude Code, Cursor, Codex CLI, Gemini CLI, Copilot CLI, … |

Works on Linux, macOS, and Windows. Nothing needs sudo — everything lives in your user profile.

## Setup

### 1. Install the server

```bash
uv tool install git+https://github.com/baramba/telegrom-mcp
```

This puts two commands on your `PATH`: `telegrom-mcp` (the MCP server) and
`telegrom-mcp-login` (one-time interactive login). Later updates: `uv tool upgrade telegrom-mcp`.

### 2. Export your API keys

macOS / Linux:

```bash
export TELEGRAM_API_ID="paste-your-api_id-here"
export TELEGRAM_API_HASH="paste-your-api_hash-here"
```

Windows (PowerShell, saved permanently for your user):

```powershell
[Environment]::SetEnvironmentVariable("TELEGRAM_API_ID","paste-your-api_id-here","User")
[Environment]::SetEnvironmentVariable("TELEGRAM_API_HASH","paste-your-api_hash-here","User")
```

### 3. Log in once (interactive, you only)

Run this **yourself in a terminal**, never in the agent chat:

```bash
telegrom-mcp-login
```

It asks for your phone number, the login code Telegram sends you, and your 2FA password if you
have one. The session is stored at `~/.config/telegrom-mcp/session` with `0600` permissions inside
a `0700` directory. Your credentials never reach the agent.

### 4. Write your access policy

```bash
cp config.example.toml ~/.config/telegrom-mcp/config.toml   # Windows: %USERPROFILE%\.config\telegrom-mcp\config.toml
```

Edit it. Chats are identified by numeric id (e.g. `-1001234567890`) or `@username`:

```toml
deny = ["@bank_bot", "@BotFather"]   # never readable, never writable — always wins

[read]
allow = []    # empty = every chat except denied ones; non-empty = only these chats

[send]
allow = []    # empty = sending is disabled; only these chats can ever be written to
```

If the file is missing, the server is read-only everywhere and sending is disabled.
The config directory can be moved with the `TELEGROM_HOME` environment variable.

### 5. Register the server with your agent

<details>
<summary>Commands for Claude Code, Codex, Gemini, Copilot, and Cursor</summary>

```bash
# Claude Code
claude mcp add telegram -s user \
  -e TELEGRAM_API_ID="$TELEGRAM_API_ID" -e TELEGRAM_API_HASH="$TELEGRAM_API_HASH" \
  -- telegrom-mcp

# OpenAI Codex CLI
codex mcp add telegram \
  --env TELEGRAM_API_ID="$TELEGRAM_API_ID" --env TELEGRAM_API_HASH="$TELEGRAM_API_HASH" \
  -- telegrom-mcp

# Gemini CLI (-s user is important: the default scope is project-only)
gemini mcp add -s user telegram \
  -e TELEGRAM_API_ID="$TELEGRAM_API_ID" -e TELEGRAM_API_HASH="$TELEGRAM_API_HASH" \
  -- telegrom-mcp

# GitHub Copilot CLI (writes to ~/.copilot/mcp-config.json)
copilot mcp add telegram \
  --env TELEGRAM_API_ID="$TELEGRAM_API_ID" --env TELEGRAM_API_HASH="$TELEGRAM_API_HASH" \
  -- telegrom-mcp
```

Cursor has no `mcp add` command — add this to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "telegram": {
      "command": "telegrom-mcp",
      "env": {
        "TELEGRAM_API_ID": "${env:TELEGRAM_API_ID}",
        "TELEGRAM_API_HASH": "${env:TELEGRAM_API_HASH}"
      }
    }
  }
}
```

After registering, restart your agent session.

</details>

Then check it works — ask your agent: *"What Telegram chats can you see?"*
Sending is **disabled by default** (the send list starts empty) — that is normal and safe.

## Usage

Example requests the agent can handle:

| You say | What happens |
|---|---|
| "What's new in my chats today?" | Lists chats, reads recent messages |
| "Find the message where Anna sent the invoice number" | Searches a chat (up to 50 messages per call) |
| "Send my summary to the project chat" | Sends — only if that chat is in `send.allow` |
| "Which chats can you write to?" | Reports the current policy in plain language |

Requests that are refused — by design, not by persuasion:

| You say | Why it fails |
|---|---|
| "Delete / forward / edit that message" | No such tools exist |
| "Read my bank bot chat" (in `deny`) | Same error as a nonexistent chat — the policy does not leak what is hidden |
| "Send to any chat not in `send.allow`" | Access denied |
| "Send 20 messages quickly" | Blocked after 10 messages per minute |

## Security model

- `deny` wins over everything, for reading and sending; `read.allow` optionally narrows reading;
  sending works **only** for `send.allow`.
- Denied and nonexistent chats produce the **same** error, so the policy never leaks what is hidden.
- Hard caps enforced by the server: 4000 characters per message, 50 messages per read,
  10 sends per minute.
- Message text returned to the agent is marked as **untrusted third-party content**
  (prompt-injection defence).
- Secrets come from the environment only; the session file is `0600` inside a `0700` directory.
- For extra safety keep `send.allow` tiny and leave your agent's per-call approval on for
  `send_message`.

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| `Environment variable TELEGRAM_API_ID is required` | Variables were exported in another terminal, or the agent started before you exported | Re-export in the terminal you start the agent from, re-register, restart the session |
| `Not logged in` / `Telegram client is not ready` | One-time login not completed | Run `telegrom-mcp-login` yourself in a terminal |
| `Chat not found or access denied` | Chat is in `deny`, or missing from `read.allow` / `send.allow` | Check `~/.config/telegrom-mcp/config.toml` |
| `Send rate limit reached` | 10 messages/minute cap | Wait a minute and retry — do not try to bypass it |

## Uninstall

```bash
uv tool uninstall telegrom-mcp
claude mcp remove telegram          # or your harness's equivalent
rm -rf ~/.config/telegrom-mcp       # Windows: rmdir /s %USERPROFILE%\.config\telegrom-mcp
```

Then delete the skill folder from your agent's skills directory, if you installed it.

## Development

```bash
git clone https://github.com/baramba/telegrom-mcp
cd telegrom-mcp
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests
```

To run the server from a clone instead of an installed tool:
`uv run telegrom-mcp` and `uv run telegrom-mcp-login`.

## Links

- [telegrom-skill](https://github.com/baramba/telegrom-skill) — agent skill that installs and safely uses this server
- [telegrom-skill references](https://github.com/baramba/telegrom-skill/tree/master/telegrom/references) — security model and full config reference
- [telegrom-skill examples](https://github.com/baramba/telegrom-skill/tree/master/telegrom/examples) — example requests and what the policy refuses

## License

MIT — see [LICENSE](LICENSE).
