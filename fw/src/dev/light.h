
#ifndef DEV_LIGHT
#define DEV_LIGHT

/*******************************************************************************
*                                I N C L U D E S                               *
*******************************************************************************/ 

#include <Arduino.h>

/*******************************************************************************
*                               C O N S T A N T S                              *
*******************************************************************************/ 

/*******************************************************************************
*                      D A T A    D E C L A R A T I O N S                      *
*******************************************************************************/ 

typedef enum
{
    LIGHT_BOTTOM,
    LIGHT_DOME,
    LIGHT_COUNT
} light_id_E;

typedef enum {
    BOTTOM_OFF = 0,
    BOTTOM_ON = 5,
    DOME_OFF = 100,
    DOME_ON = 50
} brightness_map_t;

/*******************************************************************************
*            P U B L I C    F U N C T I O N    D E C L A R A T I O N S         *
*******************************************************************************/

void light_init(light_id_E light_id);
int light_get_state(light_id_E light_id);
void light_set_state(light_id_E light_id, int brightness);

void light_cli_set_state(uint8_t argNumber, char* args[]);

#define LIGHT_COMMANDS \
{light_cli_set_state, "light-set", NULL, NULL, 2, 2} // provide the ID and its brightness in %

#endif // DEV_LIGHT
