
#include "app/scheduler.h"
#include "app/cli.h"
#include "app/depositor.h"
#include "app/motor_runner.h"

#include "dev/servo.h"

void setup() 
{
    servo_init(SERVO_DEPOSITOR, DEPOSITOR_ANGLE_CLOSED); // should be in application init not here

    // initialization of applications
    scheduler_init();
    cli_init();
    motor_runner_init();
}

void loop()
{
    // 500us tasks
    scheduler_run500us();

    // 1ms tasks
    motor_runner_run1ms();

    // 10ms tasks

    // 100ms tasks
    cli_run100ms();
}
