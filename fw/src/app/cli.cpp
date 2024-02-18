
/*******************************************************************************
*                                I N C L U D E S                               *
*******************************************************************************/ 

#include "cli.h"
#include "dev/servo.h"
#include "dev/stepper.h"
#include "dev/switch.h"
#include "app/depositor.h"
#include "app/lighting.h"

/*******************************************************************************
*                               C O N S T A N T S                              *
*******************************************************************************/ 

#define CLI_MAX_ARGS            7
#define CLI_CMD_LIST_TERMINATOR "END OF LIST"
#define CLI_PROMPT              "snorter>"

/*******************************************************************************
*                      D A T A    D E C L A R A T I O N S                      *
*******************************************************************************/ 

typedef void (*cli_f)(uint8_t argNumber, char* args[]);

typedef struct {
    cli_f       function;
    const char* command;
    const char* parameters;
    const char* description;
    uint8_t     minParam;
    uint8_t     maxParam;
} cli_cmd_s;

typedef struct
{
    struct pt  thread;
    char       line[SERIAL_MESSAGE_SIZE];
    char*      args[CLI_MAX_ARGS];
    char*      tokLine[(SERIAL_MESSAGE_SIZE + 1)];
    cli_cmd_s  cmds[];
} cli_data_s;

/*******************************************************************************
*          P R I V A T E    F U N C T I O N    D E C L A R A T I O N S         *
*******************************************************************************/ 

static char run100ms(struct pt* thread);

/*******************************************************************************
*                 S T A T I C    D A T A    D E F I N I T I O N S              *
*******************************************************************************/ 

// char line[SERIAL_MESSAGE_SIZE] = {' '};

static cli_data_s cli_data = 
{
    .cmds = 
    {
        SERVO_COMMANDS,
        STEPPER_COMMANDS,
        SWITCH_COMMANDS,
        DEPOSITOR_COMMANDS,
        LIGHTING_COMMANDS,
        {NULL, CLI_CMD_LIST_TERMINATOR, NULL, NULL, 0, 0}
    }
};

/*******************************************************************************
*                      P R I V A T E    F U N C T I O N S                      *
*******************************************************************************/ 

void cli_parseLine(char* message)
{
    // Tokenize the line with spaces as the delimiter
    char* tok = (char*) strtok(message, " ");
    uint8_t i = 0;
    while (tok != NULL && i < (CLI_MAX_ARGS + 1))
    {
        cli_data.tokLine[i] = tok;
        tok = strtok(NULL, " ");
        i++;
    }

    // Find a match for the command entered
    uint8_t j = 0;
    cli_cmd_s* cmds = cli_data.cmds;
    while (strcmp(cmds[j].command, CLI_CMD_LIST_TERMINATOR) != 0)
    {
        if (strcmp(cmds[j].command, cli_data.tokLine[0]) == 0)
        {
            break; // found the right command
        }
        j++;
    }

    // Process the command entered
    if (strcmp(message, "") != 0)
    {
        if (strcmp(cmds[j].command, CLI_CMD_LIST_TERMINATOR) == 0)
        {
            serial_send_nl(PORT_COMPUTER, "invalid command");
        }
        else if ((i - 1) > cmds[j].maxParam)
        {
            serial_send_nl(PORT_COMPUTER, "too many args");
        }
        else if ((i - 1) < cmds[j].minParam)
        {
            serial_send_nl(PORT_COMPUTER, "too few args");
        }
        else
        {
            // Package the args into a char* array
            for (uint8_t k = 1; k < i; k++)
            {
                cli_data.args[(k - 1)] = cli_data.tokLine[k];
            }

            // Call the function corresponding to the comannd with args
            cli_f func = cmds[j].function;
            func(i, cli_data.args);
        }
    }
    // reset the args and command arrays
    memset(cli_data.tokLine, '\0', sizeof(cli_data.tokLine));
    memset(cli_data.args, '\0', sizeof(cli_data.args));
}

static PT_THREAD(run100ms(struct pt* thread))
{
    PT_BEGIN(thread);
    PT_WAIT_UNTIL(thread, scheduler_taskReleased(PERIOD_100ms, (uint8_t) CLI));

    // wait until there is serial data
    while (serial_available(PORT_COMPUTER))
    {
        if (serial_handleByte(PORT_COMPUTER, serial_readByte(PORT_COMPUTER)))
        {
            serial_echo(PORT_COMPUTER);
            // char* line = (char*) malloc(SERIAL_MESSAGE_SIZE);
            // Serial.println(line);
            serial_getLine(PORT_COMPUTER, cli_data.line);
            cli_parseLine(cli_data.line);
            // free(line);
            serial_send(PORT_COMPUTER, CLI_PROMPT);
            break;
        }
    }

    PT_END(thread);
}

/*******************************************************************************
*                       P U B L I C    F U N C T I O N S                       *
*******************************************************************************/ 

void cli_init(void)
{
    PT_INIT(&cli_data.thread);
    serial_init(PORT_COMPUTER);
}

void cli_run100ms(void)
{
    run100ms(&cli_data.thread);
}
