"""Explicit synthetic Linux envelope for legacy supervisor protocol tests on any OS."""
def synthetic_ram(report):
    report['memory'] = dict(platform='linux', effective_total_bytes=10**12,
                            effective_available_bytes=report['ram']['available_bytes'])
    return report
