'''
Pelican plugin for git microblogs
'''

import logging

from pkg_resources import resource_string
from pelican import signals
from pelican.generators import Generator, PelicanTemplateNotFound

from microblog import MicroblogRepo


log = logging.getLogger(__name__)


def get_generators(pelican):
    return MicroblogGenerator


def register():
    signals.get_generators.connect(get_generators)


class MicroblogGenerator(Generator):
    '''Read git microblog and generate output with Pelican'''

    def get_template(self, name):
        try:
            return super().get_template(name)
        except PelicanTemplateNotFound as e:
            code = resource_string(__name__, 'templates/{}.html'.format(name))
            if not code:
                raise e
            log.warning(
                ('Theme provides no template for {!r}, '
                 'falling back to a very basic one').format(name)
            )
            template = self.env.from_string(code.decode('utf-8'))
            template.name = name
            self._templates[name] = template
            return template

    def generate_context(self):
        if 'MICROBLOG_REPO' not in self.settings:
            raise ValueError('required pelican variable is not defined: MICROBLOG_REPO')
        self.microblog = MicroblogRepo(self.settings['MICROBLOG_REPO'])
        self.index_url = self.settings.get(
            'MICROBLOG_INDEX_URL',
            'micro/'
        )
        self.index_dest = self.settings.get(
            'MICROBLOG_INDEX_SAVE_AS',
            self.index_url if self.index_url.endswith('.html') else f'{self.index_url}/index.html'
        )
        self.micro_url = self.settings.get(
            'MICROBLOG_PAGE_URL',
            'micro/{commit}/'
        )
        self.micro_dest = self.settings.get(
            'MICROBLOG_PAGE_SAVE_AS',
            self.micro_url if self.micro_url.endswith('.html') else f'{self.micro_url}/index.html'
        )
        pagination = self.settings['PAGINATED_TEMPLATES']
        if 'micros' not in pagination:
            pagination['micros'] = None  # Use default settings

    def generate_output(self, writer):
        context = self.context.copy()
        context['microblog'] = self.microblog
        entries = list(self.microblog.entries())
        writer.write_file(
            name=self.index_dest,
            template=self.get_template('micros'),
            context=context,
            relative_urls=self.settings['RELATIVE_URLS'],
            paginated={'micros': entries},
            template_name='micros',
            url=self.index_url,
        )
        for entry in entries:
            context['micro'] = entry
            writer.write_file(
                name=self.micro_dest.format(commit=entry.commit),
                template=self.get_template('micro'),
                context=context,
                relative_urls=self.settings['RELATIVE_URLS'],
                template_name='micro',
                url=self.micro_url.format(commit=entry.commit),
            )
