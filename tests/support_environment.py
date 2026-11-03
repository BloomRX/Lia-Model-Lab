"""Explicit synthetic Linux envelope for legacy supervisor protocol tests on any OS."""
def synthetic_ram(report):
    report['memory'] = dict(platform='linux', effective_total_bytes=10**12,
                            effective_available_bytes=report['ram']['available_bytes'])
    return report


def synthetic_launcher(windows):
    """Fabricated producer receipt ONLY for existing temp protocol unit tests."""
    if windows is None:
        return
    from lia_lab.windows_launcher import contract, CREATE_FLAGS, KILL_ON_CLOSE, ACTIVE_PROCESS, JOB_MEMORY, select_commit_limit
    report=windows['report']
    cap,reason=select_commit_limit(windows['config'],windows['observation'],windows['assessment'])
    report.update(schema_version=1,platform='windows',job_named=False,job_state='empty-confirmed',
        config=windows['config'], method=contract()['method'], applied_limit_flags=KILL_ON_CLOSE|ACTIVE_PROCESS|(JOB_MEMORY if cap else 0),
        creation_flags=CREATE_FLAGS, associated_before_resume=True, resumed=True,
        job_handle_inherited=False, security_sandbox=False, tree_empty_confirmed=True,
        process_exit_confirmed=True, active_processes=0, total_processes=1,
        cleanup_complete=True, cleanup_errors=[], termination_reason='natural-exit',primary_exit_code=0,
        commit_limit_bytes=cap, commit_limit_not_applied_reason=reason, synthetic_test_only=True,
        handle_closures=[dict(kind=k,closed=True) for k in ('job','process','thread','stdio-input','stdio-output')])
