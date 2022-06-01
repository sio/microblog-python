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
    default_markup = 'plaintext'

    def __post_init__(self):
        self.markup = self.metadata.get('markup', self.default_markup).lower()
        if self.markup not in renderers:
            raise ValueError(f'unsupported markup format: {self.markup}')

    @property
    def text(self):
        if not hasattr(self, '_text'):
            self._text = self.render()
        return self._text

    def render(self):
        renderer = self.renderers[self.markup]
        self._text = renderer(self.raw)
        return self._text


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
        return MicroblogEntry(
            timestamp=commit.committed_datetime,
            author=commit.author,
            raw=raw,
            metadata=metadata,
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
