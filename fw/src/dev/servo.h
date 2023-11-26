#ifndef DEV_SERVO
#define DEV_SERVO

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
    SERVO_DEPOSITOR,
    SERVO_COUNT
} servo_id_E;

typedef void (*servo_update_f)(servo_id_E);

/*******************************************************************************
*            P U B L I C    F U N C T I O N    D E C L A R A T I O N S         *
*******************************************************************************/

void servo_init(servo_id_E, int16_t angle);
bool servo_command(servo_id_E servo, int16_t angle, uint8_t steps);
void servo_update(servo_id_E servo);

void servo_cli_move(uint8_t argNumber, char* args[]);
void servo_cli_dump(uint8_t argNumber, char* args[]);

#define SERVO_COMMANDS \
{servo_cli_move, "servo-move", NULL, NULL, 2, 2},\
{servo_cli_dump, "servo-dump", NULL, NULL, 1, 1}

#endif // DEV_SERVO
