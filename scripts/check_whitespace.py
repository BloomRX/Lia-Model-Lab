#!/usr/bin/env python3
"""Check committed changes, not an accidentally clean checkout. No shell interpolation."""
import json
import os
import re
import subprocess
import sys


def git(*args, cwd=None, input=None):
    return subprocess.check_output(['git', *args], cwd=cwd, input=input, text=True).strip()


def revisions(event_name, event, cwd=None):
    if event_name == 'pull_request':
        base = event['pull_request']['base']['sha']
        head = event['pull_request']['head']['sha']
    elif event_name == 'push':
        base, head = event['before'], event['after']
    else:
        raise ValueError('unsupported event; explicit PR/push base required')
    if any(not isinstance(s, str) or not re.fullmatch(r'[0-9a-f]{40}', s) for s in (base, head)):
        raise ValueError('invalid event commit SHA')
    if head == '0' * 40:
        raise ValueError('deleted ref has no change HEAD to validate')
    git('cat-file', '-e', head + '^{commit}', cwd=cwd)
    if base == '0' * 40:
        default = event.get('repository', {}).get('default_branch')
        if isinstance(default, str) and event.get('ref') != 'refs/heads/' + default:
            # A newly published feature branch inherits maintained history. Its
            # change is relative to the fetched default branch, not an empty repo.
            git('check-ref-format', 'refs/heads/' + default, cwd=cwd)
            target = git('rev-parse', '--verify', 'refs/remotes/origin/' + default + '^{commit}', cwd=cwd)
            base = git('merge-base', target, head, cwd=cwd)
        else:
            # Initial default-branch push / metadata-free fixtures: all files.
            base = git('hash-object', '-w', '-t', 'tree', '--stdin', cwd=cwd, input='')
    else:
        git('cat-file', '-e', base + '^{commit}', cwd=cwd)
        if event_name == 'pull_request':
            base = git('merge-base', base, head, cwd=cwd)
    return base, head


def check(event_name, event, cwd=None):
    base, head = revisions(event_name, event, cwd)
    print(f'Whitespace committed diff: {base}..{head}', flush=True)
    return subprocess.run(['git', 'diff', '--check', base, head, '--'], cwd=cwd).returncode


def main():
    try:
        with open(os.environ['GITHUB_EVENT_PATH'], encoding='utf-8') as stream:
            event = json.load(stream)
        return check(os.environ['GITHUB_EVENT_NAME'], event)
    except (KeyError, ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(f'ERROR: cannot establish committed whitespace scope: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
