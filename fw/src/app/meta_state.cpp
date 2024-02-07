
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
    // after any function successfully runs, print the state of the system to console
    // TODO: time this
    int len_state_arr = 3;
    int state_arr[len_state_arr];
    if (get_internal_meta_state(state_arr, len_state_arr) == true)
    {
        // conv to char array
        uint16_t max_digits = 1; // start at 1 because any number has a digit
        for (int i = 0; i < len_state_arr; i++) {
            int num_digits = 1;
            int curr = state_arr[i];
            while (curr != 0) {
                num_digits += 1;
                curr /= 10;
            }
            if (num_digits > max_digits) {
                max_digits = num_digits;
            }
        }
        // don't expect to exceed the size of the string
        char state_string[max_digits * (len_state_arr + 1) + 1];
        state_string[0] = '\0';
        for (int i = 0; i < len_state_arr; i++) {
            snprintf(state_string + strlen(state_string), max_digits + 1, "%d ", state_arr[i]);
        }
        serial_send_nl(PORT_COMPUTER, state_string);
    }
}