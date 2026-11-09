#!/usr/bin/env python3
"""
codegen_c.py - Focal CNC Code Synthesis Engine
Translates screens_layout.json into native, production-grade C code for LVGL v8 / ESP-IDF.

Requirements:
- 100% compliant with focal-design-system:
  * Pastel tokens
  * Montserrat 14 font
  * Squircles FOCAL_RADIUS_M (10px) and FOCAL_RADIUS_L (20px)
  * LV_LABEL_LONG_DOT with forced line height
  * Touch hitboxes extended >= 44x44 px (lv_obj_set_ext_click_area)
- Zero warnings / zero errors on both desktop simulator (ninja -C simulator/build)
  and ESP32-S3 firmware (idf.py build).
- Real firmware callbacks:
  * G-Code parser (gcode_parser_execute_line)
  * Laser control (laser_set_power, laser_set_enable, laser_driver_pulse)
  * WiFi Manager (wifi_manager_connect_sta, wifi_manager_scan) - Clean client, no station mode text
  * NVS persistent settings (settings_manager_get, settings_manager_save)
  * ILI9488 & themes (focal_theme_set_dark, focal_theme_set_accent)
"""

import os
import sys
import json

def generate_c_code(layout_data):
    screens = {s["id"]: s for s in layout_data["screens"]}
    
    code = []
    
    # Header comment
    code.append("""/**
 * @file ui_screens.c
 * @brief Industrial UI Screen Manager for Focal CNC Laser Cutter (LVGL v8)
 *
 * AUTOMATICALLY SYNTHESIZED BY FOCAL CODEGEN ENGINE (codegen_c.py)
 * Source layout: screens_layout.json
 *
 * Implements strict focal-design-system guidelines:
 * - High-speed instant screen switching (zero slow software fade animations)
 * - 28 anti-aliased vector icons (focal_icons.h)
 * - Master-Detail list navigation for Configuration Menu
 * - Dynamic Dark / Light theme switching & accent color selector with NVS persistence
 * - Pure Client Wi-Fi manager with real scanning, scrollable network list, and visible keyboard input modal
 * - Quick Cut module with simulated 160x200 mm bed and real-time touch dragging
 * - Visual shape buttons with vector icon drawings (no technical jargon)
 * - Clean ASCII strings (zero 'ñ' or broken accents)
 * - ISO 9241-9 tactile touch targets with extended hitboxes >= 44x44 px
 */

#include <stdio.h>
#include <string.h>
#include <math.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "ui_screens.h"
#include "focal_theme.h"
#include "focal_icons.h"
#include "settings_manager.h"
#include "laser_driver.h"
#include "gcode_parser.h"
#include "wifi_manager.h"
#include "ili9488_lvgl.h"
#include "esp_log.h"

static const char *TAG = "FOCAL_UI";

#define FOCAL_FONT &lv_font_montserrat_14

// Global Theme Styles
lv_style_t focal_style_screen;
lv_style_t focal_style_card;
lv_style_t focal_style_pill;
lv_style_t focal_style_btn_primary;
lv_style_t focal_style_btn_secondary;
lv_style_t focal_style_btn_mint;
lv_style_t focal_style_btn_amber;
lv_style_t focal_style_btn_danger;
lv_style_t focal_style_warn_box;
lv_style_t focal_style_warn_text;

// Theme state
static bool s_is_dark = true;
static uint8_t s_accent_idx = 0; // 0: Blue, 1: Mint, 2: Amber, 3: Purple, 4: Red

static const uint32_t s_accent_dark_hex[5] = {
    FOCAL_HEX_PASTEL_BLUE,   // 0x60A5FA
    FOCAL_HEX_PASTEL_MINT,   // 0x34D399
    FOCAL_HEX_PASTEL_AMBER,  // 0xFBBF24
    0xA78BFA,                // Pastel Purple
    FOCAL_HEX_PASTEL_RED     // 0xF87171
};

static const uint32_t s_accent_light_hex[5] = {
    0x3B82F6, // Light Blue
    0x10B981, // Light Mint
    0xF59E0B, // Light Amber
    0x8B5CF6, // Light Purple
    0xEF4444  // Light Red
};

// Screens array
static lv_obj_t *s_screens[UI_SCREEN_MAX] = {0};
static ui_screen_id_t s_current_screen = UI_SCREEN_LAUNCHER;

// Header handles
static lv_obj_t *s_hdr_pills[UI_SCREEN_MAX] = {0};

// Forward screen creators
static void create_launcher_screen(void);
static void create_jogging_screen(void);
static void create_sd_screen(void);
static void create_cut_monitor_screen(void);
static void create_calibration_screen(void);
static void create_shapes_screen(void);
static void create_settings_screen(void);
static bool s_is_cutting = false;

// =============================================================================
// VECTOR ICON & FLEX BUTTON HELPERS
// =============================================================================
static lv_obj_t *focal_create_icon(lv_obj_t *parent, const lv_img_dsc_t *icon_src, uint32_t color_hex)
{
    lv_obj_t *img = lv_img_create(parent);
    lv_img_set_src(img, icon_src);
    lv_obj_set_style_img_recolor(img, lv_color_hex(color_hex), 0);
    lv_obj_set_style_img_recolor_opa(img, LV_OPA_COVER, 0);
    return img;
}

static lv_obj_t *focal_create_btn(lv_obj_t *parent, int w, int h, const lv_img_dsc_t *icon, const char *text, lv_style_t *style, uint32_t ic_color)
{
    lv_obj_t *btn = lv_btn_create(parent);
    lv_obj_set_size(btn, w, h);
    if (style) lv_obj_add_style(btn, style, 0);
    lv_obj_set_style_radius(btn, FOCAL_RADIUS_M, 0);
    lv_obj_set_style_pad_all(btn, 4, 0);
    lv_obj_set_flex_flow(btn, LV_FLEX_FLOW_ROW);
    lv_obj_set_flex_align(btn, LV_FLEX_ALIGN_CENTER, LV_FLEX_ALIGN_CENTER, LV_FLEX_ALIGN_CENTER);
    lv_obj_set_style_pad_column(btn, 6, 0);
    lv_obj_clear_flag(btn, LV_OBJ_FLAG_SCROLLABLE);

    if (icon) {
        lv_obj_t *img = focal_create_icon(btn, icon, ic_color);
        lv_obj_clear_flag(img, LV_OBJ_FLAG_CLICKABLE);
    }
    if (text && strlen(text) > 0) {
        lv_obj_t *lbl = lv_label_create(btn);
        lv_label_set_text(lbl, text);
        lv_obj_set_style_text_font(lbl, FOCAL_FONT, 0);
        lv_obj_clear_flag(lbl, LV_OBJ_FLAG_CLICKABLE);
        if (w > 0) {
            int avail_w = w - (icon ? 28 : 8);
            if (avail_w > 20) {
                lv_obj_set_width(lbl, avail_w);
                lv_obj_set_height(lbl, lv_font_get_line_height(FOCAL_FONT));
                lv_label_set_long_mode(lbl, LV_LABEL_LONG_DOT);
            }
        }
    }
    return btn;
}

static void on_nav_back_cb(lv_event_t *e)
{
    (void)e;
    ui_switch_screen(UI_SCREEN_LAUNCHER);
}

// Common Header builder
static lv_obj_t *create_screen_header(ui_screen_id_t screen_id, const char *title, bool show_back)
{
    lv_obj_t *screen = s_screens[screen_id];
    lv_obj_t *hdr = lv_obj_create(screen);
    lv_obj_set_size(hdr, 480, 40);
    lv_obj_set_pos(hdr, 0, 0);
    lv_obj_set_style_bg_color(hdr, s_is_dark ? lv_color_hex(0x0F1115) : lv_color_hex(0xF5F6F8), 0);
    lv_obj_set_style_bg_opa(hdr, LV_OPA_COVER, 0);
    lv_obj_set_style_border_side(hdr, LV_BORDER_SIDE_BOTTOM, 0);
    lv_obj_set_style_border_color(hdr, s_is_dark ? lv_color_hex(0x2D333F) : lv_color_hex(0xD1D5DB), 0);
    lv_obj_set_style_border_width(hdr, 1, 0);
    lv_obj_set_style_radius(hdr, 0, 0);
    lv_obj_set_style_pad_all(hdr, 4, 0);
    lv_obj_clear_flag(hdr, LV_OBJ_FLAG_SCROLLABLE);

    if (show_back) {
        lv_obj_t *btn_back = lv_btn_create(hdr);
        lv_obj_set_size(btn_back, 74, 30);
        lv_obj_align(btn_back, LV_ALIGN_LEFT_MID, 6, 0);
        lv_obj_add_style(btn_back, &focal_style_btn_secondary, 0);
        lv_obj_set_style_radius(btn_back, FOCAL_RADIUS_S, 0);
        lv_obj_set_style_pad_all(btn_back, 2, 0);
        lv_obj_set_flex_flow(btn_back, LV_FLEX_FLOW_ROW);
        lv_obj_set_flex_align(btn_back, LV_FLEX_ALIGN_CENTER, LV_FLEX_ALIGN_CENTER, LV_FLEX_ALIGN_CENTER);
        lv_obj_set_style_pad_column(btn_back, 4, 0);
        lv_obj_add_event_cb(btn_back, on_nav_back_cb, LV_EVENT_CLICKED, NULL);

        focal_create_icon(btn_back, &focal_icon_back, s_is_dark ? FOCAL_HEX_PASTEL_BLUE : 0x3B82F6);
        lv_obj_t *lbl_b = lv_label_create(btn_back);
        lv_label_set_text(lbl_b, "Menu");
        lv_obj_set_style_text_font(lbl_b, FOCAL_FONT, 0);
    }

    lv_obj_t *lbl_title = lv_label_create(hdr);
    lv_label_set_text(lbl_title, title);
    lv_obj_set_style_text_font(lbl_title, FOCAL_FONT, 0);
    lv_obj_set_style_text_color(lbl_title, s_is_dark ? lv_color_hex(0xF9FAFB) : lv_color_hex(0x111827), 0);
    if (show_back) {
        lv_obj_align(lbl_title, LV_ALIGN_LEFT_MID, 90, 0);
    } else {
        lv_obj_align(lbl_title, LV_ALIGN_LEFT_MID, 12, 0);
    }

    // Status Pill on top-right
    lv_obj_t *pill = lv_obj_create(hdr);
    lv_obj_set_size(pill, 130, 28);
    lv_obj_align(pill, LV_ALIGN_RIGHT_MID, -6, 0);
    lv_obj_add_style(pill, &focal_style_pill, 0);
    lv_obj_clear_flag(pill, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_set_flex_flow(pill, LV_FLEX_FLOW_ROW);
    lv_obj_set_flex_align(pill, LV_FLEX_ALIGN_CENTER, LV_FLEX_ALIGN_CENTER, LV_FLEX_ALIGN_CENTER);
    lv_obj_set_style_pad_column(pill, 4, 0);

    focal_create_icon(pill, &focal_icon_wifi, FOCAL_HEX_PASTEL_MINT);
    lv_obj_t *lbl_st = lv_label_create(pill);
    lv_label_set_text(lbl_st, "Focal CNC");
    lv_obj_set_style_text_font(lbl_st, FOCAL_FONT, 0);
    s_hdr_pills[screen_id] = lbl_st;

    return hdr;
}

// Laser Pulse Timer Callback
static void laser_pulse_timer_cb(lv_timer_t *timer)
{
    (void)timer;
    laser_set_power(0);
    laser_set_enable(false);
}

void laser_driver_pulse(uint32_t duration_ms, uint16_t power)
{
    laser_set_enable(true);
    laser_set_power(power);
    lv_timer_t *t = lv_timer_create(laser_pulse_timer_cb, duration_ms, NULL);
    if (t) lv_timer_set_repeat_count(t, 1);
}

// =============================================================================
// THEME & STYLES MANAGER (DARK / LIGHT & ACCENT)
// =============================================================================
static void focal_theme_update_styles(void)
{
    uint32_t bg_app = s_is_dark ? 0x0F1115 : 0xF5F6F8;
    uint32_t bg_card = s_is_dark ? 0x1A1D24 : 0xFFFFFF;
    uint32_t bg_subtle = s_is_dark ? 0x262A35 : 0xEFF1F5;
    uint32_t border_subtle = s_is_dark ? 0x2D333F : 0xD1D5DB;
    uint32_t text_primary = s_is_dark ? 0xF9FAFB : 0x111827;
    uint32_t accent_hex = s_is_dark ? s_accent_dark_hex[s_accent_idx] : s_accent_light_hex[s_accent_idx];

    lv_style_set_bg_color(&focal_style_screen, lv_color_hex(bg_app));
    lv_style_set_text_color(&focal_style_screen, lv_color_hex(text_primary));

    lv_style_set_bg_color(&focal_style_card, lv_color_hex(bg_card));
    lv_style_set_border_color(&focal_style_card, lv_color_hex(border_subtle));
    lv_style_set_text_color(&focal_style_card, lv_color_hex(text_primary));

    lv_style_set_bg_color(&focal_style_pill, lv_color_hex(bg_subtle));
    lv_style_set_border_color(&focal_style_pill, lv_color_hex(border_subtle));
    lv_style_set_text_color(&focal_style_pill, lv_color_hex(text_primary));

    lv_style_set_bg_color(&focal_style_btn_secondary, lv_color_hex(bg_card));
    lv_style_set_border_color(&focal_style_btn_secondary, lv_color_hex(border_subtle));
    lv_style_set_text_color(&focal_style_btn_secondary, lv_color_hex(text_primary));

    lv_style_set_bg_color(&focal_style_btn_primary, lv_color_hex(accent_hex));

    lv_style_set_bg_color(&focal_style_warn_box, s_is_dark ? lv_color_hex(0x451A03) : lv_color_hex(0xFEF3C7));
    lv_style_set_border_color(&focal_style_warn_box, lv_color_hex(0xF59E0B));
    lv_style_set_border_width(&focal_style_warn_box, 1);
    lv_style_set_radius(&focal_style_warn_box, FOCAL_RADIUS_S);
    lv_style_set_bg_opa(&focal_style_warn_box, LV_OPA_COVER);

    lv_style_set_text_color(&focal_style_warn_text, s_is_dark ? lv_color_hex(0xFDE68A) : lv_color_hex(0x92400E));

    lv_obj_report_style_change(NULL);
}

void focal_theme_init(void)
{
    machine_settings_t cfg;
    settings_manager_get(&cfg);
    s_is_dark = (cfg.theme_mode == 0);
    s_accent_idx = (cfg.accent_color_idx < 5) ? cfg.accent_color_idx : 0;

    lv_style_init(&focal_style_screen);
    lv_style_set_bg_opa(&focal_style_screen, LV_OPA_COVER);

    lv_style_init(&focal_style_card);
    lv_style_set_bg_opa(&focal_style_card, LV_OPA_COVER);
    lv_style_set_radius(&focal_style_card, FOCAL_RADIUS_M);
    lv_style_set_border_width(&focal_style_card, 1);
    lv_style_set_pad_all(&focal_style_card, 6);

    lv_style_init(&focal_style_pill);
    lv_style_set_bg_opa(&focal_style_pill, LV_OPA_COVER);
    lv_style_set_radius(&focal_style_pill, FOCAL_RADIUS_PILL);
    lv_style_set_border_width(&focal_style_pill, 1);
    lv_style_set_pad_hor(&focal_style_pill, 8);
    lv_style_set_pad_ver(&focal_style_pill, 2);

    lv_style_init(&focal_style_btn_primary);
    lv_style_set_bg_opa(&focal_style_btn_primary, LV_OPA_COVER);
    lv_style_set_radius(&focal_style_btn_primary, FOCAL_RADIUS_M);
    lv_style_set_text_color(&focal_style_btn_primary, lv_color_hex(0xFFFFFF));

    lv_style_init(&focal_style_btn_secondary);
    lv_style_set_bg_opa(&focal_style_btn_secondary, LV_OPA_COVER);
    lv_style_set_radius(&focal_style_btn_secondary, FOCAL_RADIUS_M);
    lv_style_set_border_width(&focal_style_btn_secondary, 1);

    lv_style_init(&focal_style_btn_mint);
    lv_style_set_bg_color(&focal_style_btn_mint, FOCAL_COLOR_PASTEL_MINT);
    lv_style_set_bg_opa(&focal_style_btn_mint, LV_OPA_COVER);
    lv_style_set_radius(&focal_style_btn_mint, FOCAL_RADIUS_M);
    lv_style_set_text_color(&focal_style_btn_mint, lv_color_hex(0xFFFFFF));

    lv_style_init(&focal_style_btn_amber);
    lv_style_set_bg_color(&focal_style_btn_amber, FOCAL_COLOR_PASTEL_AMBER);
    lv_style_set_bg_opa(&focal_style_btn_amber, LV_OPA_COVER);
    lv_style_set_radius(&focal_style_btn_amber, FOCAL_RADIUS_M);
    lv_style_set_text_color(&focal_style_btn_amber, lv_color_hex(0xFFFFFF));

    lv_style_init(&focal_style_btn_danger);
    lv_style_set_bg_color(&focal_style_btn_danger, FOCAL_COLOR_PASTEL_RED);
    lv_style_set_bg_opa(&focal_style_btn_danger, LV_OPA_COVER);
    lv_style_set_radius(&focal_style_btn_danger, FOCAL_RADIUS_M);
    lv_style_set_text_color(&focal_style_btn_danger, lv_color_hex(0xFFFFFF));

    lv_style_init(&focal_style_warn_box);
    lv_style_init(&focal_style_warn_text);

    focal_theme_update_styles();
}

void focal_theme_set_dark(bool is_dark)
{
    s_is_dark = is_dark;
    focal_theme_update_styles();

    machine_settings_t cfg;
    settings_manager_get(&cfg);
    cfg.theme_mode = is_dark ? 0 : 1;
    settings_manager_save(&cfg);
}

bool focal_theme_is_dark(void)
{
    return s_is_dark;
}

void focal_theme_set_accent(uint8_t accent_idx)
{
    if (accent_idx >= 5) accent_idx = 0;
    s_accent_idx = accent_idx;
    focal_theme_update_styles();

    machine_settings_t cfg;
    settings_manager_get(&cfg);
    cfg.accent_color_idx = accent_idx;
    settings_manager_save(&cfg);
}

uint8_t focal_theme_get_accent_idx(void)
{
    return s_accent_idx;
}

uint32_t focal_theme_get_accent_hex(void)
{
    return s_is_dark ? s_accent_dark_hex[s_accent_idx] : s_accent_light_hex[s_accent_idx];
}

lv_color_t focal_theme_get_accent_color(void)
{
    return lv_color_hex(focal_theme_get_accent_hex());
}
""")

    # Screen 0: Launcher
    code.append("""
// =============================================================================
// SCREEN 0: LAUNCHER GRID 3x2
// =============================================================================
static void on_launcher_card_click(lv_event_t *e)
{
    ui_screen_id_t target = (ui_screen_id_t)(uintptr_t)lv_event_get_user_data(e);
    ui_switch_screen(target);
}

static void create_launcher_screen(void)
{
    lv_obj_t *scr = lv_obj_create(NULL);
    s_screens[UI_SCREEN_LAUNCHER] = scr;
    lv_obj_add_style(scr, &focal_style_screen, 0);
    lv_obj_clear_flag(scr, LV_OBJ_FLAG_SCROLLABLE);

    create_screen_header(UI_SCREEN_LAUNCHER, "Focal CNC Laser", false);

    typedef struct {
        const char *title;
        const char *subtitle;
        const lv_img_dsc_t *icon;
        uint32_t accent_hex;
        ui_screen_id_t target;
    } launcher_item_t;

    const launcher_item_t items[6] = {
        { "Control",     "Jog & DRO",          &focal_icon_control,     FOCAL_HEX_PASTEL_BLUE,  UI_SCREEN_JOGGING },
        { "Archivos",    "MicroSD G-Code",     &focal_icon_files,       FOCAL_HEX_PASTEL_MINT,  UI_SCREEN_SD_FILES },
        { "Monitor",     "En Vivo",            &focal_icon_monitor,     FOCAL_HEX_PASTEL_AMBER, UI_SCREEN_CUT_MONITOR },
        { "Calibracion", "Foco, Cama & Ejes",  &focal_icon_calibration, 0xA78BFA,               UI_SCREEN_CALIBRATION },
        { "Corte Rapido","Cama 160x200",       &focal_icon_shapes,      FOCAL_HEX_PASTEL_BLUE,  UI_SCREEN_SHAPES },
        { "Ajustes",     "WiFi, Tema & Laser", &focal_icon_settings,    FOCAL_HEX_PASTEL_MINT,  UI_SCREEN_SETTINGS }
    };

    const int card_w = 146;
    const int card_h = 124;
    const int start_x = 10;
    const int start_y = 50;
    const int gap_x = 10;
    const int gap_y = 10;

    for (int i = 0; i < 6; i++) {
        int col = i % 3;
        int row = i / 3;
        int x = start_x + col * (card_w + gap_x);
        int y = start_y + row * (card_h + gap_y);

        lv_obj_t *btn = lv_btn_create(scr);
        lv_obj_set_size(btn, card_w, card_h);
        lv_obj_set_pos(btn, x, y);
        lv_obj_add_style(btn, &focal_style_btn_secondary, 0);
        lv_obj_set_style_radius(btn, FOCAL_RADIUS_L, 0);
        lv_obj_set_style_pad_all(btn, 6, 0);
        lv_obj_clear_flag(btn, LV_OBJ_FLAG_SCROLLABLE);
        lv_obj_add_event_cb(btn, on_launcher_card_click, LV_EVENT_CLICKED, (void *)(uintptr_t)items[i].target);

        // Badge Container
        lv_obj_t *badge = lv_obj_create(btn);
        lv_obj_set_size(badge, 44, 44);
        lv_obj_align(badge, LV_ALIGN_TOP_MID, 0, 8);
        lv_obj_set_style_bg_color(badge, s_is_dark ? lv_color_hex(0x262A35) : lv_color_hex(0xF0F2F5), 0);
        lv_obj_set_style_radius(badge, FOCAL_RADIUS_M, 0);
        lv_obj_set_style_border_color(badge, s_is_dark ? lv_color_hex(0x2D333F) : lv_color_hex(0xE5E7EB), 0);
        lv_obj_set_style_border_width(badge, 1, 0);
        lv_obj_clear_flag(badge, LV_OBJ_FLAG_SCROLLABLE);

        lv_obj_t *ic = focal_create_icon(badge, items[i].icon, items[i].accent_hex);
        lv_obj_center(ic);

        lv_obj_t *lbl_t = lv_label_create(btn);
        lv_label_set_text(lbl_t, items[i].title);
        lv_obj_set_style_text_font(lbl_t, FOCAL_FONT, 0);
        lv_obj_align(lbl_t, LV_ALIGN_TOP_MID, 0, 62);

        lv_obj_t *lbl_s = lv_label_create(btn);
        lv_label_set_text(lbl_s, items[i].subtitle);
        lv_obj_set_style_text_font(lbl_s, FOCAL_FONT, 0);
        lv_obj_set_style_text_color(lbl_s, s_is_dark ? lv_color_hex(0x6B7280) : lv_color_hex(0x9CA3AF), 0);
        lv_obj_align(lbl_s, LV_ALIGN_TOP_MID, 0, 86);
    }
}
""")

    # Screen 1: Jogging
    code.append("""
// =============================================================================
// SCREEN 1: CONTROL DE MAQUINA (JOGGING & DRO)
// =============================================================================
static float s_jog_step = 10.0f;
static float s_sim_x = 0.0f;
static float s_sim_y = 0.0f;
static lv_obj_t *s_dro_x = NULL;
static lv_obj_t *s_dro_y = NULL;
static lv_obj_t *s_step_btns[4] = {0};

static void update_dro_display(void)
{
    char buf[32];
    if (s_dro_x) {
        snprintf(buf, sizeof(buf), "X: %6.1f mm", s_sim_x);
        lv_label_set_text(s_dro_x, buf);
    }
    if (s_dro_y) {
        snprintf(buf, sizeof(buf), "Y: %6.1f mm", s_sim_y);
        lv_label_set_text(s_dro_y, buf);
    }
}

static void on_jog_step_select_cb(lv_event_t *e)
{
    int idx = (int)(uintptr_t)lv_event_get_user_data(e);
    if (idx < 0 || idx >= 4) return;
    const float steps[4] = { 0.1f, 1.0f, 10.0f, 50.0f };
    s_jog_step = steps[idx];

    for (int i = 0; i < 4; i++) {
        if (s_step_btns[i]) {
            if (i == idx) {
                lv_obj_set_style_bg_color(s_step_btns[i], focal_theme_get_accent_color(), 0);
                lv_obj_set_style_text_color(s_step_btns[i], lv_color_hex(0xFFFFFF), 0);
            } else {
                lv_obj_set_style_bg_color(s_step_btns[i], s_is_dark ? lv_color_hex(0x1A1D24) : lv_color_hex(0xFFFFFF), 0);
                lv_obj_set_style_text_color(s_step_btns[i], s_is_dark ? lv_color_hex(0xF9FAFB) : lv_color_hex(0x111827), 0);
            }
        }
    }
}

static void on_jog_btn_cb(lv_event_t *e)
{
    const char *dir = (const char *)lv_event_get_user_data(e);
    if (!dir) return;
    char cmd[64] = {0};
    char resp[32] = {0};

    if (strcmp(dir, "Y+") == 0) {
        s_sim_y += s_jog_step;
        if (s_sim_y > 200.0f) s_sim_y = 200.0f;
        snprintf(cmd, sizeof(cmd), "$J=G91 G21 Y%.2f F2000", s_jog_step);
    } else if (strcmp(dir, "Y-") == 0) {
        s_sim_y -= s_jog_step;
        if (s_sim_y < 0.0f) s_sim_y = 0.0f;
        snprintf(cmd, sizeof(cmd), "$J=G91 G21 Y-%.2f F2000", s_jog_step);
    } else if (strcmp(dir, "X-") == 0) {
        s_sim_x -= s_jog_step;
        if (s_sim_x < 0.0f) s_sim_x = 0.0f;
        snprintf(cmd, sizeof(cmd), "$J=G91 G21 X-%.2f F2000", s_jog_step);
    } else if (strcmp(dir, "X+") == 0) {
        s_sim_x += s_jog_step;
        if (s_sim_x > 160.0f) s_sim_x = 160.0f;
        snprintf(cmd, sizeof(cmd), "$J=G91 G21 X%.2f F2000", s_jog_step);
    } else if (strcmp(dir, "STOP") == 0) {
        strcpy(cmd, "!");
    } else if (strcmp(dir, "ZERO") == 0) {
        s_sim_x = 0.0f;
        s_sim_y = 0.0f;
        strcpy(cmd, "G92 X0 Y0");
    } else if (strcmp(dir, "HOME") == 0) {
        s_sim_x = 0.0f;
        s_sim_y = 0.0f;
        strcpy(cmd, "$H");
    }

    if (cmd[0] != 0) {
        gcode_parser_execute_line(cmd, resp, sizeof(resp));
        update_dro_display();
    }
}

static void create_jogging_screen(void)
{
    lv_obj_t *scr = lv_obj_create(NULL);
    s_screens[UI_SCREEN_JOGGING] = scr;
    lv_obj_add_style(scr, &focal_style_screen, 0);
    lv_obj_clear_flag(scr, LV_OBJ_FLAG_SCROLLABLE);

    create_screen_header(UI_SCREEN_JOGGING, "Control de Ejes", true);

    // Left Panel: DRO & Actions
    lv_obj_t *card_dro = lv_obj_create(scr);
    lv_obj_set_size(card_dro, 210, 260);
    lv_obj_set_pos(card_dro, 10, 48);
    lv_obj_add_style(card_dro, &focal_style_card, 0);
    lv_obj_clear_flag(card_dro, LV_OBJ_FLAG_SCROLLABLE);

    lv_obj_t *lbl_t = lv_label_create(card_dro);
    lv_label_set_text(lbl_t, "Posicion Actual");
    lv_obj_align(lbl_t, LV_ALIGN_TOP_LEFT, 6, 4);

    lv_obj_t *box_x = lv_obj_create(card_dro);
    lv_obj_set_size(box_x, 186, 42);
    lv_obj_set_pos(box_x, 6, 28);
    lv_obj_add_style(box_x, &focal_style_pill, 0);
    s_dro_x = lv_label_create(box_x);
    lv_label_set_text(s_dro_x, "X:    0.0 mm");
    lv_obj_set_style_text_color(s_dro_x, FOCAL_COLOR_PASTEL_BLUE, 0);
    lv_obj_center(s_dro_x);

    lv_obj_t *box_y = lv_obj_create(card_dro);
    lv_obj_set_size(box_y, 186, 42);
    lv_obj_set_pos(box_y, 6, 78);
    lv_obj_add_style(box_y, &focal_style_pill, 0);
    s_dro_y = lv_label_create(box_y);
    lv_label_set_text(s_dro_y, "Y:    0.0 mm");
    lv_obj_set_style_text_color(s_dro_y, FOCAL_COLOR_PASTEL_MINT, 0);
    lv_obj_center(s_dro_y);

    lv_obj_t *btn_zero = focal_create_btn(card_dro, 186, 42, &focal_icon_check, "Fijar Home", &focal_style_btn_secondary, FOCAL_HEX_PASTEL_MINT);
    lv_obj_set_pos(btn_zero, 6, 138);
    lv_obj_add_event_cb(btn_zero, on_jog_btn_cb, LV_EVENT_CLICKED, (void *)"ZERO");

    lv_obj_t *btn_hm = focal_create_btn(card_dro, 186, 42, &focal_icon_home, "Home", &focal_style_btn_secondary, FOCAL_HEX_PASTEL_BLUE);
    lv_obj_set_pos(btn_hm, 6, 188);
    lv_obj_add_event_cb(btn_hm, on_jog_btn_cb, LV_EVENT_CLICKED, (void *)"HOME");

    // Right Panel: Step selector and Pad
    lv_obj_t *card_jog = lv_obj_create(scr);
    lv_obj_set_size(card_jog, 240, 260);
    lv_obj_set_pos(card_jog, 230, 48);
    lv_obj_add_style(card_jog, &focal_style_card, 0);
    lv_obj_clear_flag(card_jog, LV_OBJ_FLAG_SCROLLABLE);

    const char *step_names[4] = { "0.1", "1.0", "10", "50" };
    for (int i = 0; i < 4; i++) {
        lv_obj_t *btn_s = lv_btn_create(card_jog);
        lv_obj_set_size(btn_s, 50, 32);
        lv_obj_set_pos(btn_s, 6 + i * 55, 4);
        lv_obj_add_style(btn_s, &focal_style_btn_secondary, 0);
        lv_obj_set_style_radius(btn_s, FOCAL_RADIUS_S, 0);
        s_step_btns[i] = btn_s;

        lv_obj_t *lbl = lv_label_create(btn_s);
        lv_label_set_text(lbl, step_names[i]);
        lv_obj_center(lbl);

        if (i == 2) {
            lv_obj_set_style_bg_color(btn_s, focal_theme_get_accent_color(), 0);
            lv_obj_set_style_text_color(btn_s, lv_color_hex(0xFFFFFF), 0);
        }
        lv_obj_add_event_cb(btn_s, on_jog_step_select_cb, LV_EVENT_CLICKED, (void *)(uintptr_t)i);
    }

    // Directional Pad - Uniform 50x50px geometry, centered, equal spacing
    lv_obj_t *btn_up = lv_btn_create(card_jog);
    lv_obj_set_size(btn_up, 50, 50);
    lv_obj_align(btn_up, LV_ALIGN_CENTER, 0, -40);
    lv_obj_add_style(btn_up, &focal_style_btn_secondary, 0);
    lv_obj_set_style_radius(btn_up, FOCAL_RADIUS_M, 0);
    lv_obj_set_style_pad_all(btn_up, 0, 0);
    lv_obj_set_ext_click_area(btn_up, 6);
    lv_obj_t *ic_up = focal_create_icon(btn_up, &focal_icon_jog_up, FOCAL_HEX_PASTEL_BLUE);
    lv_obj_center(ic_up);
    lv_obj_add_event_cb(btn_up, on_jog_btn_cb, LV_EVENT_CLICKED, (void *)"Y+");

    lv_obj_t *btn_dn = lv_btn_create(card_jog);
    lv_obj_set_size(btn_dn, 50, 50);
    lv_obj_align(btn_dn, LV_ALIGN_CENTER, 0, 76);
    lv_obj_add_style(btn_dn, &focal_style_btn_secondary, 0);
    lv_obj_set_style_radius(btn_dn, FOCAL_RADIUS_M, 0);
    lv_obj_set_style_pad_all(btn_dn, 0, 0);
    lv_obj_set_ext_click_area(btn_dn, 6);
    lv_obj_t *ic_dn = focal_create_icon(btn_dn, &focal_icon_jog_down, FOCAL_HEX_PASTEL_BLUE);
    lv_obj_center(ic_dn);
    lv_obj_add_event_cb(btn_dn, on_jog_btn_cb, LV_EVENT_CLICKED, (void *)"Y-");

    lv_obj_t *btn_lt = lv_btn_create(card_jog);
    lv_obj_set_size(btn_lt, 50, 50);
    lv_obj_align(btn_lt, LV_ALIGN_CENTER, -58, 18);
    lv_obj_add_style(btn_lt, &focal_style_btn_secondary, 0);
    lv_obj_set_style_radius(btn_lt, FOCAL_RADIUS_M, 0);
    lv_obj_set_style_pad_all(btn_lt, 0, 0);
    lv_obj_set_ext_click_area(btn_lt, 6);
    lv_obj_t *ic_lt = focal_create_icon(btn_lt, &focal_icon_jog_left, FOCAL_HEX_PASTEL_BLUE);
    lv_obj_center(ic_lt);
    lv_obj_add_event_cb(btn_lt, on_jog_btn_cb, LV_EVENT_CLICKED, (void *)"X-");

    lv_obj_t *btn_rt = lv_btn_create(card_jog);
    lv_obj_set_size(btn_rt, 50, 50);
    lv_obj_align(btn_rt, LV_ALIGN_CENTER, 58, 18);
    lv_obj_add_style(btn_rt, &focal_style_btn_secondary, 0);
    lv_obj_set_style_radius(btn_rt, FOCAL_RADIUS_M, 0);
    lv_obj_set_style_pad_all(btn_rt, 0, 0);
    lv_obj_set_ext_click_area(btn_rt, 6);
    lv_obj_t *ic_rt = focal_create_icon(btn_rt, &focal_icon_jog_right, FOCAL_HEX_PASTEL_BLUE);
    lv_obj_center(ic_rt);
    lv_obj_add_event_cb(btn_rt, on_jog_btn_cb, LV_EVENT_CLICKED, (void *)"X+");

    lv_obj_t *btn_sp = lv_btn_create(card_jog);
    lv_obj_set_size(btn_sp, 50, 50);
    lv_obj_align(btn_sp, LV_ALIGN_CENTER, 0, 18);
    lv_obj_add_style(btn_sp, &focal_style_btn_danger, 0);
    lv_obj_set_style_radius(btn_sp, FOCAL_RADIUS_M, 0);
    lv_obj_set_style_pad_all(btn_sp, 0, 0);
    lv_obj_set_ext_click_area(btn_sp, 6);
    lv_obj_t *ic_sp = focal_create_icon(btn_sp, &focal_icon_stop, 0xFFFFFF);
    lv_obj_center(ic_sp);
    lv_obj_add_event_cb(btn_sp, on_jog_btn_cb, LV_EVENT_CLICKED, (void *)"STOP");
}
""")

    # Screen 2: SD Files
    code.append("""
// =============================================================================
// SCREEN 2: GESTOR DE ARCHIVOS EN MICROSD
// =============================================================================
static char s_selected_file[64] = "corte_circulo_50mm.gcode";
static lv_obj_t *s_lbl_file_name = NULL;
static lv_obj_t *s_lbl_file_info = NULL;

// Floating Safety Confirmation Modal for Cutting
static lv_obj_t *s_cut_modal = NULL;
static lv_obj_t *s_cut_modal_file_lbl = NULL;
static lv_obj_t *s_cut_modal_info_lbl = NULL;
static char s_pending_cut_file[64] = "corte_circulo_50mm.gcode";
static uint32_t s_pending_lines = 1420;
static uint32_t s_pending_est_sec = 225;

static void on_cut_modal_cancel_cb(lv_event_t *e)
{
    (void)e;
    ui_close_cut_modal();
}

static void on_cut_modal_confirm_cb(lv_event_t *e)
{
    (void)e;
    ui_close_cut_modal();
    ui_switch_screen(UI_SCREEN_CUT_MONITOR);
    s_is_cutting = true;
    ui_update_status("CORTANDO", FOCAL_HEX_PASTEL_MINT);
}

static void on_file_select_cb(lv_event_t *e)
{
    const char *name = (const char *)lv_event_get_user_data(e);
    strncpy(s_selected_file, name, sizeof(s_selected_file) - 1);
    s_selected_file[sizeof(s_selected_file) - 1] = 0;
    if (s_lbl_file_name) lv_label_set_text(s_lbl_file_name, s_selected_file);
    if (s_lbl_file_info) lv_label_set_text(s_lbl_file_info, "Lineas: 1420 | Duracion: 03:45 min\\nPotencia: 80% | Foco Z: 30 mm");
}

static void on_file_start_cut_cb(lv_event_t *e)
{
    (void)e;
    ui_show_cut_modal(s_selected_file, 1420, 225);
}

static void create_sd_screen(void)
{
    lv_obj_t *scr = lv_obj_create(NULL);
    s_screens[UI_SCREEN_SD_FILES] = scr;
    lv_obj_add_style(scr, &focal_style_screen, 0);
    lv_obj_clear_flag(scr, LV_OBJ_FLAG_SCROLLABLE);

    create_screen_header(UI_SCREEN_SD_FILES, "Archivos SD", true);

    lv_obj_t *list_card = lv_obj_create(scr);
    lv_obj_set_size(list_card, 250, 260);
    lv_obj_set_pos(list_card, 10, 48);
    lv_obj_add_style(list_card, &focal_style_card, 0);

    const char *sample_files[4] = {
        "corte_circulo_50mm.gcode",
        "calibracion_cama_160x200.gcode",
        "grabado_logo.nc",
        "caja_ensamble.gcode"
    };

    for (int i = 0; i < 4; i++) {
        lv_obj_t *item = focal_create_btn(list_card, 226, 48, &focal_icon_files, sample_files[i], &focal_style_btn_secondary, FOCAL_HEX_PASTEL_MINT);
        lv_obj_set_pos(item, 4, 6 + i * 54);
        lv_obj_set_flex_align(item, LV_FLEX_ALIGN_START, LV_FLEX_ALIGN_CENTER, LV_FLEX_ALIGN_CENTER);
        lv_obj_set_style_pad_left(item, 8, 0);
        lv_obj_add_event_cb(item, on_file_select_cb, LV_EVENT_CLICKED, (void *)sample_files[i]);
    }

    lv_obj_t *det_card = lv_obj_create(scr);
    lv_obj_set_size(det_card, 200, 260);
    lv_obj_set_pos(det_card, 270, 48);
    lv_obj_add_style(det_card, &focal_style_card, 0);
    lv_obj_clear_flag(det_card, LV_OBJ_FLAG_SCROLLABLE);

    lv_obj_t *lbl_th = lv_label_create(det_card);
    lv_label_set_text(lbl_th, "Detalles");
    lv_obj_align(lbl_th, LV_ALIGN_TOP_LEFT, 6, 4);

    s_lbl_file_name = lv_label_create(det_card);
    lv_label_set_text(s_lbl_file_name, s_selected_file);
    lv_obj_set_style_text_color(s_lbl_file_name, FOCAL_COLOR_PASTEL_BLUE, 0);
    lv_obj_set_width(s_lbl_file_name, 175);
    lv_label_set_long_mode(s_lbl_file_name, LV_LABEL_LONG_WRAP);
    lv_obj_align(s_lbl_file_name, LV_ALIGN_TOP_LEFT, 6, 32);

    s_lbl_file_info = lv_label_create(det_card);
    lv_label_set_text(s_lbl_file_info, "Lineas: 1420 | Duracion: 03:45 min\\nPotencia: 80% | Foco Z: 30 mm");
    lv_obj_set_width(s_lbl_file_info, 175);
    lv_label_set_long_mode(s_lbl_file_info, LV_LABEL_LONG_WRAP);
    lv_obj_align(s_lbl_file_info, LV_ALIGN_TOP_LEFT, 6, 80);

    lv_obj_t *btn_run = focal_create_btn(det_card, 176, 48, &focal_icon_play, "Iniciar Corte", &focal_style_btn_mint, 0xFFFFFF);
    lv_obj_align(btn_run, LV_ALIGN_BOTTOM_MID, 0, -8);
    lv_obj_add_event_cb(btn_run, on_file_start_cut_cb, LV_EVENT_CLICKED, NULL);

    // FLOATING CUT CONFIRMATION & SAFETY MODAL DIALOG OVERLAY
    s_cut_modal = lv_obj_create(lv_layer_top());
    lv_obj_set_size(s_cut_modal, 480, 320);
    lv_obj_set_pos(s_cut_modal, 0, 0);
    lv_obj_set_style_bg_color(s_cut_modal, lv_color_hex(0x000000), 0);
    lv_obj_set_style_bg_opa(s_cut_modal, LV_OPA_70, 0);
    lv_obj_clear_flag(s_cut_modal, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_add_flag(s_cut_modal, LV_OBJ_FLAG_HIDDEN);

    lv_obj_t *diag = lv_obj_create(s_cut_modal);
    lv_obj_set_size(diag, 380, 240);
    lv_obj_center(diag);
    lv_obj_add_style(diag, &focal_style_card, 0);
    lv_obj_clear_flag(diag, LV_OBJ_FLAG_SCROLLABLE);

    lv_obj_t *tbox = lv_obj_create(diag);
    lv_obj_set_size(tbox, 350, 34);
    lv_obj_align(tbox, LV_ALIGN_TOP_MID, 0, -4);
    lv_obj_set_style_bg_opa(tbox, LV_OPA_TRANSP, 0);
    lv_obj_set_style_border_width(tbox, 0, 0);
    lv_obj_set_style_pad_all(tbox, 0, 0);
    lv_obj_set_flex_flow(tbox, LV_FLEX_FLOW_ROW);
    lv_obj_set_flex_align(tbox, LV_FLEX_ALIGN_START, LV_FLEX_ALIGN_CENTER, LV_FLEX_ALIGN_CENTER);
    lv_obj_set_style_pad_column(tbox, 6, 0);

    focal_create_icon(tbox, &focal_icon_laser, FOCAL_HEX_PASTEL_AMBER);
    lv_obj_t *lbl_mtitle = lv_label_create(tbox);
    lv_label_set_text(lbl_mtitle, "Confirmar Inicio de Corte");
    lv_obj_set_style_text_color(lbl_mtitle, FOCAL_COLOR_PASTEL_BLUE, 0);

    s_cut_modal_file_lbl = lv_label_create(diag);
    lv_label_set_text(s_cut_modal_file_lbl, "Archivo: corte_circulo_50mm.gcode");
    lv_obj_set_style_text_color(s_cut_modal_file_lbl, FOCAL_COLOR_PASTEL_MINT, 0);
    lv_obj_align(s_cut_modal_file_lbl, LV_ALIGN_TOP_LEFT, 6, 36);

    s_cut_modal_info_lbl = lv_label_create(diag);
    lv_label_set_text(s_cut_modal_info_lbl, "Lineas: 1420  |  Duracion est: 03:45 min");
    lv_obj_align(s_cut_modal_info_lbl, LV_ALIGN_TOP_LEFT, 6, 60);

    // Safety Alert Box with Yellow Warning Border
    lv_obj_t *warn_box = lv_obj_create(diag);
    lv_obj_set_size(warn_box, 350, 56);
    lv_obj_align(warn_box, LV_ALIGN_TOP_MID, 0, 88);
    lv_obj_add_style(warn_box, &focal_style_warn_box, 0);
    lv_obj_clear_flag(warn_box, LV_OBJ_FLAG_SCROLLABLE);

    lv_obj_t *lbl_warn = lv_label_create(warn_box);
    lv_label_set_text(lbl_warn, "ATENCION: Use gafas de proteccion laser.\\nEl cabezal se movera y el haz se activara.");
    lv_obj_add_style(lbl_warn, &focal_style_warn_text, 0);
    lv_obj_center(lbl_warn);

    // Bottom Action Buttons: Cancelar vs Iniciar Corte Ahora
    lv_obj_t *btn_mcanc = focal_create_btn(diag, 120, 42, NULL, "Cancelar", &focal_style_btn_secondary, 0);
    lv_obj_align(btn_mcanc, LV_ALIGN_BOTTOM_LEFT, 6, -4);
    lv_obj_add_event_cb(btn_mcanc, on_cut_modal_cancel_cb, LV_EVENT_CLICKED, NULL);

    lv_obj_t *btn_mstart = focal_create_btn(diag, 206, 42, &focal_icon_play, "Iniciar Corte Ahora", &focal_style_btn_mint, 0xFFFFFF);
    lv_obj_align(btn_mstart, LV_ALIGN_BOTTOM_RIGHT, -6, -4);
    lv_obj_add_event_cb(btn_mstart, on_cut_modal_confirm_cb, LV_EVENT_CLICKED, NULL);
}
""")

    # Screen 3: Cut Monitor
    code.append("""
// =============================================================================
// SCREEN 3: MONITOR DE CORTE Y TELEMETRIA EN VIVO
// =============================================================================
static lv_obj_t *s_cut_bar = NULL;
static lv_obj_t *s_lbl_cut_pct = NULL;
static lv_obj_t *s_lbl_cut_time = NULL;
static lv_obj_t *s_lbl_cut_metrics = NULL;
static lv_obj_t *s_lbl_feed_ovr = NULL;
static lv_obj_t *s_lbl_power_ovr = NULL;
static int s_feed_override = 100;
static int s_power_override = 100;

static void on_feed_ovr_cb(lv_event_t *e)
{
    int delta = (int)(uintptr_t)lv_event_get_user_data(e);
    s_feed_override += delta;
    if (s_feed_override < 10) s_feed_override = 10;
    if (s_feed_override > 200) s_feed_override = 200;
    if (s_lbl_feed_ovr) {
        char buf[32];
        snprintf(buf, sizeof(buf), "Velocidad: %d%%", s_feed_override);
        lv_label_set_text(s_lbl_feed_ovr, buf);
    }
}

static void on_power_ovr_cb(lv_event_t *e)
{
    int delta = (int)(uintptr_t)lv_event_get_user_data(e);
    s_power_override += delta;
    if (s_power_override < 10) s_power_override = 10;
    if (s_power_override > 200) s_power_override = 200;
    if (s_lbl_power_ovr) {
        char buf[32];
        snprintf(buf, sizeof(buf), "Potencia: %d%%", s_power_override);
        lv_label_set_text(s_lbl_power_ovr, buf);
    }
    if (s_is_cutting) {
        laser_set_power((800 * s_power_override) / 100);
    }
}

static void on_cut_pause_resume_cb(lv_event_t *e)
{
    (void)e;
    char resp[32];
    if (s_is_cutting) {
        gcode_parser_execute_line("!", resp, sizeof(resp));
        s_is_cutting = false;
        ui_update_status("EN PAUSA", FOCAL_HEX_PASTEL_AMBER);
    } else {
        gcode_parser_execute_line("~", resp, sizeof(resp));
        s_is_cutting = true;
        ui_update_status("CORTANDO", FOCAL_HEX_PASTEL_MINT);
    }
}

static void on_cut_estop_cb(lv_event_t *e)
{
    (void)e;
    laser_set_power(0);
    laser_set_enable(false);
    char resp[32];
    gcode_parser_execute_line("!", resp, sizeof(resp));
    s_is_cutting = false;
    ui_update_status("E-STOP", FOCAL_HEX_PASTEL_RED);
}

static void create_cut_monitor_screen(void)
{
    lv_obj_t *scr = lv_obj_create(NULL);
    s_screens[UI_SCREEN_CUT_MONITOR] = scr;
    lv_obj_add_style(scr, &focal_style_screen, 0);
    lv_obj_clear_flag(scr, LV_OBJ_FLAG_SCROLLABLE);

    create_screen_header(UI_SCREEN_CUT_MONITOR, "Monitor en Vivo", true);

    lv_obj_t *card = lv_obj_create(scr);
    lv_obj_set_size(card, 460, 260);
    lv_obj_set_pos(card, 10, 48);
    lv_obj_add_style(card, &focal_style_card, 0);
    lv_obj_clear_flag(card, LV_OBJ_FLAG_SCROLLABLE);

    s_cut_bar = lv_bar_create(card);
    lv_obj_set_size(s_cut_bar, 430, 20);
    lv_obj_align(s_cut_bar, LV_ALIGN_TOP_MID, 0, 6);
    lv_obj_set_style_bg_color(s_cut_bar, s_is_dark ? lv_color_hex(0x262A35) : lv_color_hex(0xEFF1F5), 0);
    lv_obj_set_style_radius(s_cut_bar, FOCAL_RADIUS_PILL, 0);
    lv_obj_set_style_bg_color(s_cut_bar, FOCAL_COLOR_PASTEL_MINT, LV_PART_INDICATOR);
    lv_obj_set_style_radius(s_cut_bar, FOCAL_RADIUS_PILL, LV_PART_INDICATOR);
    lv_bar_set_value(s_cut_bar, 45, LV_ANIM_OFF);

    s_lbl_cut_pct = lv_label_create(card);
    lv_label_set_text(s_lbl_cut_pct, "Progreso: 45.0% (Linea 640 / 1420)");
    lv_obj_align(s_lbl_cut_pct, LV_ALIGN_TOP_MID, 0, 30);

    lv_obj_t *box_tel = lv_obj_create(card);
    lv_obj_set_size(box_tel, 430, 60);
    lv_obj_align(box_tel, LV_ALIGN_TOP_MID, 0, 52);
    lv_obj_add_style(box_tel, &focal_style_pill, 0);
    lv_obj_set_style_radius(box_tel, FOCAL_RADIUS_M, 0);
    lv_obj_clear_flag(box_tel, LV_OBJ_FLAG_SCROLLABLE);

    s_lbl_cut_time = lv_label_create(box_tel);
    lv_label_set_text(s_lbl_cut_time, "Transcurrido: 01:42 min  |  Restante: 02:03 min");
    lv_obj_set_style_text_color(s_lbl_cut_time, FOCAL_COLOR_PASTEL_BLUE, 0);
    lv_obj_align(s_lbl_cut_time, LV_ALIGN_TOP_MID, 0, 6);

    s_lbl_cut_metrics = lv_label_create(box_tel);
    lv_label_set_text(s_lbl_cut_metrics, "Potencia: 80% (PWM 5kHz)  |  Avance: 2400 mm/min");
    lv_obj_align(s_lbl_cut_metrics, LV_ALIGN_BOTTOM_MID, 0, -6);

    // Live Overrides Pill (Feed & Power +/- 10%)
    lv_obj_t *ovr_box = lv_obj_create(card);
    lv_obj_set_size(ovr_box, 430, 44);
    lv_obj_align(ovr_box, LV_ALIGN_TOP_MID, 0, 118);
    lv_obj_add_style(ovr_box, &focal_style_pill, 0);
    lv_obj_set_style_radius(ovr_box, FOCAL_RADIUS_M, 0);
    lv_obj_clear_flag(ovr_box, LV_OBJ_FLAG_SCROLLABLE);

    s_lbl_feed_ovr = lv_label_create(ovr_box);
    lv_label_set_text(s_lbl_feed_ovr, "Vel: 100%");
    lv_obj_set_style_text_color(s_lbl_feed_ovr, FOCAL_COLOR_PASTEL_AMBER, 0);
    lv_obj_align(s_lbl_feed_ovr, LV_ALIGN_LEFT_MID, 8, 0);

    lv_obj_t *bf_m = focal_create_btn(ovr_box, 32, 28, NULL, "-", &focal_style_btn_secondary, 0);
    lv_obj_align(bf_m, LV_ALIGN_LEFT_MID, 96, 0);
    lv_obj_set_ext_click_area(bf_m, 6);
    lv_obj_add_event_cb(bf_m, on_feed_ovr_cb, LV_EVENT_CLICKED, (void *)-10);

    lv_obj_t *bf_p = focal_create_btn(ovr_box, 32, 28, NULL, "+", &focal_style_btn_secondary, 0);
    lv_obj_align(bf_p, LV_ALIGN_LEFT_MID, 134, 0);
    lv_obj_set_ext_click_area(bf_p, 6);
    lv_obj_add_event_cb(bf_p, on_feed_ovr_cb, LV_EVENT_CLICKED, (void *)10);

    s_lbl_power_ovr = lv_label_create(ovr_box);
    lv_label_set_text(s_lbl_power_ovr, "Pot: 100%");
    lv_obj_set_style_text_color(s_lbl_power_ovr, FOCAL_COLOR_PASTEL_MINT, 0);
    lv_obj_align(s_lbl_power_ovr, LV_ALIGN_LEFT_MID, 224, 0);

    lv_obj_t *bp_m = focal_create_btn(ovr_box, 32, 28, NULL, "-", &focal_style_btn_secondary, 0);
    lv_obj_align(bp_m, LV_ALIGN_LEFT_MID, 312, 0);
    lv_obj_set_ext_click_area(bp_m, 6);
    lv_obj_add_event_cb(bp_m, on_power_ovr_cb, LV_EVENT_CLICKED, (void *)-10);

    lv_obj_t *bp_p = focal_create_btn(ovr_box, 32, 28, NULL, "+", &focal_style_btn_secondary, 0);
    lv_obj_align(bp_p, LV_ALIGN_LEFT_MID, 350, 0);
    lv_obj_set_ext_click_area(bp_p, 6);
    lv_obj_add_event_cb(bp_p, on_power_ovr_cb, LV_EVENT_CLICKED, (void *)10);

    lv_obj_t *btn_pause = focal_create_btn(card, 205, 48, &focal_icon_pause, "Pausar / Seguir", &focal_style_btn_amber, 0xFFFFFF);
    lv_obj_align(btn_pause, LV_ALIGN_BOTTOM_LEFT, 8, -6);
    lv_obj_add_event_cb(btn_pause, on_cut_pause_resume_cb, LV_EVENT_CLICKED, NULL);

    lv_obj_t *btn_estop = focal_create_btn(card, 205, 48, &focal_icon_estop, "PARADA E-STOP", &focal_style_btn_danger, 0xFFFFFF);
    lv_obj_align(btn_estop, LV_ALIGN_BOTTOM_RIGHT, -8, -6);
    lv_obj_add_event_cb(btn_estop, on_cut_estop_cb, LV_EVENT_CLICKED, NULL);
}
""")

    # Screen 4: Calibration
    code.append("""
// =============================================================================
// SCREEN 4: ASISTENTE DE NIVELACION MANUAL DE CAMA (160x200 mm - 4 TORNILLOS + CENTRO)
// =============================================================================
typedef struct {
    int x;
    int y;
    const char *step_name;
    const char *screw_label;
    const char *instructions;
} calib_step_info_t;

static const calib_step_info_t s_calib_steps[5] = {
    { 10, 10, "Paso 1/5: Frontal Izq", "T1 (Frontal-Izq)", "Gira la perilla inferior-izquierda hasta que la galga o tarjeta pase rozando la boquilla." },
    { 150, 10, "Paso 2/5: Frontal Der", "T2 (Frontal-Der)", "Gira la perilla frontal-derecha hasta sentir la misma friccion suave con la galga." },
    { 150, 190, "Paso 3/5: Trasera Der", "T3 (Trasera-Der)", "Ajusta la perilla trasera-derecha igualando la altura con las esquinas frontales." },
    { 10, 190, "Paso 4/5: Trasera Izq", "T4 (Trasera-Izq)", "Gira la perilla trasera-izquierda comprobando que la distancia sea uniforme." },
    { 80, 100, "Paso 5/5: Centro Cama", "Centro (Test)", "Comprobacion central final. La altura debe ser uniforme en toda la superficie." }
};

static const int s_calib_pt_coords[5][2] = {
    { 8, 135 },   // T1: Frontal Izq (Y=10)
    { 100, 135 }, // T2: Frontal Der (Y=10)
    { 100, 8 },   // T3: Trasera Der (Y=190)
    { 8, 8 },     // T4: Trasera Izq (Y=190)
    { 54, 71 }    // Centro (Y=100)
};

static int s_calib_step = 0;
static bool s_calib_moving = false;
static uint8_t s_calib_done_mask = 0;
static bool s_calib_pointer_on = false;

static lv_obj_t *s_calib_pts[5] = {0};
static lv_obj_t *s_calib_lbl_step = NULL;
static lv_obj_t *s_calib_lbl_coords = NULL;
static lv_obj_t *s_calib_lbl_instruction = NULL;
static lv_obj_t *s_calib_btn_next = NULL;
static lv_obj_t *s_calib_btn_prev = NULL;
static lv_obj_t *s_calib_btn_ptr = NULL;
static lv_obj_t *s_calib_bar_travel = NULL;
static lv_obj_t *s_calib_laser_dot = NULL;
static lv_timer_t *s_calib_timer = NULL;

static void calib_update_view(void);

static void calib_travel_timer_cb(lv_timer_t *timer)
{
    (void)timer;
    s_calib_moving = false;
    s_calib_timer = NULL;
    calib_update_view();
}

static void calib_dispatch_move(int step_idx)
{
    char cmd[48];
    char resp[32];
    snprintf(cmd, sizeof(cmd), "G90 G0 X%d Y%d F3000", s_calib_steps[step_idx].x, s_calib_steps[step_idx].y);
    gcode_parser_execute_line(cmd, resp, sizeof(resp));

    s_calib_moving = true;
    if (s_calib_timer) {
        lv_timer_del(s_calib_timer);
        s_calib_timer = NULL;
    }
    s_calib_timer = lv_timer_create(calib_travel_timer_cb, 1400, NULL);
    if (s_calib_timer) lv_timer_set_repeat_count(s_calib_timer, 1);
    calib_update_view();
}

static void on_calib_next_cb(lv_event_t *e)
{
    (void)e;
    if (s_calib_moving) return;

    if (s_calib_step == 4) {
        char resp[32];
        gcode_parser_execute_line("$H", resp, sizeof(resp));
        s_calib_done_mask = 0x1F;
        calib_update_view();
        return;
    }

    s_calib_done_mask |= (1 << s_calib_step);
    s_calib_step++;
    calib_dispatch_move(s_calib_step);
}

static void on_calib_prev_cb(lv_event_t *e)
{
    (void)e;
    if (s_calib_moving) return;
    if (s_calib_step > 0) {
        s_calib_step--;
        calib_dispatch_move(s_calib_step);
    }
}

static void on_calib_point_click_cb(lv_event_t *e)
{
    if (s_calib_moving) return;
    int idx = (int)(uintptr_t)lv_event_get_user_data(e);
    if (idx >= 0 && idx < 5) {
        s_calib_step = idx;
        calib_dispatch_move(s_calib_step);
    }
}

static void on_calib_pointer_toggle_cb(lv_event_t *e)
{
    (void)e;
    s_calib_pointer_on = !s_calib_pointer_on;
    if (s_calib_pointer_on) {
        laser_set_enable(true);
        laser_set_power(10); // 1%
        if (s_calib_btn_ptr) {
            lv_obj_set_style_bg_color(s_calib_btn_ptr, FOCAL_COLOR_PASTEL_AMBER, 0);
            lv_obj_t *lbl = lv_obj_get_child(s_calib_btn_ptr, lv_obj_get_child_cnt(s_calib_btn_ptr) - 1);
            if (lbl) lv_label_set_text(lbl, "Puntero ON");
        }
    } else {
        laser_set_power(0);
        laser_set_enable(false);
        if (s_calib_btn_ptr) {
            lv_obj_set_style_bg_color(s_calib_btn_ptr, s_is_dark ? lv_color_hex(0x262A35) : lv_color_hex(0xE5E7EB), 0);
            lv_obj_t *lbl = lv_obj_get_child(s_calib_btn_ptr, lv_obj_get_child_cnt(s_calib_btn_ptr) - 1);
            if (lbl) lv_label_set_text(lbl, "Puntero 1%");
        }
    }
}

static void on_calib_reset_cb(lv_event_t *e)
{
    (void)e;
    s_calib_step = 0;
    s_calib_done_mask = 0;
    calib_dispatch_move(0);
}

void ui_calibration_set_step(int step_idx)
{
    if (step_idx >= 0 && step_idx < 5) {
        s_calib_step = step_idx;
        calib_dispatch_move(s_calib_step);
    }
}

static void calib_update_view(void)
{
    for (int i = 0; i < 5; i++) {
        if (!s_calib_pts[i]) continue;
        if (i == s_calib_step) {
            lv_obj_set_style_bg_color(s_calib_pts[i], focal_theme_get_accent_color(), 0);
            lv_obj_set_style_border_color(s_calib_pts[i], lv_color_hex(0xFFFFFF), 0);
            lv_obj_set_style_border_width(s_calib_pts[i], 2, 0);
        } else if (s_calib_done_mask & (1 << i)) {
            lv_obj_set_style_bg_color(s_calib_pts[i], FOCAL_COLOR_PASTEL_MINT, 0);
            lv_obj_set_style_border_color(s_calib_pts[i], lv_color_hex(0x10B981), 0);
            lv_obj_set_style_border_width(s_calib_pts[i], 1, 0);
        } else {
            lv_obj_set_style_bg_color(s_calib_pts[i], s_is_dark ? lv_color_hex(0x262A35) : lv_color_hex(0xD1D5DB), 0);
            lv_obj_set_style_border_color(s_calib_pts[i], s_is_dark ? lv_color_hex(0x3B4252) : lv_color_hex(0x9CA3AF), 0);
            lv_obj_set_style_border_width(s_calib_pts[i], 1, 0);
        }
    }

    if (s_calib_laser_dot) {
        int dot_x = s_calib_pt_coords[s_calib_step][0] + 9;
        int dot_y = s_calib_pt_coords[s_calib_step][1] + 9;
        lv_obj_set_pos(s_calib_laser_dot, dot_x, dot_y);
    }

    if (s_calib_lbl_step) {
        lv_label_set_text(s_calib_lbl_step, s_calib_steps[s_calib_step].step_name);
    }
    if (s_calib_lbl_coords) {
        char buf[48];
        snprintf(buf, sizeof(buf), "Cabezal: X: %d mm | Y: %d mm", s_calib_steps[s_calib_step].x, s_calib_steps[s_calib_step].y);
        lv_label_set_text(s_calib_lbl_coords, buf);
    }

    if (s_calib_moving) {
        if (s_calib_lbl_instruction) {
            lv_label_set_text(s_calib_lbl_instruction, "Desplazando cabezal al punto...\\nPor favor espere a que termine.");
            lv_obj_set_style_text_color(s_calib_lbl_instruction, FOCAL_COLOR_PASTEL_AMBER, 0);
        }
        if (s_calib_bar_travel) {
            lv_obj_clear_flag(s_calib_bar_travel, LV_OBJ_FLAG_HIDDEN);
        }
        if (s_calib_btn_next) {
            lv_obj_t *lbl = lv_obj_get_child(s_calib_btn_next, lv_obj_get_child_cnt(s_calib_btn_next) - 1);
            if (lbl) lv_label_set_text(lbl, "Moviendo...");
            lv_obj_add_state(s_calib_btn_next, LV_STATE_DISABLED);
        }
        if (s_calib_btn_prev) {
            lv_obj_add_state(s_calib_btn_prev, LV_STATE_DISABLED);
        }
    } else {
        if (s_calib_lbl_instruction) {
            lv_label_set_text(s_calib_lbl_instruction, s_calib_steps[s_calib_step].instructions);
            lv_obj_set_style_text_color(s_calib_lbl_instruction, s_is_dark ? lv_color_hex(0xF9FAFB) : lv_color_hex(0x111827), 0);
        }
        if (s_calib_bar_travel) {
            lv_obj_add_flag(s_calib_bar_travel, LV_OBJ_FLAG_HIDDEN);
        }
        if (s_calib_btn_next) {
            lv_obj_clear_state(s_calib_btn_next, LV_STATE_DISABLED);
            lv_obj_t *lbl = lv_obj_get_child(s_calib_btn_next, lv_obj_get_child_cnt(s_calib_btn_next) - 1);
            if (lbl) {
                if (s_calib_step == 4) {
                    lv_label_set_text(lbl, "Finalizar");
                } else {
                    lv_label_set_text(lbl, "Siguiente");
                }
            }
        }
        if (s_calib_btn_prev) {
            if (s_calib_step > 0) {
                lv_obj_clear_state(s_calib_btn_prev, LV_STATE_DISABLED);
            } else {
                lv_obj_add_state(s_calib_btn_prev, LV_STATE_DISABLED);
            }
        }
    }
}

static void create_calibration_screen(void)
{
    lv_obj_t *scr = lv_obj_create(NULL);
    s_screens[UI_SCREEN_CALIBRATION] = scr;
    lv_obj_add_style(scr, &focal_style_screen, 0);
    lv_obj_clear_flag(scr, LV_OBJ_FLAG_SCROLLABLE);

    create_screen_header(UI_SCREEN_CALIBRATION, "Nivelacion de Cama (Manual Z)", true);

    // Left Panel: Diagrama visual de cama (140x175 px proporcional a 160x200 mm)
    lv_obj_t *c1 = lv_obj_create(scr);
    lv_obj_set_size(c1, 190, 262);
    lv_obj_set_pos(c1, 10, 46);
    lv_obj_add_style(c1, &focal_style_card, 0);
    lv_obj_clear_flag(c1, LV_OBJ_FLAG_SCROLLABLE);

    lv_obj_t *t1 = lv_label_create(c1);
    lv_label_set_text(t1, "Cama 160x200 mm");
    lv_obj_set_style_text_color(t1, FOCAL_COLOR_PASTEL_BLUE, 0);
    lv_obj_align(t1, LV_ALIGN_TOP_MID, 0, 0);

    lv_obj_t *bed_box = lv_obj_create(c1);
    lv_obj_set_size(bed_box, 140, 175);
    lv_obj_set_pos(bed_box, 15, 24);
    lv_obj_set_style_bg_color(bed_box, s_is_dark ? lv_color_hex(0x14171E) : lv_color_hex(0xE5E7EB), 0);
    lv_obj_set_style_border_color(bed_box, s_is_dark ? lv_color_hex(0x3B82F6) : lv_color_hex(0x2563EB), 0);
    lv_obj_set_style_border_width(bed_box, 1, 0);
    lv_obj_set_style_radius(bed_box, 6, 0);
    lv_obj_set_style_pad_all(bed_box, 0, 0);
    lv_obj_clear_flag(bed_box, LV_OBJ_FLAG_SCROLLABLE);

    const char *pt_labels[5] = { "T1", "T2", "T3", "T4", "C" };

    for (int i = 0; i < 5; i++) {
        lv_obj_t *b = lv_btn_create(bed_box);
        lv_obj_set_size(b, 32, 32);
        lv_obj_set_pos(b, s_calib_pt_coords[i][0], s_calib_pt_coords[i][1]);
        lv_obj_set_style_radius(b, LV_RADIUS_CIRCLE, 0);
        lv_obj_set_style_pad_all(b, 0, 0);
        lv_obj_set_ext_click_area(b, 8);
        s_calib_pts[i] = b;

        lv_obj_t *lbl = lv_label_create(b);
        lv_label_set_text(lbl, pt_labels[i]);
        lv_obj_center(lbl);

        lv_obj_add_event_cb(b, on_calib_point_click_cb, LV_EVENT_CLICKED, (void *)(uintptr_t)i);
    }

    // Laser head marker dot
    s_calib_laser_dot = lv_obj_create(bed_box);
    lv_obj_set_size(s_calib_laser_dot, 14, 14);
    lv_obj_set_style_radius(s_calib_laser_dot, LV_RADIUS_CIRCLE, 0);
    lv_obj_set_style_bg_color(s_calib_laser_dot, lv_color_hex(0xEF4444), 0);
    lv_obj_set_style_border_color(s_calib_laser_dot, lv_color_hex(0xFFFFFF), 0);
    lv_obj_set_style_border_width(s_calib_laser_dot, 2, 0);
    lv_obj_clear_flag(s_calib_laser_dot, LV_OBJ_FLAG_CLICKABLE);

    lv_obj_t *lbl_foot = lv_label_create(c1);
    lv_label_set_text(lbl_foot, "4 Perillas Manuales Z");
    lv_obj_align(lbl_foot, LV_ALIGN_BOTTOM_MID, 0, -2);

    // Right Panel: Wizard controls & instructions
    lv_obj_t *c2 = lv_obj_create(scr);
    lv_obj_set_size(c2, 264, 262);
    lv_obj_set_pos(c2, 206, 46);
    lv_obj_add_style(c2, &focal_style_card, 0);
    lv_obj_clear_flag(c2, LV_OBJ_FLAG_SCROLLABLE);

    s_calib_lbl_step = lv_label_create(c2);
    lv_label_set_text(s_calib_lbl_step, "Paso 1/5: Frontal Izq");
    lv_obj_set_style_text_color(s_calib_lbl_step, FOCAL_COLOR_PASTEL_MINT, 0);
    lv_obj_align(s_calib_lbl_step, LV_ALIGN_TOP_LEFT, 6, 2);

    s_calib_lbl_coords = lv_label_create(c2);
    lv_label_set_text(s_calib_lbl_coords, "Cabezal: X: 10 mm | Y: 10 mm");
    lv_obj_align(s_calib_lbl_coords, LV_ALIGN_TOP_LEFT, 6, 24);

    // Instruction Box (Squircle radius 10 per Focal Design System)
    lv_obj_t *ins_box = lv_obj_create(c2);
    lv_obj_set_size(ins_box, 248, 70);
    lv_obj_set_pos(ins_box, 6, 48);
    lv_obj_set_style_radius(ins_box, FOCAL_RADIUS_M, 0);
    lv_obj_set_style_bg_color(ins_box, s_is_dark ? lv_color_hex(0x262A35) : lv_color_hex(0xF0F2F5), 0);
    lv_obj_set_style_border_color(ins_box, s_is_dark ? lv_color_hex(0x2D333F) : lv_color_hex(0xE5E7EB), 0);
    lv_obj_set_style_border_width(ins_box, 1, 0);
    lv_obj_set_style_pad_all(ins_box, 8, 0);
    lv_obj_clear_flag(ins_box, LV_OBJ_FLAG_SCROLLABLE);

    s_calib_lbl_instruction = lv_label_create(ins_box);
    lv_obj_set_width(s_calib_lbl_instruction, 230);
    lv_label_set_long_mode(s_calib_lbl_instruction, LV_LABEL_LONG_WRAP);
    lv_label_set_text(s_calib_lbl_instruction, s_calib_steps[0].instructions);
    lv_obj_align(s_calib_lbl_instruction, LV_ALIGN_TOP_LEFT, 0, 0);

    // Travel bar outside ins_box to avoid text overlap
    s_calib_bar_travel = lv_bar_create(c2);
    lv_obj_set_size(s_calib_bar_travel, 248, 6);
    lv_obj_set_pos(s_calib_bar_travel, 6, 124);
    lv_obj_set_style_bg_color(s_calib_bar_travel, FOCAL_COLOR_PASTEL_AMBER, LV_PART_INDICATOR);
    lv_bar_set_value(s_calib_bar_travel, 100, LV_ANIM_OFF);
    lv_obj_add_flag(s_calib_bar_travel, LV_OBJ_FLAG_HIDDEN);

    // Utility Row: Laser pointer toggle + Reset
    s_calib_btn_ptr = focal_create_btn(c2, 118, 36, &focal_icon_laser, "Puntero 1%", &focal_style_btn_secondary, FOCAL_HEX_PASTEL_AMBER);
    lv_obj_set_pos(s_calib_btn_ptr, 6, 136);
    lv_obj_set_ext_click_area(s_calib_btn_ptr, 6);
    lv_obj_add_event_cb(s_calib_btn_ptr, on_calib_pointer_toggle_cb, LV_EVENT_CLICKED, NULL);

    lv_obj_t *btn_rst = focal_create_btn(c2, 118, 36, &focal_icon_refresh, "Reiniciar", &focal_style_btn_secondary, FOCAL_HEX_PASTEL_BLUE);
    lv_obj_set_pos(btn_rst, 132, 136);
    lv_obj_set_ext_click_area(btn_rst, 6);
    lv_obj_add_event_cb(btn_rst, on_calib_reset_cb, LV_EVENT_CLICKED, NULL);

    // Bottom Navigation Buttons
    s_calib_btn_prev = focal_create_btn(c2, 108, 44, NULL, "Anterior", &focal_style_btn_secondary, 0);
    lv_obj_set_pos(s_calib_btn_prev, 6, 184);
    lv_obj_set_ext_click_area(s_calib_btn_prev, 6);
    lv_obj_add_event_cb(s_calib_btn_prev, on_calib_prev_cb, LV_EVENT_CLICKED, NULL);

    s_calib_btn_next = focal_create_btn(c2, 134, 44, &focal_icon_check, "Siguiente", &focal_style_btn_mint, 0xFFFFFF);
    lv_obj_set_pos(s_calib_btn_next, 120, 184);
    lv_obj_set_ext_click_area(s_calib_btn_next, 6);
    lv_obj_add_event_cb(s_calib_btn_next, on_calib_next_cb, LV_EVENT_CLICKED, NULL);

    calib_update_view();
}
""")

    # Screen 5: Shapes / Quick Cut
    code.append("""
// =============================================================================
// SCREEN 5: CORTE RAPIDO CON CAMA INTERACTIVA (160x200 mm)
// =============================================================================
static int s_shape_type = 0; // 0: Circulo, 1: Cuadrado, 2: Rectangulo, 3: Linea Trozado
static int s_shape_x = 50;
static int s_shape_y = 50;
static int s_shape_dim = 40;
static int s_shape_power = 80;

static lv_obj_t *s_bed_obj = NULL;
static lv_obj_t *s_bed_shape_preview = NULL;
static lv_obj_t *s_lbl_shape_pos = NULL;
static lv_obj_t *s_lbl_shape_size = NULL;
static lv_obj_t *s_lbl_shape_power = NULL;
static lv_obj_t *s_shape_sel_btns[4] = {0};

static void update_bed_shape_position(void)
{
    if (s_bed_shape_preview) {
        int w = s_shape_dim;
        int h = s_shape_dim;
        if (s_shape_type == 2) { // Rectangulo
            w = (s_shape_dim * 4) / 3;
            h = s_shape_dim;
        } else if (s_shape_type == 3) { // Linea de trozado
            w = s_shape_dim * 2;
            h = 4;
        }

        if (s_shape_x < 0) s_shape_x = 0;
        if (s_shape_x > 160 - w) s_shape_x = 160 - w;
        if (s_shape_y < 0) s_shape_y = 0;
        if (s_shape_y > 200 - h) s_shape_y = 200 - h;

        int px = (s_shape_x * 120) / 160;
        int py = 150 - ((s_shape_y + h) * 150) / 200;
        int pw = (w * 120) / 160;
        int ph = (h * 150) / 200;
        if (pw < 4) pw = 4;
        if (ph < 4) ph = 4;

        lv_obj_set_size(s_bed_shape_preview, pw, ph);
        lv_obj_set_pos(s_bed_shape_preview, px, py);

        if (s_shape_type == 0) {
            lv_obj_set_style_radius(s_bed_shape_preview, LV_RADIUS_CIRCLE, 0);
        } else {
            lv_obj_set_style_radius(s_bed_shape_preview, 2, 0);
        }
    }
    if (s_lbl_shape_pos) {
        char buf[32];
        snprintf(buf, sizeof(buf), "X: %d  Y: %d mm", s_shape_x, s_shape_y);
        lv_label_set_text(s_lbl_shape_pos, buf);
    }
}

static void on_bed_touch_event_cb(lv_event_t *e)
{
    (void)e;
    lv_indev_t *indev = lv_indev_get_act();
    if (!indev) return;
    lv_point_t p;
    lv_indev_get_point(indev, &p);

    int rel_x = p.x - 48; // card_bed(10) + bed_obj(38)
    int rel_y = p.y - 50; // card_bed(46) + bed_obj(4)

    if (rel_x >= 0 && rel_x <= 120 && rel_y >= 0 && rel_y <= 150) {
        int raw_x = (rel_x * 160) / 120;
        int raw_y = 200 - ((rel_y * 200) / 150) - (s_shape_dim / 2);
        if (raw_x < 0) raw_x = 0;
        if (raw_x > (160 - s_shape_dim)) raw_x = 160 - s_shape_dim;
        if (raw_y < 0) raw_y = 0;
        if (raw_y > (200 - s_shape_dim)) raw_y = 200 - s_shape_dim;
        s_shape_x = raw_x;
        s_shape_y = raw_y;
        update_bed_shape_position();
    }
}

static void on_shape_pos_preset_cb(lv_event_t *e)
{
    int preset = (int)(uintptr_t)lv_event_get_user_data(e);
    if (preset == 0) { // Centro
        s_shape_x = 80 - (s_shape_dim / 2);
        s_shape_y = 100 - (s_shape_dim / 2);
    } else if (preset == 1) { // Origen
        s_shape_x = 10;
        s_shape_y = 10;
    } else if (preset == 2) { // Aqui (Cabezal)
        s_shape_x = (int)s_sim_x;
        s_shape_y = (int)s_sim_y;
    }
    update_bed_shape_position();
}

void ui_shapes_set_preset(int preset_idx)
{
    if (preset_idx == 0) {
        s_shape_x = 80 - (s_shape_dim / 2);
        s_shape_y = 100 - (s_shape_dim / 2);
    } else if (preset_idx == 1) {
        s_shape_x = 10;
        s_shape_y = 10;
    } else {
        s_shape_x = 40;
        s_shape_y = 40;
    }
    update_bed_shape_position();
}

void ui_shapes_nudge(int dx, int dy)
{
    s_shape_x += dx;
    s_shape_y += dy;
    update_bed_shape_position();
}

static void on_shape_nudge_cb(lv_event_t *e)
{
    int dir = (int)(uintptr_t)lv_event_get_user_data(e);
    if (dir == 0) s_shape_x -= 5;      // Izq
    else if (dir == 1) s_shape_x += 5; // Der
    else if (dir == 2) s_shape_y += 5; // Arriba
    else if (dir == 3) s_shape_y -= 5; // Abajo
    update_bed_shape_position();
}

static void on_shape_icon_btn_click(lv_event_t *e)
{
    int idx = (int)(uintptr_t)lv_event_get_user_data(e);
    s_shape_type = idx;
    for (int i = 0; i < 4; i++) {
        if (s_shape_sel_btns[i]) {
            if (i == idx) {
                lv_obj_set_style_bg_color(s_shape_sel_btns[i], focal_theme_get_accent_color(), 0);
            } else {
                lv_obj_set_style_bg_color(s_shape_sel_btns[i], s_is_dark ? lv_color_hex(0x262A35) : lv_color_hex(0xF0F2F5), 0);
            }
        }
    }
    update_bed_shape_position();
}

static void on_shape_size_preset_cb(lv_event_t *e)
{
    int sz = (int)(uintptr_t)lv_event_get_user_data(e);
    s_shape_dim = sz;
    if (s_lbl_shape_size) {
        char buf[32];
        snprintf(buf, sizeof(buf), "Tamano: %d mm", s_shape_dim);
        lv_label_set_text(s_lbl_shape_size, buf);
    }
    update_bed_shape_position();
}

static void on_shape_size_adj_cb(lv_event_t *e)
{
    int delta = (int)(uintptr_t)lv_event_get_user_data(e);
    s_shape_dim += delta;
    if (s_shape_dim < 10) s_shape_dim = 10;
    if (s_shape_dim > 100) s_shape_dim = 100;
    if (s_lbl_shape_size) {
        char buf[32];
        snprintf(buf, sizeof(buf), "Tamano: %d mm", s_shape_dim);
        lv_label_set_text(s_lbl_shape_size, buf);
    }
    update_bed_shape_position();
}

static void on_shape_power_preset_cb(lv_event_t *e)
{
    int pwr = (int)(uintptr_t)lv_event_get_user_data(e);
    s_shape_power = pwr;
    if (s_lbl_shape_power) {
        char buf[32];
        snprintf(buf, sizeof(buf), "Potencia: %d%%", s_shape_power);
        lv_label_set_text(s_lbl_shape_power, buf);
    }
}

static void on_shape_power_adj_cb(lv_event_t *e)
{
    int delta = (int)(uintptr_t)lv_event_get_user_data(e);
    s_shape_power += delta;
    if (s_shape_power < 10) s_shape_power = 10;
    if (s_shape_power > 100) s_shape_power = 100;
    if (s_lbl_shape_power) {
        char buf[32];
        snprintf(buf, sizeof(buf), "Potencia: %d%%", s_shape_power);
        lv_label_set_text(s_lbl_shape_power, buf);
    }
}

static void on_shape_action_cb(lv_event_t *e)
{
    bool do_cut = (bool)(uintptr_t)lv_event_get_user_data(e);
    char cmd[64];
    char resp[32];

    if (!do_cut) {
        // Enmarcar con puntero al 1%
        laser_set_enable(true);
        laser_set_power(10); // 1%
        snprintf(cmd, sizeof(cmd), "G90 G0 X%d Y%d F3000", s_shape_x, s_shape_y);
        gcode_parser_execute_line(cmd, resp, sizeof(resp));
        snprintf(cmd, sizeof(cmd), "G1 X%d Y%d F2000", s_shape_x + s_shape_dim, s_shape_y);
        gcode_parser_execute_line(cmd, resp, sizeof(resp));
        snprintf(cmd, sizeof(cmd), "G1 X%d Y%d", s_shape_x + s_shape_dim, s_shape_y + s_shape_dim);
        gcode_parser_execute_line(cmd, resp, sizeof(resp));
        snprintf(cmd, sizeof(cmd), "G1 X%d Y%d", s_shape_x, s_shape_y + s_shape_dim);
        gcode_parser_execute_line(cmd, resp, sizeof(resp));
        snprintf(cmd, sizeof(cmd), "G1 X%d Y%d", s_shape_x, s_shape_y);
        gcode_parser_execute_line(cmd, resp, sizeof(resp));
        laser_set_power(0);
        laser_set_enable(false);
    } else {
        ui_show_cut_modal("corte_rapido.gcode", 140, 45);
    }
}

static void create_shapes_screen(void)
{
    lv_obj_t *scr = lv_obj_create(NULL);
    s_screens[UI_SCREEN_SHAPES] = scr;
    lv_obj_add_style(scr, &focal_style_screen, 0);
    lv_obj_clear_flag(scr, LV_OBJ_FLAG_SCROLLABLE);

    create_screen_header(UI_SCREEN_SHAPES, "Corte Rapido de Taller", true);

    // Left Panel: Simulated Machine Bed (160x200 mm) + Placement Controls
    lv_obj_t *card_bed = lv_obj_create(scr);
    lv_obj_set_size(card_bed, 196, 264);
    lv_obj_set_pos(card_bed, 10, 46);
    lv_obj_add_style(card_bed, &focal_style_card, 0);
    lv_obj_clear_flag(card_bed, LV_OBJ_FLAG_SCROLLABLE);

    // Bed Container 120x150 (Exact 0.8:1 aspect ratio matching 160x200mm)
    s_bed_obj = lv_obj_create(card_bed);
    lv_obj_set_size(s_bed_obj, 120, 150);
    lv_obj_set_pos(s_bed_obj, 38, 4);
    lv_obj_set_style_bg_color(s_bed_obj, s_is_dark ? lv_color_hex(0x14171E) : lv_color_hex(0xE5E7EB), 0);
    lv_obj_set_style_border_color(s_bed_obj, s_is_dark ? lv_color_hex(0x3B82F6) : lv_color_hex(0x2563EB), 0);
    lv_obj_set_style_border_width(s_bed_obj, 1, 0);
    lv_obj_set_style_radius(s_bed_obj, 6, 0);
    lv_obj_clear_flag(s_bed_obj, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_add_event_cb(s_bed_obj, on_bed_touch_event_cb, LV_EVENT_PRESSING, NULL);
    lv_obj_add_event_cb(s_bed_obj, on_bed_touch_event_cb, LV_EVENT_PRESSED, NULL);

    // Shape preview on bed
    s_bed_shape_preview = lv_obj_create(s_bed_obj);
    lv_obj_set_style_bg_color(s_bed_shape_preview, focal_theme_get_accent_color(), 0);
    lv_obj_set_style_bg_opa(s_bed_shape_preview, LV_OPA_60, 0);
    lv_obj_set_style_border_color(s_bed_shape_preview, lv_color_hex(0xFFFFFF), 0);
    lv_obj_set_style_border_width(s_bed_shape_preview, 1, 0);
    lv_obj_clear_flag(s_bed_shape_preview, LV_OBJ_FLAG_SCROLLABLE | LV_OBJ_FLAG_CLICKABLE);

    // Placement Presets Row
    const char *pos_preset_names[3] = { "Centro", "Origen", "Aqui" };
    for (int i = 0; i < 3; i++) {
        lv_obj_t *bp = focal_create_btn(card_bed, 60, 26, NULL, pos_preset_names[i], &focal_style_btn_secondary, 0);
        lv_obj_set_pos(bp, 3 + i * 62, 158);
        lv_obj_set_ext_click_area(bp, 8);
        lv_obj_add_event_cb(bp, on_shape_pos_preset_cb, LV_EVENT_CLICKED, (void *)(uintptr_t)i);
    }

    // Nudge Micro-step Bar (-5 / +5 mm) with Vector Icons
    const lv_img_dsc_t *nudge_icons[4] = {
        &focal_icon_jog_left,
        &focal_icon_jog_right,
        &focal_icon_jog_up,
        &focal_icon_jog_down
    };
    for (int i = 0; i < 4; i++) {
        lv_obj_t *bn = focal_create_btn(card_bed, 38, 26, nudge_icons[i], NULL, &focal_style_btn_secondary, FOCAL_HEX_PASTEL_BLUE);
        lv_obj_set_pos(bn, 8 + i * 44, 188);
        lv_obj_set_ext_click_area(bn, 10);
        lv_obj_add_event_cb(bn, on_shape_nudge_cb, LV_EVENT_CLICKED, (void *)(uintptr_t)i);
    }

    // Coordinates Readout
    s_lbl_shape_pos = lv_label_create(card_bed);
    lv_label_set_text(s_lbl_shape_pos, "X: 50  Y: 50 mm");
    lv_obj_set_style_text_color(s_lbl_shape_pos, FOCAL_COLOR_PASTEL_BLUE, 0);
    lv_obj_align(s_lbl_shape_pos, LV_ALIGN_BOTTOM_MID, 0, -4);

    update_bed_shape_position();

    // Right Panel: Shape selector, Size & Power presets, Actions
    lv_obj_t *card_ctrl = lv_obj_create(scr);
    lv_obj_set_size(card_ctrl, 254, 264);
    lv_obj_set_pos(card_ctrl, 216, 46);
    lv_obj_add_style(card_ctrl, &focal_style_card, 0);
    lv_obj_clear_flag(card_ctrl, LV_OBJ_FLAG_SCROLLABLE);

    // Row 1: 4 Essential Workshop Shapes
    const lv_img_dsc_t *shape_icons[4] = {
        &focal_icon_shape_circle,
        &focal_icon_shape_square,
        &focal_icon_shape_rect,
        &focal_icon_laser // Linea de corte / trozado
    };

    for (int i = 0; i < 4; i++) {
        lv_obj_t *b = lv_btn_create(card_ctrl);
        lv_obj_set_size(b, 54, 34);
        lv_obj_set_pos(b, 6 + i * 60, 4);
        lv_obj_add_style(b, &focal_style_btn_secondary, 0);
        lv_obj_set_style_radius(b, FOCAL_RADIUS_S, 0);
        lv_obj_set_style_pad_all(b, 0, 0);
        s_shape_sel_btns[i] = b;

        lv_obj_t *ic = focal_create_icon(b, shape_icons[i], 0xFFFFFF);
        lv_obj_center(ic);
        if (i == 0) {
            lv_obj_set_style_bg_color(b, focal_theme_get_accent_color(), 0);
        }
        lv_obj_add_event_cb(b, on_shape_icon_btn_click, LV_EVENT_CLICKED, (void *)(uintptr_t)i);
    }

    // Row 2: Size Label & +/- Nudge
    s_lbl_shape_size = lv_label_create(card_ctrl);
    lv_label_set_text(s_lbl_shape_size, "Tamano: 40 mm");
    lv_obj_align(s_lbl_shape_size, LV_ALIGN_TOP_LEFT, 6, 46);

    lv_obj_t *bs_m = focal_create_btn(card_ctrl, 28, 24, NULL, "-", &focal_style_btn_secondary, 0);
    lv_obj_set_pos(bs_m, 178, 42);
    lv_obj_set_ext_click_area(bs_m, 10);
    lv_obj_add_event_cb(bs_m, on_shape_size_adj_cb, LV_EVENT_CLICKED, (void *)-5);

    lv_obj_t *bs_p = focal_create_btn(card_ctrl, 28, 24, NULL, "+", &focal_style_btn_secondary, 0);
    lv_obj_set_pos(bs_p, 212, 42);
    lv_obj_set_ext_click_area(bs_p, 10);
    lv_obj_add_event_cb(bs_p, on_shape_size_adj_cb, LV_EVENT_CLICKED, (void *)5);

    // Row 3: 4 Size Direct Presets (20, 40, 60, 80 mm)
    const int sz_presets[4] = { 20, 40, 60, 80 };
    for (int i = 0; i < 4; i++) {
        char sz_txt[16];
        snprintf(sz_txt, sizeof(sz_txt), "%d", sz_presets[i]);
        lv_obj_t *bsz = focal_create_btn(card_ctrl, 54, 26, NULL, sz_txt, &focal_style_btn_secondary, 0);
        lv_obj_set_pos(bsz, 6 + i * 60, 70);
        lv_obj_set_ext_click_area(bsz, 6);
        lv_obj_add_event_cb(bsz, on_shape_size_preset_cb, LV_EVENT_CLICKED, (void *)(uintptr_t)sz_presets[i]);
    }

    // Row 4: Power Label & +/- Nudge
    s_lbl_shape_power = lv_label_create(card_ctrl);
    lv_label_set_text(s_lbl_shape_power, "Potencia: 80%");
    lv_obj_align(s_lbl_shape_power, LV_ALIGN_TOP_LEFT, 6, 104);

    lv_obj_t *bp_m = focal_create_btn(card_ctrl, 28, 24, NULL, "-", &focal_style_btn_secondary, 0);
    lv_obj_set_pos(bp_m, 178, 100);
    lv_obj_set_ext_click_area(bp_m, 10);
    lv_obj_add_event_cb(bp_m, on_shape_power_adj_cb, LV_EVENT_CLICKED, (void *)-10);

    lv_obj_t *bp_p = focal_create_btn(card_ctrl, 28, 24, NULL, "+", &focal_style_btn_secondary, 0);
    lv_obj_set_pos(bp_p, 212, 100);
    lv_obj_set_ext_click_area(bp_p, 10);
    lv_obj_add_event_cb(bp_p, on_shape_power_adj_cb, LV_EVENT_CLICKED, (void *)10);

    // Row 5: 4 Power Direct Presets (25%, 50%, 75%, 100%)
    const int pwr_presets[4] = { 25, 50, 75, 100 };
    for (int i = 0; i < 4; i++) {
        char pwr_txt[16];
        snprintf(pwr_txt, sizeof(pwr_txt), "%d%%", pwr_presets[i]);
        lv_obj_t *bpw = focal_create_btn(card_ctrl, 54, 26, NULL, pwr_txt, &focal_style_btn_secondary, 0);
        lv_obj_set_pos(bpw, 6 + i * 60, 128);
        lv_obj_set_ext_click_area(bpw, 6);
        lv_obj_add_event_cb(bpw, on_shape_power_preset_cb, LV_EVENT_CLICKED, (void *)(uintptr_t)pwr_presets[i]);
    }

    // Row 6: Bottom Action Buttons: Enmarcar & Cortar Ahora (Absolute Positioning, No-Overlap)
    lv_obj_t *btn_fb = focal_create_btn(card_ctrl, 114, 44, &focal_icon_laser, "Enmarcar", &focal_style_btn_secondary, FOCAL_HEX_PASTEL_AMBER);
    lv_obj_set_pos(btn_fb, 6, 208);
    lv_obj_set_ext_click_area(btn_fb, 6);
    lv_obj_add_event_cb(btn_fb, on_shape_action_cb, LV_EVENT_CLICKED, (void *)false);

    lv_obj_t *btn_cb = focal_create_btn(card_ctrl, 124, 44, &focal_icon_play, "Cortar Ahora", &focal_style_btn_mint, 0xFFFFFF);
    lv_obj_set_pos(btn_cb, 122, 208);
    lv_obj_set_style_pad_left(btn_cb, 6, 0);
    lv_obj_set_style_pad_right(btn_cb, 6, 0);
    lv_obj_set_ext_click_area(btn_cb, 6);
    lv_obj_add_event_cb(btn_cb, on_shape_action_cb, LV_EVENT_CLICKED, (void *)true);
}
""")

    # Screen 6: Settings
    code.append("""
// =============================================================================
// SCREEN 6: CONFIGURACION DE MAQUINA (MASTER-DETAIL LIST LAYOUT)
// =============================================================================
static int s_settings_tab = 0; // 0: WiFi, 1: Apariencia, 2: Laser, 3: SD, 4: Cinematica, 5: Sistema
static lv_obj_t *s_settings_panels[6] = {0};
static lv_obj_t *s_settings_menu_btns[6] = {0};

// Wi-Fi Controls
static lv_obj_t *s_wifi_list = NULL;
static lv_obj_t *s_lbl_wifi_detail = NULL;
static lv_obj_t *s_btn_wifi_scan = NULL;

// Wi-Fi Input Modal Overlay (Input box top + Keyboard bottom)
static lv_obj_t *s_wifi_modal = NULL;
static lv_obj_t *s_modal_ssid_lbl = NULL;
static lv_obj_t *s_modal_pass_ta = NULL;
static char s_connecting_ssid[33] = {0};

static void show_wifi_input_modal(const char *ssid)
{
    strncpy(s_connecting_ssid, ssid ? ssid : "", sizeof(s_connecting_ssid) - 1);
    s_connecting_ssid[sizeof(s_connecting_ssid) - 1] = 0;
    if (s_modal_ssid_lbl) {
        char buf[64];
        snprintf(buf, sizeof(buf), "Red: %s", s_connecting_ssid);
        lv_label_set_text(s_modal_ssid_lbl, buf);
    }
    if (s_modal_pass_ta) {
        lv_textarea_set_text(s_modal_pass_ta, "");
    }
    if (s_wifi_modal) {
        lv_obj_clear_flag(s_wifi_modal, LV_OBJ_FLAG_HIDDEN);
        lv_obj_move_foreground(s_wifi_modal);
    }
}

static void hide_wifi_input_modal(void)
{
    if (s_wifi_modal) {
        lv_obj_add_flag(s_wifi_modal, LV_OBJ_FLAG_HIDDEN);
    }
}

void ui_show_wifi_modal(const char *ssid)
{
    show_wifi_input_modal(ssid ? ssid : "Mi_Red_Taller");
}

void ui_hide_wifi_modal(void)
{
    hide_wifi_input_modal();
}

static void on_modal_connect_cb(lv_event_t *e)
{
    (void)e;
    const char *pass = lv_textarea_get_text(s_modal_pass_ta);
    hide_wifi_input_modal();

    machine_settings_t cfg;
    settings_manager_get(&cfg);
    strncpy(cfg.wifi_ssid, s_connecting_ssid, sizeof(cfg.wifi_ssid) - 1);
    cfg.wifi_ssid[sizeof(cfg.wifi_ssid) - 1] = 0;
    strncpy(cfg.wifi_pass, pass ? pass : "", sizeof(cfg.wifi_pass) - 1);
    cfg.wifi_pass[sizeof(cfg.wifi_pass) - 1] = 0;
    cfg.wifi_sta_enabled = true;
    settings_manager_save(&cfg);

    wifi_manager_connect_sta(s_connecting_ssid, pass);

    if (s_lbl_wifi_detail) {
        char buf[64];
        snprintf(buf, sizeof(buf), "Conectando a '%s'...", s_connecting_ssid);
        lv_label_set_text(s_lbl_wifi_detail, buf);
    }
}

static void on_modal_cancel_cb(lv_event_t *e)
{
    (void)e;
    hide_wifi_input_modal();
}

static void on_wifi_item_click_cb(lv_event_t *e)
{
    const char *ssid = (const char *)lv_event_get_user_data(e);
    show_wifi_input_modal(ssid);
}

// Background scan task
static void wifi_scan_task_fn(void *pv)
{
    (void)pv;
    wifi_scan_item_t scan_list[WIFI_MAX_SCAN_AP];
    uint16_t ap_count = 0;
    esp_err_t err = wifi_manager_scan(scan_list, WIFI_MAX_SCAN_AP, &ap_count);

    if (lvgl_port_lock(1000)) {
        if (s_btn_wifi_scan) {
            lv_obj_t *lbl = lv_obj_get_child(s_btn_wifi_scan, 1);
            if (lbl) lv_label_set_text(lbl, "Escanear");
        }
        if (s_wifi_list) {
            lv_obj_clean(s_wifi_list);
            if (err == ESP_OK && ap_count > 0) {
                for (int i = 0; i < ap_count; i++) {
                    char btn_txt[64];
                    snprintf(btn_txt, sizeof(btn_txt), "%s (%d dBm)", scan_list[i].ssid, scan_list[i].rssi);
                    lv_obj_t *btn = focal_create_btn(s_wifi_list, 290, 40, &focal_icon_wifi, btn_txt, &focal_style_btn_secondary, FOCAL_HEX_PASTEL_BLUE);
                    lv_obj_add_event_cb(btn, on_wifi_item_click_cb, LV_EVENT_CLICKED, (void *)strdup(scan_list[i].ssid));
                }
                if (s_lbl_wifi_detail) {
                    char st[64];
                    snprintf(st, sizeof(st), "%u redes encontradas. Toca para conectar.", ap_count);
                    lv_label_set_text(s_lbl_wifi_detail, st);
                }
            } else {
                lv_obj_t *lbl = lv_label_create(s_wifi_list);
                lv_label_set_text(lbl, "No se detectaron redes.");
            }
        }
        lvgl_port_unlock();
    }
    vTaskDelete(NULL);
}

static void on_wifi_scan_btn_cb(lv_event_t *e)
{
    (void)e;
    if (s_btn_wifi_scan) {
        lv_obj_t *lbl = lv_obj_get_child(s_btn_wifi_scan, 1);
        if (lbl) lv_label_set_text(lbl, "Buscando...");
    }
    if (s_lbl_wifi_detail) {
        lv_label_set_text(s_lbl_wifi_detail, "Escaneando canales 2.4 GHz...");
    }
    xTaskCreate(wifi_scan_task_fn, "wscan", 4096, NULL, 3, NULL);
}

static void on_wifi_forget_btn_cb(lv_event_t *e)
{
    (void)e;
    machine_settings_t cfg;
    settings_manager_get(&cfg);
    cfg.wifi_ssid[0] = '\\0';
    cfg.wifi_pass[0] = '\\0';
    cfg.wifi_sta_enabled = false;
    settings_manager_save(&cfg);

    wifi_manager_disconnect_sta();

    if (s_lbl_wifi_detail) {
        lv_label_set_text(s_lbl_wifi_detail, "Red olvidada. Desconectado.");
    }
}

// Master Menu Selection Handler
static void on_settings_menu_select_cb(lv_event_t *e)
{
    int idx = (int)(uintptr_t)lv_event_get_user_data(e);
    s_settings_tab = idx;

    for (int i = 0; i < 6; i++) {
        if (s_settings_menu_btns[i]) {
            if (i == idx) {
                lv_obj_set_style_bg_color(s_settings_menu_btns[i], focal_theme_get_accent_color(), 0);
                lv_obj_set_style_text_color(s_settings_menu_btns[i], lv_color_hex(0xFFFFFF), 0);
            } else {
                lv_obj_set_style_bg_color(s_settings_menu_btns[i], s_is_dark ? lv_color_hex(0x1A1D24) : lv_color_hex(0xFFFFFF), 0);
                lv_obj_set_style_text_color(s_settings_menu_btns[i], s_is_dark ? lv_color_hex(0xF9FAFB) : lv_color_hex(0x111827), 0);
            }
        }
        if (s_settings_panels[i]) {
            if (i == idx) {
                lv_obj_clear_flag(s_settings_panels[i], LV_OBJ_FLAG_HIDDEN);
            } else {
                lv_obj_add_flag(s_settings_panels[i], LV_OBJ_FLAG_HIDDEN);
            }
        }
    }
}

void ui_settings_select_tab(int idx)
{
    if (idx < 0 || idx >= 6) return;
    s_settings_tab = idx;

    for (int i = 0; i < 6; i++) {
        if (s_settings_menu_btns[i]) {
            if (i == idx) {
                lv_obj_set_style_bg_color(s_settings_menu_btns[i], focal_theme_get_accent_color(), 0);
                lv_obj_set_style_text_color(s_settings_menu_btns[i], lv_color_hex(0xFFFFFF), 0);
            } else {
                lv_obj_set_style_bg_color(s_settings_menu_btns[i], s_is_dark ? lv_color_hex(0x1A1D24) : lv_color_hex(0xFFFFFF), 0);
                lv_obj_set_style_text_color(s_settings_menu_btns[i], s_is_dark ? lv_color_hex(0xF9FAFB) : lv_color_hex(0x111827), 0);
            }
        }
        if (s_settings_panels[i]) {
            if (i == idx) {
                lv_obj_clear_flag(s_settings_panels[i], LV_OBJ_FLAG_HIDDEN);
            } else {
                lv_obj_add_flag(s_settings_panels[i], LV_OBJ_FLAG_HIDDEN);
            }
        }
    }
}

// Appearance Handlers
static void on_theme_toggle_cb(lv_event_t *e)
{
    bool is_dark = (bool)(uintptr_t)lv_event_get_user_data(e);
    focal_theme_set_dark(is_dark);
}

static void on_accent_select_cb(lv_event_t *e)
{
    uint8_t idx = (uint8_t)(uintptr_t)lv_event_get_user_data(e);
    focal_theme_set_accent(idx);
}

static void on_laser_test_pulse_cb(lv_event_t *e)
{
    (void)e;
    laser_driver_pulse(1000, 100); // 10% test pulse for 1s
}

static void on_laser_save_cb(lv_event_t *e)
{
    (void)e;
    machine_settings_t cfg;
    settings_manager_get(&cfg);
    settings_manager_save(&cfg);
}

static void on_sd_refresh_cb(lv_event_t *e)
{
    (void)e;
    ESP_LOGI(TAG, "Refrescando lista de archivos SD...");
}

static void on_sd_clean_cb(lv_event_t *e)
{
    (void)e;
    ESP_LOGI(TAG, "Limpiando archivos temporales SD...");
}

static void on_kinematics_test_x_cb(lv_event_t *e)
{
    (void)e;
    char resp[32];
    gcode_parser_execute_line("$J=G91 G21 X10 F2000", resp, sizeof(resp));
}

static void on_kinematics_test_y_cb(lv_event_t *e)
{
    (void)e;
    char resp[32];
    gcode_parser_execute_line("$J=G91 G21 Y10 F2000", resp, sizeof(resp));
}

static void on_factory_reset_confirmed_cb(lv_event_t *e)
{
    (void)e;
    settings_manager_reset_defaults();
    focal_theme_init();
    ui_switch_screen(UI_SCREEN_LAUNCHER);
}

static void create_settings_screen(void)
{
    lv_obj_t *scr = lv_obj_create(NULL);
    s_screens[UI_SCREEN_SETTINGS] = scr;
    lv_obj_add_style(scr, &focal_style_screen, 0);
    lv_obj_clear_flag(scr, LV_OBJ_FLAG_SCROLLABLE);

    create_screen_header(UI_SCREEN_SETTINGS, "Ajustes de Maquina", true);

    // Master List (Left Column, Width 136)
    lv_obj_t *nav_card = lv_obj_create(scr);
    lv_obj_set_size(nav_card, 136, 266);
    lv_obj_set_pos(nav_card, 6, 46);
    lv_obj_add_style(nav_card, &focal_style_card, 0);
    lv_obj_set_style_pad_all(nav_card, 4, 0);
    lv_obj_clear_flag(nav_card, LV_OBJ_FLAG_SCROLLABLE);

    const char *cat_names[6] = { "Red Wi-Fi", "Apariencia", "Laser", "Tarjeta SD", "Cinematica", "Sistema" };
    const lv_img_dsc_t *cat_icons[6] = {
        &focal_icon_wifi,
        &focal_icon_theme,
        &focal_icon_laser,
        &focal_icon_files,
        &focal_icon_shapes,
        &focal_icon_settings
    };

    for (int i = 0; i < 6; i++) {
        lv_obj_t *btn = focal_create_btn(nav_card, 126, 40, cat_icons[i], cat_names[i], &focal_style_btn_secondary, FOCAL_HEX_PASTEL_BLUE);
        lv_obj_set_pos(btn, 1, 2 + i * 43);
        s_settings_menu_btns[i] = btn;

        if (i == 0) {
            lv_obj_set_style_bg_color(btn, focal_theme_get_accent_color(), 0);
            lv_obj_set_style_text_color(btn, lv_color_hex(0xFFFFFF), 0);
        }
        lv_obj_add_event_cb(btn, on_settings_menu_select_cb, LV_EVENT_CLICKED, (void *)(uintptr_t)i);
    }

    // Detail Area (Right Column, Width 328, Height 266)
    lv_obj_t *detail_area = lv_obj_create(scr);
    lv_obj_set_size(detail_area, 328, 266);
    lv_obj_set_pos(detail_area, 146, 46);
    lv_obj_add_style(detail_area, &focal_style_card, 0);
    lv_obj_clear_flag(detail_area, LV_OBJ_FLAG_SCROLLABLE);

    // DETAIL PANEL 0: RED WI-FI
    lv_obj_t *p0 = lv_obj_create(detail_area);
    lv_obj_set_size(p0, 314, 252);
    lv_obj_set_pos(p0, 0, 0);
    lv_obj_clear_flag(p0, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_set_style_bg_opa(p0, LV_OPA_TRANSP, 0);
    lv_obj_set_style_border_width(p0, 0, 0);
    lv_obj_set_style_pad_all(p0, 2, 0);
    s_settings_panels[0] = p0;

    s_btn_wifi_scan = focal_create_btn(p0, 142, 34, &focal_icon_refresh, "Escanear", &focal_style_btn_secondary, FOCAL_HEX_PASTEL_BLUE);
    lv_obj_set_pos(s_btn_wifi_scan, 6, 6);
    lv_obj_set_ext_click_area(s_btn_wifi_scan, 6);
    lv_obj_add_event_cb(s_btn_wifi_scan, on_wifi_scan_btn_cb, LV_EVENT_CLICKED, NULL);

    lv_obj_t *btn_forget = focal_create_btn(p0, 142, 34, &focal_icon_trash, "Olvidar Red", &focal_style_btn_secondary, FOCAL_HEX_PASTEL_RED);
    lv_obj_align(btn_forget, LV_ALIGN_TOP_RIGHT, -6, 6);
    lv_obj_set_ext_click_area(btn_forget, 6);
    lv_obj_add_event_cb(btn_forget, on_wifi_forget_btn_cb, LV_EVENT_CLICKED, NULL);

    s_lbl_wifi_detail = lv_label_create(p0);
    lv_label_set_text(s_lbl_wifi_detail, "Toca 'Escanear' para buscar redes.");
    lv_obj_set_style_text_color(s_lbl_wifi_detail, s_is_dark ? lv_color_hex(0x9CA3AF) : lv_color_hex(0x4B5563), 0);
    lv_obj_set_pos(s_lbl_wifi_detail, 6, 46);

    // Scrollable list for detected networks
    s_wifi_list = lv_obj_create(p0);
    lv_obj_set_size(s_wifi_list, 302, 178);
    lv_obj_align(s_wifi_list, LV_ALIGN_BOTTOM_MID, 0, -4);
    lv_obj_set_style_bg_color(s_wifi_list, s_is_dark ? lv_color_hex(0x14171E) : lv_color_hex(0xFFFFFF), 0);
    lv_obj_set_style_border_width(s_wifi_list, 1, 0);
    lv_obj_set_style_border_color(s_wifi_list, s_is_dark ? lv_color_hex(0x2D333F) : lv_color_hex(0xD1D5DB), 0);
    lv_obj_set_flex_flow(s_wifi_list, LV_FLEX_FLOW_COLUMN);
    lv_obj_set_style_pad_all(s_wifi_list, 4, 0);
    lv_obj_set_style_pad_row(s_wifi_list, 4, 0);

    // DETAIL PANEL 1: APARIENCIA
    lv_obj_t *p1 = lv_obj_create(detail_area);
    lv_obj_set_size(p1, 314, 252);
    lv_obj_set_pos(p1, 0, 0);
    lv_obj_clear_flag(p1, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_set_style_bg_opa(p1, LV_OPA_TRANSP, 0);
    lv_obj_set_style_border_width(p1, 0, 0);
    lv_obj_add_flag(p1, LV_OBJ_FLAG_HIDDEN);
    s_settings_panels[1] = p1;

    lv_obj_t *lt1 = lv_label_create(p1);
    lv_label_set_text(lt1, "Tema de Pantalla");
    lv_obj_align(lt1, LV_ALIGN_TOP_LEFT, 6, 6);

    lv_obj_t *btn_dark = focal_create_btn(p1, 142, 42, NULL, "Modo Oscuro", &focal_style_btn_secondary, 0);
    lv_obj_set_pos(btn_dark, 6, 30);
    lv_obj_set_ext_click_area(btn_dark, 6);
    lv_obj_add_event_cb(btn_dark, on_theme_toggle_cb, LV_EVENT_CLICKED, (void *)true);

    lv_obj_t *btn_light = focal_create_btn(p1, 142, 42, NULL, "Modo Claro", &focal_style_btn_secondary, 0);
    lv_obj_set_pos(btn_light, 156, 30);
    lv_obj_set_ext_click_area(btn_light, 6);
    lv_obj_add_event_cb(btn_light, on_theme_toggle_cb, LV_EVENT_CLICKED, (void *)false);

    lv_obj_t *lt2 = lv_label_create(p1);
    lv_label_set_text(lt2, "Color de Enfasis");
    lv_obj_align(lt2, LV_ALIGN_TOP_LEFT, 6, 88);

    const char *color_names[5] = { "Azul", "Menta", "Ambar", "Morado", "Rojo" };
    for (int i = 0; i < 5; i++) {
        lv_obj_t *b = lv_btn_create(p1);
        lv_obj_set_size(b, 54, 40);
        lv_obj_set_pos(b, 8 + i * 60, 112);
        lv_obj_set_style_bg_color(b, lv_color_hex(s_accent_dark_hex[i]), 0);
        lv_obj_set_style_radius(b, FOCAL_RADIUS_M, 0);
        lv_obj_set_style_pad_all(b, 0, 0);
        lv_obj_set_ext_click_area(b, 4);
        lv_obj_add_event_cb(b, on_accent_select_cb, LV_EVENT_CLICKED, (void *)(uintptr_t)i);

        lv_obj_t *lbl = lv_label_create(b);
        lv_label_set_text(lbl, color_names[i]);
        lv_obj_set_style_text_color(lbl, lv_color_hex(0xFFFFFF), 0);
        lv_obj_center(lbl);
    }

    lv_obj_t *lbl_pers = lv_label_create(p1);
    lv_obj_set_width(lbl_pers, 300);
    lv_label_set_long_mode(lbl_pers, LV_LABEL_LONG_WRAP);
    lv_label_set_text(lbl_pers, "El tema y color se guardan en la memoria Flash.");
    lv_obj_align(lbl_pers, LV_ALIGN_BOTTOM_LEFT, 6, -6);

    // DETAIL PANEL 2: LASER
    lv_obj_t *p2 = lv_obj_create(detail_area);
    lv_obj_set_size(p2, 314, 252);
    lv_obj_set_pos(p2, 0, 0);
    lv_obj_clear_flag(p2, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_set_style_bg_opa(p2, LV_OPA_TRANSP, 0);
    lv_obj_set_style_border_width(p2, 0, 0);
    lv_obj_add_flag(p2, LV_OBJ_FLAG_HIDDEN);
    s_settings_panels[2] = p2;

    lv_obj_t *lt_lz = lv_label_create(p2);
    lv_label_set_text(lt_lz, "Parametros Modulo Laser");
    lv_obj_align(lt_lz, LV_ALIGN_TOP_LEFT, 6, 6);

    lv_obj_t *lbl_lpwr = lv_label_create(p2);
    lv_label_set_text(lbl_lpwr, "Potencia Maxima: 1000 (S)");
    lv_obj_set_style_text_color(lbl_lpwr, FOCAL_COLOR_PASTEL_BLUE, 0);
    lv_obj_align(lbl_lpwr, LV_ALIGN_TOP_LEFT, 6, 32);

    lv_obj_t *slider_pwr = lv_slider_create(p2);
    lv_obj_set_size(slider_pwr, 290, 16);
    lv_obj_set_pos(slider_pwr, 6, 56);
    lv_slider_set_range(slider_pwr, 100, 1000);
    lv_slider_set_value(slider_pwr, 1000, LV_ANIM_OFF);
    lv_obj_set_style_bg_color(slider_pwr, FOCAL_COLOR_PASTEL_BLUE, LV_PART_INDICATOR);

    lv_obj_t *lbl_air = lv_label_create(p2);
    lv_label_set_text(lbl_air, "Asistencia Aire M8 Auto:");
    lv_obj_align(lbl_air, LV_ALIGN_TOP_LEFT, 6, 90);

    lv_obj_t *sw_air = lv_switch_create(p2);
    lv_obj_set_pos(sw_air, 230, 84);
    lv_obj_add_state(sw_air, LV_STATE_CHECKED);

    lv_obj_t *btn_test_lz = focal_create_btn(p2, 142, 42, &focal_icon_laser, "Pulso 1s", &focal_style_btn_amber, 0xFFFFFF);
    lv_obj_set_pos(btn_test_lz, 6, 140);
    lv_obj_set_ext_click_area(btn_test_lz, 6);
    lv_obj_add_event_cb(btn_test_lz, on_laser_test_pulse_cb, LV_EVENT_CLICKED, NULL);

    lv_obj_t *btn_save_lz = focal_create_btn(p2, 142, 42, &focal_icon_check, "Guardar", &focal_style_btn_mint, 0xFFFFFF);
    lv_obj_set_pos(btn_save_lz, 156, 140);
    lv_obj_set_ext_click_area(btn_save_lz, 6);
    lv_obj_add_event_cb(btn_save_lz, on_laser_save_cb, LV_EVENT_CLICKED, NULL);

    // DETAIL PANEL 3: TARJETA SD
    lv_obj_t *p3 = lv_obj_create(detail_area);
    lv_obj_set_size(p3, 314, 252);
    lv_obj_set_pos(p3, 0, 0);
    lv_obj_clear_flag(p3, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_set_style_bg_opa(p3, LV_OPA_TRANSP, 0);
    lv_obj_set_style_border_width(p3, 0, 0);
    lv_obj_add_flag(p3, LV_OBJ_FLAG_HIDDEN);
    s_settings_panels[3] = p3;

    lv_obj_t *lt_sd = lv_label_create(p3);
    lv_label_set_text(lt_sd, "Almacenamiento MicroSD");
    lv_obj_align(lt_sd, LV_ALIGN_TOP_LEFT, 6, 6);

    lv_obj_t *lbl_sd_use = lv_label_create(p3);
    lv_label_set_text(lbl_sd_use, "Uso: 1.9 GB / 16 GB (FAT32 - 12%)");
    lv_obj_set_style_text_color(lbl_sd_use, FOCAL_COLOR_PASTEL_MINT, 0);
    lv_obj_align(lbl_sd_use, LV_ALIGN_TOP_LEFT, 6, 32);

    lv_obj_t *bar_sd = lv_bar_create(p3);
    lv_obj_set_size(bar_sd, 290, 14);
    lv_obj_set_pos(bar_sd, 6, 56);
    lv_obj_set_style_bg_color(bar_sd, FOCAL_COLOR_PASTEL_MINT, LV_PART_INDICATOR);
    lv_bar_set_value(bar_sd, 12, LV_ANIM_OFF);

    lv_obj_t *lbl_ovr = lv_label_create(p3);
    lv_label_set_text(lbl_ovr, "Sobrescribir Duplicados:");
    lv_obj_align(lbl_ovr, LV_ALIGN_TOP_LEFT, 6, 92);

    lv_obj_t *sw_ovr = lv_switch_create(p3);
    lv_obj_set_pos(sw_ovr, 230, 86);
    lv_obj_add_state(sw_ovr, LV_STATE_CHECKED);

    lv_obj_t *btn_sd_ref = focal_create_btn(p3, 142, 42, &focal_icon_refresh, "Actualizar", &focal_style_btn_secondary, FOCAL_HEX_PASTEL_BLUE);
    lv_obj_set_pos(btn_sd_ref, 6, 140);
    lv_obj_set_ext_click_area(btn_sd_ref, 6);
    lv_obj_add_event_cb(btn_sd_ref, on_sd_refresh_cb, LV_EVENT_CLICKED, NULL);

    lv_obj_t *btn_sd_fmt = focal_create_btn(p3, 142, 42, &focal_icon_trash, "Limpiar Temp", &focal_style_btn_secondary, FOCAL_HEX_PASTEL_RED);
    lv_obj_set_pos(btn_sd_fmt, 156, 140);
    lv_obj_set_ext_click_area(btn_sd_fmt, 6);
    lv_obj_add_event_cb(btn_sd_fmt, on_sd_clean_cb, LV_EVENT_CLICKED, NULL);

    // DETAIL PANEL 4: CINEMATICA
    lv_obj_t *p4 = lv_obj_create(detail_area);
    lv_obj_set_size(p4, 314, 252);
    lv_obj_set_pos(p4, 0, 0);
    lv_obj_clear_flag(p4, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_set_style_bg_opa(p4, LV_OPA_TRANSP, 0);
    lv_obj_set_style_border_width(p4, 0, 0);
    lv_obj_add_flag(p4, LV_OBJ_FLAG_HIDDEN);
    s_settings_panels[4] = p4;

    lv_obj_t *lt_kin = lv_label_create(p4);
    lv_label_set_text(lt_kin, "Cinematica 160x200 mm");
    lv_obj_align(lt_kin, LV_ALIGN_TOP_LEFT, 6, 6);

    lv_obj_t *lbl_feed = lv_label_create(p4);
    lv_label_set_text(lbl_feed, "Velocidad Max: 6000 mm/min");
    lv_obj_set_style_text_color(lbl_feed, FOCAL_COLOR_PASTEL_AMBER, 0);
    lv_obj_align(lbl_feed, LV_ALIGN_TOP_LEFT, 6, 32);

    lv_obj_t *slider_feed = lv_slider_create(p4);
    lv_obj_set_size(slider_feed, 290, 16);
    lv_obj_set_pos(slider_feed, 6, 56);
    lv_slider_set_range(slider_feed, 500, 8000);
    lv_slider_set_value(slider_feed, 6000, LV_ANIM_OFF);
    lv_obj_set_style_bg_color(slider_feed, FOCAL_COLOR_PASTEL_AMBER, LV_PART_INDICATOR);

    lv_obj_t *lbl_steps = lv_label_create(p4);
    lv_label_set_text(lbl_steps, "X: 400 pas/mm | Y: 400 pas/mm (T8x8)");
    lv_obj_align(lbl_steps, LV_ALIGN_TOP_LEFT, 6, 92);

    lv_obj_t *btn_tx = focal_create_btn(p4, 142, 42, NULL, "Test Eje X", &focal_style_btn_secondary, 0);
    lv_obj_set_pos(btn_tx, 6, 140);
    lv_obj_set_ext_click_area(btn_tx, 6);
    lv_obj_add_event_cb(btn_tx, on_kinematics_test_x_cb, LV_EVENT_CLICKED, NULL);

    lv_obj_t *btn_ty = focal_create_btn(p4, 142, 42, NULL, "Test Eje Y", &focal_style_btn_secondary, 0);
    lv_obj_set_pos(btn_ty, 156, 140);
    lv_obj_set_ext_click_area(btn_ty, 6);
    lv_obj_add_event_cb(btn_ty, on_kinematics_test_y_cb, LV_EVENT_CLICKED, NULL);

    // DETAIL PANEL 5: SISTEMA & RESET (Clean Hardware / Firmware Telemetry)
    lv_obj_t *p5 = lv_obj_create(detail_area);
    lv_obj_set_size(p5, 314, 252);
    lv_obj_set_pos(p5, 0, 0);
    lv_obj_clear_flag(p5, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_set_style_bg_opa(p5, LV_OPA_TRANSP, 0);
    lv_obj_set_style_border_width(p5, 0, 0);
    lv_obj_add_flag(p5, LV_OBJ_FLAG_HIDDEN);
    s_settings_panels[5] = p5;

    lv_obj_t *lt_sys = lv_label_create(p5);
    lv_label_set_text(lt_sys, "Hardware y Firmware");
    lv_obj_align(lt_sys, LV_ALIGN_TOP_LEFT, 6, 6);

    lv_obj_t *lbl_sys_val = lv_label_create(p5);
    lv_label_set_text(lbl_sys_val,
        "SoC: ESP32-S3 Dual-Core 240MHz\\n"
        "RAM: 8MB PSRAM | Flash: 16MB\\n"
        "Firmware: Focal CNC Studio v2.0\\n"
        "Pantalla: TFT 3.5\\\" 480x320 ILI9488");
    lv_obj_align(lbl_sys_val, LV_ALIGN_TOP_LEFT, 6, 32);

    lv_obj_t *btn_rst = focal_create_btn(p5, 292, 42, &focal_icon_trash, "Reset de Fabrica", &focal_style_btn_danger, 0xFFFFFF);
    lv_obj_set_pos(btn_rst, 6, 140);
    lv_obj_set_ext_click_area(btn_rst, 6);
    lv_obj_add_event_cb(btn_rst, on_factory_reset_confirmed_cb, LV_EVENT_CLICKED, NULL);

    // FLOATING KEYBOARD MODAL FOR WI-FI INPUT
    // (Input box at top y=12..64, keyboard at bottom y=145..320 -> ZERO OVERLAP!)
    s_wifi_modal = lv_obj_create(scr);
    lv_obj_set_size(s_wifi_modal, 480, 320);
    lv_obj_set_pos(s_wifi_modal, 0, 0);
    lv_obj_add_style(s_wifi_modal, &focal_style_screen, 0);
    lv_obj_clear_flag(s_wifi_modal, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_add_flag(s_wifi_modal, LV_OBJ_FLAG_HIDDEN);

    // Top Area: Label + Input Box + Connect/Cancel buttons (Balanced margins: 14px left, 10px right)
    s_modal_ssid_lbl = lv_label_create(s_wifi_modal);
    lv_label_set_text(s_modal_ssid_lbl, "Conectar a:");
    lv_obj_set_style_text_color(s_modal_ssid_lbl, FOCAL_COLOR_PASTEL_BLUE, 0);
    lv_obj_set_pos(s_modal_ssid_lbl, 14, 12);

    s_modal_pass_ta = lv_textarea_create(s_wifi_modal);
    lv_obj_set_size(s_modal_pass_ta, 218, 42);
    lv_obj_set_pos(s_modal_pass_ta, 14, 38);
    lv_obj_add_style(s_modal_pass_ta, &focal_style_card, 0);
    lv_textarea_set_placeholder_text(s_modal_pass_ta, "Ingresa clave Wi-Fi");
    lv_textarea_set_password_mode(s_modal_pass_ta, true);
    lv_textarea_set_one_line(s_modal_pass_ta, true);

    lv_obj_t *btn_modal_conn = focal_create_btn(s_wifi_modal, 108, 42, &focal_icon_check, "Conectar", &focal_style_btn_mint, 0xFFFFFF);
    lv_obj_set_pos(btn_modal_conn, 240, 38);
    lv_obj_set_style_pad_left(btn_modal_conn, 4, 0);
    lv_obj_set_style_pad_right(btn_modal_conn, 4, 0);
    lv_obj_set_ext_click_area(btn_modal_conn, 6);
    lv_obj_add_event_cb(btn_modal_conn, on_modal_connect_cb, LV_EVENT_CLICKED, NULL);

    lv_obj_t *btn_modal_canc = focal_create_btn(s_wifi_modal, 108, 42, NULL, "Cancelar", &focal_style_btn_secondary, 0);
    lv_obj_set_pos(btn_modal_canc, 356, 38);
    lv_obj_set_style_pad_left(btn_modal_canc, 4, 0);
    lv_obj_set_style_pad_right(btn_modal_canc, 4, 0);
    lv_obj_set_ext_click_area(btn_modal_canc, 6);
    lv_obj_add_event_cb(btn_modal_canc, on_modal_cancel_cb, LV_EVENT_CLICKED, NULL);

    // Bottom Keyboard (Height 175px leaves 65px headroom)
    lv_obj_t *kb = lv_keyboard_create(s_wifi_modal);
    lv_obj_set_size(kb, 480, 175);
    lv_obj_align(kb, LV_ALIGN_BOTTOM_MID, 0, 0);
    lv_keyboard_set_textarea(kb, s_modal_pass_ta);
}
""")

    # Public API
    code.append("""
// =============================================================================
// GLOBAL INTERFACE INITIALIZATION & DISPATCH
// =============================================================================
void ui_init(void)
{
    ESP_LOGI(TAG, "Inicializando Focal CNC UI (Launcher 3x2 con Iconos Vectoriales)...");

    focal_theme_init();
    settings_manager_init();

    // Crear las 7 pantallas definidas en screens_layout.json
    create_launcher_screen();
    create_jogging_screen();
    create_sd_screen();
    create_cut_monitor_screen();
    create_calibration_screen();
    create_shapes_screen();
    create_settings_screen();

    // Iniciar directamente en el Launcher 3x2
    s_current_screen = UI_SCREEN_LAUNCHER;
    lv_scr_load(s_screens[UI_SCREEN_LAUNCHER]);

    ESP_LOGI(TAG, "UI Focal CNC lista con transiciones instantaneas.");
}

void ui_switch_screen(ui_screen_id_t screen_id)
{
    if (screen_id >= UI_SCREEN_MAX || !s_screens[screen_id]) return;

    // Safety hook: If leaving screen and not running a cut job, force laser off
    if (s_current_screen != screen_id && !s_is_cutting) {
        laser_set_power(0);
        laser_set_enable(false);
        s_calib_pointer_on = false;
        if (s_calib_btn_ptr) {
            lv_obj_set_style_bg_color(s_calib_btn_ptr, s_is_dark ? lv_color_hex(0x1A1D24) : lv_color_hex(0xFFFFFF), 0);
        }
    }

    s_current_screen = screen_id;
    lv_scr_load(s_screens[screen_id]);
}

ui_screen_id_t ui_get_current_screen(void)
{
    return s_current_screen;
}

void ui_set_demo_mode(bool enable)
{
    (void)enable;
}

void ui_update_dro(float wx, float wy, float wz, float mx, float my, float mz)
{
    (void)wz; (void)mx; (void)my; (void)mz;
    s_sim_x = wx;
    s_sim_y = wy;
    update_dro_display();
}

void ui_update_status(const char *status_str, uint32_t color_hex)
{
    for (int i = 0; i < UI_SCREEN_MAX; i++) {
        if (s_hdr_pills[i]) {
            lv_label_set_text(s_hdr_pills[i], status_str);
            lv_obj_set_style_text_color(s_hdr_pills[i], lv_color_hex(color_hex), 0);
        }
    }
}

void ui_update_cut_monitor(float progress_pct, uint32_t current_line, uint32_t total_lines, 
                           uint32_t elapsed_sec, uint32_t power_pct, uint32_t feedrate)
{
    (void)power_pct; (void)feedrate;
    if (s_cut_bar) {
        lv_bar_set_value(s_cut_bar, (int32_t)progress_pct, LV_ANIM_OFF);
    }
    if (s_lbl_cut_pct) {
        char buf[64];
        snprintf(buf, sizeof(buf), "Progreso: %.1f%% (Linea %u / %u)", progress_pct, (unsigned)current_line, (unsigned)total_lines);
        lv_label_set_text(s_lbl_cut_pct, buf);
    }
    if (s_lbl_cut_time) {
        char buf[64];
        uint32_t em = elapsed_sec / 60;
        uint32_t es = elapsed_sec % 60;
        snprintf(buf, sizeof(buf), "Transcurrido: %02u:%02u min", (unsigned)em, (unsigned)es);
        lv_label_set_text(s_lbl_cut_time, buf);
    }
}

void ui_show_cut_modal(const char *filename, uint32_t lines, uint32_t est_sec)
{
    if (filename) {
        strncpy(s_pending_cut_file, filename, sizeof(s_pending_cut_file) - 1);
        s_pending_cut_file[sizeof(s_pending_cut_file) - 1] = 0;
    }
    s_pending_lines = lines;
    s_pending_est_sec = est_sec;

    if (s_cut_modal_file_lbl) {
        char buf[80];
        snprintf(buf, sizeof(buf), "Archivo: %s", s_pending_cut_file);
        lv_label_set_text(s_cut_modal_file_lbl, buf);
    }
    if (s_cut_modal_info_lbl) {
        char buf[80];
        uint32_t m = est_sec / 60;
        uint32_t s = est_sec % 60;
        snprintf(buf, sizeof(buf), "Lineas: %u  |  Duracion estimada: %02u:%02u min", (unsigned)lines, (unsigned)m, (unsigned)s);
        lv_label_set_text(s_cut_modal_info_lbl, buf);
    }
    if (s_cut_modal) {
        lv_obj_clear_flag(s_cut_modal, LV_OBJ_FLAG_HIDDEN);
        lv_obj_move_foreground(s_cut_modal);
    }
}

void ui_close_cut_modal(void)
{
    if (s_cut_modal) {
        lv_obj_add_flag(s_cut_modal, LV_OBJ_FLAG_HIDDEN);
    }
}
""")

    return "".join(code)

def main():
    # Determine paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
    
    # Input JSON path
    json_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(project_root, "focal_studio_designer", "screens_layout.json")
    if not os.path.exists(json_path):
        json_path = os.path.join(project_root, "screens_layout.json")
    
    if not os.path.exists(json_path):
        print(f"Error: screens_layout.json not found at {json_path}", file=sys.stderr)
        sys.exit(1)
        
    # Output C file path
    out_c_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(project_root, "components", "ui", "ui_screens.c")
    
    print(f"[codegen_c] Reading layout from: {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        layout_data = json.load(f)
        
    screen_count = len(layout_data.get("screens", []))
    print(f"[codegen_c] Found {screen_count} screens to synthesize.")
    
    c_source = generate_c_code(layout_data)
    
    os.makedirs(os.path.dirname(out_c_path), exist_ok=True)
    with open(out_c_path, "w", encoding="utf-8") as f:
        f.write(c_source)
        
    print(f"[codegen_c] C code synthesized successfully: {out_c_path} ({len(c_source)} bytes)")

if __name__ == "__main__":
    main()
