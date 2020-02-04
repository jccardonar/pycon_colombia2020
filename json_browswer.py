from six import string_types
import numbers
from collections import abc
import ipywidgets as widgets

# auxiliary functiosn for the json browser.
def extract_values_from_json_object(data):
    """
    Checks the type of data and returns a set of list of keys (if any) or the string value.
    Only supports, dict and lists or collectors. 
    """
    if not isinstance(data, dict):
        return None

    values = {}
    for key, potential_value in data.items():
        if isinstance(potential_value, (string_types, numbers.Real)):
            values[key] = potential_value

    return values


def process_data(data):
    """
    Checks the type of data and returns a set of list of keys (if any) or the string value.
    Only supports, dict and lists or collectors.
    """
    if data is None:
        return (None, None, None)
    elif isinstance(data, dict):
        keys = list(data.keys())
        values = extract_values_from_json_object(data)
        return (list(keys), data, values)
    elif isinstance(data, string_types):
        return (None, str(data), None)
    elif isinstance(data, abc.Iterable):
        processed_data = {}
        for value_n, value in enumerate(data):
            key = "{}: '{}'".format(value_n, str(value)[0:40])
            processed_data[key] = value
        return (list(processed_data.keys()), processed_data, None)
    return (None, str(data), None)


def json_browser(input_data):
    """
    The JSON browser receives a hierarchical dictionary and
    allows an user to navigate it similarly to the columns view of files in Finder of Mac.
    The idea of the widget is let users navigate a json-type dict object,
    by going deeper in the hierarchies.
    For each selected level, the user can navigate further the elements.
    If the level has any element with a value, it shows them in its own box.
    """

    # Defining overall layout objects.
    height_selection_box = 300
    smal_box_height = height_selection_box * 0.94
    general_framework_layoud = widgets.Layout(
        overflow_x="scroll",
        # overflow_y='scroll',
        # border='3px solid black',
        # height='',
        flex_direction="row",
        display="flex",
        width="900px",
        height="{}px".format(height_selection_box),
    )

    small_box_layout = widgets.Layout(
        overflow_x=None,
        # overflow_y='scroll',
        # border='3px solid black',
        # height='',
        # flex_direction='row',
        # display='flex')
        width="300px",
        min_width="300px",
        min_height="{}px".format(smal_box_height),
        height="{}px".format(smal_box_height),
    )

    divided_box_layout = widgets.Layout(
        overflow_x=None,
        # overflow_y='scroll',
        # border='3px solid black',
        # height='',
        # flex_direction='row',
        # display='flex')
        width="300px",
        min_width="300px",
        height="{}px".format(int(smal_box_height * 0.49)),
    )

    # Let us define the main compound widget box.
    main_box = widgets.HBox(layout=general_framework_layoud)

    # each hierarchy is shown in a selection box. We need to keep track of the information that
    # each box stores. We define all that information here
    widget_to_data = {}
    keys, processed_data, these_values = process_data(input_data)
    select_to_parent = {}

    # I would normally use Select, but ipywidgets 6.0 uses a list instead of a box
    # this will be fix later, but the 7.0 had other problems when I tested it.
    select_widget = widgets.SelectMultiple(
        # description='',
        options=[None] + list(keys),  # ordered_keys,
        rows=10,
        # options=['Linux\ndf', 'Windows', "OSX"],
        # options=range(0, 100),
        layout=small_box_layout,
    )

    widget_to_data[select_widget] = processed_data
    main_box.children = (select_widget,)

    # We then define the update function of the selector, that we will
    # link to an observe callback pointed to the value trait of the select box.

    def handle_change(caller, names="value"):
        select_box_called = caller["owner"]

        # the "train" box is different from the select box only if there is content
        train_box = select_to_parent.get(select_box_called, select_box_called)
        # change this to value when not s selectmultiple
        # this_key = select_box_called.value
        if select_box_called.value:
            this_key = select_box_called.value[0]
        else:
            this_key = None

        if this_key is not None:
            # index = caller["new"]["index"]
            if select_box_called not in widget_to_data:
                raise Exception("Error. Could not identify the selection box.".format())
            select_box_data = widget_to_data[select_box_called]
            if this_key not in select_box_data:
                raise Exception(
                    "Error. Could not identify value {} in data for selection box.".format(
                        this_key
                    )
                )
            new_value = select_box_data[this_key]
        else:
            new_value = None

        keys, processed_data, these_values = process_data(new_value)

        if keys is None:
            if processed_data is None:
                # We are in the None line, 'eliminate' the rest of selected boxes
                main_box.children = main_box.children[
                    : main_box.children.index(train_box) + 1
                ]
            else:
                # we are in a value. Show it.
                new_select_box = widgets.Text(
                    value=processed_data, layout=small_box_layout, disabled=True
                )
                main_box.children = main_box.children[
                    : main_box.children.index(train_box) + 1
                ] + (new_select_box,)
        else:
            # We need a new selected box. and potentially a text
            if these_values is None or not these_values:
                # We do not need to show any values for this level.
                new_select_box = widgets.SelectMultiple(
                    # description='',
                    options=[None] + list(keys),  # ordered_keys,
                    rows=10,
                    # options=['Linux\ndf', 'Windows', "OSX"],
                    # options=range(0, 100),
                    layout=small_box_layout,
                )
                new_select_box.observe(handle_change, names="value")

                # the widget_to_data accumulates garbage with time. This is ok for a proto though.
                widget_to_data[new_select_box] = processed_data
                main_box.children = main_box.children[
                    : main_box.children.index(train_box) + 1
                ] + (new_select_box,)
            else:
                # we need to show values for this level.
                new_select_box = widgets.SelectMultiple(
                    # description='',
                    options=[None] + list(keys),  # ordered_keys,
                    rows=10,
                    # options=['Linux\ndf', 'Windows', "OSX"],
                    # options=range(0, 100),
                    layout=divided_box_layout,
                )
                value_content = "\n".join(
                    ["{}: {}".format(key, value) for key, value in these_values.items()]
                )

                new_values_box = widgets.Textarea(
                    value=value_content, layout=divided_box_layout, disabled=True
                )
                new_select_box.observe(handle_change, names="value")
                new_holding_box = widgets.VBox(
                    layout=small_box_layout, children=(new_values_box, new_select_box)
                )

                select_to_parent[new_select_box] = new_holding_box
                # the widget_to_data accumulates garbage with time. This is ok for a proto though.
                widget_to_data[new_select_box] = processed_data
                main_box.children = main_box.children[
                    : main_box.children.index(train_box) + 1
                ] + (new_holding_box,)

    select_widget.observe(handle_change, names="value")
    return main_box
