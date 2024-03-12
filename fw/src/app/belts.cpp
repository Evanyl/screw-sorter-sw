
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
    belts_state_E des_state;
    uint16_t belt_top_steps;
    uint8_t belt_top_dir;
    uint16_t belt_top_rate;
    uint16_t belt_top_ramp_rate;
    uint8_t belt_top_ramp_window;
    uint16_t belt_bottom_steps;
    uint8_t belt_bottom_dir;
    uint16_t belt_bottom_rate;
    uint16_t belt_bottom_ramp_rate;
    uint8_t belt_bottom_ramp_window;
} belts_data_S;

/*******************************************************************************
*          P R I V A T E    F U N C T I O N    D E C L A R A T I O N S         *
*******************************************************************************/

static belts_state_E belts_update_state(belts_state_E curr_state);
static belts_state_E belts_parseState(char* s);

/*******************************************************************************
*                 S T A T I C    D A T A    D E F I N I T I O N S              *
*******************************************************************************/ 

static belts_data_S belts_data = 
{
    .curr_state = BELTS_STATE_IDLE,
    .des_state = BELTS_STATE_IDLE,
    .belt_top_steps = 0,
    .belt_top_dir = BELT_TOP_FORWARD,
    .belt_top_rate = BELTS_NAV_RATE,
    .belt_top_ramp_rate = BELTS_STARTING_RATE,
    .belt_top_ramp_window = BELTS_RAMP_WINDOW,
    .belt_bottom_steps = 0,
    .belt_bottom_dir = BELT_BOTTOM_FORWARD,
    .belt_bottom_rate = BELTS_NAV_RATE,
    .belt_bottom_ramp_rate = BELTS_STARTING_RATE,
    .belt_bottom_ramp_window = BELTS_RAMP_WINDOW
};

/*******************************************************************************
*                      P R I V A T E    F U N C T I O N S                      *
*******************************************************************************/
static belts_state_E belts_parseState(char* s)
{
    belts_state_E state = BELTS_STATE_COUNT;
    if (strcmp(s, "idle") == 0)
    {
        state = BELTS_STATE_IDLE;
    }
    else if (strcmp(s, "move") == 0)
    {
        state = BELTS_STATE_ACTIVE;
    }
    else
    {
        // do nothing
    }
    return state;
}


static belts_state_E belts_update_state(belts_state_E curr_state)
{
    belts_state_E next_state = curr_state;
    belts_state_E des_state = belts_data.des_state;
    switch (curr_state)
    {
        case BELTS_STATE_IDLE:
            if (des_state == BELTS_STATE_ACTIVE)
            {
                next_state = BELTS_STATE_ACTIVE;
            }
            else
            {
                // do nothing, stay in idle state
            }
            break;
        case BELTS_STATE_ACTIVE:
        {
            // Use temp variables to prevent if-statement short-circuit evaluation
            bool first_stepper = stepper_command(STEPPER_BELT_TOP,
                                belts_data.belt_top_steps,
                                belts_data.belt_top_dir,
                                belts_data.belt_top_rate,
                                belts_data.belt_top_ramp_rate,
                                belts_data.belt_top_ramp_window);
            bool second_stepper = stepper_command(STEPPER_BELT_BOTTOM,
                                belts_data.belt_bottom_steps,
                                belts_data.belt_bottom_dir,
                                belts_data.belt_bottom_rate,
                                belts_data.belt_bottom_ramp_rate,
                                belts_data.belt_bottom_ramp_window);
            if (first_stepper == false || second_stepper == false)
            {
                // do nothing, one or both of the belts are moving
            }
            else
            {
                next_state = BELTS_STATE_IDLE;
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
    belts_data.des_state = BELTS_STATE_ACTIVE;
    belts_data.belt_top_steps = atoi(args[0]);
    belts_data.belt_top_dir = atoi(args[1]);
    belts_data.belt_top_rate = atoi(args[2]);
    belts_data.belt_top_ramp_rate = atoi(args[3]);
    belts_data.belt_top_ramp_window = atoi(args[4]);

    belts_data.belt_bottom_steps = atoi(args[5]);
    belts_data.belt_bottom_dir = atoi(args[6]);
    belts_data.belt_bottom_rate = atoi(args[7]);
    belts_data.belt_bottom_ramp_rate = atoi(args[8]);
    belts_data.belt_bottom_ramp_window = atoi(args[9]);
}

void belts_cli_dump_state(uint8_t argNumber, char* args[])
{
    char* st = (char*) malloc(SERIAL_MESSAGE_SIZE);
    sprintf(st, 
            "{\"des_state\": %d, \"curr_state\": %d}", 
            (uint8_t) belts_data.des_state,
            (uint8_t) belts_data.curr_state);
    serial_send_nl(PORT_COMPUTER, st);
    free(st);
}