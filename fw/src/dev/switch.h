
#ifndef DEV_SWITCH
#define DEV_SWITCH

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
#ifdef DEPOSIT
    SWITCH_BOXES,
#elif ISOLATE_CLASSIFY
    SWITCH_DEPOSITOR,
    SWITCH_ARM,
    SWITCH_SIDELIGHT,
#else
    // nothing
#endif
    SWITCH_COUNT
} switch_id_E;

/*******************************************************************************
*            P U B L I C    F U N C T I O N    D E C L A R A T I O N S         *
*******************************************************************************/

void switch_init(switch_id_E switch_id);
bool switch_state(switch_id_E switch_id);

void switch_cli_state(uint8_t argNumber, char* args[]);

#define SWITCH_COMMANDS \
{switch_cli_state, "switch-state", NULL, NULL, 1, 1}

#endif
