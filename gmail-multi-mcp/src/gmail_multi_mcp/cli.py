"""CLI for managing accounts. The MCP server never runs an interactive flow itself."""

from __future__ import annotations

import argparse
import json
import os
import plistlib
import subprocess
import sys
from datetime import datetime
from pathlib import Path

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


SCHEDULE_LABEL = "com.gmail-multi-mcp.refresh"


def _executable() -> str | None:
    """Absolute path to this CLI, so a scheduled job never depends on PATH.

    sys.argv[0] is not trustworthy: under `python -m` or a piped script it is a
    module name or "-", and writing that into a launchd plist installs a job that
    silently never runs. Prefer the console script sitting next to the running
    interpreter, which is exactly right for a venv install.
    """
    import shutil

    candidates = [
        Path(sys.executable).parent / "gmail-multi-mcp",
        Path(sys.argv[0]) if sys.argv and sys.argv[0] else None,
        Path(shutil.which("gmail-multi-mcp") or ""),
    ]
    for candidate in candidates:
        if candidate is None or not str(candidate):
            continue
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        if resolved.is_file() and os.access(resolved, os.X_OK):
            return str(resolved)
    return None


def _log_path() -> Path:
    return home() / "logs" / "refresh.log"


def _notify(broken: list[str]) -> None:
    if sys.platform != "darwin":
        return
    title = f"Gmail MCP: {len(broken)} account(s) need re-authorization"
    body = f"{', '.join(broken)}. Run: gmail-multi-mcp reauth"
    script = (
        f"display notification {json.dumps(body)} with title {json.dumps(title)}"
    )
    subprocess.run(["osascript", "-e", script], check=False,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def cmd_refresh(args: argparse.Namespace) -> int:
    """Exercise every token once. Intended for a scheduled job.

    Loading credentials refreshes the access token when it has aged out, and the
    profile call proves the refresh token is still good. This cannot extend the
    seven-day testing-mode expiry, which is fixed at issue time, but it does keep
    tokens warm, defeats the six-month inactivity expiry, and surfaces a dead
    account on a schedule instead of mid-task.
    """
    from . import gmail_client as gm

    registry = Registry()
    accounts = registry.accounts()
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not accounts:
        print(f"[{stamp}] no accounts registered", flush=True)
        return 1

    broken: list[str] = []
    for alias, account in sorted(accounts.items()):
        try:
            info = gm.profile(account)
            print(f"[{stamp}] ok    {alias:<12} {info['email']}", flush=True)
        except (AuthError, gm.GmailError) as exc:
            broken.append(alias)
            print(f"[{stamp}] FAIL  {alias:<12} {exc}", flush=True)

    if broken:
        print(f"[{stamp}] {len(broken)} account(s) need: gmail-multi-mcp reauth", flush=True)
        if args.notify:
            _notify(broken)
        return 1
    return 0


def _plist_path() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"{SCHEDULE_LABEL}.plist"


def _launchctl(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(["launchctl", *argv], capture_output=True, text=True)


def cmd_schedule(args: argparse.Namespace) -> int:
    """Install, remove, or inspect the daily launchd job."""
    if sys.platform != "darwin":
        print("schedule is macOS only. On Linux use cron or a systemd timer:",
              file=sys.stderr)
        print(f"  0 12 * * *  {_executable() or 'gmail-multi-mcp'} refresh", file=sys.stderr)
        return 1

    path = _plist_path()
    domain = f"gui/{os.getuid()}"

    if args.status:
        print(f"plist:   {path}")
        print(f"exists:  {path.exists()}")
        result = _launchctl("print", f"{domain}/{SCHEDULE_LABEL}")
        print(f"loaded:  {result.returncode == 0}")
        print(f"log:     {_log_path()}")
        return 0

    if args.off:
        _launchctl("bootout", f"{domain}/{SCHEDULE_LABEL}")
        if path.exists():
            path.unlink()
            print(f"Removed the daily refresh job ({path}).")
        else:
            print("No scheduled job was installed.")
        return 0

    try:
        hour_s, _, minute_s = args.at.partition(":")
        hour, minute = int(hour_s), int(minute_s or 0)
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError
    except ValueError:
        print(f"Could not read --at '{args.at}'. Use 24 hour HH:MM, e.g. 12:00",
              file=sys.stderr)
        return 1

    executable = _executable()
    if executable is None:
        print("Could not locate the gmail-multi-mcp executable to schedule. Run this "
              "as the installed command, for example "
              "/path/to/.venv/bin/gmail-multi-mcp schedule", file=sys.stderr)
        return 1

    log = _log_path()
    log.parent.mkdir(parents=True, exist_ok=True)

    env = {"GMAIL_MULTI_MCP_HOME": str(home())}
    if os.environ.get("GMAIL_MULTI_MCP_CLIENT_SECRET"):
        env["GMAIL_MULTI_MCP_CLIENT_SECRET"] = os.environ["GMAIL_MULTI_MCP_CLIENT_SECRET"]

    job = {
        "Label": SCHEDULE_LABEL,
        "ProgramArguments": [executable, "refresh", "--notify"],
        "StartCalendarInterval": {"Hour": hour, "Minute": minute},
        "StandardOutPath": str(log),
        "StandardErrorPath": str(log),
        "RunAtLoad": False,
        "EnvironmentVariables": env,
    }

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as fh:
        plistlib.dump(job, fh)

    # Replace any previous copy, otherwise bootstrap refuses with "already loaded".
    _launchctl("bootout", f"{domain}/{SCHEDULE_LABEL}")
    result = _launchctl("bootstrap", domain, str(path))
    if result.returncode != 0:
        legacy = _launchctl("load", "-w", str(path))
        if legacy.returncode != 0:
            print(f"Wrote {path} but launchctl refused to load it:\n"
                  f"{result.stderr.strip() or legacy.stderr.strip()}", file=sys.stderr)
            return 1

    print(f"Daily refresh scheduled for {hour:02d}:{minute:02d} local time.")
    print(f"Job:  {path}")
    print(f"Log:  {log}")
    print(f"Off:  gmail-multi-mcp schedule --off")
    return 0


def _print_drafts(rows: list[dict]) -> None:
    for i, d in enumerate(rows, 1):
        to = d.get("to") or "(no recipient)"
        subject = d.get("subject") or "(no subject)"
        print(f"{i:>3}. {d.get('date','')[:31]:<31} {to[:44]:<44} {subject}")


def cmd_drafts(args: argparse.Namespace) -> int:
    """List unsent drafts in one account."""
    from . import gmail_client as gm

    registry = Registry()
    try:
        account = registry.resolve(args.alias)
    except LookupError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    try:
        rows = gm.list_drafts(account, max_results=args.limit, query=args.query)
    except (AuthError, gm.GmailError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if not rows:
        print(f"No drafts in '{account.alias}' ({account.email}).")
        return 0
    print(f"{len(rows)} draft(s) in '{account.alias}' ({account.email}):\n")
    _print_drafts(rows)
    return 0


def cmd_send_drafts(args: argparse.Namespace) -> int:
    """Send every draft in one account, after showing what will go out.

    Bulk sending is irreversible and drafts accumulate for years, so the list is
    always printed first and the count has to be typed back unless --yes is given.
    """
    from . import gmail_client as gm

    registry = Registry()
    try:
        account = registry.resolve(args.alias)
    except LookupError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    try:
        rows = gm.list_drafts(account, max_results=args.limit, query=args.query)
    except (AuthError, gm.GmailError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if not rows:
        print(f"No drafts in '{account.alias}' ({account.email}). Nothing to send.")
        return 0

    print(f"About to send {len(rows)} draft(s) FROM {account.email}:\n")
    _print_drafts(rows)
    print()

    if not args.yes:
        if not sys.stdin.isatty():
            print("Refusing to send without confirmation. Re-run with --yes.",
                  file=sys.stderr)
            return 1
        answer = input(f"This cannot be undone. Type {len(rows)} to send, anything else to abort: ")
        if answer.strip() != str(len(rows)):
            print("Aborted. Nothing was sent.")
            return 1

    sent, failed = 0, 0
    for row in rows:
        subject = row.get("subject") or "(no subject)"
        try:
            gm.send_draft(account, row["draft_id"])
            sent += 1
            print(f"sent   {row.get('to','')[:44]:<44} {subject}")
        except (AuthError, gm.GmailError) as exc:
            failed += 1
            print(f"FAIL   {row.get('to','')[:44]:<44} {subject}: {exc}", file=sys.stderr)

    print(f"\n{sent} sent, {failed} failed.")
    return 1 if failed else 0


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
    if args.http:
        from .server import serve_http

        serve_http(host=args.host, port=args.port, allowed_hosts=args.allow_host)
        return 0

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

    p_ref = sub.add_parser("refresh",
                           help="exercise every token once; for scheduled runs")
    p_ref.add_argument("--notify", action="store_true",
                       help="send a macOS notification when an account fails")
    p_ref.set_defaults(func=cmd_refresh)

    p_sched = sub.add_parser("schedule",
                             help="install a daily launchd job that runs refresh")
    p_sched.add_argument("--at", default="12:00", help="24 hour HH:MM (default 12:00)")
    p_sched.add_argument("--off", action="store_true", help="remove the scheduled job")
    p_sched.add_argument("--status", action="store_true", help="show whether it is installed")
    p_sched.set_defaults(func=cmd_schedule)

    p_dr = sub.add_parser("drafts", help="list unsent drafts in an account")
    p_dr.add_argument("alias", nargs="?", help="account alias or email; omit for the default")
    p_dr.add_argument("--limit", type=int, default=100, help="max drafts to list")
    p_dr.add_argument("--query", help="optional Gmail search to narrow the drafts")
    p_dr.set_defaults(func=cmd_drafts)

    p_sd = sub.add_parser("send-drafts",
                          help="send every draft in an account, after confirmation")
    p_sd.add_argument("alias", nargs="?", help="account alias or email; omit for the default")
    p_sd.add_argument("--limit", type=int, default=100, help="max drafts to send")
    p_sd.add_argument("--query", help="only send drafts matching this Gmail search")
    p_sd.add_argument("--yes", action="store_true", help="skip the confirmation prompt")
    p_sd.set_defaults(func=cmd_send_drafts)

    p_test = sub.add_parser("test", help="call Gmail once per account to verify tokens")
    p_test.add_argument("alias", nargs="?")
    p_test.set_defaults(func=cmd_test)

    p_paths = sub.add_parser("paths", help="print where config and tokens live")
    p_paths.set_defaults(func=cmd_paths)

    p_serve = sub.add_parser("serve", help="run the MCP server (stdio by default)")
    p_serve.add_argument("--http", action="store_true",
                         help="serve over streamable HTTP instead of stdio, for remote clients")
    p_serve.add_argument("--host", default="127.0.0.1",
                         help="bind address for --http (default 127.0.0.1, use a tunnel to expose)")
    p_serve.add_argument("--port", type=int, default=8765, help="port for --http")
    p_serve.add_argument("--allow-host", action="append",
                         help="hostname a remote client will send in the Host header; "
                              "repeatable, or '*' to disable the check")
    p_serve.set_defaults(func=cmd_serve)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
