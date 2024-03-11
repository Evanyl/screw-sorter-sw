
/*******************************************************************************
*                                I N C L U D E S                               *
*******************************************************************************/ 

#include "isolation_system_state.h"

#include "core_comms.h"
#include "belts.h"

#include "dev/serial.h"

/*******************************************************************************
*                               C O N S T A N T S                              *
*******************************************************************************/ 

/*******************************************************************************
*                      D A T A    D E C L A R A T I O N S                      *
*******************************************************************************/ 

typedef struct
{
    struct pt thread;
    isolation_system_state_E curr_state;
    isolation_system_state_E des_state;
} isolation_system_state_data_S;

/*******************************************************************************
*          P R I V A T E    F U N C T I O N    D E C L A R A T I O N S         *
*******************************************************************************/

static isolation_system_state_E isolation_system_state_update_state(isolation_system_state_E curr_state);
static isolation_system_state_E isolation_system_state_parseState(char* s);

/*******************************************************************************
*                 S T A T I C    D A T A    D E F I N I T I O N S              *
*******************************************************************************/ 

static isolation_system_state_data_S isolation_system_state_data = 
{
    .curr_state = ISOLATION_SYSTEM_STATE_STARTUP,
};

/*******************************************************************************
*                      P R I V A T E    F U N C T I O N S                      *
*******************************************************************************/

static isolation_system_state_E isolation_system_state_parseState(char* s)
{
    isolation_system_state_E state = ISOLATION_SYSTEM_STATE_COUNT;
    if (strcmp(s, "idle") == 0)
    {
        state = ISOLATION_SYSTEM_STATE_IDLE;
    }
    else if (strcmp(s, "attempt-isolate") == 0)
    {
        state = ISOLATION_SYSTEM_STATE_ATTEMPT_ISOLATED;
    }
    else if (strcmp(s, "confirm-isolate") == 0)
    {
        state = ISOLATION_SYSTEM_STATE_ISOLATED;
    }
    else if (strcmp(s, "deliver") == 0)
    {
        state = ISOLATION_SYSTEM_STATE_DELIVERED;
    }
    else
    {
        // do nothing
    }
    return state;
}

static isolation_system_state_E isolation_system_state_update_state(isolation_system_state_E curr_state)
{
    isolation_system_state_E next_state = curr_state;
    // get the states of all subsystems
    belts_state_E belts = belts_getState();
    // get rpi desired state from core_comms
    isolation_system_state_E des_state = isolation_system_state_data.des_state;

    switch (isolation_system_state_data.curr_state)
    {
        case ISOLATION_SYSTEM_STATE_STARTUP:
            if (belts == BELTS_STATE_IDLE)
            {
                next_state = ISOLATION_SYSTEM_STATE_IDLE;
            }
            else
            {
                // do nothing, system still homing. with just belts this is instant.
            }
            break;

        case ISOLATION_SYSTEM_STATE_IDLE:
            if (des_state == ISOLATION_SYSTEM_STATE_ATTEMPT_ISOLATED
                ||
                des_state == ISOLATION_SYSTEM_STATE_ISOLATED)
            {
                next_state = des_state;
            }
            else if (des_state == ISOLATION_SYSTEM_STATE_REJECT)
            {
                next_state = ISOLATION_SYSTEM_STATE_ENTERING_REJECT;
            }
            else
            {
                // do nothing, no isolation requested
            }
            break;

        case ISOLATION_SYSTEM_STATE_ATTEMPT_ISOLATED:
            if (belts == BELTS_STATE_ACTIVE)
            {
                // belts have completed movement, return to idle
                next_state = ISOLATION_SYSTEM_STATE_ENTERING_IDLE;
                isolation_system_state_data.des_state = ISOLATION_SYSTEM_STATE_IDLE;  // change des_state to prevent inf loop
            }   
            else
            {
                // do nothing, belts are still moving
            }
            break;
        
        case ISOLATION_SYSTEM_STATE_ISOLATED:
            if (des_state == ISOLATION_SYSTEM_STATE_DELIVERED)
            {
                next_state = ISOLATION_SYSTEM_STATE_ENTERING_DELIVERED;
            }   
            else
            {
                // do nothing, imaging/depositor is not ready for fastener
            }
            break;

        case ISOLATION_SYSTEM_STATE_ENTERING_DELIVERED:
            if (belts == BELTS_STATE_ACTIVE)
            {
                next_state = ISOLATION_SYSTEM_STATE_DELIVERED;
            }   
            else
            {
                // do nothing, still attempting to deliver fasteners to depositor
            }
            break;

        case ISOLATION_SYSTEM_STATE_DELIVERED:
                next_state = ISOLATION_SYSTEM_STATE_ENTERING_IDLE;
            break;

        case ISOLATION_SYSTEM_STATE_ENTERING_REJECT:
            if (belts == BELTS_STATE_ACTIVE)
            {
                next_state = ISOLATION_SYSTEM_STATE_REJECT;
            }
            break;

        case ISOLATION_SYSTEM_STATE_REJECT:
                next_state = ISOLATION_SYSTEM_STATE_ENTERING_IDLE;
            break;
            
        case ISOLATION_SYSTEM_STATE_ENTERING_IDLE:
            if (belts == BELTS_STATE_IDLE)
            {
                next_state = ISOLATION_SYSTEM_STATE_IDLE;
            }
            else
            {
                // do nothing, still entering idle
            }
            break;

        case ISOLATION_SYSTEM_STATE_COUNT:
            break;
    }

    return next_state;
}

static PT_THREAD(run100ms(struct pt* thread))
{
    PT_BEGIN(thread);
    PT_WAIT_UNTIL(thread, 
                  scheduler_taskReleased(PERIOD_100ms, 
                  (uint8_t) ISOLATION_SYSTEM_STATE));
    isolation_system_state_data.curr_state = 
        isolation_system_state_update_state(isolation_system_state_data.curr_state);
    PT_END(thread);
}

/*******************************************************************************
*                       P U B L I C    F U N C T I O N S                       *
*******************************************************************************/ 

void isolation_system_state_init(void)
{
    PT_INIT(&isolation_system_state_data.thread);
}

void isolation_system_state_run100ms(void)
{
    run100ms(&isolation_system_state_data.thread);
}

isolation_system_state_E isolation_system_state_getState(void)
{
    return isolation_system_state_data.curr_state;
}

void isolation_system_state_setTarget(isolation_system_state_E target)
{
    isolation_system_state_data.des_state = target;
}


void isolation_system_state_cli_target(uint8_t argNumber, char* args[])
{
    isolation_system_state_data.des_state = isolation_system_state_parseState(args[0]);
}

void isolation_system_state_cli_dump(uint8_t argNumber, char* args[])
{
    char* st = (char*) malloc(SERIAL_MESSAGE_SIZE);
    sprintf(st, 
            "{\"des_state\": %d, \"curr_state\": %d}", 
            (uint8_t) isolation_system_state_data.des_state,
            (uint8_t) isolation_system_state_data.curr_state);
    serial_send_nl(PORT_COMPUTER, st);
    free(st);
}

void isolation_system_state_core_comms_setDesState(uint8_t argNumber, char* args[])
{
    isolation_system_state_data.des_state = isolation_system_state_parseState(args[0]);
}
