color_map_rainbow = """vec3 rainbow(float value) 
{
    // Normalize the value between 0 and 1 using the global minimum and maximum values
    float normalizedValue = (value - data_min) / (data_max - data_min);
    
    // Calculate the hue value (scaled to the range [0, 6])
    float hue = 6.0 * (1.0 - normalizedValue);
    
    // Calculate the individual color components based on the hue
    float r = max(0.0, min(1.0, abs(hue - 3.0) - 1.0));
    float g = max(0.0, min(1.0, 2.0 - abs(hue - 2.0)));
    float b = max(0.0, min(1.0, 2.0 - abs(hue - 4.0)));
    
    return vec3(r, g, b);
}
"""


color_map_inferno = """vec3 inferno(float value) {
    // Normalize the value between 0 and 1 using the global minimum and maximum values
    float normalizedValue = (value - data_min) / (data_max - data_min);
    
    // Define the color points of the color map
    vec3 black = vec3(0.0, 0.0, 0.0);
    vec3 magenta = vec3(1.0, 0.0, 1.0);
    vec3 orange = vec3(1.0, 0.647, 0.0);
    vec3 white = vec3(1.0, 1.0, 1.0);
    
    float interpolationValue = 3.0;

    // Calculate color interpolation
    vec3 color;
    if (normalizedValue <= 0.333) {
        color = mix(black, magenta, normalizedValue * interpolationValue);
    } else if (normalizedValue <= 0.666) {
        color = mix(magenta, orange, (normalizedValue - 0.333) * interpolationValue);
    } else if (normalizedValue <= 1.0) {
        color = mix(orange, white, (normalizedValue - 0.666) * interpolationValue);
    } else {
        color = white;
    }
    return color;
}"""

color_map_black_body = """vec3 black_body(float value) {
    // Normalize the value between 0 and 1 using the global minimum and maximum values
    float normalizedValue = (value - data_min) / (data_max - data_min);
    
    // Define the color points of the color map
    vec3 black = vec3(0.0, 0.0, 0.0);
    vec3 red = vec3(1.0, 0.0, 0.0);
    vec3 yellow = vec3(1.0, 1.0, 0.0);
    vec3 white = vec3(1.0, 1.0, 1.0);
    
    float interpolationValue = 3.0;

    // Calculate color interpolation
    vec3 color;
    if (normalizedValue <= 0.333) {
        color = mix(black, red, normalizedValue * interpolationValue);
    } else if (normalizedValue <= 0.666) {
        color = mix(red, yellow, (normalizedValue - 0.333) * interpolationValue);
    } else if (normalizedValue <= 1.0) {
        color = mix(yellow, white, (normalizedValue - 0.666) * interpolationValue);
    } else {
        color = white;
    }
    
    return color;
}"""
