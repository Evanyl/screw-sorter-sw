
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

// keep these as angle to center, and angle to sweep, get angles from CAD
#define DEPOSITOR_STEPS_TO_CENTER 100
#define DEPOSITOR_STEPS_TO_SWEEP 150

#define DEPOSITOR_ARM_CW 1
#define DEPOSITOR_ARM_CCW 0
#define DEPOSITOR_ARM_HOME_RATE 60 // Steps per second

/*******************************************************************************
*                      D A T A    D E C L A R A T I O N S                      *
*******************************************************************************/ 

typedef struct
{
    // some tracking of angle... concern of depositor not stepper 
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
    .state = DEPOSITOR_STATE_HOME
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
        case DEPOSITOR_STATE_ENTERING_HOME:
            if (stepper_commandUntil(STEPPER_DEPOSITOR,
                                     depositor_atHome,
                                     DEPOSITOR_ARM_CW,
                                     DEPOSITOR_ARM_HOME_RATE) == false)
            {
                // do nothing
            }
            else
            {
                next_state = DEPOSITOR_STATE_HOME;
            }
            break;
        case DEPOSITOR_STATE_HOME:
            break;
            // at the home position
        case DEPOSITOR_STATE_ENTERING_CENTER:
        {
            // go to center by taking a known number of steps
            uint16_t steps = 10;
            uint16_t ramp_steps = 10;
            // TODO: Implement absolute step relative to 0, so that you can return to center
            // from any position, not just home.
            if (stepper_command(STEPPER_DEPOSITOR, 
                                     steps, 
                                     DEPOSITOR_ARM_CCW, 
                                     DEPOSITOR_ARM_HOME_RATE,
                                     ramp_steps,
                                     (int) DEPOSITOR_ARM_HOME_RATE / 2) == false)
            {
                // do nothing
            }
            else
            {
                next_state = DEPOSITOR_STATE_CENTER;
            }
            break;
        }
        case DEPOSITOR_STATE_CENTER:
            // at the center position
        case DEPOSITOR_STATE_DROP:
            // execute the drop sequence with servo
        case DEPOSITOR_STATE_ENTERING_END:
            // sweep the previous part off the imaging plane
        case DEPOSITOR_STATE_END:
            // depositor arm is at the furthest possible position from post
        case DEPOSITOR_STATE_IDLE:
            // wait on serial message from RPi
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
    return depositor_data.state;
}

void depositor_cli_home(uint8_t argNumber, char* args[])
{
    // completes operation when state becomes DEPOSITOR_STATE_HOME
    depositor_data.state = DEPOSITOR_STATE_ENTERING_HOME;
}

void depositor_cli_center(uint8_t argNumber, char* args[])
{
    // completes operation when state becomes DEPOSITOR_STATE_CENTER
    depositor_data.state = DEPOSITOR_STATE_ENTERING_CENTER;
}
