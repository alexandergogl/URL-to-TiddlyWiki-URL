"""
Alfred script: Convert an URL to a TiddlyWiki URL.
"""

import sys


def url_to_tiddly_url(Text, Delimiter=' '):
    splitted = Text.split(Delimiter, 1)

    # Format link
    if len(splitted) > 1:
        # TiddlyWiki link with link description
        entry = "[[%s|%s]]" % (splitted[1], splitted[0])
    else:
        # TiddlyWiki link without link description
        entry = "[[%s]]" % splitted[0]

    return entry


input = sys.argv[1]
entry = url_to_tiddly_url(input)
print(entry)
