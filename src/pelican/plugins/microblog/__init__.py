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
        self.url_pattern = self.settings.get(
            'MICROBLOG_URL',
            'micro/'
        )
        self.dest_pattern = self.settings.get(
            'MICROBLOG_SAVE_AS',
            self.url_pattern if self.url_pattern.endswith('.html') else f'{self.url_pattern}/index.html'
        )
        pagination = self.settings['PAGINATED_TEMPLATES']
        if 'microblog' not in pagination:
            pagination['microblog'] = None  # Use default settings

    def generate_output(self, writer):
        entries = list(self.microblog.entries())
        writer.write_file(
            name=self.dest_pattern,
            template=self.get_template('microblog'),
            context=self.context,
            relative_urls=self.settings['RELATIVE_URLS'],
            paginated={'microblog': entries},
            template_name='microblog',
            url=self.url_pattern,
        )
