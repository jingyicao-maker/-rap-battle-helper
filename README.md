# Rhyme Desk

**A small writing desk for short, sound-constrained verse.** Choose an end-rhyme word, a syllable target, two to four bars and some theme words. The program suggests drafts, lets you choose and edit lines, and writes a readable session record.

## Start here

Extract the folder. Use Python 3.11 or 3.12 and a terminal in this directory.

```bash
python -m venv .venv
```

Windows: `.venv\Scripts\activate`  
macOS/Linux: `source .venv/bin/activate`

```bash
python -m pip install -r requirements.txt
```

```bash
python desk.py
```

Press Enter for the offered defaults. A random seed makes repeated runs reproducible; changing it explores other word combinations. Use `-` for no theme keywords. The dictionary needs a known English rhyme word. Syllable targets range from 4 to 16 and bar counts from 2 to 4. Installation needs internet; later sessions use the bundled corpus and installed dictionary offline.


## Follow the code

`desk.py` contains the session in small steps. `collect_drafts()` builds a one-word-context Markov model from the prepared corpus and attempts up to 6,000 sentences.

Candidates are sorted by how many different theme words they contain. Matching is case-insensitive and whole-word based; it is not a semantic relevance score. Equal scores retain generation order. `pick_lines()` chooses the highest-ranked candidates with different ending words.

`save_session()` preserves the settings, all accepted candidates, the chosen verse and a word-by-word syllable audit.

`sound_tools.py` supplies the shared rules. `words_in()` keeps apostrophes inside contractions while separating punctuation. `sounds_for()` uses the first CMU dictionary pronunciation and caches lookups. `rhyme_part()` compares the final stressed vowel and following sounds. `inspect_line()` returns the total, ending, unknown words and individual word counts.

`prepare_corpus.py` shows the complete preparation of the training text. It removes ebook framing, headings and picture captions, normalizes spelling and punctuation, and keeps lines containing at least four words. Run `python prepare_corpus.py` to recreate the 820-line input from the original file already included in `corpus/`.

## What is saved

| Location | Contents |
| --- | --- |
| `Sessions/latest/` | Most recent interactive session; overwritten on the next interactive run |
| `session.txt` | Settings, origin, completeness and explained line checks |
| `verse.txt` | Current verse with its sound-check status |
| `candidates.tsv` | Ranked original drafts, keyword hits and selection flags |
| `line_checks.tsv` | Final text, syllables, rhyme results and unknown words |
| `settings.json` | Seed, target, bar count, keywords, random seed and search limits |



## The included example

With `light`, eight syllables, two bars, `birds love` and random seed 21, the program finds 12 candidates in 5,947 attempts. It selects “when i passed the birds in the night” and “come out the soot i love delight”. Both have eight dictionary syllables and different rhyming endings. The awkward second line illustrates why the editing step matters. These are unedited program outputs, not quotations from Blake and not peer-approved lyrics.

The source is William Blake's *Songs of Innocence and of Experience*, Project Gutenberg ebook 1934. The original notice and license are preserved. `corpus/SOURCE.md` records the source and preparation. The earlier prototype recorded retrieval on 8 October 2026; this release reuses that included copy. No copyrighted rap lyrics were added.
