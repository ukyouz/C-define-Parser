import os
import re
import pathlib
# import functools
from collections import namedtuple

DEFINE = namedtuple('DEFINE', ('name', 'params', 'token', 'line'), defaults=('', [], '', ''))
TOKEN = namedtuple('DEFINE', ('name', 'params', 'line'), defaults=('', '', ''))

REGEX_TOKEN = r'\b(?P<NAME>[A-Z_][A-Z0-9_]+)\b'
REGEX_DEFINE = r'#define\s+'+REGEX_TOKEN+r'(?:\((?P<PARAMS>[\w, ]+)\))*\s*(?P<TOKEN>[\w\d_, +*!=<>&|\/\-\(\)]+)*'
REGEX_INCLUDE = r'#include\s+["<](?P<PATH>.+)[">]\s*'
BIT = lambda n : 1 << n

class Parser():
    debug = False
    iterate = 0

    def __init__(self):
        self.defs = {} # dict of DEFINE
        pass

    def _debug_log(self, *args):
        if self.debug:
            print(*args)
    
    def insert_define(self, name, params=None, token=None):
        new_params = params or []
        new_token = token or ''
        self.defs[name] = DEFINE(
            name=name,
            params=new_params,
            token=new_token,
        )
    
    def remove_define(self, name):
        if name not in self.defs:
            raise KeyError(f'token \'{name}\' is not defined!')

        del self.defs[name]

    def strip_token(self, token):
        if token == None:
            return None
        token = token.strip()
        inline_comment_regex = r'\/\*[^\/]+\*\/'
        comments = list(re.finditer(inline_comment_regex, token))
        if len(comments):
            for match in comments:
                token = token.replace(match.group(0), '')
        return token

    def _try_eval_num(self, token):
        try:
            return eval(token.replace('/', '//'))
        except:
            return None

    def _read_file_lines(self, filepath, func, try_if_else=False, ignore_header_guard=False):
        regex_line_break = r'\\\s*'
        regex_line_comment = r'\s*\/\/.+'

        if_depth = 0
        if_true_bmp = 1 # bitmap for every #if statement
        if_done_bmp = 1 # bitmap for every #if statement
        with open(filepath, 'r') as fs:
            multi_lines = ''
            for line in fs.readlines():
                # TODO: multilines comment with /* */
                line = re.sub(regex_line_comment, '', self.strip_token(line))

                if try_if_else:
                    match_if = re.match(r'#if((?P<NOT>n*)def)*\s*(?P<TOKEN>.+)', line)
                    match_elif = re.match(r'#elif\s*(?P<TOKEN>.+)', line)
                    match_else = re.match(r'#else.*', line)
                    match_endif = re.match(r'#endif.*', line)
                    if match_if:
                        if_depth += 1
                        token = match_if.group('TOKEN')
                        if_token = ('0' # header guard always uses #ifndef __*
                            if ignore_header_guard and token.startswith('__')
                            else self.expand_token(token, try_if_else, raise_key_error=False)
                        )
                        if_token_val = self._try_eval_num(if_token) or 0
                        if_true_bmp |= BIT(if_depth) * (if_token_val ^ (match_if.group('NOT') == 'n'))
                    elif match_elif:
                        if_token = self.expand_token(match_elif.group('TOKEN'), try_if_else, raise_key_error=False)
                        if_token_val = self._try_eval_num(if_token) or 0
                        if_true_bmp |= (BIT(if_depth) * if_token_val)
                        if_true_bmp &= ~(BIT(if_depth) & if_done_bmp)
                    elif match_else:
                        if_true_bmp ^= BIT(if_depth) # toggle state
                        if_true_bmp &= ~(BIT(if_depth) & if_done_bmp)
                    elif match_endif:
                        if_true_bmp &= ~BIT(if_depth)
                        if_done_bmp &= ~BIT(if_depth)
                        if_depth -= 1

                multi_lines += line
                if re.search(regex_line_break, line):
                    continue
                single_line = re.sub(regex_line_break, '', multi_lines)
                if if_true_bmp == BIT(if_depth + 1) - 1:
                    func(single_line)
                    if_done_bmp |= BIT(if_depth)
                multi_lines = ''

    def _get_define(self, line):
        match = re.match(REGEX_DEFINE, line)
        if match == None:
            return

        name = match.group('NAME')
        params = match.group('PARAMS')
        param_list = [p.strip() for p in params.split(',')] if params else []
        match_token = match.group('TOKEN')
        token = self.strip_token(match_token) or '(1)'

        return DEFINE(
            name=name,
            params=param_list,
            token=token,
            line=line,
        )

    def read_folder_h(self, directory, try_if_else=True):
        header_files = list(pathlib.Path(directory).glob('**/*.h'))
        header_done = set()
        pre_defined_keys = self.defs.keys()

        def get_included_file(path):
            included_files = [str(h)
                for h in header_files
                if path in str(h) and
                os.path.basename(path) == os.path.basename(h)
            ]
            if len(included_files) > 1:
                raise NameError(', '.join(included_files))

            return included_files[0] if len(included_files) else None

        def read_header(filepath):
            if filepath == None or filepath in header_done:
                return

            def insert_def(line):
                match_include = re.match(REGEX_INCLUDE, line)
                if match_include != None:
                    # parse included file first
                    path = match_include.group('PATH')
                    included_file = get_included_file(path)
                    read_header(included_file)
                define = self._get_define(line)
                if define == None or define.name in pre_defined_keys:
                    return
                self.defs[define.name] = define

            try:
                self._read_file_lines(filepath, insert_def, try_if_else)
            except UnicodeDecodeError:
                print(f'Fail to open {filepath!r} with UTF-8 encoding.')

            if filepath in header_files:
                self._debug_log('Read File: %s', filepath)
                header_done.add(filepath)
 
        for header_file in header_files:
            read_header(header_file)
    
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
        except UnicodeDecodeError:
            print(f'Fail to open :{filepath} with UTF-8 encoding.')
    
    def find_tokens(self, token):
        def fine_token_params(params):
            # (() ())
            brackets = 0
            new_params = ''
            for c in params:
                brackets += (c == '(') * 1 + (c == ')') * -1
                new_params += c
                if brackets == 0:
                    break
            return new_params
        if self._try_eval_num(token):
            return []
        tokens = list(re.finditer(REGEX_TOKEN, token))
        params = ''
        if len(tokens):
            ret_tokens = []
            for match in tokens:
                _token = match.group('NAME')
                if _token in self.defs:
                    params_required = self.defs[_token].params
                    end_pos = match.end()
                    if len(params_required):
                        params = fine_token_params(token[end_pos:])
                ret_tokens.append(TOKEN(name=_token, params=params, line=_token+params))
            return ret_tokens
        else:
           return []

    # @functools.lru_cache
    def expand_token(self, token, try_if_else=False, raise_key_error=True):
        expanded_token = self.strip_token(token)
        self.iterate += 1
        if self.iterate > 20:
            self._debug_log(f'{" "*((self.iterate-20)//5)}{self.iterate:3} {token}')

        tokens = self.find_tokens(expanded_token)
        if len(tokens):
            word_boundary = lambda word: r'\b' + word + r'\b'
            for _token in tokens:
                name = _token.name
                params = self.strip_token(_token.params)
                if len(params):
                    # Expand all the parameters first
                    for p_tok in self.find_tokens(params):
                        params = params.replace(
                            p_tok.line,
                            self.expand_token(p_tok.line, try_if_else, raise_key_error)
                        )
                        tokens.remove(next((t for t in tokens if p_tok.name == t.name)))
                    new_params = params[1:-1].split(',')
                    if name in self.defs:
                        new_token = self.defs[name].token
                        # Expand the token
                        for old_p, new_p in zip(self.defs[name].params, new_params):
                            new_token = re.sub(word_boundary(old_p), new_p, new_token)
                        expanded_token = expanded_token.replace(_token.line, new_token)
                        # Take care the remaining tokens
                        expanded_token = self.expand_token(expanded_token, try_if_else, raise_key_error)
                    elif raise_key_error:
                        raise KeyError(f'token \'{name}\' is not defined!')
                    # else:
                    #     expanded_token = expanded_token.replace(_token.line, '(0)')
                elif name is not expanded_token:
                    params = self.expand_token(_token.line, try_if_else, raise_key_error)
                    expanded_token = re.sub(word_boundary(_token.line), params, expanded_token)
                    # expanded_token = expanded_token.replace(match.group(0), self.expand_token(match.group(0)))

        if expanded_token in self.defs:
            expanded_token = self.expand_token(self.defs[token].token, try_if_else, raise_key_error)

            # try to eval the value, to reduce the bracket count
            token_val = self._try_eval_num(expanded_token)
            if token_val:
                expanded_token = str(token_val)

        return expanded_token

    def get_expand_defines(self, filepath, try_if_else=False, ignore_header_guard=True):
        defines = []

        def expand_define(line):
            define = self._get_define(line)
            if define == None:
                return
            self.iterate = 0
            token = self.expand_token(define.token, try_if_else)
            if define.name in self.defs:
                token_val = self._try_eval_num(token)
                if token_val:
                    self.defs[define.name] = self.defs[define.name]._replace(token=str(token_val))
            defines.append(DEFINE(
                name=define.name,
                params=define.params,
                token=token,
                line=line,
            ))

        self._read_file_lines(filepath, expand_define, try_if_else, ignore_header_guard)
        return defines
    
    def get_expand_define(self, macro_name, try_if_else=False):
        if macro_name not in self.defs:
            return None
        
        define = self.defs[macro_name]
        token = define.token
        expanded_token = self.expand_token(token, try_if_else)

        return DEFINE(
            name=macro_name,
            params=define,
            token=expanded_token,
            line=define.line
        )

if __name__ == '__main__':
    p = Parser()
    p.read_folder_h('./samples')

    defines = p.get_expand_defines('./samples/address_map.h', try_if_else=True)
    for define in defines:
        val = p._try_eval_num(define.token)
        token = hex(val) if val and val > 0x08000 else define.token
        print(f'{define.name:25} {token}')
