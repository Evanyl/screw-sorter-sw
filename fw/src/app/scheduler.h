#ifndef APP_SCHEDULER
#define APP_SCHEDULER

/*******************************************************************************
*                                I N C L U D E S                               *
*******************************************************************************/ 

#include <pt.h>
#include <Arduino.h>

/*******************************************************************************
*                               C O N S T A N T S                              *
*******************************************************************************/ 

/*******************************************************************************
*                      D A T A    D E C L A R A T I O N S                      *
*******************************************************************************/

typedef enum
{
    PERIOD_500us,
    PERIOD_1ms,
    PERIOD_10ms,
    PERIOD_100ms,
} task_period_E;

typedef enum
{
    MOTOR_RUNNER,
    TASK_500us_COUNT
} task_500us;

typedef enum
{
    TASK_1ms_COUNT
} tasks_1ms_E;

typedef enum
{
#ifdef DEPOSIT
    BOXES,
#elif ISOLATE_CLASSIFY
    LIGHTING,
    DEPOSITOR,
    ARM,
    PLANE,
    BELTS,
#else
    // nothing
#endif
    CORE_COMMS, 
    TASK_10ms_COUNT
} tasks_10ms_E;

typedef enum
{
#ifdef DEPOSIT
    // nothing
#elif ISOLATE_CLASSIFY
    SYSTEM_STATE,
#else
    // nothing
#endif
    CLI,
    TASK_100ms_COUNT
} tasks_100ms_E;

/*******************************************************************************
*            P U B L I C    F U N C T I O N    D E C L A R A T I O N S         *
*******************************************************************************/ 

void scheduler_init(void);
void scheduler_run100us(void);
bool scheduler_taskReleased(task_period_E period, uint8_t task_id);

#endif // APP_SCHEDULER
