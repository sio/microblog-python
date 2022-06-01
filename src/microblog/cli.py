'''
Command line interface
'''

import argparse
import os
from pathlib import Path
from textwrap import dedent

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
        self.microblog = MicroblogRepo(self.repo)

    def __repr__(self):
        return f'<{self.__class__.__name__} repo={self.repo.resolve()}>'

    def run(self):
        '''Execute action specified by args'''
        log.debug(f'Action {self.args.action} on {self}')
        action = getattr(self, self.args.action)
        result = action()
        return result

    def dump(self):
        for entry in self.microblog.entries():
            print('--- MICROBLOG ENTRY')
            print(entry)
            print(' -- Rendered HTML')
            print(entry.html)
            print()

    def html(self):
        html5 = dedent('''
            <!DOCTYPE html>
            <html>
            <head>
              <title>{title}</title>
              <meta charset='utf-8'>
              <meta name="viewport" content="width=device-width, initial-scale=1">
              <style>
                body {{
                  max-width: 30em;
                  margin: 0 auto 90vh auto!important;
                  padding: 0 2px;
                }}
                footer {{
                  text-align: right;
                }}
                footer a {{
                  color: gray;
                  text-decoration: none;
                }}
                article:target {{
                  background-color: #ffffe0;
                }}
                article {{
                  margin: 0 auto 1em auto;
                  padding: 0.5em;
                  border: solid;
                  border-radius: 1em;
                  border-color: rgba(100, 100, 100, .35);
                  border-width: 1px;
                }}
              </style>
            </head>
            <body>
              <h1>{title}</h1>
              {body}
            </body>
            </html>
            ''')
        title = self.microblog.config.get('microblog', {}).get('title', 'Microblog Title')
        body = []
        post = dedent('''
            <article id="{commit}">
            {body}
            <footer title="{commit}">
            <a href="#{commit}">{footer}</a></footer>
            </article>
            ''')
        for entry in self.microblog.entries():
            body.append(post.format(
                body=entry.html,
                footer=f'by {entry.author} on {entry.timestamp}',
                commit=entry.commit,
            ))

        output = self.args.output  # None is converted to sys.stdout automatically
        if output is not None:
            output = open(output, 'w')
        print(html5.format(
            title=title,
            body='\n'.join(body)
        ), file=output)
        if output:
            output.close()


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
    cmd.html = subcommands.add_parser(
        'html',
        help='Render full blog to one-page HTML document',
    )
    cmd.html.add_argument(
        'output',
        metavar='output.html',
        default=None,
        nargs='?',
        help='Save HTML output to this file. Stdout will be used if no file is specified'
    )
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
