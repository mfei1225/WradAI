def __load():
    import os, sys, imp
    ext = 'Quartz/PDFKit/_PDFKit.so'
    for path in sys.path:
        if not path.endswith('lib-dynload'):
            continue
        ext_path = os.path.join(path, ext)
        if os.path.exists(ext_path):
            mod = imp.load_dynamic(__name__, ext_path)
            break
    else:
        raise ImportError(repr(ext) + " not found")
__load()
del __load
