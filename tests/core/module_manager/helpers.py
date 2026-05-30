def init_ok(deps=None):
    class _Mod:
        async def some_method(self):
            return None
    return _Mod()


def init_fail(deps=None):
    raise RuntimeError("intentional init failure")


def start_ok(instance, deps=None):
    pass


def stop_ok(instance):
    pass
