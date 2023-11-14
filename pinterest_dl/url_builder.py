#!/sur/bin/env python3
"""
function to build url request to pinterest
"""

import json
import time
from urllib.parse import urlencode, quote_plus


def build_url(url, options, source_url="/", context=None):
    """
    build url for request
    """

    query = {
        'source_url': source_url,
        'data': json.dumps({
            'options': options,
            'context': context
        }),
        '_': '%s' % int(time.time() * 1000)
    }

    if isinstance(query, str):
        query = quote_plus(query)
    else:
        query = urlencode(query)
    query = query.replace('+', '%20')

    url = f'{url}?{query}'

    return url
