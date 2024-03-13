
/*******************************************************************************
*                                I N C L U D E S                               *
*******************************************************************************/ 

#include "belts.h"
#include "scheduler.h"
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
    belts_state_E curr_state;
    bool belt_top_in_motion;
    bool belt_bottom_in_motion;
    uint16_t belt_top_steps;
    uint16_t belt_bottom_steps;
} belts_data_S;

/*******************************************************************************
*          P R I V A T E    F U N C T I O N    D E C L A R A T I O N S         *
*******************************************************************************/

static belts_state_E belts_update_state(belts_state_E curr_state);

/*******************************************************************************
*                 S T A T I C    D A T A    D E F I N I T I O N S              *
*******************************************************************************/ 

static belts_data_S belts_data = 
{
    .curr_state = BELTS_STATE_IDLE,
    .belt_top_in_motion = false,
    .belt_bottom_in_motion = false,
    .belt_top_steps = 0,
    .belt_bottom_steps = 0
};

/*******************************************************************************
*                      P R I V A T E    F U N C T I O N S                      *
*******************************************************************************/


static belts_state_E belts_update_state(belts_state_E curr_state)
{
    belts_state_E next_state = curr_state;
    switch (curr_state)
    {
        case BELTS_STATE_IDLE:
            if (belts_data.belt_top_steps < 0 || belts_data.belt_bottom_steps < 0)
            {
                next_state = BELTS_STATE_ACTIVE;
                belts_data.belt_top_in_motion = true;
                belts_data.belt_bottom_in_motion = true;
            }
            else
            {
                // do nothing, stay in idle state
            }
            break;
        case BELTS_STATE_ACTIVE:
        {
            // Use temp variables to prevent if-statement short-circuit evaluation
            // stepper_command emits a "true" once.
            bool first_stepper = stepper_command(STEPPER_BELT_TOP,
                                belts_data.belt_top_steps,
                                BELT_TOP_FORWARD,
                                BELTS_NAV_RATE,
                                BELTS_STARTING_RATE,
                                BELTS_RAMP_WINDOW);
            bool second_stepper = stepper_command(STEPPER_BELT_BOTTOM,
                                belts_data.belt_bottom_steps,
                                BELT_BOTTOM_FORWARD,
                                BELTS_NAV_RATE,
                                BELTS_STARTING_RATE,
                                BELTS_RAMP_WINDOW);
            if (first_stepper == true) {
                // reset the step values
                belts_data.belt_top_steps = 0;
                belts_data.belt_top_in_motion = false;
            }
            if (second_stepper == true) {
                belts_data.belt_bottom_steps = 0;
                belts_data.belt_bottom_in_motion = false;
            }

            if (belts_data.belt_top_in_motion == true 
                || 
                belts_data.belt_bottom_in_motion == true)
            {
                // do nothing, one or both of the belts are moving
            }
            else
            {
                next_state = BELTS_STATE_IDLE;
                belts_data.belt_top_steps = 0;
                belts_data.belt_bottom_steps = 0;
            }
            break;
        }
        case BELTS_STATE_COUNT:
            break;
    }

    return next_state;
}

static PT_THREAD(run10ms(struct pt* thread))
{
    PT_BEGIN(thread);
    PT_WAIT_UNTIL(thread, 
                  scheduler_taskReleased(PERIOD_10ms, (uint8_t) BELTS));
    belts_data.curr_state = belts_update_state(belts_data.curr_state);
    PT_END(thread);
}


/*******************************************************************************
*                       P U B L I C    F U N C T I O N S                       *
*******************************************************************************/ 

void belts_init(void)
{
    PT_INIT(&belts_data.thread);

    stepper_init(STEPPER_BELT_TOP);
    stepper_init(STEPPER_BELT_BOTTOM);
}

void belts_run10ms(void)
{
    run10ms(&belts_data.thread);
}

belts_state_E belts_getState(void)
{
    return belts_data.curr_state;
}

void belts_core_comms_setDesState(uint8_t argNumber, char* args[])
{
    belts_data.belt_top_steps = atoi(args[0]);
    belts_data.belt_bottom_steps = atoi(args[1]);
}

void belts_core_comms_nop(uint8_t argNumber, char* args[])
{
    return;
}

void belts_cli_stop(uint8_t argNumber, char* args[])
{
    belts_data.curr_state = BELTS_STATE_IDLE;
    belts_data.belt_top_steps = 0;
    belts_data.belt_bottom_steps = 0;
}

void belts_cli_target(uint8_t argNumber, char* args[])
{
    belts_data.belt_top_steps = atoi(args[0]);
    belts_data.belt_bottom_steps = atoi(args[1]);
}

void belts_cli_dump_state(uint8_t argNumber, char* args[])
{
    char* st = (char*) malloc(SERIAL_MESSAGE_SIZE);
    sprintf(st, 
            "{\"curr_state\": %d,\"belt_top_steps\": %d,\"belt_bottom_steps\": %d}", 
            (uint8_t) belts_data.curr_state,
            (uint16_t) belts_data.belt_top_steps,
            (uint16_t) belts_data.belt_bottom_steps);
    serial_send_nl(PORT_COMPUTER, st);
    free(st);
}