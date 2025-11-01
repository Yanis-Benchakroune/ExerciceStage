import pandas as pd
import dash
from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
import plotly.express as px

df = pd.read_csv("data/eCO2mix_RTE_En-cours-Consolide.csv", sep="\t", encoding="latin-1", index_col=False).iloc[:-1]
df["Datetime"] = pd.to_datetime(df.Date + " " + df.Heures)
df.sort_values(by="Datetime", inplace=True)
df.dropna(subset=["Consommation"], inplace=True)
min_date: pd.Timestamp = df["Datetime"].min()
max_date: pd.Timestamp = df["Datetime"].max()

cols_to_plot = [
    "Consommation", "Prévision J-1", "Prévision J",
    "Fioul", "Charbon", "Gaz",
    "Nucléaire", "Eolien", "Solaire", "Hydraulique",
    "Pompage", "Bioénergies"
    ]


eco2mix_layout = html.Div(
    style={
        "backgroundColor": "lightblue",
        "borderRadius": "10px",
        "padding": "20px",
        "margin": "20px",
    },
    children=[
        html.H2("Données éCO2mix (France)"),
        html.Div(
            [
                dbc.Button(
                    "Dernière semaine",
                    id="derniere-semaine-button",
                    className="me-2",
                    n_clicks=0,
                ),
                dbc.Button(
                    "Dernier mois",
                    id="dernier-mois-button",
                    n_clicks=0,
                ),
            ],
            className="d-flex justify-content-start mt-2",
        ),

        dcc.DatePickerRange(
            id="eco2mix-date-picker-range",
            min_date_allowed=min_date,
            max_date_allowed=max_date,
            start_date=max_date - pd.DateOffset(weeks=1),
            end_date=max_date,
            display_format="YYYY-MM-DD",
            clearable=False,
        ),
        html.Br(),
        dcc.Dropdown(
            id="eco2mix-variable-selector",
            options=[{"label": col, "value": col} for col in cols_to_plot],
            value=["Consommation"],  # default selected
            multi=True,
            placeholder="Sélectionnez les variables à afficher",
            ),
        dcc.Graph(id="conso-time-series"),
    ],
)


@callback(
    Output("conso-time-series", "figure"),
    Input("eco2mix-date-picker-range", "start_date"),
    Input("eco2mix-date-picker-range", "end_date"),
    Input("eco2mix-variable-selector", "value"),
)
def update_graph(start_date, end_date, selected_vars):
    filtered_df = df[
        (df["Datetime"] >= start_date) & (df["Datetime"] <= end_date)
    ]

    # La figure principale
    fig = px.line(
        filtered_df,
        x="Datetime",
        y=selected_vars,
        title="Productions et consommation électriques (MW)",
    )

    fig.update_layout(
        hovermode="x unified",
        legend_title_text="Variables",
    )

    return fig


@callback(
    Output("eco2mix-date-picker-range", "start_date"),
    Output("eco2mix-date-picker-range", "end_date"),
    Input("derniere-semaine-button", "n_clicks"),
    Input("dernier-mois-button", "n_clicks"),
    State("eco2mix-date-picker-range", "start_date"),
    State("eco2mix-date-picker-range", "end_date"),
)
def update_date_range(n_clicks_dernier_mois, n_clicks_six_mois, start_date, end_date):
    ctx = dash.callback_context
    changed_id = ctx.triggered[0]["prop_id"]
    if "derniere-semaine-button" in changed_id:
        return max_date - pd.DateOffset(weeks=1), max_date
    elif "dernier-mois-button" in changed_id:
        return max_date - pd.DateOffset(months=1), max_date
    else:
        return start_date, end_date