"""Classic Reed-Kellogg sentence diagram rendering.

This module provides functions to render traditional sentence diagrams
(also known as Reed-Kellogg diagrams) as SVG.

These diagrams visually represent the grammatical structure:
- Horizontal baseline for subject | predicate
- Vertical lines separating major elements
- Slanted lines for modifiers (adjectives, adverbs)
- "Pedestals" for prepositional phrases
"""

def generate_classic_diagram_svg(doc, width: int = 950, height: int = 320) -> str:
    """
    Generate a classic Reed-Kellogg style sentence diagram as SVG.

    Attempts to follow traditional rules:
    - Main horizontal baseline for subject | verb [ | direct object ]
    - Vertical line after subject
    - Slanted lines for adjectives (below nouns) and adverbs (below verbs)
    - Prepositional phrases on "pedestals" (slanted line down from attachment point,
      then horizontal line for the object of the preposition)
    - Articles treated as modifiers of the noun they precede.

    This is a heuristic approximation based on spaCy dependencies.
    It works well for simple declarative sentences and gets progressively
    less perfect with complex clauses, questions, passives with agents, etc.
    German support is approximate (V2 order etc.).
    """
    # --- Extract structure using spaCy deps (heuristic) ---
    subject = None
    verb = None
    direct_object = None
    subject_mods = []      # adjectives/articles for subject
    verb_mods = []         # adverbs for verb
    obj_mods = []          # adjectives for direct object
    prepositional_phrases = []  # list of (prep_token, pobj_token, attachment_token)

    for token in doc:
        if token.dep_ in ("nsubj", "nsubjpass"):
            subject = token
        elif token.dep_ == "ROOT" and token.pos_ in ("VERB", "AUX"):
            verb = token
        elif token.dep_ in ("dobj", "attr", "oprd"):
            direct_object = token
        elif token.dep_ == "amod":
            if subject and token.head == subject:
                subject_mods.append(token)
            elif direct_object and token.head == direct_object:
                obj_mods.append(token)
        elif token.dep_ == "advmod" and verb and token.head == verb:
            verb_mods.append(token)
        elif token.dep_ == "prep":
            pobj = next((c for c in token.children if c.dep_ == "pobj"), None)
            if pobj:
                # attach to the most recent main element (object > verb > subject)
                attach = direct_object or verb or subject
                prepositional_phrases.append((token, pobj, attach))

    # --- Layout parameters ---
    base_y = 160
    margin_left = 60
    char_width = 7.8   # approximate for Georgia 15px
    line_height = 18
    vertical_bar_height = 22

    parts = []
    parts.append(
        f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" '
        f'font-family="Georgia, Times, serif" font-size="15">'
    )

    # Subtle header with the original sentence
    sentence_str = " ".join(t.text for t in doc)
    parts.append(
        f'<rect x="0" y="0" width="{width}" height="26" fill="#f4f4f4" rx="3"/>'
    )
    parts.append(
        f'<text x="{margin_left}" y="18" font-size="11" fill="#555" font-style="italic">'
        f'{sentence_str}</text>'
    )

    x = margin_left

    # Helper to draw a word on the baseline
    def draw_word(text, x_pos, y_pos, bold=False):
        weight = 'font-weight="600"' if bold else ''
        parts.append(
            f'<text x="{x_pos}" y="{y_pos}" {weight}>{text}</text>'
        )

    # Helper for slanted modifier line + label
    def draw_modifier(mod_text, attach_x, attach_y, is_above=False):
        offset = -28 if is_above else 28
        label_y = attach_y + offset
        # label
        parts.append(f'<text x="{attach_x - 5}" y="{label_y}" font-size="12" fill="#333">{mod_text}</text>')
        # slanted line
        line_y1 = attach_y - 3 if is_above else attach_y + 3
        line_y2 = label_y + (6 if is_above else -6)
        parts.append(
            f'<line x1="{attach_x - 2}" y1="{line_y1}" x2="{attach_x - 18}" y2="{line_y2}" '
            'stroke="#444" stroke-width="1.6" stroke-linecap="round"/>'
        )

    # --- Draw subject + its modifiers ---
    if subject:
        # modifiers (articles, adjectives) go on slanted lines below the subject
        mod_attach_x = x
        for mod in subject_mods:
            draw_modifier(mod.text, mod_attach_x, base_y, is_above=False)
            mod_attach_x += len(mod.text) * char_width + 4

        draw_word(subject.text, x, base_y, bold=True)
        x += len(subject.text) * char_width + 12

        # Vertical line separating subject from predicate
        parts.append(
            f'<line x1="{x}" y1="{base_y - vertical_bar_height}" '
            f'x2="{x}" y2="{base_y + vertical_bar_height}" '
            'stroke="#222" stroke-width="2.2"/>'
        )
        x += 14

    # --- Verb + adverbs ---
    if verb:
        # adverbs below the verb
        for mod in verb_mods:
            draw_modifier(mod.text, x + 6, base_y, is_above=False)

        draw_word(verb.text, x, base_y, bold=True)
        x += len(verb.text) * char_width + 14

    # --- Direct object ---
    if direct_object:
        # vertical line before object
        parts.append(
            f'<line x1="{x}" y1="{base_y - vertical_bar_height}" '
            f'x2="{x}" y2="{base_y + vertical_bar_height}" '
            'stroke="#222" stroke-width="2"/>'
        )
        x += 14

        # object modifiers (adjectives) below
        for mod in obj_mods:
            draw_modifier(mod.text, x + 4, base_y, is_above=False)

        draw_word(direct_object.text, x, base_y)
        x += len(direct_object.text) * char_width + 10

    # --- Prepositional phrases (pedestals) ---
    for prep, pobj, attach in prepositional_phrases:
        # attach point is roughly current x or near the verb/object
        attach_x = x - 10
        # slanted line down for the preposition
        ped_y = base_y + 32
        parts.append(f'<text x="{attach_x - 4}" y="{ped_y}" font-size="12" fill="#222">{prep.text}</text>')
        parts.append(
            f'<line x1="{attach_x + 2}" y1="{base_y + 6}" x2="{attach_x + 14}" y2="{ped_y - 4}" '
            'stroke="#444" stroke-width="1.5"/>'
        )
        # horizontal line for pobj
        pobj_x = attach_x + 16
        pobj_width = max(28, len(pobj.text) * 6.8)
        parts.append(
            f'<line x1="{pobj_x}" y1="{base_y + 55}" x2="{pobj_x + pobj_width}" y2="{base_y + 55}" '
            'stroke="#444" stroke-width="1.5"/>'
        )
        parts.append(f'<text x="{pobj_x + 3}" y="{base_y + 70}" font-size="13" fill="#111">{pobj.text}</text>')

    # Main baseline (the iconic thick horizontal line)
    baseline_start = margin_left - 8
    baseline_end = max(x + 40, 380)
    parts.append(
        f'<line x1="{baseline_start}" y1="{base_y}" x2="{baseline_end}" y2="{base_y}" '
        'stroke="#222" stroke-width="2.4" stroke-linecap="square"/>'
    )

    # Subtle "baseline" label on the right (optional, for clarity)
    parts.append(
        f'<text x="{baseline_end + 6}" y="{base_y + 4}" font-size="9" fill="#888">baseline</text>'
    )

    parts.append("</svg>")
    return "\n".join(parts)
