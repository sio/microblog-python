'''
Renderers
'''

import html
import re

import markdown as md


URL = re.compile(r'((?:https?|mailto|ftp|gopher|gemini)://\S+)', re.IGNORECASE)


def split_header(text):
    '''Split header from git commit message (if any)'''
    lines = text.splitlines()
    if len(lines) > 2 and lines[1] == '' and len(lines[0]) <= 100:
        header = lines[0]
        body = '\n'.join(lines[2:])
    else:
        header = ''
        body = text
    return header, body


def plaintext(text, escape=html.escape, drop_header=False):
    '''Render HTML from plain text'''
    header, body = split_header(text)
    parts = []
    if header and not drop_header:
        parts.append(f'<h1>{escape(header)}</h1>')
    for paragraph in body.split('\n\n'):
        if not paragraph.strip():
            continue
        chunks = []
        for chunk in URL.split(paragraph):
            if not chunk.strip():
                continue
            if URL.fullmatch(chunk):
                chunks.append(f'<a href="{chunk}">{escape(chunk)}</a>')
            else:
                chunks.append(escape(chunk))
        paragraph = '\n'.join(chunks)
        parts.append(f'<p>{paragraph}</p>')
    return '\n'.join(parts)


def lowercase(text, drop_header=False):
    return plaintext(text, escape=lambda x: html.escape(x).lower())


def uppercase(text, drop_header=False):
    return plaintext(text, escape=lambda x: html.escape(x).upper())


def wikitext(text, drop_header=False):  # TODO: implement a renderer
    return plaintext(text)


_markdown_extension_configs={
    'markdown.extensions.codehilite': {
        'css_class': 'highlight',
        'guess_lang': False,
    },
    'markdown.extensions.extra': {},
    'markdown.extensions.meta': {},
    'markdown.extensions.sane_lists': {},
    'pymdownx.magiclink': {},
    'pymdownx.saneheaders': {},
}
Markdown = md.Markdown(
    output_format='html5',
    extensions=list(_markdown_extension_configs),
    extension_configs=_markdown_extension_configs,
)
def markdown(text, drop_header=False):
    '''Render HTML from Markdown text'''
    header, body = split_header(text)
    if header and not header.strip().startswith('#'):
        header = f'# {header}'
    if drop_header:
        header = ''
    return Markdown.convert(f'{header}\n\n{body}')
