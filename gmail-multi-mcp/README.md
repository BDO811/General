# gmail-multi-mcp

A local MCP server that holds a separate OAuth token for every Gmail account you
own and routes each tool call to the account you name. One server process, one
set of tools, many mailboxes.

This exists because the stock Gmail connector binds to a single authorized
identity. If you run personal mail, a company mailbox, and a second company
mailbox, you otherwise end up either re-authorizing constantly or running three
near-identical servers. Here the account is just an argument.

## How routing works

Every tool takes an optional `account` argument. It accepts either the short
alias you chose (`work`, `personal`, `amplifier`) or the full email address. Omit
it and the registry default is used. `search_all_accounts` ignores the argument
and fans out across every account in parallel, which is the reason to run one
server rather than several.

Tokens are stored one file per account under `~/.gmail-multi-mcp/tokens/`, mode
0600, and refreshed lazily on use. Nothing leaves the machine except calls to
Google.

## Setup

### 1. Create an OAuth client

In Google Cloud Console: create a project, enable the Gmail API, configure the
OAuth consent screen as **External** in testing mode, and add every Gmail address
you plan to connect as a test user. Then create credentials of type **OAuth
client ID**, application type **Desktop app**, and download the JSON.

Save it as `~/.gmail-multi-mcp/client_secret.json`, or point
`GMAIL_MULTI_MCP_CLIENT_SECRET` at wherever you keep it.

One OAuth client serves all of your accounts. The client identifies the app; the
token identifies the mailbox.

### 2. Install

```bash
cd gmail-multi-mcp
python3 -m venv .venv
.venv/bin/pip install -e .
```

Or with uv:

```bash
uv sync
```

### 3. Authorize each account

```bash
gmail-multi-mcp add work --label "Company mail" --default
gmail-multi-mcp add personal
gmail-multi-mcp add board --readonly
```

Each `add` opens a browser. Pick the matching Google account in that window. The
alias is whatever you want the model to say; the email address is read back from
Google after consent so an alias can never silently point at the wrong mailbox.

Verify:

```bash
gmail-multi-mcp list
gmail-multi-mcp test
```

### 4. Register the server with your client

See `examples/claude_desktop_config.json` and `examples/claude_code_mcp.json`.
For Claude Code:

```bash
claude mcp add gmail-multi -- /absolute/path/to/.venv/bin/gmail-multi-mcp serve
```

## Tools

| Tool | What it does |
| --- | --- |
| `list_accounts` | Every registered account, its address, scope mode, and token health |
| `account_profile` | Confirms which mailbox an alias resolves to |
| `search_messages` | Gmail search syntax against one account |
| `search_all_accounts` | The same search across every account, in parallel |
| `get_message` | One message with plain text body and attachment list |
| `get_thread` | A whole thread in order |
| `list_labels` | Label ids and names, needed before `modify_labels` |
| `create_draft` | Draft in a chosen account |
| `send_message` | Send immediately from a chosen account |
| `send_draft` | Send an existing draft |
| `modify_labels` | Add or remove labels, including `UNREAD` and `TRASH` |

## CLI

```
gmail-multi-mcp add <alias> [--label ...] [--readonly] [--default] [--force]
gmail-multi-mcp list [--json]
gmail-multi-mcp default <alias>
gmail-multi-mcp remove <alias>
gmail-multi-mcp test [alias]
gmail-multi-mcp paths
gmail-multi-mcp serve
```

## Scopes

Default is `gmail.modify` plus `gmail.compose`, which covers reading, labeling,
drafting, and sending. Pass `--readonly` on any account that should never be
written to. The server checks the stored scopes before a write and refuses with a
clear message rather than letting Google return an opaque 403.

## Design notes worth knowing

Token refresh is serialized behind a lock so two concurrent tool calls cannot
corrupt a token file. Service objects are cached per alias and dropped on a 401
or 403 so a single stale client does not wedge an account for the life of the
process. A failure on one account during fan-out lands in `errors` rather than
failing the whole call.

The server never opens a browser. Interactive consent only happens through the
CLI, so an MCP client can never trigger a login prompt mid-conversation.

## Security

`client_secret.json`, `accounts.json`, and `tokens/` are all gitignored. The
refresh tokens under `tokens/` grant full access to those mailboxes. Treat that
directory like a password vault, and run `gmail-multi-mcp remove <alias>` plus a
revoke at https://myaccount.google.com/permissions when you retire an account.

## Tests

`tests/smoke_test.py` runs entirely offline against fake tokens. It covers the
tool surface, alias and email routing, the default account and its environment
override, the read only scope guard, token file permissions, MIME assembly, and
body and attachment parsing.

```bash
.venv/bin/python tests/smoke_test.py
```

Built against MCP SDK 2.x, with a fallback import so it still loads under 1.x.
