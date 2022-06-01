'''
Command line interface
'''

import argparse
import os
from pathlib import Path

from . import logging
from .logging import log
from .repo import MicroblogRepo


def main(*a, **ka):
    '''CLI entrypoint'''
    logging.setup()
    args = parse_args(*a, **ka)
    cli = MicroblogCLI(args)
    cli.run()


class MicroblogCLI:

    _repo: str = ''
    @property
    def repo(self):
        return Path(self._repo)
    @repo.setter
    def repo(self, value):
        self._repo = str(value)

    def __init__(self, args):
        self.args = args
        self.repo = self.args.repo

    def __repr__(self):
        return f'<{self.__class__.__name__} repo={self.repo.resolve()}>'

    def run(self):
        '''Execute action specified by args'''
        log.debug(f'Action {self.args.action} on {self}')
        action = getattr(self, self.args.action)
        result = action()
        return result

    def dump(self):
        microblog = MicroblogRepo(self.repo)
        for entry in microblog.entries():
            print('--- MICROBLOG ENTRY')
            print(entry)
            print(' -- Rendered HTML')
            print(entry.html)
            print()


def parse_args(*a, **ka):
    parser = argparse.ArgumentParser(
        description='Interact with microblogs stored in git commit messages',
        epilog='Licensed under Apache License, version 2.0'
    )
    parser.add_argument(
        '--repo',
        metavar='PATH',
        type=Path,
        default=os.getenv('MICROBLOG_REPO', '.'),
        help=(
            'Path to the cloned git repo containing a microblog. '
            'Default: $MICROBLOG_REPO or "."'
        ),
    )
    subcommands = parser.add_subparsers(
        dest='action',
        required=True,
        metavar='SUBCOMMAND',
    )
    cmd = argparse.Namespace()
    cmd.dump = subcommands.add_parser(
        'dump',
        help='Dump microblog to stdout',
    )

    args = parser.parse_args(*a, **ka)

    git = args.repo / '.git'
    if not git.exists() or not git.is_dir():
        parser.error(f'not a git repository: {args.repo}')
    log.info('Opening microblog from git repository: %s', args.repo.resolve())
    return args
