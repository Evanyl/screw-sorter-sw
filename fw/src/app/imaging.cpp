
/*******************************************************************************
 *                                I N C L U D E S                               *
 *******************************************************************************/

#include "imaging.h"
#include "scheduler.h"
#include "serial.h"

/*******************************************************************************
 *                               C O N S T A N T S                              *
 *******************************************************************************/
#define TOP_DOWN_ANGLE   50
#define SIDE_ON_ANGLE 50

#define IMAGING_ARM_CW 1 // 1 = go-home direction
#define IMAGING_ARM_GO_TOP_RATE 60 // Steps per second

#define IMAGING_ARM_CCW 0 // 1 = go-home direction
#define IMAGING_ARM_GO_BOT_RATE 45 // Steps per second

#define IMAGING_PLANE_ROTATION_RATE 30 // Steps per second


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
        case IMAGING_STATE_TOP_DOWN:
            if (stepper_commandUntil(STEPPER_ARM,
                         imaging_at_top,
                         IMAGING_ARM_CW,
                         IMAGING_ARM_GO_TOP_RATE) == false)
            {
                light_set_state(LIGHT_BOTTOM, BOTTOM_ON);
            }
            else
            {
                next_state = IMAGING_STATE_IDLE;
            }
            break;

        case IMAGING_STATE_SIDE_ON:
            // switch for side-on arm is not installed yet
            // stepper_commandUntil(STEPPER_ARM,
            //              imaging_at_side,
            //              IMAGING_ARM_CCW,
            //              IMAGING_ARM_GO_BOT_RATE) == false);
            light_set_state(LIGHT_BOTTOM, BOTTOM_ON);

            // wait on serial message from RPi

        case IMAGING_STATE_IDLE:
            // waiting for commands
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
    return switch_state(SWITCH_ARM_SIDE);

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
    return IMAGING_STATE_COUNT;
}

void imaging_cli_top_down(uint8_t argNumber, char *args[])
{
    if (strcmp(args[0], "top-down-imaging") == 0)
    {
        stepper_commandUntil(STEPPER_ARM,
                            imaging_at_top,
                            IMAGING_ARM_CW,
                            IMAGING_ARM_GO_TOP_RATE);
        light_set_state(LIGHT_BOTTOM, BOTTOM_ON);
    } else {
        serial_send_nl(PORT_COMPUTER, "invalid imaging command");
    }
}

void imaging_cli_side_on(uint8_t argNumber, char *args[])
{
    // side-on switch is not installed yet
    // stepper_commandUntil(STEPPER_DEPOSITOR,
    //                      depositor_atHome,
    //                      DEPOSITOR_ARM_CW,
    //                      DEPOSITOR_ARM_HOME_RATE);
    int angle = atoi(args[1]);
    int16_t step_count = angle_to_steps(angle);
    uint8_t dir = 0;
    if (step_count < 0) {
        dir = 1;
    }
    uint16_t ramp = 10; // 10 steps to ramp up
    uint8_t ramp_start = 10;

    stepper_command(STEPPER_PLANE,
                    step_count, 
                    dir,
                    IMAGING_PLANE_ROTATION_RATE,
                    ramp,
                    (int) IMAGING_PLANE_ROTATION_RATE / 2);
}
