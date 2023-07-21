import os
import os.path
import sys
import subprocess
import re
import tempfile
import threading
from util import *

FILE_ADDED       = 'A'
FILE_MODIFIED    = 'M'
FILE_DELETED     = 'D'
FILE_COPIED      = 'C'
FILE_RENAMED     = 'R'
FILE_UNMERGED    = 'U'
FILE_TYPECHANGED = 'T'
FILE_UNTRACKED   = 'N'
FILE_BROKEN      = 'B'
FILE_UNKNOWN     = 'X'

MERGE_TOOLS = {
    'opendiff': (
        ['/usr/bin/opendiff'],
        ['{LOCAL}', '{REMOTE}', '-merge', '{MERGED}']
    ),
    'diffmerge.app': (
        ['/Applications/DiffMerge.app/Contents/MacOS/DiffMerge'],
        ['--nosplash', '-t1={FILENAME}.LOCAL', '-t2={FILENAME}.MERGED', '-t3={FILENAME}.REMOTE', '{LOCAL}', '{MERGED}', '{REMOTE}']
    ),
    'diffmerge.cmdline': (
        ['{PATH}/diffmerge', '{PATH}/diffmerge.sh'],
        ['--nosplash', '-t1=LOCAL', '-t2=MERGED', '-t3=REMOTE', '{LOCAL}', '{MERGED}', '{REMOTE}']
    ),
    'meld': (
        ['{PATH}/meld'],
        ['{LOCAL}', '{MERGED}', '{REMOTE}']
    ),
    'kdiff3': (
        ['{PATH}/kdiff3'],
        ['{LOCAL}', '{MERGED}', '{REMOTE}', '-o', '{MERGED}', '--L1', '{FILENAME}.LOCAL', '--L2', '{FILENAME}.MERGED', '--L3', '{FILENAME}.REMOTE']
    ),
    'winmerge': (
        [r'C:\Program Files\WinMerge\WinMergeU.exe'],
        ['{MERGED}'] # It does not support 3-way merge yet...
    ),
    'tortoisemerge': (
        [r'C:\Program Files\TortoiseGit\bin\TortoiseMerge.exe'],
        ['{MERGED}', '{LOCAL}', '{REMOTE}']
    ),
}

_git = None
commit_pool = {}

class GitError(RuntimeError): pass

def git_binary():
    global _git

    if _git:
        return _git

    # Search for git binary
    if os.name == 'posix':
        locations = ['{PATH}/git', '/opt/local/bin/git', '/usr/local/git/bin']
    elif sys.platform == 'win32':
        locations = (r'{PATH}\git.exe', r'C:\Program Files\Git\bin\git.exe')
    else:
        locations = []

    for _git in find_binary(locations):
        return _git

    _git = None
    raise GitError, "git executable not found"

_mergetool = None
def detect_mergetool():
    global _mergetool

    if _mergetool:
        return _mergetool

    # Select tools
    if sys.platform == 'darwin':
        # Mac OS X
        tools = ['diffmerge.app', 'diffmerge.cmdline', 'opendiff', 'meld']
    elif os.name == 'posix':
        # Other Unix
        tools = ['diffmerge.cmdline', 'meld', 'kdiff3']
    elif sys.platform == 'win32':
        # Windows
        tools = ['tortoisemerge', 'winmerge']
    else:
        raise GitError, "Cannot detect any merge tool"

    # Detect binaries
    for tool in tools:
        locations, args = MERGE_TOOLS[tool]
        for location in find_binary(locations):
            _mergetool = (location, args)
            return _mergetool

    # Return error if no tool was found
    raise GitError, "Cannot detect any merge tool"

def run_cmd(dir, args, with_retcode=False, with_stderr=False, raise_error=False, input=None, env={}, run_bg=False, setup_askpass=False):
    # Check args
    if type(args) in [str, unicode]:
        args = [args]
    args = [str(a) for a in args]

    # Check directory
    if not os.path.isdir(dir):
        raise GitError, 'Directory not exists: ' + dir

    try:
        os.chdir(dir)
    except OSError, msg:
        raise GitError, msg

    # Run command
    if type(args) != list:
        args = [args]

    # Setup environment
    git_env = dict(os.environ)
    if setup_askpass and 'SSH_ASKPASS' not in git_env:
        git_env['SSH_ASKPASS'] = '%s-askpass' % os.path.realpath(os.path.abspath(sys.argv[0]))

    git_env.update(env)
    
    preexec_fn = os.setsid if setup_askpass else None

    p = Popen([git_binary()] + args, stdout=subprocess.PIPE,
              stderr=subprocess.PIPE, stdin=subprocess.PIPE,
              env=git_env, shell=False, preexec_fn=preexec_fn)
    if run_bg:
        return p

    if input == None:
        stdout,stderr = p.communicate('')
    else:
        stdout,stderr = p.communicate(utf8_str(input))
    
    # Return command output in a form given by arguments
    ret = []

    if p.returncode != 0 and raise_error:
        raise GitError, 'git returned with the following error:\n%s' % stderr

    if with_retcode:
        ret.append(p.returncode)

    ret.append(stdout)

    if with_stderr:
        ret.append(stderr)

    if len(ret) == 1:
        return ret[0]
    else:
        return tuple(ret)

class Repository(object):
    def __init__(self, repodir, name='Main module', parent=None):
        self.name = name
        self.parent = parent

        # Search for .git directory in repodir ancestors
        repodir = os.path.abspath(repodir)
        try:
            if parent:
                if not os.path.isdir(os.path.join(repodir, '.git')):
                    raise GitError, "Not a git repository: %s" % repodir
            else:
                while not os.path.isdir(os.path.join(repodir, '.git')):
                    new_repodir = os.path.abspath(os.path.join(repodir, '..'))
                    if new_repodir == repodir or (parent and new_repodir == parent.dir):
                        raise GitError, "Directory is not a git repository"
                    else:
                        repodir = new_repodir
        except OSError:
            raise GitError, "Directory is not a git repository or it is not readable"
            
        self.dir = repodir

        # Remotes
        self.config = ConfigFile(os.path.join(self.dir, '.git', 'config'))
        self.url = self.config.get_option('remote', 'origin', 'url')

        self.remotes = {}
        for remote, opts in self.config.sections_for_type('remote'):
            if 'url' in opts:
                self.remotes[remote] = opts['url']

        # Run a git status to see whether this is really a git repository
        retcode,output = self.run_cmd(['status'], with_retcode=True)
        if retcode not in [0,1]:
            raise GitError, "Directory is not a git repository"

        # Load refs
        self.load_refs()

        # Get submodule info
        self.submodules = self.get_submodules()
        self.all_modules = [self] + self.submodules

    def load_refs(self):
        self.refs = {}
        self.branches = {}
        self.remote_branches = {}
        self.tags = {}

        # HEAD, current branch
        self.head = self.run_cmd(['rev-parse', 'HEAD']).strip()
        self.current_branch = None
        try:
            f = open(os.path.join(self.dir, '.git', 'HEAD'))
            head = f.read().strip()
            f.close()

            if head.startswith('ref: refs/heads/'):
                self.current_branch = head[16:]
        except OSError:
            pass

        # Main module references
        if self.parent:
            self.main_ref = self.parent.get_submodule_version(self.name, 'HEAD')
            if os.path.exists(os.path.join(self.parent.dir, '.git', 'MERGE_HEAD')):
                self.main_merge_ref = self.parent.get_submodule_version(self.name, 'MERGE_HEAD')
            else:
                self.main_merge_ref = None
        else:
            self.main_ref = None
            self.main_merge_ref = None

        # References
        for line in self.run_cmd(['show-ref']).split('\n'):
            commit_id, _, refname = line.partition(' ')
            self.refs[refname] = commit_id

            if refname.startswith('refs/heads/'):
                branchname = refname[11:]
                self.branches[branchname] = commit_id
            elif refname.startswith('refs/remotes/'):
                branchname = refname[13:]
                self.remote_branches[branchname] = commit_id
            elif refname.startswith('refs/tags/'):
                # Load the referenced commit for tags
                tagname = refname[10:]
                try:
                    self.tags[tagname] = self.run_cmd(['rev-parse', '%s^{commit}' % refname], raise_error=True).strip()
                except GitError:
                    pass

        # Inverse reference hashes
        self.refs_by_sha1 = invert_hash(self.refs)
        self.branches_by_sha1 = invert_hash(self.branches)
        self.remote_branches_by_sha1 = invert_hash(self.remote_branches)
        self.tags_by_sha1 = invert_hash(self.tags)

    def run_cmd(self, args, **opts):
        return run_cmd(self.dir, args, **opts)

    def get_submodules(self):
        # Check existence of .gitmodules
        gitmodules_path = os.path.join(self.dir, '.gitmodules')
        if not os.path.isfile(gitmodules_path):
            return []

        # Parse .gitmodules file
        repos = []
        submodule_config = ConfigFile(gitmodules_path)
        for name,opts in submodule_config.sections_for_type('submodule'):
            if 'path' in opts:
                repo_path = os.path.join(self.dir, opts['path'])
                repos.append(Repository(repo_path, name=opts['path'], parent=self))

        return repos

    def get_submodule_version(self, submodule_name, main_version):
        dir = os.path.dirname(submodule_name)
        name = os.path.basename(submodule_name)
        output = self.run_cmd(['ls-tree', '-z', '%s:%s' % (main_version, dir)])
        for line in output.split('\x00'):
            if not line.strip(): continue

            meta, filename = line.split('\t')
            if filename == name:
                mode, filetype, sha1 = meta.split(' ')
                if filetype == 'commit':
                    return sha1

        return None

    def get_log(self, args=[]):
        log = self.run_cmd(['log', '-z', '--date=relative', '--pretty=format:%H%n%h%n%P%n%T%n%an%n%ae%n%ad%n%s%n%b']+args)
        
        if len(log) == 0:
            return []

        commit_texts = log.split('\x00')
        commit_texts.reverse()

        commits = []
        for text in commit_texts:
            c = Commit(self)
            c.parse_gitlog_output(text)
            commit_pool[c.sha1] = c
            commits.append(c)

        commits.reverse()
        return commits

    def commit(self, author_name, author_email, msg, amend=False):
        if amend:
            # Get details of current HEAD
            is_merge_resolve = False

            output = self.run_cmd(['log', '-1', '--pretty=format:%P%n%an%n%ae%n%aD'])
            if not output.strip():
                raise GitError, "Cannot amend in an empty repository!"

            parents, author_name, author_email, author_date = output.split('\n')
            parents = parents.split(' ')
        else:
            author_date = None # Use current date

            # Get HEAD sha1 id
            if self.head == 'HEAD':
                parents = []
            else:
                head = self.run_cmd(['rev-parse', 'HEAD']).strip()
                parents = [head]

            # Get merge head if exists
            is_merge_resolve = False
            try:
                merge_head_filename = os.path.join(self.dir, '.git', 'MERGE_HEAD')
                if os.path.isfile(merge_head_filename):
                    f = open(merge_head_filename)
                    p = f.read().strip()
                    f.close()
                    parents.append(p)
                    is_merge_resolve = True
            except OSError:
                raise GitError, "Cannot open MERGE_HEAD file"

        # Write tree
        tree = self.run_cmd(['write-tree'], raise_error=True).strip()

        # Write commit
        parent_args = []
        for parent in parents:
            parent_args += ['-p', parent]

        env = {}
        if author_name: env['GIT_AUTHOR_NAME'] = author_name
        if author_email: env['GIT_AUTHOR_EMAIL'] = author_email
        if author_date: env['GIT_AUTHOR_DATE'] = author_date

        commit = self.run_cmd(
            ['commit-tree', tree] + parent_args,
            raise_error=True,
            input=msg,
            env=env
        ).strip()

        # Update reference
        self.run_cmd(['update-ref', 'HEAD', commit], raise_error=True)

        # Remove MERGE_HEAD
        if is_merge_resolve:
            try:
                os.unlink(os.path.join(self.dir, '.git', 'MERGE_HEAD'))
                os.unlink(os.path.join(self.dir, '.git', 'MERGE_MODE'))
                os.unlink(os.path.join(self.dir, '.git', 'MERGE_MSG'))
                os.unlink(os.path.join(self.dir, '.git', 'ORIG_HEAD'))
            except OSError:
                pass

    def get_status(self):
        unstaged_changes = {}
        staged_changes = {}

        # Unstaged changes
        changes = self.run_cmd(['diff', '--name-status', '-z']).split('\x00')
        for i in xrange(len(changes)/2):
            status, filename = changes[2*i], changes[2*i+1]
            if filename not in unstaged_changes or status == FILE_UNMERGED:
                unstaged_changes[filename] = status

        # Untracked files
        for filename in self.run_cmd(['ls-files', '--others', '--exclude-standard', '-z']).split('\x00'):
            if filename and filename not in unstaged_changes:
                unstaged_changes[filename] = FILE_UNTRACKED

        # Staged changes
        if self.head == 'HEAD':
            # Initial commit
            for filename in self.run_cmd(['ls-files', '--cached', '-z']).split('\x00'):
                if filename:
                    staged_changes[filename] = FILE_ADDED
        else:
            changes = self.run_cmd(['diff', '--cached', '--name-status', '-z']).split('\x00')
            for i in xrange(len(changes)/2):
                status, filename = changes[2*i], changes[2*i+1]
                if status != FILE_UNMERGED or filename not in unstaged_changes:
                    staged_changes[filename] = status

        return unstaged_changes, staged_changes

    def get_unified_status(self):
        unified_changes = {}

        # Staged & unstaged changes
        changes = self.run_cmd(['diff', 'HEAD', '--name-status', '-z']).split('\x00')
        for i in xrange(len(changes)/2):
            status, filename = changes[2*i], changes[2*i+1]
            if filename not in unified_changes or status == FILE_UNMERGED:
                unified_changes[filename] = status

        # Untracked files
        for filename in self.run_cmd(['ls-files', '--others', '--exclude-standard', '-z']).split('\x00'):
            if filename and filename not in unified_changes:
                unified_changes[filename] = FILE_UNTRACKED

        return unified_changes

    def merge_file(self, filename):
        # Store file versions in temporary files
        fd, local_file = tempfile.mkstemp(prefix=os.path.basename(filename) + '.LOCAL.')
        os.write(fd, self.run_cmd(['show', ':2:%s' % filename], raise_error=True))
        os.close(fd)

        fd, remote_file = tempfile.mkstemp(prefix=os.path.basename(filename) + '.REMOTE.')
        os.write(fd, self.run_cmd(['show', ':3:%s' % filename], raise_error=True))
        os.close(fd)
        
        # Run mergetool
        mergetool, args = detect_mergetool()
        args = list(args)

        for i in xrange(len(args)):
            args[i] = args[i].replace('{FILENAME}', os.path.basename(filename))
            args[i] = args[i].replace('{LOCAL}', local_file)
            args[i] = args[i].replace('{REMOTE}', remote_file)
            args[i] = args[i].replace('{MERGED}', os.path.join(self.dir, filename))

        s = Popen([mergetool] + args, shell=False)

    def get_lost_commits(self, refname, moving_to=None):
        # Note: refname must be a full reference name (e.g. refs/heads/master)
        # or HEAD (if head is detached).
        # moving_to must be a SHA1 commit identifier
        if refname == 'HEAD':
            commit_id = self.head
        else:
            commit_id = self.refs[refname]
        commit = commit_pool[commit_id]

        # If commit is not moving, it won't be lost :)
        if commit_id == moving_to:
            return []

        # If a commit has another reference, it won't be lost :)
        head_refnum = len(self.refs_by_sha1.get(commit_id, []))
        if (refname == 'HEAD' and head_refnum > 0) or head_refnum > 1:
            return []

        # If commit has descendants, it won't be lost: at least one of its
        # descendants has another reference
        if commit.children:
            return []

        # If commit has parents, traverse the commit graph into this direction.
        # Mark every commit as lost commit until:
        #   (1) the end of the graph is found
        #   (2) a reference is found
        #   (3) the moving_to destination is found
        #   (4) a commit is found that has more than one children.
        #       (it must have a descendant that has a reference)
        lost_commits = []
        search_pos = [commit]

        while search_pos:
            next_search_pos = []

            for c in search_pos:
                for p in c.parents:
                    if p.sha1 not in self.refs_by_sha1 and p.sha1 != moving_to \
                        and len(p.children) == 1:
                        next_search_pos.append(p)

            lost_commits += search_pos
            search_pos = next_search_pos

        return lost_commits

    def update_head(self, content):
        try:
            f = open(os.path.join(self.dir, '.git', 'HEAD'), 'w')
            f.write(content)
            f.close()
        except OSError:
            raise GitError, "Write error:\nCannot write into .git/HEAD"

    def fetch_bg(self, remote, callbackFunc, fetch_tags=False):
        url = self.remotes[remote]
        t = FetchThread(self, remote, callbackFunc, fetch_tags)
        t.start()

        return t

    def push_bg(self, remote, commit, remoteBranch, forcePush, callbackFunc):
        t = PushThread(self, remote, commit, remoteBranch, forcePush, callbackFunc)
        t.start()

        return t

class Commit(object):
    def __init__(self, repo):
        self.repo = repo

        self.sha1 = None
        self.abbrev = None

        self.parents = None
        self.children = None
        self.tree = None

        self.author_name = None
        self.author_email = None
        self.author_date = None

        self.short_msg = None
        self.full_msg = None

        self.remote_branches = None
        self.branches = None
        self.tags = None

    def parse_gitlog_output(self, text):
        lines = text.split('\n')

        (self.sha1, self.abbrev, parents, self.tree,
         self.author_name, self.author_email, self.author_date,
         self.short_msg) = lines[0:8]

        if parents:
            parent_ids = parents.split(' ')
            self.parents = [commit_pool[p] for p in parent_ids]
            for parent in self.parents:
                parent.children.append(self)
        else:
            self.parents = []

        self.children = []

        self.full_msg = '\n'.join(lines[8:])


class ConfigFile(object):
    def __init__(self, filename):
        self.sections = []

        # Patterns
        p_rootsect = re.compile(r'\[([^\]\s]+)\]')
        p_sect     = re.compile(r'\[([^\]"\s]+)\s+"([^"]+)"\]')
        p_option   = re.compile(r'(\w+)\s*=\s*(.*)')

        # Parse file
        section = None
        section_type = None
        options = {}

        f = open(filename)
        for line in f:
            line = line.strip()

            if len(line) == 0 or line.startswith('#'):
                continue

            # Parse sections
            m_rootsect = p_rootsect.match(line)
            m_sect     = p_sect.match(line)

            if (m_rootsect or m_sect) and section:
                self.sections.append( (section_type, section, options) )
            if m_rootsect:
                section_type = None
                section = m_rootsect.group(1)
                options = {}
            elif m_sect:
                section_type = m_sect.group(1)
                section = m_sect.group(2)
                options = {}
                
            # Parse options
            m_option = p_option.match(line)
            if section and m_option:
                options[m_option.group(1)] = m_option.group(2)

        if section:
            self.sections.append( (section_type, section, options) )
        f.close()

    def has_section(self, sect_type, sect_name):
        m = [ s for s in self.sections if s[0]==sect_type and s[1] == sect_name ]
        return len(m) > 0

    def sections_for_type(self, sect_type):
        return [ (s[1],s[2]) for s in self.sections if s[0]==sect_type ]

    def options_for_section(self, sect_type, sect_name):
        m = [ s[2] for s in self.sections if s[0]==sect_type and s[1] == sect_name ]
        if m:
            return m[0]
        else:
            return None

    def get_option(self, sect_type, sect_name, option):
        opts = self.options_for_section(sect_type, sect_name)
        if opts:
            return opts.get(option)
        else:
            return None

TRANSFER_COUNTING      = 0
TRANSFER_COMPRESSING   = 1
TRANSFER_RECEIVING     = 2
TRANSFER_WRITING       = 3
TRANSFER_RESOLVING     = 4
TRANSFER_ENDED         = 5
class ObjectTransferThread(threading.Thread):
    def __init__(self, repo, callback_func):
        threading.Thread.__init__(self)
        
        # Parameters
        self.repo = repo
        self.callback_func = callback_func

        # Regular expressions for progress indicator
        self.counting_expr      = re.compile(r'.*Counting objects:\s*([0-9]+)')
        self.compressing_expr   = re.compile(r'.*Compressing objects:\s*([0-9]+)%')
        self.receiving_expr     = re.compile(r'.*Receiving objects:\s*([0-9]+)%')
        self.writing_expr       = re.compile(r'.*Writing objects:\s*([0-9]+)%')
        self.resolving_expr     = re.compile(r'.*Resolving deltas:\s*([0-9]+)%')

        self.progress_exprs = (
            (self.counting_expr, TRANSFER_COUNTING),
            (self.compressing_expr, TRANSFER_COMPRESSING),
            (self.receiving_expr, TRANSFER_RECEIVING),
            (self.writing_expr, TRANSFER_WRITING),
            (self.resolving_expr, TRANSFER_RESOLVING)
        )

    def run(self, cmd):
        # Initial state
        self.error_msg = 'Unknown error occured'
        self.aborted = False

        # Run git
        self.process = self.repo.run_cmd(cmd, run_bg=True, setup_askpass=True)
        self.process.stdin.close()

        # Read stdout from a different thread (select.select() does not work
        # properly on Windows)
        stdout_thread = threading.Thread(target=self.read_stdout, args=[self.process.stdout], kwargs={})
        stdout_thread.start()

        # Read lines
        line = ''
        c = self.process.stderr.read(1)
        while c:
            if c in ['\n', '\r']:
                self.parse_line(line)
                line = ''
            else:
                line += c

            c = self.process.stderr.read(1)

        self.process.wait()
        stdout_thread.join()

        # Remaining line
        if line:
            self.parse_line(line)

        # Report end of operation
        if self.aborted:
            return
        elif self.process.returncode == 0:
            result = self.transfer_ended()
            self.callback_func(TRANSFER_ENDED, result)
        else:
            self.callback_func(TRANSFER_ENDED, self.error_msg)

    def parse_line(self, line):
        # Progress indicators
        for reg, event in self.progress_exprs:
            m = reg.match(line)
            if m:
                self.callback_func(event, int(m.group(1)))

        # Fatal error
        if line.startswith('fatal:'):
            self.error_msg = line

    def read_stdout(self, stdout):
        lines = stdout.read().split('\n')
        for line in lines:
            self.parse_line(line)

    def abort(self):
        self.aborted = True
        try:
            self.process.kill()
        except:
            pass

class FetchThread(ObjectTransferThread):
    def __init__(self, repo, remote, callback_func, fetch_tags=False):
        ObjectTransferThread.__init__(self, repo, callback_func)

        # Parameters
        self.remote = remote
        self.fetch_tags = fetch_tags

        # Regular expressions for remote refs
        self.branches = {}
        self.tags = {}
        self.branch_expr    = re.compile(r'([0-9a-f]{40}) refs\/heads\/([a-zA-Z0-9_.\-]+)')
        self.tag_expr       = re.compile(r'([0-9a-f]{40}) refs\/tags\/([a-zA-Z0-9_.\-]+)')

        self.ref_exprs = (
            (self.branch_expr, self.branches),
            (self.tag_expr, self.tags)
        )

    def run(self):
        ObjectTransferThread.run(self, ['fetch-pack', '-v', '--all', self.repo.remotes[self.remote]])
    
    def transfer_ended(self):
        # Update remote branches
        for branch, sha1 in self.branches.iteritems():
            self.repo.run_cmd(['update-ref', 'refs/remotes/%s/%s' % (self.remote, branch), sha1])

        # Update tags
        if self.fetch_tags:
            for tag, sha1 in self.tags.iteritems():
                self.repo.run_cmd(['update-ref', 'refs/tags/%s' % tag, sha1])
        
        return (self.branches, self.tags)

    def parse_line(self, line):
        ObjectTransferThread.parse_line(self, line)

        # Remote refs
        for reg, refs in self.ref_exprs:
            m = reg.match(line)
            if m:
                refs[m.group(2)] = m.group(1)

class PushThread(ObjectTransferThread):
    def __init__(self, repo, remote, commit, remote_branch, force_push, callback_func):
        ObjectTransferThread.__init__(self, repo, callback_func)

        # Parameters
        self.remote = remote
        self.commit = commit
        self.remote_branch = remote_branch
        self.force_push = force_push

    def run(self):
        if self.force_push:
            push_cmd = ['push', '-f']
        else:
            push_cmd = ['push']

        cmd = push_cmd + [self.remote, '%s:refs/heads/%s' % (self.commit.sha1, self.remote_branch)]
        ObjectTransferThread.run(self, cmd)

    def parse_line(self, line):
        ObjectTransferThread.parse_line(self, line)

        if line.startswith(' ! [rejected]'):
            self.error_msg = 'The pushed commit is non-fast forward.'

    def transfer_ended(self):
        return None

# Utility functions
def diff_for_untracked_file(filename):
    # Start "diff" text
    diff_text = 'New file: %s\n' % filename

    # Detect whether file is binary
    if is_binary_file(filename):
        diff_text += "@@ File is binary.\n\n"
    else:
        # Text file => show lines
        newfile_text = ''
        try:
            f = open(filename, 'r')
            lines = f.readlines()
            f.close()

            newfile_text += '@@ -1,0 +1,%d @@\n' % len(lines)

            for line in lines:
                newfile_text += '+ ' + line

            diff_text += newfile_text
        except OSError:
            diff_text += '@@ Error: Cannot open file\n\n'

    return diff_text

