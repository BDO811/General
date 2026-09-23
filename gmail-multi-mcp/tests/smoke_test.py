"""Offline checks: tool surface, routing, scope guard, token file permissions.

Nothing here talks to Google. Run with:
    .venv/bin/python tests/smoke_test.py
"""

from __future__ import annotations

import asyncio
import json
import os
import stat
import sys
import tempfile
from pathlib import Path

HOME = Path(tempfile.mkdtemp(prefix="gmail-multi-test-"))
os.environ["GMAIL_MULTI_MCP_HOME"] = str(HOME)

from gmail_multi_mcp import gmail_client as gm  # noqa: E402
from gmail_multi_mcp.config import (  # noqa: E402
    DEFAULT_SCOPES,
    READONLY_SCOPES,
    Account,
    Registry,
    ensure_home,
    token_path,
    write_private_json,
)
from gmail_multi_mcp.server import mcp  # noqa: E402

FAILURES: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"ok    {label}")
    else:
        FAILURES.append(label)
        print(f"FAIL  {label} {detail}")


def seed() -> Registry:
    ensure_home()
    registry = Registry()
    registry.upsert(Account("work", "amit@company.com", list(DEFAULT_SCOPES), "Company"),
                    make_default=True)
    registry.upsert(Account("personal", "amit@gmail.com", list(DEFAULT_SCOPES)))
    registry.upsert(Account("board", "amit@board.org", list(READONLY_SCOPES)))
    for alias in ("work", "personal", "board"):
        write_private_json(token_path(alias), {"refresh_token": "fake", "token": "fake"})
    return registry


EXPECTED_TOOLS = {
    "list_accounts", "account_profile", "search_messages", "search_all_accounts",
    "get_message", "get_thread", "list_labels", "list_drafts", "create_draft",
    "send_message", "send_draft", "modify_labels",
}


async def tool_surface() -> None:
    tools = await mcp.list_tools()
    names = {t.name for t in tools}
    check("all tools registered", EXPECTED_TOOLS <= names, f"missing {EXPECTED_TOOLS - names}")

    by_name = {t.name: t for t in tools}

    def schema(tool):  # 2.x uses input_schema, 1.x used inputSchema
        return getattr(tool, "input_schema", None) or getattr(tool, "inputSchema")

    for name in ("search_messages", "get_message", "send_message"):
        props = schema(by_name[name]).get("properties", {})
        check(f"{name} exposes an account argument", "account" in props)

    required = schema(by_name["send_message"]).get("required", [])
    check("account is optional on send_message", "account" not in required)
    check("every tool is documented", all(t.description for t in tools))

    sender = by_name["send_message"].annotations
    check("send_message marked destructive", bool(sender and sender.destructive_hint))
    reader = by_name["search_messages"].annotations
    check("search marked read only", bool(reader and reader.read_only_hint))


def routing(registry: Registry) -> None:
    check("alias resolves", registry.resolve("work").email == "amit@company.com")
    check("email resolves", registry.resolve("amit@gmail.com").alias == "personal")
    check("case insensitive email", registry.resolve("AMIT@GMAIL.COM").alias == "personal")
    check("None falls back to default", registry.resolve(None).alias == "work")

    try:
        registry.resolve("nope")
        check("unknown alias raises", False)
    except LookupError as exc:
        check("unknown alias raises", True)
        check("error names the valid accounts", "board" in str(exc) and "work" in str(exc))

    os.environ["GMAIL_MULTI_MCP_DEFAULT"] = "personal"
    check("env var overrides default", registry.resolve(None).alias == "personal")
    del os.environ["GMAIL_MULTI_MCP_DEFAULT"]

    registry.set_default("board")
    check("set_default persists", Registry().resolve(None).alias == "board")
    registry.set_default("work")


def scope_guard(registry: Registry) -> None:
    check("write account is not readonly", registry.resolve("work").readonly is False)
    check("readonly account flagged", registry.resolve("board").readonly is True)
    try:
        gm._assert_writable(registry.resolve("board"))
        check("write to readonly account is refused", False)
    except gm.GmailError as exc:
        check("write to readonly account is refused", True)
        check("refusal explains the fix", "--force" in str(exc))


def permissions() -> None:
    mode = stat.S_IMODE(token_path("work").stat().st_mode)
    check("token file is owner only", mode == 0o600, f"got {oct(mode)}")
    reg_mode = stat.S_IMODE(Registry().path.stat().st_mode)
    check("registry file is owner only", reg_mode == 0o600, f"got {oct(reg_mode)}")


def parsing() -> None:
    import base64

    def b64(text: str) -> str:
        return base64.urlsafe_b64encode(text.encode()).decode().rstrip("=")

    payload = {
        "mimeType": "multipart/mixed",
        "headers": [
            {"name": "From", "value": "sam@x.com"},
            {"name": "Subject", "value": "Term sheet"},
        ],
        "parts": [
            {
                "mimeType": "multipart/alternative",
                "parts": [
                    {"mimeType": "text/plain", "body": {"data": b64("plain wins")}},
                    {"mimeType": "text/html", "body": {"data": b64("<p>html</p>")}},
                ],
            },
            {
                "mimeType": "application/pdf",
                "filename": "terms.pdf",
                "body": {"attachmentId": "att-1", "size": 4096},
            },
        ],
    }
    check("plain text preferred over html", gm.extract_body(payload) == "plain wins")
    atts = gm.list_attachments(payload)
    check("attachment discovered", len(atts) == 1 and atts[0]["filename"] == "terms.pdf")

    html_only = {
        "mimeType": "multipart/alternative",
        "parts": [{"mimeType": "text/html", "body": {"data": b64("<p>only html</p>")}}],
    }
    check("falls back to html", "only html" in gm.extract_body(html_only))

    summary = gm.summarize("work", {"id": "m1", "threadId": "t1", "labelIds": ["UNREAD"],
                                    "snippet": "hi", "payload": payload})
    check("summary carries the account", summary["account"] == "work")
    check("unread derived from labels", summary["unread"] is True)
    check("subject parsed", summary["subject"] == "Term sheet")


def mime() -> None:
    msg = gm._build_mime("me@a.com", ["you@b.com"], "Hi", "Body",
                         cc=["c@b.com"], reply_to_message_id="<abc@mail>")
    raw = msg.as_string()
    check("cc set on mime", "c@b.com" in raw)
    check("reply headers set", "In-Reply-To" in raw and "References" in raw)
    check("mime encodes cleanly", isinstance(gm._encoded(msg), str))


def removal(registry: Registry) -> None:
    registry.upsert(Account("temp", "t@x.com", list(DEFAULT_SCOPES)))
    write_private_json(token_path("temp"), {"refresh_token": "fake"})
    check("remove returns True", registry.remove("temp") is True)
    check("token deleted on remove", not token_path("temp").exists())
    check("remove of unknown alias returns False", registry.remove("temp") is False)


def main() -> int:
    registry = seed()
    asyncio.run(tool_surface())
    routing(registry)
    scope_guard(registry)
    permissions()
    parsing()
    mime()
    removal(registry)

    print()
    if FAILURES:
        print(f"{len(FAILURES)} check(s) failed: {', '.join(FAILURES)}")
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
