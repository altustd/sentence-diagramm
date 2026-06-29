"""Classic Reed-Kellogg sentence diagram rendering.

This module provides functions to render traditional sentence diagrams
(also known as Reed-Kellogg diagrams) as SVG.

These diagrams visually represent the grammatical structure:
- Horizontal baseline for subject | predicate
- Vertical lines separating major elements
- Slanted lines for modifiers (adjectives, adverbs)
- "Pedestals" for prepositional phrases
"""

# Universal Dependencies (English) and TIGER-style labels (German de_core_news_sm).
_SUBJECT_DEPS = frozenset({"nsubj", "nsubjpass", "sb", "sgs"})
_DIRECT_OBJECT_DEPS = frozenset({"dobj", "attr", "oprd", "oa", "og", "obj", "conj"})
_INDIRECT_OBJECT_DEPS = frozenset({"iobj", "da"})
_PREDICATE_DEPS = frozenset({"pd"})
_NOUN_MODIFIER_DEPS = frozenset({"amod", "det", "compound", "nk"})
_OBL_DEPS = frozenset({"obl", "pobj"})
_PRONOUN_BASELINE_DEPS = frozenset({"expl:pv", "expl", "iobj"})
_LEXICAL_VERB_DEPS = frozenset({"oc", "xcomp", "ccomp"})


def _is_subject(token) -> bool:
    return token.dep_ in _SUBJECT_DEPS


def _is_direct_object(token) -> bool:
    return token.dep_ in _DIRECT_OBJECT_DEPS


def _is_indirect_object(token) -> bool:
    return token.dep_ in _INDIRECT_OBJECT_DEPS


def _is_predicate_complement(token) -> bool:
    return token.dep_ in _PREDICATE_DEPS


def _is_noun_modifier(token, noun) -> bool:
    return token.head == noun and token.dep_ in _NOUN_MODIFIER_DEPS


def _is_verb_modifier(token, verb) -> bool:
    if token.head != verb:
        return False
    if token.dep_ == "advmod":
        return True
    return token.dep_ == "mo" and token.pos_ in {"ADV", "PART"}


def _is_preposition(token) -> bool:
    if token.dep_ in {"prep", "case"}:
        return True
    return token.dep_ == "mo" and token.pos_ == "ADP"


def _is_oblique(token) -> bool:
    return token.dep_ in _OBL_DEPS


def _prep_object(prep_token):
    for child in prep_token.children:
        if child.dep_ == "pobj":
            return child
        if child.dep_ in {"nk", "pd"} and child.pos_ in {"NOUN", "PROPN", "PRON"}:
            return child
    return None


def _obl_case_marker(obl_token):
    return next((c for c in obl_token.children if c.dep_ == "case"), None)


def _collect_noun_modifiers(doc, noun):
    return [t for t in doc if _is_noun_modifier(t, noun)]


def _find_verbs(doc):
    """Return (root verb token, verb used for modifier attachment, baseline label)."""
    root = next((t for t in doc if t.dep_ == "ROOT"), None)
    if root is None:
        return None, None, None

    cop = next((c for c in root.children if c.dep_ == "cop"), None)
    if cop is not None:
        return cop, cop, f"{cop.text} {root.text}"

    if root.pos_ not in {"VERB", "AUX", "ADJ"}:
        return None, None, None

    if root.pos_ == "ADJ":
        return root, root, root.text

    lexical = next(
        (c for c in root.children if c.dep_ in _LEXICAL_VERB_DEPS and c.pos_ in {"VERB", "AUX"}),
        None,
    )
    attach = lexical or root
    if root.pos_ == "AUX" and lexical is not None:
        label = f"{root.text} {lexical.text}"
    else:
        label = root.text
    return root, attach, label


def _german_baseline_items(doc):
    """Build baseline segments in German surface (V2) word order."""
    _, attach_verb, verb_label = _find_verbs(doc)
    root = next((t for t in doc if t.dep_ == "ROOT"), None)
    placed = set()
    items = []

    def append_item(token, text, role, mods=None):
        items.append({"token": token, "text": text, "role": role, "mods": mods or []})
        placed.add(token.i)

    for token in doc:
        if token.is_punct or token.i in placed:
            continue

        if _is_noun_modifier(token, token.head) and (
            _is_subject(token.head)
            or _is_direct_object(token.head)
            or _is_indirect_object(token.head)
            or (
                token.head.dep_ == "nk"
                and token.head.head is not None
                and _is_preposition(token.head.head)
            )
        ):
            continue

        if _is_preposition(token):
            pobj = _prep_object(token)
            append_item(token, token.text, "prep")
            if pobj is not None:
                append_item(
                    pobj,
                    pobj.text,
                    "pobj",
                    _collect_noun_modifiers(doc, pobj),
                )
            continue

        if token.dep_ == "ROOT" and token.pos_ in {"VERB", "AUX"}:
            append_item(token, verb_label, "verb")
            continue

        if token.dep_ in _LEXICAL_VERB_DEPS and token.pos_ in {"VERB", "AUX"}:
            # Auxiliary + participle/infinitive is already folded into verb_label.
            if root is not None and root.pos_ == "AUX" and token.dep_ == "oc":
                continue
            append_item(token, token.text, "verb")
            continue

        if _is_subject(token):
            append_item(token, token.text, "subject", _collect_noun_modifiers(doc, token))
            continue

        if _is_indirect_object(token):
            append_item(token, token.text, "indirect", _collect_noun_modifiers(doc, token))
            continue

        if _is_direct_object(token):
            append_item(token, token.text, "object", _collect_noun_modifiers(doc, token))
            continue

        if _is_predicate_complement(token):
            append_item(token, token.text, "predicate")
            continue

        if attach_verb and _is_verb_modifier(token, attach_verb):
            append_item(token, token.text, "adverb")
            continue

        if token.dep_ == "nk" and token.head == root:
            append_item(token, token.text, "modifier")

    return items


def _spanish_baseline_items(doc):
    """Build baseline segments in Spanish surface word order (UD tags)."""
    _, attach_verb, verb_label = _find_verbs(doc)
    root = next((t for t in doc if t.dep_ == "ROOT"), None)
    placed = set()
    items = []

    def append_item(token, text, role, mods=None):
        items.append({"token": token, "text": text, "role": role, "mods": mods or []})
        placed.add(token.i)

    for token in doc:
        if token.is_punct or token.i in placed:
            continue

        if _is_noun_modifier(token, token.head) and (
            _is_subject(token.head)
            or _is_direct_object(token.head)
            or _is_indirect_object(token.head)
            or _is_oblique(token.head)
        ):
            continue

        if _is_oblique(token):
            case_marker = _obl_case_marker(token)
            if case_marker is not None:
                append_item(case_marker, case_marker.text, "prep")
            append_item(token, token.text, "pobj", _collect_noun_modifiers(doc, token))
            continue

        if _is_subject(token):
            append_item(token, token.text, "subject", _collect_noun_modifiers(doc, token))
            continue

        if token.dep_ in _PRONOUN_BASELINE_DEPS:
            append_item(token, token.text, "pronoun")
            continue

        if token.dep_ == "cop":
            append_item(token, token.text, "verb")
            continue

        if token.dep_ == "ROOT" and token.pos_ in {"VERB", "AUX", "ADJ"}:
            if any(c.dep_ == "cop" for c in token.children):
                append_item(token, token.text, "predicate")
                continue
            append_item(token, verb_label or token.text, "verb")
            continue

        if _is_direct_object(token) and token.head in {attach_verb, root}:
            case_marker = _obl_case_marker(token)
            if case_marker is not None:
                append_item(case_marker, case_marker.text, "prep")
            append_item(token, token.text, "object", _collect_noun_modifiers(doc, token))
            continue

        if attach_verb and _is_verb_modifier(token, attach_verb):
            append_item(token, token.text, "adverb")
            continue

    return items


def _english_baseline_words(doc) -> list[str]:
    """Words placed on the English diagram baseline, in reading order."""
    subject = next((t for t in doc if _is_subject(t)), None)
    _, _, verb_label = _find_verbs(doc)
    indirect_object = next((t for t in doc if _is_indirect_object(t)), None)
    direct_object = next((t for t in doc if _is_direct_object(t)), None)
    predicate = next((t for t in doc if _is_predicate_complement(t)), None)

    words: list[str] = []
    if subject is not None:
        words.append(subject.text)
    if verb_label:
        words.append(verb_label)
    if indirect_object is not None:
        words.append(indirect_object.text)
    complement = direct_object or predicate
    if complement is not None:
        words.append(complement.text)
    for token in doc:
        if not _is_preposition(token):
            continue
        words.append(token.text)
        pobj = _prep_object(token)
        if pobj is not None:
            words.append(pobj.text)
    return words


def get_baseline_words(doc) -> list[str]:
    """Return baseline word order as rendered in the classic diagram."""
    lang = getattr(doc, "lang_", None)
    if lang == "de":
        return [item["text"] for item in _german_baseline_items(doc)]
    if lang == "es":
        return [item["text"] for item in _spanish_baseline_items(doc)]
    return _english_baseline_words(doc)


def _role_needs_bar_before(role, previous_role):
    if previous_role is None:
        return False
    if role == "verb" and previous_role in {"subject", "adverb", "fronted"}:
        return True
    if role == "subject" and previous_role == "verb":
        return True
    if role in {"object", "indirect", "predicate"} and previous_role not in {role, "prep", "pobj"}:
        return True
    return False


def _generate_surface_diagram_svg(doc, items, width: int = 950, height: int = 320) -> str:
    """Diagram with baseline segments in surface reading order."""
    base_y = 160
    margin_left = 60
    char_width = 7.8
    vertical_bar_height = 22

    parts = [
        f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" '
        f'font-family="Georgia, Times, serif" font-size="15">',
        f'<rect x="0" y="0" width="{width}" height="26" fill="#f4f4f4" rx="3"/>',
        f'<text x="{margin_left}" y="18" font-size="11" fill="#555" font-style="italic">'
        f'{" ".join(t.text for t in doc)}</text>',
    ]

    x = margin_left
    previous_role = None

    def draw_word(text, x_pos, bold=False):
        weight = 'font-weight="600"' if bold else ""
        parts.append(f'<text x="{x_pos}" y="{base_y}" {weight}>{text}</text>')

    def draw_modifier(mod_text, attach_x):
        label_y = base_y + 28
        parts.append(f'<text x="{attach_x - 5}" y="{label_y}" font-size="12" fill="#333">{mod_text}</text>')
        parts.append(
            f'<line x1="{attach_x - 2}" y1="{base_y + 3}" x2="{attach_x - 18}" y2="{label_y - 6}" '
            'stroke="#444" stroke-width="1.6" stroke-linecap="round"/>'
        )

    for item in items:
        role = item["role"]
        if _role_needs_bar_before(role, previous_role):
            parts.append(
                f'<line x1="{x}" y1="{base_y - vertical_bar_height}" '
                f'x2="{x}" y2="{base_y + vertical_bar_height}" '
                'stroke="#222" stroke-width="2.2"/>'
            )
            x += 14

        mod_attach_x = x
        for mod in item["mods"]:
            draw_modifier(mod.text, mod_attach_x)
            mod_attach_x += len(mod.text) * char_width + 4

        draw_word(item["text"], x, bold=(role in {"verb", "subject"}))
        x += len(item["text"]) * char_width + 12
        previous_role = role

    baseline_start = margin_left - 8
    baseline_end = max(x + 40, 380)
    parts.append(
        f'<line x1="{baseline_start}" y1="{base_y}" x2="{baseline_end}" y2="{base_y}" '
        'stroke="#222" stroke-width="2.4" stroke-linecap="square"/>'
    )
    parts.append(
        f'<text x="{baseline_end + 6}" y="{base_y + 4}" font-size="9" fill="#888">baseline</text>'
    )
    parts.append("</svg>")
    return "\n".join(parts)


def _generate_german_diagram_svg(doc, width: int = 950, height: int = 320) -> str:
    return _generate_surface_diagram_svg(doc, _german_baseline_items(doc), width=width, height=height)


def _generate_spanish_diagram_svg(doc, width: int = 950, height: int = 320) -> str:
    return _generate_surface_diagram_svg(doc, _spanish_baseline_items(doc), width=width, height=height)


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
    German and Spanish use surface word order on the baseline; English uses
    canonical subject | verb | object order.
    """
    lang = getattr(doc, "lang_", None)
    if lang == "de":
        return _generate_german_diagram_svg(doc, width=width, height=height)
    if lang == "es":
        return _generate_spanish_diagram_svg(doc, width=width, height=height)

    # --- Extract structure using spaCy deps (heuristic) ---
    subject = next((t for t in doc if _is_subject(t)), None)
    _, attach_verb, verb_label = _find_verbs(doc)
    direct_object = next((t for t in doc if _is_direct_object(t)), None)
    indirect_object = next((t for t in doc if _is_indirect_object(t)), None)
    predicate = next((t for t in doc if _is_predicate_complement(t)), None)

    subject_mods = _collect_noun_modifiers(doc, subject) if subject else []
    verb_mods = [t for t in doc if attach_verb and _is_verb_modifier(t, attach_verb)]
    indirect_mods = _collect_noun_modifiers(doc, indirect_object) if indirect_object else []
    obj_mods = _collect_noun_modifiers(doc, direct_object) if direct_object else []
    prepositional_phrases = []

    for token in doc:
        if not _is_preposition(token):
            continue
        pobj = _prep_object(token)
        if pobj:
            attach = direct_object or indirect_object or attach_verb or subject
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
    if verb_label:
        for mod in verb_mods:
            draw_modifier(mod.text, x + 6, base_y, is_above=False)

        draw_word(verb_label, x, base_y, bold=True)
        x += len(verb_label) * char_width + 14

    def draw_object_phrase(obj_token, mods):
        nonlocal x
        parts.append(
            f'<line x1="{x}" y1="{base_y - vertical_bar_height}" '
            f'x2="{x}" y2="{base_y + vertical_bar_height}" '
            'stroke="#222" stroke-width="2"/>'
        )
        x += 14

        for mod in mods:
            draw_modifier(mod.text, x + 4, base_y, is_above=False)

        draw_word(obj_token.text, x, base_y)
        x += len(obj_token.text) * char_width + 10

    # --- Indirect object (dative / iobj) ---
    if indirect_object:
        draw_object_phrase(indirect_object, indirect_mods)

    # --- Direct object or predicate complement ---
    complement = direct_object or predicate
    complement_mods = obj_mods if direct_object else []
    if complement:
        draw_object_phrase(complement, complement_mods)

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