"""CLI for managing accounts. The MCP server never runs an interactive flow itself."""

from __future__ import annotations

import argparse
import json
import sys

from .auth import AuthError, load_credentials, run_consent_flow, token_status, whoami
from .config import (
    DEFAULT_SCOPES,
    READONLY_SCOPES,
    Account,
    Registry,
    client_secret_path,
    ensure_home,
    home,
    now_iso,
    token_path,
)


def cmd_add(args: argparse.Namespace) -> int:
    ensure_home()
    registry = Registry()
    alias = args.alias

    if token_path(alias).exists() and not args.force:
        print(f"Account '{alias}' already has a token. Use --force to re-authorize.")
        return 1

    scopes = READONLY_SCOPES if args.readonly else DEFAULT_SCOPES
    use_browser = False if args.no_browser else None
    try:
        creds = run_consent_flow(alias, scopes, port=args.port,
                                 use_browser=use_browser, timeout_seconds=args.timeout)
        email = whoami(creds)
    except AuthError as exc:
        print(f"Authorization failed: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        # Ctrl+C while waiting on the redirect is a normal way out, not a crash.
        print(f"\nCancelled. '{alias}' was not authorized.", file=sys.stderr)
        return 130

    existing = {a.email.lower(): a.alias for a in registry.accounts().values() if a.email}
    if email.lower() in existing and existing[email.lower()] != alias:
        print(
            f"Warning: {email} is already registered as '{existing[email.lower()]}'. "
            f"'{alias}' now points at the same mailbox."
        )

    registry.upsert(
        Account(alias=alias, email=email, scopes=scopes,
                label=args.label or "", added_at=now_iso()),
        make_default=args.default,
    )
    mode = "read only" if args.readonly else "read and write"
    print(f"Authorized {email} as '{alias}' ({mode}).")
    print(f"Token stored at {token_path(alias)}")
    return 0


def _token_ok(account: Account) -> bool:
    if not token_path(account.alias).exists():
        return False
    try:
        load_credentials(account)
        return True
    except AuthError:
        return False


def cmd_reauth(args: argparse.Namespace) -> int:
    """Re-run consent for accounts whose tokens have gone stale.

    In testing mode Google expires refresh tokens after seven days, which
    otherwise means hunting down each broken account by hand.
    """
    registry = Registry()
    accounts = registry.accounts()
    if not accounts:
        print("No accounts registered.", file=sys.stderr)
        return 1

    if args.alias:
        try:
            targets = [registry.resolve(args.alias)]
        except LookupError as exc:
            print(str(exc), file=sys.stderr)
            return 1
    else:
        targets = [a for _, a in sorted(accounts.items())]
        if not args.all:
            targets = [a for a in targets if not _token_ok(a)]
            if not targets:
                print("All tokens are healthy. Nothing to do.")
                return 0

    print(f"Re-authorizing {len(targets)} account(s): {', '.join(a.alias for a in targets)}")
    print("Each one opens a browser. Pick the matching account in every window.\n")

    use_browser = False if args.no_browser else None
    failures = 0
    for account in targets:
        try:
            creds = run_consent_flow(account.alias, account.scopes, port=args.port,
                                     use_browser=use_browser, timeout_seconds=args.timeout)
            email = whoami(creds)
        except AuthError as exc:
            failures += 1
            print(f"FAIL  {account.alias}: {exc}\n", file=sys.stderr)
            continue
        except KeyboardInterrupt:
            print(f"\nCancelled at '{account.alias}'. Remaining accounts were skipped.",
                  file=sys.stderr)
            return 130

        # A reauth must land on the same mailbox. Picking the wrong account in the
        # browser would otherwise silently repoint the alias.
        if account.email and email.lower() != account.email.lower():
            failures += 1
            token_path(account.alias).unlink(missing_ok=True)
            print(
                f"FAIL  {account.alias}: authorized {email} but this alias belongs to "
                f"{account.email}. Token discarded, alias unchanged. Retry and pick "
                f"{account.email} in the browser.\n",
                file=sys.stderr,
            )
            continue

        registry.upsert(Account(alias=account.alias, email=email, scopes=account.scopes,
                                label=account.label, added_at=now_iso()))
        print(f"ok    {account.alias:<12} {email}\n")

    return 1 if failures else 0


def cmd_list(args: argparse.Namespace) -> int:
    registry = Registry()
    rows = token_status(registry)
    if args.json:
        print(json.dumps({"default": registry.default_alias(), "accounts": rows}, indent=2))
        return 0
    if not rows:
        print("No accounts registered. Add one with: gmail-multi-mcp add <alias>")
        return 0
    default = registry.default_alias()
    width = max(len(r["account"]) for r in rows)
    for row in rows:
        marker = "*" if row["account"] == default else " "
        scope = "ro" if row["readonly"] else "rw"
        print(f"{marker} {row['account']:<{width}}  {row['email']:<34} [{scope}]  {row['status']}")
    print("\n* = default account used when a tool call omits `account`.")
    return 0


def cmd_remove(args: argparse.Namespace) -> int:
    registry = Registry()
    if registry.remove(args.alias):
        print(f"Removed '{args.alias}' and deleted its token.")
        return 0
    print(f"No account named '{args.alias}'.", file=sys.stderr)
    return 1


def cmd_default(args: argparse.Namespace) -> int:
    registry = Registry()
    try:
        registry.set_default(args.alias)
    except LookupError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"Default account is now '{args.alias}'.")
    return 0


def cmd_test(args: argparse.Namespace) -> int:
    from . import gmail_client as gm

    registry = Registry()
    accounts = registry.accounts()
    if args.alias:
        try:
            accounts = {args.alias: registry.resolve(args.alias)}
        except LookupError as exc:
            print(str(exc), file=sys.stderr)
            return 1
    if not accounts:
        print("No accounts registered.", file=sys.stderr)
        return 1

    failures = 0
    for alias, account in sorted(accounts.items()):
        try:
            info = gm.profile(account)
            print(f"ok    {alias:<12} {info['email']:<34} {info['messages_total']} messages")
        except (AuthError, gm.GmailError) as exc:
            failures += 1
            print(f"FAIL  {alias:<12} {exc}")
    return 1 if failures else 0


def cmd_paths(args: argparse.Namespace) -> int:
    print(f"home:          {home()}")
    print(f"registry:      {Registry().path}")
    print(f"client secret: {client_secret_path()}")
    print(f"tokens:        {home() / 'tokens'}")
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    from .server import main as serve

    serve()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gmail-multi-mcp",
        description="Manage multiple Gmail OAuth tokens and serve them over MCP.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="authorize a Gmail account and store its token")
    p_add.add_argument("alias", help="short name the model will use, e.g. work")
    p_add.add_argument("--label", default="", help="human readable note")
    p_add.add_argument("--readonly", action="store_true", help="request read only scopes")
    p_add.add_argument("--default", action="store_true", help="make this the default account")
    p_add.add_argument("--force", action="store_true", help="re-authorize an existing alias")
    p_add.add_argument("--port", type=int, default=0, help="loopback port for the OAuth redirect")
    p_add.add_argument("--no-browser", action="store_true",
                       help="do not open a browser, just print the URL to paste")
    p_add.add_argument("--timeout", type=int, default=300,
                       help="seconds to wait for the redirect back (default 300)")
    p_add.set_defaults(func=cmd_add)

    p_list = sub.add_parser("list", help="show registered accounts and token health")
    p_list.add_argument("--json", action="store_true")
    p_list.set_defaults(func=cmd_list)

    p_rm = sub.add_parser("remove", help="forget an account and delete its token")
    p_rm.add_argument("alias")
    p_rm.set_defaults(func=cmd_remove)

    p_def = sub.add_parser("default", help="set the default account")
    p_def.add_argument("alias")
    p_def.set_defaults(func=cmd_default)

    p_re = sub.add_parser("reauth",
                          help="re-run consent for accounts with expired or broken tokens")
    p_re.add_argument("alias", nargs="?", help="one account; omit to sweep all of them")
    p_re.add_argument("--all", action="store_true",
                      help="re-authorize every account, not just the broken ones")
    p_re.add_argument("--no-browser", action="store_true",
                      help="do not open a browser, just print each URL")
    p_re.add_argument("--port", type=int, default=0, help="loopback port for the redirect")
    p_re.add_argument("--timeout", type=int, default=300,
                      help="seconds to wait for each redirect (default 300)")
    p_re.set_defaults(func=cmd_reauth)

    p_test = sub.add_parser("test", help="call Gmail once per account to verify tokens")
    p_test.add_argument("alias", nargs="?")
    p_test.set_defaults(func=cmd_test)

    p_paths = sub.add_parser("paths", help="print where config and tokens live")
    p_paths.set_defaults(func=cmd_paths)

    p_serve = sub.add_parser("serve", help="run the MCP server on stdio")
    p_serve.set_defaults(func=cmd_serve)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
