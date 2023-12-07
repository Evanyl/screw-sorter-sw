
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

/*******************************************************************************
*                       P U B L I C    F U N C T I O N S                       *
*******************************************************************************/ 

void depositor_init(void)
{
    servo_init(SERVO_DEPOSITOR, DEPOSITOR_ANGLE_CLOSED);
    stepper_init(STEPPER_DEPOSITOR);
}

void depositor_run10ms(void)
{

}

depositor_state_E depositor_getState(void)
{
    return DEPOSITOR_STATE_COUNT;
}
