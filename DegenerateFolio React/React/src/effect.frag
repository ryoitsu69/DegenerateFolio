const float pi = 3.14159;
const float pi2 = pi * 2.;

const vec2 cellSizePixels = vec2(192.,192.);// best results = any multiple of 2^iterations
float edgeSizePixels = 2.5;
const float iterations = 5.;


vec2 q(vec2 x, vec2 p)
{
    return floor(x/p)*p;
}

float rand(vec2 co){
    return fract(sin(dot(co.xy ,vec2(12.9898,78.233))) * 43758.5453);
}

vec3 rand3(vec2 p)
{
    vec3 p2 = vec3(p, rand(p));
    return
    fract(sin(vec3(
        dot(p2,vec3(127.1,311.7,427.89)),
                   dot(p2,vec3(269.5,183.3,77.24)),
                   dot(p2,vec3(42004.33,123.54,714.24))
    ))*43758.5453);
}

float sdAxisAlignedRect(vec2 uv, vec2 tl, vec2 br)
{
    vec2 d = max(tl - uv, uv - br);
    return length(max(vec2(0.0), d)) + min(0.0, max(d.x, d.y));
}

mat2 rot2D(float r)
{
    float c = cos(r), s = sin(r);
    return mat2(c, s, -s, c);
}
float pulse(float x, float pulseWidth, float totalPeriod)
{
    x = mod(x,totalPeriod);
    x -= pulseWidth /= 2.;
    return 1.-smoothstep(0.,pulseWidth, abs(x));
}



void mainImage( out vec4 o, in vec2 i)
{
    vec2 uv = i / iResolution.xy - .5;
    vec2 uvn = uv;// screen / unwarped coords

    uv += iMouse.xy *.1 / iResolution.xy;

    if(iResolution.x > iResolution.y)
        uv.x *= iResolution.x / iResolution.y;
    else
        uv.y /= iResolution.x / iResolution.y;


    //uv *= 1.+sin(iTime*0.5)*.1;// zoom
    uv -= .7;// offset rotation origin
    float rotation = -(iTime+40.)*0.005;
    //rotation = -0.2;// fixed-rot
    uv *= rot2D(rotation);// rot

    vec2 cellSize = cellSizePixels / iResolution.x;

    vec2 cellOrig;
    float cellID;
    float edgeSizePixels = 7.;

    for(float i = 0.;i<iterations;i++)
    {
        cellSize *= .5;
        edgeSizePixels *= .5;
        cellOrig = q(uv, cellSize);
        cellID = rand(cellOrig);
        if(i/iterations > sin(cellID*6.28+iTime*.2)*.5+.3)
            break;
    }
    edgeSizePixels = max(edgeSizePixels, 1.);

    //float cellID = rand(cellOrig);
    float distToCenter = distance(uv, cellOrig+cellSize/2.)/(length(cellSize)/2.);
    vec2 tl = cellOrig;
    vec2 br = cellOrig + cellSize;
    float distToEdge = sdAxisAlignedRect(uv, tl, br) / length(cellSize);// 0 = edge, -1 = center

    float edgeSize = edgeSizePixels/iResolution.x/length(cellSize);
    float aEdge = smoothstep(-edgeSize, 0., distToEdge);

    float totalPulsePeriod = 10.;// in seconds
    float highlightDuration = 1.2;
    float highlightStrength = 1.7;
    float highlight = pulse((cellID*totalPulsePeriod*totalPulsePeriod)+iTime,highlightDuration,totalPulsePeriod)*highlightStrength+1.;

    // cell background
    vec3 cellColor = rand3(cellOrig);
    o = vec4(cellColor.rgbb)*.3;
    o *= highlight;
    o *= 1.-distToCenter*.4;

    // edge color
    vec4 edgeColor = vec4(0,0,0,1);
    o = mix(o, edgeColor, aEdge);

    // saturation
    o = clamp(o,0.,1.);
    //o = mix(o, vec4((o.r+o.g+o.b)/3.), sin(iTime)*.5+.5);
    o = mix(o, vec4((o.r+o.g+o.b)/3.), .6);

    // tint green / brightness
    o *= vec4(.5,1,1,0)*2.;

    // noise
    o.rgb += (rand3(uvn*iTime)-.5)*.1;

    // vignette
    uvn *= 1.1;
    o *= 1.-dot(uvn,uvn);
    function setup() {
        pixelDensity(1);
        createCanvas(400,400);
        p = createGraphics(400,400,WEBGL).noStroke();

        // Create a p5.Shader object.
        let shaderProgram = createShader(vertSrc, fragSrc);

        // Apply the p5.Shader object.
        shader(shaderProgram);

        // Style the drawing surface.
        noStroke();

        // Add a plane as a drawing surface.
        plane(100, 100);

        describe('A yellow square.');
    }

    function draw() {
        background(220)
        s.setUniform("r",[p.width,p.height]);
        s.setUniform("t",millis()/1000.);
        s.setUniform("m",[mouseX/width,mouseY/height]);
        p.shader(s);
        p.rect(0,0,50);
        image(p,0,0)
    }
    // gamma
    o = clamp(o,0.,1.);
    o = pow(o, vec4(1./1.2));
}
