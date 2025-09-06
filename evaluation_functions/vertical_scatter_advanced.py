"""
Vertical Scatter Plots for visualize distributions across categories.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

class MissingCategoryColumnError(Exception):
    """
    Custom Exception raised if no category label is present in Pandas Dataframe
    """
    pass


def vertical_scatter(
        df: pd.DataFrame,
        col: str,
        spread: float = 0.8,
        advanced_parameters: dict = None,
        general_settings: dict = None,
        sorting_function: callable = None
    )-> tuple[plt.Figure, plt.Axes]:
    """
    Generates a vertical scatter plot for the specified column in the DataFrame,
    grouped by categories.

    Args:
        df:
            Pandas DataFrame containing the data to plot.
            Must contain a 'category' column for grouping.
        col:
            The name of the column to plot on the y-axis.
        spread:
            The horizontal spread of the points in the scatter plot.
            Default is 0.8.
        advanced_parameters:
            Optional dictionary with advanced parameters for the plot.
            Can include:
                - 'valid_values_min': Minimum valid value for the y-axis.
                    - default is -np.inf.
                    - restricts which values will be plotted and
                      included in calculation of mean and std
                    - values outside still will be include for ratio calculation 
                - 'valid_values_max': Maximum valid value for the y-axis.
                    - default is np.inf.
                    - restricts which values will be plotted and
                      included in calculation of mean and std
                    - values outside still will be include for ratio calculation
                - 'plot_min': Minimum value for the y-axis.
                    - If not provided, it will be calculated to fit the data.
                - 'plot_max': Maximum value for the y-axis.
                    - If not provided, it will be calculated to fit the data.
                - 'markers': List of markers to display on the plot.
                    - Each marker has to contain 'y_pos' and can contain 'style'
                      'color', 'alpha' and 'thickness'.
                - 'display_ratios': List of display ratios to show on the plot.
                    - Each display ratio has to contain: 'title', 'n_min', 
                      'n_max', 'p_min', 'p_max'.
                    - 'i_min' defaults to -np.inf, 'i_max' defaults to np.inf
                    - the displayed ratio is calculated as:
                        n / (p + 10**-5) * 100, where n is the number of
                        values in the n-zone and p is the number of
                        values in the p-zone.
                - 'unit': Unit of the y-axis, displayed in the y-axis label.
                    - If not provided, no unit will be displayed.
                - 'y_mult': Multiplicative factor for the y-axis values.
                    - If not provided, no multiplicative factor will be applied.
        sorting_function:
            Optional function to sort the categories.
            If provided, it should take a category as input and return a value
            to sort by. If missing, categories will be sorted alphabetically.
    Returns:
        fig, ax, meta_data:
            The figure and axes objects of the created plot and a DataFrame
            containing metadata about the data displayed in the plot.
    Raises:
        MissingCategoryColumnError:
            If the DataFrame does not contain a 'category' column.    
    """
    print(f'Creating vertical scatter plot for {col}')

    if 'category' not in df.keys():
        raise MissingCategoryColumnError(
            'Provided Dataframe is missing' \
            ' Column with Category labels ("category")')    

    categories = list(set(df['category']))
    if sorting_function:
        categories.sort(key=sorting_function)
    else:
        categories.sort()

    valid_values_max = np.inf
    valid_values_min = -np.inf

    zones = []
    markers = []
    unit = None

    set_title = False
    text_size = 10
    fig_size = [3, 3]
    dot_size = 16
    y_mult = 1
    y_scale = 'linear'

    if general_settings:
        if 'font_size' in general_settings:
            text_size = general_settings['font_size']
        if 'fig_size' in general_settings:
            fig_size = general_settings['fig_size']
        if 'marker_size' in general_settings:
            dot_size = general_settings['marker_size']

    if advanced_parameters:
        if 'valid_values_min' in advanced_parameters:
            valid_values_min = advanced_parameters['valid_values_min']
            if isinstance(valid_values_min, str):
                if valid_values_min == 'inf':
                    valid_values_min = -np.inf

        if 'valid_values_max' in advanced_parameters:
            valid_values_max = advanced_parameters['valid_values_max']
            if isinstance(valid_values_max, str):
                if valid_values_max == 'inf':
                    valid_values_max = np.inf

        plot_max = None
        plot_min = None
        if 'plot_min' in advanced_parameters:
            plot_min = advanced_parameters['plot_min']
        if 'plot_max' in advanced_parameters:
            plot_max = advanced_parameters['plot_max']

        recalculate_min = False
        recalculate_max = False

        data = df[df[col] <= valid_values_max]
        data = data[data[col] >= valid_values_min]

        if plot_min is None:
            plot_min = data[col].min()
            #check if plot_min is NaN or Inf 
            if pd.isna(plot_min):
                plot_min = -1
            if np.isinf(plot_min):
                plot_min = -1e10
            recalculate_min = True
        if plot_max is None:
            plot_max = data[col].max()
            if pd.isna(plot_max):
                plot_max = 1
            if np.isinf(plot_max):
                plot_max = 1e10
            recalculate_max = True

        value_range = plot_max - plot_min
        if recalculate_min:
            plot_min = plot_min - 0.15 * value_range
        if recalculate_max:
            plot_max = plot_max + 0.15 * value_range

        if plot_max == plot_min:
            plot_max += 1
            plot_min -= 1
            value_range = 2

        if 'markers' in advanced_parameters:
            markers = advanced_parameters['markers']
            for m in markers:
                if 'y_pos' not in m:
                    raise ValueError(
                        'Each marker must have a "y_pos" key.')
                if m['y_pos'] < plot_min:
                    plot_min = m['y_pos']
                    recalculate_min = True
                if m['y_pos'] > plot_max:
                    plot_max = m['y_pos']
                    recalculate_max = True
        value_range = plot_max - plot_min
        if recalculate_min:
            plot_min = plot_min - 0.15 * value_range
        if recalculate_max:
            plot_max = plot_max + 0.15 * value_range               

        if 'y_mult' in advanced_parameters:
            y_mult = advanced_parameters['y_mult']

        if 'display_ratios' in advanced_parameters:
            display_ratios = advanced_parameters['display_ratios']

            for dr in display_ratios:
                if 'title' not in dr:
                    raise ValueError(
                        'Each display ratio must have a "title" key.')
                if 'n_min' not in dr:
                    raise ValueError(
                        'Each display ratio must have a "n_min" key.')
                if 'n_max' not in dr:
                    raise ValueError(
                        'Each display ratio must have a "n_max" key.')
                if 'p_min' not in dr:
                    raise ValueError(
                        'Each display ratio must have a "p_min" key.')
                if 'p_max' not in dr:
                    raise ValueError(
                        'Each display ratio must have a "p_max" key.')

                if 'only_table' in dr:
                    only_table = dr['only_table']
                else:
                    only_table = False

                n_min = dr['n_min']
                n_max = dr['n_max']
                p_min = dr['p_min']
                p_max = dr['p_max']

                if isinstance(n_min, str):
                    if n_min == 'inf':
                        n_min = -np.inf
                if isinstance(n_max, str):
                    if n_max == 'inf':
                        n_max = np.inf
                if isinstance(p_max, str):
                    if p_max == 'inf':
                        p_max = np.inf
                if isinstance(p_min, str):
                    if p_min == 'inf':
                        p_min = -np.inf


                if n_min > n_max:
                    raise ValueError(
                        'Negative zone minimum cannot be greater than maximum.')
                if p_min > p_max:
                    raise ValueError(
                        'Positive zone minimum cannot be greater than maximum.')

                zone = []
                if not only_table:
                    plot_max += 0.05 * value_range

                for category in categories:
                    dfc = df[df['category'] == category]
                    ndf = dfc[
                        (dfc[col] >= n_min) & (dfc[col] <= n_max)
                    ]
                    pdf = dfc[
                        (dfc[col] >= p_min) & (dfc[col] <= p_max)
                    ]

                    percentage = ndf.shape[0]  / (pdf.shape[0] + 10**-5) * 100            

                    zone.append({
                        'text': f'{dr['title']}:\n {percentage:.1f}%',
                        'y_pos': plot_max,
                        'only_table': only_table,
                        'table_head': dr['title'],
                        'value': f'{percentage:.2f}'
                    })
                zones.append(zone)

                if not only_table:
                    plot_max += 0.1 * value_range


        if 'markers' in advanced_parameters:
            markers = advanced_parameters['markers']
            for m in markers:
                if 'y_pos' not in m:
                    raise ValueError(
                        'Each marker must have a "y_pos" key.')
                

        if 'unit' in advanced_parameters:
            unit = advanced_parameters['unit']

        if 'set_title' in advanced_parameters:
            set_title = advanced_parameters['set_title']

        if 'y-scale' in advanced_parameters:
            y_scale = advanced_parameters['y-scale']
            



    else:
        plot_min = df[col].min()
        plot_max = df[col].max()
        value_range = plot_max - plot_min
        plot_min = plot_min - 0.1 * value_range
        plot_max = plot_max + 0.1 * value_range
        if plot_max == plot_min:
            plot_max += 1
            plot_min -= 1
            value_range = 2

    if y_mult != 1:
        print(f'Using y_mult: {y_mult} for {col}')

    fig, ax = plt.subplots()
    fig.set_size_inches(*fig_size)

    ax.set_ylim(plot_min * y_mult, plot_max * y_mult)

    point_spread = 0.9 * spread

    x_min = -1 +  spread / 2
    x_max = len(categories) - spread / 2

    if markers:
        for m in markers:
            line = ax.plot([x_min + 0.1 , x_max - 0.1],
                    [m['y_pos'] * y_mult, m['y_pos'] * y_mult],
                    color='black',
                    linewidth=0.5,
                    linestyle='--'
            )
            if 'style' in m:
                line[0].set_linestyle(m['style'])
            if 'color' in m:
                line[0].set_color(m['color'])
            if 'alpha' in m:
                line[0].set_alpha(m['alpha'])
            if 'thickness' in m:
                line[0].set_linewidth(m['thickness'])
            if 'text' in m:
                x_min -= (x_max - x_min) / 4 
                txt = ax.text(x_min + 0.1 , m['y_pos'] * y_mult, m['text'],
                        ha='left',
                        va='center',
                        fontsize=text_size,
                        bbox=dict(facecolor='white', alpha=1, edgecolor='none')
                        )
                if 'color' in m:
                    txt.set_color(m['color'])
                if 'alpha' in m:
                    txt.set_alpha(m['alpha'])

    meta_data = pd.DataFrame({'category':[], 'mean':[], 'std':[], 'min':[], 'max':[], 'n':[]})

    for i, c in enumerate(categories):
        data = df[df['category'] == c]
        data = data[data[col] <= valid_values_max]
        data = data[data[col] >= valid_values_min]

        data[col] *= y_mult

        n = data.shape[0]
        mid_point = np.ones(n) * i
        distribution = np.linspace(0,  point_spread, n) - point_spread / 2
        x =  mid_point +  distribution

        # Scatter plot the data points and get path for color
        pth = ax.scatter(x, data[col], label = c, alpha=0.7, s=dot_size)

        # Create line for mean and fill between std
        mean_value = data[col].mean()
        std = data[col].std()

        ax.plot([i - spread / 2, i + spread / 2],
                [mean_value, mean_value],
                color=pth.get_facecolor()[0],
                linewidth=1.5)
        ax.fill_between([i - spread / 2, i + spread / 2],
                        mean_value - std,
                        mean_value + std,
                        color=pth.get_facecolor()[0],
                        alpha=0.3)
        
        row = pd.DataFrame(
            {
                'category': c,
                'mean': mean_value,
                'std': std,
                'min': data[col].min() * y_mult,
                'max': data[col].max() * y_mult,
                'n': n
            },
            index=[0]
            )

        if zones:
            print(f"Zones: {len(zones)}")
            for zone in zones:
                print(len(zone))
                z = zone[i]
                row[z['table_head']] = z['value']
                if 'only_table' in z:
                    if not z['only_table']:
                        ax.text(i, z['y_pos'] * y_mult, z['text'],
                                ha='center',
                                va='center',
                                fontsize=text_size
                                )

      
        meta_data = pd.concat([meta_data, row], ignore_index=True)


    ax.set_xticks(range(len(set(df['category']))))
    ax.set_xticklabels(categories, rotation=45, ha='right', fontsize=text_size)
    if set_title:
        ax.set_title(col, fontsize=text_size)
    if unit:
        ax.set_ylabel(unit, fontsize=text_size)

    #ax.yaxis.set_scale(y_scale) # WIP: ToDo what about log with values <= 0?

    ax.set_xlim(x_min, x_max)

    fig.tight_layout()


    return fig, ax, meta_data


