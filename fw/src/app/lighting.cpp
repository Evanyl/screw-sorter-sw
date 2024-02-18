/*******************************************************************************
*                                I N C L U D E S                               *
*******************************************************************************/ 

#include "lighting.h"
#include "scheduler.h"

/*******************************************************************************
*                               C O N S T A N T S                              *
*******************************************************************************/ 

#define LIGHTING_SIDELIGHT_DOWN 1
#define LIGHTING_SIDELIGHT_HOMING_RATE 100

/*******************************************************************************
*                      D A T A    D E C L A R A T I O N S                      *
*******************************************************************************/ 

typedef struct
{
    // some tracking of height after homing
    lighting_state_E state;
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
    .state = LIGHTING_STATE_NAV_HOME
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

    switch (curr_state)
    {
        case LIGHTING_STATE_NAV_HOME:
            // homing routine
            break;
        case LIGHTING_STATE_COUNT:
            break;
    }

    return next_state;
}

/*******************************************************************************
*                       P U B L I C    F U N C T I O N S                       *
*******************************************************************************/ 

void lighting_init(void)
{
    stepper_init(STEPPER_SIDELIGHT);
    switch_init(SWITCH_SIDELIGHT);
    light_init(LIGHT_BACK);
}

void lighting_run10ms(void)
{
    lighting_data.state = lighting_update_state(lighting_data.state);
}

lighting_state_E lighting_getState(void)
{
    return LIGHTING_STATE_COUNT;
}

void lighting_cli_home(uint8_t argNumber, char* args[])
{
    stepper_commandUntil(STEPPER_SIDELIGHT, 
                         lighting_atHome, 
                         LIGHTING_SIDELIGHT_DOWN, 
                         LIGHTING_SIDELIGHT_HOMING_RATE);
}
