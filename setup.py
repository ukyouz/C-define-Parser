from setuptools import setup

setup(
    name='C_DefineParser',
    version='0.1.0',
    description='A example Python package',
    url='https://github.com/ukyouz/C-define-Parser',
    author='Johnny Cheng',
    author_email='zhung1206@gmail.com',
    license='MIT',
    py_modules=['test'],
    packages=['C_DefineParser', 'C_DefineParser.utils'],
    package_dir={"": "src"},
    install_requires=[],
)
