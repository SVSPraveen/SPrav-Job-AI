# conftest.py — Prevents blocked DLL plugins from crashing pytest startup.
# The langsmith pytest plugin (installed as a langchain/langgraph dependency)
# tries to import xxhash which is blocked by Windows Application Control policy
# on this machine. This file disables that plugin registration entirely.
collect_ignore_glob = []

def pytest_configure(config):
    """Deregister the langsmith plugin before it loads xxhash."""
    try:
        config.pluginmanager.set_blocked("langsmith")
    except Exception:
        pass
