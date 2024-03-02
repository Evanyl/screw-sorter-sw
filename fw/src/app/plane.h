
#ifndef APP_PLANE
#define APP_PLANE

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
    PLANE_STATE_IDLE,
    PLANE_STATE_ENTERING_ACTIVE,
    PLANE_STATE_ACTIVE,
} plane_state_E;

/*******************************************************************************
*            P U B L I C    F U N C T I O N    D E C L A R A T I O N S         *
*******************************************************************************/

void plane_init(void);
void plane_run10ms(void);
plane_state_E plane_getState(void);
void plane_core_comms_setCorrAngle(uint8_t argNumber, char* args[]);

#define PLANE_CORE_COMMS_COMMANDS \
{plane_core_comms_setCorrAngle, "corr-angle", 1}

#endif // APP_PLANE
