#!/usr/bin/env python3
"""
build_screens_layout.py - Generates the complete screens_layout.json
describing all 7 UI screens of Focal CNC Laser Cutter.
"""

import json
import os

def create_component(id, type, x, y, width, height, text=None, icon=None, style=None, color=None, callback_id=None, **kwargs):
    comp = {
        "id": id,
        "type": type,
        "x": x,
        "y": y,
        "width": width,
        "height": height,
        "text": text,
        "icon": icon,
        "style": style,
        "color": color,
        "callback_id": callback_id
    }
    for k, v in kwargs.items():
        if v is not None:
            comp[k] = v
    return comp

def build_layout():
    layout = {
        "version": "2.0.0",
        "display": {
            "width": 480,
            "height": 320,
            "orientation": "landscape",
            "controller": "ILI9488",
            "touch_controller": "XPT2046"
        },
        "screens": []
    }

    # =========================================================================
    # 1. LAUNCHER (Grilla 3x2)
    # =========================================================================
    launcher_screen = {
        "id": "launcher",
        "screen_enum": "UI_SCREEN_LAUNCHER",
        "title": "Focal CNC Laser",
        "show_back": False,
        "components": []
    }

    launcher_items = [
        ("btn_launcher_ctrl", "Control", "Jog & DRO", "focal_icon_control", "FOCAL_HEX_PASTEL_BLUE", "on_launcher_card_click", "UI_SCREEN_JOGGING"),
        ("btn_launcher_files", "Archivos", "MicroSD G-Code", "focal_icon_files", "FOCAL_HEX_PASTEL_MINT", "on_launcher_card_click", "UI_SCREEN_SD_FILES"),
        ("btn_launcher_mon", "Monitor", "En Vivo", "focal_icon_monitor", "FOCAL_HEX_PASTEL_AMBER", "on_launcher_card_click", "UI_SCREEN_CUT_MONITOR"),
        ("btn_launcher_calib", "Calibracion", "Foco, Cama & Ejes", "focal_icon_calibration", "0xA78BFA", "on_launcher_card_click", "UI_SCREEN_CALIBRATION"),
        ("btn_launcher_shapes", "Corte Rapido", "Cama 160x200", "focal_icon_shapes", "FOCAL_HEX_PASTEL_BLUE", "on_launcher_card_click", "UI_SCREEN_SHAPES"),
        ("btn_launcher_sett", "Ajustes", "WiFi, Tema & Laser", "focal_icon_settings", "FOCAL_HEX_PASTEL_MINT", "on_launcher_card_click", "UI_SCREEN_SETTINGS")
    ]

    card_w, card_h = 146, 124
    start_x, start_y = 10, 50
    gap_x, gap_y = 10, 10

    for idx, (cid, title, subtitle, icon, color, cb, target) in enumerate(launcher_items):
        col = idx % 3
        row = idx // 3
        x = start_x + col * (card_w + gap_x)
        y = start_y + row * (card_h + gap_y)

        btn = create_component(
            id=cid,
            type="button",
            x=x,
            y=y,
            width=card_w,
            height=card_h,
            text=title,
            icon=icon,
            style="focal_style_btn_secondary",
            color=color,
            callback_id=cb,
            user_data=target,
            subtitle=subtitle,
            radius="FOCAL_RADIUS_L"
        )
        launcher_screen["components"].append(btn)

    layout["screens"].append(launcher_screen)

    # =========================================================================
    # 2. CONTROL MANUAL / JOGGING & DRO
    # =========================================================================
    jogging_screen = {
        "id": "jogging",
        "screen_enum": "UI_SCREEN_JOGGING",
        "title": "Control de Ejes",
        "show_back": True,
        "components": []
    }

    # Left Panel: DRO & Actions
    card_dro = create_component(
        id="card_dro",
        type="card",
        x=10,
        y=48,
        width=210,
        height=260,
        text="Posicion Actual",
        icon=None,
        style="focal_style_card",
        color=None,
        callback_id=None,
        children=[
            create_component("box_dro_x", "dro", 6, 28, 186, 42, text="X:    0.0 mm", icon=None, style="focal_style_pill", color="FOCAL_COLOR_PASTEL_BLUE", callback_id=None),
            create_component("box_dro_y", "dro", 6, 78, 186, 42, text="Y:    0.0 mm", icon=None, style="focal_style_pill", color="FOCAL_COLOR_PASTEL_MINT", callback_id=None),
            create_component("btn_jog_zero", "button", 6, 138, 186, 42, text="Fijar Home", icon="focal_icon_check", style="focal_style_btn_secondary", color="FOCAL_HEX_PASTEL_MINT", callback_id="on_jog_btn_cb", user_data="ZERO"),
            create_component("btn_jog_home", "button", 6, 188, 186, 42, text="Home", icon="focal_icon_home", style="focal_style_btn_secondary", color="FOCAL_HEX_PASTEL_BLUE", callback_id="on_jog_btn_cb", user_data="HOME")
        ]
    )
    jogging_screen["components"].append(card_dro)

    # Right Panel: Step selector and Pad
    card_jog = create_component(
        id="card_jog",
        type="card",
        x=230,
        y=48,
        width=240,
        height=260,
        text=None,
        icon=None,
        style="focal_style_card",
        color=None,
        callback_id=None,
        children=[
            create_component("btn_step_01", "button", 6, 4, 50, 32, text="0.1", icon=None, style="focal_style_btn_secondary", color=None, callback_id="on_jog_step_select_cb", user_data=0),
            create_component("btn_step_10", "button", 61, 4, 50, 32, text="1.0", icon=None, style="focal_style_btn_secondary", color=None, callback_id="on_jog_step_select_cb", user_data=1),
            create_component("btn_step_100", "button", 116, 4, 50, 32, text="10", icon=None, style="focal_style_btn_secondary", color=None, callback_id="on_jog_step_select_cb", user_data=2, selected=True),
            create_component("btn_step_500", "button", 171, 4, 50, 32, text="50", icon=None, style="focal_style_btn_secondary", color=None, callback_id="on_jog_step_select_cb", user_data=3),
            create_component("btn_jog_up", "button", 95, 65, 50, 50, text=None, icon="focal_icon_jog_up", style="focal_style_btn_secondary", color="FOCAL_HEX_PASTEL_BLUE", callback_id="on_jog_btn_cb", user_data="Y+", ext_click_area=6),
            create_component("btn_jog_down", "button", 95, 181, 50, 50, text=None, icon="focal_icon_jog_down", style="focal_style_btn_secondary", color="FOCAL_HEX_PASTEL_BLUE", callback_id="on_jog_btn_cb", user_data="Y-", ext_click_area=6),
            create_component("btn_jog_left", "button", 37, 123, 50, 50, text=None, icon="focal_icon_jog_left", style="focal_style_btn_secondary", color="FOCAL_HEX_PASTEL_BLUE", callback_id="on_jog_btn_cb", user_data="X-", ext_click_area=6),
            create_component("btn_jog_right", "button", 153, 123, 50, 50, text=None, icon="focal_icon_jog_right", style="focal_style_btn_secondary", color="FOCAL_HEX_PASTEL_BLUE", callback_id="on_jog_btn_cb", user_data="X+", ext_click_area=6),
            create_component("btn_jog_stop", "button", 95, 123, 50, 50, text=None, icon="focal_icon_stop", style="focal_style_btn_danger", color="0xFFFFFF", callback_id="on_jog_btn_cb", user_data="STOP", ext_click_area=6)
        ]
    )
    jogging_screen["components"].append(card_jog)

    layout["screens"].append(jogging_screen)

    # =========================================================================
    # 3. ARCHIVOS EN MICROSD
    # =========================================================================
    sd_screen = {
        "id": "sd_files",
        "screen_enum": "UI_SCREEN_SD_FILES",
        "title": "Archivos SD",
        "show_back": True,
        "components": []
    }

    card_file_list = create_component(
        id="card_file_list",
        type="card",
        x=10,
        y=48,
        width=250,
        height=260,
        text=None,
        icon=None,
        style="focal_style_card",
        color=None,
        callback_id=None,
        children=[
            create_component("btn_file_item_1", "button", 4, 6, 226, 48, text="corte_circulo_50mm.gcode", icon="focal_icon_files", style="focal_style_btn_secondary", color="FOCAL_HEX_PASTEL_MINT", callback_id="on_file_select_cb", user_data="corte_circulo_50mm.gcode"),
            create_component("btn_file_item_2", "button", 4, 60, 226, 48, text="calibracion_cama_160x200.gcode", icon="focal_icon_files", style="focal_style_btn_secondary", color="FOCAL_HEX_PASTEL_MINT", callback_id="on_file_select_cb", user_data="calibracion_cama_160x200.gcode"),
            create_component("btn_file_item_3", "button", 4, 114, 226, 48, text="grabado_logo.nc", icon="focal_icon_files", style="focal_style_btn_secondary", color="FOCAL_HEX_PASTEL_MINT", callback_id="on_file_select_cb", user_data="grabado_logo.nc"),
            create_component("btn_file_item_4", "button", 4, 168, 226, 48, text="caja_ensamble.gcode", icon="focal_icon_files", style="focal_style_btn_secondary", color="FOCAL_HEX_PASTEL_MINT", callback_id="on_file_select_cb", user_data="caja_ensamble.gcode")
        ]
    )
    sd_screen["components"].append(card_file_list)

    card_file_det = create_component(
        id="card_file_detail",
        type="card",
        x=270,
        y=48,
        width=200,
        height=260,
        text=None,
        icon=None,
        style="focal_style_card",
        color=None,
        callback_id=None,
        children=[
            create_component("lbl_file_header", "label", 6, 4, 175, 20, text="Detalles", icon=None, style=None, color=None, callback_id=None),
            create_component("lbl_file_name", "label", 6, 32, 175, 40, text="corte_circulo_50mm.gcode", icon=None, style=None, color="FOCAL_COLOR_PASTEL_BLUE", callback_id=None),
            create_component("lbl_file_info", "label", 6, 80, 175, 60, text="Lineas: 1420 | Duracion: 03:45 min\nPotencia: 80% | Foco Z: 30 mm", icon=None, style=None, color=None, callback_id=None),
            create_component("btn_file_run", "button", 12, 198, 176, 48, text="Iniciar Corte", icon="focal_icon_play", style="focal_style_btn_mint", color="0xFFFFFF", callback_id="on_file_start_cut_cb")
        ]
    )
    sd_screen["components"].append(card_file_det)

    # Modal Safety Confirmation
    modal_cut = create_component(
        id="modal_cut_confirm",
        type="modal",
        x=0,
        y=0,
        width=480,
        height=320,
        text=None,
        icon=None,
        style=None,
        color=None,
        callback_id=None,
        children=[
            create_component(
                "card_modal_dialog", "card", 50, 40, 380, 240, text=None, icon=None, style="focal_style_card", color=None, callback_id=None,
                children=[
                    create_component("lbl_modal_title", "label", 6, 6, 350, 24, text="Confirmar Inicio de Corte", icon="focal_icon_laser", style=None, color="FOCAL_COLOR_PASTEL_BLUE", callback_id=None),
                    create_component("lbl_modal_file", "label", 6, 36, 350, 20, text="Archivo: corte_circulo_50mm.gcode", icon=None, style=None, color="FOCAL_COLOR_PASTEL_MINT", callback_id=None),
                    create_component("lbl_modal_info", "label", 6, 60, 350, 20, text="Lineas: 1420  |  Duracion est: 03:45 min", icon=None, style=None, color=None, callback_id=None),
                    create_component("box_modal_warn", "card", 15, 88, 350, 56, text="ATENCION: Use gafas de proteccion laser.\nEl cabezal se movera y el haz se activara.", icon=None, style="focal_style_warn_box", color=None, callback_id=None),
                    create_component("btn_cut_modal_cancel", "button", 6, 188, 120, 42, text="Cancelar", icon=None, style="focal_style_btn_secondary", color=None, callback_id="on_cut_modal_cancel_cb"),
                    create_component("btn_cut_modal_start", "button", 168, 188, 206, 42, text="Iniciar Corte Ahora", icon="focal_icon_play", style="focal_style_btn_mint", color="0xFFFFFF", callback_id="on_cut_modal_confirm_cb")
                ]
            )
        ]
    )
    sd_screen["components"].append(modal_cut)

    layout["screens"].append(sd_screen)

    # =========================================================================
    # 4. MONITOR EN VIVO
    # =========================================================================
    monitor_screen = {
        "id": "cut_monitor",
        "screen_enum": "UI_SCREEN_CUT_MONITOR",
        "title": "Monitor en Vivo",
        "show_back": True,
        "components": []
    }

    card_mon = create_component(
        id="card_monitor",
        type="card",
        x=10,
        y=48,
        width=460,
        height=260,
        text=None,
        icon=None,
        style="focal_style_card",
        color=None,
        callback_id=None,
        children=[
            create_component("bar_cut_progress", "bar", 15, 6, 430, 20, text=None, icon=None, style=None, color="FOCAL_COLOR_PASTEL_MINT", callback_id=None, min=0, max=100, value=45),
            create_component("lbl_cut_pct", "label", 15, 30, 430, 20, text="Progreso: 45.0% (Linea 640 / 1420)", icon=None, style=None, color=None, callback_id=None),
            create_component(
                "box_cut_telemetry", "card", 15, 52, 430, 60, text=None, icon=None, style="focal_style_pill", color=None, callback_id=None,
                children=[
                    create_component("lbl_cut_time", "label", 10, 6, 410, 20, text="Transcurrido: 01:42 min  |  Restante: 02:03 min", icon=None, style=None, color="FOCAL_COLOR_PASTEL_BLUE", callback_id=None),
                    create_component("lbl_cut_metrics", "label", 10, 32, 410, 20, text="Potencia: 80% (PWM 5kHz)  |  Avance: 2400 mm/min", icon=None, style=None, color=None, callback_id=None)
                ]
            ),
            create_component(
                "box_cut_overrides", "card", 15, 118, 430, 44, text=None, icon=None, style="focal_style_pill", color=None, callback_id=None,
                children=[
                    create_component("lbl_feed_ovr", "label", 8, 12, 80, 20, text="Vel: 100%", icon=None, style=None, color="FOCAL_COLOR_PASTEL_AMBER", callback_id=None),
                    create_component("btn_feed_minus", "button", 96, 8, 32, 28, text="-", icon=None, style="focal_style_btn_secondary", color=None, callback_id="on_feed_ovr_cb", user_data=-10, ext_click_area=6),
                    create_component("btn_feed_plus", "button", 134, 8, 32, 28, text="+", icon=None, style="focal_style_btn_secondary", color=None, callback_id="on_feed_ovr_cb", user_data=10, ext_click_area=6),
                    create_component("lbl_power_ovr", "label", 224, 12, 80, 20, text="Pot: 100%", icon=None, style=None, color="FOCAL_COLOR_PASTEL_MINT", callback_id=None),
                    create_component("btn_power_minus", "button", 312, 8, 32, 28, text="-", icon=None, style="focal_style_btn_secondary", color=None, callback_id="on_power_ovr_cb", user_data=-10, ext_click_area=6),
                    create_component("btn_power_plus", "button", 350, 8, 32, 28, text="+", icon=None, style="focal_style_btn_secondary", color=None, callback_id="on_power_ovr_cb", user_data=10, ext_click_area=6)
                ]
            ),
            create_component("btn_cut_pause_resume", "button", 8, 198, 205, 48, text="Pausar / Seguir", icon="focal_icon_pause", style="focal_style_btn_amber", color="0xFFFFFF", callback_id="on_cut_pause_resume_cb"),
            create_component("btn_cut_estop", "button", 235, 198, 205, 48, text="PARADA E-STOP", icon="focal_icon_estop", style="focal_style_btn_danger", color="0xFFFFFF", callback_id="on_cut_estop_cb")
        ]
    )
    monitor_screen["components"].append(card_mon)

    layout["screens"].append(monitor_screen)

    # =========================================================================
    # 5. CALIBRACION (NIVELACION MANUAL Z - 4 TORNILLOS + CENTRO)
    # =========================================================================
    calib_screen = {
        "id": "calibration",
        "screen_enum": "UI_SCREEN_CALIBRATION",
        "title": "Nivelacion de Cama (Manual Z)",
        "show_back": True,
        "components": []
    }

    # Left: Diagrama Cama
    card_calib_bed = create_component(
        id="card_calib_bed",
        type="card",
        x=10,
        y=46,
        width=190,
        height=262,
        text="Cama 160x200 mm",
        icon=None,
        style="focal_style_card",
        color="FOCAL_COLOR_PASTEL_BLUE",
        callback_id=None,
        children=[
            create_component(
                "box_bed_canvas", "bed", 15, 24, 140, 175, text=None, icon=None, style=None, color=None, callback_id=None,
                children=[
                    create_component("btn_calib_pt_t1", "button", 8, 135, 32, 32, text="T1", icon=None, style="focal_style_btn_secondary", color=None, callback_id="on_calib_point_click_cb", user_data=0, ext_click_area=8),
                    create_component("btn_calib_pt_t2", "button", 100, 135, 32, 32, text="T2", icon=None, style="focal_style_btn_secondary", color=None, callback_id="on_calib_point_click_cb", user_data=1, ext_click_area=8),
                    create_component("btn_calib_pt_t3", "button", 100, 8, 32, 32, text="T3", icon=None, style="focal_style_btn_secondary", color=None, callback_id="on_calib_point_click_cb", user_data=2, ext_click_area=8),
                    create_component("btn_calib_pt_t4", "button", 8, 8, 32, 32, text="T4", icon=None, style="focal_style_btn_secondary", color=None, callback_id="on_calib_point_click_cb", user_data=3, ext_click_area=8),
                    create_component("btn_calib_pt_c", "button", 54, 71, 32, 32, text="C", icon=None, style="focal_style_btn_secondary", color=None, callback_id="on_calib_point_click_cb", user_data=4, ext_click_area=8),
                    create_component("calib_laser_dot", "card", 17, 144, 14, 14, text=None, icon=None, style=None, color="0xEF4444", callback_id=None)
                ]
            ),
            create_component("lbl_calib_footer", "label", 10, 236, 170, 20, text="4 Perillas Manuales Z", icon=None, style=None, color=None, callback_id=None)
        ]
    )
    calib_screen["components"].append(card_calib_bed)

    # Right: Wizard
    card_calib_wiz = create_component(
        id="card_calib_wizard",
        type="card",
        x=206,
        y=46,
        width=264,
        height=262,
        text=None,
        icon=None,
        style="focal_style_card",
        color=None,
        callback_id=None,
        children=[
            create_component("lbl_calib_step", "label", 6, 2, 248, 20, text="Paso 1/5: Frontal Izq", icon=None, style=None, color="FOCAL_COLOR_PASTEL_MINT", callback_id=None),
            create_component("lbl_calib_coords", "label", 6, 24, 248, 20, text="Cabezal: X: 10 mm | Y: 10 mm", icon=None, style=None, color=None, callback_id=None),
            create_component("box_calib_instruction", "card", 6, 48, 248, 70, text="Gira la perilla inferior-izquierda hasta que la galga o tarjeta pase rozando la boquilla.", icon=None, style="focal_style_card", color=None, callback_id=None),
            create_component("bar_calib_travel", "bar", 6, 124, 248, 6, text=None, icon=None, style=None, color="FOCAL_COLOR_PASTEL_AMBER", callback_id=None, min=0, max=100, value=100),
            create_component("btn_calib_pointer", "button", 6, 136, 118, 36, text="Puntero 1%", icon="focal_icon_laser", style="focal_style_btn_secondary", color="FOCAL_HEX_PASTEL_AMBER", callback_id="on_calib_pointer_toggle_cb", ext_click_area=6),
            create_component("btn_calib_reset", "button", 132, 136, 118, 36, text="Reiniciar", icon="focal_icon_refresh", style="focal_style_btn_secondary", color="FOCAL_HEX_PASTEL_BLUE", callback_id="on_calib_reset_cb", ext_click_area=6),
            create_component("btn_calib_prev", "button", 6, 184, 108, 44, text="Anterior", icon=None, style="focal_style_btn_secondary", color=None, callback_id="on_calib_prev_cb", ext_click_area=6),
            create_component("btn_calib_next", "button", 120, 184, 134, 44, text="Siguiente", icon="focal_icon_check", style="focal_style_btn_mint", color="0xFFFFFF", callback_id="on_calib_next_cb", ext_click_area=6)
        ]
    )
    calib_screen["components"].append(card_calib_wiz)

    layout["screens"].append(calib_screen)

    # =========================================================================
    # 6. CORTE RAPIDO (CAMA 160x200 mm)
    # =========================================================================
    shapes_screen = {
        "id": "shapes",
        "screen_enum": "UI_SCREEN_SHAPES",
        "title": "Corte Rapido de Taller",
        "show_back": True,
        "components": []
    }

    card_shapes_bed = create_component(
        id="card_shapes_bed",
        type="card",
        x=10,
        y=46,
        width=196,
        height=264,
        text=None,
        icon=None,
        style="focal_style_card",
        color=None,
        callback_id=None,
        children=[
            create_component(
                "bed_shapes_obj", "bed", 38, 4, 120, 150, text=None, icon=None, style=None, color=None, callback_id="on_bed_touch_event_cb",
                children=[
                    create_component("bed_shapes_preview", "card", 37, 75, 30, 30, text=None, icon=None, style=None, color="FOCAL_HEX_PASTEL_BLUE", callback_id=None)
                ]
            ),
            create_component("btn_shape_pos_center", "button", 3, 158, 60, 26, text="Centro", icon=None, style="focal_style_btn_secondary", color=None, callback_id="on_shape_pos_preset_cb", user_data=0, ext_click_area=8),
            create_component("btn_shape_pos_origin", "button", 65, 158, 60, 26, text="Origen", icon=None, style="focal_style_btn_secondary", color=None, callback_id="on_shape_pos_preset_cb", user_data=1, ext_click_area=8),
            create_component("btn_shape_pos_here", "button", 127, 158, 60, 26, text="Aqui", icon=None, style="focal_style_btn_secondary", color=None, callback_id="on_shape_pos_preset_cb", user_data=2, ext_click_area=8),
            create_component("btn_nudge_left", "button", 8, 188, 38, 26, text=None, icon="focal_icon_jog_left", style="focal_style_btn_secondary", color="FOCAL_HEX_PASTEL_BLUE", callback_id="on_shape_nudge_cb", user_data=0, ext_click_area=10),
            create_component("btn_nudge_right", "button", 52, 188, 38, 26, text=None, icon="focal_icon_jog_right", style="focal_style_btn_secondary", color="FOCAL_HEX_PASTEL_BLUE", callback_id="on_shape_nudge_cb", user_data=1, ext_click_area=10),
            create_component("btn_nudge_up", "button", 96, 188, 38, 26, text=None, icon="focal_icon_jog_up", style="focal_style_btn_secondary", color="FOCAL_HEX_PASTEL_BLUE", callback_id="on_shape_nudge_cb", user_data=2, ext_click_area=10),
            create_component("btn_nudge_down", "button", 140, 188, 38, 26, text=None, icon="focal_icon_jog_down", style="focal_style_btn_secondary", color="FOCAL_HEX_PASTEL_BLUE", callback_id="on_shape_nudge_cb", user_data=3, ext_click_area=10),
            create_component("lbl_shape_pos", "label", 6, 236, 180, 20, text="X: 50  Y: 50 mm", icon=None, style=None, color="FOCAL_COLOR_PASTEL_BLUE", callback_id=None)
        ]
    )
    shapes_screen["components"].append(card_shapes_bed)

    card_shapes_ctrl = create_component(
        id="card_shapes_ctrl",
        type="card",
        x=216,
        y=46,
        width=254,
        height=264,
        text=None,
        icon=None,
        style="focal_style_card",
        color=None,
        callback_id=None,
        children=[
            # Shapes row
            create_component("btn_shape_circ", "button", 6, 4, 54, 34, text=None, icon="focal_icon_shape_circle", style="focal_style_btn_secondary", color="0xFFFFFF", callback_id="on_shape_icon_btn_click", user_data=0),
            create_component("btn_shape_sq", "button", 66, 4, 54, 34, text=None, icon="focal_icon_shape_square", style="focal_style_btn_secondary", color="0xFFFFFF", callback_id="on_shape_icon_btn_click", user_data=1),
            create_component("btn_shape_rect", "button", 126, 4, 54, 34, text=None, icon="focal_icon_shape_rect", style="focal_style_btn_secondary", color="0xFFFFFF", callback_id="on_shape_icon_btn_click", user_data=2),
            create_component("btn_shape_line", "button", 186, 4, 54, 34, text=None, icon="focal_icon_laser", style="focal_style_btn_secondary", color="0xFFFFFF", callback_id="on_shape_icon_btn_click", user_data=3),
            # Size row
            create_component("lbl_shape_size", "label", 6, 46, 160, 20, text="Tamano: 40 mm", icon=None, style=None, color=None, callback_id=None),
            create_component("btn_shape_size_minus", "button", 178, 42, 28, 24, text="-", icon=None, style="focal_style_btn_secondary", color=None, callback_id="on_shape_size_adj_cb", user_data=-5, ext_click_area=10),
            create_component("btn_shape_size_plus", "button", 212, 42, 28, 24, text="+", icon=None, style="focal_style_btn_secondary", color=None, callback_id="on_shape_size_adj_cb", user_data=5, ext_click_area=10),
            # Size presets
            create_component("btn_shape_sz_20", "button", 6, 70, 54, 26, text="20", icon=None, style="focal_style_btn_secondary", color=None, callback_id="on_shape_size_preset_cb", user_data=20, ext_click_area=6),
            create_component("btn_shape_sz_40", "button", 66, 70, 54, 26, text="40", icon=None, style="focal_style_btn_secondary", color=None, callback_id="on_shape_size_preset_cb", user_data=40, ext_click_area=6),
            create_component("btn_shape_sz_60", "button", 126, 70, 54, 26, text="60", icon=None, style="focal_style_btn_secondary", color=None, callback_id="on_shape_size_preset_cb", user_data=60, ext_click_area=6),
            create_component("btn_shape_sz_80", "button", 186, 70, 54, 26, text="80", icon=None, style="focal_style_btn_secondary", color=None, callback_id="on_shape_size_preset_cb", user_data=80, ext_click_area=6),
            # Power row
            create_component("lbl_shape_power", "label", 6, 104, 160, 20, text="Potencia: 80%", icon=None, style=None, color=None, callback_id=None),
            create_component("btn_shape_pwr_minus", "button", 178, 100, 28, 24, text="-", icon=None, style="focal_style_btn_secondary", color=None, callback_id="on_shape_power_adj_cb", user_data=-10, ext_click_area=10),
            create_component("btn_shape_pwr_plus", "button", 212, 100, 28, 24, text="+", icon=None, style="focal_style_btn_secondary", color=None, callback_id="on_shape_power_adj_cb", user_data=10, ext_click_area=10),
            # Power presets
            create_component("btn_shape_pw_25", "button", 6, 128, 54, 26, text="25%", icon=None, style="focal_style_btn_secondary", color=None, callback_id="on_shape_power_preset_cb", user_data=25, ext_click_area=6),
            create_component("btn_shape_pw_50", "button", 66, 128, 54, 26, text="50%", icon=None, style="focal_style_btn_secondary", color=None, callback_id="on_shape_power_preset_cb", user_data=50, ext_click_area=6),
            create_component("btn_shape_pw_75", "button", 126, 128, 54, 26, text="75%", icon=None, style="focal_style_btn_secondary", color=None, callback_id="on_shape_power_preset_cb", user_data=75, ext_click_area=6),
            create_component("btn_shape_pw_100", "button", 186, 128, 54, 26, text="100%", icon=None, style="focal_style_btn_secondary", color=None, callback_id="on_shape_power_preset_cb", user_data=100, ext_click_area=6),
            # Actions
            create_component("btn_shape_frame", "button", 6, 208, 114, 44, text="Enmarcar", icon="focal_icon_laser", style="focal_style_btn_secondary", color="FOCAL_HEX_PASTEL_AMBER", callback_id="on_shape_action_cb", user_data=False, ext_click_area=6),
            create_component("btn_shape_cut", "button", 122, 208, 124, 44, text="Cortar Ahora", icon="focal_icon_play", style="focal_style_btn_mint", color="0xFFFFFF", callback_id="on_shape_action_cb", user_data=True, ext_click_area=6)
        ]
    )
    shapes_screen["components"].append(card_shapes_ctrl)

    layout["screens"].append(shapes_screen)

    # =========================================================================
    # 7. AJUSTES DE MAQUINA (MASTER-DETAIL)
    # =========================================================================
    settings_screen = {
        "id": "settings",
        "screen_enum": "UI_SCREEN_SETTINGS",
        "title": "Ajustes de Maquina",
        "show_back": True,
        "components": []
    }

    # Master list
    nav_card = create_component(
        id="nav_card",
        type="card",
        x=6,
        y=46,
        width=136,
        height=266,
        text=None,
        icon=None,
        style="focal_style_card",
        color=None,
        callback_id=None,
        children=[
            create_component("btn_sett_wifi", "button", 1, 2, 126, 40, text="Red Wi-Fi", icon="focal_icon_wifi", style="focal_style_btn_secondary", color="FOCAL_HEX_PASTEL_BLUE", callback_id="on_settings_menu_select_cb", user_data=0),
            create_component("btn_sett_app", "button", 1, 45, 126, 40, text="Apariencia", icon="focal_icon_theme", style="focal_style_btn_secondary", color="FOCAL_HEX_PASTEL_BLUE", callback_id="on_settings_menu_select_cb", user_data=1),
            create_component("btn_sett_las", "button", 1, 88, 126, 40, text="Laser", icon="focal_icon_laser", style="focal_style_btn_secondary", color="FOCAL_HEX_PASTEL_BLUE", callback_id="on_settings_menu_select_cb", user_data=2),
            create_component("btn_sett_sd", "button", 1, 131, 126, 40, text="Tarjeta SD", icon="focal_icon_files", style="focal_style_btn_secondary", color="FOCAL_HEX_PASTEL_BLUE", callback_id="on_settings_menu_select_cb", user_data=3),
            create_component("btn_sett_kin", "button", 1, 174, 126, 40, text="Cinematica", icon="focal_icon_shapes", style="focal_style_btn_secondary", color="FOCAL_HEX_PASTEL_BLUE", callback_id="on_settings_menu_select_cb", user_data=4),
            create_component("btn_sett_sys", "button", 1, 217, 126, 40, text="Sistema", icon="focal_icon_settings", style="focal_style_btn_secondary", color="FOCAL_HEX_PASTEL_BLUE", callback_id="on_settings_menu_select_cb", user_data=5)
        ]
    )
    settings_screen["components"].append(nav_card)

    # Detail column
    detail_area = create_component(
        id="detail_area",
        type="card",
        x=146,
        y=46,
        width=328,
        height=266,
        text=None,
        icon=None,
        style="focal_style_card",
        color=None,
        callback_id=None,
        children=[
            # Panel 0: Wi-Fi
            create_component(
                "p0_wifi", "card", 0, 0, 314, 252, text=None, icon=None, style=None, color=None, callback_id=None,
                children=[
                    create_component("btn_wifi_scan", "button", 6, 6, 142, 34, text="Escanear", icon="focal_icon_refresh", style="focal_style_btn_secondary", color="FOCAL_HEX_PASTEL_BLUE", callback_id="on_wifi_scan_btn_cb", ext_click_area=6),
                    create_component("btn_wifi_forget", "button", 166, 6, 142, 34, text="Olvidar Red", icon="focal_icon_trash", style="focal_style_btn_secondary", color="FOCAL_HEX_PASTEL_RED", callback_id="on_wifi_forget_btn_cb", ext_click_area=6),
                    create_component("lbl_wifi_detail", "label", 6, 46, 300, 20, text="Toca 'Escanear' para buscar redes.", icon=None, style=None, color=None, callback_id=None),
                    create_component("list_wifi_networks", "card", 6, 70, 302, 178, text=None, icon=None, style=None, color=None, callback_id=None)
                ]
            ),
            # Panel 1: Apariencia
            create_component(
                "p1_appearance", "card", 0, 0, 314, 252, text=None, icon=None, style=None, color=None, callback_id=None,
                children=[
                    create_component("lbl_app_theme", "label", 6, 6, 300, 20, text="Tema de Pantalla", icon=None, style=None, color=None, callback_id=None),
                    create_component("btn_theme_dark", "button", 6, 30, 142, 42, text="Modo Oscuro", icon=None, style="focal_style_btn_secondary", color=None, callback_id="on_theme_toggle_cb", user_data=True, ext_click_area=6),
                    create_component("btn_theme_light", "button", 156, 30, 142, 42, text="Modo Claro", icon=None, style="focal_style_btn_secondary", color=None, callback_id="on_theme_toggle_cb", user_data=False, ext_click_area=6),
                    create_component("lbl_app_accent", "label", 6, 88, 300, 20, text="Color de Enfasis", icon=None, style=None, color=None, callback_id=None),
                    create_component("btn_accent_0", "button", 8, 112, 54, 40, text="Azul", icon=None, style=None, color="FOCAL_HEX_PASTEL_BLUE", callback_id="on_accent_select_cb", user_data=0, ext_click_area=4),
                    create_component("btn_accent_1", "button", 68, 112, 54, 40, text="Menta", icon=None, style=None, color="FOCAL_HEX_PASTEL_MINT", callback_id="on_accent_select_cb", user_data=1, ext_click_area=4),
                    create_component("btn_accent_2", "button", 128, 112, 54, 40, text="Ambar", icon=None, style=None, color="FOCAL_HEX_PASTEL_AMBER", callback_id="on_accent_select_cb", user_data=2, ext_click_area=4),
                    create_component("btn_accent_3", "button", 188, 112, 54, 40, text="Morado", icon=None, style=None, color="0xA78BFA", callback_id="on_accent_select_cb", user_data=3, ext_click_area=4),
                    create_component("btn_accent_4", "button", 248, 112, 54, 40, text="Rojo", icon=None, style=None, color="FOCAL_HEX_PASTEL_RED", callback_id="on_accent_select_cb", user_data=4, ext_click_area=4),
                    create_component("lbl_app_persistence", "label", 6, 220, 300, 20, text="El tema y color se guardan en la memoria Flash.", icon=None, style=None, color=None, callback_id=None)
                ]
            ),
            # Panel 2: Láser
            create_component(
                "p2_laser", "card", 0, 0, 314, 252, text=None, icon=None, style=None, color=None, callback_id=None,
                children=[
                    create_component("lbl_laser_title", "label", 6, 6, 300, 20, text="Parametros Modulo Laser", icon=None, style=None, color=None, callback_id=None),
                    create_component("lbl_laser_pwr", "label", 6, 32, 300, 20, text="Potencia Maxima: 1000 (S)", icon=None, style=None, color="FOCAL_COLOR_PASTEL_BLUE", callback_id=None),
                    create_component("slider_laser_pwr", "slider", 6, 56, 290, 16, text=None, icon=None, style=None, color="FOCAL_COLOR_PASTEL_BLUE", callback_id=None, min=100, max=1000, value=1000),
                    create_component("lbl_laser_air", "label", 6, 90, 200, 20, text="Asistencia Aire M8 Auto:", icon=None, style=None, color=None, callback_id=None),
                    create_component("sw_laser_air", "switch", 230, 84, 50, 25, text=None, icon=None, style=None, color=None, callback_id=None, checked=True),
                    create_component("btn_laser_pulse", "button", 6, 140, 142, 42, text="Pulso 1s", icon="focal_icon_laser", style="focal_style_btn_amber", color="0xFFFFFF", callback_id="on_laser_test_pulse_cb", ext_click_area=6),
                    create_component("btn_laser_save", "button", 156, 140, 142, 42, text="Guardar", icon="focal_icon_check", style="focal_style_btn_mint", color="0xFFFFFF", callback_id="on_laser_save_cb", ext_click_area=6)
                ]
            ),
            # Panel 3: Tarjeta SD
            create_component(
                "p3_sd", "card", 0, 0, 314, 252, text=None, icon=None, style=None, color=None, callback_id=None,
                children=[
                    create_component("lbl_sd_title", "label", 6, 6, 300, 20, text="Almacenamiento MicroSD", icon=None, style=None, color=None, callback_id=None),
                    create_component("lbl_sd_use", "label", 6, 32, 300, 20, text="Uso: 1.9 GB / 16 GB (FAT32 - 12%)", icon=None, style=None, color="FOCAL_COLOR_PASTEL_MINT", callback_id=None),
                    create_component("bar_sd_use", "bar", 6, 56, 290, 14, text=None, icon=None, style=None, color="FOCAL_COLOR_PASTEL_MINT", callback_id=None, min=0, max=100, value=12),
                    create_component("lbl_sd_ovr", "label", 6, 92, 200, 20, text="Sobrescribir Duplicados:", icon=None, style=None, color=None, callback_id=None),
                    create_component("sw_sd_ovr", "switch", 230, 86, 50, 25, text=None, icon=None, style=None, color=None, callback_id=None, checked=True),
                    create_component("btn_sd_refresh", "button", 6, 140, 142, 42, text="Actualizar", icon="focal_icon_refresh", style="focal_style_btn_secondary", color="FOCAL_HEX_PASTEL_BLUE", callback_id="on_sd_refresh_cb", ext_click_area=6),
                    create_component("btn_sd_clean", "button", 156, 140, 142, 42, text="Limpiar Temp", icon="focal_icon_trash", style="focal_style_btn_secondary", color="FOCAL_HEX_PASTEL_RED", callback_id="on_sd_clean_cb", ext_click_area=6)
                ]
            ),
            # Panel 4: Cinemática
            create_component(
                "p4_kinematics", "card", 0, 0, 314, 252, text=None, icon=None, style=None, color=None, callback_id=None,
                children=[
                    create_component("lbl_kin_title", "label", 6, 6, 300, 20, text="Cinematica 160x200 mm", icon=None, style=None, color=None, callback_id=None),
                    create_component("lbl_kin_feed", "label", 6, 32, 300, 20, text="Velocidad Max: 6000 mm/min", icon=None, style=None, color="FOCAL_COLOR_PASTEL_AMBER", callback_id=None),
                    create_component("slider_kin_feed", "slider", 6, 56, 290, 16, text=None, icon=None, style=None, color="FOCAL_COLOR_PASTEL_AMBER", callback_id=None, min=500, max=8000, value=6000),
                    create_component("lbl_kin_steps", "label", 6, 92, 300, 20, text="X: 400 pas/mm | Y: 400 pas/mm (T8x8)", icon=None, style=None, color=None, callback_id=None),
                    create_component("btn_kin_tx", "button", 6, 140, 142, 42, text="Test Eje X", icon=None, style="focal_style_btn_secondary", color=None, callback_id="on_kinematics_test_x_cb", ext_click_area=6),
                    create_component("btn_kin_ty", "button", 156, 140, 142, 42, text="Test Eje Y", icon=None, style="focal_style_btn_secondary", color=None, callback_id="on_kinematics_test_y_cb", ext_click_area=6)
                ]
            ),
            # Panel 5: Sistema
            create_component(
                "p5_system", "card", 0, 0, 314, 252, text=None, icon=None, style=None, color=None, callback_id=None,
                children=[
                    create_component("lbl_sys_title", "label", 6, 6, 300, 20, text="Hardware y Firmware", icon=None, style=None, color=None, callback_id=None),
                    create_component("lbl_sys_val", "label", 6, 32, 300, 80, text="SoC: ESP32-S3 Dual-Core 240MHz\nRAM: 8MB PSRAM | Flash: 16MB\nFirmware: Focal CNC Studio v2.0\nPantalla: TFT 3.5\" 480x320 ILI9488", icon=None, style=None, color=None, callback_id=None),
                    create_component("btn_sys_reset", "button", 6, 140, 292, 42, text="Reset de Fabrica", icon="focal_icon_trash", style="focal_style_btn_danger", color="0xFFFFFF", callback_id="on_factory_reset_confirmed_cb", ext_click_area=6)
                ]
            )
        ]
    )
    settings_screen["components"].append(detail_area)

    # Floating Wi-Fi Keyboard Modal
    modal_wifi = create_component(
        id="modal_wifi_keyboard",
        type="modal",
        x=0,
        y=0,
        width=480,
        height=320,
        text=None,
        icon=None,
        style="focal_style_screen",
        color=None,
        callback_id=None,
        children=[
            create_component("lbl_modal_wifi_ssid", "label", 14, 12, 218, 20, text="Conectar a:", icon=None, style=None, color="FOCAL_COLOR_PASTEL_BLUE", callback_id=None),
            create_component("ta_modal_wifi_pass", "textarea", 14, 38, 218, 42, text=None, icon=None, style="focal_style_card", color=None, callback_id=None, placeholder="Ingresa clave Wi-Fi", password_mode=True),
            create_component("btn_modal_wifi_conn", "button", 240, 38, 108, 42, text="Conectar", icon="focal_icon_check", style="focal_style_btn_mint", color="0xFFFFFF", callback_id="on_modal_connect_cb", ext_click_area=6),
            create_component("btn_modal_wifi_canc", "button", 356, 38, 108, 42, text="Cancelar", icon=None, style="focal_style_btn_secondary", color=None, callback_id="on_modal_cancel_cb", ext_click_area=6),
            create_component("kb_modal_wifi", "keyboard", 0, 145, 480, 175, text=None, icon=None, style=None, color=None, callback_id=None)
        ]
    )
    settings_screen["components"].append(modal_wifi)

    layout["screens"].append(settings_screen)

    return layout

if __name__ == "__main__":
    layout = build_layout()
    output_path = os.path.join(os.path.dirname(__file__), "..", "screens_layout.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(layout, f, indent=2, ensure_ascii=False)
    print(f"Screens layout successfully generated at {os.path.abspath(output_path)}")
