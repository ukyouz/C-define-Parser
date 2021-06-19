import os
import re
import pathlib
import functools
from collections import namedtuple

class Parser():
    Define = namedtuple('Define', 'name, params, token, line')
    Token = namedtuple('Define', 'name, params, token')
    token_regex = r'(?P<NAME>[A-Z][A-Z0-9_]+)'
    define_regex = r'#define\s+(?P<NAME>[A-Z0-9_]+)(?:\((?P<PARAMS>[\w, ]+)\))*\s+(?P<TOKEN>[\w\d_, +*!=<>&|\/\-\(\)]+)'
    definitions = {} # array of Define
    iterate = 0

    def __init__(self):
        pass
    
    def insert_token(self, name, token):
        self.definitions[name] = self.Define(
            name=name,
            params=[],
            token=token,
            line='',
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
        
    def _read_file_lines(self, filepath, func, try_if_else = False):
        # define_off = 0
        line_break_regex = r'\\\s*'
        line_comment_regex = r'\s*\/\/.+'
        with open(filepath, 'r') as fs:
            multi_lines = ''
            for line in fs.readlines():
                line = line.strip()
                # TODO: expand if/elif/else expression
                multi_lines += re.sub(line_comment_regex, '', line)
                if re.search(line_break_regex, line):
                    continue
                single_line = re.sub(line_break_regex, '', multi_lines)
                func(single_line)
                multi_lines = ''
    
    '''
    TODO: read_folder_h method,
    parse the included files first with self.read_h then try expand #if expression with self.expand_token
    '''
    
    def read_h(self, filepath):
        def insert_def(line):
            match = re.match(self.define_regex, line)
            if match == None:
                return
            name = match.group('NAME')
            params = match.group('PARAMS')
            param_list = [p.strip() for p in params.split(',')] if params else []
            token = self.strip_token(match.group('TOKEN'))
            # if len(param_list):
            #     return
            self.definitions[name] = self.Define(
                name=name,
                params=param_list,
                token=token,
                line=line,
            )
        self._read_file_lines(filepath, insert_def)
    
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
        def is_valid_num(token):
            try:
                eval(token)
                return True
            except:
                return False
        if is_valid_num(token):
            return []
        tokens = list(re.finditer(self.token_regex, token))
        params = ''
        if len(tokens):
            ret_tokens = []
            for match in tokens:
                _token = match.group('NAME')
                if _token in self.definitions:
                    params_required = self.definitions[_token].params
                    end_pos = match.end()
                    if len(params_required):
                        params = fine_token_params(token[end_pos:])
                else:
                    print(f'token \'{_token}\' is not defined!')
                    raise KeyError
                ret_tokens.append(self.Token(name=_token, params=params, token=_token+params))
            return ret_tokens
        else:
           return []
    
    # @functools.lru_cache
    def expand_token(self, token):
        expanded_token = self.strip_token(token)
        self.iterate += 1
        if self.iterate > 20:
            print('???')
        tokens = self.find_tokens(expanded_token)
        if len(tokens):
            word_boundary = lambda word: r'\b' + word + r'\b'
            for _token in tokens:
                name = _token.name
                params = self.strip_token(_token.params)
                if len(params):
                    # Expand all the parameters first
                    for p_tok in self.find_tokens(params):
                        params = params.replace(p_tok.token, self.expand_token(p_tok.token))
                        tokens.remove(next((t for t in tokens if p_tok.name == t.name)))
                    new_params = params[1:-1].split(',')
                    if name in self.definitions:
                        new_token = self.definitions[name].token
                        # Expand the token
                        for old_p, new_p in zip(self.definitions[name].params, new_params):
                            new_token = re.sub(word_boundary(old_p), new_p, new_token)
                        expanded_token = expanded_token.replace(_token.token, new_token)
                        # Take care the remaining tokens
                        expanded_token = self.expand_token(expanded_token)
                    else:
                        print(f'token \'{name}\' is not defined!')
                        raise KeyError
                elif name is not expanded_token:
                    params = self.expand_token(_token.token)
                    expanded_token = re.sub(word_boundary(_token.token), params, expanded_token)
                    # expanded_token = expanded_token.replace(match.group(0), self.expand_token(match.group(0)))
        if expanded_token in self.definitions:
            expanded_token = self.expand_token(self.definitions[token].token)

        return expanded_token

    def get_expand_defines(self, filepath):
        defines = []
        def expand_define(line):
            # TODO: process include files first
            match = re.match(self.define_regex, line)
            if match == None:
                return
            params = match.group('PARAMS')
            param_list = [p.strip() for p in params.split(',')] if params else []
            if len(param_list):
                return
            name = match.group('NAME')
            self.iterate = 0
            token = self.strip_token(match.group('TOKEN'))
            token = self.expand_token(token)
            if name in self.definitions:
                try:
                    token = str(eval(token))
                except:
                    pass
                self.definitions[name] = self.definitions[name]._replace(token=token)
            defines.append(self.Define(
                name=name,
                params=param_list,
                token=token,
                line=line,
            ))
        self._read_file_lines(filepath, expand_define)
        return defines
    
    def get_expand_define(self, macro_name):
        if macro_name not in self.definitions:
            return ''
        
        define = self.definitions[macro_name]
        token = define.token
        expanded_token = self.expand_token(token)

        return self.Define(
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

    p.insert_token(name='ENV', token='1')
    defines = p.get_expand_defines('./samples/address_map.h')
    print(defines)
