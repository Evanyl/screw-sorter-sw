
/*******************************************************************************
*                                I N C L U D E S                               *
*******************************************************************************/ 

#include "belts.h"
#include "scheduler.h"

/*******************************************************************************
*                               C O N S T A N T S                              *
*******************************************************************************/ 

#define BELTS_NAV_RATE 1500
#define BELTS_STARTING_RATE 200

/*******************************************************************************
*                      D A T A    D E C L A R A T I O N S                      *
*******************************************************************************/ 

typedef struct
{
    struct pt thread;
    belts_state_E state;
    belts_state_E des_state;
    uint16_t top_belt_steps;
    uint8_t top_belt_dir;
    uint16_t bottom_belt_steps;
    uint8_t bottom_belt_dir;
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
    .top_belt_dir = 1,
    .bottom_belt_steps = 0,
    .bottom_belt_dir = 1,

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
    bool top = false;
    bool bottom = false;

    switch (curr_state)
    {
        case BELTS_STATE_IDLE:
            if (belts_data.des_state == BELTS_STATE_ACTIVE)
            {
                // only go to active once per write from SW to des_state
                next_state = BELTS_STATE_ACTIVE;
            }
            else
            {
                // do nothing, waiting for new belt command
            }
            break;
        case BELTS_STATE_ACTIVE:
            top = stepper_command(STEPPER_BELT_TOP,  
                                belts_data.top_belt_steps, 
                                belts_data.top_belt_dir, 
                                1500, 
                                belts_data.top_belt_steps*0.05, 
                                100);
            bottom = stepper_command(STEPPER_BELT_BOTTOM,  
                                belts_data.bottom_belt_steps, 
                                belts_data.bottom_belt_dir, 
                                1500, 
                                belts_data.bottom_belt_steps*0.05, 
                                100);
            if (top == false || bottom == false)
            {
                // do nothing, belts are moving
            }
            else
            {
                // check that RPi side has returned to "idle" before acting on
                //     another command to move belts
                if (belts_data.des_state == BELTS_STATE_IDLE)
                {
                    // reset step counting of both belts
                    stepper_calibSteps(STEPPER_BELT_TOP);
                    stepper_calibSteps(STEPPER_BELT_BOTTOM);
                    next_state = BELTS_STATE_IDLE;
                }
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

void belts_cli_setDesState(uint8_t argNumber, char* args[])
{
    belts_data.des_state = belts_parseState(args[0]);
}

void belts_cli_setSteps(uint8_t argNumber, char* args[])
{
    belts_data.top_belt_steps = atoi(args[0]);
    belts_data.bottom_belt_steps = atoi(args[1]);
}

void belts_core_comms_setDesState(uint8_t argNumber, char* args[])
{
    belts_data.des_state = belts_parseState(args[0]);
}

void belts_core_comms_setSteps(uint8_t argNumber, char* args[])
{
    belts_data.top_belt_steps = abs(atoi(args[0]));
    belts_data.bottom_belt_steps = abs(atoi(args[1]));
    belts_data.top_belt_dir = 1;
    belts_data.bottom_belt_dir = 1;
    if (atoi(args[0]) < 0)
    {
        belts_data.top_belt_dir = 0;
    }
    if (atoi(args[1]) < 0)
    {
        belts_data.bottom_belt_dir = 0;   
    }
}
