import codecs
from typing import Optional

import orjson

from django.conf import settings
from django.core.handlers.wsgi import WSGIRequest
from rest_framework.exceptions import ParseError
from rest_framework.parsers import BaseParser

from shared.renderers import ORJSONRenderer


class ORJSONParser(BaseParser):
    """
    Parses JSON-serialized data  with the help of the `orjson` package.
    `orjson` is much more performant than the standard `json` package.
    """
    media_type = 'application/json'
    renderer_class = ORJSONRenderer
    
    def parse(
        self, stream: WSGIRequest, media_type: Optional[str] = None,
        parser_context: Optional[dict] = None
    ) -> dict:
        """
        Parses the incoming bytestream as JSON via `orjson`
        and returns the resulting data.
        """
        parser_context = parser_context or {}
        encoding = parser_context.get('encoding', settings.DEFAULT_CHARSET)
        
        try:
            decoded_stream = codecs.getreader(encoding)(stream)
            return orjson.loads(decoded_stream.read())
        except orjson.JSONDecodeError as exc:
            raise ParseError('JSON parse error - %s' % str(exc))
