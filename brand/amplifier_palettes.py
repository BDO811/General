# -*- coding: utf-8 -*-
"""Amplifier Health named palettes.

AMPLIFIER-DESIGN-PALETTE  the house palette and the DEFAULT for every document.
                          Bone ground, forest green accent, warm black ink.
                          Anything that leaves the building: flyers, proposals,
                          investor documents, printed collateral.

AMPLIFIER-DARK-PALETTE    the dark variant. Near black ground, cyan and emerald.
                          Screens, dashboards, product UI. Never the default.

Both carry the same key names, so one document can render in either.
Hex values for the design palette were lifted from the production flyer
(Amplifier_Flyer_01_Voice_AI_Platforms.pdf), not sampled by eye.
"""

AMPLIFIER_DESIGN_PALETTE = {
    "name": "AMPLIFIER-DESIGN-PALETTE",
    # ground
    "bg":        "#f0eae0",   # bone, the page
    "surface":   "#e9e3d5",   # wash, panels, the block behind display type
    "surface_2": "#d8d0c2",   # hairlines, rules, table keylines
    "panel":     "#12241a",   # dark green black, code and inverted blocks
    # ink
    "ink":       "#181716",   # primary text
    "ink_2":     "#484643",   # secondary text
    "muted":     "#6c6965",   # microtype, labels, captions
    # accent
    "accent":    "#1e5631",   # forest green, primary accent and logo
    "accent_2":  "#4caf6e",   # bright green, syntax, positive deltas
    "cta":       "#000000",   # pill buttons
    # type
    "display":   "Cormorant Garamond Light",
    "deck":      "Newsreader 16pt Italic",
    "body":      "Inter",
    "mono":      "JetBrains Mono",
}

AMPLIFIER_DARK_PALETTE = {
    "name": "AMPLIFIER-DARK-PALETTE",
    # ground
    "bg":        "#050505",
    "surface":   "#0a0a0a",
    "surface_2": "#18181b",
    "panel":     "#26262c",
    # ink
    "ink":       "#fafafa",
    "ink_2":     "#b4b4bc",
    "muted":     "#8b8b93",
    # accent
    "accent":    "#22d3ee",
    "accent_2":  "#10b981",
    "cta":       "#22d3ee",
    # type
    "display":   "Cormorant Garamond SemiBold",
    "deck":      "Cormorant Garamond SemiBold",
    "body":      "Inter",
    "mono":      "JetBrains Mono",
}

PALETTES = {
    "AMPLIFIER-DESIGN-PALETTE": AMPLIFIER_DESIGN_PALETTE,
    "AMPLIFIER-DARK-PALETTE":   AMPLIFIER_DARK_PALETTE,
}

# Every document starts here. Only depart from it when the destination is a
# screen and someone asked for the dark cut by name.
DEFAULT = "AMPLIFIER-DESIGN-PALETTE"

def get(name=None):
    key = (name or DEFAULT).strip().upper()
    if key not in PALETTES:
        raise KeyError("unknown palette %r, known: %s" % (name, ", ".join(PALETTES)))
    return PALETTES[key]
