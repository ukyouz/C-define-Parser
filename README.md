# C-define Parser

This is not a C preprocessor, but only a simple define parser for C header files.

When lots of defined constants stack to each other, it begins hard to tell the actual value of the each constant, that may be important if you want to debug. However, such information usually disppaears due to C proprocessor, it indeed knows all constant values and replace them all into the real executable sections, as the result you lose the list of those important constants.

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
