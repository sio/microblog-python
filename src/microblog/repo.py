'''
Reading microblog from git commit history
'''

import re
from collections import UserDict
from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import git
import toml

from .logging import log


renderers = dict(
    plaintext = str,
    lowercase = str.lower,
    uppercase = str.upper,
    wikitext  = str,  # TODO
    markdown  = str,  # TODO
)


@dataclass
class MicroblogEntry:
    timestamp: datetime
    raw: str
    author: str
    metadata: Mapping
    commit: str
    markup: str = 'plaintext'

    def __post_init__(self):
        self.markup = self.metadata.get('markup', self.markup).lower()
        if self.markup not in renderers:
            raise ValueError(f'unsupported markup format: {self.markup}')

    @property
    def html(self):
        if not hasattr(self, '_html'):
            self._html = self.render()
        return self._html

    def render(self):
        renderer = self.renderers[self.markup]
        self._html = renderer(self.raw)
        return self._html


class MicroblogMetadata(UserDict):
    '''Case-insensitive mapping object for metadata'''
    def __getitem__(self, key):
        return super().__getitem__(key.lower())

    def __setitem__(self, key, value):
        return super().__setitem__(key.lower(), value)


class MicroblogRepo:

    def __init__(self, repo_path):
        self.path = Path(repo_path)
        self.repo = git.Repo(repo_path)
        self.config = self._load_config()

    def _load_config(self):
        config = self.path / 'microblog.toml'
        if config.exists():
            with config.open() as c:
                return toml.load(c)
        return dict()

    def entries(self, start=None):
        '''Yield MicroblogEntries starting from the provided commit'''
        repo = self.repo
        if start is None:
            start = repo.head.commit
        for commit in repo.iter_commits(start):
            if any(commit.tree != parent.tree for parent in commit.parents):
                log.debug(f'Skipping non-empty commit {commit}')
                continue
            yield self.entry(commit)

    def entry(self, commit) -> MicroblogEntry:
        '''Read MicroblogEntry from commit'''
        raw, metadata = self.parse_metadata(commit.message)
        if 'markup' in self.config.get('default', {}) and 'markup' not in metadata:
            metadata['markup'] = self.config['default']['markup']
        return MicroblogEntry(
            timestamp=commit.committed_datetime,
            author=str(commit.author),
            raw=raw,
            metadata=metadata,
            commit=str(commit),
        )

    def parse_metadata(self, text) -> [str, MicroblogMetadata]:
        '''Separate MicroblogMetadata from free-form text'''
        metadata_prefix = 'Microblog-'
        metadata_regex = re.compile(rf'^{metadata_prefix}(\w+)\:(.*)')
        raw_lines = list()
        metadata = MicroblogMetadata()
        for line in reversed(text.splitlines()):
            if raw_lines:  # we have already seen a non-metadata line
                raw_lines.append(line)
                continue
            match = metadata_regex.search(line)
            if not match and line.strip():  # this is the first non-metadata line
                raw_lines.append(line)
            if not match:
                continue
            key, value = match.groups()
            metadata[key] = value.strip()
        return '\n'.join(reversed(raw_lines)), metadata
