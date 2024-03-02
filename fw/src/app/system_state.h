
#ifndef APP_SYSTEM_STATE
#define APP_SYSTEM_STATE

/*******************************************************************************
*                                I N C L U D E S                               *
*******************************************************************************/ 

#include <Arduino.h>

/*******************************************************************************
*                               C O N S T A N T S                              *
*******************************************************************************/ 

/*******************************************************************************
*                      D A T A    D E C L A R A T I O N S                      *
*******************************************************************************/ 

typedef enum 
{
    SYSTEM_STATE_STARTUP,
    SYSTEM_STATE_IDLE,
    SYSTEM_STATE_ENTERING_DEPOSITED,
    SYSTEM_STATE_DEPOSITED,
    SYSTEM_STATE_ENTERING_TOPDOWN,
    SYSTEM_STATE_TOPDOWN,
    SYSTEM_STATE_ENTERING_SIDEON,
    SYSTEM_STATE_SIDEON,
    SYSTEM_STATE_ENTERING_IDLE,
    SYSTEM_STATE_COUNT
} system_state_E;

/*******************************************************************************
*            P U B L I C    F U N C T I O N    D E C L A R A T I O N S         *
*******************************************************************************/

void system_state_init(void);
void system_state_run100ms(void);
system_state_E system_state_getState(void);

void system_state_cli_target(uint8_t argNumber, char* args[]);

void system_state_core_comms_setDesState(uint8_t argNumber, char* args[]);

#define SYSTEM_STATE_COMMANDS \
{system_state_cli_target, "system-state-target", NULL, NULL, 1, 1}

#define SYSTEM_STATE_CORE_COMMS_COMMANDS \
{system_state_core_comms_setDesState, "des-state", 1}

#endif // APP_SYSTEM_STATE
