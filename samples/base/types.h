#ifndef __TYPES_H__
#define __TYPES_H__

#include "conf.h"

#include <string.h>     // memset(), memcpy(), NULL

#if (ENV == ENV_DEVELOP)

#ifndef WIN32
#error "#ifndef WIN32"
#endif

typedef unsigned long long  U64;
typedef signed long long    S64;


#else /* #if (ENV == ENV_DEVELOP) */

#ifdef TRUE
#error "#ifdef TRUE"
#endif

#ifdef FALSE
#error "#ifdef FALSE"
#endif

#define TRUE            (1)
#define FALSE           (0)

typedef unsigned char       BOOL;   //Boolean:          TRUE/FALSE

#endif /* #if (ENV == ENV_DEVELOP) */

typedef unsigned char       U8;
typedef unsigned short      U16;
typedef unsigned long       U32;
typedef signed char         S8;
typedef signed short        S16;
typedef signed long         S32;


#define MAX_U64_VAL         (0xFFFFFFFFFFFFFFFFLL)
#define MAX_U32_VAL         (0xFFFFFFFF)
#define MAX_U16_VAL         (0xFFFF)
#define MAX_U8_VAL          (0xFF)

#define SECTOR_SIZE         (512)
#define SECTOR_SIZE_SHIFT   (9)
#define SECTOR_SIZE_MASK    (SECTOR_SIZE - 1)

#define _V          volatile

/*
 * BIT
 *
 */
#define BIT(n)     (1uL << (n))

#define BIT0    BIT(0)
#define BIT1    BIT(1)
#define BIT2    BIT(2)
#define BIT3    BIT(3)
#define BIT4    BIT(4)
#define BIT5    BIT(5)
#define BIT6    BIT(6)
#define BIT7    BIT(7)
#define BIT8    BIT(8)
#define BIT9    BIT(9)
#define BIT10   BIT(10)
#define BIT11   BIT(11)
#define BIT12   BIT(12)
#define BIT13   BIT(13)
#define BIT14   BIT(14)
#define BIT15   BIT(15)
#define BIT16   BIT(16)
#define BIT17   BIT(17)
#define BIT18   BIT(18)
#define BIT19   BIT(19)
#define BIT20   BIT(20)
#define BIT21   BIT(21)
#define BIT22   BIT(22)
#define BIT23   BIT(23)
#define BIT24   BIT(24)
#define BIT25   BIT(25)
#define BIT26   BIT(26)
#define BIT27   BIT(27)
#define BIT28   BIT(28)
#define BIT29   BIT(29)
#define BIT30   BIT(30)
#define BIT31   BIT(31)

#define BIT_MASK(n)          (((U32)BIT(n)) - 1)


#define MOD_2N(x, y)            ((x) & ((y) - 1))
#define ALIGN_2N(x, y)          ((x) + ((MOD_2N((x), (y)) > 0) * (y)) - MOD_2N((x), (y)))


#define CALC_8B_ADD(augend_l, augend_h, addend_l, addend_h, sum_l, sum_h)      \
        {                                                                      \
            sum_l = augend_l + addend_l;                                       \
            sum_h = augend_h + addend_h + ((augend_l > sum_l) ? 1 : 0);        \
        }

#define CALC_8B_LEFT_SHIFT(val_l, val_h, shift_num, rst_l, rst_h)               \
        {                                                                       \
            rst_l = val_l << shift_num;                                         \
            rst_h = (val_h << shift_num) | (val_l >> (32 - shift_num));         \
        }

#define CALC_8B_RIGHT_SHIFT(val_l, val_h, shift_num, rst_l, rst_h)               \
        {                                                                        \
            rst_h = val_h >> shift_num;                                          \
            rst_l = (val_l >> shift_num) | (val_h << (32 - shift_num));          \
        }

#endif /* #ifndef __TYPES_H__ */

