
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

#define DEPOSITOR_CLOSE_STEPS  255
#define DEPOSITOR_CLOSE_RATE   255
#define DEPOSITOR_CLOSE_ANGLE  62.0 // Fully closed

#define DEPOSITOR_OPEN_STEPS   255
#define DEPOSITOR_OPEN_RATE    255
#define DEPOSITOR_OPEN_ANGLE   0.0 //-90.0 achieves full open

#define DEPOSITOR_SLIT_ANGLE   DEPOSITOR_CLOSE_ANGLE - 12.0
#define DEPOSITOR_SLIT_RATE    255
#define DEPOSITOR_SLIT_STEPS   5

#define DEPOSITOR_ARM_HOME_ANGLE 0.0
#define DEPOSITOR_ARM_CENTER_ANGLE 75.0
#define DEPOSITOR_ARM_SWEEP_ANGLE  110.0
#define DEPOSITOR_ARM_RAMP_ANGLE 5.0 // Degrees

#define DEPOSITOR_ARM_NAV_RATE 1500
#define DEPOSITOR_ARM_HOME_RATE 150
#define DEPOSITOR_ARM_STARTING_RATE 250 // Steps per second

#define DEPOSITOR_ARM_CW 1

#define DEPOSITOR_JOSTLE_MOVEMENTS 40
#define DEPOSITOR_JOSTLE_ITERATIONS 4
#define DEPOSITOR_DELTA_THETA 1.0
#define DEPOSITOR_JOSTLE_RATE 1000

/*******************************************************************************
*                      D A T A    D E C L A R A T I O N S                      *
*******************************************************************************/ 

typedef struct
{
    struct pt  thread;
    depositor_state_E state;
    int8_t jostle_iter_counter;
    int8_t jostle_counter;
    uint16_t jostle_rate;
    float jostle_routine[DEPOSITOR_JOSTLE_MOVEMENTS];
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
    .jostle_iter_counter = 0,
    .jostle_counter = 0,
    .jostle_rate = DEPOSITOR_JOSTLE_RATE,
    .jostle_routine = {0,0.25,-0.25,0.25,-0.25,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0},
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
                next_state = DEPOSITOR_STATE_CENTERING;
            }
            break;

        case DEPOSITOR_STATE_CENTERING:
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
                                  DEPOSITOR_SLIT_ANGLE,
                                  DEPOSITOR_SLIT_STEPS,
                                  DEPOSITOR_SLIT_RATE) == false)
                {
                    // do nothing
                }
                else
                {
                    next_state = DEPOSITOR_STATE_DROPPING;
                }
            }
            break;

        case DEPOSITOR_STATE_DROPPING:
            if (depositor_data.jostle_counter < DEPOSITOR_JOSTLE_MOVEMENTS)
            {
                uint8_t j = depositor_data.jostle_counter;
                float dtheta = depositor_data.jostle_routine[j];
                bool stepper = stepper_commandAngle(STEPPER_DEPOSITOR, 
                                        DEPOSITOR_ARM_CENTER_ANGLE + dtheta,
                                        0.0,
                                        depositor_data.jostle_rate,
                                        depositor_data.jostle_rate);
                if (stepper == false)
                {
                    // wait for current motion to finish
                }
                else
                {
                    depositor_data.jostle_counter++;
                }
            }
            else if (depositor_data.jostle_iter_counter < DEPOSITOR_JOSTLE_ITERATIONS)
            {
                uint8_t m = depositor_data.jostle_iter_counter;
                // open servo little bit more
                if (servo_command(SERVO_DEPOSITOR,
                                  DEPOSITOR_SLIT_ANGLE - (m+1)*DEPOSITOR_DELTA_THETA,
                                  50,
                                  100) == false)
                {
                    // do nothing
                }
                else
                {
                    depositor_data.jostle_counter = 0;
                    depositor_data.jostle_iter_counter += 1;
                    // depositor_data.jostle_rate -= 100;
                }
            }
            else
            {
                if (servo_command(SERVO_DEPOSITOR,
                                  DEPOSITOR_OPEN_ANGLE,
                                  DEPOSITOR_OPEN_STEPS,
                                  DEPOSITOR_OPEN_RATE) == false)
                {
                    // wait for cup to open
                }
                else
                {
                    // reset jostle counter for next time, change state
                    depositor_data.jostle_counter = 0;
                    depositor_data.jostle_iter_counter = 0;
                    depositor_data.jostle_rate = DEPOSITOR_JOSTLE_RATE;
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
