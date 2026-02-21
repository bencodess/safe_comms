from __future__ import annotations

from itertools import combinations, product
import re

BASE_BAD_TERMS = {
    "violence": [
        "kill", "killing", "killer", "murder", "massacre", "slaughter", "execute", "execution",
        "behead", "decapitate", "assassinate", "shoot", "gun down", "stab", "knife attack",
        "bomb", "bombing", "explosive", "explode", "detonate", "terror", "terrorist",
        "hostage", "kidnap", "abduct", "arson", "burn alive", "torture", "lynch", "gore",
        "bloodbath", "genocide", "ethnic cleansing", "war crime", "hitman", "sniper",
        "school shooting", "mass shooting", "suicide bomb", "car bomb", "grenade", "molotov",
        "sprengstoff", "anschlag", "attentat", "amoklauf", "erschiessen", "erstechen",
        "toeten", "mord", "folter", "blutbad", "waffengewalt", "gewaltfantasie", "anfassen", "rape", "raping",
        "rayping", "ich werde dich finden", "i will find you", "hurt you", "lock you", "oil up", "oiled up", "epstein"
    ],
    "hate": [
        "nazi", "neo nazi", "white power", "kkk", "supremacist", "racist", "race war",
        "antisemitic", "anti semitic", "judenhass", "hate speech", "ethnic hatred",
        "xenophobic", "homophobic", "transphobic", "islamophobic", "bigot", "bigotry",
        "nigger", "nigga", "niqqa", "slur", "racial slur", "heil hitler", "sieg heil",
        "master race", "subhuman", "exterminate them", "deport them all", "gas them",
        "replace theory", "1488", "ausländer raus", "volksverräter", "rassenhass",
        "menschenverachtend", "n1gga"
    ],
    "sexual": [
        "porn", "porno", "pornhub", "nude", "nudes", "nudity", "nsfw", "explicit", "xxx",
        "hardcore", "fetish", "bdsm", "deepthroat", "blowjob", "handjob", "anal", "cum",
        "creampie", "sexting", "sex chat", "onlyfans", "camgirl", "cam sex", "escort",
        "prostitute", "brothel", "incest", "bestiality", "rape fantasy", "child porn",
        "cp", "loli", "lolicon", "underage sex", "minor nudes", "revenge porn",
        "nacktbild", "sexvideo", "pornografisch", "erotisch", "intimfoto", "cum", "cumshot", "comshot"
    ],
    "drugs": [
        "cocaine", "coke", "crack", "meth", "methamphetamine", "heroin", "fentanyl",
        "opioid", "oxycodone", "morphine", "lsd", "ecstasy", "mdma", "ketamine",
        "pcp", "amphetamine", "speed", "weed", "marijuana", "cannabis", "hash",
        "drug deal", "dealer", "buy drugs", "sell drugs", "overdose", "inject heroin",
        "snort cocaine", "cook meth", "cartel", "narcotics", "dope", "pill mill",
        "drogen", "drogendealer", "koks", "gras", "hasch", "ecstasy pillen", "btm", "crackhead"
    ],
    "abuse": [
        "child abuse", "child sexual abuse", "grooming", "molest", "molestation",
        "domestic violence", "intimate partner violence", "self harm", "self-harm",
        "cut myself", "cutting", "suicide", "kill myself", "hang myself", "overdose myself",
        "abuse children", "beat your wife", "beat your kid", "shaken baby", "csa",
        "csam", "rape child", "underage exploitation", "forced marriage", "human trafficking",
        "zwangsprostitution", "kindesmissbrauch", "selbstmord", "ritzen", "suizid", "haeusliche gewalt", "homicide"
    ],
    "profanity": [
        "fuck", "fucking", "motherfucker", "shit", "bullshit", "bitch", "bastard", "asshole",
        "dickhead", "cunt", "wanker", "prick", "slut", "whore", "son of a bitch",
        "retard", "dumbass", "jackass", "fucker", "idiot", "moron", "piece of shit",
        "fick", "scheisse", "miststueck", "hurensohn", "fotze", "arschloch", "wichser",
        "spast", "nutte", "verpiss dich", "halt die fresse", "opfer", "pussy",
    ],
    "scam": [
        "credit card dump", "stolen card", "cvv", "fullz", "phishing", "fake login",
        "account takeover", "steal password", "malware", "ransomware", "keylogger",
        "botnet", "ddos for hire", "hack account", "crack password", "bruteforce",
        "sim swap", "money mule", "ponzi", "pump and dump", "advance fee fraud",
        "romance scam", "gift card scam", "wire fraud", "bank fraud", "identity theft",
        "betrug", "phishing link", "konto hacken", "daten klauen",
    ],
}

EXTRA_PROFANITY_SEEDS = [
    "douche", "douchebag", "dipshit", "shithead", "shitface", "piss", "pissed", "piss off",
    "freak", "loser", "garbage", "trash", "scumbag", "skank", "hoe", "ho", "twat", "jerk",
    "imbecile", "stupid", "idiotic", "dumb", "brain dead", "braindead", "cretin", "clown",
    "clownass", "wannabe", "sucker", "lame", "pathetic", "degenerate", "pervert", "psycho",
    "lunatic", "maniac", "weirdo", "fool", "tool", "numbnuts", "nutsack", "ballsack",
    "arse", "arsehole", "bollocks", "bloody hell", "f off", "screw you", "eat shit",
    "penner", "trottel", "depp", "idiotisch", "huso", "fotz", "spacken", "mongo",
    "bimbo", "simp", "cringe", "incel", "soyboy", "beta male", "alpha clown", "dogshit",
    "shitshow", "shitstorm", "asshat", "assclown", "asswipe", "butthead", "cocksucker",
    "cock", "dick", "penis", "boobs", "tits", "milf", "dildo", "buttplug", "cumshot",
    "jerkoff", "wixxer", "wixxa", "schwachkopf", "vollidiot", "knecht", "lappen",
]

BASE_PREFIXES = [
    "dirty", "filthy", "stupid", "dumb", "crazy", "foul", "gross", "toxic", "bloody", "damn",
    "hard", "extreme", "pure", "ultra", "mega", "insane", "savage", "aggressive", "nasty", "vile",
    "evil", "brutal", "raw", "wild", "mad", "cold", "dark", "loud", "chaos", "mean",
]

BASE_SUFFIXES = [
    "head", "face", "brain", "mouth", "rat", "pig", "dog", "lord", "king", "queen",
    "mode", "move", "plan", "crew", "zone", "style", "energy", "storm", "wave", "pattern",
]

LEET_MAP = {
    "a": ["4", "@"],
    "e": ["3"],
    "i": ["1", "!"],
    "o": ["0"],
    "s": ["5", "$"],
    "t": ["7"],
    "g": ["9"],
}

TARGET_BASE_TERMS = 10000
TARGET_OBFUSCATED_TERMS = 10000


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
    return False, category, unique_terms, "Potentially unsafe content detected. If error please view README.md"

