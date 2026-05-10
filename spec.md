# Intoduction
This is a simple app that helps paraglider pilots to learn how much to a speedbar to apply at various conditions.

It recieves the paraglider polar as input. Then it outputs:
- polar curve
- best glide for still air
- the 2d heat table indicating optimal speedbar position and expected glide for various combinations of wind and sync.

# Polar Curve
Polar curve is defined by 3 points [X, Y]. X represents a airspeed, Y represents sync rate (negative). The first and last points are definiing the boundaries of polar and correspond to trim speed (0 speedbar) and max speed (full speedbar). Middle point defines the curvature of the polar.

The app will fit quadratic to these 3 points.

# UI Window
Contains:
- parameters to define the polar curve
- [Calculate] button
- Output: best glide
- Output: polar curve chart
- Output: best speedbar and glide chart (heat table)