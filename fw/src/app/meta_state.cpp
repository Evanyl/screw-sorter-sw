
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
std::string get_internal_meta_state(void);

/*******************************************************************************
 *                 S T A T I C    D A T A    D E F I N I T I O N S              *
 *******************************************************************************/

/*******************************************************************************
 *                      P R I V A T E    F U N C T I O N S                      *
 *******************************************************************************/

std::string get_internal_meta_state(void)
{
    nlohmann::json output_json = {
        {"state_machines", {{"depositor", depositor_getState()}, {"imaging", imaging_getState()}}}};
    // iterate through all state machines, running their getters
    // their getters populate each portion of the JSON
    return output_json.dump();
}
/*******************************************************************************
 *                       P U B L I C    F U N C T I O N S                       *
 *******************************************************************************/
// todo: figure out how to send output in reponse to a CLI command
void get_meta_state(uint8_t argNumber, char **args)
{
    get_internal_meta_state();
}