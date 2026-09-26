"""Regenerate the v2 progress cards: crops -> HTML -> PNG (headless Chrome) -> size check.

    python tools/summary/v2/build.py            # all cards
    python tools/summary/v2/build.py 01 07      # only cards whose file name starts with these
"""
import glob
import os
import runpy
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from common2 import OUT, make_crops  # noqa: E402

CHROME = ['google-chrome', '--headless=new', '--disable-gpu', '--hide-scrollbars', '--force-device-scale-factor=2',
          '--window-size=1080,1350', '--virtual-time-budget=8000']


def main(only):
    make_crops()
    scripts = sorted(glob.glob(os.path.join(HERE, 'card*.py')))
    for s in scripts:
        nn = os.path.basename(s)[4:6]
        if only and nn not in only:
            continue
        runpy.run_path(s, run_name='__main__')
    from PIL import Image
    bad = []
    for html in sorted(glob.glob(OUT + '[0-9][0-9]-*.html')):
        nn = os.path.basename(html)[:2]
        if only and nn not in only:
            continue
        png = html[:-5] + '.png'
        subprocess.run(CHROME + [f'--screenshot={png}', 'file://' + html], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        size = Image.open(png).size
        print(os.path.basename(png), size)
        if size != (2160, 2700):
            bad.append(png)
    if bad:
        sys.exit(f'wrong size: {bad}')


if __name__ == '__main__':
    main(sys.argv[1:])
