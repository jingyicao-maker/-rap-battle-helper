# Small sound checks shared by draft generation and manual editing
import re
from functools import lru_cache
import pronouncing


def words_in(text):
    # Keep contractions together, while ignoring punctuation and case.
    return re.findall(r"[a-z]+(?:'[a-z]+)?", text.lower().replace('’', "'"))


@lru_cache(maxsize=None)
def sounds_for(word):
    # Choosing one dictionary pronunciation keeps the rule easy to reproduce.
    # The cache avoids repeating the same lookup during thousands of attempts.
    sounds = pronouncing.phones_for_word(word)
    return sounds[0] if sounds else None


def syllables_in(word):
    sounds = sounds_for(word)
    return pronouncing.syllable_count(sounds) if sounds else None


def rhyme_part(word):
    sounds = sounds_for(word)
    return pronouncing.rhyming_part(sounds) if sounds else None


def inspect_line(line, target, seed, keywords):
    words = words_in(line)
    counts = [syllables_in(word) for word in words]
    unknown = [word for word, count in zip(words, counts) if count is None]
    # Unknown word prevents a trustworthy total but not silently treat it as 0.
    total = sum(counts) if words and not unknown else None
    ending = words[-1] if words else ''
    rhymes = bool(rhyme_part(seed) and rhyme_part(ending) == rhyme_part(seed))
    matches = sorted(set(words) & set(keywords))
    return {'line': line, 'ending': ending, 'syllables': total,
            'target_met': total == target, 'rhyme_met': rhymes,
            'unknown_words': ', '.join(unknown),
            'word_counts': ' / '.join(f'{w}={c if c is not None else "?"}' for w, c in zip(words, counts)),
            'keyword_hits': len(matches), 'matched_keywords': ', '.join(matches)}
