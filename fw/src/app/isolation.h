
#ifndef APP_ISOLATION
#define APP_ISOLATION

/*******************************************************************************
*                                I N C L U D E S                               *
*******************************************************************************/ 

#include <Arduino.h>

#include "dev/stepper.h"

/*******************************************************************************
*                               C O N S T A N T S                              *
*******************************************************************************/ 

/*******************************************************************************
*                      D A T A    D E C L A R A T I O N S                      *
*******************************************************************************/ 

typedef enum 
{
    ISOLATION_STATE_IDLE,
    ISOLATION_STATE_MOVING,
    ISOLATION_STATE_ISOLATED,
    ISOLATION_STATE_COUNT
} isolation_state_E;

/*******************************************************************************
*            P U B L I C    F U N C T I O N    D E C L A R A T I O N S         *
*******************************************************************************/

void isolation_init(void);
void isolation_run10ms(void);
isolation_state_E isolation_getState(void);


#define ISOLATION_COMMANDS \
{isolation_cli_home, "isolation-home", NULL, NULL, 0, 0}

#endif // APP_isolation
