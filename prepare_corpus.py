"""Rebuild the line-based training file from the included Gutenberg text."""
from pathlib import Path
import re
import unicodedata

home = Path(__file__).resolve().parent
raw = (home / "corpus/blake_original.txt").read_text(encoding="utf-8")

# Start at the first poem so the cover, contents and publication notes are out.
# Stop before the Gutenberg end marker; the original file retains its license.
poems = raw[raw.index("Piping down the valleys wild,"):]
poems = poems.split("*** END OF THE PROJECT GUTENBERG EBOOK")[0]
lines = []
for line in poems.splitlines():
    # Uppercase lines are poem titles. Picture captions are not poem lines.
    if line.isupper() or "[Picture:" in line:
        continue
    # Match the dictionary's plain spelling: fillèd -> filled; ’ -> '.
    line = unicodedata.normalize("NFKD", line.replace("’", "'"))
    line = line.encode("ascii", "ignore").decode("ascii")
    words = re.findall(r"[a-z]+(?:'[a-z]+)?", line.lower())
    # Very short lines offer few transitions; keep lines with at least 4 words.
    if len(words) >= 4:
        lines.append(" ".join(words))

# One record per verse line lets NewlineText learn where each line ends.
text = "\n".join(lines) + "\n"
(home / "corpus/blake_lines.txt").write_text(text, encoding="utf-8")
print(f"Prepared {len(lines)} lines from the included Blake text.")
