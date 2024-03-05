
/*******************************************************************************
*                                I N C L U D E S                               *
*******************************************************************************/ 

#include "isolation.h"
#include "system_state.h"
#include "scheduler.h"

/*******************************************************************************
*                               C O N S T A N T S                              *
*******************************************************************************/ 
#define BELT_ONE_HOME_ANGLE 0.0
#define BELT_ONE_RAMP_ANGLE 5.0 // Degrees
#define BELT_ONE_STARTING_RATE 250 // Steps per second

#define BELT_TWO_HOME_ANGLE 0.0
#define BELT_TWO_RAMP_ANGLE 5.0 // Degrees
#define BELT_TWO_STARTING_RATE 250 // Steps per second

#define BELT_ONE_CW 1
#define BELT_TWO_CW 1

/*******************************************************************************
*                      D A T A    D E C L A R A T I O N S                      *
*******************************************************************************/ 

typedef struct
{
    struct pt  thread;
    isolation_state_E state;
} isolation_data_S;

/*******************************************************************************
*          P R I V A T E    F U N C T I O N    D E C L A R A T I O N S         *
*******************************************************************************/

static char run10ms(struct pt* thread);
static isolation_state_E isolation_update_state(isolation_state_E curr_state);

/*******************************************************************************
*                 S T A T I C    D A T A    D E F I N I T I O N S              *
*******************************************************************************/ 

static isolation_data_S isolation_data = 
{
    .state = ISOLATION_STATE_IDLE,
};

/*******************************************************************************
*                      P R I V A T E    F U N C T I O N S                      *
*******************************************************************************/

static isolation_state_E isolation_update_state(isolation_state_E curr_state)
{
    isolation_state_E next_state = curr_state;
    system_state_E system_state = system_state_getState();

    switch (curr_state)
    {
        case ISOLATION_STATE_IDLE:
            break;
        case ISOLATION_STATE_MOVING:
            break;
        case ISOLATION_STATE_ISOLATED:
            next_state = ISOLATION_STATE_IDLE;
            break;
    }

    return next_state;
}

static PT_THREAD(run10ms(struct pt* thread))
{
    PT_BEGIN(thread);
    PT_WAIT_UNTIL(thread, 
                  scheduler_taskReleased(PERIOD_10ms, (uint8_t) ISOLATION));
    isolation_data.state = isolation_update_state(isolation_data.state);
    PT_END(thread);
}

/*******************************************************************************
*                       P U B L I C    F U N C T I O N S                       *
*******************************************************************************/ 

void isolation_init(void)
{
    // start subsystem thread
    PT_INIT(&isolation_data.thread);

    stepper_init(STEPPER_BELT_ONE);
    stepper_init(STEPPER_BELT_TWO);
}

void isolation_run10ms(void)
{
    run10ms(&isolation_data.thread);
}

isolation_state_E isolation_getState(void)
{
    return isolation_data.state;
}
