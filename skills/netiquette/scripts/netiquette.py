#!/usr/bin/env python3
"""Polite batch fetcher: fixed user-agent, per-host pacing shared across
processes, robots.txt compliance. One working folder is one crawl.

Usage:
    netiquette.py FOLDER [URL ...] [--url-file FILE] [--user-agent UA]
                  [--delay SEC] [--timers PATH] [--max-domains N]
                  [--take-over-lock]

stdout: one line per URL, "<status> <url> <base-path|-> <link-count|->".
"""

import argparse
import hashlib
import http.client
import json
import mimetypes
import io
import os
import re
import shutil
import sys
import threading
import time
import urllib.request
import zlib
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urljoin, urlsplit, urlunsplit

DEFAULT_USER_AGENT = "NetiquetteBot/1.0"
DEFAULT_DELAY = 5.0
DEFAULT_MAX_DOMAINS = 3
DEFAULT_TIMERS = Path.home() / ".cache" / "netiquette" / "timers.json"

REQUEST_TIMEOUT = 30
MAX_REDIRECTS = 5
TIMER_LOCK_WAIT = 10.0
TIMER_LOCK_STALE = 5.0
RETRY_AFTER_FALLBACK = 60.0
RETRY_AFTER_CAP = 3600.0

DEFAULT_PORTS = {"http": 80, "https": 443}
HTML_TYPES = {"text/html", "application/xhtml+xml"}
# Characters left unescaped when re-quoting paths and queries. "%" is kept so
# already-encoded URLs are not double-encoded.
URL_SAFE = "/%:@!$&'()*+,;=-._~?"


# --- URLs -------------------------------------------------------------------

def normalize_url(url):
    """Canonical form used as the state key, or None if not a usable http(s) URL."""
    try:
        parts = urlsplit(url.strip())
        port = parts.port
    except ValueError:
        return None
    scheme = parts.scheme.lower()
    host = parts.hostname
    if scheme not in DEFAULT_PORTS or not host:
        return None
    try:
        host = host.encode("idna").decode("ascii")
    except UnicodeError:
        return None
    if ":" in host:
        host = "[%s]" % host
    netloc = host if port in (None, DEFAULT_PORTS[scheme]) else "%s:%d" % (host, port)
    path = quote(parts.path, safe=URL_SAFE) or "/"
    query = quote(parts.query, safe=URL_SAFE)
    return urlunsplit((scheme, netloc, path, query, ""))


def url_hash(url):
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]


def host_of(url):
    """Pacing key. Ports are ignored on purpose: one server, one clock."""
    return urlsplit(url).hostname


def origin_of(url):
    parts = urlsplit(url)
    return "%s://%s" % (parts.scheme, parts.netloc)


# --- Files ------------------------------------------------------------------

def write_json_atomic(path, data):
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, sort_keys=True)
    os.replace(tmp, path)


def read_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


class LockHeld(Exception):
    pass


class FolderLock:
    """Guards state.json against two invocations on the same working folder."""

    def __init__(self, path):
        self.path = path

    def acquire(self, take_over):
        try:
            self._create()
        except FileExistsError:
            if not take_over:
                raise LockHeld(self._describe())
            os.remove(self.path)
            self._create()

    def release(self):
        try:
            os.remove(self.path)
        except FileNotFoundError:
            pass

    def _create(self):
        fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        with os.fdopen(fd, "w") as f:
            f.write("%d %f\n" % (os.getpid(), time.time()))

    def _describe(self):
        try:
            age = time.time() - os.path.getmtime(self.path)
            owner = self.path.read_text().split()[0]
        except (OSError, IndexError):
            return "working folder is locked (%s)" % self.path
        return ("working folder is locked by pid %s for %.0f s (%s); "
                "pass --take-over-lock if that process is dead" % (owner, age, self.path))


class TimerStore:
    """Per-host next-allowed request times, shared by every process of this user.

    The lock only covers read-modify-write of the file, never a download, so a
    lock older than TIMER_LOCK_STALE can only belong to a dead process.
    """

    def __init__(self, path):
        self.path = path
        self.lock_path = path.with_name(path.name + ".lock")
        path.parent.mkdir(parents=True, exist_ok=True)

    def reserve(self, host, delay):
        """Claims the next slot for host and returns its epoch time."""
        with self._locked():
            timers = self._read()
            now = time.time()
            slot = max(timers.get(host, 0.0), now)
            timers[host] = slot + delay
            self._write(timers, now)
        return slot

    def push_back(self, host, until):
        with self._locked():
            timers = self._read()
            timers[host] = max(timers.get(host, 0.0), until)
            self._write(timers, time.time())

    @contextmanager
    def _locked(self):
        deadline = time.monotonic() + TIMER_LOCK_WAIT
        while True:
            try:
                os.close(os.open(self.lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
                break
            except FileExistsError:
                pass
            try:
                if time.time() - os.path.getmtime(self.lock_path) > TIMER_LOCK_STALE:
                    os.remove(self.lock_path)
                    continue
            except FileNotFoundError:
                continue
            if time.monotonic() > deadline:
                raise TimeoutError("timer lock busy: %s" % self.lock_path)
            time.sleep(0.05)
        try:
            yield
        finally:
            try:
                os.remove(self.lock_path)
            except FileNotFoundError:
                pass

    def _read(self):
        try:
            return read_json(self.path)
        except ValueError:
            return {}

    def _write(self, timers, now):
        write_json_atomic(self.path, {h: t for h, t in timers.items() if t > now})


# --- robots.txt -------------------------------------------------------------

class Robots:
    """robots.txt rules for one user-agent, per RFC 9309, plus the non-standard
    Crawl-delay.

    urllib.robotparser is not used: it strips a trailing "?" from rule paths
    ("Disallow: /r?" becomes "/r" and blocks /robots.txt) and ignores the "*"
    and "$" wildcards, so it both over- and under-blocks.
    """

    def __init__(self, rules=(), crawl_delay=None):
        self.rules = list(rules)  # (pattern length, allow, compiled regex)
        self.crawl_delay = crawl_delay

    @classmethod
    def disallow_all(cls):
        return cls([cls._rule("/", False)])

    @classmethod
    def parse(cls, text, user_agent):
        token = user_agent.split("/")[0].strip().lower()
        groups = []  # (agents, rules, crawl delays)
        in_agent_lines = False
        for line in text.splitlines():
            key, _, value = line.split("#", 1)[0].partition(":")
            key, value = key.strip().lower(), value.strip()
            if key == "user-agent":
                if not in_agent_lines:
                    groups.append((set(), [], []))
                    in_agent_lines = True
                groups[-1][0].add(value.lower())
                continue
            if key not in ("allow", "disallow", "crawl-delay") or not groups:
                continue
            in_agent_lines = False
            if key == "crawl-delay":
                try:
                    groups[-1][2].append(float(value))
                except ValueError:
                    pass
            elif value:
                groups[-1][1].append(cls._rule(value, key == "allow"))

        matched = [g for g in groups if token in g[0]] or [g for g in groups if "*" in g[0]]
        rules = [rule for g in matched for rule in g[1]]
        delays = [delay for g in matched for delay in g[2]]
        return cls(rules, max(delays) if delays else None)

    @staticmethod
    def _rule(path, allow):
        pattern = quote(path, safe=URL_SAFE + "*$")
        anchored = pattern.endswith("$")
        regex = ".*".join(re.escape(part) for part in pattern.rstrip("$").split("*"))
        return len(pattern), allow, re.compile(regex + ("$" if anchored else ""))

    def can_fetch(self, url):
        parts = urlsplit(url)
        target = parts.path + ("?" + parts.query if parts.query else "")
        if target == "/robots.txt":
            return True
        # Longest matching pattern wins; on a tie, allow wins.
        best = (-1, True)
        for length, allow, regex in self.rules:
            if regex.match(target) and (length, allow) > best:
                best = (length, allow)
        return best[1]


# --- HTML -------------------------------------------------------------------

class PageParser(HTMLParser):
    """Rough HTML-to-Markdown conversion plus link extraction in one pass.

    Real-world HTML omits end tags freely, so every structure here tolerates
    missing or stray end tags rather than trusting nesting.
    """

    SKIP = {"script", "style", "noscript", "template", "svg"}
    BLOCKS = {"p", "div", "section", "article", "header", "footer", "nav", "main",
              "aside", "figure", "figcaption", "form", "dl", "dt", "dd", "address",
              "details", "summary"}
    HEADINGS = {"h1": 1, "h2": 2, "h3": 3, "h4": 4, "h5": 5, "h6": 6}

    def __init__(self, url):
        super().__init__(convert_charrefs=True)
        self.url = url
        self.base = url
        self.title = ""
        self.links = []
        self._seen = {url}
        self._base_set = False
        self._in_title = False
        self._skip = 0
        self._pre = 0
        self._lists = []    # [tag, item counter]
        self._marker_end = None
        self._anchors = []  # (href, buffer, start index)
        self._tables = []   # {"rows", "cells", "cell_open"}
        self._buffers = [("root", [])]

    @property
    def _out(self):
        return self._buffers[-1][1]

    def markdown(self):
        body = "".join("".join(buf) for _, buf in self._buffers)
        body = re.sub(r"[ \t]+\n", "\n", body)
        body = re.sub(r"\n{3,}", "\n\n", body).strip()
        title = re.sub(r"\s+", " ", self.title).strip()
        return "Title: %s\nURL: %s\n\n%s\n" % (title, self.url, body)

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self._skip += 1
            return
        if self._skip:
            return
        attrs = dict(attrs)
        if tag == "title":
            self._in_title = True
        elif tag == "base" and attrs.get("href") and not self._base_set:
            self.base = urljoin(self.url, attrs["href"])
            self._base_set = True
        elif tag in ("a", "area"):
            href = self._add_link(attrs.get("href"))
            if tag == "a":
                self._anchors.append((href, self._out, len(self._out)))
        elif tag in self.HEADINGS:
            self._block()
            self._out.append("#" * self.HEADINGS[tag] + " ")
        elif tag in self.BLOCKS:
            self._block()
        elif tag == "br":
            self._out.append("\n")
        elif tag == "hr":
            self._block()
            self._out.append("---")
            self._block()
        elif tag == "pre":
            self._block()
            self._out.append("```\n")
            self._pre += 1
        elif tag == "code" and not self._pre:
            self._out.append("`")
        elif tag in ("ul", "ol"):
            self._out.append("\n")
            self._lists.append([tag, 0])
        elif tag == "li":
            self._start_item()
        elif tag == "blockquote":
            self._block()
            self._buffers.append(("quote", []))
        elif tag == "img" and attrs.get("alt"):
            self._text("[image: %s]" % attrs["alt"])
        elif tag == "table":
            self._block()
            self._tables.append({"rows": 0, "cells": None, "cell_open": False})
        elif tag == "tr" and self._tables:
            self._close_row(self._tables[-1])
            self._tables[-1]["cells"] = []
        elif tag in ("td", "th") and self._tables:
            table = self._tables[-1]
            self._close_cell(table)
            if table["cells"] is None:
                table["cells"] = []
            table["cell_open"] = True
            self._buffers.append(("cell", []))

    def handle_endtag(self, tag):
        if tag in self.SKIP:
            self._skip = max(0, self._skip - 1)
            return
        if self._skip:
            return
        if tag == "title":
            self._in_title = False
        elif tag == "a":
            self._close_anchor()
        elif tag in self.HEADINGS or tag in self.BLOCKS:
            self._block()
        elif tag == "pre" and self._pre:
            self._pre -= 1
            self._out.append("\n```")
            self._block()
        elif tag == "code" and not self._pre:
            self._out.append("`")
        elif tag in ("ul", "ol") and self._lists:
            self._lists.pop()
            self._out.append("\n" if self._lists else "\n\n")
        elif tag == "blockquote" and self._has_buffer("quote"):
            quoted = self._pop_buffer("quote").strip()
            self._out.append("\n".join("> " + line for line in quoted.split("\n")))
            self._block()
        elif tag in ("td", "th") and self._tables:
            self._close_cell(self._tables[-1])
        elif tag == "tr" and self._tables:
            self._close_row(self._tables[-1])
        elif tag == "table" and self._tables:
            self._close_row(self._tables.pop())
            self._block()

    def handle_data(self, data):
        if self._skip:
            return
        if self._in_title:
            self.title += data
        elif self._pre:
            self._out.append(data)
        else:
            self._text(data)

    def _text(self, data):
        text = re.sub(r"\s+", " ", data)
        if self._last_char() in ("", "\n", " "):
            text = text.lstrip()
        if text:
            self._out.append(text)

    def _last_char(self):
        for chunk in reversed(self._out):
            if chunk:
                return chunk[-1]
        return ""

    def _block(self):
        # A block directly inside <li> must not separate the marker from its text.
        if self._marker_end == (id(self._out), len(self._out)):
            return
        self._out.append("\n\n")

    def _start_item(self):
        self._out.append("\n")
        marker = "-"
        if self._lists and self._lists[-1][0] == "ol":
            self._lists[-1][1] += 1
            marker = "%d." % self._lists[-1][1]
        indent = "  " * max(len(self._lists) - 1, 0)
        self._out.append(indent + marker + " ")
        self._marker_end = (id(self._out), len(self._out))

    def _add_link(self, href):
        if not href:
            return None
        try:
            link = normalize_url(urljoin(self.base, href.strip()))
        except ValueError:
            return None
        if link and link not in self._seen:
            self._seen.add(link)
            self.links.append(link)
        return link

    def _close_anchor(self):
        if not self._anchors:
            return
        href, buf, start = self._anchors.pop()
        if buf is not self._out or self._pre or not href or href == self.url:
            return
        text = re.sub(r"\s+", " ", "".join(buf[start:])).strip()
        if text:
            buf[start:] = ["[%s](%s)" % (text, href)]

    def _has_buffer(self, kind):
        return any(k == kind for k, _ in self._buffers[1:])

    def _pop_buffer(self, kind):
        """Pops up to and including the innermost buffer of kind, merging any
        unclosed inner buffers into it."""
        parts = []
        while len(self._buffers) > 1:
            k, buf = self._buffers.pop()
            parts.insert(0, "".join(buf))
            if k == kind:
                break
        return "".join(parts)

    def _close_cell(self, table):
        if not table["cell_open"] or not self._has_buffer("cell"):
            return
        text = re.sub(r"\s+", " ", self._pop_buffer("cell")).strip()
        table["cells"].append(text.replace("|", "\\|"))
        table["cell_open"] = False

    def _close_row(self, table):
        self._close_cell(table)
        cells = table["cells"]
        table["cells"] = None
        if not cells:
            return
        self._out.append("\n| " + " | ".join(cells) + " |")
        if table["rows"] == 0:
            self._out.append("\n|" + " --- |" * len(cells))
        table["rows"] += 1


def decode_html(raw, header_charset):
    match = re.search(rb"""<meta[^>]+charset=["']?([\w.:-]+)""", raw[:4096], re.I)
    sniffed = match.group(1).decode("ascii") if match else None
    for encoding in (header_charset, sniffed):
        if encoding:
            try:
                return raw.decode(encoding, errors="replace")
            except LookupError:
                pass
    return raw.decode("utf-8", errors="replace")


# --- Crawl ------------------------------------------------------------------

def retry_after_seconds(value):
    if not value:
        return RETRY_AFTER_FALLBACK
    value = value.strip()
    if value.isdigit():
        seconds = float(value)
    else:
        try:
            seconds = parsedate_to_datetime(value).timestamp() - time.time()
        except (TypeError, ValueError):
            return RETRY_AFTER_FALLBACK
    return min(max(seconds, 0.0), RETRY_AFTER_CAP)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Redirects surface as HTTPError so each hop gets its own slot and robots check."""

    def redirect_request(self, *args, **kwargs):
        return None


class Result:
    def __init__(self, status, record=None, stop_host=False):
        self.status = status
        self.record = record
        self.stop_host = stop_host


class Crawl:
    def __init__(self, folder, user_agent, delay, timers):
        self.folder = folder
        self.user_agent = user_agent
        self.delay = delay
        self.timers = timers
        self.opener = urllib.request.build_opener(_NoRedirect)
        self.state_path = folder / "state.json"
        self.state = read_json(self.state_path)
        self.state_lock = threading.Lock()
        self.print_lock = threading.Lock()
        # Keyed by origin. Each origin belongs to exactly one host worker, so
        # no lock is needed. None means robots.txt was unavailable.
        self.robots = {}

    def run(self, urls, max_domains):
        by_host = {}
        for url in urls:
            normalized = normalize_url(url)
            if normalized is None:
                self._emit("invalid", url)
                continue
            queue = by_host.setdefault(host_of(normalized), [])
            if normalized not in queue:
                queue.append(normalized)
        with ThreadPoolExecutor(max_workers=max_domains) as pool:
            futures = [pool.submit(self._crawl_host, queue) for queue in by_host.values()]
        for future in futures:
            future.result()

    def _crawl_host(self, urls):
        for index, url in enumerate(urls):
            with self.state_lock:
                known = self.state.get(url)
            if known and not known.get("retry"):
                self._emit_record("visited", url, known)
                continue
            result = self._fetch(url)
            if result.record is not None:
                self._store(url, result.record)
                self._emit_record(result.status, url, result.record)
            else:
                self._emit(result.status, url)
            if result.stop_host:
                for rest in urls[index + 1:]:
                    self._emit("deferred", rest)
                return

    def _fetch(self, url):
        current = url
        try:
            for _ in range(MAX_REDIRECTS + 1):
                robots = self._robots_for(current)
                if robots is None:
                    return Result("robots-unavailable")
                if not robots.can_fetch(current):
                    return Result("robots", self._record("robots", current))
                response = self._open(current, max(self.delay, robots.crawl_delay or 0.0))
                with response:
                    code = response.getcode()
                    location = response.headers.get("Location")
                    if 300 <= code < 400 and location:
                        target = normalize_url(urljoin(current, location))
                        if target is None:
                            return Result(code, self._record(code, current, error="bad Location: %s" % location))
                        if host_of(target) != host_of(current):
                            return Result(code, self._cross_host_redirect(url, code, target))
                        current = target
                        continue
                    return self._handle_response(url, current, code, response)
            return Result("error", self._record("error", current, error="too many redirects"))
        except UnsupportedEncoding as exc:
            return Result("error", self._record("error", current, error=str(exc)))
        except (URLError, OSError, http.client.HTTPException, zlib.error) as exc:
            return Result("error", self._record("error", current, error=describe(exc), retry=True))

    def _handle_response(self, url, final_url, code, response):
        content_type = response.headers.get("Content-Type") or "application/octet-stream"
        if code in (429, 503):
            wait = retry_after_seconds(response.headers.get("Retry-After"))
            self.timers.push_back(host_of(final_url), time.time() + wait)
            error = "retry after %.0f s" % wait
            return Result(code, self._record(code, final_url, content_type, error=error, retry=True), stop_host=True)
        if not 200 <= code < 300:
            return Result(code, self._record(code, final_url, content_type, retry=code >= 500))

        base = url_hash(url)
        mime = content_type.split(";")[0].strip().lower()
        is_html = mime in HTML_TYPES
        extension = ".html" if is_html else (mimetypes.guess_extension(mime) or ".bin")
        body_path = self.folder / (base + extension)
        with open(body_path, "wb") as f:
            copy_body(response, f)
        files = {"body": body_path.name}
        link_count = None
        if is_html:
            page = PageParser(final_url)
            page.feed(decode_html(body_path.read_bytes(), response.headers.get_content_charset()))
            page.close()
            files["md"] = base + ".md"
            files["links"] = base + ".links.txt"
            write_text(self.folder / files["md"], page.markdown())
            write_text(self.folder / files["links"], "".join(link + "\n" for link in page.links))
            link_count = len(page.links)
        return Result(code, self._record(code, final_url, content_type, files, link_count))

    def _cross_host_redirect(self, url, code, target):
        """Hands the target back to the caller instead of following it, so the
        target host is only ever contacted by its own worker."""
        links_name = url_hash(url) + ".links.txt"
        write_text(self.folder / links_name, target + "\n")
        return self._record(code, target, files={"links": links_name}, link_count=1)

    def _robots_for(self, url):
        origin = origin_of(url)
        if origin not in self.robots:
            self.robots[origin] = self._load_robots(origin)
        return self.robots[origin]

    def _load_robots(self, origin):
        current = origin + "/robots.txt"
        try:
            for _ in range(MAX_REDIRECTS + 1):
                with self._open(current, self.delay) as response:
                    code = response.getcode()
                    location = response.headers.get("Location")
                    if 300 <= code < 400 and location:
                        target = normalize_url(urljoin(current, location))
                        # Off-host robots redirects are typically "example.com ->
                        # www.example.com"; the pages redirect the same way and
                        # never get fetched from this origin.
                        if target is None or host_of(target) != host_of(current):
                            return Robots()
                        current = target
                        continue
                    if code in (429, 503):
                        wait = retry_after_seconds(response.headers.get("Retry-After"))
                        self.timers.push_back(host_of(current), time.time() + wait)
                        return None
                    if code in (401, 403):
                        return Robots.disallow_all()
                    if 400 <= code < 500:
                        return Robots()
                    if not 200 <= code < 300:
                        return None
                    body = io.BytesIO()
                    copy_body(response, body)
                    text = body.getvalue().decode("utf-8", errors="replace")
                    robots = Robots.parse(text, self.user_agent)
                    if robots.crawl_delay and robots.crawl_delay > self.delay:
                        # The robots.txt request itself was spaced by --delay only.
                        self.timers.push_back(host_of(current), time.time() + robots.crawl_delay)
                    return robots
        except (URLError, OSError, http.client.HTTPException, zlib.error, UnsupportedEncoding):
            return None
        return None

    def _open(self, url, delay):
        """Waits for this host's next slot, then sends one request.
        HTTP error statuses come back as the response, not as an exception."""
        slot = self.timers.reserve(host_of(url), delay)
        time.sleep(max(0.0, slot - time.time()))
        request = urllib.request.Request(url, headers={
            "User-Agent": self.user_agent,
            "Accept-Encoding": "gzip, deflate",
        })
        try:
            return self.opener.open(request, timeout=REQUEST_TIMEOUT)
        except HTTPError as exc:
            return exc

    def _record(self, status, final_url, content_type=None, files=None,
                link_count=None, error=None, retry=False):
        return {
            "status": status,
            "final_url": final_url,
            "content_type": content_type,
            "files": files or {},
            "link_count": link_count,
            "error": error,
            "retry": retry,
            "fetched_at": time.time(),
        }

    def _store(self, url, record):
        with self.state_lock:
            self.state[url] = record
            final_url = record["final_url"]
            same_host = host_of(final_url) == host_of(url)
            if final_url != url and same_host and not record["retry"] and final_url not in self.state:
                self.state[final_url] = record
            write_json_atomic(self.state_path, self.state)

    def _emit_record(self, status, url, record):
        body = record["files"].get("body") or record["files"].get("links")
        base = str(self.folder / body.split(".")[0]) if body else "-"
        links = "-" if record["link_count"] is None else record["link_count"]
        self._emit(status, url, base, links)

    def _emit(self, status, url, base="-", links="-"):
        with self.print_lock:
            print("%s %s %s %s" % (status, url, base, links), flush=True)


class UnsupportedEncoding(Exception):
    pass


def copy_body(response, out):
    """Streams the body to out, undoing gzip or deflate content encoding.
    Some servers compress even when the request did not ask for it."""
    encoding = (response.headers.get("Content-Encoding") or "identity").strip().lower()
    if encoding == "identity":
        shutil.copyfileobj(response, out)
        return
    if encoding not in ("gzip", "x-gzip", "deflate"):
        raise UnsupportedEncoding("unsupported Content-Encoding: %s" % encoding)
    # wbits 32 + MAX_WBITS auto-detects gzip and zlib headers.
    decompressor = zlib.decompressobj(32 + zlib.MAX_WBITS)
    while True:
        chunk = response.read(65536)
        if not chunk:
            break
        out.write(decompressor.decompress(chunk))
    out.write(decompressor.flush())


def describe(exc):
    return "%s: %s" % (type(exc).__name__, exc)


def write_text(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


# --- CLI --------------------------------------------------------------------

def parse_args(argv):
    parser = argparse.ArgumentParser(description="Fetch web pages politely into a working folder.")
    parser.add_argument("folder", type=Path, help="working folder, one per crawl (created if missing)")
    parser.add_argument("urls", nargs="*", help="URLs to fetch")
    parser.add_argument("--url-file", type=Path, help="file with one URL per line")
    parser.add_argument("--user-agent", default=DEFAULT_USER_AGENT)
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY,
                        help="minimum seconds between requests to one host (default %(default)s)")
    parser.add_argument("--timers", type=Path, default=DEFAULT_TIMERS,
                        help="shared per-host timer file (default %(default)s)")
    parser.add_argument("--max-domains", type=int, default=DEFAULT_MAX_DOMAINS,
                        help="hosts fetched in parallel (default %(default)s)")
    parser.add_argument("--take-over-lock", action="store_true",
                        help="remove a stale working-folder lock left by a dead process")
    args = parser.parse_args(argv)
    if args.delay < 0:
        parser.error("--delay must not be negative")
    if args.max_domains < 1:
        parser.error("--max-domains must be at least 1")
    return args


def read_url_file(path):
    with open(path, encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


def main(argv=None):
    args = parse_args(argv)
    urls = list(args.urls)
    if args.url_file:
        urls += read_url_file(args.url_file)
    if not urls:
        print("no URLs given", file=sys.stderr)
        return 1

    args.folder.mkdir(parents=True, exist_ok=True)
    lock = FolderLock(args.folder / ".lock")
    try:
        lock.acquire(args.take_over_lock)
    except LockHeld as exc:
        print(exc, file=sys.stderr)
        return 2
    try:
        crawl = Crawl(args.folder.resolve(), args.user_agent, args.delay, TimerStore(args.timers))
        crawl.run(urls, args.max_domains)
    finally:
        lock.release()
    return 0


if __name__ == "__main__":
    sys.exit(main())
