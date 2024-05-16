//https://www.shadertoy.com/view/Ml2GWy

module.exports = `

// Copyright Inigo Quilez, 2015 - https://iquilezles.org/
// I am the sole copyright owner of this Work.
// You cannot host, display, distribute or share this Work in any form,
// including physical and digital. You cannot use this Work in any
// commercial or non-commercial product, website or project. You cannot
// sell this Work and you cannot mint an NFTs of it.
// I share this Work for educational purposes, and you can link to it,
// through an URL, proper attribution and unmodified screenshot, as part
// of your educational material. If these conditions are too restrictive
// please contact me and we'll definitely work it out.


void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
    vec2 pos = 256.0*fragCoord.xy/iResolution.x + iTime;

    vec3 col = vec3(0.0);
    for( int i=0; i<6; i++ )
    {
        vec2 a = floor(pos);
        vec2 b = fract(pos);

        vec4 w = fract((sin(a.x*7.0+31.0*a.y + 0.01*iTime)+vec4(0.035,0.01,0.0,0.7))*13.545317); // randoms

        col += w.xyz *                                   // color
        2.0*smoothstep(0.45,0.55,w.w) *           // intensity
        sqrt( 16.0*b.x*b.y*(1.0-b.x)*(1.0-b.y) ); // pattern

        pos /= 2.0; // lacunarity
        col /= 2.0; // attenuate high frequencies
    }

    col = pow( col, vec3(0.7,0.8,0.5) );    // contrast and color shape

    fragColor = vec4( col, 1.0 );
}

`
