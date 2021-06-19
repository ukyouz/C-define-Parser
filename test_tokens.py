import unittest
import pathlib
from C_DefineParser import Parser

class TestTokens(unittest.TestCase):

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

	def test_simple_token(self):
		token = self.parser.expand_token('NVME_CMD_SIZE')
		self.assertEqual(token, '(64)')

	def test_simple_define(self):
		define = self.parser.get_expand_define('BUFFER_ALIGN_SHIFT')
		self.assertEqual(define.token, '(2)')

	def test_multiline_token(self):
		token = self.parser.expand_token('MULTI_LINE_DEF')
		value = eval(token)
		self.assertEqual(value, 3)

	def test_multiline_define(self):
		define = self.parser.get_expand_define('MULTI_LINE_DEF')
		value = eval(define.token)
		self.assertEqual(value, 3)
    
	def test_complex_token(self):
		token = self.parser.expand_token('(ALIGN_2N(BUFFER_BASE, BUFFER_ALIGN_SHIFT))')
		value = eval(token)
		self.assertEqual(value, 0x4000000)

		token = self.parser.expand_token('NVME_IO_QUEUEN_BASE(8)')
		value = eval(token)
		self.assertEqual(value, 0x3010000)

	def test_complex_define(self):
		define = self.parser.get_expand_define('BUFFER_0_BASE')
		value = eval(define.token)
		self.assertEqual(value, 0x4000000)

		define = self.parser.get_expand_define('NVME_IO_QUEUE0_BASE')
		value = eval(define.token)
		self.assertEqual(value, 0x1010000)

if __name__ == '__main__':
    unittest.main()
