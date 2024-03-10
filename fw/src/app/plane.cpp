
/*******************************************************************************
*                                I N C L U D E S                               *
*******************************************************************************/ 

#include "plane.h"
#include "system_state.h"
#include "scheduler.h"

/*******************************************************************************
*                               C O N S T A N T S                              *
*******************************************************************************/ 

#define PLANE_NAV_RATE 750
#define PLANE_STARTING_RATE 100

#define PLANE_IDLE_ANGLE 0.0

/*******************************************************************************
*                      D A T A    D E C L A R A T I O N S                      *
*******************************************************************************/ 

typedef struct
{
    // some tracking of height after homing
    struct pt thread;
    plane_state_E state;
    float corr_angle;
} plane_data_S;

/*******************************************************************************
*          P R I V A T E    F U N C T I O N    D E C L A R A T I O N S         *
*******************************************************************************/

static plane_state_E plane_update_state(plane_state_E curr_state);

/*******************************************************************************
*                 S T A T I C    D A T A    D E F I N I T I O N S              *
*******************************************************************************/ 

static plane_data_S plane_data = 
{
    .state = PLANE_STATE_IDLE,
    .corr_angle = PLANE_IDLE_ANGLE
};

/*******************************************************************************
*                      P R I V A T E    F U N C T I O N S                      *
*******************************************************************************/

static plane_state_E plane_update_state(plane_state_E curr_state)
{
    plane_state_E next_state = curr_state;
    system_state_E system_state = system_state_getState();

    switch (curr_state)
    {
        case PLANE_STATE_IDLE:
            if (system_state == SYSTEM_STATE_ENTERING_SIDEON)
            {
                stepper_calibAngle(STEPPER_PLANE, PLANE_IDLE_ANGLE);
                next_state = PLANE_STATE_ENTERING_ACTIVE;
            }
            else
            {
                // do nothing, stay in idle state
            }
            break;
        case PLANE_STATE_ENTERING_ACTIVE:
            if (stepper_commandAngle(STEPPER_PLANE,
                                     plane_data.corr_angle,
                                     abs(plane_data.corr_angle * 0.1), 
                                     PLANE_NAV_RATE,
                                     PLANE_STARTING_RATE) == false)
            {
                // do nothing, straightening screw
            }
            else
            {
                next_state = PLANE_STATE_ACTIVE;
            }
            break;
        case PLANE_STATE_ACTIVE:
            if (system_state == SYSTEM_STATE_ENTERING_IDLE)
            {
                next_state = PLANE_STATE_IDLE;
            }
            else
            {
                // do nothing, side-on imaging
            }
            break;
        case PLANE_STATE_COUNT:
            break;
    }

    return next_state;
}

static PT_THREAD(run10ms(struct pt* thread))
{
    PT_BEGIN(thread);
    PT_WAIT_UNTIL(thread, 
                  scheduler_taskReleased(PERIOD_10ms, (uint8_t) PLANE));
    plane_data.state = plane_update_state(plane_data.state);
    PT_END(thread);
}


/*******************************************************************************
*                       P U B L I C    F U N C T I O N S                       *
*******************************************************************************/ 

void plane_init(void)
{
    PT_INIT(&plane_data.thread);

    stepper_init(STEPPER_PLANE);
}

void plane_run10ms(void)
{
    run10ms(&plane_data.thread);
}

plane_state_E plane_getState(void)
{
    return plane_data.state;
}

void plane_core_comms_setCorrAngle(uint8_t argNumber, char* args[])
{
    plane_data.corr_angle = atof(args[0]);
}
