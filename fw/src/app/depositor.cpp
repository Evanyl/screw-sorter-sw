
/*******************************************************************************
*                                I N C L U D E S                               *
*******************************************************************************/ 

#include "depositor.h"
#include "scheduler.h"

/*******************************************************************************
*                               C O N S T A N T S                              *
*******************************************************************************/ 

#define DEPOSITOR_ANGLE_OPEN   -90.0
#define DEPOSITOR_ANGLE_CLOSED  62.0

#define DEPOSITOR_STEPS_TO_CENTER 100
#define DEPOSITOR_STEPS_TO_SWEEP 150

#define DEPOSITOR_ARM_CW 1
#define DEPOSITOR_ARM_HOME_RATE 5

/*******************************************************************************
*                      D A T A    D E C L A R A T I O N S                      *
*******************************************************************************/ 

typedef struct
{
    depositor_state_E state;
} depositor_data_S;

/*******************************************************************************
*          P R I V A T E    F U N C T I O N    D E C L A R A T I O N S         *
*******************************************************************************/

static bool depositor_atHome(void);
static depositor_state_E depositor_update_state(depositor_state_E curr_state);

/*******************************************************************************
*                 S T A T I C    D A T A    D E F I N I T I O N S              *
*******************************************************************************/ 

static depositor_data_S depositor_data = 
{
    .state = DEPOSITOR_STATE_NAV_HOME
};

/*******************************************************************************
*                      P R I V A T E    F U N C T I O N S                      *
*******************************************************************************/

static bool depositor_atHome(void)
{
    return switch_state(SWITCH_DEPOSITOR);
}

static depositor_state_E depositor_update_state(depositor_state_E curr_state)
{
    depositor_state_E next_state = curr_state;

    switch (curr_state)
    {
        case DEPOSITOR_STATE_NAV_HOME:
            
            if (stepper_commandUntil(STEPPER_DEPOSITOR, 
                                     depositor_atHome, 
                                     DEPOSITOR_ARM_CW, 
                                     DEPOSITOR_ARM_HOME_RATE) == false)
            {
                // do nothing
            }
            else
            {
                next_state = DEPOSITOR_STATE_IDLE;
            }
            break;
        case DEPOSITOR_STATE_IDLE:
        case DEPOSITOR_STATE_DROP:
        case DEPOSITOR_STATE_NAV_END:
        case DEPOSITOR_STATE_COUNT:
            break;
    }

    return next_state;
}

/*******************************************************************************
*                       P U B L I C    F U N C T I O N S                       *
*******************************************************************************/ 

void depositor_init(void)
{
    servo_init(SERVO_DEPOSITOR, DEPOSITOR_ANGLE_CLOSED);
    switch_init(SWITCH_DEPOSITOR);
    stepper_init(STEPPER_DEPOSITOR);
}

void depositor_run10ms(void)
{
    depositor_data.state = depositor_update_state(depositor_data.state);
}

depositor_state_E depositor_getState(void)
{
    return DEPOSITOR_STATE_COUNT;
}
