
/*******************************************************************************
 *                                I N C L U D E S                               *
 *******************************************************************************/

#include "meta_state.h"
#include "dev/serial.h"

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
bool get_internal_meta_state(const char** output, int length)
{
    // TODO: Change this to proper serialization of structs.
    // We get the integer enums returned from getState() store it into output.
    const char* imaging_state = imaging_get_state_str();
    const char* depositing_state = depositor_get_state_str();
    // TODO add in isolation system once it is built
    const char* state_machine_version = "1.0";
    if (length == 3) {
        output[VERSION] = state_machine_version;
        output[IMAGING] = imaging_state;
        output[DEPOSITOR] = depositing_state;
        return true;
    } else {
        return false;
    }
}

void get_meta_state(uint8_t argNumber, char **args)
{
    // queries all state machines and populates a string with results
    // TODO: time this
    int len_state_arr = 3;
    const char* state_arr[len_state_arr];
    if (get_internal_meta_state(state_arr, len_state_arr) == true)
    {
        uint16_t total_char_len = 0;
        // calculate the max length of char array
        char state_string[SERIAL_MESSAGE_SIZE];
        state_string[0] = '\0';
        sprintf(state_string, "{\"version\":%s, \"imaging\":%s, \"depositor\":%s}", state_arr[0], state_arr[1], state_arr[2]);
        serial_send_nl(PORT_COMPUTER, state_string);        
    }
    else
    {
        serial_send_nl(PORT_COMPUTER, "get_meta_state_failed");
    }
}