import re

from typing import Iterable

REGEX_SYNTAX_LINE_COMMENT = re.compile(r"(.*?)(//.*)")
REGEX_SYNTAX_INLINE_COMMENT = re.compile(r"(.*)(/\*.*\*/)(.*)")

def remove_comment(texts: Iterable[str], keep_line_comment=False):

    def remove_oneline_comment(string) -> tuple[str, bool]:
        m = REGEX_SYNTAX_INLINE_COMMENT.match(string)
        if m:
            return remove_oneline_comment(m[1] + (' ' * len(m[2])) + m[3])

        m = re.match(r'(.*)(/\*.*)', string)
        if m:
            return (m[1], True)

        m = REGEX_SYNTAX_LINE_COMMENT.match(string)
        if m:
            if keep_line_comment:
                return (string, False)
            else:
                return (m[1], False)

        return (string, False)

    def remove_block_comment_end(string) -> tuple[str, bool]:
        m = re.match(r'(.*\*/)(.*)', string)
        if m:
            text_ret = (' ' * len(m[1])) + m[2]
            return text_ret, False
        else:
            return ('', True)

    multi_comment = False
    for line in texts:
        if multi_comment is False:
            clean_txt, multi_comment = remove_oneline_comment(line)
            yield clean_txt
        else:
            clean_txt, multi_comment = remove_block_comment_end(line)
            if multi_comment is False:
                clean_txt, multi_comment = remove_oneline_comment(clean_txt)
            yield clean_txt
