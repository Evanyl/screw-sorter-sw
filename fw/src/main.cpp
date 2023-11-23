
#include "app/scheduler.h"
#include "app/cli.h"

void setup() 
{
    scheduler_init();
    serial_init();
}

void loop()
{
    // 500us tasks
    scheduler_run500us();

    // 1ms tasks

    // 10ms tasks

    // 100ms tasks
    serial_run100ms();
}
