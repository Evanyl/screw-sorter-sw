
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
#define DEPOSITOR_OPEN_RATE    25
#define DEPOSITOR_OPEN_ANGLE   0.0 //-90.0 achieves full open

#define DEPOSITOR_CLOSE_STEPS  255
#define DEPOSITOR_CLOSE_RATE   255
#define DEPOSITOR_CLOSE_ANGLE  62.0 // Fully closed

#define DEPOSITOR_ARM_HOME_ANGLE 0.0
#define DEPOSITOR_ARM_CENTER_ANGLE 75.0
#define DEPOSITOR_ARM_SWEEP_ANGLE  110.0
#define DEPOSITOR_ARM_RAMP_ANGLE 5.0 // Degrees

#define DEPOSITOR_ARM_NAV_RATE 750
#define DEPOSITOR_ARM_HOME_RATE 150
#define DEPOSITOR_ARM_STARTING_RATE 250 // Steps per second

#define DEPOSITOR_ARM_CW 1

/*******************************************************************************
*                      D A T A    D E C L A R A T I O N S                      *
*******************************************************************************/ 

typedef struct
{
    struct pt  thread;
    depositor_state_E state;
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
                    // home position, zero stepper angle
                    stepper_calibAngle(STEPPER_DEPOSITOR, 
                                       DEPOSITOR_ARM_HOME_ANGLE);
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
            if (stepper_commandAngle(STEPPER_DEPOSITOR, 
                                     DEPOSITOR_ARM_SWEEP_ANGLE, 
                                     DEPOSITOR_ARM_RAMP_ANGLE, 
                                     DEPOSITOR_ARM_NAV_RATE, 
                                     DEPOSITOR_ARM_STARTING_RATE) == false)
            {
                // do nothing, sweeping away previous screw
            }
            else
            {
                next_state = DEPOSITOR_STATE_DROPPING;
            }
            break;

        case DEPOSITOR_STATE_DROPPING:
            if (stepper_commandAngle(STEPPER_DEPOSITOR, 
                                     DEPOSITOR_ARM_CENTER_ANGLE, 
                                     DEPOSITOR_ARM_RAMP_ANGLE, 
                                     DEPOSITOR_ARM_NAV_RATE, 
                                     DEPOSITOR_ARM_STARTING_RATE) == false)
            {
                // do nothing, navigating to the center
            }
            else
            {
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
            }
            break;

        case DEPOSITOR_STATE_ENTERING_IDLE:
            if (stepper_commandAngle(STEPPER_DEPOSITOR,
                                     DEPOSITOR_ARM_HOME_ANGLE,
                                     DEPOSITOR_ARM_RAMP_ANGLE,
                                     DEPOSITOR_ARM_NAV_RATE,
                                     DEPOSITOR_ARM_STARTING_RATE) == false)
            {
                // do nothing, navigating back to home position
            }
            else
            {
                if (servo_command(SERVO_DEPOSITOR,
                                  DEPOSITOR_CLOSE_ANGLE,
                                  DEPOSITOR_CLOSE_STEPS,
                                  DEPOSITOR_CLOSE_RATE) == false)
                {
                    // do nothing, servo closing
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

    // TODO remove this
    stepper_init(STEPPER_BELT_TOP);
    stepper_init(STEPPER_BELT_BOTTOM);
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
    stepper_calibAngle(STEPPER_DEPOSITOR, 0.0);
}
