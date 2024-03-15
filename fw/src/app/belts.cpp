
/*******************************************************************************
*                                I N C L U D E S                               *
*******************************************************************************/ 

#include "belts.h"
#include "scheduler.h"

/*******************************************************************************
*                               C O N S T A N T S                              *
*******************************************************************************/ 

#define BELTS_NAV_RATE 750
#define BELTS_STARTING_RATE 100

/*******************************************************************************
*                      D A T A    D E C L A R A T I O N S                      *
*******************************************************************************/ 

typedef struct
{
    struct pt thread;
    belts_state_E state;
    belts_state_E des_state;
    uint16_t top_belt_steps;
    uint16_t bottom_belt_steps;
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
    .des_state = BELTS_STATE_IDLE,
    .top_belt_steps = 0,
    .bottom_belt_steps = 0,

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
    else if (strcmp(s, "active") == 0)
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

    switch (curr_state)
    {
        case BELTS_STATE_IDLE:
            if (belts_data.des_state == BELTS_STATE_ACTIVE)
            {
                next_state = BELTS_STATE_ACTIVE;
            }
            else
            {
                // do nothing, not commanding belts
            }
            break;
        case BELTS_STATE_ACTIVE:
            if (stepper_command(STEPPER_BELT_TOP, 
                                belts_data.top_belt_steps, 
                                1, 
                                750, 
                                belts_data.bottom_belt_steps*0.1, 
                                100) == false ||
                stepper_command(STEPPER_BELT_TOP,  
                                belts_data.bottom_belt_steps, 
                                1, 
                                750, 
                                belts_data.bottom_belt_steps*0.1, 
                                100) == false)
            {
                // do nothing, belts are moving
            }
            else
            {
                // reset step counting of both belts
                stepper_calibSteps(STEPPER_BELT_TOP);
                stepper_calibSteps(STEPPER_BELT_BOTTOM);
                next_state = BELTS_STATE_IDLE;
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

void belts_core_comms_setDesState(uint8_t argNumber, char* args[])
{
    belts_data.des_state = belts_parseState(args[0]);
}

void belts_core_comms_setSteps(uint8_t argNumber, char* args[])
{
    belts_data.top_belt_steps = atoi(args[0]);
    belts_data.bottom_belt_steps = atoi(args[1]);
}
