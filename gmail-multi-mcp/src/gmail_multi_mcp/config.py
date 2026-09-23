"""Account registry and on-disk layout.

Everything lives under GMAIL_MULTI_MCP_HOME (default ~/.gmail-multi-mcp):

    accounts.json              registry of aliases, emails, scopes, default
    client_secret.json         OAuth client downloaded from Google Cloud
    tokens/<alias>.json        one refresh token per account, mode 0600
"""

from __future__ import annotations

import json
import os
import stat
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
]

READONLY_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
]


def home() -> Path:
    raw = os.environ.get("GMAIL_MULTI_MCP_HOME", "~/.gmail-multi-mcp")
    return Path(raw).expanduser()


def tokens_dir() -> Path:
    return home() / "tokens"


def registry_path() -> Path:
    return home() / "accounts.json"


def token_path(alias: str) -> Path:
    return tokens_dir() / f"{alias}.json"


def client_secret_path() -> Path:
    override = os.environ.get("GMAIL_MULTI_MCP_CLIENT_SECRET")
    if override:
        return Path(override).expanduser()
    return home() / "client_secret.json"


def ensure_home() -> None:
    home().mkdir(parents=True, exist_ok=True)
    tokens_dir().mkdir(parents=True, exist_ok=True)
    os.chmod(home(), stat.S_IRWXU)
    os.chmod(tokens_dir(), stat.S_IRWXU)


def write_private_json(path: Path, payload: dict) -> None:
    """Write JSON atomically with owner-only permissions."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, sort_keys=True)
        os.chmod(tmp, stat.S_IRUSR | stat.S_IWUSR)
        os.replace(tmp, path)
    except Exception:
        Path(tmp).unlink(missing_ok=True)
        raise


@dataclass
class Account:
    alias: str
    email: str
    scopes: list[str] = field(default_factory=lambda: list(DEFAULT_SCOPES))
    label: str = ""
    added_at: str = ""

    def to_dict(self) -> dict:
        return {
            "email": self.email,
            "scopes": self.scopes,
            "label": self.label,
            "added_at": self.added_at,
        }

    @property
    def readonly(self) -> bool:
        return not any(
            s.endswith("gmail.modify")
            or s.endswith("gmail.compose")
            or s.endswith("gmail.send")
            or s == "https://mail.google.com/"
            for s in self.scopes
        )


class Registry:
    """accounts.json, loaded fresh on every read so the CLI and the server stay in sync."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or registry_path()

    def _raw(self) -> dict:
        if not self.path.exists():
            return {"accounts": {}, "default": None}
        with self.path.open(encoding="utf-8") as fh:
            data = json.load(fh)
        data.setdefault("accounts", {})
        data.setdefault("default", None)
        return data

    def accounts(self) -> dict[str, Account]:
        raw = self._raw()
        out: dict[str, Account] = {}
        for alias, entry in raw["accounts"].items():
            out[alias] = Account(
                alias=alias,
                email=entry.get("email", ""),
                scopes=entry.get("scopes", list(DEFAULT_SCOPES)),
                label=entry.get("label", ""),
                added_at=entry.get("added_at", ""),
            )
        return out

    def get(self, alias: str) -> Account | None:
        return self.accounts().get(alias)

    def default_alias(self) -> str | None:
        raw = self._raw()
        explicit = os.environ.get("GMAIL_MULTI_MCP_DEFAULT")
        if explicit and explicit in raw["accounts"]:
            return explicit
        if raw["default"] and raw["default"] in raw["accounts"]:
            return raw["default"]
        aliases = sorted(raw["accounts"])
        return aliases[0] if aliases else None

    def resolve(self, alias: str | None) -> Account:
        """Map a caller-supplied alias (or None) onto a real account.

        Accepts the alias itself or the full email address, so the model can say
        either "work" or "amit@example.com".
        """
        accounts = self.accounts()
        if not accounts:
            raise LookupError(
                "No Gmail accounts are registered. Run: gmail-multi-mcp add <alias>"
            )
        if alias is None or alias == "":
            resolved = self.default_alias()
            if resolved is None:
                raise LookupError("No default account is set.")
            return accounts[resolved]
        if alias in accounts:
            return accounts[alias]
        by_email = {a.email.lower(): a for a in accounts.values() if a.email}
        if alias.lower() in by_email:
            return by_email[alias.lower()]
        known = ", ".join(sorted(accounts)) or "(none)"
        raise LookupError(f"Unknown account '{alias}'. Registered accounts: {known}")

    def upsert(self, account: Account, make_default: bool = False) -> None:
        raw = self._raw()
        raw["accounts"][account.alias] = account.to_dict()
        if make_default or not raw.get("default"):
            raw["default"] = account.alias
        write_private_json(self.path, raw)

    def remove(self, alias: str) -> bool:
        raw = self._raw()
        if alias not in raw["accounts"]:
            return False
        del raw["accounts"][alias]
        if raw.get("default") == alias:
            remaining = sorted(raw["accounts"])
            raw["default"] = remaining[0] if remaining else None
        write_private_json(self.path, raw)
        token_path(alias).unlink(missing_ok=True)
        return True

    def set_default(self, alias: str) -> None:
        raw = self._raw()
        if alias not in raw["accounts"]:
            raise LookupError(f"Unknown account '{alias}'")
        raw["default"] = alias
        write_private_json(self.path, raw)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
