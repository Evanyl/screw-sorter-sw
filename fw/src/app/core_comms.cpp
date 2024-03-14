/*******************************************************************************
*                                I N C L U D E S                               *
*******************************************************************************/ 

#include "core_comms.h"
#include "plane.h"
#include "belts.h"
#include "depositor.h"
#include "classify_system_state.h"
#include <chrono>

// from https://github.com/arduino/Arduino/issues/9413, but didn't solve my issue
extern "C" {
  // This must exist to keep the linker happy but is never called.
  int _gettimeofday( struct timeval *tv, void *tzvp )
  {
    Serial.println("_gettimeofday dummy");
    uint64_t t = 0;  // get uptime in nanoseconds
    tv->tv_sec = t / 1000000000;  // convert to seconds
    tv->tv_usec = ( t % 1000000000 ) / 1000;  // get remaining microseconds
    return 0;  // return non-zero for error
  } // end _gettimeofday()
}

/*******************************************************************************
*                               C O N S T A N T S                              *
*******************************************************************************/ 

#define CORE_COMMS_CMD_LIST_TERMINATOR "END OF LIST"
#define CORE_COMMS_MAX_ARGS 25

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
    classify_system_state_E classify_des_state;
    float corr_angle;
    uint16_t belt_top_steps;
    uint16_t belt_bottom_steps;
} core_comms_in_s;

typedef struct
{
    classify_system_state_E classify_curr_state;
    belts_state_E belts_curr_state;
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

/*******************************************************************************
*                 S T A T I C    D A T A    D E F I N I T I O N S              *
*******************************************************************************/ 

static core_comms_s core_comms_data = 
{
    .in_data =
    {
        .classify_des_state = CLASSIFY_SYSTEM_STATE_IDLE,
        .corr_angle = 0.0,
        .belt_top_steps = 0,
        .belt_bottom_steps = 0,
    },
    .out_data =
    {
        .classify_curr_state = CLASSIFY_SYSTEM_STATE_STARTUP,
        .belts_curr_state = BELTS_STATE_IDLE,
    },
    .cmds = 
    {
        CLASSIFY_SYSTEM_STATE_CORE_COMMS_COMMANDS,
        PLANE_CORE_COMMS_COMMANDS,
        BELTS_CORE_COMMS_COMMANDS,
        {NULL, CORE_COMMS_CMD_LIST_TERMINATOR, 0}
    },
};

static std::chrono::steady_clock::time_point last_time;
static long long dt = 0;
/*******************************************************************************
*                      P R I V A T E    F U N C T I O N S                      *
*******************************************************************************/ 

static void core_comms_parseLine(char* message)
{
    // Tokenize the line with spaces as the delimiter
    char* tok = (char*) strtok(message, " ");
    uint8_t i = 0;
    while (tok != NULL && i < (CORE_COMMS_MAX_ARGS + 1))
    {
        // Serial1.print("Loop 1");
        core_comms_data.tokLine[i] = tok;
        tok = strtok(NULL, " ");
        i++;
    }

    uint8_t j = 0;
    core_comms_cmd_s* cmds = core_comms_data.cmds;
    while (j < i)
    {
        // Serial1.print("Loop 2\n");
        uint8_t k = 0;
        while (strcmp(cmds[k].command, CORE_COMMS_CMD_LIST_TERMINATOR) != 0) 
        {
            // Serial1.print("Loop 3\n");
            // Serial1.printf("%d, %d, %d, %s, %s\n", i,j,k, core_comms_data.tokLine[j], cmds[k].command);
            if (strcmp(cmds[k].command, core_comms_data.tokLine[j]) == 0)
            {
                // Package the args into a char* array
                for (uint8_t e=0; e<cmds[k].params; e++)
                {
                    core_comms_data.args[e] = core_comms_data.tokLine[j+e+1];
                }
                // Serial1.printf("Done for-loop\n");

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
            // not sending to PORT_RPI so we don't screw up sw side loop
            char* resp = (char*) malloc(SERIAL_MESSAGE_SIZE + 50);
            sprintf(resp, "invalid command: %s", core_comms_data.tokLine[j]);
            serial_send_nl(PORT_COMPUTER, resp);
            free(resp);
            serial_send_nl(PORT_COMPUTER, message);
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
        // Serial1.print("loop avail\n");
        if (serial_handleByte(PORT_RPI, serial_readByte(PORT_RPI)))
        {
            std::chrono::steady_clock::time_point curr;
            curr = std::chrono::steady_clock::now();
            dt = std::chrono::duration_cast<std::chrono::nanoseconds>(last_time - curr).count();
            char* time_out = (char*) malloc(SERIAL_MESSAGE_SIZE + 50);
            sprintf(time_out, "%lld ns", dt);
            Serial1.println(time_out);
            free(time_out);
            last_time = curr;
            serial_getLine(PORT_RPI, core_comms_data.line);
            Serial1.println(core_comms_data.line);
            core_comms_parseLine(core_comms_data.line);
            char* resp = (char*) malloc(SERIAL_MESSAGE_SIZE);
            sprintf(resp, "{\"classify_system_state\": %d,\"belts_state\": %d,\"depositor_state\": %d}\n",
                            classify_system_state_getState(),
                            belts_getState(),
                            depositor_getState());
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
    last_time = std::chrono::steady_clock::now();
}

void core_comms_run10ms(void)
{
    run10ms(&core_comms_data.thread);
}
