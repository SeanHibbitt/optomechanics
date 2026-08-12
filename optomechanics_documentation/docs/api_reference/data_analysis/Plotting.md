# Plotting

Helper utilities for creating and styling Plotly figures.

## Examples

```python
import plotly.graph_objects as go
from optomechanics.data_analysis.Plotting import lighten_color, update_plotly_layout

fig = go.Figure()
fig.add_trace(go.Scatter(x=frequencies, y=amplitudes, name="S21"))

# Adjust axis labels, font size, and tick format
# tick_format is (yaxis_format, xaxis_format)
update_plotly_layout(
    fig,
    x_label="Frequency (Hz)",
    y_label="Amplitude (dB)",
    font_size=14,
    tick_format=(".1f", ".3e"),
)

# Lighten a colour for shading a confidence interval
light_blue = lighten_color("steelblue", amount=0.4)
```

::: optomechanics.data_analysis.Plotting
