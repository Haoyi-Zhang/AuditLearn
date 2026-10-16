"""Verify exact regeneration of the consumed two-clock schematic."""
from pathlib import Path
import subprocess
import sys
import tempfile
HERE=Path(__file__).resolve().parent
if __name__=='__main__':
    with tempfile.TemporaryDirectory(prefix='auditlearn-figures-') as tmp:
        out=Path(tmp)
        subprocess.run([sys.executable,'-B',str(HERE/'draw_schematics.py'),'--output',str(out)],check=True,timeout=60)
        if (out/'clocks.pdf').read_bytes() != (HERE/'clocks.pdf').read_bytes():
            raise RuntimeError('Stale or nondeterministic two-clock schematic')
    print('Two-clock schematic regenerates exactly.')
