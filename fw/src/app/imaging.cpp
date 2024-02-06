
/*******************************************************************************
 *                                I N C L U D E S                               *
 *******************************************************************************/

#include "imaging.h"
#include "scheduler.h"

/*******************************************************************************
 *                               C O N S T A N T S                              *
 *******************************************************************************/
#define TOP_DOWN_ANGLE   50
#define SIDE_ON_ANGLE 50

#define IMAGING_ARM_CW 1 // 1 = go-home direction
#define IMAGING_ARM_GO_TOP_RATE 60 // Steps per second

#define IMAGING_ARM_CCW 0 // 1 = go-home direction
#define IMAGING_ARM_GO_SIDE_RATE 45 // Steps per second

#define IMAGING_PLANE_ROTATION_RATE 30 // Steps per second
#define IMAGING_PLANE_CW 1
#define IMAGING_PLANE_CCW 0
#define IMAGING_PLANE_RAMP_RATE 15
#define IMAGING_PLANE_RAMP_STEPS 10


/*******************************************************************************
 *                      D A T A    D E C L A R A T I O N S                      *
 *******************************************************************************/
typedef struct
{
    imaging_state_E state;
} imaging_data_S;

/*******************************************************************************
 *          P R I V A T E    F U N C T I O N    D E C L A R A T I O N S         *
 *******************************************************************************/

static imaging_state_E imaging_update_state(imaging_state_E curr_state);
static bool imaging_at_top(void);
static bool imaging_at_side(void);

/*******************************************************************************
 *                 S T A T I C    D A T A    D E F I N I T I O N S              *
 *******************************************************************************/
static imaging_data_S imaging_data =
{
    .state = IMAGING_STATE_IDLE
};
/*******************************************************************************
 *                      P R I V A T E    F U N C T I O N S                      *
 *******************************************************************************/
static imaging_state_E imaging_update_state(imaging_state_E curr_state)
{
    imaging_state_E next_state = curr_state;

    switch (curr_state)
    {
        case IMAGING_STATE_ENTERING_TOP_DOWN:
            if (stepper_commandUntil(STEPPER_ARM,
                         imaging_at_top,
                         IMAGING_ARM_CW,
                         IMAGING_ARM_GO_TOP_RATE) == false)
            {
            }
            else
            {
                // Set light once, after reaching top-down position.
                light_set_state(LIGHT_DOME, DOME_OFF);
                light_set_state(LIGHT_BOTTOM, BOTTOM_ON);
                next_state = IMAGING_STATE_TOP_DOWN;
            }
            break;
        case IMAGING_STATE_TOP_DOWN:
            break;
        case IMAGING_STATE_ENTERING_SIDE_ON:
        {
            // switch for side-on arm is not installed yet
            uint16_t plane_angle = 20;
            uint16_t plane_step_count = angle_to_steps(plane_angle);
            uint8_t plane_direction = plane_step_count < 0 ? IMAGING_PLANE_CCW : IMAGING_PLANE_CW;
            if (stepper_commandUntil(STEPPER_ARM,
                                imaging_at_side,
                                IMAGING_ARM_CCW,
                                IMAGING_ARM_GO_SIDE_RATE) == false
                ||
                stepper_command(STEPPER_PLANE,
                                plane_step_count,
                                plane_direction,
                                IMAGING_PLANE_ROTATION_RATE,
                                IMAGING_PLANE_RAMP_RATE,
                                IMAGING_PLANE_RAMP_STEPS
                                ) == false)
            {
                // do nothing
            }
            else
            {
                // the steppers have completed motion.
                // Set light once, after reaching side-on position.
                light_set_state(LIGHT_BOTTOM, BOTTOM_OFF);
                light_set_state(LIGHT_DOME, DOME_ON);
                next_state = IMAGING_STATE_SIDE_ON;
            }
            break;
        }
        case IMAGING_STATE_SIDE_ON:
            break;
        case IMAGING_STATE_IDLE:
            // waiting for commands
            // perform checks for other states to prevent motion
            break;
        case IMAGING_STATE_COUNT:
            break;
    }

    return next_state;
}

static bool imaging_at_top(void)
{
    return switch_state(SWITCH_ARM_TOP);
}

static bool imaging_at_side(void)
{
    return true;
    return switch_state(SWITCH_ARM_BOTTOM);

}

/*******************************************************************************
 *                       P U B L I C    F U N C T I O N S                       *
 *******************************************************************************/

void imaging_init(void)
{
    stepper_init(STEPPER_PLANE);
    stepper_init(STEPPER_ARM);
    light_init(LIGHT_BOTTOM);
    light_init(LIGHT_DOME);
}

void imaging_run10ms(void)
{
    imaging_data.state = imaging_update_state(imaging_data.state);
}

imaging_state_E imaging_getState(void)
{
    return imaging_data.state;
}

void imaging_cli_top_down(uint8_t argNumber, char *args[])
{
    // stepper_commandUntil(STEPPER_ARM,
    //                     imaging_at_top,
    //                     IMAGING_ARM_CW,
    //                     IMAGING_ARM_GO_TOP_RATE);
    // light_set_state(LIGHT_BOTTOM, BOTTOM_ON);
    imaging_data.state = IMAGING_STATE_ENTERING_TOP_DOWN;
}

void imaging_cli_side_on(uint8_t argNumber, char *args[])
{
    // side-on switch is not installed yet
    // stepper_commandUntil(STEPPER_DEPOSITOR,
    //                      depositor_atHome,
    //                      DEPOSITOR_ARM_CW,
    //                      DEPOSITOR_ARM_HOME_RATE);
    // int angle = atoi(args[1]);
    // int16_t step_count = angle_to_steps(angle);
    // uint8_t dir = 0;
    // if (step_count < 0) {
    //     dir = 1;
    // }
    // uint16_t ramp = 10; // 10 steps to ramp up
    // uint8_t ramp_start = 10;

    // stepper_command(STEPPER_PLANE,
    //                 step_count, 
    //                 dir,
    //                 IMAGING_PLANE_ROTATION_RATE,
    //                 ramp,
    //                 (int) IMAGING_PLANE_ROTATION_RATE / 2);
    imaging_data.state = IMAGING_STATE_ENTERING_SIDE_ON;
}
