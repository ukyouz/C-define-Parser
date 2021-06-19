#ifndef __CONF_H__
#define __CONF_H__

#define ENV_DEVELOP                 (0)
#define ENV_PUBLIC                  (1)
#define ENV_SIMULATE                (2)
#define ENV_TEST                    (3)

#ifdef WIN32
#define ENV                          (ENV_DEVELOP)
#else
#define ENV                          (ENV_PUBLIC) // ENV_TEST
#endif

#endif
