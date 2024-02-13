
#ifndef APP_DEPOSITOR
#define APP_DEPOSITOR

/*******************************************************************************
*                                I N C L U D E S                               *
*******************************************************************************/ 

#include <Arduino.h>

#include "dev/stepper.h"
#include "dev/servo.h"
#include "dev/switch.h"

/*******************************************************************************
*                               C O N S T A N T S                              *
*******************************************************************************/ 

#define DEPOSITOR_ANGLE_OPEN   -90.0
#define DEPOSITOR_ANGLE_CLOSED  62.0

/*******************************************************************************
*                      D A T A    D E C L A R A T I O N S                      *
*******************************************************************************/ 

typedef enum 
{
    DEPOSITOR_STATE_ENTERING_HOME,
    DEPOSITOR_STATE_HOME,
    DEPOSITOR_STATE_ENTERING_CENTER,
    DEPOSITOR_STATE_CENTER,
    DEPOSITOR_STATE_DROP,
    DEPOSITOR_STATE_ENTERING_END,
    DEPOSITOR_STATE_END,
    DEPOSITOR_STATE_IDLE,
    DEPOSITOR_STATE_COUNT
} depositor_state_E;

/*******************************************************************************
*            P U B L I C    F U N C T I O N    D E C L A R A T I O N S         *
*******************************************************************************/

void depositor_init(void);
void depositor_run10ms(void);
const char* depositor_get_state_str(void);
depositor_state_E depositor_get_state_enum(void);

void depositor_cli_home(uint8_t argNumber, char* args[]);
void depositor_cli_center(uint8_t argNumber, char* args[]);


#define DEPOSITOR_COMMANDS \
{depositor_cli_home, "depositor-home", NULL, NULL, 0, 0},\
{depositor_cli_center, "depositor-center", NULL, NULL, 0, 0}


#endif // APP_DEPOSITOR
