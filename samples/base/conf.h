#ifndef __CONF_H__
#define __CONF_H__

#define ENV_DEVELOP                 (0)
#define ENV_PUBLIC                  (1)
#define ENV_SIMULATE                (2)
#define ENV_TEST                    (3)

#ifndef ENV
#define ENV                          (ENV_DEVELOP)
#endif

#endif
