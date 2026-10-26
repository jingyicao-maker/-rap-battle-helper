# Generate short rhyme drafts, edit them, and save the sound checks.
from pathlib import Path
import argparse
import csv
import json
import random
import markovify
from sound_tools import words_in, rhyme_part, syllables_in, inspect_line

home = Path(__file__).resolve().parent


def ask_number(prompt, default, low, high):
    # Keep ordinary typing mistakes inside the prompt instead of ending the session.
    while True:
        answer = input(f'{prompt} [{default}]: ').strip() or str(default)
        if answer.isdigit() and low <= int(answer) <= high:
            return int(answer)
        print(f'Please enter a whole number from {low} to {high}.')


def collect_drafts(settings):
    corpus = (home / 'corpus/blake_lines.txt').read_text(encoding='utf-8')
    source_lines = set(corpus.splitlines())
    model = markovify.NewlineText(corpus, state_size=1)
    random.seed(settings['random_seed'])
    pool, seen = [], set()
    if not rhyme_part(settings['seed']):
        return [], 0
    # A finite attempt budget means a difficult seed cannot run indefinitely.
    for attempt in range(1, settings['attempt_limit'] + 1):
        line = model.make_sentence(tries=1)
        if not line or line in source_lines or line in seen:
            continue
        result = inspect_line(line, settings['target'], settings['seed'], settings['keywords'])
        if not result['target_met'] or not result['rhyme_met']:
            continue
        result['draft_id'] = len(pool) + 1
        pool.append(result)
        seen.add(line)
        if len(pool) == settings['pool_limit']:
            break
    # Equal scores keep their generation order. Keywords rank exact word overlap,
    # not meaning, grammar or a line's suitability for performance.
    return sorted(pool, key=lambda row: row['keyword_hits'], reverse=True), attempt


def pick_lines(pool, bars):
    chosen, endings = [], set()
    for draft in pool:
        if draft['ending'] not in endings:
            chosen.append(draft)
            endings.add(draft['ending'])
        if len(chosen) == bars:
            break
    return chosen


def write_table(path, rows, fields):
    # Write a header even when no drafts passed, so an empty result is explicit.
    with path.open('w', encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fields, delimiter='\t', extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def save_session(settings, pool, chosen, revised, attempts, destination):
    destination.mkdir(parents=True, exist_ok=True)
    chosen_ids = {row['draft_id'] for row in chosen}
    for draft in pool:
        draft['selected'] = draft['draft_id'] in chosen_ids
    checks = [inspect_line(line, settings['target'], settings['seed'], settings['keywords']) for line in revised]
    endings = [row['ending'] for row in checks]
    complete = len(checks) == settings['bars']
    passes = (complete and all(row['target_met'] and row['rhyme_met'] for row in checks)
              and len(set(endings)) == len(endings))
    edited = any(new != old['line'] for new, old in zip(revised, chosen))
    status = 'SOUND CHECKS PASS' if passes else 'NEEDS REVISION / INCOMPLETE'
    report = ['RHYME DESK — SESSION', status,
              f"Seed: {settings['seed']} | Target: {settings['target']} syllables | Bars: {len(checks)}/{settings['bars']}",
              f"Theme words: {', '.join(settings['keywords']) or '(none)'}",
              f"Attempts: {attempts}/{settings['attempt_limit']} | Sound-valid drafts: {len(pool)}",
              'Origin: Markov drafts with user-entered edits.' if edited else 'Origin: unedited Markov drafts.', '', 'CURRENT VERSE']
    report += revised or ['No suitable lines found. Try another seed or syllable target.']
    report += ['', 'LINE CHECKS']
    for i, row in enumerate(checks, 1):
        report += [f"{i}. syllables={row['syllables']}; target={row['target_met']}; rhyme={row['rhyme_met']}",
                   '   ' + row['word_counts']]
    report += ['', f'Distinct endings: {len(set(endings)) == len(endings)}',
               'A sound-check pass is not a judgement of rhythm, grammar, originality or quality.',
               'Read the verse aloud and revise it.']
    (destination / 'session.txt').write_text('\n'.join(report) + '\n', encoding='utf-8')
    (destination / 'verse.txt').write_text(status + '\n\n' + '\n'.join(revised) + '\n', encoding='utf-8')
    (destination / 'settings.json').write_text(json.dumps(settings, indent=2), encoding='utf-8')
    fields = ['draft_id', 'line', 'ending', 'syllables', 'keyword_hits', 'matched_keywords', 'selected']
    write_table(destination / 'candidates.tsv', pool, fields)
    write_table(destination / 'line_checks.tsv', checks,
                ['line', 'ending', 'syllables', 'target_met', 'rhyme_met', 'unknown_words', 'word_counts'])
    return '\n'.join(report)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo', action='store_true', help='Reproduce the supplied unedited two-bar example')
    args = parser.parse_args()
    settings = {'seed': 'light', 'target': 8, 'keywords': ['birds', 'love'], 'bars': 2,
                'random_seed': 21, 'attempt_limit': 6000, 'pool_limit': 12}
    if not args.demo:
        print('RHYME DESK\n\nPress Enter to use an example value given in []. \nCtrl+C to quit the session.\n\n')
        while True:
            seed = input('One end-rhyme word [light]: ').strip().lower() or 'light'
            if words_in(seed) == [seed] and rhyme_part(seed):
                settings['seed'] = seed
                break
            print('Use one English word with a dictionary pronunciation, such as light or day.')
        settings['target'] = ask_number('Syllables per line', 8, 4, 16)
        settings['bars'] = ask_number('Number of bars', 2, 2, 4)
        theme = input('Theme words (with spaces) [example: birds love; enter - for none]: ').strip() or 'birds love'
        settings['keywords'] = sorted(set(words_in(theme)))
        settings['random_seed'] = ask_number('Random seed (same settings reproduce the draft)', 21, 0, 9999)
    vocabulary = (home / 'wordbank/words.txt').read_text(encoding='utf-8').split()
    ideas = [word for word in sorted(set(vocabulary)) if word != settings['seed']
             and rhyme_part(word) == rhyme_part(settings['seed']) and syllables_in(word) <= 2]
    print('Rhyme ideas from the small word bank:', ', '.join(ideas) or '(none)')
    print('Building drafts; some combinations may produce fewer lines than requested...')
    pool, attempts = collect_drafts(settings)
    chosen = pick_lines(pool, settings['bars'])
    for row in pool:
        marker = '*' if row in chosen else ' '
        print(f"{marker} {row['draft_id']:>2}. {row['line']} [{row['keyword_hits']} theme hits]")
    if not args.demo and pool:
        while True:
            answer = input('Choose draft IDs separated by spaces, or Enter for the starred selection: ').strip()
            if not answer:
                break
            ids = answer.split()
            available = {str(row['draft_id']): row for row in pool}
            if (len(ids) == min(settings['bars'], len(pool)) and len(set(ids)) == len(ids)
                    and all(value in available for value in ids)):
                chosen = [available[value] for value in ids]
                break
            print('Choose the requested number of different IDs from the displayed pool.')
    revised = [row['line'] for row in chosen]
    if not args.demo and chosen:
        print('\nEdit the selected lines below. Enter keeps a draft unchanged.')
        for i, line in enumerate(revised):
            revised[i] = input(f'{i + 1}. {line}\nReplacement: ').strip() or line
    # Keep the reproducible demonstration separate from later personal experiments.
    destination = home / 'Sessions' / ('demo' if args.demo else 'latest')
    print('\n' + save_session(settings, pool, chosen, revised, attempts, destination))
    print('\nSaved to', destination)


if __name__ == '__main__':
    main()
