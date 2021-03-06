import os
import pathlib
import re

# import functools
from collections import namedtuple
from contextlib import contextmanager
from pprint import pformat, pprint

DEFINE = namedtuple("DEFINE", ("name", "params", "token", "line"), defaults=("", [], "", ""))
TOKEN = namedtuple("DEFINE", ("name", "params", "line"), defaults=("", "", ""))

REGEX_TOKEN = r"\b(?P<NAME>[a-zA-Z_][a-zA-Z0-9_]+)\b"
REGEX_DEFINE = (
    r"#define\s+" + REGEX_TOKEN + r"(?P<HAS_PAREN>\((?P<PARAMS>[\w, ]*)\))*\s*(?P<TOKEN>.+)*"
)
REGEX_UNDEF = r"#undef\s+" + REGEX_TOKEN
REGEX_INCLUDE = r'#include\s+["<](?P<PATH>.+)[">]\s*'
BIT = lambda n: 1 << n


class DuplicatedIncludeError(Exception):
    """assert when parser can not found ONE valid include header file."""


def is_junction(path):
    try:
        return bool(os.readlink(path))
    except OSError:
        return False


def get_junction_folder(path, root=""):
    paths = pathlib.Path(path).parts
    roots = pathlib.Path(root).parts
    top_to_bottoms = (paths[0: len(roots) + i + 1] for i in range(len(paths) - len(roots)))
    # top_to_bottoms = (paths[0: i + 1] for i in range(len(paths)))
    for ps in top_to_bottoms:
        path = os.path.join(*ps)
        if is_junction(path):
            return path

    return None


class Parser:
    debug = False
    iterate = 0

    def __init__(self):
        self.reset()

    def reset(self):
        self.defs = {}  # dict of DEFINE
        self.folder = ""

    def _debug_log(self, *args):
        if self.debug:
            print(*args)

    def insert_define(self, name, *, params=None, token=None):
        ''' params: list of parameters required, token: define body '''
        new_params = params or []
        new_token = token or ""
        self.defs[name] = DEFINE(
            name=name,
            params=new_params,
            token=new_token,
        )

    def remove_define(self, name):
        if name not in self.defs:
            raise KeyError(f"token '{name}' is not defined!")

        del self.defs[name]

    def strip_token(self, token, reserve_whitespace=False):
        if token == None:
            return None
        if reserve_whitespace:
            token = token.rstrip()
        else:
            token = token.strip()
        inline_comment_regex = r"\/\*[^\/]+\*\/"
        comments = list(re.finditer(inline_comment_regex, token))
        if len(comments):
            for match in comments:
                token = token.replace(match.group(0), "")
        return token

    def try_eval_num(self, token):
        REG_LITERALS = [
            r"\b(?P<NUM>[0-9]+)([ul]|ull?|ll?u|ll)\b",
            r"\b(?P<NUM>0b[01]+)([ul]|ull?|ll?u|ll)\b",
            r"\b(?P<NUM>0[0-7]+)([ul]|ull?|ll?u|ll)\b",
            r"\b(?P<NUM>0x[0-9a-f]+)([ul]|ull?|ll?u|ll)\b",
        ]
        # remove integer literals type hint
        for reg in REG_LITERALS:
            for match in re.finditer(reg, token, re.IGNORECASE):
                literal_integer = match.group(0)
                number = match.group("NUM")
                token = token.replace(literal_integer, number)
        # calculate size of special type
        # transform type cascading to bit mask for equivalence calculation
        for sz_log2, special_type in enumerate(("U8", "U16", "U32", "U64")):
            # limitation:
            #   for equation like (U32)1 << (U32)(15) may be calculated to wrong value
            #   due to operator order
            data_sz = 2**sz_log2
            # sizeof(U16) -> 2
            token = re.sub(rf"sizeof\(\s*{special_type}\s*\)", str(data_sz), token)
            # (U16)x -> 0xFFFF & x
            token = re.sub(
                rf"\(\s*{special_type}\s*\)", "0x" + "F" * data_sz * 2 + " & ", token
            )
        try:
            # syntax translation from C -> Python
            token = token.replace("/", "//")
            token = token.replace("&&", " and ")
            token = token.replace("||", " or ")
            return int(eval(token))
        except:
            return None

    def _read_file_lines(
        self,
        filepath,
        func,
        try_if_else=False,
        ignore_header_guard=False,
        reserve_whitespace=False,
    ):
        regex_line_break = r"\\\s*$"
        regex_line_comment = r"\s*\/\/.*$"

        if_depth = 0
        if_true_bmp = 1  # bitmap for every #if statement
        if_done_bmp = 1  # bitmap for every #if statement
        first_guard_token = True
        is_block_comment = False
        with open(filepath, "r", errors="replace") as fs:
            multi_lines = ""
            for line in fs.readlines():

                if not is_block_comment:
                    if "/*" in line:  # start of block comment
                        block_comment_start = line.index("/*")
                        is_block_comment = "*/" not in line
                        block_comment_ending = (
                            line.index("*/") + 2 if not is_block_comment else len(line)
                        )
                        line = line[:block_comment_start] + line[block_comment_ending:]
                        if is_block_comment:
                            multi_lines += line

                if is_block_comment:
                    if "*/" in line:  # end of block comment
                        line = line[line.index("*/") + 2 :]
                        is_block_comment = False
                    else:
                        continue

                line = re.sub(
                    regex_line_comment, "", self.strip_token(line, reserve_whitespace)
                )

                if try_if_else:
                    match_if = re.match(r"#if((?P<NOT>n*)def)*\s*(?P<TOKEN>.+)", line)
                    match_elif = re.match(r"#elif\s*(?P<TOKEN>.+)", line)
                    match_else = re.match(r"#else.*", line)
                    match_endif = re.match(r"#endif.*", line)
                    if match_if:
                        if_depth += 1
                        token = match_if.group("TOKEN")
                        if_token = (
                            "0"  # header guard always uses #ifndef *
                            if ignore_header_guard and first_guard_token
                            else self.expand_token(token, try_if_else, raise_key_error=False)
                        )
                        if_token_val = bool(self.try_eval_num(if_token))
                        if_true_bmp |= BIT(if_depth) * (
                            if_token_val ^ (match_if.group("NOT") == "n")
                        )
                        first_guard_token = (
                            False if match_if.group("NOT") == "n" else first_guard_token
                        )
                    elif match_elif:
                        if_token = self.expand_token(
                            match_elif.group("TOKEN"), try_if_else, raise_key_error=False
                        )
                        if_token_val = bool(self.try_eval_num(if_token))
                        if_true_bmp |= BIT(if_depth) * if_token_val
                        if_true_bmp &= ~(BIT(if_depth) & if_done_bmp)
                    elif match_else:
                        if_true_bmp ^= BIT(if_depth)  # toggle state
                        if_true_bmp &= ~(BIT(if_depth) & if_done_bmp)
                    elif match_endif:
                        if_true_bmp &= ~BIT(if_depth)
                        if_done_bmp &= ~BIT(if_depth)
                        if_depth -= 1

                multi_lines += re.sub(regex_line_break, "", line)
                if re.search(regex_line_break, line):
                    continue
                single_line = re.sub(regex_line_break, "", multi_lines)
                if if_true_bmp == BIT(if_depth + 1) - 1:
                    func(single_line)
                    if_done_bmp |= BIT(if_depth)
                elif try_if_else and (match_if or match_elif or match_else or match_endif):
                    func(single_line)
                multi_lines = ""

    def _get_define(self, line):
        match = re.match(REGEX_UNDEF, line)
        if match is not None:
            name = match.gropu("NAME")
            if name in self.defs:
                del self.defs[match.group("NAME")]
            return

        match = re.match(REGEX_DEFINE, line)
        if match == None:
            return

        name = match.group("NAME")
        parentheses = match.group("HAS_PAREN")
        params = match.group("PARAMS")
        param_list = [p.strip() for p in params.split(",")] if params else []
        match_token = match.group("TOKEN")
        token = self.strip_token(match_token) or "(1)"

        """
        #define AAA     // params = None
        #define BBB()   // params = []
        #define CCC(a)  // params = ['a']
        """
        return DEFINE(
            name=name,
            params=param_list if parentheses else None,
            token=token,
            line=line,
        )

    def read_folder_h(self, directory, try_if_else=True):
        self.folder = directory

        # glob all header files that not located in junction (aka. Windows symlink)
        header_files = []
        #   glob files are sorted, so just cache previous found junction folder
        prev_folder, junction = "", None
        for f in pathlib.Path(directory).glob("**/*.h"):
            if junction and str(f).startswith(junction):
                # skip file inside junction
                continue
            if (dir := os.path.dirname(f)) and dir != prev_folder:
                prev_folder = dir
                if (j := get_junction_folder(os.path.dirname(f), root=directory)):
                    junction = j
                else:
                    header_files.append(f)
            else:
                header_files.append(f)

        header_done = set()
        pre_defined_keys = self.defs.keys()

        def get_included_file(path, src_file):
            included_files = [
                str(h)
                for h in header_files
                if path in str(h) and os.path.basename(path) == os.path.basename(h)
            ]
            if len(included_files) > 1:
                included_files = [
                    f for f in included_files if str(f).replace(path, "") in str(src_file)
                ]

            if len(included_files) > 1:
                raise DuplicatedIncludeError(pformat(included_files, indent=4, width=120))

            return included_files[0] if len(included_files) else None

        def read_header(filepath):
            if filepath == None or filepath in header_done:
                return

            def insert_def(line):
                match_include = re.match(REGEX_INCLUDE, line)
                if match_include != None:
                    # parse included file first
                    path = match_include.group("PATH")
                    included_file = get_included_file(path, src_file=filepath)
                    read_header(included_file)
                define = self._get_define(line)
                if define == None or define.name in pre_defined_keys:
                    return
                self.defs[define.name] = define

            try:
                self._read_file_lines(filepath, insert_def, try_if_else)
            except UnicodeDecodeError as e:
                print(f"Fail to open {filepath!r}. {e}")

            if filepath in header_files:
                self._debug_log("Read File: %s", filepath)
                header_done.add(filepath)

        for header_file in header_files:
            read_header(header_file)

        return True

    def read_h(self, filepath, try_if_else=False):
        def insert_def(line):
            define = self._get_define(line)
            if define == None:
                return
            # if len(define.params):
            #     return
            self.defs[define.name] = define

        try:
            self._read_file_lines(filepath, insert_def, try_if_else)
        except UnicodeDecodeError as e:
            print(f"Fail to open :{filepath}. {e}")

    @contextmanager
    def read_c(self, filepath, try_if_else=False):
        """use `with` context manager for having temporary tokens defined in .c source file"""

        defs = {}

        def insert_def(line):
            define = self._get_define(line)
            if define == None:
                return
            # if len(define.params):
            #     return
            defs[define.name] = define

        try:
            self._read_file_lines(filepath, insert_def, try_if_else)
            for define in defs.values():
                self.insert_define(
                    name=define.name,
                    params=define.params,
                    token=define.token,
                )
            yield
        except UnicodeDecodeError as e:
            print(f"Fail to open :{filepath}. {e}")
        finally:
            for define in defs.values():
                del self.defs[define.name]

    def find_tokens(self, token):
        def fine_token_params(params):
            if len(params) and params[0] != "(":
                return None
            # (() ())
            brackets = 0
            new_params = ""
            for c in params:
                brackets += (c == "(") * 1 + (c == ")") * -1
                new_params += c
                if brackets == 0:
                    break
            return new_params

        if self.try_eval_num(token):
            return []

        # remove string value in token
        regex_str = r'"[^"]+"'
        token = re.sub(regex_str, "", token)

        tokens = list(re.finditer(REGEX_TOKEN, token))
        if len(tokens):
            ret_tokens = []
            for match in tokens:
                _token = match.group("NAME")
                params = None
                if _token in self.defs:
                    params_required = self.defs[_token].params
                    end_pos = match.end()
                    if params_required is not None:
                        params = fine_token_params(token[end_pos:])
                param_str = params if params else ""
                ret_tokens.append(TOKEN(name=_token, params=params, line=_token + param_str))
            return ret_tokens
        else:
            return []

    def _check_parentheses(self, token):
        lparan_cnt = 0
        rparan_cnt = 0
        for char in token:
            if char == "(":
                lparan_cnt += 1
            if char == ")":
                rparan_cnt += 1
        return lparan_cnt == rparan_cnt

    def _iter_arg(self, params):
        if len(params) == 0:
            return []
        assert params[0] == "(" and params[-1] == ")"
        parma_list = params[1:-1].split(",")
        arguments = []
        for arg in parma_list:
            arguments.append(arg.strip())
            prams_str = ",".join(arguments)
            if self._check_parentheses(prams_str):
                yield prams_str
                arguments = []

    # @functools.lru_cache
    def expand_token(self, token, try_if_else=False, raise_key_error=True):
        expanded_token = self.strip_token(token)
        self.iterate += 1
        if self.iterate > 20:
            self._debug_log(f'{" "*((self.iterate-20)//5)}{self.iterate:3} {token}')

        tokens = self.find_tokens(expanded_token)
        if len(tokens):
            word_boundary = lambda word: r"\b(##)*%s\b" % re.escape(word)
            for _token in tokens:
                name = _token.name
                params = self.strip_token(_token.params)
                if params is not None:
                    # Expand all the parameters first
                    for p_tok in self.find_tokens(params):
                        params = re.sub(
                            word_boundary(p_tok.line),
                            self.expand_token(p_tok.line, try_if_else, raise_key_error),
                            params,
                        )
                        processed = list(t for t in tokens if p_tok.name == t.name)
                        if len(processed):
                            tokens.remove(processed[0])
                    if name in self.defs:
                        old_params = self.defs[name].params or []
                        new_params = list(self._iter_arg(params))
                        new_token = self.defs[name].token
                        # Expand the token
                        for old_p, new_p in zip(old_params, new_params):
                            new_token = re.sub(word_boundary(old_p), new_p, new_token)
                        # expanded_token = expanded_token.replace(_token.line, new_token)
                        new_token_val = self.try_eval_num(new_token)
                        new_token = str(new_token_val) if new_token_val else new_token
                        if _token.line == name:
                            expanded_token = re.sub(
                                word_boundary(_token.line), new_token, expanded_token
                            )
                        else:
                            expanded_token = expanded_token.replace(_token.line, new_token)
                        # Take care the remaining tokens
                        expanded_token = self.expand_token(
                            expanded_token, try_if_else, raise_key_error
                        )
                    elif raise_key_error:
                        raise KeyError(f"token '{name}' is not defined!")
                    # else:
                    #     expanded_token = expanded_token.replace(_token.line, '(0)')
                elif name is not expanded_token:
                    params = self.expand_token(_token.line, try_if_else, raise_key_error)
                    expanded_token = re.sub(word_boundary(_token.line), params, expanded_token)
                    # expanded_token = expanded_token.replace(match.group(0), self.expand_token(match.group(0)))

        if expanded_token in self.defs:
            expanded_token = self.expand_token(
                self.defs[token].token, try_if_else, raise_key_error
            )

            # try to eval the value, to reduce the bracket count
            token_val = self.try_eval_num(expanded_token)
            if token_val is not None:
                expanded_token = str(token_val)

        return expanded_token

    def get_expand_defines(self, filepath, try_if_else=False, ignore_header_guard=True):
        defines = []

        def expand_define(line):
            define = self._get_define(line)
            if define == None:
                return
            self.iterate = 0
            token = self.expand_token(define.token, try_if_else, raise_key_error=False)
            if define.name in self.defs:
                token_val = self.try_eval_num(token)
                if token_val is not None:
                    self.defs[define.name] = self.defs[define.name]._replace(
                        token=str(token_val)
                    )
            defines.append(
                DEFINE(
                    name=define.name,
                    params=define.params,
                    token=token,
                    line=line,
                )
            )

        self._read_file_lines(filepath, expand_define, try_if_else, ignore_header_guard)
        return defines

    def get_expand_define(self, macro_name, try_if_else=False):
        if macro_name not in self.defs:
            return None

        define = self.defs[macro_name]
        token = define.token
        expanded_token = self.expand_token(token, try_if_else, raise_key_error=False)

        return DEFINE(name=macro_name, params=define, token=expanded_token, line=define.line)

    def get_preprocess_source(self, filepath, try_if_else=False):
        lines = []

        def read_line(line):
            lines.append(line)

        ignore_header_guard = os.path.splitext(filepath)[1] == ".h"
        self._read_file_lines(
            filepath, read_line, try_if_else, ignore_header_guard, reserve_whitespace=True
        )
        return lines


if __name__ == "__main__":
    p = Parser()
    p.read_folder_h("./samples")

    defines = p.get_expand_defines("./samples/address_map.h", try_if_else=True)
    for define in defines:
        val = p.try_eval_num(define.token)
        token = hex(val) if val and val > 0x08000 else define.token
        print(f"{define.name:25} {token}")
