#ifndef SERIAL_COMM
#define SERIAL_COMM

/*******************************************************************************
*                               Standard Includes
*******************************************************************************/

#include <Arduino.h>

/*******************************************************************************
*                               Header File Includes
*******************************************************************************/

/*******************************************************************************
*                               Static Functions
*******************************************************************************/

/*******************************************************************************
*                               Constants
*******************************************************************************/

#define CMD_EOL              '\n'
#define STRING_EOL           '\0'
#define COMMAND_BUFF_MAX_LEN 30
#define COMMAND_ARGS_MAX_LEN 4

/*******************************************************************************
*                               Structures
*******************************************************************************/

typedef struct {
    // char array to store the message
    char line[COMMAND_BUFF_MAX_LEN];
    // index to add next char received
    uint8_t index;
} message_t;

/*******************************************************************************
*                               Variables
*******************************************************************************/

/*******************************************************************************
*                               Functions
*******************************************************************************/

void serial_init();

void serial_send(char* bytes);

bool serial_handleByte(char byte);

void serial_echo();

#endif