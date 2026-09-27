---
name: netiquette
description: Polite web fetching for crawls and multi-page information gathering. It uses a fixed user-agent, per-site rate limits shared by all sessions, and robots.txt compliance. Pages are saved as raw HTML, Markdown and link lists in a working folder. Use this skill whenever the task means fetching more than one or two pages from the web. That includes crawling or scraping a site, following links, reading through documentation or a blog archive, collecting facts across a site's pages, mirroring pages for later analysis, or any research that walks from page to page. Use it even if the user just says "look through the site" or "check all the pages under /docs". WebFetch is still fine for a single quick lookup of one page.
---

# Netiquette

The WebFetch tool cannot set a user-agent or space out requests, so a crawl run through it can hit a site in quick succession. `scripts/netiquette.py` fetches pages the way a well-behaved crawler does:

- It identifies itself as `NetiquetteBot/1.0`.
- It follows robots.txt, including `Crawl-delay`.
- It waits at least 5 seconds between requests to the same host. The timers are shared by every crawl and every Claude session on this machine, so a site sees one clock.

The script only fetches. You decide what to fetch next.

## Running it

```
python3 <skill-dir>/scripts/netiquette.py <working-folder> URL [URL ...]
python3 <skill-dir>/scripts/netiquette.py <working-folder> --url-file urls.txt
```

`<skill-dir>` is this skill's base directory. On Windows, use `python` instead of `python3`.

Optional flags:

- `--delay SEC`: minimum spacing per host. The default is 5, and robots.txt `Crawl-delay` raises it.
- `--max-domains N`: number of hosts fetched in parallel. The default is 3.
- `--user-agent S`
- `--timers PATH`
- `--take-over-lock`

Each call takes a batch of URLs, runs until they are done and exits. Calls take time because of the spacing: a batch of 10 URLs on one host takes about 50 seconds. Give the Bash call a long enough timeout, or split large batches. Batches that span several hosts run in parallel and finish faster.

## Output

stdout has one line per URL:

```
<status> <url> <base-path> <link-count>
```

For example:

```
200 https://docs.example.org/guide/ /tmp/crawl/3f9a1c0d2b7e4a55 42
visited https://docs.example.org/ /tmp/crawl/0f115db062b7c0dd 17
robots https://docs.example.org/private/x - -
```

| Status | Meaning | What to do |
|---|---|---|
| `200` (or another 2xx) | Fetched. The files are at `<base-path>.*`. | Read them as needed. |
| `visited` | Already fetched earlier in this crawl, so no request was made. The files from the earlier fetch are listed. | Nothing. |
| `301`/`302`/… with 1 link | Redirect to another host. The target is in `<base-path>.links.txt`. | Submit the target if you still want it. |
| `404` and other 4xx | Recorded. Not retried. | Move on. |
| `429`, `503`, other 5xx, `error` | Failed and marked for retry. For 429 and 503 the host's timer has been pushed back. | Resubmit in a later call if it matters. |
| `deferred` | Not attempted, because the host answered 429 or 503 earlier in this call. | Resubmit in a later call. |
| `robots` | Disallowed by robots.txt. Recorded. | Don't try to work around it. |
| `robots-unavailable` | The site's robots.txt could not be read, so the host was left alone for this call. | Retry later, or tell the user. |
| `invalid` | Not an http(s) URL. | Fix or drop it. |

Resubmitting is cheap because the script skips everything already done. Retrying 429 or 503 right away doesn't work: the shared timer makes the call wait out the site's `Retry-After`, up to an hour.

## Working folder

One folder is one crawl. Choose it at the start and pass the same path on every call of that crawl. Use the session's scratchpad directory unless the user wants the pages kept somewhere specific. `state.json` in the folder records every URL already handled, and that record is how repeat URLs are skipped. A new folder mid-crawl means refetching pages the site has already served.

Never run two calls on the same folder at the same time, not even as parallel Bash calls. The folder lock rejects the second call with a message giving the lock's age. To fetch more in parallel, put more URLs from different hosts in one call. Parallel calls on different folders are fine, because the shared timers keep each host's spacing.

If a call reports a locked folder and you are sure no other call is running, for example after a crash, rerun it with `--take-over-lock`.

## Reading the results

For each fetched HTML page:

- `<base-path>.md`: a rough Markdown conversion. It keeps the title, headings, paragraphs, lists, links, code blocks and tables. Read this first. It is much shorter than the HTML.
- `<base-path>.html`: the raw page and the source of truth. Use it when the Markdown looks mangled or garbled, or when you need something the conversion drops, such as where an element sits on the page, attributes, forms or script-embedded data.
- `<base-path>.links.txt`: every link on the page, absolute, without fragments, one per line, with duplicates removed.

Non-HTML responses (PDF, JSON, images, …) are saved as `<base-path>.<ext>` with no Markdown or link file.

Only open the files you need. The stdout lines are the index.

## Choosing what to fetch next

Pick follow-up URLs from `.links.txt` rather than from the raw HTML. Its URLs are already absolute and normalized, so they match the keys the script uses to skip visited pages. Use `grep` on the links files to narrow by path prefix or keyword. Fetch only what the task needs: stay within the site section the user cares about, and don't expand to every link on the page.
