import os
import re
import pathlib
import functools
from collections import namedtuple

DEFINE = namedtuple('DEFINE', ('name', 'params', 'token', 'line'), defaults=('', [], '', ''))
TOKEN = namedtuple('DEFINE', ('name', 'params', 'line'), defaults=('', '', ''))

REGEX_TOKEN = r'(?P<NAME>[A-Z_][A-Z0-9_]+)'
REGEX_DEFINE = r'#define\s+'+REGEX_TOKEN+r'(?:\((?P<PARAMS>[\w, ]+)\))*\s*(?P<TOKEN>[\w\d_, +*!=<>&|\/\-\(\)]+)*'
BIT = lambda n : 1 << n

class Parser():
    defs = {} # dict of DEFINE
    debug = True
    iterate = 0

    def __init__(self):
        pass
    
    def insert_define(self, name, params=None, token=None):
        new_params = params or []
        new_token = token or ''
        self.defs[name] = DEFINE(
            name=name,
            params=new_params,
            token=new_token,
        )
    
    def strip_token(self, token):
        if token == None:
            return None
        token = token.strip()
        inline_comment_regex = r'\/\*[\w\d_, +*!=<>&|\-\(\)]+\*\/'
        comments = list(re.finditer(inline_comment_regex, token))
        if len(comments):
            for match in comments:
                token = token.replace(match.group(0), '')
        return token
    
    def _try_eval_num(self, token):
        try:
            return eval(token)
        except:
            return None
        
    def _read_file_lines(self, filepath, func, try_if_else = False):
        regex_line_break = r'\\\s*'
        regex_line_comment = r'\s*\/\/.+'

        if_depth = 0
        if_true_bmp = 1 # bitmap for every #if statement
        if_done_bmp = 1 # bitmap for every #if statement
        with open(filepath, 'r') as fs:
            multi_lines = ''
            for line in fs.readlines():
                line = re.sub(regex_line_comment, '', line.strip())

                if try_if_else:
                    match_if = re.match(r'#if((?P<NOT>n*)def)*\s+(?P<TOKEN>.+)', line)
                    match_elif = re.match(r'#elif\s+(?P<TOKEN>.+)', line)
                    match_else = re.match(r'#else.*', line)
                    match_endif = re.match(r'#endif.*', line)
                    if match_if:
                        if_depth += 1
                        if_token = self.expand_token(match_if.group('TOKEN'), raise_key_error=False)
                        if_true_bmp |= BIT(if_depth) * (eval(if_token) ^ (match_if.group('NOT') != None))
                    elif match_elif:
                        if_token = self.expand_token(match_elif.group('TOKEN'), raise_key_error=False)
                        if_true_bmp |= (BIT(if_depth) * (eval(if_token)))
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
    
    '''
    TODO: read_folder_h method,
    parse the included files first with self.read_h then try expand #if expression with self.expand_token
    '''
    
    def read_h(self, filepath, try_if_else=False):

        def insert_def(line):
            define = self._get_define(line)
            if define == None:
                return
            # if len(define.params):
            #     return
            self.defs[define.name] = define

        self._read_file_lines(filepath, insert_def, try_if_else)
    
    def find_tokens(self, token, raise_key_error=True):
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
                elif raise_key_error:
                    raise KeyError(f'token \'{_token}\' is not defined!')
                ret_tokens.append(TOKEN(name=_token, params=params, line=_token+params))
            return ret_tokens
        else:
           return []
    
    # @functools.lru_cache
    def expand_token(self, token, raise_key_error=True):
        expanded_token = self.strip_token(token)
        self.iterate += 1
        if self.iterate > 20 and self.debug:
            print(f'{" "*((self.iterate-20)//5)}{self.iterate:3} {token}')

        tokens = self.find_tokens(expanded_token, raise_key_error)
        if len(tokens):
            word_boundary = lambda word: r'\b' + word + r'\b'
            for _token in tokens:
                name = _token.name
                params = self.strip_token(_token.params)
                if len(params):
                    # Expand all the parameters first
                    for p_tok in self.find_tokens(params, raise_key_error):
                        params = params.replace(
                            p_tok.line,
                            self.expand_token(p_tok.line, raise_key_error)
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
                        expanded_token = self.expand_token(expanded_token, raise_key_error)
                    elif raise_key_error:
                        raise KeyError(f'token \'{name}\' is not defined!')
                    # else:
                    #     expanded_token = expanded_token.replace(_token.line, '(0)')
                elif name is not expanded_token:
                    params = self.expand_token(_token.line, raise_key_error)
                    expanded_token = re.sub(word_boundary(_token.line), params, expanded_token)
                    # expanded_token = expanded_token.replace(match.group(0), self.expand_token(match.group(0)))
                elif name not in self.defs:
                    expanded_token = expanded_token.replace(_token.line, '(0)')

        if expanded_token in self.defs:
            expanded_token = self.expand_token(self.defs[token].token, raise_key_error)

        return expanded_token

    def get_expand_defines(self, filepath, try_if_else=False):
        defines = []

        def expand_define(line):
            # TODO: process include files first
            define = self._get_define(line)
            if define == None:
                return
            self.iterate = 0
            token = self.expand_token(define.token)
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

        self._read_file_lines(filepath, expand_define, try_if_else)
        return defines
    
    def get_expand_define(self, macro_name):
        if macro_name not in self.defs:
            return ''
        
        define = self.defs[macro_name]
        token = define.token
        expanded_token = self.expand_token(token)

        return DEFINE(
            name=macro_name,
            params=define,
            token=expanded_token,
            line=define.line
        )

if __name__ == '__main__':
    p = Parser()
    inc_path = './samples'
    for inc_file in pathlib.Path(inc_path).glob('**/*.h'):
        p.read_h(inc_file)

    p.insert_define(name='ENV', token='1')
    defines = p.get_expand_defines('./samples/address_map.h')
    print(defines)
