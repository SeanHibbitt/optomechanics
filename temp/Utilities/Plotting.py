def update_plotly_layout(fig, xaxis_title, yaxis_title, xaxis_range=None, yaxis_range=None, title_name=None, tick_format = ('n', '.2f')):
    """
    Update the layout of a Plotly figure with custom x-axis and y-axis settings.
    
    Parameters:
    - fig: Plotly figure object to update.
    - xaxis_title: Title for the x-axis.
    - yaxis_title: Title for the y-axis.
    - xaxis_range: Optional, range for the x-axis as [min, max]. Default is None.
    - yaxis_range: Optional, range for the y-axis as [min, max]. Default is None.
    """
    fig.update_layout(
        yaxis_title=yaxis_title,
        xaxis_title=xaxis_title,
        template='plotly_white',
        title=title_name,
        xaxis=dict(
            tickformat=tick_format[1],  # Format numbers to 2 decimal places
            ticksuffix='',     # Remove suffix like 'B' for billions
            showgrid=True,     # Show grid lines for better visibility
            tickfont=dict(
                family='Arial',  # Font family
                size=14,         # Font size
                color='black'    # Font color
            ),
            range=xaxis_range   # Set the x-axis range if provided
        ),
        yaxis=dict(
            tickformat=tick_format[0],  # Format numbers to 2 decimal places
            ticksuffix='',     # Remove suffix like 'B' for billions
            showgrid=True,     # Show grid lines for better visibility
            tickfont=dict(
                family='Arial',  # Font family
                size=14,         # Font size
                color='black'    # Font color
            ),
            range=yaxis_range   # Set the y-axis range if provided
        )
    )

