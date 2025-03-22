// Adjustable parameters
top_platform_radius = 45;
bottom_platform_radius = 65; // Increased for stability
platform_thickness = 5;
leg_radius = 7;
leg_length = 120;
number_of_legs = 3;
number_of_circles = 7; // Number of concentric circles
circle_line_width = 0.75; // Width of the engraved lines
circle_spacing = 5; // Spacing between the circles
etching_depth = 0.65; // Depth of the etching
cable_hole_diameter = 7.5; // Diameter of the cable holes
number_of_cable_holes = 6; // Number of holes around the perimeter
leg_rotation = 30; // Rotation of legs in leg() module
zone_of_influence = 25; // Zone around leg where holes should not be placed

// --- Thin Ring Module ---
module thin_ring(radius, height, thickness, $fn = 60) {
    difference() {
        cylinder(h = height, r = radius, center = false, $fn = $fn);
        translate([0, 0, -0.1]) // Ensure the inner cylinder cuts through
        cylinder(h = height + 0.2, r = radius - thickness, center = false, $fn = $fn);
    }
}

// --- Cable Hole Module ---
module cable_hole(diameter) {
    cylinder(h = platform_thickness + 1, r = diameter / 2, center = true, $fn = 60);
}

// --- Top Platform Module ---
module top_platform() {
    difference() {
        cylinder(h = platform_thickness, r = top_platform_radius, center = false, $fn = 60);

        // Create concentric circle etchings on the TOP surface
        for (i = [1:number_of_circles]) {
            circle_radius = i * circle_spacing;
            translate([0, 0, platform_thickness - etching_depth])
            thin_ring(radius = circle_radius, height = etching_depth, thickness = circle_line_width);
        }

        // Create concentric circle etchings on the BOTTOM surface
        for (i = [1:number_of_circles]) {
            circle_radius = i * circle_spacing;
            translate([0, 0, 0]) // No vertical translation needed (already on the bottom)
            thin_ring(radius = circle_radius, height = etching_depth, thickness = circle_line_width);
        }

        // Add cable holes around the perimeter, avoiding the leg positions
        for (i = [0:number_of_cable_holes-1]) {
            angle = i * 360 / number_of_cable_holes;
            // Check if the angle is within a leg's zone of influence
            is_in_leg_zone = false;
            for (j = [0:number_of_legs-1]) {
                leg_angle = j * 360 / number_of_legs + leg_rotation;
                if (abs(angle - leg_angle) < zone_of_influence || abs(angle - leg_angle - 360) < zone_of_influence) {
                    is_in_leg_zone = true;
                }
            }
            
            if (!is_in_leg_zone) {
                rotate([0, 0, angle])
                translate([top_platform_radius - cable_hole_diameter / 2 - 2, 0, platform_thickness / 2])
                cable_hole(cable_hole_diameter);
            }
        }
    }
}

// --- Bottom Platform Module ---
module bottom_platform() {
    difference() {
        cylinder(h = platform_thickness, r = bottom_platform_radius, center = false, $fn = 60);

        // Create concentric circle etchings on the TOP surface
        for (i = [1:number_of_circles]) {
            circle_radius = i * circle_spacing;
            translate([0, 0, platform_thickness - etching_depth])
            thin_ring(radius = circle_radius, height = etching_depth, thickness = circle_line_width);
        }

        // Create concentric circle etchings on the BOTTOM surface
        for (i = [1:number_of_circles]) {
            circle_radius = i * circle_spacing;
            translate([0, 0, 0]) // No vertical translation needed (already on the bottom)
            thin_ring(radius = circle_radius, height = etching_depth, thickness = circle_line_width);
        }

        // Add cable holes around the perimeter, avoiding the leg positions
        for (i = [0:number_of_cable_holes-1]) {
            angle = i * 360 / number_of_cable_holes;
            
            // Check if the angle is within a leg's zone of influence
            is_in_leg_zone = false;
            for (j = [0:number_of_legs-1]) {
                leg_angle = j * 360 / number_of_legs + leg_rotation;
                if (abs(angle - leg_angle) < zone_of_influence || abs(angle - leg_angle - 360) < zone_of_influence) {
                    is_in_leg_zone = true;
                }
            }

            if (!is_in_leg_zone) {
                rotate([0, 0, angle])
                translate([bottom_platform_radius - cable_hole_diameter / 2 - 2, 0, platform_thickness / 2])
                cable_hole(cable_hole_diameter);
            }
        }
    }
}

// --- Leg Module ---
module leg() {
    rotate([0, 0, leg_rotation]) // Rotate legs for stability
    translate([top_platform_radius - leg_radius - 1, 0, platform_thickness])
    cylinder(h = leg_length, r = leg_radius, center = false, $fn = 60);
}

// --- Assembly ---
module tripod_stand() {
    // Bottom Platform
    bottom_platform();

    // Legs
    for (i = [0:360/number_of_legs:360 - 360/number_of_legs]) {
        rotate([0, 0, i])
        leg();
    }

    // Top Platform
    translate([0, 0, leg_length + platform_thickness])
    top_platform();
}

// --- Main ---
tripod_stand();