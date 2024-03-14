
/*******************************************************************************
*                                I N C L U D E S                               *
*******************************************************************************/ 

#include "arm.h"
#include "classify_system_state.h"
#include "scheduler.h"

/*******************************************************************************
*                               C O N S T A N T S                              *
*******************************************************************************/ 

#define ARM_SIDEON_ANGLE 74.0
#define ARM_TOPDOWN_ANGLE 0.0
#define ARM_RAMP_ANGLE 5.0

#define ARM_NAV_RATE 750
#define ARM_HOMING_RATE 100
#define ARM_STARTING_RATE 250

#define ARM_CW 1

/*******************************************************************************
*                      D A T A    D E C L A R A T I O N S                      *
*******************************************************************************/ 

typedef struct
{
    // some tracking of height after homing
    struct pt thread;
    arm_state_E state;
} arm_data_S;

/*******************************************************************************
*          P R I V A T E    F U N C T I O N    D E C L A R A T I O N S         *
*******************************************************************************/

static bool arm_atHome(void);
static arm_state_E arm_update_state(arm_state_E curr_state);

/*******************************************************************************
*                 S T A T I C    D A T A    D E F I N I T I O N S              *
*******************************************************************************/ 

static arm_data_S arm_data = 
{
    .state = ARM_STATE_HOMING
};

/*******************************************************************************
*                      P R I V A T E    F U N C T I O N S                      *
*******************************************************************************/

static bool arm_atHome(void)
{
    return switch_state(SWITCH_ARM);
}

static arm_state_E arm_update_state(arm_state_E curr_state)
{
    arm_state_E next_state = curr_state;
    classify_system_state_E classify_system_state = classify_system_state_getState();

    switch (curr_state)
    {
        case ARM_STATE_HOMING:
            if (stepper_commandUntil(STEPPER_ARM, 
                                     arm_atHome, 
                                     ARM_CW, 
                                     ARM_HOMING_RATE) == false)
            {
                // do nothing, homing
            }
            else
            {
                stepper_calibAngle(STEPPER_ARM, ARM_TOPDOWN_ANGLE);
                next_state = ARM_STATE_IDLE;
            }
            break;
        case ARM_STATE_IDLE:
            if (classify_system_state == CLASSIFY_SYSTEM_STATE_ENTERING_SIDEON)
            {
                next_state = ARM_STATE_ENTERING_SIDEON;
            }
            else
            {
                // do nothing, stay in top-down
            }
            break;
        case ARM_STATE_ENTERING_SIDEON:
            if (stepper_commandAngle(STEPPER_ARM,
                                     ARM_SIDEON_ANGLE,
                                     ARM_RAMP_ANGLE,
                                     ARM_NAV_RATE,
                                     ARM_STARTING_RATE) == false)
            {
                // do nothing, navigating to side-on position
            }   
            else
            {
                next_state = ARM_STATE_SIDEON;
            }
            break;
        case ARM_STATE_SIDEON:
            if (classify_system_state == CLASSIFY_SYSTEM_STATE_ENTERING_IDLE)
            {
                next_state = ARM_STATE_ENTERING_IDLE;
            }
            else
            {
                // do nothing, doig side-on imaging
            }
            break;
        case ARM_STATE_ENTERING_IDLE:
            if (stepper_commandAngle(STEPPER_ARM,
                                     ARM_TOPDOWN_ANGLE,
                                     ARM_RAMP_ANGLE,
                                     ARM_NAV_RATE,
                                     ARM_STARTING_RATE) == false)
            {
                // do nothinng
            }
            else
            {
                next_state = ARM_STATE_IDLE;
            }
            break;
        case ARM_STATE_COUNT:
            break;
    }

    return next_state;
}

static PT_THREAD(run10ms(struct pt* thread))
{
    PT_BEGIN(thread);
    PT_WAIT_UNTIL(thread, 
                  scheduler_taskReleased(PERIOD_10ms, (uint8_t) ARM));
    arm_data.state = arm_update_state(arm_data.state);
    PT_END(thread);
}


/*******************************************************************************
*                       P U B L I C    F U N C T I O N S                       *
*******************************************************************************/ 

void arm_init(void)
{
    PT_INIT(&arm_data.thread);

    stepper_init(STEPPER_ARM);
    switch_init(SWITCH_ARM);
}

void arm_run10ms(void)
{
    run10ms(&arm_data.thread);
}

arm_state_E arm_getState(void)
{
    return arm_data.state;
}

void arm_cli_home(uint8_t argNumber, char* args[])
{
    stepper_commandUntil(STEPPER_ARM, 
                         arm_atHome, 
                         ARM_CW, 
                         ARM_HOMING_RATE);
}
