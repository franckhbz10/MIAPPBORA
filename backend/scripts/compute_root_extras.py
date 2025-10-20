import re
from pathlib import Path

root = Path(__file__).resolve().parents[2]
backend = root / 'backend'

root_freeze = root / 'requirements.root.frozen.txt'
backend_freeze = backend / 'requirements.backend.frozen.txt'
out_file = backend / 'requirements.root-extras.txt'

name_re = re.compile(r'^([A-Za-z0-9_.\-]+)\s*(?:==|>=|<=|~=|!=|===)')

def parse_names(lines):
    names = {}
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('-'):
            continue
        m = name_re.match(line)
        if m:
            names[m.group(1).lower()] = line
    return names

rf = root_freeze.read_text(encoding='utf-8').splitlines()
bf = backend_freeze.read_text(encoding='utf-8').splitlines()

root_pkgs = parse_names(rf)
back_pkgs = parse_names(bf)

extras = [spec for name, spec in root_pkgs.items() if name not in back_pkgs]
extras.sort(key=str.lower)

out_file.write_text('\n'.join(extras) + '\n', encoding='utf-8')
print(f'Extras written to {out_file} (count={len(extras)})')
