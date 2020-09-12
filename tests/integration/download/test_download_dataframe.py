import os
import time
import dash
import dash_core_components as dcc
import dash_core_components.express as dcx
import dash_html_components as html
import pytest
import pandas as pd
import numpy as np

from dash.dependencies import Input, Output


@pytest.mark.parametrize("fmt", ("csv", "json", "html", "feather", "parquet", "stata", "pickle"))
def test_download_dataframe(fmt, dash_dcc):
    df = pd.DataFrame({'a': [1, 2, 3, 4], 'b': [2, 1, 5, 6], 'c': ['x', 'x', 'y', 'y']})
    reader = getattr(pd, "read_{}".format(fmt))  # e.g. read_csv
    writer = getattr(df, "to_{}".format(fmt))  # e.g. to_csv
    filename = "df.{}".format(fmt)
    # Create app.
    app = dash.Dash(__name__)
    app.layout = html.Div(
        [
            html.Button("Click me", id="btn"),
            dcc.Download(id="download"),
        ]
    )

    @app.callback(Output("download", "data"), [Input("btn", "n_clicks")])
    def download(n_clicks):
        # For csv and html, the index must be removed to preserve the structure.
        if fmt in ["csv", "html", "excel"]:
            return dcx.send_data_frame(writer, filename, index=False)
        # For csv and html, the index must be removed to preserve the structure.
        if fmt in ["stata"]:
            a = dcx.send_data_frame(writer, filename, write_index=False)
            return a
        # For other formats, no modifications are needed.
        return dcx.send_data_frame(writer, filename)

    # Check that there is nothing before starting the app
    fp = os.path.join(dash_dcc.download_path, filename)
    assert not os.path.isfile(fp)
    # Run the app.
    dash_dcc.start_server(app)
    time.sleep(0.5)
    # Check that a file has been download, and that it's content matches the original data frame.
    df_download = reader(fp)
    if isinstance(df_download, list):
        df_download = df_download[0]
    # For stata data, pandas equals fails. Hence, a custom equals is used instead.
    assert df.columns.equals(df_download.columns)
    assert df.index.equals(df_download.index)
    np.testing.assert_array_equal(df.values, df_download.values)