color_map_rainbow = """vec3 rainbow(float value) 
{   
    vec3 sampleColors[7] = vec3[7](
        vec3(1.0, 0.0, 0.0),
        vec3(1.0, 1.0, 0.0),
        vec3(0.0, 1.0, 0.0),
        vec3(0.0, 1.0, 1.0),
        vec3(0.0, 0.0, 1.0),
        vec3(1.0, 0.0, 1.0),
        vec3(1.0, 0.0, 0.0)
    );

    float normalizedValue = clamp((value - data_min) / (data_max - data_min), 0.0, 1.0);
    int lastIndex = sampleColors.length() - 1;
    
    // Calculate color segments
    int index = int(normalizedValue * lastIndex);
    float weight = fract(normalizedValue * lastIndex);

    vec3 color0 = sampleColors[index];
    vec3 color1 = sampleColors[index + 1];
    vec3 color = mix(color0, color1, weight);

    return color;
}
"""


color_map_inferno = """vec3 inferno(float value) {
    
    //vec3 sampleColors[4] = vec3[4](
    //    vec3(0.0, 0.0, 0.0),
    //    vec3(1.0, 0.0, 1.0),
    //    vec3(1.0, 0.647, 0.0),
    //    vec3(1.0, 1.0, 1.0),
    //);

    vec3 sampleColors[6] = vec3[6](
        vec3(0.0, 0.0, 0.0),
        vec3(20.0/255.0, 11.0/255.0, 52.0/255.0),
        vec3(132.0/255.0, 32.0/255.0, 107.0/255.0),
        vec3(229.0/255.0, 92.0/255.0, 48.0/255.0),
        vec3(246.0/255.0, 215.0/255.0, 70.0/255.0),
        vec3(1.0, 1.0, 1.0)
    );

    float normalizedValue = clamp((value - data_min) / (data_max - data_min), 0.0, 1.0);
    int lastIndex = sampleColors.length() - 1;
    
    // Calculate color segments
    int index = int(normalizedValue * lastIndex);
    float weight = fract(normalizedValue * lastIndex);

    vec3 color0 = sampleColors[index];
    vec3 color1 = sampleColors[index + 1];
    vec3 color = mix(color0, color1, weight);

    return color;
}"""

color_map_black_body = """vec3 black_body(float value) {

    vec3 sampleColors[4] = vec3[4](
        vec3(0.0, 0.0, 0.0),
        vec3(1.0, 0.0, 0.0),
        vec3(1.0, 1.0, 0.0),
        vec3(1.0, 1.0, 1.0)
    );

    float normalizedValue = clamp((value - data_min) / (data_max - data_min), 0.0, 1.0);
    int lastIndex = sampleColors.length() - 1;
    
    // Calculate color segments
    int index = int(normalizedValue * lastIndex);
    float weight = fract(normalizedValue * lastIndex);

    vec3 color0 = sampleColors[index];
    vec3 color1 = sampleColors[index + 1];
    vec3 color = mix(color0, color1, weight);

    return color;
}"""

color_map_turbo = """vec3 turbo(float value) {
    
    vec3 sampleColors[15] = vec3[15](
        vec3(48.0 / 255.0, 18.0 / 255.0, 59.0 / 255.0),
        vec3(65.0 / 255.0, 69.0 / 255.0, 171.0 / 255.0),
        vec3(70.0 / 255.0, 117.0 / 255.0, 237.0 / 255.0),
        vec3(57.0 / 255.0, 162.0 / 255.0, 252.0 / 255.0),
        vec3(27.0 / 255.0, 207.0 / 255.0, 212.0 / 255.0),
        vec3(36.0 / 255.0, 236.0 / 255.0, 166.0 / 255.0),
        vec3(97.0 / 255.0, 252.0 / 255.0, 108.0 / 255.0),
        vec3(164.0 / 255.0, 252.0 / 255.0, 59.0 / 255.0),
        vec3(209.0 / 255.0, 232.0 / 255.0, 52.0 / 255.0),
        vec3(243.0 / 255.0, 198.0 / 255.0, 58.0 / 255.0),
        vec3(254.0 / 255.0, 155.0 / 255.0, 45.0 / 255.0),
        vec3(243.0 / 255.0, 99.0 / 255.0, 21.0 / 255.0),
        vec3(217.0 / 255.0, 56.0 / 255.0, 6.0 / 255.0),
        vec3(177.0 / 255.0, 25.0 / 255.0, 1.0 / 255.0),
        vec3(122.0 / 255.0, 4.0 / 255.0, 2.0 / 255.0)
    );

    float normalizedValue = clamp((value - data_min) / (data_max - data_min), 0.0, 1.0);

    int lastIndex = sampleColors.length() - 1;
    
    // Calculate color segments
    int index = int(normalizedValue * lastIndex);
    float weight = fract(normalizedValue * lastIndex);

    vec3 color0 = sampleColors[index];
    vec3 color1 = sampleColors[index + 1];
    vec3 color = mix(color0, color1, weight);

    return color;
}"""


color_map_viridis = """vec3 viridis(float value) {

    // Viridis
    vec3 sampleColors[18] = vec3[18](
        vec3(0.267, 0.0049, 0.3294),
        vec3(0.2819, 0.0897, 0.4124),
        vec3(0.2803, 0.1657, 0.4765),
        vec3(0.2637, 0.2376, 0.5188),
        vec3(0.2374, 0.3052, 0.5419),
        vec3(0.2086, 0.3678, 0.5527),
        vec3(0.1823, 0.4262, 0.5571),
        vec3(0.1592, 0.4822, 0.5581),
        vec3(0.1378, 0.5375, 0.5549),
        vec3(0.1211, 0.5927, 0.5446),
        vec3(0.1281, 0.6477, 0.5235),
        vec3(0.1807, 0.7014, 0.4882),
        vec3(0.2741, 0.752, 0.4366),
        vec3(0.3952, 0.7975, 0.3678),
        vec3(0.5356, 0.8358, 0.2819),
        vec3(0.6889, 0.8654, 0.1827),
        vec3(0.8456, 0.8873, 0.0997),
        vec3(0.9932, 0.9062, 0.1439)
    );

    float normalizedValue = clamp((value - data_min) / (data_max - data_min), 0.0, 1.0);

    int lastIndex = sampleColors.length() - 1;
    
    // Calculate color segments
    int index = int(normalizedValue * lastIndex);
    float weight = fract(normalizedValue * lastIndex);

    vec3 color0 = sampleColors[index];
    vec3 color1 = sampleColors[index + 1];
    vec3 color = mix(color0, color1, weight);

    return color;
}"""
