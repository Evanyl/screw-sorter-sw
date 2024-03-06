#ifndef APP_ARM
#define APP_ARM

/*******************************************************************************
*                                I N C L U D E S                               *
*******************************************************************************/ 

#include <Arduino.h>

#include "dev/stepper.h"
#include "dev/switch.h"

/*******************************************************************************
*                               C O N S T A N T S                              *
*******************************************************************************/ 

/*******************************************************************************
*                      D A T A    D E C L A R A T I O N S                      *
*******************************************************************************/ 

typedef enum 
{
    ARM_STATE_HOMING,
    ARM_STATE_IDLE,
    ARM_STATE_ENTERING_TOPDOWN,
    ARM_STATE_TOPDOWN,
    ARM_STATE_ENTERING_SIDEON,
    ARM_STATE_SIDEON,
    ARM_STATE_ENTERING_IDLE,
    ARM_STATE_COUNT
} arm_state_E;

/*******************************************************************************
*            P U B L I C    F U N C T I O N    D E C L A R A T I O N S         *
*******************************************************************************/

void arm_init(void);
void arm_run10ms(void);
arm_state_E arm_getState(void);

void arm_cli_home(uint8_t argNumber, char* args[]);

#define ARM_COMMANDS \
{arm_cli_home, "arm-home", NULL, NULL, 0, 0}

#endif // APP_ARM
