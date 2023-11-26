
#include "app/scheduler.h"
#include "app/cli.h"
#include "dev/motor_runner.h"
#include "dev/servo.h"

void setup() 
{
    // initialization of applications
    scheduler_init();
    cli_init();

    servo_init(SERVO_DEPOSITOR, 0); // should be in depositor init not here...

    // begin motor control
    motor_runner_init();
}

void loop()
{
    // 500us tasks
    scheduler_run500us();

    // 1ms tasks

    // 10ms tasks

    // 100ms tasks
    cli_run100ms();
}
