#ifndef TUTILS_H
#define TUTILS_H

#define __MAX_TCOUNT 128
#ifndef LOCAL_TGROUP
    #error "Unity Tests: LOCAL_TGROUP is not defined before including tutils.h"
#endif

#define _TSETUP(group) TEST_SETUP(group)

#define _TTEAR_DOWN(group) TEST_TEAR_DOWN(group)

#define _TTEST(group, name) TEST(group, name)

#define _TRUN(group, name) RUN_TEST_CASE(group, name)
#define _TGROUP(group) TEST_GROUP_RUNNER(group)

#define SETUP() _TSETUP(LOCAL_TGROUP)
#define TEAR_DOWN() _TTEAR_DOWN(LOCAL_TGROUP)

#define T(name) _TTEST(LOCAL_TGROUP, name)
#define RUN(name) _TRUN(LOCAL_TGROUP, name)
#define GROUP_RUNNER() _TGROUP(LOCAL_TGROUP)

#endif // TUTILS_H
