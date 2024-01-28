
#ifndef APP_IMAGING
#define APP_IMAGING

/*******************************************************************************
 *                                I N C L U D E S                               *
 *******************************************************************************/

#include <Arduino.h>

#include "dev/stepper.h"
#include "dev/servo.h"

/*******************************************************************************
 *                               C O N S T A N T S                              *
 *******************************************************************************/

/*******************************************************************************
 *                      D A T A    D E C L A R A T I O N S                      *
 *******************************************************************************/

typedef enum
{
    IMAGING_STATE_TOP_DOWN,
    IMAGING_STATE_SIDE_ON,
    IMAGING_STATE_IDLE,
    IMAGING_STATE_COUNT
} imaging_state_E;

/*******************************************************************************
 *            P U B L I C    F U N C T I O N    D E C L A R A T I O N S         *
 *******************************************************************************/

void imaging_init(void);
void imaging_run10ms(void);
imaging_state_E imaging_getState(void);

void imaging_cli_top_down(uint8_t argNumber, char *args[]);

#define IMAGING_COMMANDS                                       \
    {                                                          \
        imaging_cli_home, "imaging-top-down", NULL, NULL, 0, 0 \
    }

#endif // APP_IMAGING
