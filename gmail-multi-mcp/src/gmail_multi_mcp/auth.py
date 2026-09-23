"""OAuth token handling: one token file per account, refreshed lazily.

The interactive consent flow only ever runs from the CLI. The MCP server itself
never opens a browser; if a token is missing or unrecoverable it returns an
error telling the operator which CLI command to run.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from .config import (
    Account,
    Registry,
    client_secret_path,
    ensure_home,
    now_iso,
    token_path,
    write_private_json,
)


class AuthError(RuntimeError):
    pass


_refresh_lock = threading.Lock()


def load_credentials(account: Account) -> Credentials:
    """Return usable credentials for one account, refreshing and persisting if needed."""
    path = token_path(account.alias)
    if not path.exists():
        raise AuthError(
            f"No stored token for account '{account.alias}'. "
            f"Run: gmail-multi-mcp add {account.alias}"
        )
    with path.open(encoding="utf-8") as fh:
        info = json.load(fh)

    try:
        creds = Credentials.from_authorized_user_info(info, scopes=account.scopes)
    except ValueError as exc:
        raise AuthError(
            f"Token file for '{account.alias}' is malformed ({exc}). "
            f"Re-authorize with: gmail-multi-mcp add {account.alias} --force"
        ) from exc

    if creds.valid:
        return creds

    if not creds.refresh_token:
        raise AuthError(
            f"Token for '{account.alias}' expired and carries no refresh token. "
            f"Run: gmail-multi-mcp add {account.alias} --force"
        )

    # Serialize refreshes so two concurrent tool calls cannot race on the file.
    with _refresh_lock:
        try:
            creds.refresh(Request())
        except Exception as exc:
            raise AuthError(
                f"Could not refresh the token for '{account.alias}': {exc}. "
                f"Re-authorize with: gmail-multi-mcp add {account.alias} --force"
            ) from exc
        persist_credentials(account.alias, creds)
    return creds


def persist_credentials(alias: str, creds: Credentials) -> None:
    ensure_home()
    payload = json.loads(creds.to_json())
    payload["stored_at"] = now_iso()
    write_private_json(token_path(alias), payload)


def run_consent_flow(alias: str, scopes: list[str], port: int = 0) -> Credentials:
    """Run the local loopback OAuth flow for one account.

    Google ties the refresh token to the Google account picked in the browser, so
    running this once per Gmail account is what gives the server its separate
    identities.
    """
    from google_auth_oauthlib.flow import InstalledAppFlow

    secret = client_secret_path()
    if not secret.exists():
        raise AuthError(
            f"OAuth client file not found at {secret}. Download the Desktop app "
            "client_secret.json from Google Cloud Console and place it there, or "
            "point GMAIL_MULTI_MCP_CLIENT_SECRET at it."
        )

    flow = InstalledAppFlow.from_client_secrets_file(str(secret), scopes=scopes)
    creds = flow.run_local_server(
        port=port,
        prompt="consent",          # force a refresh token even on re-auth
        access_type="offline",
        authorization_prompt_message=(
            f"\nAuthorize the Gmail account you want stored as '{alias}'.\n"
            "Pick the right account in the browser window that just opened.\n"
        ),
        success_message=(
            f"Account '{alias}' authorized. You can close this tab and return to the terminal."
        ),
        open_browser=True,
    )
    persist_credentials(alias, creds)
    return creds


def whoami(creds: Credentials) -> str:
    """Resolve the authorized address so an alias can never silently point elsewhere."""
    from googleapiclient.discovery import build

    service = build("gmail", "v1", credentials=creds, cache_discovery=False)
    profile = service.users().getProfile(userId="me").execute()
    return profile.get("emailAddress", "")


def token_status(registry: Registry) -> list[dict]:
    rows = []
    for alias, account in sorted(registry.accounts().items()):
        path: Path = token_path(alias)
        row = {
            "account": alias,
            "email": account.email,
            "label": account.label,
            "readonly": account.readonly,
            "token_file": str(path),
            "authorized": path.exists(),
            "status": "ok",
        }
        if not path.exists():
            row["status"] = "missing token, run: gmail-multi-mcp add " + alias
        else:
            try:
                load_credentials(account)
            except AuthError as exc:
                row["status"] = str(exc)
        rows.append(row)
    return rows
