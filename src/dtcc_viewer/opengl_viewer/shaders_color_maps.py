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
    
    vec3 sampleColors[6] = vec3[6](
        vec3(0.0000, 0.0000, 0.0000),
        vec3(0.0784, 0.0431, 0.2039),
        vec3(0.5176, 0.1255, 0.4196),
        vec3(0.8980, 0.3608, 0.1882),
        vec3(0.9647, 0.8431, 0.2745),
        vec3(1.0000, 1.0000, 1.0000)
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
        vec3(0.1882, 0.0706, 0.2314),
        vec3(0.2549, 0.2706, 0.6706),
        vec3(0.2745, 0.4588, 0.9294),
        vec3(0.2235, 0.6353, 0.9882),
        vec3(0.1059, 0.8118, 0.8314),
        vec3(0.1412, 0.9255, 0.6510),
        vec3(0.3804, 0.9882, 0.4235),
        vec3(0.6431, 0.9882, 0.2314),
        vec3(0.8196, 0.9098, 0.2039),
        vec3(0.9529, 0.7765, 0.2275),
        vec3(0.9961, 0.6078, 0.1765),
        vec3(0.9529, 0.3882, 0.0824),
        vec3(0.8510, 0.2196, 0.0235),
        vec3(0.6941, 0.0980, 0.0039),
        vec3(0.4784, 0.0157, 0.0078)
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
