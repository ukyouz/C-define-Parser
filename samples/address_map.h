#ifndef __ADDRESS_MAP_H__
#define __ADDRESS_MAP_H__

#include "base/conf.h"
#include "base/types.h"

#if 0
#define IF_0_BLOCK      (0)
#else
#define IF_0_ELSE_BLOCK (1)
#endif

#define MULTI_LINE_DEF       \
                        (1L) \
                        +    \
                        (2LLU)

/*
 * Sample NVME Model
 */

#if 0||1
#define SHOULD_BE_1      (1)
#endif

#if(ENV == ENV_DEVELOP)
#define NVME_CORE_BASE              (0x00100000)
#elif(ENV == ENV_TEST)
#define NVME_CORE_BASE              (0x00A00000)
#else
#define NVME_CORE_BASE              (0x00C00000)
#endif
#define NVME_REGS_BASE              (NVME_CORE_BASE + 0x400)


#define NVME_CMD_SIZE               (64)

#define NVME_ADM_QUEUE_SIZE         (NVME_CMD_SIZE)
#define NVME_ADM_QUEUE_DEPTH        (16384 /* should be equal to hardware limitation */)
#define NVME_ADM_QUEUE_BASE         (NVME_CORE_BASE + 0x10000)

#define NVME_IO_QUEUE_SIZE          (NVME_CMD_SIZE)
#define NVME_IO_QUEUE_DEPTH         (65536 /* should be equal to hardware limitation */)
#define NVME_IO_QUEUE0_BASE         (NVME_ADM_QUEUE_BASE + NVME_ADM_QUEUE_SIZE * NVME_ADM_QUEUE_DEPTH)
#define NVME_IO_QUEUE1_BASE         (NVME_IO_QUEUE0_BASE + NVME_IO_QUEUE_SIZE * NVME_IO_QUEUE_DEPTH)
#define NVME_IO_QUEUE2_BASE         (NVME_IO_QUEUE1_BASE + NVME_IO_QUEUE_SIZE * NVME_IO_QUEUE_DEPTH)
#define NVME_IO_QUEUE3_BASE         (NVME_IO_QUEUE2_BASE + NVME_IO_QUEUE_SIZE * NVME_IO_QUEUE_DEPTH)
#define NVME_IO_QUEUE4_BASE         (NVME_IO_QUEUE3_BASE + NVME_IO_QUEUE_SIZE * NVME_IO_QUEUE_DEPTH)
#define NVME_IO_QUEUE5_BASE         (NVME_IO_QUEUE4_BASE + NVME_IO_QUEUE_SIZE * NVME_IO_QUEUE_DEPTH)
#define NVME_IO_QUEUE6_BASE         (NVME_IO_QUEUE5_BASE + NVME_IO_QUEUE_SIZE * NVME_IO_QUEUE_DEPTH)
#define NVME_IO_QUEUE7_BASE         (NVME_IO_QUEUE6_BASE + NVME_IO_QUEUE_SIZE * NVME_IO_QUEUE_DEPTH)
#define NVME_IO_QUEUE8_BASE         (NVME_IO_QUEUE7_BASE + NVME_IO_QUEUE_SIZE * NVME_IO_QUEUE_DEPTH)
#define NVME_IO_QUEUEN_BASE(n)      (NVME_IO_QUEUE0_BASE + (n) * NVME_IO_QUEUE_SIZE * NVME_IO_QUEUE_DEPTH)

#define NVME_END                    (ALIGN_2N(NVME_IO_QUEUE8_BASE + NVME_IO_QUEUE_SIZE * NVME_IO_QUEUE_DEPTH, 16))

/*
 * Other sample
 */

#define BUFFER_BASE                  (0x04000000)
#define BUFFER_ALIGN_SHIFT           (2)

#define BUFFER_0_BASE                (ALIGN_2N(BUFFER_BASE, BUFFER_ALIGN_SHIFT))
#define BUFFER_0_SIZE                (0xC00)

#if (ENV == ENV_DEVELOP)

#define BUFFER_1_BASE                (ALIGN_2N(BUFFER_0_BASE + BUFFER_0_SIZE, BUFFER_ALIGN_SHIFT))
#define BUFFER_1_SIZE                (0x1000)

#endif

#define FIFO_0_BASE                  (ALIGN_2N(BUFFER_1_BASE, 4))
#define FIFO_0_UNIT                  (32 /* For unit size (Byte) */)
#define FIFO_0_DEPTH                 (2)

#define FIFO_1_BASE                  (ALIGN_2N(FIFO_0_BASE + FIFO_0_UNIT * FIFO_0_DEPTH, 4))
#define FIFO_1_UNIT                  (16) // sample line comment
#define FIFO_1_DEPTH                 (4)

#if (ENV == ENV_TEST)

#define FIFO_2_BASE                  (ALIGN_2N(FIFO_1_BASE + FIFO_1_UNIT * FIFO_1_DEPTH, ALIGN_2N(BUFFER_ALIGN_SHIFT, 2)))
#define FIFO_2_UNIT                  (16)
#define FIFO_2_DEPTH                 (8)

#define BUFFER_END                   (FIFO_2_BASE + FIFO_2_UNIT * FIFO_2_DEPTH)

#else

#define BUFFER_END                   (FIFO_1_BASE + FIFO_1_UNIT * FIFO_1_DEPTH)

#endif

#endif
