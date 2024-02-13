
#ifndef APP_IMAGING
#define APP_IMAGING

/*******************************************************************************
 *                                I N C L U D E S                               *
 *******************************************************************************/

#include <Arduino.h>

#include "dev/stepper.h"
#include "dev/light.h"
#include "dev/switch.h"

/*******************************************************************************
 *                               C O N S T A N T S                              *
 *******************************************************************************/

/*******************************************************************************
 *                      D A T A    D E C L A R A T I O N S                      *
 *******************************************************************************/

typedef enum
{
    IMAGING_STATE_ENTERING_TOP_DOWN,
    IMAGING_STATE_TOP_DOWN,
    IMAGING_STATE_ENTERING_SIDE_ON,
    IMAGING_STATE_SIDE_ON,
    IMAGING_STATE_COUNT
} imaging_state_E;

/*******************************************************************************
 *            P U B L I C    F U N C T I O N    D E C L A R A T I O N S         *
 *******************************************************************************/

void imaging_init(void);
void imaging_run10ms(void);
const char* imaging_get_state_str(void);
imaging_state_E imaging_get_state_enum(void);

void imaging_cli_top_down(uint8_t argNumber, char *args[]);
void imaging_cli_side_on(uint8_t argNumber, char *args[]);

#define IMAGING_COMMANDS \
{imaging_cli_top_down, "imaging-top-down", NULL, NULL, 0, 0},\
{imaging_cli_side_on, "imaging-side-on", NULL, NULL, 1, 1}

#endif // APP_IMAGING
