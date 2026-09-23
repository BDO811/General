"""Thin Gmail API wrapper, one client instance per account alias."""

from __future__ import annotations

import base64
import threading
from email.message import EmailMessage
from typing import Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .auth import load_credentials
from .config import Account

MAX_BODY_CHARS = 20000


class GmailError(RuntimeError):
    pass


class ClientPool:
    """Caches one googleapiclient service per alias.

    The Gmail service object is not documented as thread safe, so each alias gets
    its own lock and fan-out work runs one request per alias at a time.
    """

    def __init__(self) -> None:
        self._services: dict[str, Any] = {}
        self._locks: dict[str, threading.Lock] = {}
        self._guard = threading.Lock()

    def _lock_for(self, alias: str) -> threading.Lock:
        with self._guard:
            return self._locks.setdefault(alias, threading.Lock())

    def service(self, account: Account):
        with self._lock_for(account.alias):
            svc = self._services.get(account.alias)
            if svc is None:
                creds = load_credentials(account)
                svc = build("gmail", "v1", credentials=creds, cache_discovery=False)
                self._services[account.alias] = svc
            return svc

    def invalidate(self, alias: str) -> None:
        with self._guard:
            self._services.pop(alias, None)


POOL = ClientPool()


def _call(account: Account, request_factory):
    """Run one Gmail request, retrying once after dropping a stale cached client."""
    for attempt in (1, 2):
        svc = POOL.service(account)
        try:
            return request_factory(svc).execute()
        except HttpError as exc:
            if exc.resp.status in (401, 403) and attempt == 1:
                POOL.invalidate(account.alias)
                continue
            raise GmailError(_http_message(account, exc)) from exc
    raise GmailError(f"Gmail request failed for account '{account.alias}'")


def _http_message(account: Account, exc: HttpError) -> str:
    status = exc.resp.status
    detail = getattr(exc, "reason", "") or str(exc)
    if status == 401:
        return (
            f"Gmail rejected the credentials for '{account.alias}'. "
            f"Re-authorize: gmail-multi-mcp add {account.alias} --force"
        )
    if status == 403 and "insufficient" in detail.lower():
        return (
            f"Account '{account.alias}' is authorized with scopes that do not allow this "
            f"operation ({', '.join(account.scopes)}). Re-authorize with write scopes."
        )
    if status == 429:
        return f"Gmail rate limited account '{account.alias}'. Retry shortly."
    return f"Gmail API error {status} on account '{account.alias}': {detail}"


# --------------------------------------------------------------------------- read


def search(account: Account, query: str, max_results: int = 20,
           include_spam_trash: bool = False) -> list[dict]:
    listing = _call(
        account,
        lambda svc: svc.users().messages().list(
            userId="me",
            q=query or None,
            maxResults=max(1, min(max_results, 100)),
            includeSpamTrash=include_spam_trash,
        ),
    )
    out = []
    for stub in listing.get("messages", []):
        meta = _call(
            account,
            lambda svc, mid=stub["id"]: svc.users().messages().get(
                userId="me",
                id=mid,
                format="metadata",
                metadataHeaders=["From", "To", "Cc", "Subject", "Date"],
            ),
        )
        out.append(summarize(account.alias, meta))
    return out


def get_message(account: Account, message_id: str, include_body: bool = True) -> dict:
    fmt = "full" if include_body else "metadata"
    msg = _call(
        account,
        lambda svc: svc.users().messages().get(userId="me", id=message_id, format=fmt),
    )
    record = summarize(account.alias, msg)
    if include_body:
        record["body"] = extract_body(msg.get("payload", {}))
        record["attachments"] = list_attachments(msg.get("payload", {}))
    return record


def get_thread(account: Account, thread_id: str, include_body: bool = True) -> dict:
    thread = _call(
        account,
        lambda svc: svc.users().threads().get(
            userId="me", id=thread_id, format="full" if include_body else "metadata"
        ),
    )
    messages = []
    for msg in thread.get("messages", []):
        record = summarize(account.alias, msg)
        if include_body:
            record["body"] = extract_body(msg.get("payload", {}))
        messages.append(record)
    return {"account": account.alias, "thread_id": thread_id, "messages": messages}


def list_drafts(account: Account, max_results: int = 50,
                query: str | None = None) -> list[dict]:
    """Enumerate drafts with their draft ids, which send_draft needs.

    A message search with in:drafts returns message ids, not draft ids, so this
    has to go through the drafts endpoint.
    """
    listing = _call(
        account,
        lambda svc: svc.users().drafts().list(
            userId="me", maxResults=max(1, min(max_results, 100)), q=query or None
        ),
    )
    out = []
    for stub in listing.get("drafts", []):
        detail = _call(
            account,
            lambda svc, did=stub["id"]: svc.users().drafts().get(
                userId="me", id=did, format="metadata"
            ),
        )
        record = summarize(account.alias, detail.get("message", {}))
        record["draft_id"] = detail.get("id")
        out.append(record)
    return out


def list_labels(account: Account) -> list[dict]:
    data = _call(account, lambda svc: svc.users().labels().list(userId="me"))
    return [
        {"id": l["id"], "name": l["name"], "type": l.get("type", "")}
        for l in data.get("labels", [])
    ]


def profile(account: Account) -> dict:
    data = _call(account, lambda svc: svc.users().getProfile(userId="me"))
    return {
        "account": account.alias,
        "email": data.get("emailAddress", ""),
        "messages_total": data.get("messagesTotal"),
        "threads_total": data.get("threadsTotal"),
    }


# -------------------------------------------------------------------------- write


def _build_mime(sender: str, to: list[str], subject: str, body: str,
                cc: list[str] | None = None, bcc: list[str] | None = None,
                reply_to_message_id: str | None = None,
                references: str | None = None, html: bool = False) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = ", ".join(to)
    if cc:
        msg["Cc"] = ", ".join(cc)
    if bcc:
        msg["Bcc"] = ", ".join(bcc)
    msg["Subject"] = subject
    if reply_to_message_id:
        msg["In-Reply-To"] = reply_to_message_id
        msg["References"] = references or reply_to_message_id
    if html:
        msg.set_content("This message requires an HTML capable client.")
        msg.add_alternative(body, subtype="html")
    else:
        msg.set_content(body)
    return msg


def _encoded(msg: EmailMessage) -> str:
    return base64.urlsafe_b64encode(msg.as_bytes()).decode()


def create_draft(account: Account, to: list[str], subject: str, body: str,
                 cc: list[str] | None = None, bcc: list[str] | None = None,
                 thread_id: str | None = None, html: bool = False) -> dict:
    _assert_writable(account)
    sender = profile(account)["email"]
    mime = _build_mime(sender, to, subject, body, cc, bcc, html=html)
    payload: dict[str, Any] = {"message": {"raw": _encoded(mime)}}
    if thread_id:
        payload["message"]["threadId"] = thread_id
    draft = _call(
        account, lambda svc: svc.users().drafts().create(userId="me", body=payload)
    )
    return {
        "account": account.alias,
        "draft_id": draft.get("id"),
        "message_id": draft.get("message", {}).get("id"),
        "thread_id": draft.get("message", {}).get("threadId"),
        "from": sender,
        "to": to,
        "subject": subject,
    }


def send_message(account: Account, to: list[str], subject: str, body: str,
                 cc: list[str] | None = None, bcc: list[str] | None = None,
                 thread_id: str | None = None, html: bool = False) -> dict:
    _assert_writable(account)
    sender = profile(account)["email"]
    mime = _build_mime(sender, to, subject, body, cc, bcc, html=html)
    payload: dict[str, Any] = {"raw": _encoded(mime)}
    if thread_id:
        payload["threadId"] = thread_id
    sent = _call(
        account, lambda svc: svc.users().messages().send(userId="me", body=payload)
    )
    return {
        "account": account.alias,
        "message_id": sent.get("id"),
        "thread_id": sent.get("threadId"),
        "from": sender,
        "to": to,
        "subject": subject,
    }


def send_draft(account: Account, draft_id: str) -> dict:
    _assert_writable(account)
    sent = _call(
        account,
        lambda svc: svc.users().drafts().send(userId="me", body={"id": draft_id}),
    )
    return {
        "account": account.alias,
        "draft_id": draft_id,
        "message_id": sent.get("id"),
        "thread_id": sent.get("threadId"),
    }


def modify_labels(account: Account, message_id: str, add: list[str] | None = None,
                  remove: list[str] | None = None) -> dict:
    _assert_writable(account)
    body = {"addLabelIds": add or [], "removeLabelIds": remove or []}
    msg = _call(
        account,
        lambda svc: svc.users().messages().modify(userId="me", id=message_id, body=body),
    )
    return {
        "account": account.alias,
        "message_id": msg.get("id"),
        "label_ids": msg.get("labelIds", []),
    }


def _assert_writable(account: Account) -> None:
    if account.readonly:
        raise GmailError(
            f"Account '{account.alias}' is authorized read only. "
            f"Re-authorize with write scopes: gmail-multi-mcp add {account.alias} --force"
        )


# ------------------------------------------------------------------------ parsing


def headers_of(msg: dict) -> dict[str, str]:
    payload = msg.get("payload", {}) or {}
    return {h["name"].lower(): h["value"] for h in payload.get("headers", [])}


def summarize(alias: str, msg: dict) -> dict:
    hdrs = headers_of(msg)
    return {
        "account": alias,
        "message_id": msg.get("id"),
        "thread_id": msg.get("threadId"),
        "from": hdrs.get("from", ""),
        "to": hdrs.get("to", ""),
        "cc": hdrs.get("cc", ""),
        "subject": hdrs.get("subject", ""),
        "date": hdrs.get("date", ""),
        "snippet": msg.get("snippet", ""),
        "label_ids": msg.get("labelIds", []),
        "unread": "UNREAD" in msg.get("labelIds", []),
    }


def _decode(data: str) -> str:
    padded = data + "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(padded).decode("utf-8", errors="replace")


def extract_body(payload: dict) -> str:
    """Prefer text/plain, fall back to the first text/html part, then truncate."""
    plain, html = _walk_body(payload)
    text = plain or html or ""
    if len(text) > MAX_BODY_CHARS:
        text = text[:MAX_BODY_CHARS] + f"\n\n[truncated at {MAX_BODY_CHARS} characters]"
    return text


def _walk_body(part: dict) -> tuple[str, str]:
    mime = part.get("mimeType", "")
    data = part.get("body", {}).get("data")
    if data and mime == "text/plain":
        return _decode(data), ""
    if data and mime == "text/html":
        return "", _decode(data)
    plain_acc, html_acc = "", ""
    for child in part.get("parts", []) or []:
        p, h = _walk_body(child)
        plain_acc = plain_acc or p
        html_acc = html_acc or h
        if plain_acc:
            break
    return plain_acc, html_acc


def list_attachments(payload: dict) -> list[dict]:
    found: list[dict] = []

    def walk(part: dict) -> None:
        filename = part.get("filename") or ""
        body = part.get("body", {}) or {}
        if filename and body.get("attachmentId"):
            found.append({
                "filename": filename,
                "mime_type": part.get("mimeType", ""),
                "size_bytes": body.get("size", 0),
                "attachment_id": body["attachmentId"],
            })
        for child in part.get("parts", []) or []:
            walk(child)

    walk(payload)
    return found
