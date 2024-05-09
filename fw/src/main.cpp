
#include "app/scheduler.h"
#include "app/cli.h"
#include "app/core_comms.h"
#include "app/motor_runner.h"

#ifdef DEPOSIT
#include "app/boxes.h"
#elif ISOLATE_CLASSIFY
#include "app/system_state.h"
#include "app/depositor.h"
#include "app/lighting.h"
#include "app/arm.h"
#include "app/plane.h"
#include "app/belts.h"
#else
// nothing
#endif

void setup() 
{
    // initialization of applications
    scheduler_init();
    cli_init();
    core_comms_init();
    motor_runner_init(); // motors must be initialized prior
#ifdef DEPOSIT
    boxes_init();
#elif ISOLATE_CLASSIFY
    system_state_init();
    depositor_init();
    lighting_init();
    arm_init();
    plane_init();
    belts_init();
#else
    // nothing
#endif
}

void loop()
{
    // 100us tasks
    scheduler_run100us();

    // 500us tasks
    motor_runner_run500us();

    // 1ms tasks

    // 10ms tasks
#ifdef DEPOSIT
    // boxes_run10ms();
#elif ISOLATE_CLASSIFY 
    depositor_run10ms();
    lighting_run10ms();
    arm_run10ms();
    plane_run10ms();
    belts_run10ms();
#else
    // nothing
#endif
    core_comms_run10ms();

    // 100ms tasks
#ifdef DEPOSIT
    // nothing
#elif ISOLATE_CLASSIFY
    system_state_run100ms();
#else
    // nothing
#endif
    cli_run100ms();
}
