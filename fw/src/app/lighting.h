#ifndef APP_LIGHTING
#define APP_LIGHTING

/*******************************************************************************
*                                I N C L U D E S                               *
*******************************************************************************/ 

#include <Arduino.h>

#include "dev/stepper.h"
#include "dev/switch.h"
#include "dev/light.h"

/*******************************************************************************
*                               C O N S T A N T S                              *
*******************************************************************************/ 

/*******************************************************************************
*                      D A T A    D E C L A R A T I O N S                      *
*******************************************************************************/ 

typedef enum 
{
    LIGHTING_STATE_HOMING,
    LIGHTING_STATE_ENTERING_IDLE,
    LIGHTING_STATE_IDLE,
    LIGHTING_STATE_ENTERING_TOPDOWN,
    LIGHTING_STATE_TOPDOWN,
    LIGHTING_STATE_ENTERING_SIDEON,
    LIGHTING_STATE_SIDEON,
    LIGHTING_STATE_COUNT
} lighting_state_E;

/*******************************************************************************
*            P U B L I C    F U N C T I O N    D E C L A R A T I O N S         *
*******************************************************************************/

void lighting_init(void);
void lighting_run10ms(void);
lighting_state_E lighting_getState(void);

void lighting_cli_home(uint8_t argNumber, char* args[]);

#define LIGHTING_COMMANDS \
{lighting_cli_home, "lighting-home", NULL, NULL, 0, 0}

#endif // APP_LIGHTING
