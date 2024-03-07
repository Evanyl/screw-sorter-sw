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
    LIGHT_BACK,
    LIGHT_SIDE,
    LIGHT_COUNT
} light_id_E;

/*******************************************************************************
*                       P U B L I C    F U N C T I O N S                       *
*******************************************************************************/ 

void light_init(light_id_E light, uint16_t brightness);
void light_command(light_id_E light, uint16_t brightness);

void light_cli_update(uint8_t argNumber, char* args[]);

#define LIGHT_COMMANDS \
{light_cli_update, "light-update", NULL, NULL, 2, 2} \

#endif // DEV_LIGHT
