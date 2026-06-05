"""Classic Reed-Kellogg sentence diagram rendering.

This module provides functions to render traditional sentence diagrams
(also known as Reed-Kellogg diagrams) as SVG.

These diagrams visually represent the grammatical structure:
- Horizontal baseline for subject | predicate
- Vertical lines separating major elements
- Slanted lines for modifiers (adjectives, adverbs)
- "Pedestals" for prepositional phrases
"""

def generate_classic_diagram_svg(doc, width: int = 900, height: int = 280) -> str:
    """
    Generate an SVG string for a classic Reed-Kellogg style sentence diagram.

    This is a practical approximation that works well for simple to moderately
    complex sentences (SVO, adjectives, adverbs, prepositional phrases, basic compounds).

    For very complex sentences (multiple clauses, infinitives, gerunds) it will
    still produce a readable diagram but may not be 100% textbook perfect.
    """
    # Collect key grammatical elements using dependency labels
    subject = None
    verb = None
    direct_object = None
    subject_modifiers = []   # amod on subject
    verb_modifiers = []      # advmod on verb
    preps = []               # (prep_token, pobj_token)

    for token in doc:
        if token.dep_ in ("nsubj", "nsubjpass"):
            subject = token
        elif token.dep_ == "ROOT" and token.pos_ in ("VERB", "AUX"):
            verb = token
        elif token.dep_ in ("dobj", "attr", "oprd"):
            direct_object = token
        elif token.dep_ == "amod" and subject and token.head == subject:
            subject_modifiers.append(token)
        elif token.dep_ == "advmod" and verb and token.head == verb:
            verb_modifiers.append(token)
        elif token.dep_ == "prep":
            for child in token.children:
                if child.dep_ == "pobj":
                    preps.append((token, child))
                    break

    # Start building SVG
    parts = []
    parts.append(f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" font-family="Georgia, serif">')

    # Light background and title
    parts.append(f'<rect x="0" y="0" width="{width}" height="30" fill="#f8f9fa"/>')
    sentence_text = " ".join(t.text for t in doc)
    parts.append(f'<text x="12" y="20" font-size="12" fill="#444" font-style="italic">{sentence_text}</text>')

    # Baseline y
    base_y = 140          # main horizontal line y-position
    x = 60                # starting x for the diagram

    # --- SUBJECT SIDE ---
    if subject:
        # Adjectives / articles on slanted lines above the subject
        mod_x = x
        for mod in subject_modifiers:
            parts.append(f'<text x="{mod_x}" y="{base_y - 38}" font-size="13" fill="#222">{mod.text}</text>')
            # Slanted modifier line
            parts.append(f'<line x1="{mod_x + 8}" y1="{base_y - 32}" x2="{x + len(subject.text)*4.2}" y2="{base_y - 8}" '
                         'stroke="#333" stroke-width="1.5" stroke-linecap="round"/>')
            mod_x += max(38, len(mod.text) * 7)

        # Main subject word on the baseline
        parts.append(f'<text x="{x}" y="{base_y + 5}" font-size="15" font-weight="600" fill="#111">{subject.text}</text>')

        # Advance x past the subject
        x += max(55, len(subject.text) * 8.5)

        # Vertical bar separating subject from predicate
        parts.append(f'<line x1="{x}" y1="{base_y - 18}" x2="{x}" y2="{base_y + 18}" '
                     'stroke="#222" stroke-width="2.5"/>')
        x += 18

    # --- VERB / PREDICATE ---
    if verb:
        # Adverbs on slanted lines below the verb
        for mod in verb_modifiers:
            parts.append(f'<text x="{x + 12}" y="{base_y + 32}" font-size="12" fill="#222" font-style="italic">{mod.text}</text>')
            parts.append(f'<line x1="{x + 8}" y1="{base_y + 8}" x2="{x + 18}" y2="{base_y + 24}" '
                         'stroke="#333" stroke-width="1.5"/>')

        parts.append(f'<text x="{x}" y="{base_y + 5}" font-size="15" font-weight="600" fill="#111">{verb.text}</text>')
        x += max(60, len(verb.text) * 8.5)

    # --- DIRECT OBJECT ---
    if direct_object:
        # Another vertical line before the object
        parts.append(f'<line x1="{x}" y1="{base_y - 18}" x2="{x}" y2="{base_y + 18}" '
                     'stroke="#222" stroke-width="2"/>')
        x += 16
        parts.append(f'<text x="{x}" y="{base_y + 5}" font-size="15" fill="#111">{direct_object.text}</text>')
        x += max(50, len(direct_object.text) * 8)

    # --- PREPOSITIONAL PHRASES (pedestals) ---
    for prep, pobj in preps:
        ped_start_x = x - 25
        # Slanted line from the main structure (usually from verb or object area)
        parts.append(f'<text x="{ped_start_x}" y="{base_y + 38}" font-size="12" fill="#222">{prep.text}</text>')
        parts.append(f'<line x1="{ped_start_x + 6}" y1="{base_y + 28}" x2="{ped_start_x + 22}" y2="{base_y + 55}" '
                     'stroke="#333" stroke-width="1.5"/>')

        # Small horizontal line for the object of the preposition
        obj_width = max(35, len(pobj.text) * 7.5)
        parts.append(f'<line x1="{ped_start_x + 22}" y1="{base_y + 55}" x2="{ped_start_x + 22 + obj_width}" y2="{base_y + 55}" '
                     'stroke="#333" stroke-width="1.5"/>')
        parts.append(f'<text x="{ped_start_x + 26}" y="{base_y + 70}" font-size="13" fill="#111">{pobj.text}</text>')

        x = max(x, ped_start_x + 22 + obj_width + 10)

    # Baseline (the famous horizontal line)
    baseline_end = max(x + 30, 420)
    parts.append(f'<line x1="55" y1="{base_y}" x2="{baseline_end}" y2="{base_y}" '
                 'stroke="#222" stroke-width="2"/>')

    parts.append('</svg>')
    return '\n'.join(parts)
