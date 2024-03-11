
#ifndef APP_CLASSIFY_SYSTEM_STATE
#define APP_CLASSIFY_SYSTEM_STATE

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
    CLASSIFY_SYSTEM_STATE_STARTUP,
    CLASSIFY_SYSTEM_STATE_IDLE,
    CLASSIFY_SYSTEM_STATE_ENTERING_DEPOSITED,
    CLASSIFY_SYSTEM_STATE_DEPOSITED,
    CLASSIFY_SYSTEM_STATE_ENTERING_TOPDOWN,
    CLASSIFY_SYSTEM_STATE_TOPDOWN,
    CLASSIFY_SYSTEM_STATE_ENTERING_SIDEON,
    CLASSIFY_SYSTEM_STATE_SIDEON,
    CLASSIFY_SYSTEM_STATE_ENTERING_IDLE,
    CLASSIFY_SYSTEM_STATE_COUNT
} classify_system_state_E;

/*******************************************************************************
*            P U B L I C    F U N C T I O N    D E C L A R A T I O N S         *
*******************************************************************************/

void classify_system_state_init(void);
void classify_system_state_run100ms(void);
classify_system_state_E classify_system_state_getState(void);

void classify_system_state_cli_target(uint8_t argNumber, char* args[]);
void classify_system_state_cli_dump(uint8_t argNumer, char* args[]);

void classify_system_state_core_comms_setDesState(uint8_t argNumber, char* args[]);

#define CLASSIFY_SYSTEM_STATE_COMMANDS \
{classify_system_state_cli_target, "classify-system-state-target", NULL, NULL, 1, 1}, \
{classify_system_state_cli_dump, "classify-system-state-dump", NULL, NULL, 0, 0}

#define CLASSIFY_SYSTEM_STATE_CORE_COMMS_COMMANDS \
{classify_system_state_core_comms_setDesState, "classify-des-state", 1}

#endif // APP_CLASSIFY_SYSTEM_STATE
