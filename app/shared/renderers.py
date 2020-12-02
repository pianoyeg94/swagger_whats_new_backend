import decimal
import datetime
from typing import Optional, Any

import orjson

from django.db.models import QuerySet
from django.http.multipartparser import parse_header
from django.utils.encoding import force_str
from django.utils.functional import Promise
from rest_framework.renderers import BaseRenderer


def _default(obj: Any) -> Any:
    """
    Provides defaults to encode data types
    that cannot be natively handled by `orjson`
    """
    if isinstance(obj, Promise):
        return force_str(obj)
    elif isinstance(obj, datetime.timedelta):
        return str(obj.total_seconds())
    elif isinstance(obj, decimal.Decimal):
        return float(obj)
    elif isinstance(obj, QuerySet):
        return tuple(obj)
    elif isinstance(obj, bytes):
        return obj.decode()
    elif hasattr(obj, '__getitem__'):
        cls = (list if isinstance(obj, (list, tuple)) else dict)
        try:
            return cls(obj)
        except Exception:
            pass
    elif hasattr(obj, '__iter__'):
        return tuple(item for item in obj)


class ORJSONRenderer(BaseRenderer):
    """
    Renderer which serializes to JSON with the help of the `orjson` package.
    `orjson` is much more performant than the standard `json` package.
    """
    media_type = 'application/json'
    format = 'json'
    default = _default
    options = orjson.OPT_NON_STR_KEYS | orjson.OPT_SERIALIZE_NUMPY

    # We don't set a charset because JSON is a binary encoding,
    # that can be encoded as utf-8, utf-16 or utf-32.
    # See: https://www.ietf.org/rfc/rfc4627.txt
    # Also: http://lucumr.pocoo.org/2013/7/19/application-mimetypes-and-encodings/
    charset = None
    
    def needs_to_be_pretty_printed(
        self, accepted_media_type: str,
        renderer_context: dict
    ) -> bool:
        if accepted_media_type:
            # If the media type looks like 'application/json; indent=4',
            # then pretty print the result (via orjson's OPT_INDENT_2 option)
            base_media_type, params = parse_header(
                accepted_media_type.encode('ascii')
            )
            if params.get('indent'):
                return True
        
        if renderer_context.get('indent'):
            # If 'indent' is provided in the context,
            # then pretty print the result (via orjson's OPT_INDENT_2 option).
            # E.g. If we're being called by the BrowsableAPIRenderer.
            return True
        
        return False
    
    def render(
        self, data, accepted_media_type: Optional[str] = None,
        renderer_context: Optional[dict] = None
    ) -> bytes:
        """
        Render `data` into JSON via `orjson`, returning a bytestring.
        """
        if data is None:
            return b''
        
        renderer_context = renderer_context or {}
        needs_to_be_pretty_printed = self.needs_to_be_pretty_printed(
            accepted_media_type, renderer_context
        )
        options = self.options | orjson.OPT_INDENT_2 \
            if needs_to_be_pretty_printed else self.options
        
        result = orjson.dumps(data, default=self.default, option=options).decode()
        
        # We always fully escape \u2028 and \u2029 to ensure we output JSON
        # that is a strict javascript subset.
        # See: http://timelessrepo.com/json-isnt-a-javascript-subset
        result.replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')
        return result.encode()
