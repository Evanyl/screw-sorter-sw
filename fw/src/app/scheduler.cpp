
/*******************************************************************************
*                                I N C L U D E S                               *
*******************************************************************************/ 

#include "scheduler.h"

/*******************************************************************************
*                               C O N S T A N T S                              *
*******************************************************************************/ 

#define BASE_PERIOD_MICROSEC (100)
#define COUNT_500us          (500    / BASE_PERIOD_MICROSEC)
#define COUNT_1ms            (1000   / BASE_PERIOD_MICROSEC)
#define COUNT_10ms           (10000  / BASE_PERIOD_MICROSEC)
#define COUNT_100ms          (100000 / BASE_PERIOD_MICROSEC)

/*******************************************************************************
*          P R I V A T E    F U N C T I O N    D E C L A R A T I O N S         *
*******************************************************************************/

static void scheduler_ISR(void);
static char run500us(struct pt* thread);

/*******************************************************************************
*                      D A T A    D E C L A R A T I O N S                      *
*******************************************************************************/ 

typedef struct
{
    HardwareTimer* timer;
    // private volatile data, only expose to scheduler task
    volatile uint16_t counter;
    volatile bool task_500us_flag;
    volatile bool task_1ms_flag;
    volatile bool task_10ms_flag;
    volatile bool task_100ms_flag;
    // public data
    struct pt thread;
    bool mutexes_1ms[TASK_1ms_COUNT];
    bool mutexes_10ms[TASK_10ms_COUNT];
    bool mutexes_100ms[TASK_100ms_COUNT];
} scheduler_data_s;

/*******************************************************************************
*                 S T A T I C    D A T A    D E F I N I T I O N S              *
*******************************************************************************/

static scheduler_data_s scheduler_data;

/*******************************************************************************
*                      P R I V A T E    F U N C T I O N S                      *
*******************************************************************************/

static void scheduler_ISR(void)
{
    if (scheduler_data.counter < COUNT_100ms)
    {
        scheduler_data.counter++;
        if (scheduler_data.counter % COUNT_500us == 0)
        {
            scheduler_data.task_500us_flag = true;
        }
        if (scheduler_data.counter % COUNT_1ms == 0)
        {
            scheduler_data.task_1ms_flag = true;
        }
        if (scheduler_data.counter % COUNT_10ms == 0)
        {
            scheduler_data.task_10ms_flag = true;
        }
        if (scheduler_data.counter % COUNT_100ms == 0)
        {
            scheduler_data.task_100ms_flag = true;
        }
    }
    else
    {
        scheduler_data.counter = 0;
    }
}

static PT_THREAD(run500us(struct pt* thread))
{
    PT_BEGIN(thread);
    PT_WAIT_UNTIL(thread, scheduler_data.task_500us_flag);
    // scheduling code here
    if (scheduler_data.task_1ms_flag)
    {
        scheduler_data.task_1ms_flag = false;
        (void) memset(&scheduler_data.mutexes_1ms, 1, 
                      sizeof(scheduler_data.mutexes_1ms));
    }
    else if (scheduler_data.task_10ms_flag)
    {
        scheduler_data.task_10ms_flag = false;
        (void) memset(&scheduler_data.mutexes_10ms, 1, 
                      sizeof(scheduler_data.mutexes_10ms));
    }
    else if (scheduler_data.task_100ms_flag)
    {
        scheduler_data.task_100ms_flag = false;
        (void) memset(&scheduler_data.mutexes_100ms, 1, 
                      sizeof(scheduler_data.mutexes_100ms));
    }
    else
    {
        // do nothing
    }
    scheduler_data.task_500us_flag = false;
    PT_END(thread);
}

/*******************************************************************************
*                       P U B L I C    F U N C T I O N S                       *
*******************************************************************************/

void scheduler_init(void)
{
    (void) memset(&scheduler_data, 0, sizeof(scheduler_data_s));
    scheduler_data.timer = new HardwareTimer(TIM4);
    
    scheduler_data.timer->setOverflow(BASE_PERIOD_MICROSEC, MICROSEC_FORMAT);
    scheduler_data.timer->refresh();
    scheduler_data.timer->attachInterrupt(scheduler_ISR);
    scheduler_data.timer->resume();
    PT_INIT(&scheduler_data.thread);
}

void scheduler_run500us(void)
{
    run500us(&scheduler_data.thread);
}

bool scheduler_taskReleased(task_period_E period, uint8_t task_id)
{
    bool ret = false;
    if (period == PERIOD_1ms)
    {
        ret = scheduler_data.mutexes_1ms[task_id];
        scheduler_data.mutexes_1ms[task_id] = false;
    }
    else if (period == PERIOD_10ms)
    {
        ret = scheduler_data.mutexes_10ms[task_id];
        scheduler_data.mutexes_10ms[task_id] = false;
    }
    else if (period == PERIOD_100ms)
    {
        ret = scheduler_data.mutexes_100ms[task_id];
        scheduler_data.mutexes_100ms[task_id] = false;
    }
    else
    {
        // invalid period, do nothing
    }
    return ret;
}