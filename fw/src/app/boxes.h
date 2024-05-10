
#ifndef APP_BOXES
#define APP_BOXES

/*******************************************************************************
*                                I N C L U D E S                               *
*******************************************************************************/ 

#include <Arduino.h>
#include <pt.h>

/*******************************************************************************
*                               C O N S T A N T S                              *
*******************************************************************************/ 

/*******************************************************************************
*                      D A T A    D E C L A R A T I O N S                      *
*******************************************************************************/ 

typedef enum 
{
    BOXES_STATE_STARTUP,
    BOXES_STATE_IDLE,
    BOXES_STATE_ACTIVE,
    BOXES_STATE_COUNT
} boxes_state_E;

/*******************************************************************************
*            P U B L I C    F U N C T I O N    D E C L A R A T I O N S         *
*******************************************************************************/

void boxes_init(void);
void boxes_run10ms(void);
boxes_state_E boxes_getState(void);
void boxes_cli_setDesState(uint8_t argNumber, char* args[]);
void boxes_cli_setBox(uint8_t argNumber, char* args[]);
void boxes_cli_home(uint8_t argNumber, char* args[]);
void boxes_cli_boxesDump(uint8_t argNumber, char* args[]);
void boxes_core_comms_setDesState(uint8_t argNumber, char* args[]);
void boxes_core_comms_setBox(uint8_t argNumber, char* args[]);

#define BOXES_CLI_COMMANDS \
{boxes_cli_setDesState, "boxes-des-state", NULL, NULL, 1, 1}, \
{boxes_cli_setBox, "boxes-box", NULL, NULL, 1, 1}, \
{boxes_cli_home, "boxes-home", NULL, NULL, 0, 0}, \
{boxes_cli_boxesDump, "boxes-dump", NULL, NULL, 0, 0}

#define BOXES_CORE_COMMS_COMMANDS \
{boxes_core_comms_setDesState, "boxes-des-state", 1}, \
{boxes_core_comms_setBox, "boxes-box", 1}

#endif // APP_BOXES
