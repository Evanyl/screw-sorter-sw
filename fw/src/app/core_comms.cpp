/*******************************************************************************
*                                I N C L U D E S                               *
*******************************************************************************/ 

#include "core_comms.h"
#ifdef DEPOSIT
#include "boxes.h"
#elif ISOLATE_CLASSIFY
#include "plane.h"
#include "system_state.h"
#include "belts.h"
#include "depositor.h"
#else
// nothing
#endif

/*******************************************************************************
*                               C O N S T A N T S                              *
*******************************************************************************/ 

#define CORE_COMMS_CMD_LIST_TERMINATOR "END OF LIST"
#define CORE_COMMS_MAX_ARGS 10

/*******************************************************************************
*                      D A T A    D E C L A R A T I O N S                      *
*******************************************************************************/ 

typedef void (*core_comms_f) (uint8_t argNumber, char* args[]);

typedef struct
{
    const core_comms_f func;
    const char* command;
    const uint8_t params;
} core_comms_cmd_s;

typedef struct
{
#ifdef DEPOSIT
    // nothing
#elif ISOLATE_CLASSIFY
    system_state_E des_state;
    float corr_angle;

    belts_state_E belts_des_state;
    uint16_t top_belt_steps;
    uint16_t bottom_belt_steps;
#else
    // nothing
#endif
} core_comms_in_s;

typedef struct
{
#ifdef DEPOSIT
    // nothing
#elif ISOLATE_CLASSIFY
    system_state_E curr_state;
    belts_state_E belts_curr_state;
#else
    // nothing
#endif
} core_comms_out_s;

typedef struct 
{
    // data for task
    struct pt        thread;
    // data for serial comms handling
    char             line[SERIAL_MESSAGE_SIZE];
    char*            args[CORE_COMMS_MAX_ARGS];
    char*            tokLine[(SERIAL_MESSAGE_SIZE + 1)];
    // data for holding processed messages
    core_comms_in_s  in_data;
    core_comms_out_s out_data;
    core_comms_cmd_s cmds[];
} core_comms_s;

/*******************************************************************************
*          P R I V A T E    F U N C T I O N    D E C L A R A T I O N S         *
*******************************************************************************/ 

static char run10ms(struct pt* thread);

static void core_comms_calib(uint8_t argNumber, char* args[]);

/*******************************************************************************
*                 S T A T I C    D A T A    D E F I N I T I O N S              *
*******************************************************************************/ 

static core_comms_s core_comms_data = 
{
    .in_data =
    {
#ifdef DEPOSIT
        // nothing
#elif ISOLATE_CLASSIFY
        .des_state = SYSTEM_STATE_IDLE,
        .corr_angle = 0.0,

        .belts_des_state = BELTS_STATE_IDLE,
        .top_belt_steps = 0,
        .bottom_belt_steps = 0,
#else
        // nothing
#endif
    },
    .out_data =
    {
#ifdef DEPOSIT
        // nothing
#elif ISOLATE_CLASSIFY
        .curr_state = SYSTEM_STATE_STARTUP,

        .belts_curr_state = BELTS_STATE_IDLE,
#else
        // nothing
#endif
    },
    .cmds = 
    {
#ifdef DEPOSIT
        BOXES_CORE_COMMS_COMMANDS,
#elif ISOLATE_CLASSIFY
        SYSTEM_STATE_CORE_COMMS_COMMANDS,
        PLANE_CORE_COMMS_COMMANDS,
        BELTS_CORE_COMMS_COMMANDS,
#else
        // nothing
#endif
        {core_comms_calib, "calib-serial", 0},
        {NULL, CORE_COMMS_CMD_LIST_TERMINATOR, 0}
    },
};

/*******************************************************************************
*                      P R I V A T E    F U N C T I O N S                      *
*******************************************************************************/ 

static void core_comms_calib(uint8_t argNumber, char* args[])
{
    // do nothing, just want to elicit response from firmware for SW calib
}

static void core_comms_parseLine(char* message)
{
    // Tokenize the line with spaces as the delimiter
    char* tok = (char*) strtok(message, " ");
    uint8_t i = 0;
    while (tok != NULL && i < (CORE_COMMS_MAX_ARGS + 1))
    {
        core_comms_data.tokLine[i] = tok;
        tok = strtok(NULL, " ");
        i++;
    }

    uint8_t j = 0;
    core_comms_cmd_s* cmds = core_comms_data.cmds;
    while (j < i)
    {
        uint8_t k = 0;
        while (strcmp(cmds[k].command, CORE_COMMS_CMD_LIST_TERMINATOR) != 0) 
        {
            if (strcmp(cmds[k].command, core_comms_data.tokLine[j]) == 0)
            {
                // Package the args into a char* array
                for (uint8_t e=0; e<cmds[k].params; e++)
                {
                    core_comms_data.args[e] = core_comms_data.tokLine[j+e+1];
                }

                // Call the function corresponding to the command with args
                core_comms_f func = cmds[k].func;
                func(cmds[k].params, core_comms_data.args);
                // Reset the args array
                memset(core_comms_data.args, '\0', sizeof(core_comms_data.args));
                j += cmds[k].params + 1;
                break;
            }
            k++;
        }
        if (strcmp(cmds[k].command, CORE_COMMS_CMD_LIST_TERMINATOR) == 0) {
            if (DEBUG_COMMS) {
                // send a debug msg to PC port in event of invalid msg
                char* resp = (char*) malloc(SERIAL_MESSAGE_SIZE + 50);
                sprintf(resp, "invalid command: %s", core_comms_data.tokLine[j]);
                serial_send_nl(PORT_COMPUTER, resp);
                free(resp);
                serial_send_nl(PORT_COMPUTER, message);
            }
            // break out so we don't infinite-loop in an invalid command
            break;
        }
    }

    // Reset the args and command arrays
    memset(core_comms_data.tokLine, '\0', sizeof(core_comms_data.tokLine));
}

static PT_THREAD(run10ms(struct pt* thread))
{
    PT_BEGIN(thread);
    PT_WAIT_UNTIL(thread, 
                  scheduler_taskReleased(PERIOD_10ms, (uint8_t) CORE_COMMS));
    // wait until there is serial data
    while (serial_available(PORT_RPI))
    {
        if (serial_handleByte(PORT_RPI, serial_readByte(PORT_RPI)))
        {
            serial_getLine(PORT_RPI, core_comms_data.line);
            core_comms_parseLine(core_comms_data.line);
            char* resp = (char*) malloc(SERIAL_MESSAGE_SIZE);
#ifdef DEPOSIT
            sprintf(resp,
                    "{\"boxes_state\": %d}\n",
                    boxes_getState());
#elif ISOLATE_CLASSIFY
            sprintf(resp,
                    "{\"system_state\": %d, \
                      \"belts_state\": %d,  \
                      \"depositor_state\": %d}\n",
                    system_state_getState(),
                    belts_getState(),
                    depositor_getState());
#else
            // nothing
#endif
            // send back the current state of the entire system
            serial_send(PORT_RPI, resp);
            free(resp);
            break;
        }
    }

    PT_END(thread);
}

/*******************************************************************************
*                       P U B L I C    F U N C T I O N S                       *
*******************************************************************************/ 

void core_comms_init(void)
{
    PT_INIT(&core_comms_data.thread);
    serial_init(PORT_RPI);
}

void core_comms_run10ms(void)
{
    run10ms(&core_comms_data.thread);
}
