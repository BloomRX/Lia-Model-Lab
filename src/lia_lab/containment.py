"""Explicit resource controls and process supervision, NOT an OS security sandbox."""
import os
import shutil
import signal
import subprocess
import sys

from .io import LabError


def policy(profile, timeout, device):
    if profile not in {'portable-process', 'linux-rlimit', 'linux-netns-rlimit'}:
        raise LabError('unknown containment profile')
    if profile != 'portable-process' and (sys.platform != 'linux' or device != 'cpu'):
        raise LabError('linux-rlimit is implemented only for Linux CPU; no silent fallback')
    netns = profile == 'linux-netns-rlimit'
    if netns and not shutil.which('unshare'):
        raise LabError('unshare missing; no network fallback')
    return {'network_launcher': shutil.which('unshare') if netns else None,
            'supervisor_netns_inode': os.stat('/proc/self/ns/net').st_ino if netns else None,
            'profile': profile, 'security_sandbox': False, 'network_policy': 'required-linux-IP-network-namespace' if netns else 'not-applied',
            'filesystem_policy': 'not-applied', 'gpu_memory_hard_limit': 'not-applied',
            'descendant_cleanup': 'posix-process-group-not-escape-proof' if os.name == 'posix' else 'worker-only-no-job-object',
            'limits': {'cpu_seconds': timeout * 4, 'address_space_bytes': 8 * 1024**3,
                       'file_bytes': 64 * 1024**2, 'open_files': 128, 'user_processes_threads': 128}
                       if profile != 'portable-process' else None,
            'os_resource_limits': 'required-in-worker' if profile != 'portable-process' else 'not-applied-explicit-portable-profile'}


def apply_limits(settings):
    if settings['profile'] == 'portable-process':
        return settings
    if sys.platform != 'linux':
        raise LabError('Linux limits requested on unsupported OS')
    if settings['profile'] == 'linux-netns-rlimit':
        inode = os.stat('/proc/self/ns/net').st_ino
        if inode == settings['supervisor_netns_inode']:
            raise LabError('network namespace not applied; refusing fallback')
        settings = {**settings, 'network_policy':'applied-new-linux-IP-network-namespace', 'effective_netns_inode':inode}
    import resource
    names = {'cpu_seconds': resource.RLIMIT_CPU, 'address_space_bytes': resource.RLIMIT_AS,
             'file_bytes': resource.RLIMIT_FSIZE, 'open_files': resource.RLIMIT_NOFILE,
             'user_processes_threads': resource.RLIMIT_NPROC}
    for key, kind in names.items():
        wanted = settings['limits'][key]
        _, hard = resource.getrlimit(kind)
        bound = wanted if hard == resource.RLIM_INFINITY else min(wanted, hard)
        resource.setrlimit(kind, (bound, bound))
    actual = {key: resource.getrlimit(kind)[0] for key, kind in names.items()}
    return {**settings, 'os_resource_limits': 'applied', 'effective_limits': actual,
            'nproc_caveat':'per-real-UID count, not PID namespace; privileged accounts may bypass enforcement'}


def supervise(command, env, log, timeout):
    """Kill the POSIX group on timeout/interruption; Windows only the direct child."""
    process = subprocess.Popen(command, env=env, stdout=log, stderr=log, start_new_session=os.name == 'posix')
    try:
        return process.wait(timeout=timeout)
    except (subprocess.TimeoutExpired, KeyboardInterrupt):
        if os.name == 'posix':
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        else:
            process.kill()
        process.wait()
        raise


def launch_command(command, settings):
    if settings['profile'] == 'linux-netns-rlimit':
        return [settings['network_launcher'], '--user', '--map-root-user', '--net', '--', *command]
    return command
