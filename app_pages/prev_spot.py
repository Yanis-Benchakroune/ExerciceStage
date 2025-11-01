from dash import dcc, html, Input, Output, callback, State, dash_table
import os
import pandas as pd
import pickle
import base64
import io
import plotly.express as px
import requests
from datetime import date

model_files = [f for f in os.listdir("models") if f.endswith(".pkl")]
prev_spot_layout = prev_spot_layout = html.Div(
    style={
        "backgroundColor": "lightblue",
        "borderRadius": "10px",
        "padding": "20px",
        "margin": "20px",
    },
    children=[
        html.H2("Prévisions de prix SPOT"),

        html.H4("Source des données :"),
        dcc.RadioItems(
            id="data-source",
            options=[
                {"label": "Importer un fichier CSV", "value": "csv"},
                {"label": "Télécharger via l’API éCO2mix", "value": "api"},
            ],
            value="csv",
            inline=True,
            style={"marginBottom": "10px"},
            labelStyle={"display": "inline-block", "marginRight": "30px"}
        ),

        # CSV upload
        html.Div(
            id="csv-upload-container",
            children=[
                dcc.Upload(
                    id="upload-data",
                    children=html.Div(["Glisser-déposer ou sélectionner un fichier CSV à importer"]),
                    style={
                        "width": "100%",
                        "height": "60px",
                        "lineHeight": "60px",
                        "borderWidth": "1px",
                        "borderStyle": "dashed",
                        "borderRadius": "5px",
                        "textAlign": "center",
                        "margin": "10px",
                    },
                    multiple=False,
                ),
                html.P(
                    [
                        "Veuillez importer un fichier CSV contenant les données historiques (téléchargé depuis ",
                        html.A(
                            "eco2mix",
                            href="https://www.rte-france.com/eco2mix/telecharger-les-indicateurs",
                            target="_blank",
                            rel="noopener noreferrer",
                        ),
                        ").",
                    ]
                ),
            ],
        ),

        # API date selection
        html.Div(
            id="api-date-container",
            style={"display": "none"},
            children=[
                html.H4("Sélectionnez la période de téléchargement :"),
                dcc.DatePickerRange(
                    id="date-range-picker",
                    start_date=date(2025, 1, 1),
                    end_date=date.today(),
                    display_format="DD/MM/YYYY",
                ),
                html.Button("Télécharger depuis l’API", id="api-download-button", n_clicks=0),
                html.Div(id="api-download-status", style={"marginTop": "10px", "color": "green"}),
            ],
        ),

        html.Div(id="output-data-upload"),

        html.H3("Sélectionner un modèle :"),
        dcc.Dropdown(
            id="model-dropdown",
            options=[{"label": f, "value": f} for f in model_files if f != "scaler.pkl"],
            placeholder="Sélectionner un modèle",
        ),
        html.Button("Lancer les prévisions", id="run-forecasts-button", n_clicks=0),

        html.Div(
            dcc.Graph(id="forecast-graph"),
            id="graph-container",
            style={"display": "none"},
        ),
    ],
)

@callback(
    Output("csv-upload-container", "style"),
    Output("api-date-container", "style"),
    Input("data-source", "value"),
)
def toggle_input_mode(source):
    if source == "api":
        return {"display": "none"}, {"display": "block"}
    return {"display": "block"}, {"display": "none"}

@callback(
    Output("output-data-upload", "children", allow_duplicate=True),
    Output("upload-data", "contents", allow_duplicate=True),
    Input("api-download-button", "n_clicks"),
    State("date-range-picker", "start_date"),
    State("date-range-picker", "end_date"),
    prevent_initial_call="initial_duplicate",
)
def download_from_api(n_clicks, start_date, end_date):
    if n_clicks == 0 or not start_date or not end_date:
        return html.Div(), None

    try:
        url = "https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/eco2mix-national-tr/exports/json"
        params = {
            "limit": -1,
            "where": f"date_heure >= '{pd.to_datetime(start_date)}' AND date_heure <= '{pd.to_datetime(end_date)}'",
        }
        resp = requests.get(url, params=params)
        resp.raise_for_status()

        data = pd.DataFrame(resp.json())
        data = data.rename(columns={
            "date": "Date", "heure": "Heures",
            'consommation': 'Consommation',
            'prevision_j1': 'Prévision J-1',
            'prevision_j': 'Prévision J',
            'fioul': 'Fioul',
            'charbon': 'Charbon',
            'gaz': 'Gaz',
            'nucleaire': 'Nucléaire',
            'eolien': 'Eolien',
            'eolien_terrestre': 'Eolien terrestre',
            'eolien_offshore': 'Eolien offshore',
            'solaire': 'Solaire',
            'hydraulique': 'Hydraulique',
            'pompage': 'Pompage',
            'bioenergies': 'Bioénergies',
            'ech_physiques': 'Ech. physiques',
            'taux_co2': 'Taux de Co2',
            'ech_comm_angleterre': 'Ech. comm. Angleterre',
            'ech_comm_espagne': 'Ech. comm. Espagne',
            'ech_comm_italie': 'Ech. comm. Italie',
            'ech_comm_suisse': 'Ech. comm. Suisse',
            'ech_comm_allemagne_belgique': 'Ech. comm. Allemagne-Belgique',
            'fioul_tac': 'Fioul - TAC',
            'fioul_cogen': 'Fioul - Cogén.',
            'fioul_autres': 'Fioul - Autres',
            'gaz_tac': 'Gaz - TAC',
            'gaz_cogen': 'Gaz - Cogén.',
            'gaz_ccg': 'Gaz - CCG',
            'gaz_autres': 'Gaz - Autres',
            'hydraulique_fil_eau_eclusee': 'Hydraulique - Fil de l?eau + éclusée',
            'hydraulique_lacs': 'Hydraulique - Lacs',
            'hydraulique_step_turbinage': 'Hydraulique - STEP turbinage',
            'bioenergies_dechets': 'Bioénergies - Déchets',
            'bioenergies_biomasse': 'Bioénergies - Biomasse',
            'bioenergies_biogaz': 'Bioénergies - Biogaz'
        })

        csv_buffer = io.StringIO()
        data.to_csv(csv_buffer, index=False, sep="\t")
        encoded_csv = base64.b64encode(csv_buffer.getvalue().encode("latin1")).decode()

        preview_table = dash_table.DataTable(
            columns=[{"name": i, "id": i} for i in data.columns],
            data=data.head(20).to_dict("records"),
            style_table={"overflowY": "auto", "height": "400px"},
            style_cell={"textAlign": "left", "padding": "5px"},
            style_header={"backgroundColor": "#f0f0f0", "fontWeight": "bold"},
        )

        return html.Div([
            html.H5(f"Données téléchargées depuis l’API ({len(data)} lignes)"),
            html.Hr(),
            preview_table,
        ]), f"data:text/csv;base64,{encoded_csv}"

    except Exception as e:
        return html.Div([f"Erreur lors du téléchargement API: {e}"]), None


@callback(
    Output("output-data-upload", "children"),
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
)
def upload_input_file(contents, filename):
    if contents is None:
        return html.Div()
    try:
        # Les fichiers eCO2mix_RTE_*.xls sont en réalité des .csv séparés par des \t
        # Ils sont encodés en latin1 (présence d'accents),
        # et la dernière ligne est un message d'avertissement, à supprimer
        _, content_string = contents.split("base64,")
        decoded = base64.b64decode(content_string)
        df = pd.read_csv(
            io.StringIO(decoded.decode("latin1")), sep="\t", index_col=False
        ).iloc[:-1]

        # Si l'import a réussi, affiche le nom du fichier et ses premières lignes
        return html.Div([
            html.H5(filename),
            html.Hr(),
            dash_table.DataTable(
                columns=[{"name": i, "id": i} for i in df.columns],
                data=df.to_dict('records'),
                style_table={'overflowY': 'auto',
                             'height': '400px',   # sets visible height
                             },
                style_cell={'textAlign': 'left', 'padding': '5px'},
                style_header={'backgroundColor': '#f0f0f0', 'fontWeight': 'bold'})
            ])
    except Exception as e:
        print(e)
        return html.Div(["There was an error processing this file."])


@callback(
    Output("forecast-graph", "figure"),
    Output("graph-container", "style"),
    Input("run-forecasts-button", "n_clicks"),
    State("model-dropdown", "value"),
    State("upload-data", "contents"),
)
def run_forecasts(n_clicks, model_filename, contents):
    if not (n_clicks > 0 and model_filename and contents):
        return {}, {"display": "none"}

    try:
        _, content_string = contents.split("base64,")
        decoded = base64.b64decode(content_string)
        df = pd.read_csv(
            io.StringIO(decoded.decode("latin1")), sep="\t", index_col=False
        ).iloc[:-1]

        with open(f"models/{model_filename}", "rb") as file:
            model = pickle.load(file)
        with open("models/scaler.pkl", "rb") as file:
            scaler = pickle.load(file)
        df.replace("ND", float("nan")).dropna()
        prediction_datetimes = pd.to_datetime(df.Date + " " + df.Heures)        
        df = df[model.feature_names_in_]
        try:
            # TODO: exploiter `previsions_prix_spot`
            df = scaler.transform(df)
            previsions_prix_spot = model.predict(df)
        except Exception as e:
            return html.Div([f"Erreur lors de l'exécution du modèle: {e}"])

        previsions_prix_spot = pd.Series(data=previsions_prix_spot, index=prediction_datetimes, name="Prediction")
        # Enregistre en .csv les données de prévision
        pd.DataFrame(previsions_prix_spot).to_csv("data/previsions.csv")

        spot = pd.read_csv("data/France.csv", sep=",", parse_dates=[-3,-2])
        spot = spot.loc[spot["Datetime (UTC)"].isin(prediction_datetimes)]
        df_previsions = pd.merge(spot, previsions_prix_spot, left_on="Datetime (UTC)", right_index=True)
        
        fig = px.line(
            df_previsions, 
            x="Datetime (UTC)", 
            y=["Prediction", "Price (EUR/MWhe)"], 
            title="Prévisions de prix SPOT (EUR/MWh) à partir des données éCO2mix comparées avec les prix réels")
        fig.update_layout(hovermode="x unified")
        
        # return fig
        return fig, {"display": "block"}

    except Exception as e:
        print(e)
        return {}
