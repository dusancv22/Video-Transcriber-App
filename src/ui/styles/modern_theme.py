"""
Modern Material Design 3 Theme System for Video Transcriber App
This module provides a comprehensive theming system with colors, typography, and component styles.
"""

class ModernTheme:
    """Modern Material Design 3 inspired theme for the Video Transcriber App"""
    
    # Material Design 3 Color Palette
    COLORS = {
        # Primary colors - Modern blue gradient
        'primary': '#3B82F6',
        'primary_hover': '#2563EB',
        'primary_pressed': '#1D4ED8',
        'primary_light': '#EFF6FF',
        'primary_surface': '#DBEAFE',
        
        # Secondary colors
        'secondary': '#8B5CF6',
        'secondary_hover': '#7C3AED',
        'secondary_light': '#EDE9FE',
        
        # Neutral colors for backgrounds and text
        'background': '#F8FAFC',
        'surface': '#FFFFFF',
        'surface_variant': '#F1F5F9',
        'outline': '#E2E8F0',
        'outline_variant': '#CBD5E1',
        
        # Text colors
        'text_primary': '#0F172A',
        'text_secondary': '#475569',
        'text_tertiary': '#64748B',
        'text_disabled': '#94A3B8',
        'text_on_primary': '#FFFFFF',
        
        # Semantic colors
        'success': '#10B981',
        'success_light': '#D1FAE5',
        'warning': '#F59E0B',
        'warning_light': '#FEF3C7',
        'error': '#EF4444',
        'error_light': '#FEE2E2',
        'info': '#06B6D4',
        'info_light': '#CFFAFE',
    }
    
    # Typography Scale
    TYPOGRAPHY = {
        'font_family': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
        'font_family_mono': '"SF Mono", Monaco, "Cascadia Code", "Roboto Mono", Consolas, "Courier New", monospace',
        
        # Font sizes
        'size_xs': '11px',
        'size_sm': '12px',
        'size_base': '14px',
        'size_lg': '16px',
        'size_xl': '18px',
        'size_2xl': '20px',
        'size_3xl': '24px',
        'size_4xl': '32px',
        
        # Font weights
        'weight_normal': '400',
        'weight_medium': '500',
        'weight_semibold': '600',
        'weight_bold': '700',
        
        # Line heights
        'leading_tight': '1.25',
        'leading_normal': '1.5',
        'leading_relaxed': '1.75',
    }
    
    # Spacing System (Compact for flat design)
    SPACING = {
        'xs': '3px',
        'sm': '6px', 
        'md': '8px',
        'lg': '10px',
        'xl': '12px',
        'xxl': '16px',
        'xxxl': '20px',
    }
    
    # Border Radius (Flat design)
    RADIUS = {
        'sm': '2px',
        'md': '3px', 
        'lg': '4px',
        'xl': '6px',
        'full': '9999px',
    }
    
    # Elevation/Shadow System
    SHADOWS = {
        'none': 'none',
        'sm': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        'base': '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
        'md': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        'lg': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
        'xl': '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
    }
    
    @classmethod
    def get_stylesheet(cls):
        """Generate the complete PyQt6 stylesheet"""
        return f"""
        /* ========================================
           Global Application Styles
           ======================================== */
        
        QMainWindow {{
            background-color: {cls.COLORS['background']};
            color: {cls.COLORS['text_primary']};
            font-family: {cls.TYPOGRAPHY['font_family']};
            font-size: {cls.TYPOGRAPHY['size_base']};
        }}
        
        QWidget {{
            font-family: {cls.TYPOGRAPHY['font_family']};
            font-size: {cls.TYPOGRAPHY['size_base']};
            color: {cls.COLORS['text_primary']};
        }}
        
        /* ========================================
           Modern Card Container
           ======================================== */
        
        .card {{
            background-color: {cls.COLORS['surface']};
            border: 1px solid {cls.COLORS['outline']};
            border-radius: {cls.RADIUS['lg']};
            padding: {cls.SPACING['xl']};
            margin: {cls.SPACING['md']};
        }}
        
        /* ========================================
           Button Styles
           ======================================== */
        
        QPushButton {{
            background-color: {cls.COLORS['primary']};
            color: {cls.COLORS['text_on_primary']};
            border: none;
            border-radius: {cls.RADIUS['md']};
            padding: {cls.SPACING['sm']} {cls.SPACING['md']};
            font-weight: {cls.TYPOGRAPHY['weight_medium']};
            font-size: {cls.TYPOGRAPHY['size_sm']};
            min-height: 28px;
            text-align: center;
        }}
        
        QPushButton:hover {{
            background-color: {cls.COLORS['primary_hover']};
        }}
        
        QPushButton:pressed {{
            background-color: {cls.COLORS['primary_pressed']};
        }}
        
        QPushButton:disabled {{
            background-color: {cls.COLORS['outline']};
            color: {cls.COLORS['text_disabled']};
        }}
        
        /* Secondary Button Style */
        QPushButton.secondary {{
            background-color: {cls.COLORS['surface']};
            color: {cls.COLORS['primary']};
            border: 2px solid {cls.COLORS['primary']};
        }}
        
        QPushButton.secondary:hover {{
            background-color: {cls.COLORS['primary_light']};
            border-color: {cls.COLORS['primary_hover']};
        }}
        
        /* Danger Button Style */
        QPushButton.danger {{
            background-color: {cls.COLORS['error']};
        }}
        
        QPushButton.danger:hover {{
            background-color: #DC2626;
        }}
        
        /* Warning Button Style */
        QPushButton.warning {{
            background-color: {cls.COLORS['warning']};
        }}
        
        QPushButton.warning:hover {{
            background-color: #D97706;
        }}
        
        /* ========================================
           Progress Bar Styles
           ======================================== */
        
        QProgressBar {{
            background-color: {cls.COLORS['outline']};
            border: none;
            border-radius: {cls.RADIUS['sm']};
            height: 8px;
            text-align: center;
        }}
        
        QProgressBar::chunk {{
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 {cls.COLORS['primary']},
                stop:1 {cls.COLORS['secondary']}
            );
            border-radius: {cls.RADIUS['sm']};
        }}
        
        /* ========================================
           List Widget Styles
           ======================================== */
        
        QListWidget {{
            background-color: {cls.COLORS['surface']};
            border: 1px solid {cls.COLORS['outline']};
            border-radius: {cls.RADIUS['lg']};
            padding: {cls.SPACING['sm']};
            outline: none;
        }}
        
        QListWidget::item {{
            background-color: {cls.COLORS['surface_variant']};
            border: 1px solid {cls.COLORS['outline']};
            border-radius: {cls.RADIUS['md']};
            padding: {cls.SPACING['lg']};
            margin: {cls.SPACING['xs']} 0px;
            color: {cls.COLORS['text_primary']};
        }}
        
        QListWidget::item:selected {{
            background-color: {cls.COLORS['primary_light']};
            border-color: {cls.COLORS['primary']};
        }}
        
        QListWidget::item:hover {{
            background-color: {cls.COLORS['primary_surface']};
            border-color: {cls.COLORS['primary']};
        }}
        
        /* ========================================
           Label Styles
           ======================================== */
        
        QLabel {{
            color: {cls.COLORS['text_secondary']};
            font-size: {cls.TYPOGRAPHY['size_base']};
            font-weight: {cls.TYPOGRAPHY['weight_normal']};
        }}
        
        QLabel.title {{
            font-size: {cls.TYPOGRAPHY['size_3xl']};
            font-weight: {cls.TYPOGRAPHY['weight_bold']};
            color: {cls.COLORS['text_primary']};
            margin-bottom: {cls.SPACING['md']};
        }}
        
        QLabel.subtitle {{
            font-size: {cls.TYPOGRAPHY['size_lg']};
            font-weight: {cls.TYPOGRAPHY['weight_semibold']};
            color: {cls.COLORS['text_secondary']};
            margin-bottom: {cls.SPACING['sm']};
        }}
        
        QLabel.caption {{
            font-size: {cls.TYPOGRAPHY['size_sm']};
            color: {cls.COLORS['text_tertiary']};
        }}
        
        /* ========================================
           Line Edit Styles
           ======================================== */
        
        QLineEdit {{
            background-color: {cls.COLORS['surface']};
            border: 2px solid {cls.COLORS['outline']};
            border-radius: {cls.RADIUS['md']};
            padding: {cls.SPACING['md']} {cls.SPACING['lg']};
            font-size: {cls.TYPOGRAPHY['size_base']};
            color: {cls.COLORS['text_primary']};
            min-height: 20px;
        }}
        
        QLineEdit:focus {{
            border-color: {cls.COLORS['primary']};
            background-color: {cls.COLORS['surface']};
        }}
        
        QLineEdit:disabled {{
            background-color: {cls.COLORS['surface_variant']};
            color: {cls.COLORS['text_disabled']};
            border-color: {cls.COLORS['outline']};
        }}
        
        /* ========================================
           ComboBox Styles
           ======================================== */
        
        QComboBox {{
            background-color: {cls.COLORS['surface']};
            border: 2px solid {cls.COLORS['outline']};
            border-radius: {cls.RADIUS['md']};
            padding: {cls.SPACING['md']} {cls.SPACING['lg']};
            font-size: {cls.TYPOGRAPHY['size_base']};
            color: {cls.COLORS['text_primary']};
            min-height: 20px;
        }}
        
        QComboBox:hover {{
            border-color: {cls.COLORS['primary']};
        }}
        
        QComboBox::drop-down {{
            border: none;
            padding-right: {cls.SPACING['lg']};
        }}
        
        QComboBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid {cls.COLORS['text_secondary']};
            margin-right: {cls.SPACING['sm']};
        }}
        
        /* ========================================
           ScrollBar Styles
           ======================================== */
        
        QScrollBar:vertical {{
            background-color: {cls.COLORS['surface_variant']};
            width: 12px;
            border-radius: {cls.RADIUS['md']};
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {cls.COLORS['outline_variant']};
            border-radius: 6px;
            min-height: 30px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {cls.COLORS['text_tertiary']};
        }}
        
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {{
            border: none;
            background: none;
            height: 0px;
        }}
        
        /* ========================================
           Tab Widget Styles
           ======================================== */
        
        QTabWidget::pane {{
            background-color: {cls.COLORS['surface']};
            border: 1px solid {cls.COLORS['outline']};
            border-radius: {cls.RADIUS['lg']};
        }}
        
        QTabBar::tab {{
            background-color: {cls.COLORS['surface_variant']};
            color: {cls.COLORS['text_secondary']};
            padding: {cls.SPACING['md']} {cls.SPACING['xl']};
            margin-right: {cls.SPACING['xs']};
            border-top-left-radius: {cls.RADIUS['md']};
            border-top-right-radius: {cls.RADIUS['md']};
        }}
        
        QTabBar::tab:selected {{
            background-color: {cls.COLORS['surface']};
            color: {cls.COLORS['primary']};
            font-weight: {cls.TYPOGRAPHY['weight_semibold']};
        }}
        
        QTabBar::tab:hover {{
            background-color: {cls.COLORS['primary_light']};
        }}
        
        /* ========================================
           Menu Styles
           ======================================== */
        
        QMenuBar {{
            background-color: {cls.COLORS['surface']};
            border-bottom: 1px solid {cls.COLORS['outline']};
            padding: {cls.SPACING['xs']};
        }}
        
        QMenuBar::item {{
            padding: {cls.SPACING['sm']} {cls.SPACING['lg']};
            background-color: transparent;
            color: {cls.COLORS['text_primary']};
        }}
        
        QMenuBar::item:selected {{
            background-color: {cls.COLORS['primary_light']};
            border-radius: {cls.RADIUS['md']};
        }}
        
        QMenu {{
            background-color: {cls.COLORS['surface']};
            border: 1px solid {cls.COLORS['outline']};
            border-radius: {cls.RADIUS['md']};
            padding: {cls.SPACING['sm']};
        }}
        
        QMenu::item {{
            padding: {cls.SPACING['md']} {cls.SPACING['xl']};
            border-radius: {cls.RADIUS['sm']};
        }}
        
        QMenu::item:selected {{
            background-color: {cls.COLORS['primary_light']};
            color: {cls.COLORS['primary']};
        }}
        
        /* ========================================
           Status Bar Styles
           ======================================== */
        
        QStatusBar {{
            background-color: {cls.COLORS['surface']};
            border-top: 1px solid {cls.COLORS['outline']};
            color: {cls.COLORS['text_secondary']};
            font-size: {cls.TYPOGRAPHY['size_sm']};
            padding: {cls.SPACING['sm']};
        }}
        
        /* ========================================
           ToolTip Styles
           ======================================== */
        
        QToolTip {{
            background-color: {cls.COLORS['text_primary']};
            color: {cls.COLORS['text_on_primary']};
            border: none;
            border-radius: {cls.RADIUS['md']};
            padding: {cls.SPACING['sm']} {cls.SPACING['md']};
            font-size: {cls.TYPOGRAPHY['size_sm']};
        }}
        
        /* ========================================
           Frame Styles
           ======================================== */
        
        QFrame {{
            background-color: {cls.COLORS['surface']};
            border: 1px solid {cls.COLORS['outline']};
            border-radius: {cls.RADIUS['lg']};
        }}
        
        QFrame.card {{
            padding: {cls.SPACING['xl']};
            margin: {cls.SPACING['md']};
        }}
        
        /* ========================================
           Group Box Styles
           ======================================== */
        
        QGroupBox {{
            font-weight: {cls.TYPOGRAPHY['weight_semibold']};
            font-size: {cls.TYPOGRAPHY['size_base']};
            color: {cls.COLORS['text_secondary']};
            border: 2px solid {cls.COLORS['outline']};
            border-radius: {cls.RADIUS['lg']};
            padding-top: {cls.SPACING['xl']};
            margin-top: {cls.SPACING['md']};
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: {cls.SPACING['lg']};
            padding: 0 {cls.SPACING['sm']};
            background-color: {cls.COLORS['background']};
        }}
        """
    
    @classmethod
    def get_component_styles(cls):
        """Get additional component-specific styles"""
        return {
            'primary_button': f"""
                background-color: {cls.COLORS['primary']};
                color: {cls.COLORS['text_on_primary']};
                border: none;
                border-radius: {cls.RADIUS['md']};
                padding: {cls.SPACING['md']} {cls.SPACING['xl']};
                font-weight: {cls.TYPOGRAPHY['weight_semibold']};
                font-size: {cls.TYPOGRAPHY['size_base']};
                min-height: 40px;
            """,
            
            'secondary_button': f"""
                background-color: {cls.COLORS['surface']};
                color: {cls.COLORS['primary']};
                border: 2px solid {cls.COLORS['primary']};
                border-radius: {cls.RADIUS['md']};
                padding: {cls.SPACING['md']} {cls.SPACING['xl']};
                font-weight: {cls.TYPOGRAPHY['weight_semibold']};
                font-size: {cls.TYPOGRAPHY['size_base']};
                min-height: 40px;
            """,
            
            'danger_button': f"""
                background-color: {cls.COLORS['error']};
                color: {cls.COLORS['text_on_primary']};
                border: none;
                border-radius: {cls.RADIUS['md']};
                padding: {cls.SPACING['md']} {cls.SPACING['xl']};
                font-weight: {cls.TYPOGRAPHY['weight_semibold']};
                font-size: {cls.TYPOGRAPHY['size_base']};
                min-height: 40px;
            """,
            
            'card_container': f"""
                background-color: {cls.COLORS['surface']};
                border: 1px solid {cls.COLORS['outline']};
                border-radius: {cls.RADIUS['lg']};
                padding: {cls.SPACING['xl']};
                margin: {cls.SPACING['md']};
            """,
        }