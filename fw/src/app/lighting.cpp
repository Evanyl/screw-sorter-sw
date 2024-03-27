/*******************************************************************************
*                                I N C L U D E S                               *
*******************************************************************************/ 

#include "lighting.h"
#include "scheduler.h"
#include "system_state.h"

#include "dev/light.h"
#include "dev/servo.h"

/*******************************************************************************
*                               C O N S T A N T S                              *
*******************************************************************************/ 

#define LIGHTING_SIDELIGHT_UP 0
#define LIGHTING_SIDELIGHT_DOWN 1
#define LIGHTING_SIDELIGHT_HOMING_RATE 250
#define LIGHTING_SIDELIGHT_IDLE_HEIGHT_STEPS 6000

#define LIGHTING_NAV_RATE 1500

#define LIGHTING_BACKLIGHT_ON  0
#define LIGHTING_BACKLIGHT_OFF 65535
#define LIGHTING_SIDELIGHT_ON  0
#define LIGHTING_SIDELIGHT_OFF 65535

/*******************************************************************************
*                      D A T A    D E C L A R A T I O N S                      *
*******************************************************************************/ 

typedef struct
{
    lighting_state_E state;
    struct pt thread;
} lighting_data_S;

/*******************************************************************************
*          P R I V A T E    F U N C T I O N    D E C L A R A T I O N S         *
*******************************************************************************/

static bool lighting_atHome(void);
static lighting_state_E lighting_update_state(lighting_state_E curr_state);

/*******************************************************************************
*                 S T A T I C    D A T A    D E F I N I T I O N S              *
*******************************************************************************/ 

static lighting_data_S lighting_data = 
{
    .state = LIGHTING_STATE_HOMING
};

/*******************************************************************************
*                      P R I V A T E    F U N C T I O N S                      *
*******************************************************************************/

static bool lighting_atHome(void)
{
    return switch_state(SWITCH_SIDELIGHT);
}

static lighting_state_E lighting_update_state(lighting_state_E curr_state)
{
    lighting_state_E next_state = curr_state;
    system_state_E system_state = system_state_getState();

    switch (curr_state)
    {
        case LIGHTING_STATE_HOMING:
            if (stepper_commandUntil(STEPPER_SIDELIGHT, 
                                     lighting_atHome, 
                                     LIGHTING_SIDELIGHT_DOWN, 
                                     LIGHTING_SIDELIGHT_HOMING_RATE) == false)
            {
                // do nothing, homing.
            }
            else
            {
                next_state = LIGHTING_STATE_ENTERING_IDLE;
            }
            break;
        case LIGHTING_STATE_ENTERING_IDLE:
            if (stepper_command(STEPPER_SIDELIGHT,
                                LIGHTING_SIDELIGHT_IDLE_HEIGHT_STEPS,
                                LIGHTING_SIDELIGHT_UP,
                                LIGHTING_NAV_RATE,
                                750,
                                50) == false)
            {
                // do nothing, navigating to idle position.
            }
            else
            {
                stepper_calibSteps(STEPPER_SIDELIGHT);
                next_state = LIGHTING_STATE_IDLE;
            }
            break;
        case LIGHTING_STATE_IDLE:
            if (system_state == SYSTEM_STATE_ENTERING_TOPDOWN)
            {
                next_state = LIGHTING_STATE_ENTERING_TOPDOWN;
            }
            else
            {
                // do nothing, stay in the idle state
            }
            break;
        case LIGHTING_STATE_ENTERING_TOPDOWN:
            light_command(LIGHT_BACK, LIGHTING_BACKLIGHT_ON);
            next_state = LIGHTING_STATE_TOPDOWN;
            break;
        case LIGHTING_STATE_TOPDOWN:
            if (system_state == SYSTEM_STATE_ENTERING_SIDEON)
            {
                light_command(LIGHT_BACK, LIGHTING_BACKLIGHT_OFF);
                next_state = LIGHTING_STATE_ENTERING_SIDEON;
            }
            else
            {
                // do nothing, stay in topdown configuration
            }
            break;
        case LIGHTING_STATE_ENTERING_SIDEON:
            if (stepper_command(STEPPER_SIDELIGHT, 
                                LIGHTING_SIDELIGHT_IDLE_HEIGHT_STEPS, 
                                LIGHTING_SIDELIGHT_DOWN, 
                                LIGHTING_NAV_RATE,
                                750,
                                50) == false)
            {
                // do nothing, still navigating to deployed position
            }
            else
            {
                stepper_calibSteps(STEPPER_SIDELIGHT);
                light_command(LIGHT_SIDE, LIGHTING_SIDELIGHT_ON);
                next_state = LIGHTING_STATE_SIDEON;
            }
            break;
        case LIGHTING_STATE_SIDEON:
            if (system_state == SYSTEM_STATE_ENTERING_IDLE)
            {
                light_command(LIGHT_SIDE, LIGHTING_SIDELIGHT_OFF);
                next_state = LIGHTING_STATE_ENTERING_IDLE;
            }
            else
            {
                // do nothing, stay in sideon configuration
            }
            break;
        case LIGHTING_STATE_COUNT:
            break;
    }

    return next_state;
}

static PT_THREAD(run10ms(struct pt* thread))
{
    PT_BEGIN(thread);
    PT_WAIT_UNTIL(thread, 
                  scheduler_taskReleased(PERIOD_10ms, (uint8_t) LIGHTING));
    lighting_data.state = lighting_update_state(lighting_data.state);
    PT_END(thread);
}

/*******************************************************************************
*                       P U B L I C    F U N C T I O N S                       *
*******************************************************************************/ 

void lighting_init(void)
{
    PT_INIT(&lighting_data.thread);

    servo_init(SERVO_COVER, 0);
    stepper_init(STEPPER_SIDELIGHT);
    switch_init(SWITCH_SIDELIGHT);
    light_init(LIGHT_BACK, LIGHTING_BACKLIGHT_OFF);
    light_init(LIGHT_SIDE, LIGHTING_SIDELIGHT_OFF); 
}

void lighting_run10ms(void)
{
    run10ms(&lighting_data.thread);
}

lighting_state_E lighting_getState(void)
{
    return lighting_data.state;
}

void lighting_cli_home(uint8_t argNumber, char* args[])
{
    stepper_commandUntil(STEPPER_SIDELIGHT, 
                         lighting_atHome, 
                         LIGHTING_SIDELIGHT_DOWN, 
                         LIGHTING_SIDELIGHT_HOMING_RATE);
}
