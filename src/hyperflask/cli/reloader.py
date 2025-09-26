from werkzeug._reloader import WatchdogReloaderLoop, reloader_loops
import os.path


# watchdog is a dependency of hyperflask so it would always be selected as the reloader
class WatchdogWithExtraFilesPatternsReloaderLoop(WatchdogReloaderLoop):
    def __init__(self, *args, extra_files=None, **kwargs):
        # VERY HACKY SOLUTION !
        # in werkzeug reloader, it is not possible to add patterns as extra_files
        # to circumvent this and avoid copy/pasting big chunk of code, we patch os.path.abspath
        # which is used to process the list of extra_files in the __init__
        extra_files = list(extra_files) if extra_files else []
        extra_files.append("*.jpy")
        abspath = os.path.abspath
        def patched_abspath(path):
            if path.startswith("*."):
                return path
            return abspath(path)
        os.path.abspath = patched_abspath
        super().__init__(*args, extra_files=extra_files, **kwargs)
        os.path.abspath = abspath


reloader_loops["auto"] = WatchdogWithExtraFilesPatternsReloaderLoop
