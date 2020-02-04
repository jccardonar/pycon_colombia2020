import ipywidgets as widgets
import matplotlib.pyplot as plt
from functools import reduce

def hover(hover_color="#F0F0F0"):
    '''
    Hover function, I got them directly from the pandas style documentation page.
    It lets you highlight in a table the row where the mouse is located.
    '''
    return dict(selector="tr:hover",
                    props=[("background-color", "%s" % hover_color)])

def process_df_for_widget(df_traffic, aggregation_columns=None, 
                          time_column="TIME", value_column="BW", 
                          top_flows_to_show=5):
    '''
    Adjusts a TS data frame to be depicted in a time series widget.
    
    
    The data frame must contain a time column, and a value column. Only one value column is permitted.
    The rest of the columns are characteristics of the time series.
    One can filter the aggregation columns, by default it uses all of them.
    
    Using the aggregation columns, the code calculates the top contributiors of the data frame.
    It then creates and returns two data frames: graph_df and table_df,
    which are suitable to be depicted in a graph and a table in the widget.
    '''
    
    # Although Pandas defaults into non making any inline operation, 
    # let us not risk it and work with a copy of the df.
    df_traffic = df_traffic.copy()

    # Get the list of aggregation columns. It defaults to any non-time, non-value column in the df.
    if aggregation_columns is None:
        aggregation_columns = list(set(df_traffic.columns) - {time_column, value_column})
        aggregation_columns = sorted(aggregation_columns)
    else:
        aggregation_columns = list(aggregation_columns)

    # Find top flows, if columns are aggregated, if not, then we only mantain the total value in time.
    if aggregation_columns:
        top_flows = df_traffic.groupby(by=aggregation_columns).sum().reset_index().sort_values(value_column, ascending=False)
        top_flows = top_flows.head(top_flows_to_show)

        # filter all non top flows, and summarize them as "Others".
        filtered_df = df_traffic.merge(top_flows.rename(columns={value_column:"NULL_CHECK"}), on=tuple(set(aggregation_columns)), how="left")
        filtered_df.loc[filtered_df.NULL_CHECK.isnull(), aggregation_columns] = "Others"
        filtered_df = filtered_df.groupby(list(set(aggregation_columns) | {time_column})).sum()[value_column].reset_index()

        aggregation_column_name = '-'.join([str(column) for column in aggregation_columns])
        aggregation_column = reduce(lambda x,y: x + '-' + y, [filtered_df[column].astype(str) for column in aggregation_columns])

        filtered_df[aggregation_column_name] = aggregation_column
    else:
        filtered_df = df_traffic.groupby(time_column)[value_column].sum().reset_index()
        aggregation_column_name = "TOTAL"
        filtered_df["TOTAL"] = aggregation_column_name
    
    # Create graph and table dfs.
    # The table df does not contain any TIME information, it shows the sum in time over the remaining flows.
    table_df = filtered_df.groupby(list(set(aggregation_columns) | {aggregation_column_name})).mean()[value_column].sort_values(ascending=False)
    graph_df = filtered_df
    
    graph_df = graph_df[[aggregation_column_name, time_column, value_column]]
    graph_df = graph_df.set_index([aggregation_column_name, time_column]).unstack(aggregation_column_name)
    graph_df.columns = graph_df.columns.get_level_values(1)
    graph_df = graph_df[list(table_df.reset_index()[aggregation_column_name])]
    
    # remove the aggregation column in the table if there are more than one selected column
    if len(aggregation_columns) > 1:
        table_df = table_df.reset_index().drop(aggregation_column_name, axis=1)
    else:
        table_df = table_df.reset_index()

    return table_df, graph_df

def ts_widget(
    df_traffic,
    aggregation_columns=None,
    time_column="TIME",
    value_column="BW",
    top_flows_to_show=5,
    align_vertically=True,
):
    """
    Returns a Box widget containing various widgets used to depict and explore a time series data frame.
    the widget contains:
    - A HTML and a figure widget used to depict the data of the aggregated data frame.
    - A set of check boxes to allow users to select the characteristics shown that are depicted in the figure and table.
    - An update button used to refresh the table and graph widgets when the user changes the checkboxes.
    - A Text box which contains information on the state of the widget (E.g. Processing, Updated, etc.)
    
    The graph and the table are placed horizontally if the align_vertically is False. If selected, a horizontal 
    widget is more compact, but cannot show that much information.
    
    The update function of the update button is a nested function and uses non-local variables.
    """

    # Get the list of aggregation columns. It defaults to any non-time, non-value column in the df.
    if aggregation_columns is None:
        aggregation_columns = list(
            set(df_traffic.columns) - {time_column, value_column}
        )
        aggregation_columns = sorted(aggregation_columns)
    else:
        aggregation_columns = list(aggregation_columns)

    # Defines the layout objects that we will use depending on the widget layout (horizontal or vertical).
    # The values here defined were obtained with trial and error :)

    # The only fancy thing here is the use of a variable traffic_traph_box_widget to define whether the
    # graph and table box is vertical or horizontal
    if align_vertically:
        all_widget_height = "1050px"
        all_widget_width = "1000px"

        table_height = "400px"
        table_width = all_widget_width

        graph_table_height = "950px"

        traffic_traph_box_widget = widgets.VBox
        figure_size = [9.1, 4.8]
    else:
        all_widget_height = "700px"
        all_widget_width = "1000px"

        graph_table_height = "650px"

        table_height = "600px"
        table_width = "500px"

        traffic_traph_box_widget = widgets.HBox
        figure_size = [4.8, 4.8]

    # define the main widget.
    ts_main_widget = widgets.VBox(
        layout=widgets.Layout(height=all_widget_height, width=all_widget_width)
    )

    # the main widget is formed by a control box and the graph_table_box.
    # The control box which contains the check boxes, update butoon and information box.
    # the graph_and table box is self-described.
    control_information_box = widgets.VBox()
    graph_table_box = traffic_traph_box_widget(
        layout=widgets.Layout(height=graph_table_height, width=all_widget_width)
    )
    ts_main_widget.children = (control_information_box, graph_table_box)

    # Control box
    # the control box is itself formed by:
    # * another box holding the checkboxes
    # * the update button
    # * The information text
    # The first two elements are horitzontally alligned using a box called cbx_update_box

    cbx_update_box = widgets.HBox()
    information_widget = widgets.Text(disabled=True, description="State:")
    control_information_box.children = (cbx_update_box, information_widget)

    # the cbx is itself divided into the check_box box and the update button.
    # I place the check boxes into their own box to let them have a box space.

    check_boxes = {}
    check_boxes_box = widgets.HBox(
        layout=widgets.Layout(overflow_x="scroll", height="50px", width="850px")
    )
    for level in aggregation_columns:
        # Create check boxes for each TS characteristic column.
        this_checkbox = widgets.Checkbox(description=level)
        check_boxes_box.children = check_boxes_box.children + (this_checkbox,)
        this_checkbox.value = False
        check_boxes[level] = this_checkbox

    # Update button
    refresh_button = widgets.Button(description="Update")
    cbx_update_box.children = (check_boxes_box, refresh_button)

    # Now, let us finish with the graph and table box.
    fig_prefix_distribution, ax_prefix_distribution = plt.subplots()
    this_canvas = fig_prefix_distribution.canvas
    # this_canvas = Canvas(fig_prefix_distribution)

    fig_prefix_distribution.set_size_inches(figure_size)
    this_canvas.figure.set_label("{}".format("Figure"))

    table_box_layout = widgets.Layout(
        overflow_x="scroll",
        overflow_y="scroll",
        # border='3px solid black',
        width=table_width,
        height=table_height,
        flex_direction="row",
        display="flex",
    )

    table_widget = widgets.HTML()
    table_box_widget = widgets.VBox(children=(table_widget,), layout=table_box_layout)

    graph_table_box.children = (this_canvas, table_box_widget)

    # Finally, define the update function and assign it to the butotn
    def update_compound_widget(caller=None):
        """
        The update function checks the aggrupation characteristics, calculates the resulting df,
        and updates the table and graph.
        """

        information_widget.value = "Updating..."
        # find the aggregation level using the check boxes
        aggregation_level = []

        for level in check_boxes:
            check_box = check_boxes[level]

            if check_box.value:
                aggregation_level.append(level)

        table_df, graph_df = process_df_for_widget(
            df_traffic,
            aggregation_columns=aggregation_level,
            value_column=value_column,
            time_column=time_column,
            top_flows_to_show=top_flows_to_show,
        )
        ax_prefix_distribution.clear()
        aggregation_column_name = next(
            iter(set(graph_df.columns) - {time_column, value_column})
        )

        graph_df.plot.area(ax=ax_prefix_distribution)

        ax_prefix_distribution.legend_.remove()
        ax_prefix_distribution.legend(
            bbox_to_anchor=(0.1, 0.85, 0.9, 0.105),
            loc=3,
            ncol=2,
            mode=None,
            borderaxespad=0.1,
            fontsize=8,
        )
        ax_prefix_distribution.set_ylabel(value_column)
        table_widget.value = (
            table_df.style.set_table_attributes('class="table"')
            .set_table_styles([hover()])
            .render()
        )

        information_widget.value = "Redrawing..."
        plt.draw_all()
        information_widget.value = "Done"

    refresh_button.on_click(update_compound_widget)
    return ts_main_widget
