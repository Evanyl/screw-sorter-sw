
/*******************************************************************************
*                                I N C L U D E S                               *
*******************************************************************************/ 

#include "boxes.h"
#include "scheduler.h"

#include "dev/stepper.h"
#include "dev/switch.h"

/*******************************************************************************
*                               C O N S T A N T S                              *
*******************************************************************************/ 

#define BOXES_NAV_RATE 1500
#define BOXES_STARTING_RATE 200

#define BOXES_HOMING_RATE 250
#define BOXES_HOME_DIR 1

#define BOXES_STEPS_PER_BOX 325

/*******************************************************************************
*                      D A T A    D E C L A R A T I O N S                      *
*******************************************************************************/ 

typedef struct
{
    struct pt thread;
    boxes_state_E state;
    boxes_state_E des_state;
    uint8_t curr_box;
    uint8_t des_box;
} boxes_data_S;

/*******************************************************************************
*          P R I V A T E    F U N C T I O N    D E C L A R A T I O N S         *
*******************************************************************************/

static boxes_state_E boxes_update_state(boxes_state_E curr_state);
static boxes_state_E boxes_parseState(char* s);
static bool boxes_atHome(void);

/*******************************************************************************
*                 S T A T I C    D A T A    D E F I N I T I O N S              *
*******************************************************************************/ 

static boxes_data_S boxes_data = 
{
    .state = BOXES_STATE_STARTUP,
    .des_state = BOXES_STATE_IDLE,
    .curr_box = 0,
    .des_box = 0,
};

/*******************************************************************************
*                      P R I V A T E    F U N C T I O N S                      *
*******************************************************************************/

static bool boxes_atHome(void)
{
    return switch_state(SWITCH_BOXES);
}

static boxes_state_E boxes_parseState(char* s)
{
    boxes_state_E state = BOXES_STATE_COUNT;
    if (strcmp(s, "startup") == 0)
    {
        state = BOXES_STATE_STARTUP;
    }
    else if (strcmp(s, "idle") == 0)
    {
        state = BOXES_STATE_IDLE;
    }
    else if (strcmp(s, "active") == 0)
    {
        state = BOXES_STATE_ACTIVE;
    }
    else
    {
        // do nothing
    }
    return state;
}

static boxes_state_E boxes_update_state(boxes_state_E curr_state)
{
    boxes_state_E next_state = curr_state;

    uint8_t dir = 0;
    int8_t delta = boxes_data.des_box - boxes_data.curr_box;
    uint16_t steps = abs(delta) * BOXES_STEPS_PER_BOX;

    switch (curr_state)
    {
        case BOXES_STATE_STARTUP:
            if (stepper_commandUntil(STEPPER_BOXES, 
                                     boxes_atHome, 
                                     BOXES_HOME_DIR, 
                                     BOXES_HOMING_RATE) == false)
            {
                // do nothing, homing
            }
            else
            {
                stepper_calibSteps(STEPPER_BOXES);
                next_state = BOXES_STATE_IDLE;
            }
            break;
        case BOXES_STATE_IDLE:
            if (boxes_data.des_state == BOXES_STATE_ACTIVE)
            {
                // only go to active once per write from SW to des_state
                next_state = BOXES_STATE_ACTIVE;
            }
            else
            {
                // do nothing, waiting for new belt command
            }
            break;
        case BOXES_STATE_ACTIVE:
            if (delta > 0)
            {
                dir = 1;
            }
            else
            {
                dir = 0;
            }

            if (stepper_command(STEPPER_BOXES,  
                                steps, 
                                dir, 
                                1500, 
                                steps*0.1, 
                                BOXES_STARTING_RATE) == false)
            {
                // do nothing, belts are moving
            }
            else
            {
                // check that RPi side has returned to "idle" before acting on
                //     another command to move boxes
                if (boxes_data.des_state == BOXES_STATE_IDLE)
                {
                    // reset step counting of both boxes
                    stepper_calibSteps(STEPPER_BOXES);
                    boxes_data.curr_box = boxes_data.des_box;
                    next_state = BOXES_STATE_IDLE;
                }
            }
            break;
        case BOXES_STATE_COUNT:
            break;
    }

    return next_state;
}

static PT_THREAD(run10ms(struct pt* thread))
{
    PT_BEGIN(thread);
    PT_WAIT_UNTIL(thread, 
                  scheduler_taskReleased(PERIOD_10ms, (uint8_t) BOXES));
    boxes_data.state = boxes_update_state(boxes_data.state);
    PT_END(thread);
}


/*******************************************************************************
*                       P U B L I C    F U N C T I O N S                       *
*******************************************************************************/ 

void boxes_init(void)
{
    PT_INIT(&boxes_data.thread);

    stepper_init(STEPPER_BOXES);
    switch_init(SWITCH_BOXES);
}

void boxes_run10ms(void)
{
    run10ms(&boxes_data.thread);
}

boxes_state_E boxes_getState(void)
{
    return boxes_data.state;
}

void boxes_cli_setDesState(uint8_t argNumber, char* args[])
{
    boxes_data.des_state = boxes_parseState(args[0]);
}

void boxes_cli_setBox(uint8_t argNumber, char* args[])
{
    boxes_data.des_box = atoi(args[0]);
}

void boxes_cli_home(uint8_t argNumber, char* args[])
{
    stepper_commandUntil(STEPPER_BOXES, 
                         boxes_atHome, 
                         BOXES_HOME_DIR, 
                         BOXES_HOMING_RATE);
}

void boxes_core_comms_setDesState(uint8_t argNumber, char* args[])
{
    boxes_data.des_state = boxes_parseState(args[0]);
}

void boxes_core_comms_setBox(uint8_t argNumber, char* args[])
{
    boxes_data.des_box = atoi(args[0]);
}


