# -*- coding: utf-8 -*-
"""Pull topical imagery for a document backdrop.

    python3 fetch_imagery.py <slug> ["query"]
    python3 fetch_imagery.py --all

Sources, in order:

1. Pixabay, when `PIXABAY_API_KEY` is set. Free key from pixabay.com/api/docs.
   Pixabay's content licence needs no attribution.
2. Openverse, which needs no key. Restricted to CC0 and public domain so the
   backdrop carries no attribution obligation either.

The image lands in brand/assets/imagery/<slug>.jpg with a sidecar .json
recording where it came from. The document composites it against the page
colour at 10% through AmplifierDoc.set_backdrop.
"""
import json, os, subprocess, sys, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "assets", "imagery")
UA = "AmplifierBrandKit/1.0"

# What each document asks for. Keep queries abstract and textural: the image
# runs at 10% behind body copy, so anything with faces, hard edges or text in
# it turns to noise.
# query, plus terms at least one of which must appear in the hit's own tags.
# The tag guard is what stops "sound wave" returning a photograph of the sea.
TOPICS = {
    "token_run_rate":      ("growth chart graph", ["line graph", "chart", "graph"]),
    "regulatory_approach": ("courthouse columns", ["courthouse", "column", "classical"]),
    "sona2":               ("audio waveform", ["waveform"]),
    "lp_diligence":        ("paper texture", ["texture", "paper"]),
}

MIN_WIDTH = 1400


def _curl_json(url, headers=None):
    cmd = ["curl", "-sS", "-m", "40", url, "-H", "User-Agent: " + UA]
    for h in headers or []:
        cmd += ["-H", h]
    raw = subprocess.run(cmd, capture_output=True, text=True).stdout
    try:
        return json.loads(raw)
    except ValueError:
        raise SystemExit("unexpected response from %s:\n%s" % (url, raw[:400]))


def _landscape(w, h):
    return w and h and w >= MIN_WIDTH and w >= h


def from_pixabay(query, key, require=None, limit=6):
    params = {
        "key": key, "q": query, "image_type": "photo",
        "orientation": "horizontal", "safesearch": "true",
        "order": "popular", "min_width": str(MIN_WIDTH), "per_page": "20",
    }
    data = _curl_json("https://pixabay.com/api/?" + urllib.parse.urlencode(params))
    out = []
    for hit in data.get("hits") or []:
        src = hit.get("largeImageURL") or hit.get("webformatURL")
        if not src:
            continue
        tags = (hit.get("tags") or "").lower()
        if require and not any(t.lower() in tags for t in require):
            continue
        out.append({"source": "pixabay", "url": src, "page": hit.get("pageURL"),
                    "id": hit.get("id"), "tags": hit.get("tags"),
                    "license": "Pixabay Content License, no attribution required"})
        if len(out) >= limit:
            break
    return out


def from_openverse(query, limit=6):
    """Return candidates, widest first. Openverse's url is often a provider
    thumbnail, so the reported width is a hint rather than what arrives."""
    params = {"q": query, "license": "cc0,pdm", "mature": "false", "page_size": "20"}
    data = _curl_json("https://api.openverse.org/v1/images/?"
                      + urllib.parse.urlencode(params))
    cands = [h for h in (data.get("results") or [])
             if _landscape(h.get("width"), h.get("height")) and h.get("url")]
    cands.sort(key=lambda h: h.get("width") or 0, reverse=True)
    return [{"source": "openverse", "url": h.get("url"),
             "page": h.get("foreign_landing_url"), "id": h.get("id"),
             "title": h.get("title"), "creator": h.get("creator"),
             "reported_width": h.get("width"), "reported_height": h.get("height"),
             "license": "%s %s, no attribution required"
                        % ((h.get("license") or "").upper(),
                           h.get("license_version") or "")}
            for h in cands[:limit]]


def fetch(slug, query=None):
    topic = TOPICS.get(slug)
    require = None
    if query is None:
        if not topic:
            raise SystemExit("no query for %r, pass one as the second argument" % slug)
        query, require = topic
    elif topic:
        require = topic[1]

    key = os.environ.get("PIXABAY_API_KEY")
    candidates = []
    if key:
        candidates = from_pixabay(query, key, require)
        if not candidates:
            print("pixabay matched nothing relevant for %r, trying openverse" % query)
    candidates += from_openverse(query)
    if not candidates:
        raise SystemExit("no usable landscape image for %r" % query)

    os.makedirs(OUT_DIR, exist_ok=True)
    dest = os.path.join(OUT_DIR, "%s.jpg" % slug)
    for hit in candidates:
        subprocess.run(["curl", "-sSL", "-m", "60", "-o", dest, hit["url"],
                        "-H", "User-Agent: " + UA])
        if not os.path.exists(dest) or os.path.getsize(dest) < 15000:
            continue
        try:
            from PIL import Image
            with Image.open(dest) as im:
                w, h = im.size
        except Exception:
            continue
        # at 10% behind the page, resolution matters less than shape
        if w < 900 or w < h:
            continue
        hit.update({"query": query, "pixels": "%dx%d" % (w, h)})
        with open(os.path.join(OUT_DIR, "%s.json" % slug), "w") as f:
            json.dump(hit, f, indent=2)
        print("saved %-22s %dx%d  (%s)" % (slug, w, h, hit["source"]))
        return dest
    raise SystemExit("every candidate failed to download usably for %r" % query)


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        raise SystemExit("usage: fetch_imagery.py <slug> [query]  |  --all\n"
                         "slugs: %s" % ", ".join(TOPICS))
    if args[0] == "--all":
        for s in TOPICS:
            fetch(s)
    else:
        fetch(args[0], args[1] if len(args) > 1 else None)
