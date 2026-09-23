"""MCP server exposing every registered Gmail account through one set of tools.

Routing rule: every tool takes an optional `account` argument holding an alias
("work", "personal") or the full address. Omit it and the registry default is
used. `search_all_accounts` fans out across every account at once, which is the
whole reason for running one server instead of several.
"""

from __future__ import annotations

import concurrent.futures
from typing import Annotated, Any

from mcp.types import ToolAnnotations
from pydantic import Field

from . import gmail_client as gm
from .auth import AuthError, token_status
from .config import Registry

try:  # MCP SDK 2.x
    from mcp.server.mcpserver import MCPServer as _Server
    from mcp.server.mcpserver.exceptions import ToolError
except ImportError:  # MCP SDK 1.x, where the class was called FastMCP
    from mcp.server.fastmcp import FastMCP as _Server
    from mcp.server.fastmcp.exceptions import ToolError

mcp = _Server(
    "gmail-multi",
    instructions=(
        "Gmail across several accounts. Each tool takes an optional `account` "
        "argument holding an alias or an email address; omit it to use the default. "
        "Call list_accounts when you do not know which aliases exist, and "
        "search_all_accounts when you do not know which mailbox holds a thread. "
        "Confirm the account before sending mail."
    ),
)
REGISTRY = Registry()

READ_ONLY = ToolAnnotations(read_only_hint=True, open_world_hint=True)
WRITE = ToolAnnotations(read_only_hint=False, destructive_hint=False, open_world_hint=True)
DESTRUCTIVE = ToolAnnotations(read_only_hint=False, destructive_hint=True, open_world_hint=True)

AccountArg = Annotated[
    str | None,
    Field(
        default=None,
        description=(
            "Which Gmail account to use: a registered alias or the full email address. "
            "Omit to use the default account. Call list_accounts to see the options."
        ),
    ),
]


def _resolve(alias: str | None):
    """Turn a caller-supplied alias into an account, or fail with an actionable message."""
    try:
        return REGISTRY.resolve(alias)
    except LookupError as exc:
        raise ToolError(str(exc)) from exc


def _run(alias: str | None, fn, *args, **kwargs) -> Any:
    account = _resolve(alias)
    try:
        return fn(account, *args, **kwargs)
    except (AuthError, gm.GmailError) as exc:
        raise ToolError(str(exc)) from exc


# ------------------------------------------------------------------- discovery


@mcp.tool(annotations=READ_ONLY)
def list_accounts() -> dict:
    """List every Gmail account this server can route to, with its authorization state.

    Call this first when you do not already know which aliases exist.
    """
    rows = token_status(REGISTRY)
    return {
        "default_account": REGISTRY.default_alias(),
        "count": len(rows),
        "accounts": rows,
    }


@mcp.tool(annotations=READ_ONLY)
def account_profile(account: AccountArg = None) -> dict:
    """Confirm which mailbox an alias actually resolves to, plus message and thread counts."""
    return _run(account, gm.profile)


# ------------------------------------------------------------------------ read


@mcp.tool(annotations=READ_ONLY)
def search_messages(
    query: Annotated[str, Field(description="Gmail search syntax, e.g. 'from:sam@x.com is:unread newer_than:7d'")],
    account: AccountArg = None,
    max_results: Annotated[int, Field(default=20, ge=1, le=100)] = 20,
    include_spam_trash: bool = False,
) -> dict:
    """Search one account's mail and return message summaries (no bodies)."""
    results = _run(account, gm.search, query, max_results, include_spam_trash)
    return {"account": _resolve(account).alias, "query": query,
            "count": len(results), "messages": results}


@mcp.tool(annotations=READ_ONLY)
def search_all_accounts(
    query: Annotated[str, Field(description="Gmail search syntax applied to every account")],
    max_results_per_account: Annotated[int, Field(default=10, ge=1, le=50)] = 10,
    accounts: Annotated[
        list[str] | None,
        Field(default=None, description="Restrict the fan-out to these aliases. Omit for all."),
    ] = None,
) -> dict:
    """Run one search across every registered account in parallel.

    Use this when you do not know which mailbox holds the thread, or when you
    need a single view across work and personal mail. Failures on one account do
    not block the others; they come back in `errors`.
    """
    registry_accounts = REGISTRY.accounts()
    if not registry_accounts:
        raise ToolError("No Gmail accounts are registered. Run: gmail-multi-mcp add <alias>")

    if accounts:
        selected = []
        for alias in accounts:
            selected.append(_resolve(alias))
    else:
        selected = list(registry_accounts.values())

    messages: list[dict] = []
    errors: list[dict] = []

    def one(acct):
        return acct, gm.search(acct, query, max_results_per_account)

    with concurrent.futures.ThreadPoolExecutor(max_workers=min(8, len(selected))) as pool:
        futures = [pool.submit(one, a) for a in selected]
        for future in concurrent.futures.as_completed(futures):
            try:
                acct, rows = future.result()
                messages.extend(rows)
            except (AuthError, gm.GmailError) as exc:
                errors.append({"error": str(exc)})
            except Exception as exc:  # keep one bad account from sinking the fan-out
                errors.append({"error": f"{type(exc).__name__}: {exc}"})

    messages.sort(key=lambda m: m.get("date", ""), reverse=True)
    return {
        "query": query,
        "accounts_searched": [a.alias for a in selected],
        "count": len(messages),
        "messages": messages,
        "errors": errors,
    }


@mcp.tool(annotations=READ_ONLY)
def get_message(
    message_id: Annotated[str, Field(description="Gmail message id from a search result")],
    account: AccountArg = None,
    include_body: bool = True,
) -> dict:
    """Fetch one message, including its plain text body and attachment list."""
    return _run(account, gm.get_message, message_id, include_body)


@mcp.tool(annotations=READ_ONLY)
def get_thread(
    thread_id: Annotated[str, Field(description="Gmail thread id from a search result")],
    account: AccountArg = None,
    include_body: bool = True,
) -> dict:
    """Fetch a whole thread in order, so a reply can be written with full context."""
    return _run(account, gm.get_thread, thread_id, include_body)


@mcp.tool(annotations=READ_ONLY)
def list_labels(account: AccountArg = None) -> dict:
    """List label ids and names for one account, needed before modify_labels."""
    labels = _run(account, gm.list_labels)
    return {"account": _resolve(account).alias, "count": len(labels), "labels": labels}


# ----------------------------------------------------------------------- write


@mcp.tool(annotations=WRITE)
def create_draft(
    to: Annotated[list[str], Field(description="Recipient addresses")],
    subject: str,
    body: Annotated[str, Field(description="Plain text body unless html is true")],
    account: AccountArg = None,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    thread_id: Annotated[str | None, Field(default=None, description="Attach the draft to this thread to reply in place")] = None,
    html: bool = False,
) -> dict:
    """Create a draft in one account. Prefer this over send_message when a human should review it."""
    return _run(account, gm.create_draft, to, subject, body, cc, bcc, thread_id, html)


@mcp.tool(annotations=DESTRUCTIVE)
def send_message(
    to: Annotated[list[str], Field(description="Recipient addresses")],
    subject: str,
    body: Annotated[str, Field(description="Plain text body unless html is true")],
    account: AccountArg = None,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    thread_id: Annotated[str | None, Field(default=None, description="Send as a reply inside this thread")] = None,
    html: bool = False,
) -> dict:
    """Send mail immediately from one account. This is irreversible, so confirm the account first."""
    return _run(account, gm.send_message, to, subject, body, cc, bcc, thread_id, html)


@mcp.tool(annotations=DESTRUCTIVE)
def send_draft(
    draft_id: Annotated[str, Field(description="Draft id returned by create_draft")],
    account: AccountArg = None,
) -> dict:
    """Send a draft that already exists in the account."""
    return _run(account, gm.send_draft, draft_id)


@mcp.tool(annotations=DESTRUCTIVE)
def modify_labels(
    message_id: str,
    account: AccountArg = None,
    add_label_ids: list[str] | None = None,
    remove_label_ids: list[str] | None = None,
) -> dict:
    """Add or remove labels on a message. Remove 'UNREAD' to mark read, add 'TRASH' to trash."""
    return _run(account, gm.modify_labels, message_id, add_label_ids, remove_label_ids)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
