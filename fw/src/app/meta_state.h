#ifndef META_STATE
#define META_STATE

/*******************************************************************************
 *                                I N C L U D E S                               *
 *******************************************************************************/

#include "depositor.h"
#include "imaging.h"
#include <string>
// #include <nlohmann/json.hpp>

/*******************************************************************************
 *                               C O N S T A N T S                              *
 *******************************************************************************/

/*******************************************************************************
 *                      D A T A    D E C L A R A T I O N S                      *
 *******************************************************************************/
typedef enum
{
    VERSION,
    IMAGING,
    DEPOSITOR,
    ISOLATION,
} state_machine_id_E;
/*******************************************************************************
 *            P U B L I C    F U N C T I O N    D E C L A R A T I O N S         *
 *******************************************************************************/
bool get_internal_meta_state(const char* output, int length);
void get_meta_state(uint8_t argNumber, char **args);

#define META_STATE_COMMANDS                                \
    {                                                      \
        get_meta_state, "get-meta-state", NULL, NULL, 0, 0 \
    }

#endif // META_STATE
