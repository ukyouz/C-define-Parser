# C-define Parser

This is not a C preprocessor, but only a simple define parser for C header files.

When lots of defined constants stack to each other, it begins hard to tell the actual value of the each constant, that may be important if you want to debug. However, such information usually disppaears due to C preprocessor, it indeed knows all constant values and replace them all into the real executable sections, as the result you lose the list of those important constants.

If you have used text editor with intellisense feature, they may possible expand the macro for user, for example when hovering over the macro, but they “expand” only. That means, you may get a very long line with a lot of brackets, if luckily, you can copy-paste the long line into other place and get the actual value of it. Imaging their are hundreds of constants in a big project…, you get the idea.

C-define Parser parses those defined constants for you, expanding macro as much as possible to get the final “single value” for every constant.

For example, the input header file:

```c
#define BASE_Y     (BASE_X + X_SIZE)
```

You can get a result like:

```c
#define BASE_Y     (0x40C0)
```

Because C-define Parser can find the defines of `BASE_X` and `X_SIZE` and the defines they used, and on, and on, and on, and finally export a number for you, then you can control the output format as you like.

# Installation

`pip install git+https://github.com/ukyouz/C-define-Parser`

# Usage

To parse all header files in your source folder:

```python
import C_DefineParser

p = C_DefineParser.Parser()
p.read_folder_h("./samples")
```

Then you can get parsed definitions in a header file.

```python
defines = p.get_expand_defines("./samples/address_map.h")
# [C_DefineParser.Define(...), ...]

# try to eval the expaned token as a single value
val = p.try_eval_num(defines[0].token)
```

Or just get an expanded macro token:

```python
define = p.get_expand_defines("BIT(31)")
# C_DefineParser.Define(...)
```