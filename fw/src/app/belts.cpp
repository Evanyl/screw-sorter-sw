
/*******************************************************************************
*                                I N C L U D E S                               *
*******************************************************************************/ 

#include "belts.h"
#include "isolation_system_state.h"
#include "scheduler.h"
#include "dev/serial.h"

/*******************************************************************************
*                               C O N S T A N T S                              *
*******************************************************************************/ 

#define BELTS_NAV_RATE 750
#define BELTS_STARTING_RATE 50
#define BELTS_RAMP_WINDOW 250

#define BELT_TOP_FORWARD 1
#define BELT_TOP_BACKWARD 0
#define BELT_BOTTOM_FORWARD 1
#define BELT_BOTTOM_BACKWARD 0

/*******************************************************************************
*                      D A T A    D E C L A R A T I O N S                      *
*******************************************************************************/ 

typedef struct
{
    // some tracking of height after homing
    struct pt thread;
    belts_state_E state;
    float belt_top_steps;
    float belt_bottom_steps;
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
    .state = BELTS_STATE_IDLE,
    .belt_top_steps = 950,
    .belt_bottom_steps = 750
};

/*******************************************************************************
*                      P R I V A T E    F U N C T I O N S                      *
*******************************************************************************/

static belts_state_E belts_update_state(belts_state_E curr_state)
{
    belts_state_E next_state = curr_state;
    isolation_system_state_E isolation_system_state = isolation_system_state_getState();
    switch (curr_state)
    {
        case BELTS_STATE_IDLE:
            if (isolation_system_state == ISOLATION_SYSTEM_STATE_ATTEMPT_ISOLATED
                ||
                isolation_system_state == ISOLATION_SYSTEM_STATE_ENTERING_DELIVERED)
            {
                next_state = BELTS_STATE_ENTERING_ACTIVE;
            }
            else
            {
                // do nothing, stay in idle state
            }
            break;
        case BELTS_STATE_ENTERING_ACTIVE:
        {
            // Use temp variables to prevent if-statement short-circuit evaluation
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
            if (first_stepper == false || second_stepper == false)
            {
                // do nothing, one or both of the belts are moving
            }
            else
            {
                next_state = BELTS_STATE_ACTIVE;
            }
            break;
        }
        case BELTS_STATE_ACTIVE:
            if (isolation_system_state == ISOLATION_SYSTEM_STATE_ENTERING_IDLE)
            {
                next_state = BELTS_STATE_IDLE;
            }
            else
            {
                // do nothing, 
            }
            break;
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
    belts_data.state = belts_update_state(belts_data.state);
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
    return belts_data.state;
}

void belts_core_comms_setDistance(uint8_t argNumber, char* args[])
{
    belts_data.belt_top_steps = atof(args[0]);
    belts_data.belt_bottom_steps = atof(args[1]);
}

void belts_cli_dump_state(uint8_t argNumber, char* args[])
{
    char* st = (char*) malloc(SERIAL_MESSAGE_SIZE);
    sprintf(st, 
            "{\"curr_state\": %d}", 
            (uint8_t) belts_data.state);
    serial_send_nl(PORT_COMPUTER, st);
    free(st);
}