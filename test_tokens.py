import unittest
import pathlib
from C_DefineParser import DEFINE, Parser

class TestAllTokens(unittest.TestCase):

	@classmethod
	def setUpClass(cls):
		cls.parser = Parser()
		inc_path = './samples'
		for inc_file in pathlib.Path(inc_path).glob('**/*.h'):
			cls.parser.read_h(inc_file)
		return cls
	
	def setUp(self):
		self.parser.debug = False
		self.parser.iterate = 0

	def _assert_define(self, name, expected_val):
		define = self.parser.get_expand_define(name)
		value = eval(define.token)
		self.assertEqual(value, expected_val)
	
	def _assert_token(self, token, expected_val):
		token = self.parser.expand_token(token)
		value = eval(token)
		self.assertEqual(value, expected_val)
	
	def test_simple_token(self):
		self._assert_token('NVME_CMD_SIZE', 64)
		self._assert_token('0x00C0000', 0x0C0000)
		self._assert_token('ALIGN_2N(0x00C0000, 0xC00)', 0x0C0000)

	def test_simple_define(self):
		self._assert_define('BUFFER_ALIGN_SHIFT', 2)

	def test_multiline_token(self):
		self._assert_token('MULTI_LINE_DEF', 3)

	def test_multiline_define(self):
		self._assert_define('MULTI_LINE_DEF', 3)
    
	def test_complex_token(self):
		self._assert_token('(ALIGN_2N(BUFFER_BASE, BUFFER_ALIGN_SHIFT))', 0x4000000)
		self._assert_token('NVME_IO_QUEUEN_BASE(8)', 0x2D10000)

	def test_complex_define(self):
		self._assert_define('BUFFER_0_BASE', 0x4000000)
		self._assert_define('NVME_IO_QUEUE0_BASE', 0xD10000)

class TestENV_PUBLIC_Tokens(unittest.TestCase):

	@classmethod
	def setUpClass(cls):
		cls.parser = Parser()
		inc_path = './samples'
		cls.parser.insert_define('ENV', token='ENV_PUBLIC')
		cls.parser.read_folder_h(inc_path)
		return cls
	
	def setUp(self):
		self.parser.debug = False
		self.parser.iterate = 0

	def _assert_define(self, name, expected_val):
		define = self.parser.get_expand_define(name, try_if_else=True)
		value = eval(define.token)
		self.assertEqual(value, expected_val)
	
	def _assert_token(self, token, expected_val):
		token = self.parser.expand_token(token, try_if_else=True)
		value = eval(token)
		self.assertEqual(value, expected_val)
	
	def test_simple_token(self):
		self._assert_token('NVME_CMD_SIZE', 64)

	def test_simple_define(self):
		self._assert_define('BUFFER_ALIGN_SHIFT', 2)

	def test_multiline_token(self):
		self._assert_token('MULTI_LINE_DEF', 3)

	def test_multiline_define(self):
		self._assert_define('MULTI_LINE_DEF', 3)
    
	def test_complex_token(self):
		self._assert_token('(ALIGN_2N(BUFFER_BASE, BUFFER_ALIGN_SHIFT))', 0x4000000)
		self._assert_token('NVME_IO_QUEUEN_BASE(8)', 0x2D10000)

	def test_complex_define(self):
		self._assert_define('BUFFER_0_BASE', 0x4000000)
		self._assert_define('NVME_IO_QUEUE0_BASE', 0xD10000)
	
	def test_existence_define(self):
		define = self.parser.get_expand_define('BUFFER_1_BASE', try_if_else=True)
		self.assertIsNone(define)

class TestENV_PUBLIC_Tokens(unittest.TestCase):

	@classmethod
	def setUpClass(cls):
		cls.parser = Parser()
		inc_path = './samples'
		cls.parser.insert_define('ENV', token='ENV_TEST')
		cls.parser.read_folder_h(inc_path)
		return cls
	
	def setUp(self):
		self.parser.debug = False
		self.parser.iterate = 0

	def _assert_define(self, name, expected_val):
		define = self.parser.get_expand_define(name, try_if_else=True)
		value = eval(define.token)
		self.assertEqual(value, expected_val)
	
	def _assert_token(self, token, expected_val):
		token = self.parser.expand_token(token, try_if_else=True)
		value = eval(token)
		self.assertEqual(value, expected_val)
	
	def test_simple_token(self):
		self._assert_token('NVME_CMD_SIZE', 64)

	def test_simple_define(self):
		self._assert_define('BUFFER_ALIGN_SHIFT', 2)

	def test_multiline_token(self):
		self._assert_token('MULTI_LINE_DEF', 3)

	def test_multiline_define(self):
		self._assert_define('MULTI_LINE_DEF', 3)
    
	def test_complex_token(self):
		self._assert_token('(ALIGN_2N(BUFFER_BASE, BUFFER_ALIGN_SHIFT))', 0x4000000)
		self._assert_token('NVME_IO_QUEUEN_BASE(8)', 0x2B10000)

	def test_complex_define(self):
		self._assert_define('BUFFER_0_BASE', 0x4000000)
		self._assert_define('NVME_IO_QUEUE0_BASE', 0xB10000)
	
	def test_existence_define(self):
		define = self.parser.get_expand_define('BUFFER_1_BASE', try_if_else=True)
		self.assertIsNone(define)

if __name__ == '__main__':
    unittest.main()
