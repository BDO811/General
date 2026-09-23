# -*- coding: utf-8 -*-
"""Pull topical imagery from Pixabay for a document backdrop.

    export PIXABAY_API_KEY=...            # free key from pixabay.com/api/docs
    python3 fetch_imagery.py sona2 "sound wave audio spectrum"

Downloads the best match into brand/assets/imagery/<slug>.jpg. The document
then composites it against the page colour at 10% through
AmplifierDoc.set_backdrop, so the PDF carries no transparency group and the
backdrop prints the way it screens.

Pixabay content licence: free to use, no attribution required. Do not
redistribute the image itself as a standalone asset.
"""
import json, os, subprocess, sys, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "assets", "imagery")
API = "https://pixabay.com/api/"

# What each document asks for. Keep queries abstract and textural: the image
# runs at 10% behind body copy, so anything with faces, hard edges or text in
# it turns to noise.
TOPICS = {
    "token_run_rate":       "abstract data growth lines minimal",
    "regulatory_approach":  "architecture columns government building minimal",
    "sona2":                "sound wave audio spectrum abstract",
}


def fetch(slug, query=None, key=None):
    key = key or os.environ.get("PIXABAY_API_KEY")
    if not key:
        raise SystemExit("set PIXABAY_API_KEY first, free key at "
                         "https://pixabay.com/api/docs/")
    query = query or TOPICS.get(slug)
    if not query:
        raise SystemExit("no query for %r, pass one as the second argument" % slug)

    params = {
        "key": key,
        "q": query,
        "image_type": "photo",
        "orientation": "horizontal",
        "safesearch": "true",
        "order": "popular",
        "min_width": "1920",
        "per_page": "20",
    }
    url = API + "?" + urllib.parse.urlencode(params)
    raw = subprocess.run(["curl", "-sS", url], capture_output=True, text=True).stdout
    try:
        data = json.loads(raw)
    except ValueError:
        raise SystemExit("pixabay returned: %s" % raw[:300])
    hits = data.get("hits") or []
    if not hits:
        raise SystemExit("no results for %r" % query)

    hit = hits[0]
    src = hit.get("largeImageURL") or hit.get("webformatURL")
    os.makedirs(OUT_DIR, exist_ok=True)
    dest = os.path.join(OUT_DIR, "%s.jpg" % slug)
    subprocess.run(["curl", "-sSL", "-o", dest, src], check=True)
    meta = os.path.join(OUT_DIR, "%s.json" % slug)
    with open(meta, "w") as f:
        json.dump({"query": query, "id": hit.get("id"), "page": hit.get("pageURL"),
                   "source": src, "tags": hit.get("tags")}, f, indent=2)
    print("saved", dest)
    print("source", hit.get("pageURL"))
    return dest


if __name__ == "__main__":
    slug = sys.argv[1] if len(sys.argv) > 1 else None
    if not slug:
        raise SystemExit("usage: fetch_imagery.py <slug> [query]\nslugs: %s"
                         % ", ".join(TOPICS))
    fetch(slug, sys.argv[2] if len(sys.argv) > 2 else None)
