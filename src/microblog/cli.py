'''
Command line interface
'''

import argparse
import os
import sys
import toml
from dataclasses import dataclass, asdict
from pathlib import Path
from tempfile import NamedTemporaryFile

from . import logging
from .logging import log
from .repo import MicroblogRepo


def main(*a, **ka):
    '''CLI entrypoint'''
    logging.setup()
    args = parse_args(*a, **ka)
    cli = MicroblogCLI(args)
    cli.run()


@dataclass
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
        self._load()
        if not self._repo and self.args.action != 'open':
            log.error('Repository was not specified, use "open" subcommand first')
            sys.exit(1)

    def __del__(self):
        if self._repo:
            self._dump()

    def _dump(self):
        '''Dump state to persistent storage'''
        statefile = self.args.state.resolve()
        log.debug(f'Saving {self} to {statefile}')
        with NamedTemporaryFile(
                mode='w',
                prefix=__package__,
                dir=statefile.parent,
                delete=False,
        ) as temp:
            toml.dump(asdict(self), temp)
            temp.flush()
        os.replace(temp.name, statefile)  # atomic because we stay on the same filesystem

    def _load(self):
        '''Load state from persistent storage'''
        if not self.args.state.exists():
            return
        with self.args.state.open() as state:
            saved = toml.load(state)
        for key, value in saved.items():
            setattr(self, key, value)
        log.debug(f'Loaded {self} from {self.args.state}')
        self._validate()

    def _validate(self):
        if not self.repo.exists() or not self.repo.is_dir():
            raise ValueError(f'directory does not exist: {self.repo}')

    def run(self):
        '''Execute action specified by args'''
        log.debug(f'Executing {self.args.action} on {self}')
        action = getattr(self, self.args.action)
        result = action()
        self._validate()
        return result

    def open(self):
        '''Remember which repo we will work with from now on'''
        self.repo = self.args.repo

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
        '--state',
        metavar='PATH',
        type=Path,
        default=os.getenv('MICROBLOG_STATE', './microblog.state'),
        help=(
            'Path to file that stores persistent state between runs. '
            'Default: $MICROBLOG_STATE or "./microblog.state"'
        ),
    )
    subcommands = parser.add_subparsers(
        dest='action',
        required=True,
        metavar='SUBCOMMAND',
    )
    cmd = argparse.Namespace()
    cmd.open = subcommands.add_parser(
        'open',
        help='Open microblog from cloned git repository'
    )
    cmd.open.add_argument(
        'repo',
        metavar='PATH',
        type=Path,
        help='Path to git repository on local machine',
    )
    cmd.dump = subcommands.add_parser(
        'dump',
        help='Dump microblog to stdout',
    )

    args = parser.parse_args(*a, **ka)

    if not (args.state.parent.exists() and args.state.parent.is_dir()):
        parser.error(f'not a directory: {args.state.parent}')
    if args.state.is_dir():
        parser.error(f'directory exists in place of state file: {args.state}')

    if args.action == 'open':
        git = args.repo / '.git'
        if not git.exists() or not git.is_dir():
            parser.error(f'not a git repository: {args.repo}')
    return args
