def plot_conf_mat(clf, X_test, y_test, N = 5):
    """ 
    to get the confusion matrix for multiclass classifier 
    """ 
    import seaborn as sn
    import matplotlib.pyplot as plt
    import pandas as pd
    import numpy as np
    from sklearn.metrics import confusion_matrix
    
    y_pred = clf.predict(X_test)
    cm = confusion_matrix(y_test, y_pred)
    labels = clf.classes_
    df_cm = pd.DataFrame(cm, index = [i for i in labels],
                      columns = [i for i in labels])
    plt.figure(figsize = (10,7))
    sn.heatmap(df_cm, annot=False);
    
    # find the top-N mistakes
    cm_copy = cm.copy()
    np.fill_diagonal(cm_copy, -1)
    for i in range(N):
        max_idx = cm_copy.argmax()
        max_idx = np.unravel_index(max_idx, cm_copy.shape)
        # set that value to -1
        cm_copy[max_idx] = -1
        print('Top {} mistake: truth is {}, but predicting {}'.format(i+1,
        df_cm.index[max_idx[0]],
        df_cm.columns[max_idx[1]]))

def plot_conf_mat_bokeh(clf, X_test, y_test, html_file = ''):
    """ 
    to get the confusion matrix for multiclass classifier 
    but with bokeh
    """ 
    import pandas as pd
    import numpy as np
    import bokeh.plotting as bkp
    from bokeh.palettes import inferno
    from bokeh.models import (
        ColumnDataSource,
        HoverTool,
        LinearColorMapper,
        LogColorMapper,
        BasicTicker,
        PrintfTickFormatter,
        ColorBar,
    )
    
    y_pred = clf.predict(X_test)
    cm = confusion_matrix(y_test, y_pred)
    labels = clf.classes_
    df_cm = pd.DataFrame(cm, index = [i for i in labels],
                      columns = [i for i in labels])
    df_cm.index.name = 'Truth'
    df_cm.columns.name = 'Prediction'
    # reshape to 1D array or values with a truth and prediction for each row.
    df = pd.DataFrame(df_cm.stack(), columns=['value']).reset_index()
    truths = list(df_cm.index)
    predictions = list(df_cm.columns)
    colors = inferno(256)
    mapper = LogColorMapper(palette=colors, low=df['value'].min(), high=df['value'].max())
    source = ColumnDataSource(df)
    TOOLS = "hover,save,pan,box_zoom,reset,wheel_zoom"
    p = bkp.figure(title="Confusion matrix",
               x_axis_label = 'Prediction', y_axis_label = 'Truth',
               x_range=predictions, y_range=list(reversed(truths)),
               x_axis_location="below", plot_width=800, plot_height=800,
               tools=TOOLS, toolbar_location='above')
    p.grid.grid_line_color = None
    p.axis.axis_line_color = None
    p.axis.major_tick_line_color = None
    p.axis.major_label_text_font_size = "8pt"
    p.axis.major_label_standoff = 0
    p.xaxis.major_label_orientation = np.pi / 3
    p.rect(x='Prediction', y='Truth', width=1, height=1,
           source=source,
           fill_color={'field': 'value', 'transform': mapper},
           line_color=None)
    color_bar = ColorBar(color_mapper=mapper, major_label_text_font_size="8pt",
                         #ticker=BasicTicker(desired_num_ticks=len(colors)),
                         label_standoff=6, border_line_color=None, location=(0, 0))
    p.add_layout(color_bar, 'right')
    p.select_one(HoverTool).tooltips = [
         ('Truth', '@Truth'),
         ('Predition', '@Prediction'),
         ('Counts', '@value')
    ]
    bkp.output_notebook()
    if len(html_file) > 0:
        bkp.output_file(html_file)
    bkp.show(p)
        

def get_proba(clf, X_scaled, y_true = 'Not provided', N = 5): 
    """ 
    to get top-N predictions for multiclass classifier 
    given a scaled input
    """
    labels = clf.classes_
    y_pred = clf.predict_proba(X_scaled.reshape(1,-1))
    tmp = [(name, proba) for name, proba in zip(labels, y_pred[0])]
    tmp = sorted(tmp, key = lambda x: x[1], reverse = True)
    print('Truth is {}'.format(y_true))
    print('Predictions are:')
    for i in range(5):
        print(tmp[i])