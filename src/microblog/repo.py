'''
Reading microblog from git commit history
'''

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
)


@dataclass
class MicroblogEntry:
    timestamp: datetime
    raw: str
    author: str
    markup: str
    metadata: Mapping

    def __post_init__(self):
        if self.markup.lower() not in renderers:
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

    def entries(self):
        '''Yield MicroblogEntries in no particular order'''
        repo = self.repo
        for commit in repo.iter_commits(repo.head.commit):
            if any(commit.tree != parent.tree for parent in commit.parents):
                log.debug(f'Skipping non-empty commit {commit}')
                continue
            yield self.entry(commit)

    def entry(self, commit) -> MicroblogEntry:
        '''Read MicroblogEntry from commit'''
        return commit  # FIXME

    def parse_metadata(self, text) -> MicroblogMetadata:
        '''Find MicroblogMetadata in free-form text'''
