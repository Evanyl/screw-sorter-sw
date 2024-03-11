
#ifndef APP_ISOLATION_SYSTEM_STATE
#define APP_ISOLATION_SYSTEM_STATE

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
    ISOLATION_SYSTEM_STATE_STARTUP,
    ISOLATION_SYSTEM_STATE_IDLE,
    ISOLATION_SYSTEM_STATE_ATTEMPT_ISOLATED,   // chug the belts some distance in an attempt to achieve isolation,
                                                // but confirmation of isolation is from camera
    ISOLATION_SYSTEM_STATE_ISOLATED,            // rpi sets this state when camera sees isolated fastener
    ISOLATION_SYSTEM_STATE_ENTERING_DELIVERED,
    ISOLATION_SYSTEM_STATE_DELIVERED,
    ISOLATION_SYSTEM_STATE_ENTERING_REJECT,
    ISOLATION_SYSTEM_STATE_REJECT,
    ISOLATION_SYSTEM_STATE_ENTERING_IDLE,
    ISOLATION_SYSTEM_STATE_COUNT
} isolation_system_state_E;

/*******************************************************************************
*            P U B L I C    F U N C T I O N    D E C L A R A T I O N S         *
*******************************************************************************/

void isolation_system_state_init(void);
void isolation_system_state_run100ms(void);
isolation_system_state_E isolation_system_state_getState(void);

void isolation_system_state_cli_target(uint8_t argNumber, char* args[]);
void isolation_system_state_cli_dump(uint8_t argNumer, char* args[]);

void isolation_system_state_core_comms_setDesState(uint8_t argNumber, char* args[]);

#define ISOLATION_SYSTEM_STATE_COMMANDS \
{isolation_system_state_cli_target, "isolation-system-state-target", NULL, NULL, 1, 1}, \
{isolation_system_state_cli_dump, "isolation-system-state-dump", NULL, NULL, 0, 0}

#define ISOLATION_SYSTEM_STATE_CORE_COMMS_COMMANDS \
{isolation_system_state_core_comms_setDesState, "isolation-des-state", 1}

#endif // APP_ISOLATION_SYSTEM_STATE
