"""After restoring a backup on another computer (or for another Windows user): puts the keys from the backup's
"Ключі (відкрито).json" back into the program's vault, where Windows encrypts them for this user.

    python app/tools/restore_keys.py "path to Ключі (відкрито).json"

Prints only which keys went in, never their values. Delete the JSON file afterwards."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__)
        return 2
    from studio.vault import vault
    values = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    done = []
    for name, value in values.items():
        if isinstance(value, str) and value:  # every name the backup carried (backup.py takes the whole vault)
            vault.set(name, value)
            done.append(name)
    print("Restored:", ", ".join(done) or "nothing")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
