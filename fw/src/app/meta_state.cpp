
/*******************************************************************************
 *                                I N C L U D E S                               *
 *******************************************************************************/

#include "meta_state.h"

/*******************************************************************************
 *                               C O N S T A N T S                              *
 *******************************************************************************/

/*******************************************************************************
 *                      D A T A    D E C L A R A T I O N S                      *
 *******************************************************************************/

/*******************************************************************************
 *          P R I V A T E    F U N C T I O N    D E C L A R A T I O N S         *
 *******************************************************************************/

/*******************************************************************************
 *                 S T A T I C    D A T A    D E F I N I T I O N S              *
 *******************************************************************************/

/*******************************************************************************
 *                      P R I V A T E    F U N C T I O N S                      *
 *******************************************************************************/

/*******************************************************************************
 *                       P U B L I C    F U N C T I O N S                       *
 *******************************************************************************/
// todo: figure out how to send output in reponse to a CLI command
bool get_internal_meta_state(int* output, int length)
{
    // TODO: Change this to proper serialization of structs.
    // We get the integer enums returned from getState() store it into output.
    imaging_state_E imaging_state = imaging_getState();
    depositor_state_E depositing_state = depositor_getState();
    // TODO add in isolation system once it is built
    int version = 1;
    if (length == 3) {
        output[0] = version;
        output[1] = imaging_state;
        output[2] = depositing_state;
        return true;
    } else {
        return false;
    }
}

void get_meta_state(uint8_t argNumber, char **args)
{
    // internal implementation is do-nothing, since every successful function call runs get_internal_meta_state()
    // this is a workaround because CLI functions cannot have return values
}