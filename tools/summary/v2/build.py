"""Regenerate the v2 progress cards: crops -> HTML -> PNG (headless Chrome) -> size check.

    python tools/summary/v2/build.py              # all cards, Korean and English
    python tools/summary/v2/build.py 01 07        # only cards whose file name starts with these
    python tools/summary/v2/build.py --lang en    # one language (ko: NN-slug.html, en: NN-slug.en.html)
"""
import glob
import os
import runpy
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import common2  # noqa: E402  (puts tools/summary on sys.path)
import common  # noqa: E402
from common2 import OUT, make_crops  # noqa: E402

CHROME = ['google-chrome', '--headless=new', '--disable-gpu', '--hide-scrollbars', '--force-device-scale-factor=2',
          '--window-size=1080,1350', '--virtual-time-budget=8000']
LANGS = ('ko', 'en')


def outputs(lang):
    """the rendered HTML files of one language: 'NN-slug.html' (ko) or 'NN-slug.en.html' (en)."""
    for html in sorted(glob.glob(OUT + '[0-9][0-9]-*.html')):
        if html.endswith('.en.html') == (lang == 'en'):
            yield html


def main(only, langs):
    make_crops()
    scripts = sorted(glob.glob(os.path.join(HERE, 'card*.py')))
    for lang in langs:
        common2.set_lang(lang)
        for s in scripts:
            nn = os.path.basename(s)[4:6]
            if only and nn not in only:
                continue
            common._pid[0] = common2._qid[0] = 0  # SVG gradient ids restart per card: same file whatever else is built
            runpy.run_path(s, run_name='__main__')
    from PIL import Image
    bad = []
    for lang in langs:
        for html in outputs(lang):
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
    args = sys.argv[1:]
    langs = LANGS
    if '--lang' in args:
        i = args.index('--lang')
        langs = (args[i + 1],)
        assert langs[0] in LANGS, langs
        del args[i:i + 2]
    main(args, langs)
