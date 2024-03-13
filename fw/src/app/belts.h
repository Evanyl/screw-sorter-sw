
#ifndef APP_BELTS
#define APP_BELTS

/*******************************************************************************
*                                I N C L U D E S                               *
*******************************************************************************/ 

#include <Arduino.h>
#include <pt.h>

#include "dev/stepper.h"

/*******************************************************************************
*                               C O N S T A N T S                              *
*******************************************************************************/ 

#define BELTS_NAV_RATE 750
#define BELTS_STARTING_RATE 50
#define BELTS_RAMP_WINDOW 250

#define BELT_TOP_FORWARD 1
#define BELT_TOP_BACKWARD 0
#define BELT_BOTTOM_FORWARD 1
#define BELT_BOTTOM_BACKWARD 0
/*******************************************************************************
*                      D A T A    D E C L A R A T I O N S                      *
*******************************************************************************/ 

typedef enum 
{
    BELTS_STATE_IDLE,
    BELTS_STATE_ACTIVE,
    BELTS_STATE_COUNT
} belts_state_E;

/*******************************************************************************
*            P U B L I C    F U N C T I O N    D E C L A R A T I O N S         *
*******************************************************************************/

void belts_init(void);
void belts_run10ms(void);
belts_state_E belts_getState(void);
void belts_core_comms_setDesState(uint8_t argNumber, char* args[]);
void belts_cli_dump_state(uint8_t argNumber, char* args[]);
void belts_cli_target(uint8_t argNumber, char* args[]);

#define BELTS_CORE_COMMS_COMMANDS \
{belts_core_comms_setDesState, "belts-des-state", 2}

#define BELTS_COMMANDS \
{belts_cli_dump_state, "belts-dump-state", NULL, NULL, 0, 0}, \
{belts_cli_target, "belts-target", NULL, NULL, 2, 2}

#endif // APP_BELTS
