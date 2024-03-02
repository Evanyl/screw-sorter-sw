
/*******************************************************************************
*                                I N C L U D E S                               *
*******************************************************************************/ 

#include "system_state.h"

#include "core_comms.h"
#include "lighting.h"
#include "depositor.h"
#include "arm.h"
#include "plane.h"

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
    system_state_E curr_state;
    system_state_E des_state;
} system_state_data_S;

/*******************************************************************************
*          P R I V A T E    F U N C T I O N    D E C L A R A T I O N S         *
*******************************************************************************/

static system_state_E system_state_update_state(system_state_E curr_state);
static system_state_E system_state_parseState(char* s);

/*******************************************************************************
*                 S T A T I C    D A T A    D E F I N I T I O N S              *
*******************************************************************************/ 

static system_state_data_S system_state_data = 
{
    .curr_state = SYSTEM_STATE_STARTUP,
};

/*******************************************************************************
*                      P R I V A T E    F U N C T I O N S                      *
*******************************************************************************/

static system_state_E system_state_parseState(char* s)
{
    system_state_E state = SYSTEM_STATE_COUNT;
    if (strcmp(s, "idle") == 0)
    {
        state = SYSTEM_STATE_IDLE;
    }
    else if (strcmp(s, "top-down") == 0)
    {
        state = SYSTEM_STATE_TOPDOWN;
    }
    else if (strcmp(s, "side-on") == 0)
    {
        state = SYSTEM_STATE_SIDEON;
    }
    else
    {
        // do nothing
    }

    return state;
}

static system_state_E system_state_update_state(system_state_E curr_state)
{
    system_state_E next_state = curr_state;
    // get the states of all subsystems
    depositor_state_E depositor = depositor_getState();
    lighting_state_E lighting = lighting_getState();
    arm_state_E arm = arm_getState();
    // plane_state_E plane = plane_getState();
    // get rpi desired state from core_comms
    system_state_E des_state = system_state_data.des_state;

    switch (system_state_data.curr_state)
    {
        case SYSTEM_STATE_STARTUP:
            if (depositor == DEPOSITOR_STATE_IDLE &&
                arm == ARM_STATE_IDLE             &&
                lighting == LIGHTING_STATE_IDLE)
            {
                next_state = SYSTEM_STATE_IDLE;
            }
            else
            {
                // do nothing, system still homing.
            }
            break;

        case SYSTEM_STATE_IDLE:
            if (des_state == SYSTEM_STATE_TOPDOWN)
            {
                next_state = SYSTEM_STATE_ENTERING_DEPOSITED;
            }
            else
            {
                // do nothing, no imaging requested
            }
            break;

        case SYSTEM_STATE_ENTERING_DEPOSITED:
            if (depositor == DEPOSITOR_STATE_ENTERING_IDLE)
            {
                next_state = SYSTEM_STATE_DEPOSITED;
            }   
            else
            {
                // do nothing, depositor executing deposit sequence.
            }
            break;

        case SYSTEM_STATE_DEPOSITED:
            if (depositor == DEPOSITOR_STATE_IDLE)
            {
                next_state = SYSTEM_STATE_ENTERING_TOPDOWN;
            }
            else
            {
                // do nothing, wait for depositor to get back to idle
            }
            break;

        case SYSTEM_STATE_ENTERING_TOPDOWN:
            if (lighting == LIGHTING_STATE_TOPDOWN &&
                arm == ARM_STATE_TOPDOWN)
            {
                next_state = SYSTEM_STATE_TOPDOWN;
            }
            else
            {
                // do nothing, plane orienting screw
            }
            break;

        case SYSTEM_STATE_TOPDOWN:
            if (des_state == SYSTEM_STATE_SIDEON)
            {
                next_state = SYSTEM_STATE_ENTERING_SIDEON;
            }
            else
            {
                // do nothing, waiting on prompt from rpi
            }
            break;

        case SYSTEM_STATE_ENTERING_SIDEON:
            if (arm == ARM_STATE_SIDEON           && 
                lighting == LIGHTING_STATE_SIDEON/*plane == PLANE_STATE_ACTIVE*/)
            {
                next_state = SYSTEM_STATE_SIDEON;
            }
            else
            {
                // do nothing, arm, lighting, and plane are entering sideon
            }
            break;

        case SYSTEM_STATE_SIDEON:
            if (des_state == SYSTEM_STATE_IDLE)
            {
                next_state = SYSTEM_STATE_ENTERING_IDLE;
            }
            else
            {
                // do nothing, wait on prompt from rpi
            }
            break;

        case SYSTEM_STATE_ENTERING_IDLE:
            if (depositor == DEPOSITOR_STATE_IDLE &&
                lighting == LIGHTING_STATE_IDLE   &&
                arm == ARM_STATE_IDLE             
                /*plane == PLANE_STATE_IDLE*/)
            {
                next_state = SYSTEM_STATE_IDLE;
            }
            else
            {
                // do nothing, still entering idle
            }
            break;

        case SYSTEM_STATE_COUNT:
            break;
    }

    return next_state;
}

static PT_THREAD(run100ms(struct pt* thread))
{
    PT_BEGIN(thread);
    PT_WAIT_UNTIL(thread, 
                  scheduler_taskReleased(PERIOD_100ms, 
                  (uint8_t) SYSTEM_STATE));
    system_state_data.curr_state = system_state_update_state(system_state_data.curr_state);
    PT_END(thread);
}

/*******************************************************************************
*                       P U B L I C    F U N C T I O N S                       *
*******************************************************************************/ 

void system_state_init(void)
{
    PT_INIT(&system_state_data.thread);
}

void system_state_run100ms(void)
{
    run100ms(&system_state_data.thread);
}

system_state_E system_state_getState(void)
{
    return system_state_data.curr_state;
}

void system_state_setTarget(system_state_E target)
{
    // also need to set the desired angle of the plane, perhaps maintain a
    // struct in core comms that holds this updated mem, and write getters to
    // bring data into state machine modules.
    system_state_data.des_state = target;
}


void system_state_cli_target(uint8_t argNumber, char* args[])
{
    system_state_data.des_state = system_state_parseState(args[0]);
}

void system_state_core_comms_setDesState(uint8_t argNumber, char* args[])
{
    system_state_data.des_state = system_state_parseState(args[0]);
}
