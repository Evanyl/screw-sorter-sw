
#include "app/scheduler.h"
#include "app/cli.h"
#include "app/depositor.h"
#include "app/lighting.h"
#include "app/motor_runner.h"

#include "dev/servo.h"

void setup() 
{
    // initialization of applications
    scheduler_init();
    depositor_init();
    lighting_init();
    cli_init();
    motor_runner_init(); // motors must be initialized first
}

void loop()
{
    // 500us tasks
    scheduler_run500us();

    // 1ms tasks
    motor_runner_run1ms();

    // 10ms tasks
    // depositor_run10ms();
    // plane_run10ms();
    // arm_run10ms();

    // 100ms tasks
    cli_run100ms();
}
