
/*******************************************************************************
*                                I N C L U D E S                               *
*******************************************************************************/ 

#include "depositor.h"
#include "lighting.h"
#include "system_state.h"
#include "scheduler.h"

/*******************************************************************************
*                               C O N S T A N T S                              *
*******************************************************************************/ 

#define DEPOSITOR_OPEN_STEPS   255
#define DEPOSITOR_OPEN_RATE    10
#define DEPOSITOR_OPEN_ANGLE   0.0 //-90.0

#define DEPOSITOR_CLOSE_STEPS  255
#define DEPOSITOR_CLOSE_RATE   255
#define DEPOSITOR_CLOSE_ANGLE  62.0

// change these to angle to center, and angle to sweep. Get angles from CAD.
#define DEPOSITOR_STEPS_TO_CENTER 2000
#define DEPOSITOR_STEPS_TO_SWEEP 3200

#define DEPOSITOR_ARM_CW 1
#define DEPOSITOR_ARM_CCW 0
#define DEPOSITOR_ARM_NAV_RATE 500
#define DEPOSITOR_ARM_HOME_RATE 150 // Steps per second

/*******************************************************************************
*                      D A T A    D E C L A R A T I O N S                      *
*******************************************************************************/ 

typedef struct
{
    // some tracking of angle... concern of depositor not stepper?
    struct pt  thread;
    depositor_state_E state;
    uint16_t curr_angle;
    uint16_t des_angle;
} depositor_data_S;

/*******************************************************************************
*          P R I V A T E    F U N C T I O N    D E C L A R A T I O N S         *
*******************************************************************************/

static char run10ms(struct pt* thread);
static bool depositor_atHome(void);
static depositor_state_E depositor_update_state(depositor_state_E curr_state);

/*******************************************************************************
*                 S T A T I C    D A T A    D E F I N I T I O N S              *
*******************************************************************************/ 

static depositor_data_S depositor_data = 
{
    .state = DEPOSITOR_STATE_HOMING,
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
    system_state_E system_state = system_state_getState();

    switch (curr_state)
    {
        case DEPOSITOR_STATE_HOMING:
            if (lighting_getState() == LIGHTING_STATE_IDLE)
            {
                if (stepper_commandUntil(STEPPER_DEPOSITOR, 
                                         depositor_atHome, 
                                         DEPOSITOR_ARM_CW, 
                                         DEPOSITOR_ARM_HOME_RATE) == false)
                {
                    // do nothing, homing
                }
                else
                {
                    next_state = DEPOSITOR_STATE_IDLE;
                }
            }
            else
            {
                // do nothing, wait for lighting to home.
            }
            break;

        case DEPOSITOR_STATE_IDLE:
            if (system_state == SYSTEM_STATE_ENTERING_DEPOSITED)
            {
                next_state = DEPOSITOR_STATE_SWEEPING;
            }
            else
            {
                // do nothing, stay in idle position
            }
            break;
            
        case DEPOSITOR_STATE_SWEEPING:
            if (stepper_command(STEPPER_DEPOSITOR,
                                DEPOSITOR_STEPS_TO_SWEEP,
                                DEPOSITOR_ARM_CCW,
                                DEPOSITOR_ARM_NAV_RATE,
                                200,
                                25) == false)
            {
                // do nothing, navigating to sweep position
            }
            else
            {
                next_state = DEPOSITOR_STATE_CENTERING;
            }
            break;
        case DEPOSITOR_STATE_CENTERING:
            if (stepper_command(STEPPER_DEPOSITOR,
                                DEPOSITOR_STEPS_TO_SWEEP - 
                                    DEPOSITOR_STEPS_TO_CENTER,
                                DEPOSITOR_ARM_CW,
                                DEPOSITOR_ARM_NAV_RATE,
                                100,
                                25) == false)
            {
                // do nothing, navigating to center position
            }
            else
            {
                next_state = DEPOSITOR_STATE_DROPPING;
            }
            break;
        case DEPOSITOR_STATE_DROPPING:
            // execute the drop sequence with servo
            if (servo_command(SERVO_DEPOSITOR,
                              DEPOSITOR_OPEN_ANGLE,
                              DEPOSITOR_OPEN_STEPS,
                              DEPOSITOR_OPEN_RATE) == false)
            {
                // do nothing
            }
            else
            {
                next_state = DEPOSITOR_STATE_ENTERING_IDLE;
            }
            break;
        case DEPOSITOR_STATE_ENTERING_IDLE:
            if (stepper_command(STEPPER_DEPOSITOR,
                                DEPOSITOR_STEPS_TO_CENTER,
                                DEPOSITOR_ARM_CW,
                                DEPOSITOR_ARM_NAV_RATE,
                                100,
                                25) == false )
            {
                // do nothing, navigating back to idle position
            }
            else
            {
                if (servo_command(SERVO_DEPOSITOR,
                                  DEPOSITOR_OPEN_ANGLE,
                                  DEPOSITOR_OPEN_STEPS,
                                  DEPOSITOR_OPEN_RATE) == false)
                {
                    // do nothing, closing the depositor cup
                }
                else
                {
                    next_state = DEPOSITOR_STATE_IDLE;
                }
            }
            break;
        case DEPOSITOR_STATE_COUNT:
            break;
    }

    return next_state;
}

static PT_THREAD(run10ms(struct pt* thread))
{
    PT_BEGIN(thread);
    PT_WAIT_UNTIL(thread, 
                  scheduler_taskReleased(PERIOD_10ms, (uint8_t) DEPOSITOR));
    depositor_data.state = depositor_update_state(depositor_data.state);
    PT_END(thread);
}

/*******************************************************************************
*                       P U B L I C    F U N C T I O N S                       *
*******************************************************************************/ 

void depositor_init(void)
{
    // start subsystem thread
    PT_INIT(&depositor_data.thread);

    servo_init(SERVO_DEPOSITOR, DEPOSITOR_CLOSE_ANGLE);
    switch_init(SWITCH_DEPOSITOR);
    stepper_init(STEPPER_DEPOSITOR);
}

void depositor_run10ms(void)
{
    run10ms(&depositor_data.thread);
}

depositor_state_E depositor_getState(void)
{
    return depositor_data.state;
}

void depositor_cli_home(uint8_t argNumber, char* args[])
{
    stepper_commandUntil(STEPPER_DEPOSITOR, 
                         depositor_atHome, 
                         DEPOSITOR_ARM_CW, 
                         DEPOSITOR_ARM_HOME_RATE);
}
