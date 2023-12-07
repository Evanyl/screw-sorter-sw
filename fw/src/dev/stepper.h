
#ifndef DEV_STEPPER
#define DEV_STEPPER

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
    STEPPER_DEPOSITOR,
    STEPPER_COUNT
} stepper_id_E;

typedef void (*stepper_update_f)(stepper_id_E);

/*******************************************************************************
*            P U B L I C    F U N C T I O N    D E C L A R A T I O N S         *
*******************************************************************************/

void stepper_init(stepper_id_E stepper);
bool stepper_command(stepper_id_E stepper, uint16_t steps, uint8_t dir, uint16_t rate);
void stepper_update(stepper_id_E);

void stepper_cli_move(uint8_t argNumber, char* args[]);
void stepper_cli_dump(uint8_t argNumber, char* args[]);

#define STEPPER_COMMANDS \
{stepper_cli_move, "stepper-move", NULL, NULL, 4, 4},\
{stepper_cli_dump, "stepper-dump", NULL, NULL, 1, 1}

#endif
