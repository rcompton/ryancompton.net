// Adjustable parameters
top_platform_radius = 80;
bottom_platform_radius = 90; // Increased for stability
platform_thickness = 7;
leg_radius = 8;
leg_length = 100;
number_of_legs = 4;
number_of_circles = 5; // Number of concentric circles
circle_line_width = 0.75; // Width of the engraved lines
circle_spacing = 10; // Spacing between the circles
etching_depth = 1.25; // Depth of the etching
cable_hole_diameter = 7.5; // Diameter of the cable holes
number_of_cable_holes = 2; // Number of holes around the perimeter
leg_rotation = 30; // Rotation of legs in leg() module
zone_of_influence = 25; // Zone around leg where holes should not be placed
leg_socket_stop_thickness = 3.5; // Material thickness at the top of the leg socket
leg_socket_clearance = 0.6; // NEW: Additional radius for leg sockets for a looser fit

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

// --- Top Platform Module (Modified for Socket Clearance) ---
module top_platform() {
    difference() {
        // Main body of the top platform
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
            translate([0, 0, 0]) // Etchings are on the bottom face (z=0 up to z=etching_depth)
            thin_ring(radius = circle_radius, height = etching_depth, thickness = circle_line_width);
        }

        // Add cable holes around the perimeter, avoiding the leg positions
        for (i = [0:number_of_cable_holes-1]) {
            angle = i * 360 / number_of_cable_holes;
            is_in_leg_zone = false;
            for (j = [0:number_of_legs-1]) {
                leg_angle_check = j * 360 / number_of_legs + leg_rotation; // Angle of the leg center
                diff = abs(angle - leg_angle_check);
                if (min(diff, 360 - diff) < zone_of_influence) {
                    is_in_leg_zone = true;
                }
            }
            
            if (!is_in_leg_zone) {
                rotate([0, 0, angle])
                translate([top_platform_radius - cable_hole_diameter / 2 - 2, 0, platform_thickness / 2])
                cable_hole(cable_hole_diameter);
            }
        }

        // ***** MODIFIED: Add Leg Sockets (Blind Holes) with Clearance *****
        for (leg_idx = [0:number_of_legs-1]) {
            socket_angle_deg = leg_idx * (360 / number_of_legs) + leg_rotation;
            socket_radial_pos = top_platform_radius - leg_radius - 1;
            socket_x = socket_radial_pos * cos(socket_angle_deg);
            socket_y = socket_radial_pos * sin(socket_angle_deg);

            socket_cut_depth = platform_thickness - leg_socket_stop_thickness;
            actual_socket_cut_depth = max(0, socket_cut_depth); 

            // Define the radius of the socket, including clearance
            socket_radius = leg_radius + leg_socket_clearance; // MODIFIED HERE

            if (actual_socket_cut_depth > 0) { 
                translate([socket_x, socket_y, -0.1]) 
                    cylinder(h = actual_socket_cut_depth + 0.1, r = socket_radius, $fn = 60); // Use socket_radius
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
            translate([0, 0, 0])
            thin_ring(radius = circle_radius, height = etching_depth, thickness = circle_line_width);
        }

        // Add cable holes around the perimeter, avoiding the leg positions
        for (i = [0:number_of_cable_holes-1]) {
            angle = i * 360 / number_of_cable_holes;
            is_in_leg_zone = false;
            for (j = [0:number_of_legs-1]) {
                leg_angle_check = j * 360 / number_of_legs + leg_rotation;
                diff = abs(angle - leg_angle_check);
                 if (min(diff, 360 - diff) < zone_of_influence) {
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
    rotate([0, 0, leg_rotation]) 
    translate([top_platform_radius - leg_radius - 1, 0, platform_thickness]) 
    cylinder(h = leg_length, r = leg_radius, center = false, $fn = 60);
}

// --- Assembly Modules ---
module base_with_legs() {
    bottom_platform();
    for (rot_angle = [0 : 360/number_of_legs : 360 - 360/number_of_legs]) { 
        rotate([0, 0, rot_angle]) 
        leg(); 
    }
}

module top_platform_printable() {
    top_platform();
}

module full_tripod_assembly() {
    base_with_legs();
    translate([0, 0, platform_thickness + leg_length])
    top_platform_printable();
}

// --- Main Rendering ---
// Option 1: Render only the top platform
//top_platform_printable();

// Option 2: Render only the base with legs
// translate([bottom_platform_radius * 2.5, 0, 0]) 
base_with_legs();

// Option 3: Render the full assembled tripod
// translate([0, (bottom_platform_radius + top_platform_radius) * 1.5, 0]) 
// full_tripod_assembly();
