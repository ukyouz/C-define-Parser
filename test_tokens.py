import pytest
import pathlib
from C_DefineParser import Parser

@pytest.fixture
def parser_default():
	parser = Parser()
	inc_path = './samples'
	for inc_file in pathlib.Path(inc_path).glob('**/*.h'):
		parser.read_h(inc_file)
	return parser

@pytest.mark.parametrize("token, expected_value", [
	('ENV', 0),
	('SHOULD_BE_1', 1),
	('NVME_CMD_SIZE', 64),
	('0x00C0000', 0x0C0000),
	('ALIGN_2N(0x00C0000, 0xC00)', 0x0C0000),
	('MULTI_LINE_DEF', 3),
	('MULTI_LINE_DEF', 3),
	('(ALIGN_2N(BUFFER_BASE, BUFFER_ALIGN_SHIFT))', 0x4000000),
])
def test_token(parser_default, token, expected_value):
	token = parser_default.expand_token(token)
	value = eval(token)
	assert value == expected_value

@pytest.mark.parametrize("define, expected_value", [
	('ENV', 0),
	('BUFFER_ALIGN_SHIFT', 2),
	('MULTI_LINE_DEF', 3),
	('BUFFER_0_BASE', 0x4000000),
])
def test_define(parser_default, define, expected_value):
	define = parser_default.get_expand_define(define)
	value = parser_default.try_eval_num(define.token)
	assert value == expected_value

################################################################################

@pytest.fixture
def parser_public():
	parser = Parser()
	inc_path = './samples'
	parser.insert_define('ENV', token='ENV_PUBLIC')
	parser.read_folder_h(inc_path)
	return parser

@pytest.mark.parametrize("token, expected_value", [
	('ENV', 1),
	('NVME_CMD_SIZE', 64),
	('BUFFER_ALIGN_SHIFT', 2),
	('MULTI_LINE_DEF', 3),
	('(ALIGN_2N(BUFFER_BASE, BUFFER_ALIGN_SHIFT))', 0x4000000),
])
def test_token_pub(parser_public, token, expected_value):
	token = parser_public.expand_token(token)
	value = eval(token)
	assert value == expected_value

@pytest.mark.parametrize("define, expected_value", [
	('ENV', 1),
	('BUFFER_ALIGN_SHIFT', 2),
	('MULTI_LINE_DEF', 3),
	('BUFFER_0_BASE', 0x4000000),
])
def test_define_pub(parser_public, define, expected_value):
	define = parser_public.get_expand_define(define)
	value = parser_public.try_eval_num(define.token)
	assert value == expected_value

def test_stacks_pub(parser_public):
    def _compare(token1, token2):
        a = parser_public.expand_token(token1, try_if_else=True)
        b = parser_public.expand_token(token2, try_if_else=True)
        assert eval(a) == eval(b)
    _compare('NVME_IO_QUEUE0_BASE', 'NVME_IO_QUEUEN_BASE(0)')
    _compare('NVME_IO_QUEUE1_BASE', 'NVME_IO_QUEUEN_BASE(1)')
    _compare('NVME_IO_QUEUE2_BASE', 'NVME_IO_QUEUEN_BASE(2)')
    _compare('NVME_IO_QUEUE3_BASE', 'NVME_IO_QUEUEN_BASE(3)')
    _compare('NVME_IO_QUEUE4_BASE', 'NVME_IO_QUEUEN_BASE(4)')
    _compare('NVME_IO_QUEUE5_BASE', 'NVME_IO_QUEUEN_BASE(5)')
    _compare('NVME_IO_QUEUE6_BASE', 'NVME_IO_QUEUEN_BASE(6)')
    _compare('NVME_IO_QUEUE7_BASE', 'NVME_IO_QUEUEN_BASE(7)')

def test_existence_pub(parser_public):
	define = parser_public.get_expand_define('BUFFER_1_BASE', try_if_else=True)
	assert define == None

################################################################################

@pytest.fixture
def parser_test():
	parser = Parser()
	inc_path = './samples'
	parser.insert_define('ENV', token='ENV_TEST')
	parser.read_folder_h(inc_path, try_if_else=True)
	return parser

@pytest.mark.parametrize("token, expected_value", [
	('ENV', 3),
	('SHOULD_BE_1', 1),
	('NVME_CMD_SIZE', 64),
	('BUFFER_ALIGN_SHIFT', 2),
	('MULTI_LINE_DEF', 3),
	('(ALIGN_2N(BUFFER_BASE, BUFFER_ALIGN_SHIFT))', 0x4000000),
])
def test_token_test(parser_test, token, expected_value):
	token = parser_test.expand_token(token, try_if_else=True)
	value = eval(token)
	assert value == expected_value

def test_stacks_test(parser_test):
    def _compare(token1, token2):
        a = parser_test.expand_token(token1, try_if_else=True)
        b = parser_test.expand_token(token2, try_if_else=True)
        assert eval(a) == eval(b)
    _compare('NVME_IO_QUEUE0_BASE', 'NVME_IO_QUEUEN_BASE(0)')
    _compare('NVME_IO_QUEUE1_BASE', 'NVME_IO_QUEUEN_BASE(1)')
    _compare('NVME_IO_QUEUE2_BASE', 'NVME_IO_QUEUEN_BASE(2)')
    _compare('NVME_IO_QUEUE3_BASE', 'NVME_IO_QUEUEN_BASE(3)')
    _compare('NVME_IO_QUEUE4_BASE', 'NVME_IO_QUEUEN_BASE(4)')
    _compare('NVME_IO_QUEUE5_BASE', 'NVME_IO_QUEUEN_BASE(5)')
    _compare('NVME_IO_QUEUE6_BASE', 'NVME_IO_QUEUEN_BASE(6)')
    _compare('NVME_IO_QUEUE7_BASE', 'NVME_IO_QUEUEN_BASE(7)')

@pytest.mark.parametrize("define, expected_value", [
	('ENV', 3),
	('BUFFER_ALIGN_SHIFT', 2),
	('MULTI_LINE_DEF', 3),
	('BUFFER_0_BASE', 0x4000000),
])
def test_define_test(parser_test, define, expected_value):
	define = parser_test.get_expand_define(define)
	value = parser_test.try_eval_num(define.token)
	assert value == expected_value

def test_existence_test(parser_test):
	define = parser_test.get_expand_define('BUFFER_1_BASE', try_if_else=True)
	assert define == None

