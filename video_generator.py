import os
import sys
import math
import shutil
import subprocess
from PIL import Image, ImageDraw, ImageFont

# ── Configuration Constants ─────────────────────────────────────────────
WIDTH = 1280
HEIGHT = 720
FPS = 30
TOTAL_FRAMES = 45 * FPS  # 1350 frames
TEMP_FRAMES_DIR = "temp_frames"
OUTPUT_VIDEO_PATH = "assets/demo_video.mp4"

# ── Color Palette ───────────────────────────────────────────────────────
BG_DARK = (14, 17, 23)          # #0E1117 (Streamlit main bg)
BG_SIDEBAR = (26, 29, 36)       # #1A1D24 (Streamlit sidebar bg)
ACCENT_RED = (255, 75, 75)      # #FF4B4B (Streamlit red)
CARD_BG = (38, 39, 48)          # #262730 (Streamlit card bg)
BORDER_COLOR = (49, 51, 63)     # #31333F (Streamlit border)
TEXT_WHITE = (250, 250, 250)    # #FAFAFA
TEXT_GREY = (163, 168, 180)     # #A3A8B4
TEXT_BLACK = (0, 0, 0)
COLOR_SUCCESS = (36, 193, 108)  # #24C16C

# ── Font Helper ─────────────────────────────────────────────────────────
def load_font(font_type='regular', size=16):
    """Loads a system font with fallbacks."""
    paths = {
        'regular': [r"C:\Windows\Fonts\segoeui.ttf", r"C:\Windows\Fonts\arial.ttf"],
        'bold': [r"C:\Windows\Fonts\segoeuib.ttf", r"C:\Windows\Fonts\arialbd.ttf"],
        'italic': [r"C:\Windows\Fonts\segoeuii.ttf", r"C:\Windows\Fonts\ariali.ttf"]
    }
    for path in paths.get(font_type, paths['regular']):
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except IOError:
                continue
    return ImageFont.load_default()

# Load fonts once to cache them
font_title = load_font('bold', 48)
font_sub = load_font('regular', 26)
font_badge = load_font('bold', 16)
font_header = load_font('bold', 22)
font_sidebar_header = load_font('bold', 18)
font_sidebar_section = load_font('bold', 14)
font_label = load_font('regular', 12)
font_body = load_font('regular', 14)
font_body_bold = load_font('bold', 14)
font_large_val = load_font('bold', 34)
font_btn_live = load_font('bold', 20)

# ── Easing Utilities ────────────────────────────────────────────────────
def ease_out_quad(t):
    return t * (2 - t)

def ease_in_out_quad(t):
    if t < 0.5:
        return 2 * t * t
    else:
        return -1 + (4 - 2 * t) * t

# ── Centering Text Helpers ──────────────────────────────────────────────
def draw_text_centered(draw, text, cx, cy, font, fill):
    bbox = font.getbbox(str(text))
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    x = cx - w / 2 - bbox[0]
    y = cy - h / 2 - bbox[1]
    draw.text((x, y), str(text), font=font, fill=fill)

def draw_text_left(draw, text, x, cy, font, fill):
    bbox = font.getbbox(str(text))
    h = bbox[3] - bbox[1]
    y = cy - h / 2 - bbox[1]
    draw.text((x - bbox[0], y), str(text), font=font, fill=fill)

# ── Custom Vector Icon Drawers ─────────────────────────────────────────
def draw_warning_icon(draw, x, y, size=24):
    """Draws a warning triangle icon manually."""
    padding = size * 0.1
    points = [
        (x + size / 2, y + padding),
        (x + padding, y + size - padding),
        (x + size - padding, y + size - padding)
    ]
    draw.polygon(points, fill=ACCENT_RED)
    
    # Exclamation mark inside triangle
    draw.line([(x + size / 2, y + size * 0.42), (x + size / 2, y + size * 0.68)], fill=TEXT_WHITE, width=int(size * 0.08 + 1))
    draw.ellipse([
        (x + size / 2 - size * 0.05, y + size * 0.76),
        (x + size / 2 + size * 0.05, y + size * 0.86)
    ], fill=TEXT_WHITE)

def draw_chart_icon(draw, x, y, size=24):
    """Draws a bar chart icon manually."""
    # Three bars
    w_bar = size * 0.2
    gap = size * 0.1
    h1 = size * 0.4
    h2 = size * 0.8
    h3 = size * 0.6
    
    draw.rectangle([x, y + size - h1, x + w_bar, y + size], fill=ACCENT_RED)
    draw.rectangle([x + w_bar + gap, y + size - h2, x + 2*w_bar + gap, y + size], fill=ACCENT_RED)
    draw.rectangle([x + 2*w_bar + 2*gap, y + size - h3, x + 3*w_bar + 2*gap, y + size], fill=ACCENT_RED)

def draw_search_icon(draw, x, y, size=18, color=TEXT_GREY):
    """Draws a magnifying glass search icon."""
    r = size * 0.3
    cx, cy = x + size * 0.35, y + size * 0.35
    draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], outline=color, width=2)
    draw.line([(cx + r * 0.7, cy + r * 0.7), (x + size * 0.8, y + size * 0.8)], fill=color, width=2)

def draw_spinner(draw, cx, cy, size=40, angle=0):
    """Draws a rotating loading spinner."""
    bbox = [cx - size/2, cy - size/2, cx + size/2, cy + size/2]
    # Draw arc in red
    draw.arc(bbox, start=angle, end=angle + 270, fill=ACCENT_RED, width=4)

def draw_cursor(draw, x, y):
    """Draws a professional, clean white cursor with a black outline."""
    points = [
        (x, y),
        (x, y + 17),
        (x + 4, y + 13),
        (x + 8, y + 21),
        (x + 10, y + 20),
        (x + 6, y + 12),
        (x + 11, y + 12)
    ]
    draw.polygon(points, fill=TEXT_WHITE, outline=TEXT_BLACK)

# ── Scene Rendering Functions ──────────────────────────────────────────

def create_gradient_bg(color1, color2):
    """Creates a high quality linear gradient background."""
    base = Image.new('RGB', (1, HEIGHT))
    draw = ImageDraw.Draw(base)
    for y in range(HEIGHT):
        ratio = y / (HEIGHT - 1)
        r = int(color1[0] + (color2[0] - color1[0]) * ratio)
        g = int(color1[1] + (color2[1] - color1[1]) * ratio)
        b = int(color1[2] + (color2[2] - color1[2]) * ratio)
        draw.point((0, y), fill=(r, g, b))
    return base.resize((WIDTH, HEIGHT), Image.Resampling.BILINEAR)

# Cached backgrounds
bg_scene1_5 = create_gradient_bg((10, 14, 23), (28, 33, 46)) # Dark gradient

def draw_sidebar_base(draw):
    """Draws the static base Streamlit sidebar on the image."""
    draw.rectangle([0, 0, 340, HEIGHT], fill=BG_SIDEBAR)
    draw.line([(340, 0), (340, HEIGHT)], fill=BORDER_COLOR, width=1)
    
    # Sidebar Header
    draw_text_left(draw, "Customer Information", 30, 40, font_sidebar_header, TEXT_WHITE)
    draw.line([(30, 65), (310, 65)], fill=BORDER_COLOR, width=1)
    
    # Demographics Section
    draw_text_left(draw, "Demographics", 30, 85, font_sidebar_section, TEXT_GREY)

def draw_dropdown(draw, label, value, y_pos, active=False, hover_option=None):
    """Draws a Streamlit selectbox/dropdown widget."""
    draw_text_left(draw, label, 30, y_pos, font_label, TEXT_WHITE)
    
    box_y = y_pos + 12
    box_h = 32
    # Draw selectbox container
    draw.rounded_rectangle([30, box_y, 310, box_y + box_h], radius=4, fill=CARD_BG, outline=BORDER_COLOR, width=1)
    draw_text_left(draw, value, 40, box_y + box_h / 2, font_body, TEXT_WHITE)
    
    # Draw simple down arrow on the right
    ax = 290
    ay = box_y + 13
    draw.polygon([(ax, ay), (ax + 8, ay), (ax + 4, ay + 6)], fill=TEXT_GREY)
    
    # Draw dropdown options if dropdown is active (open)
    if active:
        pop_y = box_y + box_h + 2
        pop_h = 95
        # Draw background card for menu options
        draw.rounded_rectangle([30, pop_y, 310, pop_y + pop_h], radius=4, fill=CARD_BG, outline=ACCENT_RED, width=1)
        
        options = ["Month-to-month", "One year", "Two year"]
        for i, opt in enumerate(options):
            opt_y = pop_y + 6 + i * 28
            if hover_option == opt:
                draw.rectangle([32, opt_y - 4, 308, opt_y + 22], fill=BORDER_COLOR)
            draw_text_left(draw, opt, 42, opt_y + 9, font_body, TEXT_WHITE)

def draw_slider(draw, label, val_text, pct, y_pos):
    """Draws a Streamlit slider widget."""
    draw_text_left(draw, label, 30, y_pos, font_label, TEXT_WHITE)
    draw_text_left(draw, val_text, 280, y_pos, font_label, TEXT_GREY)
    
    track_y = y_pos + 20
    # Draw slider track
    draw.line([(30, track_y), (310, track_y)], fill=BORDER_COLOR, width=4)
    # Highlight track up to pct
    fill_x = int(30 + pct * 280)
    draw.line([(30, track_y), (fill_x, track_y)], fill=ACCENT_RED, width=4)
    # Slider handle thumb
    draw.ellipse([(fill_x - 7, track_y - 7), (fill_x + 7, track_y + 7)], fill=ACCENT_RED)

def draw_predict_button(draw, pressed=False):
    """Draws the primary Predict Churn button in Streamlit styling."""
    btn_y = 445
    btn_h = 36
    
    fill_color = (211, 60, 60) if pressed else ACCENT_RED
    draw.rounded_rectangle([30, btn_y, 310, btn_y + btn_h], radius=4, fill=fill_color)
    
    # Centered text in button
    cx = 170
    cy = btn_y + btn_h / 2
    
    # Draw magnifying glass next to button text
    draw_search_icon(draw, cx - 60, cy - 8, size=16, color=TEXT_WHITE)
    draw_text_centered(draw, "Predict Churn", cx + 10, cy, font_body_bold, TEXT_WHITE)

def draw_dashboard_header(draw):
    """Draws the main area title bar."""
    draw_chart_icon(draw, 370, 35, size=24)
    draw_text_left(draw, "Customer Churn Predictor", 405, 47, font_header, TEXT_WHITE)
    draw_text_left(draw, "Enter customer details in the sidebar and click Predict Churn to assess their cancellation risk.", 370, 80, font_label, TEXT_GREY)

def draw_main_area_placeholder(draw):
    """Draws informational placeholder cards in the main area so it doesn't look blank."""
    # ── Divider line below header
    draw.line([(370, 105), (1240, 105)], fill=BORDER_COLOR, width=1)

    # ── Row of 3 metric mini-cards ────────────────────────────────
    cards_data = [
        ("Model", "XGBoost", ACCENT_RED),
        ("ROC-AUC", "0.842", (100, 200, 255)),
        ("F1 Score", "0.627", COLOR_SUCCESS),
    ]
    card_w = 240
    card_h = 80
    gap = 30
    start_x = 370
    start_y = 130
    for i, (label, value, accent) in enumerate(cards_data):
        cx = start_x + i * (card_w + gap)
        # Card background
        draw.rounded_rectangle([cx, start_y, cx + card_w, start_y + card_h], radius=6, fill=CARD_BG, outline=BORDER_COLOR, width=1)
        # Accent top border
        draw.line([(cx + 6, start_y), (cx + card_w - 6, start_y)], fill=accent, width=3)
        # Label
        draw_text_left(draw, label, cx + 20, start_y + 28, font_label, TEXT_GREY)
        # Value
        draw_text_left(draw, value, cx + 20, start_y + 55, font_header, TEXT_WHITE)

    # ── "How it works" info card ──────────────────────────────────
    info_y = 240
    draw.rounded_rectangle([370, info_y, 1240, info_y + 180], radius=8, fill=CARD_BG, outline=BORDER_COLOR, width=1)
    draw_text_left(draw, "How It Works", 400, info_y + 25, font_sidebar_header, TEXT_WHITE)
    draw.line([(400, info_y + 45), (1210, info_y + 45)], fill=BORDER_COLOR, width=1)

    steps = [
        ("1.", "Fill in customer details", "Use the sidebar form to enter demographics, account, and service info."),
        ("2.", "Click Predict Churn", "The XGBoost model analyzes 19 features to compute a churn probability."),
        ("3.", "Review risk factors", "See which specific attributes are driving the churn risk for this customer."),
    ]
    for i, (num, title, desc) in enumerate(steps):
        sy = info_y + 60 + i * 38
        # Step number in accent red
        draw_text_left(draw, num, 410, sy + 10, font_body_bold, ACCENT_RED)
        # Step title
        draw_text_left(draw, title, 435, sy + 10, font_body_bold, TEXT_WHITE)
        # Step description
        draw_text_left(draw, desc, 610, sy + 10, font_label, TEXT_GREY)

    # ── Dataset info bar at the bottom ────────────────────────────
    bar_y = 450
    draw.rounded_rectangle([370, bar_y, 1240, bar_y + 42], radius=6, fill=(22, 25, 32))
    draw_text_centered(draw, "Dataset: IBM Telco Customer Churn  |  7,043 customers  |  19 features  |  Trained with XGBoost", 805, bar_y + 21, font_label, TEXT_GREY)

# ── Render Scenes Static/Dynamic Frame Gen ──────────────────────────────

def render_scene1(frame_num):
    """Scene 1: Title Card (0.0s – 7.0s)"""
    img = bg_scene1_5.copy()
    draw = ImageDraw.Draw(img)
    
    # Accent top bar
    draw.rectangle([0, 0, WIDTH, 5], fill=ACCENT_RED)
    
    # Animation timings
    # Title fade/slide in
    t_title = min(1.0, frame_num / 40.0)
    e_title = ease_out_quad(t_title)
    y_title = int(240 + e_title * 40)
    opacity_title = t_title
    
    # Subtitle fade/slide in
    t_sub = max(0.0, min(1.0, (frame_num - 20) / 40.0))
    e_sub = ease_out_quad(t_sub)
    y_sub = int(400 - e_sub * 20)
    opacity_sub = t_sub
    
    # Metrics Badge scale/fade in
    t_badge = max(0.0, min(1.0, (frame_num - 40) / 40.0))
    opacity_badge = t_badge
    
    # Create overlay for transparent text & card rendering
    overlay = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    
    # Draw Title
    title_text = "Customer Churn Prediction"
    draw_text_centered(draw_overlay, title_text, WIDTH / 2, y_title, font_title, (250, 250, 250, int(opacity_title * 255)))
    
    # Draw Subtitle
    sub_text = "Built with XGBoost & Streamlit"
    draw_text_centered(draw_overlay, sub_text, WIDTH / 2, y_sub, font_sub, (255, 75, 75, int(opacity_sub * 255)))
    
    # Draw Stats Badge
    if opacity_badge > 0:
        badge_w, badge_h = 580, 48
        by = 475
        bx = WIDTH / 2 - badge_w / 2
        # Round rectangle background
        draw_overlay.rounded_rectangle(
            [bx, by, bx + badge_w, by + badge_h],
            radius=8,
            fill=(38, 39, 48, int(opacity_badge * 230)),
            outline=(255, 75, 75, int(opacity_badge * 255)),
            width=1
        )
        badge_text = "Catches 79% of at-risk customers  |  ROC-AUC 0.842"
        draw_text_centered(draw_overlay, badge_text, WIDTH / 2, by + badge_h / 2, font_badge, (230, 235, 245, int(opacity_badge * 255)))
        
    final_img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
    return final_img

def render_scene2(frame_num):
    """Scene 2: Sidebar Form Mockup (7.0s – 17.0s)"""
    img = Image.new('RGB', (WIDTH, HEIGHT), BG_DARK)
    draw = ImageDraw.Draw(img)
    
    f_scene = frame_num - 210  # 0 to 299
    
    # Defaults
    tenure_val = 0
    charges_val = 18.0
    contract_val = "Month-to-month"
    dropdown_active = False
    hover_option = None
    btn_pressed = False
    show_spinner = False
    
    cursor_x, cursor_y = -100, -100
    cursor_alpha = 0.0
    
    # Mouse Animation State Machine
    if f_scene < 30:  # 7.0s to 8.0s (Move to Tenure slider)
        t = f_scene / 30.0
        e = ease_in_out_quad(t)
        cursor_x = int(600 + e * (30 - 600))
        cursor_y = int(600 + e * (235 - 600))
        cursor_alpha = t
        
    elif f_scene < 75:  # 8.0s to 9.5s (Drag Tenure to 12 months)
        t = (f_scene - 30) / 45.0
        tenure_val = int(t * 12)
        pct = tenure_val / 72.0
        x_thumb = int(30 + pct * 280)
        cursor_x = x_thumb
        cursor_y = 235
        cursor_alpha = 1.0
        
    elif f_scene < 105:  # 9.5s to 10.5s (Move to Contract Dropdown)
        tenure_val = 12
        t = (f_scene - 75) / 30.0
        e = ease_in_out_quad(t)
        cursor_x = int(77 + e * (170 - 77))
        cursor_y = int(235 + e * (297 - 235))
        cursor_alpha = 1.0
        
    elif f_scene < 120:  # 10.5s to 11.0s (Click dropdown, move to Option)
        tenure_val = 12
        dropdown_active = True
        t = (f_scene - 105) / 15.0
        e = ease_in_out_quad(t)
        cursor_x = 170
        cursor_y = int(297 + e * (352 - 297))
        cursor_alpha = 1.0
        hover_option = "Month-to-month"
        
    elif f_scene < 135:  # 11.0s to 11.5s (Select Option, move to Monthly Charges slider)
        tenure_val = 12
        contract_val = "Month-to-month"
        t = (f_scene - 120) / 15.0
        e = ease_in_out_quad(t)
        cursor_x = int(170 + e * (30 - 170))
        cursor_y = int(352 + e * (375 - 352))
        cursor_alpha = 1.0
        
    elif f_scene < 150:  # 11.5s to 12.0s (Hover over charges thumb)
        tenure_val = 12
        cursor_x = 30
        cursor_y = 375
        cursor_alpha = 1.0
        
    elif f_scene < 195:  # 12.0s to 13.5s (Drag Charges to $70)
        tenure_val = 12
        t = (f_scene - 150) / 45.0
        charges_val = 18.0 + t * 52.0
        pct = (charges_val - 18.0) / 102.0
        x_thumb = int(30 + pct * 280)
        cursor_x = x_thumb
        cursor_y = 375
        cursor_alpha = 1.0
        
    elif f_scene < 225:  # 13.5s to 14.5s (Move to Predict Churn Button)
        tenure_val = 12
        charges_val = 70.0
        t = (f_scene - 195) / 30.0
        e = ease_in_out_quad(t)
        cursor_x = int(173 + e * (170 - 173))
        cursor_y = int(375 + e * (463 - 375))
        cursor_alpha = 1.0
        
    elif f_scene < 240:  # 14.5s to 15.0s (Hover on Predict Churn Button)
        tenure_val = 12
        charges_val = 70.0
        cursor_x = 170
        cursor_y = 463
        cursor_alpha = 1.0
        
    elif f_scene < 250:  # 15.0s to 15.33s (Click Button)
        tenure_val = 12
        charges_val = 70.0
        btn_pressed = True
        cursor_x = 170
        cursor_y = 463
        cursor_alpha = 1.0
        
    else:  # 15.33s to 17.0s (Spinner displays, cursor fades out)
        tenure_val = 12
        charges_val = 70.0
        show_spinner = True
        t_fade = (f_scene - 250) / 15.0
        cursor_alpha = max(0.0, 1.0 - t_fade)
        cursor_x = 170
        cursor_y = 463
        
    # Render UI
    draw_sidebar_base(draw)
    
    # Render widgets
    draw_dropdown(draw, "Gender", "Male", 110)
    draw_slider(draw, "Tenure (months)", f"{tenure_val}", tenure_val / 72.0, 205)
    draw_dropdown(draw, "Contract", contract_val, 265, active=dropdown_active, hover_option=hover_option)
    
    # Hide slider track for charges if dropdown menu overlaps it to avoid graphic glitches
    if not dropdown_active:
        draw_slider(draw, "Monthly Charges ($)", f"${charges_val:.0f}", (charges_val - 18.0) / 102.0, 345)
    else:
        # Just render label when dropdown is covering
        draw_text_left(draw, "Monthly Charges ($)", 30, 345, font_label, TEXT_WHITE)
        
    draw_predict_button(draw, pressed=btn_pressed)
    draw_dashboard_header(draw)
    draw_main_area_placeholder(draw)
    
    # Spinner Logic
    if show_spinner:
        spin_angle = (f_scene - 250) * 12
        cx, cy = 340 + (WIDTH - 340) / 2, 330
        draw_spinner(draw, cx, cy, size=45, angle=spin_angle)
        draw_text_centered(draw, "Computing prediction...", cx, cy + 50, font_body, TEXT_GREY)
        
    # Render cursor overlay
    if cursor_alpha > 0:
        # Create cursor image with alpha channel
        cursor_img = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
        cursor_draw = ImageDraw.Draw(cursor_img)
        draw_cursor(cursor_draw, cursor_x, cursor_y)
        
        # Create and apply alpha mask properly
        alpha_mask = Image.new('L', (WIDTH, HEIGHT), int(cursor_alpha * 255))
        cursor_img.putalpha(alpha_mask)
        
        # Blend with main image
        img = Image.alpha_composite(img.convert('RGBA'), cursor_img).convert('RGB')
        
    return img

def render_scene3(frame_num):
    """Scene 3: Prediction Result Card (17.0s – 25.0s)"""
    img = Image.new('RGB', (WIDTH, HEIGHT), BG_DARK)
    draw = ImageDraw.Draw(img)
    
    f_scene = frame_num - 510  # 0 to 239
    
    # Draw stable sidebar
    draw_sidebar_base(draw)
    draw_dropdown(draw, "Gender", "Male", 110)
    draw_slider(draw, "Tenure (months)", "12", 12.0 / 72.0, 205)
    draw_dropdown(draw, "Contract", "Month-to-month", 265)
    draw_slider(draw, "Monthly Charges ($)", "$70", (70.0 - 18.0) / 102.0, 345)
    draw_predict_button(draw, pressed=False)
    draw_dashboard_header(draw)
    
    # Timings for result card animation
    # Fade/slide up of the card (0 to 20 frames)
    t_card = min(1.0, f_scene / 20.0)
    e_card = ease_out_quad(t_card)
    card_y = int(170 - e_card * 40)  # Slides from 170 up to 130
    opacity_card = t_card
    
    # Progress gauge animation (20 to 60 frames)
    t_gauge = max(0.0, min(1.0, (f_scene - 20) / 40.0))
    e_gauge = ease_out_quad(t_gauge)
    gauge_pct = e_gauge * 68.4
    
    # Render with Transparency Overlay
    overlay = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    
    if opacity_card > 0:
        alpha_byte = int(opacity_card * 255)
        # Card Container (800x230)
        cx1, cy1 = 370, card_y
        cx2, cy2 = 1170, card_y + 230
        
        # Draw background and border
        draw_overlay.rounded_rectangle([cx1, cy1, cx2, cy2], radius=8, fill=(38, 39, 48, int(opacity_card * 240)), outline=(255, 75, 75, alpha_byte), width=2)
        
        # High Risk Badge / Header
        draw_warning_icon(draw_overlay, cx1 + 30, cy1 + 25, size=26)
        draw_text_left(draw_overlay, "High Risk of Churn", cx1 + 70, cy1 + 38, font_header, (255, 75, 75, alpha_byte))
        
        # Metrics: Column 1: Churn Probability
        draw_text_left(draw_overlay, "Churn Probability", cx1 + 30, cy1 + 90, font_label, (163, 168, 180, alpha_byte))
        draw_text_left(draw_overlay, f"{gauge_pct:.1f}%" if f_scene > 20 else "0.0%", cx1 + 30, cy1 + 125, font_large_val, (255, 75, 75, alpha_byte))
        
        # Metrics: Column 2: Confidence
        draw_text_left(draw_overlay, "Confidence", cx1 + 250, cy1 + 90, font_label, (163, 168, 180, alpha_byte))
        draw_text_left(draw_overlay, "68.4%", cx1 + 250, cy1 + 125, font_large_val, (250, 250, 250, alpha_byte))
        
        # Risk Gauge Label
        draw_text_left(draw_overlay, "Risk Level", cx1 + 30, cy1 + 172, font_label, (163, 168, 180, alpha_byte))
        
        # Risk Gauge Bar: Track
        rx1, ry1 = cx1 + 110, cy1 + 165
        rx2, ry2 = cx1 + 600, cy1 + 180
        draw_overlay.rounded_rectangle([rx1, ry1, rx2, ry2], radius=4, fill=(49, 51, 63, alpha_byte))
        
        # Risk Gauge Bar: Fill
        if gauge_pct > 0:
            fill_w = int((gauge_pct / 100.0) * (rx2 - rx1))
            draw_overlay.rounded_rectangle([rx1, ry1, rx1 + fill_w, ry2], radius=4, fill=(255, 75, 75, alpha_byte))
            # Text on the right of the gauge
            draw_text_left(draw_overlay, f"{gauge_pct:.1f}%", rx1 + fill_w + 12, cy1 + 172, font_body_bold, (255, 75, 75, alpha_byte))
            
    final_img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
    return final_img

def render_scene4(frame_num):
    """Scene 4: Risk Factors Breakdown (25.0s – 35.0s)"""
    img = Image.new('RGB', (WIDTH, HEIGHT), BG_DARK)
    draw = ImageDraw.Draw(img)
    
    f_scene = frame_num - 750  # 0 to 299
    
    # Draw stable sidebar
    draw_sidebar_base(draw)
    draw_dropdown(draw, "Gender", "Male", 110)
    draw_slider(draw, "Tenure (months)", "12", 12.0 / 72.0, 205)
    draw_dropdown(draw, "Contract", "Month-to-month", 265)
    draw_slider(draw, "Monthly Charges ($)", "$70", (70.0 - 18.0) / 102.0, 345)
    draw_predict_button(draw, pressed=False)
    draw_dashboard_header(draw)
    
    # Draw static prediction card from Scene 3 (fully loaded)
    card_y = 130
    draw.rounded_rectangle([370, card_y, 1170, card_y + 230], radius=8, fill=CARD_BG, outline=ACCENT_RED, width=2)
    draw_warning_icon(draw, 400, card_y + 25, size=26)
    draw_text_left(draw, "High Risk of Churn", 440, card_y + 38, font_header, ACCENT_RED)
    draw_text_left(draw, "Churn Probability", 400, card_y + 90, font_label, TEXT_GREY)
    draw_text_left(draw, "68.4%", 400, card_y + 125, font_large_val, ACCENT_RED)
    draw_text_left(draw, "Confidence", 620, card_y + 90, font_label, TEXT_GREY)
    draw_text_left(draw, "68.4%", 620, card_y + 125, font_large_val, TEXT_WHITE)
    draw_text_left(draw, "Risk Level", 400, card_y + 172, font_label, TEXT_GREY)
    
    # Gauge track and filled bar
    draw.rounded_rectangle([510, card_y + 165, 1000, card_y + 180], radius=4, fill=BORDER_COLOR)
    fill_w = int(0.684 * (1000 - 510))
    draw.rounded_rectangle([510, card_y + 165, 510 + fill_w, card_y + 180], radius=4, fill=ACCENT_RED)
    draw_text_left(draw, "68.4%", 510 + fill_w + 12, card_y + 172, font_body_bold, ACCENT_RED)
    
    # Key Risk Factors Section animation
    # Heading fade-in at 25.0s - 25.67s (0 to 20 frames)
    t_head = min(1.0, f_scene / 20.0)
    opacity_head = t_head
    
    # Factor 1: Contract Type (20 to 50 frames)
    t_f1 = max(0.0, min(1.0, (f_scene - 20) / 30.0))
    e_f1 = ease_out_quad(t_f1)
    f1_x = int(340 + e_f1 * 30)  # Slides from 340 to 370
    opacity_f1 = t_f1
    
    # Factor 2: Tenure (55 to 85 frames)
    t_f2 = max(0.0, min(1.0, (f_scene - 55) / 30.0))
    e_f2 = ease_out_quad(t_f2)
    f2_x = int(340 + e_f2 * 30)
    opacity_f2 = t_f2
    
    # Factor 3: Monthly Charges (90 to 120 frames)
    t_f3 = max(0.0, min(1.0, (f_scene - 90) / 30.0))
    e_f3 = ease_out_quad(t_f3)
    f3_x = int(340 + e_f3 * 30)
    opacity_f3 = t_f3
    
    overlay = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    
    # Draw Heading
    if opacity_head > 0:
        draw_overlay.text((370, 395), "Key Risk Factors", font=font_sidebar_header, fill=(250, 250, 250, int(opacity_head * 255)))
        
    card_w, card_h = 800, 48
    
    # Render Factor 1
    if opacity_f1 > 0:
        fy = 435
        # Red left-accented card
        draw_overlay.rounded_rectangle([f1_x, fy, f1_x + card_w, fy + card_h], radius=6, fill=(30, 34, 41, int(opacity_f1 * 255)))
        draw_overlay.rectangle([f1_x, fy, f1_x + 5, fy + card_h], fill=(255, 75, 75, int(opacity_f1 * 255)))
        draw_text_left(draw_overlay, "Contract Type", f1_x + 24, fy + card_h / 2, font_body_bold, (250, 250, 250, int(opacity_f1 * 255)))
        draw_text_left(draw_overlay, "Month-to-month  (42.7% churn rate)", f1_x + 200, fy + card_h / 2, font_body, (163, 168, 180, int(opacity_f1 * 255)))
        
    # Render Factor 2
    if opacity_f2 > 0:
        fy = 495
        draw_overlay.rounded_rectangle([f2_x, fy, f2_x + card_w, fy + card_h], radius=6, fill=(30, 34, 41, int(opacity_f2 * 255)))
        draw_overlay.rectangle([f2_x, fy, f2_x + 5, fy + card_h], fill=(255, 75, 75, int(opacity_f2 * 255)))
        draw_text_left(draw_overlay, "Tenure", f2_x + 24, fy + card_h / 2, font_body_bold, (250, 250, 250, int(opacity_f2 * 255)))
        draw_text_left(draw_overlay, "12 months  (< 10 months is the highest risk period)", f2_x + 200, fy + card_h / 2, font_body, (163, 168, 180, int(opacity_f2 * 255)))
        
    # Render Factor 3
    if opacity_f3 > 0:
        fy = 555
        draw_overlay.rounded_rectangle([f3_x, fy, f3_x + card_w, fy + card_h], radius=6, fill=(30, 34, 41, int(opacity_f3 * 255)))
        draw_overlay.rectangle([f3_x, fy, f3_x + 5, fy + card_h], fill=(255, 75, 75, int(opacity_f3 * 255)))
        draw_text_left(draw_overlay, "Monthly Charges", f3_x + 24, fy + card_h / 2, font_body_bold, (250, 250, 250, int(opacity_f3 * 255)))
        draw_text_left(draw_overlay, "$70 / mo  (high charges increase budget pressure)", f3_x + 200, fy + card_h / 2, font_body, (163, 168, 180, int(opacity_f3 * 255)))
        
    final_img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
    return final_img

def render_scene5(frame_num):
    """Scene 5: Closing Card (35.0s – 45.0s)"""
    img = bg_scene1_5.copy()
    draw = ImageDraw.Draw(img)
    
    # Accent top bar
    draw.rectangle([0, 0, WIDTH, 5], fill=ACCENT_RED)
    
    f_scene = frame_num - 1050  # 0 to 299
    
    # Title fade/slide in (0 to 30 frames)
    t_title = min(1.0, f_scene / 30.0)
    e_title = ease_out_quad(t_title)
    y_title = int(220 + e_title * 20)  # slides 220 to 240
    opacity_title = t_title
    
    # Subtitle fade/slide in (15 to 45 frames)
    t_sub = max(0.0, min(1.0, (f_scene - 15) / 30.0))
    e_sub = ease_out_quad(t_sub)
    y_sub = int(320 - e_sub * 15)  # slides 320 to 305
    opacity_sub = t_sub
    
    # Button fade/scale in (30 to 60 frames)
    t_btn = max(0.0, min(1.0, (f_scene - 30) / 30.0))
    opacity_btn = t_btn
    
    # Glow animation (only starts after button is fully visible, i.e., f_scene > 60)
    glow_size = 0.0
    glow_opacity = 0.0
    if f_scene > 60:
        # Breathing glow effect (1.5s cycle = 45 frames)
        cycle_frames = 45
        t_cycle = ((f_scene - 60) % cycle_frames) / float(cycle_frames)
        # Smooth oscillation using sine wave
        wave = (math.sin(t_cycle * 2 * math.pi) + 1.0) / 2.0  # 0.0 to 1.0
        glow_size = 2.0 + wave * 10.0                        # 2 to 12 pixels
        glow_opacity = 0.45 * (1.0 - wave * 0.5)              # Opacity breathes
        
    overlay = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    
    # Draw Heading
    draw_text_centered(draw_overlay, "Try it live", WIDTH / 2, y_title, font_title, (250, 250, 250, int(opacity_title * 255)))
    
    # Draw Subtitle
    draw_text_centered(draw_overlay, "Experience the real-time XGBoost churn model in action", WIDTH / 2, y_sub, font_sub, (163, 168, 180, int(opacity_sub * 255)))
    
    # Draw Button
    if opacity_btn > 0:
        btn_w, btn_h = 600, 68
        by = 370
        bx = WIDTH / 2 - btn_w / 2
        
        # Draw breathing glow
        if glow_opacity > 0:
            glow_col = (255, 75, 75, int(glow_opacity * 255))
            draw_overlay.rounded_rectangle(
                [bx - glow_size, by - glow_size, bx + btn_w + glow_size, by + btn_h + glow_size],
                radius=10 + int(glow_size),
                fill=glow_col
            )
            
        # Draw primary button
        draw_overlay.rounded_rectangle(
            [bx, by, bx + btn_w, by + btn_h],
            radius=8,
            fill=(255, 75, 75, int(opacity_btn * 255))
        )
        
        # Button text
        btn_text = "customer-churn-predictor.streamlit.app"
        draw_text_centered(draw_overlay, btn_text, WIDTH / 2, by + btn_h / 2, font_btn_live, (250, 250, 250, int(opacity_btn * 255)))
        
    final_img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
    return final_img

# ── Main Generator Loop ──────────────────────────────────────────────────

def render_frame_to_image(frame_num):
    """Router that handles transitions and scene scheduling."""
    # Transitions:
    # 195 to 210: Cross-fade Scene 1 -> Scene 2 (15 frames)
    if 195 <= frame_num < 210:
        alpha = (frame_num - 195) / 15.0
        img1 = render_scene1(195)
        img2 = render_scene2(210)
        return Image.blend(img1, img2, alpha)
        
    # 1020 to 1050: Cross-fade Scene 4 -> Scene 5 (30 frames)
    elif 1020 <= frame_num < 1050:
        alpha = (frame_num - 1020) / 30.0
        img1 = render_scene4(1020)
        img2 = render_scene5(1050)
        return Image.blend(img1, img2, alpha)
        
    # Standard Scenes:
    elif 0 <= frame_num < 195:
        return render_scene1(frame_num)
    elif 210 <= frame_num < 510:
        return render_scene2(frame_num)
    elif 510 <= frame_num < 750:
        return render_scene3(frame_num)
    elif 750 <= frame_num < 1020:
        return render_scene4(frame_num)
    else:  # 1050 <= frame_num < 1350
        return render_scene5(frame_num)

def generate_video():
    """Generates all PNG frames and compiles them into a video using FFmpeg."""
    print("Creating temporary frames directory...")
    if os.path.exists(TEMP_FRAMES_DIR):
        shutil.rmtree(TEMP_FRAMES_DIR)
    os.makedirs(TEMP_FRAMES_DIR)
    
    try:
        print(f"Generating {TOTAL_FRAMES} frames ({TOTAL_FRAMES/FPS:.1f} seconds at {FPS} FPS)...")
        for f in range(TOTAL_FRAMES):
            frame_img = render_frame_to_image(f)
            frame_path = os.path.join(TEMP_FRAMES_DIR, f"frame_{f:04d}.png")
            frame_img.save(frame_path, "PNG")
            
            # Simple progress logging
            if (f + 1) % 100 == 0 or f == 0 or f == TOTAL_FRAMES - 1:
                print(f"  Progress: {f + 1}/{TOTAL_FRAMES} frames generated ({(f+1)/TOTAL_FRAMES*100:.1f}%)")
                
        print("Compiling frames into video via FFmpeg...")
        # Ensure output folder exists
        out_dir = os.path.dirname(OUTPUT_VIDEO_PATH)
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir)
            
        # Compile command
        cmd = [
            "ffmpeg",
            "-y",                               # Overwrite output file
            "-r", str(FPS),                     # Input frame rate
            "-i", os.path.join(TEMP_FRAMES_DIR, "frame_%04d.png"),
            "-c:v", "libx264",                  # H.264 video codec
            "-pix_fmt", "yuv420p",              # YUV 4:2:0 pixel format (widely supported)
            "-preset", "medium",                # Speed/compression trade-off
            "-crf", "18",                       # High visual quality
            OUTPUT_VIDEO_PATH
        ]
        
        print(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            print("FFmpeg Compilation Failed!")
            print("Stderr:")
            print(result.stderr)
            raise RuntimeError(f"FFmpeg failed with exit code {result.returncode}")
            
        print(f"Video generated successfully at: {OUTPUT_VIDEO_PATH}")
        
    finally:
        print("Cleaning up temporary frames directory...")
        if os.path.exists(TEMP_FRAMES_DIR):
            shutil.rmtree(TEMP_FRAMES_DIR)

if __name__ == "__main__":
    generate_video()
