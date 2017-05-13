#!/usr/bin/env python3
import argparse
import gzip
import pathlib
import requests
from edict import parser
from edict import db


_DL_URL = 'http://ftp.monash.edu/pub/nihongo/edict2.gz'
_RAW_PATH = pathlib.Path('~/.local/cache/edict2.txt').expanduser()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser('Look up words in edict2 dictionary')
    parser.add_argument('word')
    parser.add_argument('-w', '--wild', action='store_true')
    return parser.parse_args()


def download() -> str:
    print('Downloading dictionary file...', flush=True)
    data = requests.get(_DL_URL).content
    data = gzip.decompress(data)
    return data.decode('euc-jp')


def create_db_if_needed() -> None:
    if not _RAW_PATH.exists():
        data = download()
        _RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
        _RAW_PATH.write_text(data)
    db.init()
    if not db.exists():
        with _RAW_PATH.open('r') as handle:
            db.put_entries(entry for entry in parser.parse(list(handle)))


def main() -> None:
    args = parse_args()
    word: str = args.word
    wild: bool = args.wild
    create_db_if_needed()

    if wild:
        query = '%' + '%'.join(word) + '%'
    else:
        query = word

    for kanji in sorted(db.search(query), key=lambda kanji: len(kanji.kanji)):
        print(kanji.kanji)
        print(kanji.kana)
        for glossary in kanji.entry.glossaries:
            print(glossary.english)
        print()


if __name__ == '__main__':
    main()
