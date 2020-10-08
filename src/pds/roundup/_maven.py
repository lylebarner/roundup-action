# encoding: utf-8

'''🤠 PDS Roundup: Maven context'''

from . import Context
from .errors import InvokedProcessError, MissingEnvVarError
from .step import Step, StepName, NullStep, ChangeLogStep, DocPublicationStep, RequirementsStep
from .util import invoke, invokeGIT
from lxml import etree
import logging, os

_logger = logging.getLogger(__name__)

_mavenNamespace = 'http://maven.apache.org/POM/4.0.0'
_mavenSettingsNamespace = 'http://maven.apache.org/SETTINGS/1.0.0'
_xsiNamespace = 'http://www.w3.org/2001/XMLSchema-instance'
_mavenXSDLocation = 'https://maven.apache.org/xsd/settings-1.0.0.xsd'


class MavenContext(Context):
    '''A Maven context supports Maven (Java) software proejcts'''
    def __init__(self, cwd, environ):
        self.steps = {
            StepName.null:                NullStep,
            StepName.unitTest:            _UnitTestStep,
            StepName.integrationTest:     _IntegrationTestStep,
            StepName.changeLog:           ChangeLogStep,
            StepName.requirements:        RequirementsStep,
            StepName.docs:                _DocsStep,
            StepName.build:               _BuildStep,
            StepName.githubRelease:       _GitHubReleaseStep,
            StepName.artifactPublication: _ArtifactPublicationStep,
            StepName.docPublication:      _DocPublicationStep,
        }
        super(MavenContext, self).__init__(cwd, environ)


class _MavenStep(Step):
    '''☕️ Maven steps provide common conveniences for Maven and the Java environment'''
    def getVersionFromPOM(self):
        '''Get the version string from a ``pom.xml`` file'''
        cwd = self.assembly.context.cwd
        pomFile = os.path.join(cwd, 'pom.xml')
        if not os.path.isfile(pomFile):
            _logger.info('☡ No ``pom.xml`` found in %s; cannot determine version', cwd)
            return None
        pom = etree.parse(pomFile)
        versions = pom.xpath('/ns:project/ns:version', namespaces={'ns': _mavenNamespace})
        if len(versions) == 0:
            _logger.info('☡ No ``<version>`` found in %s; cannot determine version', pomFile)
            return None
        elif len(versions) > 1:
            _logger.info(
                '☡ More than one ``<version>`` found in %s; using the first one, but your POM is bad',
                pomFile
            )
        return versions[0].text.strip()

    def _createSettingsXML(self):
        '''Create a Maven-compatible ``settings.xml`` file for future use by
        ``Step``s created by this context.
        '''
        container = '/root/.m2'
        os.makedirs(container, exist_ok=True)
        settings = os.path.join(container, 'settings.xml')
        if os.path.isfile(settings): return

        env = self.assembly.context.environ
        username, password = env.get('ossrh_username'), env.get('ossrh_password')
        if not username: raise MissingEnvVarError('ossrh_username')
        if not password: raise MissingEnvVarError('ossrh_password')

        nsmap = {
            None: _mavenSettingsNamespace,
            'xsi': _xsiNamespace
        }
        prefix = f'{{{_mavenSettingsNamespace}}}'
        root = etree.Element(
            prefix + 'settings',
            attrib={f'{{{_xsiNamespace}}}schemaLocation': f'{_mavenSettingsNamespace} {_mavenXSDLocation}'},
            nsmap=nsmap
        )
        servers = etree.Element(prefix + 'servers')
        root.append(servers)
        server = etree.Element(prefix + 'server')
        servers.append(server)
        etree.SubElement(server, prefix + 'id').text = 'ossrh'
        etree.SubElement(server, prefix + 'username').text = username
        etree.SubElement(server, prefix + 'password').text = password
        tree = etree.ElementTree(root)
        with open(settings, 'wb') as out:
            tree.write(out, encoding='utf-8', xml_declaration=True, pretty_print=True)

    def invokeMaven(self, args):
        '''Invoke Maven, creating a ``settings.xml`` file each time as necessary'''
        self._createSettingsXML()
        argv = ['mvn'] + args
        return invoke(argv)


class _UnitTestStep(_MavenStep):
    def execute(self):
        _logger.debug('Maven unit test step')
        self.invokeMaven(['test'])


class _IntegrationTestStep(_MavenStep):
    def execute(self):
        _logger.debug('Maven integration test step; TBD')


class _DocsStep(_MavenStep):
    def execute(self):
        _logger.debug('Maven docs step')
        self.invokeMaven(['site'])


class _BuildStep(_MavenStep):
    def execute(self):
        _logger.debug('Maven build step')
        self.invokeMaven(['compile'])


class _GitHubReleaseStep(_MavenStep):
    def execute(self):
        _logger.debug('Maven GitHub release step')

        token = self.getToken()
        if not token:
            _logger.info('🤷‍♀️ No GitHub administrative token; cannot release to GitHub')
            return

        # 😮 TODO: Use Python GitHub API!
        # 🤷‍♀️ Thomas uses ``--unshallow``, but when I try that I get an error.
        # So we skip it for now:
        invokeGIT(['fetch', '--prune', '--tags'])
        tags = invokeGIT(['tag', '--list', '*dev*'])
        for tag in tags:
            tag = tag.strip()
            try:
                invokeGIT(['tag', '--delete', tag])
                invokeGIT(['push', '--delete', 'origin', tag])
            except InvokedProcessError:
                pass
        invoke(['maven-snapshot-release', '--token', token])


class _ArtifactPublicationStep(_MavenStep):
    def execute(self):
        _logger.debug('Maven artifact publication step; TBD')
        if self.assembly.isStable():
            self.invokeMaven(['-DremoveSnapshot=true', 'versions:set'])
            invokeGIT(['add', 'pom.xml'])
            version = self.getVersionFromPOM()
            self.invokeMaven(['--activate-profiles', 'release', 'clean', 'site', 'deploy'])
            invokeGIT(['git', 'tag', 'v' + version])
            invokeGIT(['git', 'push', '--tags'])
        else:
            version = self.getVersionFromPOM()
            self.invokeMaven(['clean', 'site', 'deploy'])


class _DocPublicationStep(DocPublicationStep):  # Could multiply inherit from _MavenStep too for semantics
    def getDocDir(self):
        return 'target/site'
