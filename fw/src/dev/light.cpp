
/*******************************************************************************
*                                I N C L U D E S                               *
*******************************************************************************/ 

#include "light.h"
#include "serial.h"

/*******************************************************************************
*                               C O N S T A N T S                              *
*******************************************************************************/ 

/*******************************************************************************
*                      D A T A    D E C L A R A T I O N S                      *
*******************************************************************************/ 

typedef struct
{
    int brightness;
    uint8_t pin;
} light_s;

typedef struct
{
    light_data_s lights[LIGHT_COUNT];
} light_data_s;

/*******************************************************************************
*          P R I V A T E    F U N C T I O N    D E C L A R A T I O N S         *
*******************************************************************************/
uint16_t _brightness_to_duty(int brightness);
/*******************************************************************************
*                 S T A T I C    D A T A    D E F I N I T I O N S              *
*******************************************************************************/ 

light_data_s light_data =
{
    .lights = 
    {
        [LIGHT_BOTTOM] =
        {
            .pin = PA0, // actual pin TBD
            .pwm_pin = PA_0,
            .brightness = 0
        },
        [LIGHT_DOME] =
        {
            .pin = PA1, // actual pin TBD
            .pwm_pin = PA_1,
            .brightness = 0
        }
    }
};

/*******************************************************************************
*                      P R I V A T E    F U N C T I O N S                      *
*******************************************************************************/ 
uint16_t _brightness_to_duty(int brightness)
{
    int output_brightness = max(0, min(brightness, 100));
    return (uint16_t) output_brightness / 100.0 * 65535;
}

/*******************************************************************************
*                       P U B L I C    F U N C T I O N S                       *
*******************************************************************************/ 
void light_set_state(light_id_E light_id, int brightness)
{
    uint16_t duty = _brightness_to_duty(brightness);
    light_data.lights[light_id].brightness = brightness;
    pwm_start(light_data.lights[light_id].pwm_pin, 2000, duty, 
              TimerCompareFormat_t::RESOLUTION_16B_COMPARE_FORMAT);
}

void light_init(light_id_E light_id)
{
    pinMode(light_data.lights[light_id].pin, OUTPUT);
    light_set_state(light_id, 0);
}

int light_get_state(light_id_E light_id)
{
    return light_data.lights[light_id].brightness;
}

void light_cli_set_state(uint8_t argNumber, char* args[])
{
    if (strcmp(args[0], "backlight") == 0)
    {   
        int brightness = atof(args[1]);
        light_set_state(LIGHT_BOTTOM, brightness);
    }
    else if (strcmp(args[0], "domelight") == 0)
    {
        int brightness = atof(args[1]);
        light_set_state(LIGHT_DOME, brightness);
    }
    else
    {
        serial_send_nl(PORT_COMPUTER, "invalid light");
    }
}