from __future__ import annotations

import json
from itertools import combinations, product
from pathlib import Path
import re

CONFIG_PATH = Path(__file__).resolve().parent / "data" / "moderation_terms.json"


def _load_config() -> dict:
    if not CONFIG_PATH.exists():
        raise RuntimeError(f"Missing moderation config: {CONFIG_PATH}")
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


_CONFIG = _load_config()

BASE_BAD_TERMS: dict[str, list[str]] = _CONFIG["BASE_BAD_TERMS"]
EXTRA_PROFANITY_SEEDS: list[str] = _CONFIG["EXTRA_PROFANITY_SEEDS"]
BASE_PREFIXES: list[str] = _CONFIG["BASE_PREFIXES"]
BASE_SUFFIXES: list[str] = _CONFIG["BASE_SUFFIXES"]
LEET_MAP: dict[str, list[str]] = _CONFIG["LEET_MAP"]
TARGET_BASE_TERMS: int = int(_CONFIG["TARGET_BASE_TERMS"])
TARGET_OBFUSCATED_TERMS: int = int(_CONFIG["TARGET_OBFUSCATED_TERMS"])


def _single_word_terms(terms: dict[str, set[str]]) -> dict[str, str]:
    owner: dict[str, str] = {}
    for cat, values in terms.items():
        for term in values:
            if " " not in term:
                owner[term] = cat
    return owner


def _leet_variants(word: str, limit: int = 32) -> set[str]:
    positions = [i for i, char in enumerate(word) if char in LEET_MAP]
    if not positions:
        return set()

    variants: set[str] = set()
    max_positions = min(4, len(positions))

    for count in range(1, max_positions + 1):
        for selected in combinations(positions, count):
            options = [LEET_MAP[word[i]] for i in selected]
            for replacements in product(*options):
                chars = list(word)
                for idx, rep in zip(selected, replacements):
                    chars[idx] = rep
                variants.add("".join(chars))
                if len(variants) >= limit:
                    return variants

    return variants


def _repeat_char_variants(word: str, limit: int = 12) -> set[str]:
    variants: set[str] = set()
    for i, char in enumerate(word):
        if char.isalpha():
            variants.add(word[: i + 1] + char + word[i + 1 :])
            variants.add(word[:i] + char + char + word[i:])
            if len(variants) >= limit:
                break
    return variants


def _separator_variants(word: str) -> set[str]:
    if len(word) < 3 or " " in word:
        return set()
    chars = list(word)
    return {
        ".".join(chars),
        "_".join(chars),
        "-".join(chars),
    }


def _inflate_base_terms(terms: dict[str, set[str]], target_total: int) -> dict[str, set[str]]:
    total = sum(len(values) for values in terms.values())
    if total >= target_total:
        return terms

    all_by_category = {cat: sorted(values) for cat, values in terms.items()}

    while total < target_total:
        changed = False
        for category, seeds in all_by_category.items():
            for seed in seeds:
                for prefix in BASE_PREFIXES:
                    candidate = f"{prefix} {seed}"
                    if candidate not in terms[category]:
                        terms[category].add(candidate)
                        total += 1
                        changed = True
                        if total >= target_total:
                            return terms
                for suffix in BASE_SUFFIXES:
                    candidate = f"{seed} {suffix}"
                    if candidate not in terms[category]:
                        terms[category].add(candidate)
                        total += 1
                        changed = True
                        if total >= target_total:
                            return terms
                if " " not in seed:
                    for prefix in BASE_PREFIXES[:10]:
                        for suffix in BASE_SUFFIXES[:10]:
                            candidate = f"{prefix} {seed} {suffix}"
                            if candidate not in terms[category]:
                                terms[category].add(candidate)
                                total += 1
                                changed = True
                                if total >= target_total:
                                    return terms
        if not changed:
            return terms

    return terms


def _inflate_obfuscated_terms(
    base_terms: dict[str, set[str]],
    target_total: int,
) -> tuple[dict[str, set[str]], int]:
    owners = _single_word_terms(base_terms)
    generated = {cat: set() for cat in base_terms}

    total_obf = 0
    for word, category in owners.items():
        for variant in _leet_variants(word):
            if variant not in base_terms[category] and variant not in generated[category]:
                generated[category].add(variant)
                total_obf += 1
                if total_obf >= target_total:
                    return generated, total_obf

        for variant in _repeat_char_variants(word):
            if variant not in base_terms[category] and variant not in generated[category]:
                generated[category].add(variant)
                total_obf += 1
                if total_obf >= target_total:
                    return generated, total_obf

        for variant in _separator_variants(word):
            if variant not in base_terms[category] and variant not in generated[category]:
                generated[category].add(variant)
                total_obf += 1
                if total_obf >= target_total:
                    return generated, total_obf

    if total_obf < target_total:
        markers = ["*", ".", "_", "-", "+", "~", "!", "$", "@"]
        words = sorted(owners.items())
        round_idx = 0
        while total_obf < target_total:
            changed = False
            marker = markers[round_idx % len(markers)]
            for word, category in words:
                if len(word) < 2:
                    continue
                pos = (round_idx % (len(word) - 1)) + 1
                variant = f"{word[:pos]}{marker}{word[pos:]}"
                if variant not in base_terms[category] and variant not in generated[category]:
                    generated[category].add(variant)
                    total_obf += 1
                    changed = True
                    if total_obf >= target_total:
                        return generated, total_obf
            if not changed:
                break
            round_idx += 1

    return generated, total_obf


def _build_bad_terms() -> tuple[dict[str, list[str]], int, int]:
    terms: dict[str, set[str]] = {cat: set(values) for cat, values in BASE_BAD_TERMS.items()}

    terms["profanity"].update(EXTRA_PROFANITY_SEEDS)

    terms = _inflate_base_terms(terms, TARGET_BASE_TERMS)
    base_count = sum(len(values) for values in terms.values())

    obf_terms, obf_count = _inflate_obfuscated_terms(terms, TARGET_OBFUSCATED_TERMS)

    for category, values in obf_terms.items():
        terms[category].update(values)

    final_terms = {cat: sorted(values) for cat, values in terms.items()}
    return final_terms, base_count, obf_count


BAD_TERMS, BASE_TERMS_COUNT, OBFUSCATED_TERMS_COUNT = _build_bad_terms()


def _contains_term(text: str, term: str) -> bool:
    if " " not in term:
        if term.isalnum():
            pattern = rf"\b{re.escape(term)}\b"
            return re.search(pattern, text) is not None
        return term in text

    normalized_text = re.sub(r"\s+", " ", re.sub(r"[\W_]+", " ", text)).strip()
    normalized_term = re.sub(r"\s+", " ", re.sub(r"[\W_]+", " ", term)).strip()
    return normalized_term in normalized_text


def moderate_text(content: str) -> tuple[bool, str, list[str], str]:
    lowered = content.lower()
    found: list[str] = []
    category = "clean"

    for cat, terms in BAD_TERMS.items():
        for term in terms:
            if _contains_term(lowered, term):
                found.append(term)
                if category == "clean":
                    category = cat

    if not found:
        return True, "clean", [], "No risky terms detected."

    unique_terms = sorted(set(found))
    return False, category, unique_terms, "Potentially unsafe content detected."
