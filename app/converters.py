from werkzeug.routing import BaseConverter


class RegionConverter(BaseConverter):
    """Kod regionu: dwie wielkie litery."""

    regex = "[A-Z]{2}"

    def to_url(self, value):
        return str(value).upper()
