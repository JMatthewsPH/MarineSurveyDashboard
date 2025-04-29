"""
UI Helper Functions for Loading States and UI Elements

This module provides functions for creating loading states, skeleton UI,
and other visual indicators for improving user experience during data loading.
"""

import streamlit as st
import time
import plotly.graph_objects as go
import numpy as np

def loading_spinner(text="Loading data..."):
    """
    Display a loading spinner with custom text.
    
    Args:
        text: Text to display with the spinner
    
    Returns:
        Streamlit spinner context manager
    """
    return st.spinner(text)

def skeleton_chart(height=400, chart_type="line"):
    """
    Create a skeleton placeholder chart while the real data is loading.
    
    Args:
        height: Height of the chart in pixels
        chart_type: Type of chart to create skeleton for (line, bar)
        
    Returns:
        Plotly figure object with skeleton chart
    """
    # Create a light gray background figure
    fig = go.Figure()
    
    # Adding placeholder data based on chart type
    if chart_type == "line":
        # Create a subtle wavy line for line charts
        x = np.linspace(0, 10, 50)
        y = np.sin(x) * 0.1 + 0.5  # Very subtle wave
        
        fig.add_trace(go.Scatter(
            x=x, 
            y=y,
            mode='lines',
            line=dict(color='#E0E0E0', width=2),
            hoverinfo='none'
        ))
        
    elif chart_type == "bar":
        # Create subtle placeholder bars
        x = list(range(1, 6))
        y = [0.3, 0.5, 0.4, 0.6, 0.35]  # Random heights
        
        fig.add_trace(go.Bar(
            x=x,
            y=y,
            marker_color='#E0E0E0',
            hoverinfo='none'
        ))
    
    # Style the skeleton chart
    fig.update_layout(
        height=height,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            showgrid=False,
            showticklabels=False,
            zeroline=False
        ),
        yaxis=dict(
            showgrid=False,
            showticklabels=False,
            zeroline=False
        ),
        margin=dict(l=20, r=20, t=30, b=20),
        showlegend=False
    )
    
    # Add a subtle loading message
    fig.add_annotation(
        text="Loading data...",
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=16, color="#BDBDBD")
    )
    
    return fig

def create_loading_placeholder(container, message="Loading data...", height=400):
    """
    Create a loading placeholder in a given container.
    
    Args:
        container: Streamlit container to add the placeholder to
        message: Message to display during loading
        height: Height of the placeholder
        
    Returns:
        The placeholder object
    """
    placeholder = container.empty()
    with placeholder.container():
        st.markdown(f"<div style='height: {height}px; display: flex; align-items: center; justify-content: center;'>"
                   f"<div style='text-align: center;'>"
                   f"<div class='loader'></div>"
                   f"<p style='color: #BDBDBD; margin-top: 15px;'>{message}</p>"
                   f"</div></div>", unsafe_allow_html=True)
    return placeholder

def add_loading_css():
    """Add CSS for loading animations"""
    return """
    <style>
    .loader {
        border: 8px solid #f3f3f3;
        border-top: 8px solid #3498db;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        animation: spin 1s linear infinite;
        margin: 0 auto;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .skeleton-text {
        height: 1.2em;
        background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
        background-size: 200% 100%;
        animation: loading 1.5s infinite;
        border-radius: 4px;
        margin-bottom: 8px;
        width: 100%;
    }
    
    .skeleton-text.short {
        width: 60%;
    }
    
    @keyframes loading {
        0% {
            background-position: 200% 0;
        }
        100% {
            background-position: -200% 0;
        }
    }
    </style>
    """

def skeleton_text_placeholder(lines=3, container=None):
    """
    Create skeleton text placeholders while content is loading
    
    Args:
        lines: Number of lines to create
        container: Optional container to place the skeleton in
    """
    target = container if container else st
    
    skeleton_html = "<div>"
    for i in range(lines):
        # Make some lines shorter for a more natural look
        class_name = "skeleton-text short" if i % 3 == 1 else "skeleton-text"
        skeleton_html += f'<div class="{class_name}"></div>'
    skeleton_html += "</div>"
    
    target.markdown(skeleton_html, unsafe_allow_html=True)