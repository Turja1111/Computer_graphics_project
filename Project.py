"""
CYBER RUNNER 2077 - NEON HORIZON (FIXED VERSION)
Course: CSE423 Computer Graphics via OpenGL
Implementation: Functional Programming (No Classes)
Strictly using allowed PyOpenGL functions per specification.

CONTROLS:
  [W]         : Resume from slide
  [S]         : Slide under obstacles
  [A] / [D]   : Lane Switch (Left/Right)
  [SPACE]     : Jump
  [MOUSE L]   : Laser Shot (Hold for Charge)
  [MOUSE R]   : Grenade Launcher
  [F]         : First Person View
  [1]         : Side View
  [2]         : Top-Down View
  [3]         : Cinematic View
  [4]         : Third Person View (Default)
  [C]         : Cheat Mode (Invincibility)
  [V]         : God Mode AI (Auto-Play)
  [B]         : Slow Motion (Cheat)
  [P]         : Pause
  [R]         : Restart
  [Arrow Keys]: Camera Control
"""

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import math
import random
import time
import sys
from OpenGL.GLUT import GLUT_BITMAP_HELVETICA_18

# =============================================================================
# GLOBAL CONSTANTS & CONFIGURATION
# =============================================================================

WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 900
WINDOW_TITLE = b"CYBER RUNNER 2077: NEON HORIZON"

# Neon Cyberpunk Color Palette
COL_NEON_CYAN = (0.0, 1.0, 1.0)
COL_NEON_PINK = (1.0, 0.0, 0.8)
COL_NEON_BLUE = (0.0, 0.5, 1.0)
COL_NEON_GREEN = (0.0, 1.0, 0.0)
COL_NEON_PURPLE = (0.8, 0.0, 1.0)
COL_NEON_YELLOW = (1.0, 1.0, 0.0)
COL_NEON_ORANGE = (1.0, 0.5, 0.0)
COL_GOLD = (1.0, 0.84, 0.0)
COL_WARNING = (1.0, 0.0, 0.0)
COL_DARK_VOID = (0.05, 0.05, 0.15)
COL_LIGHTER_SKY = (0.2, 0.3, 0.5)
COL_WHITE = (1.0, 1.0, 1.0)
COL_GRAY = (0.5, 0.5, 0.5)
COL_BARRIER_RED = (0.8, 0.0, 0.0)

# Physics Constants
GRAVITY = -50.0
JUMP_FORCE = 30.0
LANE_WIDTH = 13.0
MAX_SPEED = 150.0
SPEED_INCREMENT = 0.5
INITIAL_SPEED = 60.0

# Game Balance
PLAYER_START_HEALTH = 3
PLAYER_START_GRENADES = 5
MAX_GRENADES = 5
COMBO_TIMEOUT = 3.0
VICTORY_SCORE = 5000
SHIELD_DURATION = 10.0  # Shield lasts 10 seconds
SPEED_BOOST_DURATION = 5.0  # Speed boost lasts 5 seconds

# =============================================================================
# GLOBAL STATE VARIABLES
# =============================================================================

# Game Core
game_state = "menu"  # menu, playing, paused, gameover, victory, loading
last_time = 0
dt_accumulator = 0.0
current_speed = INITIAL_SPEED
total_distance = 0.0
current_score = 0
loading_countdown = 3.0

# Camera System
camera_mode = "third"  # third, first, side, top, cinematic
camera_offset_y = 0.0  # Arrow key adjustment
camera_rotation = 0.0  # Arrow key rotation
camera_cinematic_angle = 0.0

# Player State
player_x = 0.0
player_y = 0.0
player_z = 0.0
player_lane_index = 1  # 0=left, 1=center, 2=right
player_velocity_y = 0.0
player_is_jumping = False
player_is_sliding = False
player_slide_timer = 0.0
player_health = PLAYER_START_HEALTH
player_grenades = PLAYER_START_GRENADES
player_cheat_mode = False
player_has_shield = False
player_shield_timer = 0.0  # NEW: Track shield duration
player_speed_boost_active = False  # NEW: Track speed boost
player_speed_boost_timer = 0.0  # NEW: Track speed boost duration
player_charging = False
player_charge_start_time = 0.0
player_animation_phase = 0.0
player_damage_flash = 0.0
player_perfect_dodge_count = 0

# Combo System
combo_multiplier = 1
combo_last_collect_time = 0.0

# Game Objects Collections
obstacles = []
collectibles = []
projectiles = []
particles = []
environment_buildings = []
environment_stars = []
floating_platforms = []

# Difficulty Progression
difficulty_level = 1
obstacle_spawn_rate = 0.04
last_speed_up_score = 0

# Cheats & AI
player_god_mode = False
slow_motion = False

# Statistics
stats_obstacles_dodged = 0
stats_gems_collected = 0

# Guaranteed power-up tracking for first 2000m - 2 of each
shield_spawn_count = 0  # Track how many shields spawned (need 2)
speed_spawn_count = 0   # Track how many speed boosts spawned (need 2)
grenade_spawn_count = 0 # Track how many grenade packs spawned (need 2)

# On-Screen Message System
on_screen_messages = []  # List of (message, timestamp) tuples
MESSAGE_DISPLAY_DURATION = 2.5  # Seconds to show each message

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def lerp(a, b, t):
    """Linear interpolation."""
    return a + (b - a) * t

def clamp(value, min_val, max_val):
    """Clamp value between min and max."""
    return max(min_val, min(max_val, value))

def distance_3d(x1, y1, z1, x2, y2, z2):
    """Calculate 3D distance."""
    return math.sqrt((x2-x1)**2 + (y2-y1)**2 + (z2-z1)**2)

def color_lerp(c1, c2, t):
    """Interpolate between two colors."""
    return (lerp(c1[0], c2[0], t), lerp(c1[1], c2[1], t), lerp(c1[2], c2[2], t))

def show_message(message):
    """Add a message to the on-screen display queue."""
    global on_screen_messages
    on_screen_messages.append((message, time.time()))
    print(f"[MESSAGE] {message}")  # Also print to console

# =============================================================================
# INITIALIZATION FUNCTIONS
# =============================================================================

def init_game():
    """Initialize all global variables for new game."""
    global game_state, current_speed, total_distance, current_score, last_time
    global obstacles, collectibles, projectiles, particles
    global environment_buildings, floating_platforms
    global difficulty_level, obstacle_spawn_rate, last_speed_up_score
    global combo_multiplier, combo_last_collect_time
    global stats_obstacles_dodged, stats_gems_collected
    global loading_countdown, player_perfect_dodge_count
    global on_screen_messages
    
    game_state = "menu"
    current_speed = INITIAL_SPEED
    total_distance = 0.0
    current_score = 0
    last_time = time.time()
    loading_countdown = 3.0
    
    difficulty_level = 1
    obstacle_spawn_rate = 0.02
    last_speed_up_score = 0
    
    combo_multiplier = 1
    combo_last_collect_time = 0.0
    
    stats_obstacles_dodged = 0
    stats_gems_collected = 0
    player_perfect_dodge_count = 0
    
    # Reset guaranteed power-up tracking - 2 of each
    global shield_spawn_count, speed_spawn_count, grenade_spawn_count
    shield_spawn_count = 0
    speed_spawn_count = 0
    grenade_spawn_count = 0
    
    on_screen_messages = []  # Clear messages
    
    reset_player()
    
    obstacles = []
    collectibles = []
    projectiles = []
    particles = []
    environment_buildings = []
    floating_platforms = []
    
    init_environment()
    print("[INIT] Game Initialized Successfully")

def reset_player():
    """Reset player to starting state."""
    global player_x, player_y, player_z, player_lane_index
    global player_velocity_y, player_is_jumping, player_is_sliding
    global player_health, player_grenades, player_has_shield
    global player_damage_flash, player_animation_phase
    global player_shield_timer, player_speed_boost_active, player_speed_boost_timer
    
    player_x = 0.0
    player_y = 0.0
    player_z = 0.0
    player_lane_index = 1
    player_velocity_y = 0.0
    player_is_jumping = False
    player_is_sliding = False
    player_health = PLAYER_START_HEALTH
    player_grenades = PLAYER_START_GRENADES
    player_has_shield = False
    player_shield_timer = 0.0
    player_speed_boost_active = False
    player_speed_boost_timer = 0.0
    player_damage_flash = 0.0
    player_animation_phase = 0.0

def init_environment():
    """Generate static environment elements."""
    global environment_stars, environment_buildings, floating_platforms
    
    environment_stars = []
    environment_buildings = []
    floating_platforms = []
    
    # Generate starfield
    for i in range(300):
        star = {
            'x': random.uniform(-400, 400),
            'y': random.uniform(50, 250),
            'z': random.uniform(-100, -800),
            'size': random.uniform(1.5, 4.0),
            'brightness': random.uniform(0.5, 1.0)
        }
        environment_stars.append(star)
    
    # Initial buildings
    for i in range(40):
        spawn_building(initial=True)
    
    # Floating platforms for depth
    for i in range(20):
        spawn_floating_platform(initial=True)

# =============================================================================
# PRIMITIVE DRAWING FUNCTIONS (MANUAL TRIANGLES ONLY)
# =============================================================================

def draw_triangle_cube(x, y, z, size, color):
    """Draw a cube using 12 triangles (2 per face)."""
    s = size / 2.0
    
    glPushMatrix()
    glTranslatef(x, y, z)
    
    # Define 8 vertices
    v = [
        (-s, -s, -s), (s, -s, -s), (s, s, -s), (-s, s, -s),  # Back face
        (-s, -s, s), (s, -s, s), (s, s, s), (-s, s, s)       # Front face
    ]
    
    glBegin(GL_TRIANGLES)
    
    # Front face (brighter)
    glColor3f(color[0], color[1], color[2])
    glVertex3f(*v[4]); glVertex3f(*v[5]); glVertex3f(*v[6])
    glVertex3f(*v[4]); glVertex3f(*v[6]); glVertex3f(*v[7])
    
    # Back face (darker)
    dark = tuple(c * 0.4 for c in color)
    glColor3f(*dark)
    glVertex3f(*v[0]); glVertex3f(*v[3]); glVertex3f(*v[2])
    glVertex3f(*v[0]); glVertex3f(*v[2]); glVertex3f(*v[1])
    
    # Top face
    light = tuple(min(1.0, c * 1.2) for c in color)
    glColor3f(*light)
    glVertex3f(*v[3]); glVertex3f(*v[7]); glVertex3f(*v[6])
    glVertex3f(*v[3]); glVertex3f(*v[6]); glVertex3f(*v[2])
    
    # Bottom face
    glColor3f(*dark)
    glVertex3f(*v[0]); glVertex3f(*v[1]); glVertex3f(*v[5])
    glVertex3f(*v[0]); glVertex3f(*v[5]); glVertex3f(*v[4])
    
    # Right face
    med = tuple(c * 0.7 for c in color)
    glColor3f(*med)
    glVertex3f(*v[1]); glVertex3f(*v[2]); glVertex3f(*v[6])
    glVertex3f(*v[1]); glVertex3f(*v[6]); glVertex3f(*v[5])
    
    # Left face
    glColor3f(*med)
    glVertex3f(*v[0]); glVertex3f(*v[4]); glVertex3f(*v[7])
    glVertex3f(*v[0]); glVertex3f(*v[7]); glVertex3f(*v[3])
    
    glEnd()
    glPopMatrix()

def draw_triangle_sphere(radius, slices, stacks, color):
    """Draw sphere approximation using triangles."""
    glBegin(GL_TRIANGLES)
    
    for i in range(stacks):
        lat0 = math.pi * (-0.5 + float(i) / stacks)
        z0 = math.sin(lat0)
        zr0 = math.cos(lat0)
        
        lat1 = math.pi * (-0.5 + float(i + 1) / stacks)
        z1 = math.sin(lat1)
        zr1 = math.cos(lat1)
        
        for j in range(slices):
            lng0 = 2 * math.pi * float(j) / slices
            x0 = math.cos(lng0)
            y0 = math.sin(lng0)
            
            lng1 = 2 * math.pi * float(j + 1) / slices
            x1 = math.cos(lng1)
            y1 = math.sin(lng1)
            
            # Vertices
            v1 = (x0 * zr0 * radius, y0 * zr0 * radius, z0 * radius)
            v2 = (x0 * zr1 * radius, y0 * zr1 * radius, z1 * radius)
            v3 = (x1 * zr0 * radius, y1 * zr0 * radius, z0 * radius)
            v4 = (x1 * zr1 * radius, y1 * zr1 * radius, z1 * radius)
            
            # Shading based on height
            shade = 0.6 + 0.4 * z0
            glColor3f(color[0] * shade, color[1] * shade, color[2] * shade)
            
            glVertex3f(*v1); glVertex3f(*v2); glVertex3f(*v3)
            glVertex3f(*v3); glVertex3f(*v2); glVertex3f(*v4)
    
    glEnd()

def draw_triangle_cylinder(base_radius, top_radius, height, slices, color):
    """Draw cylinder/cone using triangular strips."""
    glBegin(GL_TRIANGLES)
    
    for i in range(slices):
        theta1 = 2.0 * math.pi * i / slices
        theta2 = 2.0 * math.pi * (i + 1) / slices
        
        # Bottom vertices
        x1_b = base_radius * math.cos(theta1)
        y1_b = base_radius * math.sin(theta1)
        x2_b = base_radius * math.cos(theta2)
        y2_b = base_radius * math.sin(theta2)
        
        # Top vertices
        x1_t = top_radius * math.cos(theta1)
        y1_t = top_radius * math.sin(theta1)
        x2_t = top_radius * math.cos(theta2)
        y2_t = top_radius * math.sin(theta2)
        
        # Side faces (2 triangles per slice)
        shade = 0.5 + 0.5 * math.cos(theta1)
        glColor3f(color[0] * shade, color[1] * shade, color[2] * shade)
        
        glVertex3f(x1_b, y1_b, 0)
        glVertex3f(x2_b, y2_b, 0)
        glVertex3f(x1_t, y1_t, height)
        
        glVertex3f(x2_b, y2_b, 0)
        glVertex3f(x2_t, y2_t, height)
        glVertex3f(x1_t, y1_t, height)
        
        # Bottom cap
        dark = tuple(c * 0.3 for c in color)
        glColor3f(*dark)
        glVertex3f(0, 0, 0)
        glVertex3f(x2_b, y2_b, 0)
        glVertex3f(x1_b, y1_b, 0)
        
        # Top cap
        if top_radius > 0:
            glVertex3f(0, 0, height)
            glVertex3f(x1_t, y1_t, height)
            glVertex3f(x2_t, y2_t, height)
    
    glEnd()

def draw_triangle_cone(base_radius, height, slices, color):
    """Draw cone (cylinder with top_radius=0)."""
    draw_triangle_cylinder(base_radius, 0.0, height, slices, color)

# =============================================================================
# COMPLEX CHARACTER & OBJECT DRAWING
# =============================================================================

def draw_robot_player():
    """Draw detailed humanoid robot with 6 primitive shapes."""
    global player_x, player_y, player_z, player_is_sliding, player_animation_phase
    global player_cheat_mode, player_has_shield, player_charging
    global player_charge_start_time, player_damage_flash, player_speed_boost_active
    
    glPushMatrix()
    glTranslatef(player_x, player_y, player_z)
    
    # Slide animation (rotate backward)
    if player_is_sliding:
        glRotatef(-45, 1, 0, 0)
        glTranslatef(0, -1.5, 1.5)
    
    # Determine color scheme
    base_color = COL_NEON_CYAN
    if player_cheat_mode:
        base_color = COL_GOLD
    elif player_has_shield:
        base_color = COL_NEON_GREEN
    elif player_speed_boost_active:
        base_color = COL_NEON_YELLOW
    
    # Damage flash effect
    if player_damage_flash > 0:
        flash_amt = player_damage_flash
        base_color = color_lerp(base_color, COL_WARNING, flash_amt)
    
    # Animation parameters
    run_cycle = math.sin(player_animation_phase)
    arm_swing = run_cycle * 25
    leg_swing = run_cycle * 35
    
    # 1. TORSO (Cuboid)
    glPushMatrix()
    glScalef(1.2, 1.8, 0.9)
    draw_triangle_cube(0, 0, 0, 1.0, base_color)
    glPopMatrix()
    
    # Chest core light
    glPushMatrix()
    glTranslatef(0, 0.3, 0.55)
    pulse = 0.8 + 0.2 * math.sin(player_animation_phase * 3)
    glScalef(pulse, pulse, pulse)
    draw_triangle_cube(0, 0, 0, 0.3, COL_WHITE)
    glPopMatrix()
    
    # 2. HEAD (Sphere)
    glPushMatrix()
    glTranslatef(0, 1.5, 0)
    draw_triangle_sphere(0.5, 12, 12, (0.85, 0.85, 0.85))
    
    # Visor (eyes)
    glTranslatef(0, 0.1, 0.45)
    glScalef(0.8, 0.2, 0.15)
    draw_triangle_cube(0, 0, 0, 1.0, COL_NEON_PINK)
    glPopMatrix()
    
    # 3. LEFT ARM (Cylinder)
    glPushMatrix()
    glTranslatef(-0.85, 0.6, 0)
    glRotatef(arm_swing, 1, 0, 0)
    glRotatef(90, 1, 0, 0)
    draw_triangle_cylinder(0.2, 0.18, 1.3, 10, base_color)
    
    # Left hand (sphere)
    glTranslatef(0, 0, 1.3)
    draw_triangle_sphere(0.22, 8, 8, (0.2, 0.2, 0.25))
    glPopMatrix()
    
    # 4. RIGHT ARM WITH WEAPON (Cylinder)
    glPushMatrix()
    glTranslatef(0.85, 0.6, 0)
    glRotatef(-arm_swing * 0.5, 1, 0, 0)
    
    # Weapon attachment
    glPushMatrix()
    glTranslatef(0, 0, 0.7)
    glRotatef(90, 0, 0, 1)
    glScalef(0.3, 0.3, 1.2)
    draw_triangle_cube(0, 0, 0, 1.0, (0.3, 0.3, 0.35))
    
    # Weapon barrel tip
    glTranslatef(0, 0, 0.6)
    draw_triangle_cylinder(0.15, 0.1, 0.4, 8, (0.5, 0.5, 0.55))
    
    # Charge effect visualization
    if player_charging:
        charge_time = time.time() - player_charge_start_time
        charge_size = min(charge_time * 0.6, 1.2)
        charge_pulse = 1.0 + 0.2 * math.sin(charge_time * 10)
        
        glTranslatef(0, 0, 0.3)
        glScalef(charge_pulse, charge_pulse, charge_pulse)
        draw_triangle_sphere(charge_size, 12, 12, COL_NEON_PINK)
    glPopMatrix()
    
    # Arm cylinder
    glRotatef(90, 1, 0, 0)
    draw_triangle_cylinder(0.2, 0.18, 1.3, 10, base_color)
    glPopMatrix()
    
    # 5. LEFT LEG (Cylinder)
    glPushMatrix()
    glTranslatef(-0.35, -1.1, 0)
    glRotatef(-leg_swing, 1, 0, 0)
    glRotatef(90, 1, 0, 0)
    draw_triangle_cylinder(0.25, 0.2, 1.6, 10, base_color)
    glPopMatrix()
    
    # 6. RIGHT LEG (Cylinder)
    glPushMatrix()
    glTranslatef(0.35, -1.1, 0)
    glRotatef(leg_swing, 1, 0, 0)
    glRotatef(90, 1, 0, 0)
    draw_triangle_cylinder(0.25, 0.2, 1.6, 10, base_color)
    glPopMatrix()
    
    # Shield effect (wireframe sphere using points and lines)
    if player_has_shield:
        glPushMatrix()
        shield_pulse = 1.0 + 0.15 * math.sin(player_animation_phase * 2.5)
        glScalef(shield_pulse, shield_pulse, shield_pulse)
        
        # Draw shield wireframe circles using lines
        glLineWidth(2.5)
        glColor3f(0.0, 1.0, 0.0)
        
        # Horizontal circles at different heights
        for h in range(-2, 3):
            height = h * 0.5
            radius = math.sqrt(max(0, 2.2**2 - height**2))
            
            glBegin(GL_LINES)
            segments = 24
            for i in range(segments):
                theta1 = 2 * math.pi * i / segments
                theta2 = 2 * math.pi * (i + 1) / segments
                
                x1 = radius * math.cos(theta1)
                z1 = radius * math.sin(theta1)
                x2 = radius * math.cos(theta2)
                z2 = radius * math.sin(theta2)
                
                glVertex3f(x1, height, z1)
                glVertex3f(x2, height, z2)
            glEnd()
        
        # Vertical circles
        for i in range(4):
            angle = i * math.pi / 4
            
            glBegin(GL_LINES)
            segments = 24
            for j in range(segments):
                theta1 = 2 * math.pi * j / segments
                theta2 = 2 * math.pi * (j + 1) / segments
                
                y1 = 2.2 * math.sin(theta1)
                r1 = 2.2 * math.cos(theta1)
                y2 = 2.2 * math.sin(theta2)
                r2 = 2.2 * math.cos(theta2)
                
                x1 = r1 * math.cos(angle)
                z1 = r1 * math.sin(angle)
                x2 = r2 * math.cos(angle)
                z2 = r2 * math.sin(angle)
                
                glVertex3f(x1, y1, z1)
                glVertex3f(x2, y2, z2)
            glEnd()
        
        glLineWidth(1.0)
        glPopMatrix()
    
    glPopMatrix()

def draw_heart(x, y, size, color):
    """Draw a heart shape using triangles for HUD."""
    glPushMatrix()
    glTranslatef(x, y, 0)
    glScalef(size, size, size)
    
    glBegin(GL_TRIANGLES)
    glColor3f(*color)
    
    # Heart shape approximation (10 triangles)
    # Center triangle
    glVertex3f(0, -0.3, 0)
    glVertex3f(-0.3, 0.1, 0)
    glVertex3f(0.3, 0.1, 0)
    
    # Left lobe
    glVertex3f(-0.3, 0.1, 0)
    glVertex3f(-0.5, 0.3, 0)
    glVertex3f(-0.3, 0.4, 0)
    
    glVertex3f(-0.3, 0.1, 0)
    glVertex3f(-0.3, 0.4, 0)
    glVertex3f(0, 0.3, 0)
    
    # Right lobe
    glVertex3f(0.3, 0.1, 0)
    glVertex3f(0.3, 0.4, 0)
    glVertex3f(0.5, 0.3, 0)
    
    glVertex3f(0.3, 0.1, 0)
    glVertex3f(0, 0.3, 0)
    glVertex3f(0.3, 0.4, 0)
    
    # Bottom point
    glVertex3f(0, -0.3, 0)
    glVertex3f(-0.15, -0.1, 0)
    glVertex3f(0, -0.1, 0)
    
    glVertex3f(0, -0.3, 0)
    glVertex3f(0, -0.1, 0)
    glVertex3f(0.15, -0.1, 0)
    
    glEnd()
    glPopMatrix()

# =============================================================================
# ENVIRONMENT RENDERING
# =============================================================================

def draw_environment():
    """Draw the complete cyberpunk environment."""
    global total_distance, environment_stars, environment_buildings, floating_platforms
    
    # 2. SKY GRADIENT (Using large triangles)
    glDisable(GL_DEPTH_TEST)
    glBegin(GL_TRIANGLES)
    
    # Top half (darker)
    glColor3f(*COL_DARK_VOID)
    glVertex3f(-500, 300, -500)
    glVertex3f(500, 300, -500)
    glColor3f(*COL_LIGHTER_SKY)
    glVertex3f(0, 0, -500)
    
    # Bottom half (lighter)
    glColor3f(*COL_LIGHTER_SKY)
    glVertex3f(-500, 0, -500)
    glVertex3f(500, 0, -500)
    glVertex3f(0, 0, -500)
    
    glEnd()
    glEnable(GL_DEPTH_TEST)
    
    # 3. INFINITE GRID FLOOR
    draw_grid_floor()
    
    # 4. LANE DIVIDERS
    draw_lane_dividers()
    
    # 5. SIDE WALLS
    draw_side_walls()
    
    # 6. BACKGROUND BUILDINGS
    for building in environment_buildings:
        draw_triangle_cube(building['x'], building['height'] / 2, building['z'],
                          building['width'], building['color'])
    
    # 7. FLOATING PLATFORMS
    for platform in floating_platforms:
        glPushMatrix()
        glTranslatef(platform['x'], platform['y'], platform['z'])
        glRotatef(platform['rot'], 0, 1, 0)
        draw_triangle_cube(0, 0, 0, platform['size'], platform['color'])
        glPopMatrix()

def draw_grid_floor():
    """Draw scrolling neon grid floor."""
    global total_distance, current_speed
    
    # Dynamic color based on speed
    speed_ratio = current_speed / MAX_SPEED
    if speed_ratio < 0.25:
        grid_color = COL_NEON_PURPLE
    elif speed_ratio < 0.5:
        grid_color = color_lerp(COL_NEON_PURPLE, COL_NEON_PINK, (speed_ratio - 0.25) * 4)
    elif speed_ratio < 0.75:
        grid_color = color_lerp(COL_NEON_PINK, COL_NEON_CYAN, (speed_ratio - 0.5) * 4)
    else:
        grid_color = color_lerp(COL_NEON_CYAN, COL_NEON_BLUE, (speed_ratio - 0.75) * 4)
    
    # Grid scrolling offset
    grid_offset = total_distance % 20
    
    glLineWidth(2.5)
    glBegin(GL_LINES)
    
    # Longitudinal lines (along track)
    for x in range(-4, 5):
        x_pos = x * LANE_WIDTH
        fade_factor = 1.0 - abs(x) / 5.0
        glColor3f(grid_color[0] * fade_factor, 
                 grid_color[1] * fade_factor, 
                 grid_color[2] * fade_factor)
        glVertex3f(x_pos, 0, 50)
        glVertex3f(x_pos, 0, -600)
    
    # Lateral lines (perpendicular to track)
    for z in range(0, 650, 20):
        z_pos = 50 - z + grid_offset
        dist_fade = 1.0 - abs(z_pos + 200) / 600.0
        dist_fade = max(0.0, dist_fade)
        
        glColor3f(grid_color[0] * dist_fade, 
                 grid_color[1] * dist_fade, 
                 grid_color[2] * dist_fade)
        
        if z_pos > -600:
            glVertex3f(-60, 0, z_pos)
            glVertex3f(60, 0, z_pos)
    
    glEnd()
    glLineWidth(1.0)

def draw_lane_dividers():
    """Draw bright cyan lane dividing lines."""
    glLineWidth(3.0)
    glBegin(GL_LINES)
    glColor3f(*COL_NEON_CYAN)
    
    # Left divider
    glVertex3f(-LANE_WIDTH, 0.1, 50)
    glVertex3f(-LANE_WIDTH, 0.1, -600)
    
    # Right divider
    glVertex3f(LANE_WIDTH, 0.1, 50)
    glVertex3f(LANE_WIDTH, 0.1, -600)
    
    glEnd()
    glLineWidth(1.0)

def draw_side_walls():
    """Draw pulsating red boundary walls."""
    pulse = 1.0 + 0.1 * math.sin(time.time() * 2)
    wall_height = 10.0 * pulse
    
    # Left wall
    glPushMatrix()
    glTranslatef(-50, wall_height / 2, -300)
    glScalef(2, wall_height, 600)
    draw_triangle_cube(0, 0, 0, 1.0, COL_BARRIER_RED)
    glPopMatrix()
    
    # Right wall
    glPushMatrix()
    glTranslatef(50, wall_height / 2, -300)
    glScalef(2, wall_height, 600)
    draw_triangle_cube(0, 0, 0, 1.0, COL_BARRIER_RED)
    glPopMatrix()

# =============================================================================
# GAME OBJECTS RENDERING
# =============================================================================

def draw_obstacles():
    """Draw all obstacle types."""
    for obs in obstacles:
        if obs['type'] == 'barrier':
            # Red glowing cuboid barrier
            draw_triangle_cube(obs['x'], 2.5, obs['z'], 4.5, COL_BARRIER_RED)
            
            # Health indicator (small cubes on top)
            for i in range(obs['hp']):
                glPushMatrix()
                glTranslatef(obs['x'] - 1 + i * 1, 5.5, obs['z'])
                draw_triangle_cube(0, 0, 0, 0.4, COL_WHITE)
                glPopMatrix()
        
        elif obs['type'] == 'spike':
            # Rotating spike cone
            glPushMatrix()
            glTranslatef(obs['x'], 0, obs['z'])
            glRotatef(obs.get('rot', 0), 0, 1, 0)
            glRotatef(-90, 1, 0, 0)
            draw_triangle_cone(1.2, 4.0, 12, COL_NEON_ORANGE)
            glPopMatrix()
        
        elif obs['type'] == 'beam':
            # Horizontal rotating cylinder
            glPushMatrix()
            glTranslatef(obs['x'], 2.0, obs['z'])
            glRotatef(obs.get('rot', 0), 0, 0, 1)
            glRotatef(90, 0, 1, 0)
            draw_triangle_cylinder(1.0, 1.0, 14.0, 12, COL_GRAY)
            
            # Glowing ends
            glTranslatef(0, 0, 7)
            draw_triangle_sphere(1.2, 8, 8, COL_WARNING)
            glTranslatef(0, 0, -14)
            draw_triangle_sphere(1.2, 8, 8, COL_WARNING)
            glPopMatrix()
        
        elif obs['type'] == 'crusher':
            # Pulsating moving cube
            scale = 3.5 + 0.8 * math.sin(time.time() * 4)
            draw_triangle_cube(obs['x'], 2.5, obs['z'], scale, COL_NEON_PINK)
        
        elif obs['type'] == 'hazard':
            # Bouncing sphere
            glPushMatrix()
            glTranslatef(obs['x'], obs['y'], obs['z'])
            scale = obs.get('scale', 1.0)
            glScalef(scale, scale, scale)
            draw_triangle_sphere(1.0, 12, 12, COL_NEON_PURPLE)
            glPopMatrix()

def draw_collectibles():
    """Draw all power-up collectibles."""
    for col in collectibles:
        glPushMatrix()
        glTranslatef(col['x'], col['y'], col['z'])
        glRotatef(col['rot'], 0, 1, 0)
        
        # Pulsating scale
        pulse = 1.0 + 0.2 * math.sin(col['rot'] * 0.05)
        glScalef(pulse, pulse, pulse)
        
        # Determine color and shape based on type
        if col['type'] == 'gem_green':
            draw_triangle_sphere(0.6, 10, 10, COL_NEON_GREEN)
        elif col['type'] == 'gem_blue':
            draw_triangle_sphere(0.7, 10, 10, COL_NEON_BLUE)
        elif col['type'] == 'gem_purple':
            draw_triangle_sphere(0.8, 10, 10, COL_NEON_PURPLE)
        elif col['type'] == 'gem_gold':
            draw_triangle_sphere(1.0, 12, 12, COL_GOLD)
        elif col['type'] == 'shield':
            # Shield: Large green sphere with cube frame
            draw_triangle_sphere(1.0, 12, 12, COL_NEON_GREEN)
            # Add wireframe cube using lines for shield effect
            glPushMatrix()
            glScalef(1.3, 1.3, 1.3)
            # Draw cube outline with lines
            s = 0.5
            glLineWidth(2.0)
            glBegin(GL_LINES)
            glColor3f(*COL_NEON_CYAN)
            # Bottom square
            glVertex3f(-s, -s, -s); glVertex3f(s, -s, -s)
            glVertex3f(s, -s, -s); glVertex3f(s, -s, s)
            glVertex3f(s, -s, s); glVertex3f(-s, -s, s)
            glVertex3f(-s, -s, s); glVertex3f(-s, -s, -s)
            # Top square
            glVertex3f(-s, s, -s); glVertex3f(s, s, -s)
            glVertex3f(s, s, -s); glVertex3f(s, s, s)
            glVertex3f(s, s, s); glVertex3f(-s, s, s)
            glVertex3f(-s, s, s); glVertex3f(-s, s, -s)
            # Vertical lines
            glVertex3f(-s, -s, -s); glVertex3f(-s, s, -s)
            glVertex3f(s, -s, -s); glVertex3f(s, s, -s)
            glVertex3f(s, -s, s); glVertex3f(s, s, s)
            glVertex3f(-s, -s, s); glVertex3f(-s, s, s)
            glEnd()
            glLineWidth(1.0)
            glPopMatrix()
        elif col['type'] == 'speed':
            # Speed: Yellow cylinder with multiple rings
            glRotatef(90, 1, 0, 0)
            draw_triangle_cylinder(0.5, 0.5, 1.2, 10, COL_NEON_YELLOW)
            # Add rings for emphasis
            for i in range(3):
                glTranslatef(0, 0, 0.3)
                draw_triangle_cylinder(0.6, 0.6, 0.1, 8, COL_NEON_ORANGE)
        elif col['type'] == 'grenade':
            # Grenade: Stack of orange cubes
            draw_triangle_cube(0, 0, 0, 0.8, COL_NEON_ORANGE)
            glTranslatef(0, 0.5, 0)
            draw_triangle_cube(0, 0, 0, 0.6, COL_NEON_ORANGE)
            glTranslatef(0, 0.4, 0)
            draw_triangle_cube(0, 0, 0, 0.4, COL_NEON_ORANGE)
        
        glPopMatrix()

def draw_projectiles():
    """Draw player projectiles."""
    for proj in projectiles:
        glPushMatrix()
        glTranslatef(proj['x'], proj['y'], proj['z'])
        
        if proj['type'] == 'laser':
            # Small yellow sphere with trail
            draw_triangle_sphere(0.3, 8, 8, COL_NEON_YELLOW)
            
            # Trail effect
            for i in range(1, 4):
                glPushMatrix()
                glTranslatef(0, 0, i * 0.5)
                alpha = 1.0 - i * 0.25
                trail_col = tuple(c * alpha for c in COL_NEON_YELLOW)
                glScalef(0.8, 0.8, 0.8)
                draw_triangle_sphere(0.3, 6, 6, trail_col)
                glPopMatrix()
        
        elif proj['type'] == 'charge':
            # Large pulsating pink sphere
            pulse = 1.0 + 0.3 * math.sin(time.time() * 10)
            glScalef(pulse, pulse, pulse)
            draw_triangle_sphere(0.8, 12, 12, COL_NEON_PINK)
        
        elif proj['type'] == 'grenade':
            # Rotating orange cube
            glRotatef(proj.get('rot', 0), 1, 1, 0)
            draw_triangle_cube(0, 0, 0, 0.6, COL_NEON_ORANGE)
        
        glPopMatrix()

def draw_particles():
    """Draw particle effects."""
    for part in particles:
        glPushMatrix()
        glTranslatef(part['x'], part['y'], part['z'])
        
        # Fade based on remaining life
        life_ratio = part['life'] / 1.0
        size = life_ratio * 0.5
        color = tuple(c * life_ratio for c in part['color'])
        
        draw_triangle_cube(0, 0, 0, size, color)
        glPopMatrix()

# =============================================================================
# HUD RENDERING (2D OVERLAY)
# =============================================================================

def draw_hud():
    """Draw heads-up display."""
    global current_score, total_distance, player_health, player_grenades
    global game_state, combo_multiplier, player_cheat_mode, player_god_mode, current_speed
    global player_has_shield, player_shield_timer, player_speed_boost_active, player_speed_boost_timer
    
    # Switch to 2D orthographic projection
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    # Map to -1 to 1 coordinates
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glDisable(GL_DEPTH_TEST)
    
    def draw_text(x, y, text, color):
        glColor3f(*color)
        glRasterPos2f(x, y)
        for char in text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    
    # MENU STATE
    if game_state == "menu":
        # Title
        draw_text(-0.35, 0.3, "CYBER RUNNER 2077", COL_NEON_CYAN)
        draw_text(-0.25, 0.15, "NEON HORIZON", COL_NEON_PINK)
        
        # Instructions
        draw_text(-0.18, -0.1, "PRESS SPACE TO START", COL_WHITE)
        draw_text(-0.6, -0.3, "WASD: Move/Slide  |  SPACE: Jump  |  MOUSE: Shoot  |  F/1/2/3: Camera", COL_GRAY)
        draw_text(-0.4, -0.4, "C: God Mode  |  V: AI  |  B: Slow Motion  |  P: Pause", COL_GRAY)
        
        # Animated buttons (triangles)
        pulse = 0.8 + 0.2 * math.sin(time.time() * 3)
        glBegin(GL_TRIANGLES)
        glColor3f(COL_NEON_GREEN[0] * pulse, COL_NEON_GREEN[1] * pulse, COL_NEON_GREEN[2] * pulse)
        glVertex2f(-0.15, -0.55)
        glVertex2f(0.15, -0.55)
        glVertex2f(0.0, -0.65)
        glEnd()
    
    # LOADING STATE
    elif game_state == "loading":
        countdown_text = str(int(loading_countdown) + 1) if loading_countdown > 0 else "GO!"
        draw_text(-0.05, 0.1, countdown_text, COL_NEON_YELLOW)
        draw_text(-0.1, -0.1, "GET READY...", COL_WHITE)
    
    # PLAYING STATE
    elif game_state == "playing":
        # Combo multiplier (top-left)
        if combo_multiplier > 1:
            combo_text = f"x{combo_multiplier} COMBO!"
            draw_text(-0.95, 0.90, combo_text, COL_GOLD)
        
        # Distance (top-left)
        draw_text(-0.95, 0.82, f"DISTANCE: {int(total_distance)}m", COL_WHITE)
        
        # Health (top-center with hearts)
        draw_text(-0.15, 0.90, "HP:", COL_WARNING)
        for i in range(player_health):
            # Use triangle-based hearts
            heart_x = -0.05 + i * 0.15
            heart_y = 0.92
            glMatrixMode(GL_PROJECTION)
            glPushMatrix()
            glLoadIdentity()
            glMatrixMode(GL_MODELVIEW)
            glPushMatrix()
            glLoadIdentity()
            
            # Draw heart using triangles
            glBegin(GL_TRIANGLES)
            glColor3f(*COL_WARNING)
            x_base = heart_x
            y_base = heart_y
            
            # Simple heart approximation
            glVertex2f(x_base, y_base - 0.02)
            glVertex2f(x_base - 0.03, y_base)
            glVertex2f(x_base + 0.03, y_base)
            
            glVertex2f(x_base - 0.03, y_base)
            glVertex2f(x_base - 0.04, y_base + 0.02)
            glVertex2f(x_base - 0.02, y_base + 0.02)
            
            glVertex2f(x_base + 0.03, y_base)
            glVertex2f(x_base + 0.02, y_base + 0.02)
            glVertex2f(x_base + 0.04, y_base + 0.02)
            glEnd()
            
            glPopMatrix()
            glMatrixMode(GL_PROJECTION)
            glPopMatrix()
            glMatrixMode(GL_MODELVIEW)
        
        # Grenades (top-right)
        draw_text(0.70, 0.90, f"GRENADES: {player_grenades}/{MAX_GRENADES}", COL_NEON_ORANGE)
        
        # Score (top-right, below grenades) - PERMANENT DISPLAY
        draw_text(0.70, 0.82, f"SCORE: {int(current_score)}", COL_NEON_CYAN)
        
        # Speed indicator (bottom-right bar)
        speed_ratio = current_speed / MAX_SPEED
        bar_width = speed_ratio * 0.3
        bar_color = color_lerp(COL_NEON_GREEN, COL_WARNING, speed_ratio)
        
        glBegin(GL_TRIANGLES)
        glColor3f(*bar_color)
        glVertex2f(0.65, -0.90)
        glVertex2f(0.65 + bar_width, -0.90)
        glVertex2f(0.65 + bar_width, -0.85)
        
        glVertex2f(0.65, -0.90)
        glVertex2f(0.65 + bar_width, -0.85)
        glVertex2f(0.65, -0.85)
        glEnd()
        
        draw_text(0.67, -0.93, f"SPEED: {int(speed_ratio * 100)}%", COL_WHITE)
        
        # Active power-up indicators (top-right below score)
        active_y = 0.74
        if player_has_shield:
            remaining = int(player_shield_timer)
            draw_text(0.70, active_y, f"SHIELD: {remaining}s", COL_NEON_GREEN)
            active_y -= 0.08
        
        if player_speed_boost_active:
            remaining = int(player_speed_boost_timer)
            draw_text(0.70, active_y, f"SPEED BOOST: {remaining}s", COL_NEON_YELLOW)
            active_y -= 0.08
        
        # Cheat mode indicator
        if player_cheat_mode:
            draw_text(-0.15, -0.85, "[CHEAT MODE ACTIVE]", COL_GOLD)
        
        # God mode (AI) indicator
        if player_god_mode:
            # Position it below cheat mode if both are active, otherwise same level
            y_pos = -0.92 if player_cheat_mode else -0.85
            draw_text(-0.15, y_pos, "[GOD MODE AI ACTIVE]", COL_NEON_CYAN)
        
        # Perfect dodge streak
        if player_perfect_dodge_count >= 5:
            draw_text(-0.2, -0.75, f"PERFECT DODGES: {player_perfect_dodge_count}", COL_NEON_CYAN)
        
        # On-screen messages (center of screen, large and visible)
        current_time = time.time()
        # Clean up old messages
        global on_screen_messages
        on_screen_messages = [(msg, t) for msg, t in on_screen_messages if current_time - t < MESSAGE_DISPLAY_DURATION]
        
        # Display recent messages (max 3, stacked vertically in center)
        for i, (msg, timestamp) in enumerate(on_screen_messages[-3:]):
            age = current_time - timestamp
            fade = 1.0 - (age / MESSAGE_DISPLAY_DURATION)  # Fade out over time
            y_offset = 0.4 - i * 0.12  # Stack messages vertically from top-center
            
            # All messages use WHITE color as requested
            base_col = COL_WHITE
            msg_color = (base_col[0] * fade, base_col[1] * fade, base_col[2] * fade)
            
            # Center the text approximately
            text_width = len(msg) * 0.015
            draw_text(-text_width/2, y_offset, msg, msg_color)
    
    # PAUSED STATE
    elif game_state == "paused":
        # Darken screen
        glBegin(GL_TRIANGLES)
        glColor3f(0.0, 0.0, 0.0)
        glVertex2f(-1, -1)
        glVertex2f(1, -1)
        glVertex2f(1, 1)
        glVertex2f(-1, -1)
        glVertex2f(1, 1)
        glVertex2f(-1, 1)
        glEnd()
        
        draw_text(-0.1, 0.1, "PAUSED", COL_NEON_CYAN)
        draw_text(-0.2, -0.1, "P: Resume  |  R: Restart  |  Q: Quit", COL_WHITE)
    
    # GAME OVER STATE
    elif game_state == "gameover":
        draw_text(-0.15, 0.2, "GAME OVER", COL_WARNING)
        draw_text(-0.25, 0.05, f"FINAL SCORE: {int(current_score)}", COL_WHITE)
        draw_text(-0.25, -0.1, f"DISTANCE: {int(total_distance)}m", COL_WHITE)
        draw_text(-0.3, -0.25, f"OBSTACLES DODGED: {stats_obstacles_dodged}", COL_NEON_CYAN)
        draw_text(-0.25, -0.4, f"GEMS COLLECTED: {stats_gems_collected}", COL_GOLD)
        draw_text(-0.25, -0.6, "PRESS R TO RESTART", COL_GRAY)
    
    # VICTORY STATE
    elif game_state == "victory":
        draw_text(-0.15, 0.3, "YOU WIN!", COL_GOLD)
        draw_text(-0.3, 0.15, f"FINAL SCORE: {int(current_score)}", COL_WHITE)
        draw_text(-0.25, 0.0, f"DISTANCE: {int(total_distance)}m", COL_WHITE)
        draw_text(-0.25, -0.15, "PRESS R TO RESTART", COL_GRAY)
        draw_text(-0.3, -0.3, "PRESS C TO CONTINUE", COL_NEON_GREEN)
    
    # Restore 3D projection
    glEnable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()

# =============================================================================
# UPDATE LOGIC
# =============================================================================

def update_game():
    """Main game update loop."""
    global last_time, game_state, current_speed, total_distance, current_score
    global difficulty_level, last_speed_up_score, loading_countdown, obstacle_spawn_rate
    global combo_multiplier, combo_last_collect_time, player_perfect_dodge_count
    global player_shield_timer, player_has_shield, player_speed_boost_timer, player_speed_boost_active
    
    current_time = time.time()
    dt = current_time - last_time
    last_time = current_time
    
    # Cap delta time to prevent huge jumps
    if dt > 0.1:
        dt = 0.1
    
    # Apply slow motion cheat
    if slow_motion and game_state == "playing":
        dt *= 0.5
    
    # LOADING STATE
    if game_state == "loading":
        loading_countdown -= dt
        if loading_countdown <= 0:
            game_state = "playing"
            print("[START] Game Started!")
        return
    
    # MENU/PAUSED/GAMEOVER - Only animate environment
    if game_state in ["menu", "paused", "gameover", "victory"]:
        update_environment(dt * 20.0)
        update_floating_platforms(dt)
        return
    
    # PLAYING STATE
    if game_state == "playing":
        # Update power-up timers
        if player_has_shield:
            player_shield_timer -= dt
            if player_shield_timer <= 0:
                player_has_shield = False
                player_shield_timer = 0
                show_message("Shield Expired!")
                print("[SHIELD] Shield expired!")
        
        if player_speed_boost_active:
            player_speed_boost_timer -= dt
            if player_speed_boost_timer <= 0:
                player_speed_boost_active = False
                player_speed_boost_timer = 0
                show_message("Speed Boost Expired!")
                print("[SPEED] Speed boost expired!")
        
        # Speed progression (faster with speed boost)
        speed_multiplier = 1.5 if player_speed_boost_active else 1.0
        current_speed = min(MAX_SPEED * speed_multiplier, current_speed + dt * SPEED_INCREMENT)
        distance_delta = current_speed * dt
        total_distance += distance_delta
        
        # Score based on distance
        score_delta = distance_delta * 0.1
        if slow_motion:
            score_delta *= 0.5
        current_score += score_delta
        
        # Difficulty scaling every 500 points
        if int(current_score / 500) > int(last_speed_up_score / 500):
            difficulty_level += 1
            obstacle_spawn_rate = min(0.08, obstacle_spawn_rate + 0.008)
            last_speed_up_score = current_score
            print(f"[SPEED UP] Level {difficulty_level}! Speed: {int(current_speed)}")
        
        # Victory condition
        if current_score >= VICTORY_SCORE and game_state == "playing":
            game_state = "victory"
            print("[VICTORY] You Win!")
            return
        
        # Update game systems
        update_player(dt)
        update_environment(distance_delta)
        update_obstacles(dt, distance_delta)
        update_collectibles(dt, distance_delta)
        update_projectiles(dt)
        update_particles(dt)
        update_floating_platforms(dt)
        
        # Spawning logic
        if len(obstacles) < 8 and random.random() < obstacle_spawn_rate:
            spawn_obstacle()
        
        if len(collectibles) < 6 and random.random() < 0.05:
            spawn_collectible()
        
        # God mode (AI auto-runner)
        if player_god_mode:
            update_ai()
        
        # Collision detection
        check_collisions()
        
        # Combo timeout
        if time.time() - combo_last_collect_time > COMBO_TIMEOUT:
            combo_multiplier = 1

def update_player(dt):
    """Update player physics and animation."""
    global player_x, player_y, player_lane_index, player_velocity_y
    global player_is_jumping, player_is_sliding, player_slide_timer
    global player_animation_phase, player_damage_flash
    
    # Lane interpolation (smooth movement)
    target_x = (player_lane_index - 1) * LANE_WIDTH
    player_x += (target_x - player_x) * 12.0 * dt
    
    # Jump physics
    if player_is_jumping:
        player_y += player_velocity_y * dt
        player_velocity_y += GRAVITY * dt
        
        if player_y <= 0:
            player_y = 0
            player_is_jumping = False
            player_velocity_y = 0
    
    # Slide timer
    if player_is_sliding:
        player_slide_timer -= dt
        if player_slide_timer <= 0:
            player_is_sliding = False
    
    # Animation phase for running
    player_animation_phase += dt * 12.0
    
    # Damage flash decay
    if player_damage_flash > 0:
        player_damage_flash -= dt * 3.0
        player_damage_flash = max(0, player_damage_flash)

def update_environment(distance_delta):
    """Update scrolling environment."""
    global environment_buildings
    
    # Move buildings toward player
    for building in environment_buildings:
        building['z'] += distance_delta
    
    # Remove buildings behind camera
    environment_buildings = [b for b in environment_buildings if b['z'] < 100]
    
    # Spawn new buildings
    while len(environment_buildings) < 40:
        spawn_building()

def spawn_building(initial=False):
    """Spawn a background building."""
    z_pos = random.uniform(-200, -800) if initial else random.uniform(-800, -900)
    x_pos = random.choice([-1, 1]) * random.uniform(60, 150)
    
    building = {
        'x': x_pos,
        'z': z_pos,
        'width': random.uniform(15, 40),
        'height': random.uniform(30, 120),
        'color': (0.1, 0.1, random.uniform(0.2, 0.5))
    }
    environment_buildings.append(building)

def update_floating_platforms(dt):
    """Update floating platforms."""
    global floating_platforms
    
    for platform in floating_platforms:
        platform['rot'] += 30 * dt
    
    # Keep count stable
    if len(floating_platforms) < 20:
        spawn_floating_platform()

def spawn_floating_platform(initial=False):
    """Spawn a floating platform."""
    z_pos = random.uniform(-200, -600) if initial else random.uniform(-600, -700)
    
    platform = {
        'x': random.uniform(-80, 80),
        'y': random.uniform(15, 40),
        'z': z_pos,
        'size': random.uniform(2, 5),
        'rot': random.uniform(0, 360),
        'color': (random.uniform(0.2, 0.4), random.uniform(0.2, 0.4), random.uniform(0.4, 0.6))
    }
    floating_platforms.append(platform)

def update_obstacles(dt, distance_delta):
    """Update all obstacles."""
    global obstacles, stats_obstacles_dodged, player_perfect_dodge_count
    
    for obs in obstacles[:]:
        # Move toward player
        obs['z'] += distance_delta
        
        # Type-specific updates
        if obs['type'] == 'spike':
            obs['rot'] = obs.get('rot', 0) + 45 * dt
        
        elif obs['type'] == 'beam':
            obs['rot'] = obs.get('rot', 0) + 90 * dt
        
        elif obs['type'] == 'crusher':
            # Move left-right
            obs['x'] += obs['dir'] * 18.0 * dt
            if abs(obs['x']) > LANE_WIDTH * 1.5:
                obs['dir'] *= -1
        
        elif obs['type'] == 'hazard':
            # Bouncing motion
            obs['y'] = 2.0 + 1.5 * abs(math.sin(time.time() * 2 + obs.get('phase', 0)))
            obs['scale'] = 0.8 + 0.4 * math.sin(time.time() * 3)
        
        # Remove if behind player
        if obs['z'] > 10:
            obstacles.remove(obs)
            stats_obstacles_dodged += 1
            player_perfect_dodge_count += 1

def spawn_obstacle():
    """Spawn a random obstacle."""
    lane = random.randint(0, 2)
    x = (lane - 1) * LANE_WIDTH
    z = -600
    
    # Available types based on difficulty
    types = ['barrier']
    if total_distance > 500:
        types.append('spike')
    if total_distance > 1000:
        types.extend(['beam', 'hazard'])
    if total_distance > 1500:
        types.append('crusher')
    
    obs_type = random.choice(types)
    
    obs = {
        'type': obs_type,
        'x': x,
        'y': 0,
        'z': z,
        'hp': 3 if obs_type == 'barrier' else 1,
        'dir': random.choice([-1, 1]),  # For crusher
        'rot': random.uniform(0, 360),  # For rotation
        'phase': random.uniform(0, 6.28)  # For bouncing
    }
    obstacles.append(obs)

def update_collectibles(dt, distance_delta):
    """Update power-ups."""
    for col in collectibles[:]:
        col['z'] += distance_delta
        col['rot'] += 120 * dt
        
        # Remove if behind
        if col['z'] > 10:
            collectibles.remove(col)

def spawn_collectible():
    """Spawn a random power-up."""
    global shield_spawn_count, speed_spawn_count, grenade_spawn_count
    
    lane = random.randint(0, 2)
    x = (lane - 1) * LANE_WIDTH
    z = -600
    y = 2.5
    
    # Guaranteed power-ups in first 2000m - 2 of each type
    if total_distance < 2000:
        # Check which power-ups still need to spawn
        needed_powerups = []
        if shield_spawn_count < 2:
            needed_powerups.append('shield')
        if speed_spawn_count < 2:
            needed_powerups.append('speed')
        if grenade_spawn_count < 2:
            needed_powerups.append('grenade')
        
        # If we still need to spawn guaranteed power-ups, prioritize them heavily
        if needed_powerups and random.random() < 0.6:  # 60% chance to spawn needed power-up
            col_type = random.choice(needed_powerups)
            # Increment counter
            if col_type == 'shield':
                shield_spawn_count += 1
                print(f"[SPAWN] Shield {shield_spawn_count}/2 spawned at distance {int(total_distance)}m")
            elif col_type == 'speed':
                speed_spawn_count += 1
                print(f"[SPAWN] Speed boost {speed_spawn_count}/2 spawned at distance {int(total_distance)}m")
            elif col_type == 'grenade':
                grenade_spawn_count += 1
                print(f"[SPAWN] Grenade pack {grenade_spawn_count}/2 spawned at distance {int(total_distance)}m")
        else:
            # Normal random selection for early game
            r = random.random()
            if r < 0.20:
                col_type = 'gem_green'
            elif r < 0.40:
                col_type = 'gem_blue'
            elif r < 0.55:
                col_type = 'gem_purple'
            elif r < 0.70:
                col_type = 'gem_gold'
            elif r < 0.80 and shield_spawn_count < 2:
                col_type = 'shield'
                shield_spawn_count += 1
            elif r < 0.90 and speed_spawn_count < 2:
                col_type = 'speed'
                speed_spawn_count += 1
            elif grenade_spawn_count < 2:
                col_type = 'grenade'
                grenade_spawn_count += 1
            else:
                col_type = 'gem_blue'  # Default to gem if all power-ups spawned
    else:
        # After 2000m - normal random spawning
        r = random.random()
        if r < 0.15:
            col_type = 'gem_green'
        elif r < 0.30:
            col_type = 'gem_blue'
        elif r < 0.42:
            col_type = 'gem_purple'
        elif r < 0.52:
            col_type = 'gem_gold'
        elif r < 0.68:
            col_type = 'shield'
        elif r < 0.84:
            col_type = 'speed'
        else:
            col_type = 'grenade'
    
    col = {
        'type': col_type,
        'x': x,
        'y': y,
        'z': z,
        'rot': 0
    }
    collectibles.append(col)
    print(f"[COLLECTIBLE] Spawned {col_type} at lane {lane}, x={x:.1f}, y={y:.1f}, z={z:.1f}")

def update_projectiles(dt):
    """Update player projectiles."""
    for proj in projectiles[:]:
        # Move forward (away from player)
        proj['z'] -= 180.0 * dt
        proj['life'] -= dt
        
        # Grenade physics
        if proj['type'] == 'grenade':
            proj['y'] += proj['vy'] * dt
            proj['vy'] += GRAVITY * dt
            proj['rot'] = proj.get('rot', 0) + 360 * dt
            
            # Explode on ground
            if proj['y'] <= 0:
                spawn_explosion(proj['x'], 0, proj['z'], COL_NEON_ORANGE, 15)
                projectiles.remove(proj)
                continue
        
        # Remove if expired
        if proj['life'] <= 0 or proj['z'] < -700:
            if proj in projectiles:
                projectiles.remove(proj)

def update_particles(dt):
    """Update particle effects."""
    for part in particles[:]:
        part['x'] += part['vx'] * dt
        part['y'] += part['vy'] * dt
        part['z'] += part['vz'] * dt
        part['vy'] += GRAVITY * dt * 0.5  # Lighter gravity
        part['life'] -= dt
        
        if part['life'] <= 0:
            particles.remove(part)

def spawn_explosion(x, y, z, color, count=10):
    """Create explosion particle effect."""
    for i in range(count):
        part = {
            'x': x,
            'y': y,
            'z': z,
            'vx': random.uniform(-15, 15),
            'vy': random.uniform(10, 25),
            'vz': random.uniform(-15, 15),
            'life': random.uniform(0.5, 1.2),
            'color': color
        }
        particles.append(part)

def update_ai():
    """Simple AI for auto-runner cheat."""
    global player_lane_index, player_is_jumping, player_velocity_y, player_is_sliding, player_slide_timer
    
    # Find nearest obstacle in current lane
    my_x = (player_lane_index - 1) * LANE_WIDTH
    nearest_dist = 999
    threat = None
    
    for obs in obstacles:
        if obs['z'] < 0 and obs['z'] > -150:
            if abs(obs['x'] - my_x) < 6:
                dist = abs(obs['z'])
                if dist < nearest_dist:
                    nearest_dist = dist
                    threat = obs
    
    # React to threat
    if threat and nearest_dist < 50:
        if threat['type'] in ['spike', 'hazard']:
            # Jump over
            if not player_is_jumping and player_y == 0:
                player_is_jumping = True
                player_velocity_y = JUMP_FORCE
        elif threat['type'] == 'beam':
            # Slide under
            if not player_is_sliding:
                player_is_sliding = True
                player_slide_timer = 1.0
        else:
            # Change lane
            safe_lanes = [0, 1, 2]
            for obs in obstacles:
                if obs['z'] < 0 and obs['z'] > -100:
                    obs_lane = round((obs['x'] / LANE_WIDTH) + 1)
                    if obs_lane in safe_lanes:
                        safe_lanes.remove(obs_lane)
            
            if safe_lanes and player_lane_index not in safe_lanes:
                player_lane_index = random.choice(safe_lanes)
    
    # Collect power-ups
    for col in collectibles:
        if col['z'] < 0 and col['z'] > -100:
            col_lane = round((col['x'] / LANE_WIDTH) + 1)
            if col_lane != player_lane_index and abs(col['z']) > 30:
                player_lane_index = col_lane
                break

def check_collisions():
    """Check all collision interactions."""
    global player_health, game_state, player_has_shield, current_score
    global player_grenades, combo_multiplier, combo_last_collect_time
    global stats_gems_collected, player_damage_flash, obstacles
    global collectibles, projectiles, player_perfect_dodge_count
    global player_shield_timer, player_speed_boost_active, player_speed_boost_timer
    
    # Player bounding box
    player_box = {
        'x': player_x,
        'y': player_y,
        'z': player_z,
        'radius': 1.5
    }
    
    # 1. PLAYER vs OBSTACLES
    for obs in obstacles[:]:
        dx = abs(obs['x'] - player_box['x'])
        dz = abs(obs['z'] - player_box['z'])
        
        if dx < 3.0 and dz < 3.0:
            # Specific collision rules
            collision = True
            
            # General jump check - if player is high enough, they clear most obstacles
            if player_y > 4.0 and obs['type'] != 'beam':
                collision = False  # Jumped over
            elif obs['type'] == 'spike' and player_y > 3.0:
                collision = False  # Lower jump can clear spikes
            elif obs['type'] == 'beam' and player_is_sliding:
                collision = False  # Slid under beam
            elif obs['type'] == 'hazard':
                dy = abs(obs.get('y', 2.0) - player_y)
                if dy > 2.0:
                    collision = False
            
            if collision:
                if player_cheat_mode:
                    # Cheat mode: destroy obstacle
                    obstacles.remove(obs)
                    spawn_explosion(obs['x'], 2, obs['z'], COL_GOLD, 12)
                    current_score += 50
                elif player_has_shield:
                    # Shield absorbs hit
                    player_has_shield = False
                    player_shield_timer = 0
                    obstacles.remove(obs)
                    spawn_explosion(obs['x'], 2, obs['z'], COL_NEON_GREEN, 12)
                    show_message("SHIELD DESTROYED! No Damage Taken")
                    print("[SHIELD] Shield absorbed damage!")
                else:
                    # Take damage
                    player_health -= 1
                    player_damage_flash = 1.0
                    player_perfect_dodge_count = 0
                    obstacles.remove(obs)
                    spawn_explosion(player_x, player_y + 1, player_z, COL_WARNING, 15)
                    print(f"[HIT] Health: {player_health}/3")
                    
                    if player_health <= 0:
                        game_state = "gameover"
                        print("[GAME OVER]")
                        return
    
    # 2. PROJECTILES vs OBSTACLES
    for proj in projectiles[:]:
        for obs in obstacles[:]:
            dist = distance_3d(proj['x'], proj['y'], proj['z'], 
                              obs['x'], obs.get('y', 2), obs['z'])
            
            if dist < 4.0:
                # Determine damage
                if proj['type'] == 'charge':
                    damage = 10  # One-shot kill
                elif proj['type'] == 'grenade':
                    damage = 5
                else:
                    damage = 1
                
                obs['hp'] -= damage
                
                # Remove projectile (except charge shot persists)
                if proj['type'] != 'charge' and proj in projectiles:
                    projectiles.remove(proj)
                
                # Destroy obstacle if health depleted
                if obs['hp'] <= 0:
                    if obs in obstacles:
                        obstacles.remove(obs)
                    current_score += 20 if obs['type'] == 'barrier' else 15
                    spawn_explosion(obs['x'], 2, obs['z'], COL_NEON_PINK, 10)
                    print(f"[DESTROYED] +{20 if obs['type'] == 'barrier' else 15} points")
                
                break
    
    # 3. PLAYER vs COLLECTIBLES
    for col in collectibles[:]:
        dist = distance_3d(player_x, player_y, player_z, 
                          col['x'], col['y'], col['z'])
        
        # Debug: Print positions when collectible is near
        if col['z'] > -50 and col['z'] < 50:
            print(f"[DEBUG] Collectible {col['type']} at x={col['x']:.1f}, y={col['y']:.1f}, z={col['z']:.1f} | Player at x={player_x:.1f}, y={player_y:.1f}, z={player_z:.1f} | Distance={dist:.2f}")
        
        # INCREASED collision radius from 2.5 to 5.0 for better detection
        if dist < 5.0:
            collectibles.remove(col)
            stats_gems_collected += 1
            
            print(f"[COLLECT] *** COLLECTED {col['type']} *** at distance {dist:.2f} | Current score before: {int(current_score)}")
            
            # Apply effects with specific colors for particles
            if col['type'] == 'gem_green':
                points = 10 * combo_multiplier
                current_score += points
                update_combo()
                show_message(f"Green Gem is collected! +{points}pts")
                spawn_explosion(col['x'], col['y'], col['z'], COL_NEON_GREEN, 12)
                print(f"[SCORE] Green gem +{points} points | New score: {int(current_score)}")
            elif col['type'] == 'gem_blue':
                points = 25 * combo_multiplier
                current_score += points
                update_combo()
                show_message(f"Blue Gem is collected! +{points}pts")
                spawn_explosion(col['x'], col['y'], col['z'], COL_NEON_BLUE, 12)
                print(f"[SCORE] Blue gem +{points} points | New score: {int(current_score)}")
            elif col['type'] == 'gem_purple':
                points = 50 * combo_multiplier
                current_score += points
                update_combo()
                show_message(f"Purple Gem is collected! +{points}pts")
                spawn_explosion(col['x'], col['y'], col['z'], COL_NEON_PURPLE, 12)
                print(f"[SCORE] *** PURPLE GEM *** +{points} points | New score: {int(current_score)}")
                print(f"[MESSAGE] Showing message: Purple Gem is collected! +{points}pts")
            elif col['type'] == 'gem_gold':
                points = 100 * combo_multiplier
                current_score += points
                update_combo()
                show_message(f"Gold Gem is collected! +{points}pts")
                spawn_explosion(col['x'], col['y'], col['z'], COL_GOLD, 15)
                print(f"[SCORE] Gold gem +{points} points | New score: {int(current_score)}")
            elif col['type'] == 'shield':
                current_score += 75  # Shield awards 75 points
                player_has_shield = True
                player_shield_timer = SHIELD_DURATION
                show_message("Shield is collected! +75pts")
                spawn_explosion(col['x'], col['y'], col['z'], COL_NEON_GREEN, 15)
                print(f"[SHIELD] *** SHIELD ACTIVATED *** +75 points | New score: {int(current_score)}")
            elif col['type'] == 'speed':
                current_score += 60  # Speed boost awards 60 points
                player_speed_boost_active = True
                player_speed_boost_timer = SPEED_BOOST_DURATION
                show_message("Speed Boost is collected! +60pts")
                spawn_explosion(col['x'], col['y'], col['z'], COL_NEON_YELLOW, 15)
                print(f"[SPEED] Speed boost activated! +60 points | New score: {int(current_score)}")
            elif col['type'] == 'grenade':
                current_score += 50  # Grenade pack awards 50 points
                player_grenades = min(MAX_GRENADES, player_grenades + 3)
                show_message(f"Grenade Pack is collected! +50pts")
                spawn_explosion(col['x'], col['y'], col['z'], COL_NEON_ORANGE, 15)
                print(f"[GRENADE] Grenade pack collected! +50 points | New score: {int(current_score)}")
    
    # 4. PERFECT DODGE BONUS
    if player_perfect_dodge_count >= 10:
        current_score += 100
        show_message("PERFECT DODGE BONUS +100pts!")
        print("[BONUS] Perfect Dodge +100 points!")
        player_perfect_dodge_count = 0

def update_combo():
    """Update combo system."""
    global combo_multiplier, combo_last_collect_time
    
    time_since_last = time.time() - combo_last_collect_time
    
    if time_since_last < COMBO_TIMEOUT:
        if combo_multiplier == 1:
            combo_multiplier = 2
        elif combo_multiplier == 2:
            combo_multiplier = 3
        elif combo_multiplier == 3:
            combo_multiplier = 5
        print(f"[COMBO] x{combo_multiplier}")
    else:
        combo_multiplier = 1
    
    combo_last_collect_time = time.time()

# =============================================================================
# INPUT CALLBACKS
# =============================================================================

def handle_keyboard(key, x, y):
    """Handle keyboard input."""
    global player_lane_index, player_is_jumping, player_velocity_y
    global player_is_sliding, player_slide_timer, game_state
    global player_cheat_mode, player_god_mode, slow_motion, camera_mode
    global loading_countdown
    
    k = key.lower()
    
    # ESC - Quit
    if k == b'\x1b':
        sys.exit(0)
    
    # MENU STATE
    if game_state == "menu":
        if k == b' ':
            game_state = "loading"
            loading_countdown = 3.0
            print("[LOADING] Get ready...")
        return
    
    # GAME OVER / VICTORY STATE
    if game_state in ["gameover", "victory"]:
        if k == b'r':
            init_game()
            game_state = "loading"
            loading_countdown = 3.0
            print("[RESTART] Restarting game...")
        elif k == b'c' and game_state == "victory":
            game_state = "playing"
            print("[CONTINUE] Continuing after victory...")
        elif k == b'q' or k == b'm':
            init_game()
        return
    
    # PAUSED STATE
    if game_state == "paused":
        if k == b'p' or k == b'r':
            game_state = "playing"
            print("[RESUME] Game resumed")
        elif k == b'q':
            init_game()
        return
    
    # PLAYING STATE
    if game_state == "playing":
        # Movement
        if k == b'a' and player_lane_index > 0:
            player_lane_index -= 1
        elif k == b'd' and player_lane_index < 2:
            player_lane_index += 1
        elif k == b' ':
            if not player_is_jumping and player_y == 0:
                player_is_jumping = True
                player_velocity_y = JUMP_FORCE
        elif k == b's':
            if not player_is_sliding:
                player_is_sliding = True
                player_slide_timer = 1.0
        elif k == b'w':
            player_is_sliding = False
        
        # Game control
        elif k == b'p':
            game_state = "paused"
            print("[PAUSE] Game paused")
        elif k == b'r':
            init_game()
            game_state = "loading"
            loading_countdown = 3.0
        
        # Camera modes
        elif k == b'f':
            camera_mode = "first" if camera_mode != "first" else "third"
            print(f"[CAMERA] {camera_mode.upper()} person view")
        elif k == b'1':
            camera_mode = "side"
            print("[CAMERA] Side view")
        elif k == b'2':
            camera_mode = "top"
            print("[CAMERA] Top-down view")
        elif k == b'3':
            camera_mode = "cinematic"
            print("[CAMERA] Cinematic view")
        elif k == b'4':
            camera_mode = "third"
            print("[CAMERA] Third person view (default)")
        
        # Cheats
        elif k == b'c':
            player_cheat_mode = not player_cheat_mode
            print(f"[CHEAT] Cheat Mode: {'ON' if player_cheat_mode else 'OFF'}")
        elif k == b'v':
            player_god_mode = not player_god_mode
            print(f"[CHEAT] God Mode (AI): {'ON' if player_god_mode else 'OFF'}")
        elif k == b'b':
            slow_motion = not slow_motion
            print(f"[CHEAT] Slow Motion: {'ON' if slow_motion else 'OFF'}")

def handle_special_keys(key, x, y):
    """Handle special keys (arrow keys)."""
    global camera_offset_y, camera_rotation
    
    if game_state == "playing":
        if key == GLUT_KEY_UP:
            camera_offset_y += 2.0
        elif key == GLUT_KEY_DOWN:
            camera_offset_y -= 2.0
        elif key == GLUT_KEY_LEFT:
            camera_rotation += 10.0
        elif key == GLUT_KEY_RIGHT:
            camera_rotation -= 10.0

def handle_mouse(button, state, x, y):
    """Handle mouse input."""
    global player_charging, player_charge_start_time, projectiles, player_grenades
    
    if game_state != "playing":
        return
    
    # Left click - Laser/Charge shot
    if button == GLUT_LEFT_BUTTON:
        if state == GLUT_DOWN:
            player_charging = True
            player_charge_start_time = time.time()
        elif state == GLUT_UP:
            player_charging = False
            charge_duration = time.time() - player_charge_start_time
            
            # Determine projectile type
            if charge_duration > 1.0:
                proj_type = 'charge'
                print("[WEAPON] Charge shot!")
            else:
                proj_type = 'laser'
            
            # Create projectile
            proj = {
                'type': proj_type,
                'x': player_x + 0.8,
                'y': player_y + 1.5,
                'z': player_z - 2.0,
                'life': 4.0,
                'vy': 0
            }
            projectiles.append(proj)
    
    # Right click - Grenade
    elif button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        if player_grenades > 0 or player_cheat_mode:
            if not player_cheat_mode:
                player_grenades -= 1
            
            proj = {
                'type': 'grenade',
                'x': player_x,
                'y': player_y + 2.0,
                'z': player_z - 1.0,
                'vy': 18.0,
                'life': 5.0,
                'rot': 0
            }
            projectiles.append(proj)
            print(f"[WEAPON] Grenade launched! ({player_grenades} remaining)")

# =============================================================================
# RENDERING & CAMERA
# =============================================================================

def setup_camera():
    """Setup camera based on current mode."""
    global camera_mode, player_x, player_y, camera_offset_y
    global camera_rotation, camera_cinematic_angle
    
    if game_state == "menu":
        # Orbiting camera for menu
        t = time.time() * 0.3
        cam_x = 100 * math.sin(t)
        cam_y = 50
        cam_z = 100 * math.cos(t)
        gluLookAt(cam_x, cam_y, cam_z, 0, 0, -300, 0, 1, 0)
    
    elif game_state == "loading":
        # Static dramatic angle
        gluLookAt(0, 30, 40, 0, 5, -50, 0, 1, 0)
    
    elif game_state in ["playing", "paused"]:
        if camera_mode == "third":
            # Third-person chase camera
            cam_x = player_x * 0.7
            cam_y = 20.0 + camera_offset_y
            cam_z = player_z + 35.0
            
            # Apply rotation
            if camera_rotation != 0:
                angle = math.radians(camera_rotation)
                radius = 35.0
                cam_x += radius * math.sin(angle)
                cam_z += radius * (1 - math.cos(angle))
            
            look_x = player_x
            look_y = player_y + 3.0
            look_z = player_z - 30.0
            
            gluLookAt(cam_x, cam_y, cam_z, look_x, look_y, look_z, 0, 1, 0)
        
        elif camera_mode == "first":
            # First-person cockpit view
            gluLookAt(player_x, player_y + 1.8, player_z - 0.5,
                     player_x, player_y + 1.8, -500,
                     0, 1, 0)
        
        elif camera_mode == "side":
            # Side view (platform game style)
            gluLookAt(40, 15, player_z,
                     player_x, player_y + 2, player_z - 20,
                     0, 1, 0)
        
        elif camera_mode == "top":
            # Top-down view
            gluLookAt(player_x, 60, player_z + 10,
                     player_x, 0, player_z - 30,
                     0, 0, -1)
        
        elif camera_mode == "cinematic":
            # Orbiting cinematic camera
            camera_cinematic_angle += 0.01
            radius = 30.0
            cam_x = player_x + radius * math.sin(camera_cinematic_angle)
            cam_z = player_z + radius * math.cos(camera_cinematic_angle)
            cam_y = 25.0
            
            gluLookAt(cam_x, cam_y, cam_z,
                     player_x, player_y + 2, player_z - 20,
                     0, 1, 0)
    
    elif game_state in ["gameover", "victory"]:
        # Elevated dramatic angle
        gluLookAt(0, 40, 60, 0, 5, -50, 0, 1, 0)

def display():
    """Main display callback."""
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    
    # Setup camera
    setup_camera()
    
    # Render scene
    draw_environment()
    
    if game_state != "menu":
        draw_robot_player()
    
    draw_obstacles()
    draw_collectibles()
    draw_projectiles()
    draw_particles()
    
    # Draw HUD (2D overlay)
    draw_hud()
    
    glutSwapBuffers()

def idle():
    """Idle callback for continuous updates."""
    update_game()
    glutPostRedisplay()

def reshape(width, height):
    """Handle window reshape."""
    if height == 0:
        height = 1
    
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60.0, float(width) / float(height), 0.1, 1000.0)
    glMatrixMode(GL_MODELVIEW)

# =============================================================================
# MAIN FUNCTION
# =============================================================================

def main():
    """Initialize and run the game."""
    # Initialize GLUT
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(WINDOW_TITLE)
    
    # OpenGL settings
    glClearColor(*COL_DARK_VOID, 1.0)
    glEnable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60.0, float(WINDOW_WIDTH) / float(WINDOW_HEIGHT), 0.1, 1000.0)
    glMatrixMode(GL_MODELVIEW)
    
    # Initialize game data
    init_game()
    
    # Register callbacks
    glutDisplayFunc(display)
    glutIdleFunc(idle)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(handle_keyboard)
    glutSpecialFunc(handle_special_keys)
    glutMouseFunc(handle_mouse)
    
    # Start
    print("=" * 60)
    print("CYBER RUNNER 2077: NEON HORIZON")
    print("=" * 60)
    print("Controls:")
    print("  W/A/S/D - Move and Slide")
    print("  SPACE   - Jump")
    print("  MOUSE L - Shoot (Hold for charge)")
    print("  MOUSE R - Grenade")
    print("  F/1/2/3/4 - Camera modes")
    print("  P       - Pause")
    print("  C/V/B   - Cheats (Cheat/God-AI/Slow-Mo)")
    print("=" * 60)
    print("\nStarting game loop...")
    
    glutMainLoop()

if __name__ == "__main__":
    main()