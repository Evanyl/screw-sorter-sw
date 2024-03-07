/*******************************************************************************
*                                I N C L U D E S                               *
*******************************************************************************/ 

#include <Arduino.h>

#include "light.h"
#include "serial.h"

/*******************************************************************************
*                               C O N S T A N T S                              *
*******************************************************************************/ 

#define LIGHT_PWM_FREQ_HZ 2000

/*******************************************************************************
*                      D A T A    D E C L A R A T I O N S                      *
*******************************************************************************/ 

typedef struct
{
    uint8_t dig_pin;
    PinName pwm_pin;
    uint16_t brightness;
} light_s;


typedef struct
{
    light_s lights[LIGHT_COUNT];
} light_data_s;

/*******************************************************************************
*          P R I V A T E    F U N C T I O N    D E C L A R A T I O N S         *
*******************************************************************************/ 

/*******************************************************************************
*                 S T A T I C    D A T A    D E F I N I T I O N S              *
*******************************************************************************/ 

light_data_s light_data = 
{
    .lights = 
    {
        [LIGHT_BACK] = 
        {
            .dig_pin = PA0,
            .pwm_pin = PA_0,
        },
        [LIGHT_SIDE] =
        {
            .dig_pin = PA8,
            .pwm_pin = PA_8,
        }
    }
};

/******************************************************************************* 
*                      P R I V A T E    F U N C T I O N S                      * 
*******************************************************************************/ 

/******************************************************************************* 
*                       P U B L I C    F U N C T I O N S                       * 
*******************************************************************************/ 

void light_init(light_id_E id, uint16_t brightness)
{
    light_s* l = &light_data.lights[id];
    pinMode(l->dig_pin, OUTPUT);
    pwm_start((PinName) l->pwm_pin, 
              LIGHT_PWM_FREQ_HZ, 
              brightness,
              TimerCompareFormat_t::RESOLUTION_16B_COMPARE_FORMAT);
}

void light_command(light_id_E id, uint16_t brightness)
{
    light_s* l = &light_data.lights[id];
    pwm_start((PinName) l->pwm_pin, 
              LIGHT_PWM_FREQ_HZ, 
              brightness,
              TimerCompareFormat_t::RESOLUTION_16B_COMPARE_FORMAT);
}

void light_cli_update(uint8_t argNumber, char* args[])
{
    light_id_E l = LIGHT_COUNT;
    if (strcmp(args[0], "sidelight") == 0)
    {   
        l = LIGHT_SIDE;
    }
    else if (strcmp(args[0], "backlight") == 0)
    {
        l = LIGHT_BACK;
    }
    else
    {
        // do nothing
    }

    uint16_t brightness = atoi(args[1]);
    if (l != LIGHT_COUNT)
    {
        light_command(l, brightness);
    }
    else
    {
        serial_send_nl(PORT_COMPUTER, "invalid light");
    }
}
