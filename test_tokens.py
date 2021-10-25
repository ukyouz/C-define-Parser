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
	('NVME_CMD_SIZE', 64),
	('0x00C0000', 0x0C0000),
	('ALIGN_2N(0x00C0000, 0xC00)', 0x0C0000),
	('MULTI_LINE_DEF', 3),
	('MULTI_LINE_DEF', 3),
	('(ALIGN_2N(BUFFER_BASE, BUFFER_ALIGN_SHIFT))', 0x4000000),
	('NVME_IO_QUEUEN_BASE(8)', 0x2D10000)
])
def test_token(parser_default, token, expected_value):
	token = parser_default.expand_token(token)
	value = eval(token)
	assert value == expected_value

@pytest.mark.parametrize("define, expected_value", [
	('BUFFER_ALIGN_SHIFT', 2),
	('MULTI_LINE_DEF', 3),
	('BUFFER_0_BASE', 0x4000000),
	('NVME_IO_QUEUE0_BASE', 0xD10000),
])
def test_define(parser_default, define, expected_value):
	define = parser_default.get_expand_define(define)
	value = eval(define.token)
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
	('NVME_CMD_SIZE', 64),
	('BUFFER_ALIGN_SHIFT', 2),
	('MULTI_LINE_DEF', 3),
	('(ALIGN_2N(BUFFER_BASE, BUFFER_ALIGN_SHIFT))', 0x4000000),
	('NVME_IO_QUEUEN_BASE(8)', 0x2D10000)
])
def test_token(parser_public, token, expected_value):
	token = parser_public.expand_token(token)
	value = eval(token)
	assert value == expected_value

@pytest.mark.parametrize("define, expected_value", [
	('BUFFER_ALIGN_SHIFT', 2),
	('MULTI_LINE_DEF', 3),
	('BUFFER_0_BASE', 0x4000000),
	('NVME_IO_QUEUE0_BASE', 0xD10000),
])
def test_define(parser_public, define, expected_value):
	define = parser_public.get_expand_define(define)
	value = eval(define.token)
	assert value == expected_value

def test_existence(parser_public):
	define = parser_public.get_expand_define('BUFFER_1_BASE', try_if_else=True)
	assert define == None

################################################################################

@pytest.fixture
def parser_test():
	parser = Parser()
	inc_path = './samples'
	parser.insert_define('ENV', token='ENV_TEST')
	parser.read_folder_h(inc_path)
	return parser

@pytest.mark.parametrize("token, expected_value", [
	('NVME_CMD_SIZE', 64),
	('BUFFER_ALIGN_SHIFT', 2),
	('MULTI_LINE_DEF', 3),
	('(ALIGN_2N(BUFFER_BASE, BUFFER_ALIGN_SHIFT))', 0x4000000),
	('NVME_IO_QUEUE8_BASE', 0x2D10000),
	('NVME_IO_QUEUEN_BASE(8)', 0x2D10000)
])
def test_token(parser_test, token, expected_value):
	token = parser_test.expand_token(token)
	value = eval(token)
	assert value == expected_value

@pytest.mark.parametrize("define, expected_value", [
	('BUFFER_ALIGN_SHIFT', 2),
	('MULTI_LINE_DEF', 3),
	('BUFFER_0_BASE', 0x4000000),
	('NVME_IO_QUEUE0_BASE', 0xD10000),
	('NVME_IO_QUEUE0_BASE', 0xD10000),
])
def test_define(parser_test, define, expected_value):
	define = parser_test.get_expand_define(define)
	value = parser_test._try_eval_num(define.token)
	assert value == expected_value

def test_existence(parser_test):
	define = parser_test.get_expand_define('BUFFER_1_BASE', try_if_else=True)
	assert define == None

