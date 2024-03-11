
#include "app/scheduler.h"
#include "app/system_state.h"
#include "app/cli.h"
#include "app/core_comms.h"
#include "app/depositor.h"
#include "app/lighting.h"
#include "app/arm.h"
#include "app/plane.h"
#include "app/belts.h"
#include "app/motor_runner.h"

void setup() 
{
    // initialization of applications
    scheduler_init();
    system_state_init();
    depositor_init();
    lighting_init();
    arm_init();
    plane_init();
    belts_init();
    cli_init();
    core_comms_init();
    motor_runner_init(); // motors must be initialized first
}

void loop()
{
    // 100us tasks
    scheduler_run100us();

    // 500us tasks
    motor_runner_run500us();

    // 1ms tasks

    // 10ms tasks
    depositor_run10ms();
    lighting_run10ms();
    arm_run10ms();
    plane_run10ms();
    belts_run10ms();
    core_comms_run10ms();

    // 100ms tasks
    system_state_run100ms();
    cli_run100ms();
}
