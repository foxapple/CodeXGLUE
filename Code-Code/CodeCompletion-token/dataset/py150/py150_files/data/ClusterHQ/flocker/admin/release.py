# -*- test-case-name: admin.test.test_release,admin.functional.test_release -*-  # noqa
# Copyright ClusterHQ Inc.  See LICENSE file for details.

"""
Helper utilities for the Flocker release process.

XXX This script is not automatically checked by buildbot. See
https://clusterhq.atlassian.net/browse/FLOC-397
"""

import yaml
import os
import sys
import tempfile
import virtualenv

from datetime import datetime
from subprocess import check_call

from boto.s3.website import RoutingRules, RoutingRule

from effect import (
    Effect, sync_perform, ComposedDispatcher)
from effect.do import do

from characteristic import attributes
from git import GitCommandError, Repo
from pytz import UTC

from twisted.python.filepath import FilePath
from twisted.python.usage import Options, UsageError
from twisted.python.constants import Names, NamedConstant
from twisted.web import template

import flocker
from flocker.common.version import get_package_key_suffix
from flocker.provision._effect import sequence, dispatcher as base_dispatcher

from flocker.common.version import (
    get_doc_version,
    is_pre_release,
    is_release,
    is_weekly_release,
)
from flocker.provision._install import ARCHIVE_BUCKET

from .aws import (
    boto_dispatcher,
    UpdateS3ErrorPage,
    ListS3Keys,
    DeleteS3Keys,
    CopyS3Keys,
    DownloadS3KeyRecursively,
    UploadToS3,
    UploadToS3Recursively,
    CreateCloudFrontInvalidation,
    UpdateS3RoutingRules
)

from .yum import (
    yum_dispatcher,
    CreateRepo,
    DownloadPackagesFromRepository,
)

from .packaging import available_distributions, DISTRIBUTION_NAME_MAP


DEV_ARCHIVE_BUCKET = 'clusterhq-dev-archive'


class NotTagged(Exception):
    """
    Raised if publishing to production and the version being published version
    isn't tagged.
    """


class NotARelease(Exception):
    """
    Raised if trying to publish documentation to, or packages for a version
    that isn't a release.
    """


class DocumentationRelease(Exception):
    """
    Raised if trying to upload packages for a documentation release.
    """


class Environments(Names):
    """
    The environments that documentation can be published to.
    """
    PRODUCTION = NamedConstant()
    STAGING = NamedConstant()


class TagExists(Exception):
    """
    Raised if trying to release a version for which a tag already exists.
    """


class BranchExists(Exception):
    """
    Raised if trying to release a version for which a branch already exists.
    """


class MissingPreRelease(Exception):
    """
    Raised if trying to release a pre-release for which the previous expected
    pre-release does not exist.
    """


@attributes([
    'documentation_bucket',
    'cloudfront_cname',
    'dev_bucket',
])
class DocumentationConfiguration(object):
    """
    The configuration for publishing documentation.

    :ivar bytes documentation_bucket: The bucket to publish documentation to.
    :ivar bytes cloudfront_cname: a CNAME associated to the cloudfront
        distribution pointing at the documentation bucket.
    :ivar bytes dev_bucket: The bucket buildbot uploads documentation to.
    """

DOCUMENTATION_CONFIGURATIONS = {
    Environments.PRODUCTION:
        DocumentationConfiguration(
            documentation_bucket="clusterhq-docs",
            cloudfront_cname="docs.clusterhq.com",
            dev_bucket="clusterhq-staging-docs"),
    Environments.STAGING:
        DocumentationConfiguration(
            documentation_bucket="clusterhq-staging-docs",
            cloudfront_cname="docs.staging.clusterhq.com",
            dev_bucket="clusterhq-staging-docs"),
}


def parse_routing_rules(routing_config, hostname):
    """
    Parse routing rule description.

    The configuration is a dictionary. The top-level keys are common prefixes
    for the rules in them. Each top-level key maps to a dictionary that maps
    the rest of a prefix to the redirection target. A redirection target is a
    dictionary of keyword arguments to ``boto.s3.website.Redirect``. If no
    hostname is provided in the redirection target, then the passed hostname is
    used, and the common prefix is prepended to the redirection target.

    :param routing_config: ``dict`` containing the routing configuration.
    :param bytes hostname: The hostname the bucket is hosted at.

    :return: Parsed routing rules.
    :rtype: ``boto.s3.website.RoutingRules``
    """
    rules = []
    for prefix, relative_redirects in routing_config.items():
        for postfix, destination in relative_redirects.items():
            destination.setdefault('http_redirect_code', '302')
            destination['protocol'] = 'https'
            if 'hostname' not in destination.keys():
                destination['hostname'] = hostname
                for key in ('replace_key', 'replace_key_prefix'):
                    if key in destination:
                        destination[key] = prefix + destination[key]
            rules.append(RoutingRule.when(
                key_prefix=prefix+postfix,
            ).then_redirect(**destination))

    # Sort the rules in reverse order of prefix to match, so that
    # long-match wins.
    return RoutingRules(
        sorted(rules, key=lambda rule: rule.condition.key_prefix,
               reverse=True)
    )


@do
def publish_docs(flocker_version, doc_version, environment, routing_config):
    """
    Publish the Flocker documentation. The documentation for each version of
    Flocker is uploaded to a development bucket on S3 by the build server and
    this copies the documentation for a particular ``flocker_version`` and
    publishes it as ``doc_version``. Attempting to publish documentation to a
    staging environment as a documentation version publishes it as the version
    being updated.

    :param bytes flocker_version: The version of Flocker to publish the
        documentation for.
    :param bytes doc_version: The version to publish the documentation as.
    :param Environments environment: The environment to publish the
        documentation to.
    :param dict routing_config: The loaded routing configuration (see
        ``parse_routing_rules`` for details).
    :raises NotARelease: Raised if trying to publish to a version that isn't a
        release.
    :raises NotTagged: Raised if publishing to production and the version being
        published version isn't tagged.
    """
    if not (is_release(doc_version) or
            is_weekly_release(doc_version) or
            is_pre_release(doc_version)):
        raise NotARelease()

    if environment == Environments.PRODUCTION:
        if get_doc_version(flocker_version) != doc_version:
            raise NotTagged()
    configuration = DOCUMENTATION_CONFIGURATIONS[environment]

    dev_prefix = 'release/flocker-%s/' % (flocker_version,)
    version_prefix = 'en/%s/' % (get_doc_version(doc_version),)

    is_dev = not is_release(doc_version)
    if is_dev:
        stable_prefix = "en/devel/"
    else:
        stable_prefix = "en/latest/"

    # Get the list of keys in the new documentation.
    new_version_keys = yield Effect(
        ListS3Keys(bucket=configuration.dev_bucket,
                   prefix=dev_prefix))

    # Get the list of keys already existing for the given version.
    # This should only be non-empty for documentation releases.
    existing_version_keys = yield Effect(
        ListS3Keys(bucket=configuration.documentation_bucket,
                   prefix=version_prefix))

    existing_latest_keys = yield Effect(
        ListS3Keys(bucket=configuration.documentation_bucket,
                   prefix=stable_prefix))

    # Copy the new documentation to the documentation bucket at the
    # versioned prefix, i.e. en/x.y.z
    yield Effect(
        CopyS3Keys(source_bucket=configuration.dev_bucket,
                   source_prefix=dev_prefix,
                   destination_bucket=configuration.documentation_bucket,
                   destination_prefix=version_prefix,
                   keys=new_version_keys))

    # Copy the new documentation to the documentation bucket at the
    # stable prefix, e.g. en/latest
    yield Effect(
        CopyS3Keys(source_bucket=configuration.dev_bucket,
                   source_prefix=dev_prefix,
                   destination_bucket=configuration.documentation_bucket,
                   destination_prefix=stable_prefix,
                   keys=new_version_keys))

    # Delete any keys that aren't in the new documentation.
    yield Effect(
        DeleteS3Keys(bucket=configuration.documentation_bucket,
                     prefix=version_prefix,
                     keys=existing_version_keys - new_version_keys))

    yield Effect(
        DeleteS3Keys(bucket=configuration.documentation_bucket,
                     prefix=stable_prefix,
                     keys=existing_latest_keys - new_version_keys))

    # Update the key used for error pages if we're publishing to staging or if
    # we're publishing a marketing release to production.
    if (
        (environment is Environments.STAGING) or
        (environment is Environments.PRODUCTION and not is_dev)
    ):
        yield Effect(
            UpdateS3ErrorPage(bucket=configuration.documentation_bucket,
                              target_prefix=version_prefix))

    # The changed keys are the new keys, the keys that were deleted from this
    # version, and the keys for the previous version.
    changed_keys = (new_version_keys | existing_version_keys)

    # S3 serves /index.html when given /, so any changed /index.html means
    # that / changed as well.
    # Note that we check for '/index.html' but remove 'index.html'
    changed_keys |= {key_name[:-len('index.html')]
                     for key_name in changed_keys
                     if key_name.endswith('/index.html')}

    # Always update the root.
    changed_keys |= {''}

    # The full paths are all the changed keys under the stable prefix, and
    # the new version prefix. This set is slightly bigger than necessary.
    changed_paths = {prefix + key_name
                     for key_name in changed_keys
                     for prefix in [stable_prefix, version_prefix]}

    yield Effect(UpdateS3RoutingRules(
        bucket=configuration.documentation_bucket,
        routing_rules=parse_routing_rules(
            routing_config, configuration.cloudfront_cname),
    ))

    # Invalidate all the changed paths in cloudfront.
    yield Effect(
        CreateCloudFrontInvalidation(cname=configuration.cloudfront_cname,
                                     paths=changed_paths))


class PublishDocsOptions(Options):
    """
    Arguments for ``publish-docs`` script.
    """

    optParameters = [
        ["flocker-version", None, flocker.__version__,
         "The version of flocker from which the documentation was built."],
        ["doc-version", None, None,
         "The version to publish the documentation as.\n"
         "This will differ from \"flocker-version\" for staging uploads."
         "Attempting to publish documentation as a documentation version "
         "publishes it as the version being updated.\n"
         "``doc-version`` is set to 0.3.0.post1 the documentation will be "
         "published as 0.3.0.\n"],
    ]

    optFlags = [
        ["production", None, "Publish documentation to production."],
    ]

    environment = Environments.STAGING

    def parseArgs(self):
        if self['doc-version'] is None:
            self['doc-version'] = get_doc_version(self['flocker-version'])

        if self['production']:
            self.environment = Environments.PRODUCTION


def publish_docs_main(args, base_path, top_level):
    """
    :param list args: The arguments passed to the script.
    :param FilePath base_path: The executable being run.
    :param FilePath top_level: The top-level of the flocker repository.
    """
    options = PublishDocsOptions()

    try:
        options.parseOptions(args)
    except UsageError as e:
        sys.stderr.write("%s: %s\n" % (base_path.basename(), e))
        raise SystemExit(1)

    redirects_path = top_level.descendant(['docs', 'redirects.yaml'])
    routing_config = yaml.safe_load(redirects_path.getContent())
    try:
        sync_perform(
            dispatcher=ComposedDispatcher([boto_dispatcher, base_dispatcher]),
            effect=publish_docs(
                flocker_version=options['flocker-version'],
                doc_version=options['doc-version'],
                environment=options.environment,
                routing_config=routing_config,
                ))
    except NotARelease:
        sys.stderr.write("%s: Can't publish non-release.\n"
                         % (base_path.basename(),))
        raise SystemExit(1)
    except NotTagged:
        sys.stderr.write(
            "%s: Can't publish non-tagged version to production.\n"
            % (base_path.basename(),))
        raise SystemExit(1)


class UploadOptions(Options):
    """
    Options for uploading artifacts.
    """
    optParameters = [
        ["flocker-version", None, flocker.__version__,
         "The version of Flocker to upload artifacts for."
         "Python packages for " + flocker.__version__ + "will be uploaded.\n"],
        ["target", None, ARCHIVE_BUCKET,
         "The bucket to upload artifacts to.\n"],
        ["build-server", None,
         b'http://build.clusterhq.com',
         "The URL of the build-server.\n"],
    ]

    def parseArgs(self):
        version = self['flocker-version']

        if not (is_release(version) or
                is_weekly_release(version) or
                is_pre_release(version)):
            raise NotARelease()

        if get_doc_version(version) != version:
            raise DocumentationRelease()


FLOCKER_PACKAGES = [
    b'clusterhq-python-flocker',
    b'clusterhq-flocker-cli',
    b'clusterhq-flocker-node',
    b'clusterhq-flocker-docker-plugin',
]


@do
def update_repo(package_directory, target_bucket, target_key, source_repo,
                packages, flocker_version, distribution):
    """
    Update ``target_bucket`` yum repository with ``packages`` from
    ``source_repo`` repository.

    :param FilePath package_directory: Temporary directory to download
        repository to.
    :param bytes target_bucket: S3 bucket to upload repository to.
    :param bytes target_key: Path within S3 bucket to upload repository to.
    :param bytes source_repo: Repository on the build server to get packages
        from.
    :param list packages: List of bytes, each specifying the name of a package
        to upload to the repository.
    :param bytes flocker_version: The version of flocker to upload packages
        for.
    :param Distribution distribution: The distribution to upload packages for.
    """
    package_directory.createDirectory()

    package_type = distribution.package_type()

    yield Effect(DownloadS3KeyRecursively(
        source_bucket=target_bucket,
        source_prefix=target_key,
        target_path=package_directory,
        filter_extensions=('.' + package_type.value,)))

    downloaded_packages = yield Effect(DownloadPackagesFromRepository(
        source_repo=source_repo,
        target_path=package_directory,
        packages=packages,
        flocker_version=flocker_version,
        distribution=distribution,
        ))

    new_metadata = yield Effect(CreateRepo(
        repository_path=package_directory,
        distribution=distribution,
        ))

    yield Effect(UploadToS3Recursively(
        source_path=package_directory,
        target_bucket=target_bucket,
        target_key=target_key,
        files=downloaded_packages | new_metadata,
        ))


@do
def upload_packages(scratch_directory, target_bucket, version, build_server,
                    top_level):
    """
    The ClusterHQ yum and deb repositories contain packages for Flocker, as
    well as the dependencies which aren't available in CentOS 7. It is
    currently hosted on Amazon S3. When doing a release, we want to add the
    new Flocker packages, while preserving the existing packages in the
    repository. To do this, we download the current repository, add the new
    package, update the metadata, and then upload the repository.

    :param FilePath scratch_directory: Temporary directory to download
        repository to.
    :param bytes target_bucket: S3 bucket to upload repository to.
    :param bytes version: Version to download packages for.
    :param bytes build_server: Server to download new packages from.
    :param FilePath top_level: The top-level of the flocker repository.
    """
    distribution_names = available_distributions(
        flocker_source_path=top_level,
    )

    for distribution_name in distribution_names:
        distribution = DISTRIBUTION_NAME_MAP[distribution_name]
        architecture = distribution.native_package_architecture()

        yield update_repo(
            package_directory=scratch_directory.child(
                b'{}-{}-{}'.format(
                    distribution.name,
                    distribution.version,
                    architecture)),
            target_bucket=target_bucket,
            target_key=os.path.join(
                distribution.name + get_package_key_suffix(version),
                distribution.version,
                architecture),
            source_repo=os.path.join(
                build_server, b'results/omnibus',
                version,
                b'{}-{}'.format(distribution.name, distribution.version)),
            packages=FLOCKER_PACKAGES,
            flocker_version=version,
            distribution=distribution,
        )


packages_template = (
    '<html xmlns:t="http://twistedmatrix.com/ns/twisted.web.template/0.1">\n'
    'This is an index for pip\n'
    '<div t:render="packages"><a>'
    '<t:attr name="href"><t:slot name="package_name" /></t:attr>'
    '<t:slot name="package_name" />'
    '</a><br />\n</div>'
    '</html>'
    )


class PackagesElement(template.Element):
    """A Twisted Web template element to render the Pip index file."""

    def __init__(self, packages):
        template.Element.__init__(self, template.XMLString(packages_template))
        self._packages = packages

    @template.renderer
    def packages(self, request, tag):
        for package in self._packages:
            if package != 'index.html':
                yield tag.clone().fillSlots(package_name=package)


def create_pip_index(scratch_directory, packages):
    """
    Create an index file for pip.

    :param FilePath scratch_directory: Temporary directory to create index in.
    :param list packages: List of bytes, filenames of packages to be in the
        index.
    """
    index_file = scratch_directory.child('index.html')
    with index_file.open('w') as f:
        # Although this returns a Deferred, it works without the reactor
        # because there are no Deferreds in the template evaluation.
        # See this cheat described at
        # https://twistedmatrix.com/documents/15.0.0/web/howto/twisted-templates.html
        template.flatten(None, PackagesElement(packages), f.write)
    return index_file


@do
def upload_pip_index(scratch_directory, target_bucket):
    """
    Upload an index file for pip to S3.

    :param FilePath scratch_directory: Temporary directory to create index in.
    :param bytes target_bucket: S3 bucket to upload index to.
    """
    packages = yield Effect(
        ListS3Keys(bucket=target_bucket,
                   prefix='python/'))

    index_path = create_pip_index(
        scratch_directory=scratch_directory,
        packages=packages)

    yield Effect(
        UploadToS3(
            source_path=scratch_directory,
            target_bucket=target_bucket,
            target_key='python/index.html',
            file=index_path,
        ))


@do
def upload_python_packages(scratch_directory, target_bucket, top_level,
                           output, error):
    """
    The repository contains source distributions and binary distributions
    (wheels) for Flocker. It is currently hosted on Amazon S3.

    :param FilePath scratch_directory: Temporary directory to create packages
        in.
    :param bytes target_bucket: S3 bucket to upload packages to.
    :param FilePath top_level: The top-level of the flocker repository.
    """
    # XXX This has a side effect so it should be an Effect
    # https://clusterhq.atlassian.net/browse/FLOC-1731
    check_call([
        'python', 'setup.py',
        'sdist', '--dist-dir={}'.format(scratch_directory.path),
        'bdist_wheel', '--dist-dir={}'.format(scratch_directory.path)],
        cwd=top_level.path, stdout=output, stderr=error)

    files = set([f.basename() for f in scratch_directory.children()])
    yield Effect(UploadToS3Recursively(
        source_path=scratch_directory,
        target_bucket=target_bucket,
        target_key='python',
        files=files,
        ))


def publish_artifacts_main(args, base_path, top_level):
    """
    Publish release artifacts.

    :param list args: The arguments passed to the scripts.
    :param FilePath base_path: The executable being run.
    :param FilePath top_level: The top-level of the flocker repository.
    """
    options = UploadOptions()

    try:
        options.parseOptions(args)
    except UsageError as e:
        sys.stderr.write("%s: %s\n" % (base_path.basename(), e))
        raise SystemExit(1)
    except NotARelease:
        sys.stderr.write("%s: Can't publish artifacts for a non-release.\n"
                         % (base_path.basename(),))
        raise SystemExit(1)
    except DocumentationRelease:
        sys.stderr.write("%s: Can't publish artifacts for a documentation "
                         "release.\n" % (base_path.basename(),))
        raise SystemExit(1)

    dispatcher = ComposedDispatcher([boto_dispatcher, yum_dispatcher,
                                     base_dispatcher])

    scratch_directory = FilePath(tempfile.mkdtemp(
        prefix=b'flocker-upload-'))
    scratch_directory.child('packages').createDirectory()
    scratch_directory.child('python').createDirectory()
    scratch_directory.child('pip').createDirectory()

    try:
        sync_perform(
            dispatcher=dispatcher,
            effect=sequence([
                upload_packages(
                    scratch_directory=scratch_directory.child('packages'),
                    target_bucket=options['target'],
                    version=options['flocker-version'],
                    build_server=options['build-server'],
                    top_level=top_level,
                ),
                upload_python_packages(
                    scratch_directory=scratch_directory.child('python'),
                    target_bucket=options['target'],
                    top_level=top_level,
                    output=sys.stdout,
                    error=sys.stderr,
                ),
                upload_pip_index(
                    scratch_directory=scratch_directory.child('pip'),
                    target_bucket=options['target'],
                ),
            ]),
        )

    finally:
        scratch_directory.remove()


def calculate_base_branch(version, path):
    """
    The branch a release branch is created from depends on the release
    type and sometimes which pre-releases have preceeded this.

    :param bytes version: The version of Flocker to get a base branch for.
    :param bytes path: See :func:`git.Repo.init`.
    :returns: The base branch from which the new release branch was created.
    """
    if not (is_release(version) or
            is_weekly_release(version) or
            is_pre_release(version)):
        raise NotARelease()

    repo = Repo(path=path, search_parent_directories=True)
    existing_tags = [tag for tag in repo.tags if tag.name == version]

    if existing_tags:
        raise TagExists()

    # We always base releases off master now.
    base_branch_name = 'master'

    # We create a new branch from a branch, not a tag, because a maintenance
    # or documentation change may have been applied to the branch and not the
    # tag.
    # The branch must be available locally for the next step.
    repo.git.checkout(base_branch_name)

    return (
        branch for branch in repo.branches if
        branch.name == base_branch_name).next()


def create_release_branch(version, base_branch):
    """
    checkout a new Git branch to make changes on and later tag as a release.

    :param bytes version: The version of Flocker to create a release branch
        for.
    :param base_branch: See :func:`git.Head`. The branch to create the release
        branch from.
    """
    try:
        base_branch.checkout(b='release/flocker-' + version)
    except GitCommandError:
        raise BranchExists()


class InitializeReleaseOptions(Options):
    """
    Arguments for ``initialize-release`` script.
    """

    optParameters = [
        ["flocker-version", None, None,
         "The version of Flocker to create a release for."],
        ["path", None, None,
         "Full path where the cloned repo should be created."],
    ]

    def parseArgs(self):
        if self['flocker-version'] is None:
            raise UsageError("`--flocker-version` must be specified.")
        if self['path'] is None:
            self['path'] = FilePath(os.getcwd()).parent()
        else:
            self['path'] = FilePath(self['path'])
        if not self['path'].exists():
            self['path'].makedirs()


def initialize_release_main(args, base_path, top_level):
    """
    Clone the Flocker repo and install a new virtual environment for
    a release.

    :param list args: The arguments passed to the script.
    :param FilePath base_path: The executable being run.
    :param FilePath top_level: The top-level of the flocker repository.
    """
    options = InitializeReleaseOptions()

    try:
        options.parseOptions(args)
    except UsageError as e:
        sys.stderr.write("%s: %s\n" % (base_path.basename(), e))
        raise SystemExit(1)

    version = options['flocker-version']
    path = options['path']
    initialize_release(version, path, top_level)


def initialize_release(version, path, top_level):
    """
    Clone the Flocker repo and install a new virtual environment for
    a release.

    :param bytes version: The version to release.
    :param FilePath path: The path in which the release branch
        will be created.
    :param FilePath top_level: The top-level of the flocker repository.

    """
    REMOTE_URL = "https://github.com/ClusterHQ/flocker"
    release_path = path.child("flocker-release-{}".format(version))
    sys.stdout.write("Cloning repo in {}...\n".format(release_path.path))

    release_repo = Repo.init(release_path.path)
    release_origin = release_repo.create_remote('origin', REMOTE_URL)
    release_origin.fetch()

    sys.stdout.write("Checking out master...\n")
    release_repo.git.checkout("master")

    sys.stdout.write("Updating repo...\n")
    release_repo.git.pull("origin", "master")

    sys.stdout.write(
        "Creating release branch for version {}...\n".format(version))
    release_repo.active_branch.checkout(b="release/flocker-{}".format(version))

    sys.stdout.write("Creating virtual environment...\n")
    virtualenv_path = release_path.child("flocker-{}".format(version))
    virtualenv.create_environment(
        virtualenv_path.path,
        site_packages=False
    )

    sys.stdout.write("Installing dependencies...\n")
    environment = {
        "PATH": os.environ["PATH"]
    }
    check_call(
        [virtualenv_path.descendant(["bin", "python"]).path,
         virtualenv_path.descendant(["bin", "pip"]).path,
         "install", "-e", ".[dev]"],
        stdout=open(os.devnull, 'w'),
        env=environment,
        cwd=release_path.path,
    )

    sys.stdout.write("Updating LICENSE file...\n")
    update_license_file(list(), top_level)

    sys.stdout.write("Committing result (no push)...\n")
    try:
        release_repo.git.commit(
            a=True, m="'Updated copyright in LICENSE file'"
        )
    except GitCommandError:
        # This will happen when the LICENSE file has not changed, so we'll
        # ignore the error.
        pass

    sys.stdout.write(
        "\nCompleted.\n\nPlease copy and paste the following commands "
        "in your shell to enter the release environment and continue "
        "the pre-tag release process:\n\n"
        "export VERSION={};\ncd {};\nsource flocker-{}/bin/activate;\n\n"
        .format(version, release_path.path, version)
    )


class CreateReleaseBranchOptions(Options):
    """
    Arguments for ``create-release-branch`` script.
    """

    optParameters = [
        ["flocker-version", None, None,
         "The version of Flocker to create a release branch for."],
    ]

    def parseArgs(self):
        if self['flocker-version'] is None:
            raise UsageError("`--flocker-version` must be specified.")


def create_release_branch_main(args, base_path, top_level):
    """
    Create a release branch.

    :param list args: The arguments passed to the script.
    :param FilePath base_path: The executable being run.
    :param FilePath top_level: The top-level of the flocker repository.
    """
    options = CreateReleaseBranchOptions()

    try:
        options.parseOptions(args)
    except UsageError as e:
        sys.stderr.write("%s: %s\n" % (base_path.basename(), e))
        raise SystemExit(1)

    version = options['flocker-version']
    path = FilePath(__file__).path

    try:
        base_branch = calculate_base_branch(version=version, path=path)
        create_release_branch(version=version, base_branch=base_branch)
    except NotARelease:
        sys.stderr.write("%s: Can't create a release branch for non-release.\n"
                         % (base_path.basename(),))
        raise SystemExit(1)
    except TagExists:
        sys.stderr.write("%s: Tag already exists for this release.\n"
                         % (base_path.basename(),))
        raise SystemExit(1)
    except BranchExists:
        sys.stderr.write("%s: The release branch already exists.\n"
                         % (base_path.basename(),))
        raise SystemExit(1)


def update_license_file(args, top_level, year=datetime.now(UTC).year):
    """
    Update the LICENSE file to include the current year.

    :param list args: The arguments passed to the script.
    :param FilePath top_level: The top-level of the flocker repository.
    """
    license_template = top_level.child('admin').child('LICENSE.template')
    with license_template.open() as input_file:
        with top_level.child('LICENSE').open('w') as output_file:
            output_file.write(input_file.read().format(current_year=year))
