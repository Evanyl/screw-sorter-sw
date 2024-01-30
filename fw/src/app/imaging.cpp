
/*******************************************************************************
 *                                I N C L U D E S                               *
 *******************************************************************************/

#include "imaging.h"
#include "scheduler.h"

/*******************************************************************************
 *                               C O N S T A N T S                              *
 *******************************************************************************/
#define TOP_DOWN_ANGLE   50
#define SIDE_ON_ANGLE 50

/*******************************************************************************
 *                      D A T A    D E C L A R A T I O N S                      *
 *******************************************************************************/

/*******************************************************************************
 *          P R I V A T E    F U N C T I O N    D E C L A R A T I O N S         *
 *******************************************************************************/

static imaging_state_E imaging_update_state(imaging_state_E curr_state);

/*******************************************************************************
 *                 S T A T I C    D A T A    D E F I N I T I O N S              *
 *******************************************************************************/

/*******************************************************************************
 *                      P R I V A T E    F U N C T I O N S                      *
 *******************************************************************************/

/*******************************************************************************
 *                       P U B L I C    F U N C T I O N S                       *
 *******************************************************************************/

void imaging_init(void)
{
    // switch_init(SWITCH_DEPOSITOR);
    // stepper_init(STEPPER_DEPOSITOR);
}

void imaging_run10ms(void)
{
    // depositor_data.state = depositor_update_state(depositor_data.state);
}

imaging_state_E imaging_getState(void)
{
    return IMAGING_STATE_COUNT;
}

void imaging_cli_top_down(uint8_t argNumber, char *args[])
{
    // stepper_commandUntil(STEPPER_DEPOSITOR,
    //                      depositor_atHome,
    //                      DEPOSITOR_ARM_CW,
    //                      DEPOSITOR_ARM_HOME_RATE);
}
