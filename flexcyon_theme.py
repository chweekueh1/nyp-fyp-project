import gradio as gr
from gradio.themes import Base

class FlexcyonTheme(Base):
    def __init__(self):
        super().__init__(
            primary_hue="green",
            secondary_hue="purple",
            neutral_hue="gray"
        )
        self.set(
            body_background_fill="#1A1A1A",  # base-01
            block_background_fill="#2D2D2D",  # base-02
            button_primary_background_fill="#4CAF50",  # green accent
            button_primary_text_color="#FFFFFF",
            button_secondary_background_fill="#9c27b0",  # purple accent
            button_secondary_text_color="#FFFFFF",
            border_color_primary="#3D3D3D"
            # Add more variables as needed and supported
        )

flexcyon_theme = FlexcyonTheme() 