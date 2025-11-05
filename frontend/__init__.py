import sys

if sys.version_info >= (3, 8):
    from importlib.metadata import version as package_version

    version = package_version("django-jazzmin")
else:
    import pkg_resources

    version = pkg_resources.get_distribution("django-jazzmin").version
