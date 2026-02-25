import plotly.express as px
import pandas as pd
import plotly.graph_objects as go


def create_histogramme(df):
    """Use to creat the histogram representing the number of houses based on their value e
    xcluding the 500k$ witch look like a top limit value"""

    df_filtre = df[df["median_house_value"] < 500000]

    fig_hist = px.histogram(
        df_filtre,
        x="median_house_value",
        nbins=50,
        title="Distribution de la valeur des maisons",
        color_discrete_sequence=["#3e0879"],
    )
    fig_hist.update_layout(height=600, margin=dict(t=50, l=0, r=0, b=0))
    return fig_hist.to_html()


def creat_graph(df):
    """this fonction is use to create the graph representing the house values based on their age for each zone"""

    df_moyennes = (
        df.groupby(["housing_median_age", "ocean_proximity"])["median_house_value"]
        .mean()
        .reset_index()
    )

    graph = px.line(
        df_moyennes,
        x="housing_median_age",
        y="median_house_value",
        color="ocean_proximity",
        line_shape="spline",
        title="Prix moyen des maisons par âge et emplacement",
        color_discrete_sequence=px.colors.qualitative.D3,
    )

    df_globale = (
        df.groupby("housing_median_age")["median_house_value"].mean().reset_index()
    )

    graph.add_scatter(
        x=df_globale["housing_median_age"],
        y=df_globale["median_house_value"],
        name="MOYENNE GLOBALE",
        line=dict(color="black", width=3, dash="dash"),  # Pointillés pour la distinguer
        mode="lines",
    )

    graph.update_layout(
        xaxis_title="Âge de la maison",
        yaxis_title="Valeur moyenne ($)",
        hovermode="x unified",
        height=600,
    )

    return graph.to_html()


def prepare_sunburst_data_age_house(df_filtered):
    """Agrège et prépare les données pour le sunburst age biens"""
    agg = df_filtered.groupby(
        ["ocean_proximity", "tranche_age"], as_index=False, observed=True
    ).agg({"nb_ventes": "sum", "median_house_value": "mean"})

    # ← AJOUTE CETTE LIGNE : créer la colonne prix_moyen
    agg["prix_moyen"] = agg["median_house_value"].round(0)

    return agg


def create_temp_sunburst_age_house(df_filtered):
    """Crée un sunburst temporaire et retourne ses données"""
    filtered_data = prepare_sunburst_data_age_house(df_filtered)

    temp_fig = px.sunburst(
        filtered_data,
        path=["ocean_proximity", "tranche_age"],
        values="nb_ventes",
        color="prix_moyen",
        color_continuous_scale="Viridis",
        custom_data=["prix_moyen", "nb_ventes"],
    )

    return temp_fig.data[0]


def camenber_age_place(df):
    df = df.copy().dropna(
        subset=[
            "ocean_proximity",
            "housing_median_age",
            "median_income",
            "median_house_value",
        ]
    )

    bins_rooms = [0, 10, 20, 30, 40, 50, 100]
    labels_rooms = [
        "Âge: 1-10",
        "Âge: 11-20",
        "Âge: 21-30",
        "Âge: 31-40",
        "Âge: 41-50",
        "Âge: 50+",
    ]
    df["tranche_age"] = pd.cut(
        df["housing_median_age"], bins=bins_rooms, labels=labels_rooms
    ).astype(str)

    bin_rev = [0, 1.5, 3, 4.5, 6, 7.5, 10, 100]
    labels_rev = [
        "0-15k$",
        "15-30k$",
        "30-45k$",
        "45-60k$",
        "60-75k$",
        "75-100k$",
        "100k$+",
    ]
    df["revenu_label"] = pd.cut(
        df["median_income"], bins=bin_rev, labels=labels_rev
    ).astype(str)

    df["nb_ventes"] = 1

    initial_data = prepare_sunburst_data_age_house(df)

    fig = px.sunburst(
        initial_data,
        path=["ocean_proximity", "tranche_age"],
        values="nb_ventes",
        color="prix_moyen",
        color_continuous_scale="Viridis",
        custom_data=["prix_moyen", "nb_ventes"],
    )

    fig.update_traces(
        hovertemplate="<b>📍 %{label}</b><br>"
        + "🏠 Nombre de ventes: %{customdata[1]:,}<br>"
        + "💰 Prix moyen: $%{customdata[0]:,.0f}<br>"
        + "📊 Part du total: %{percentParent:.1%}<br>"
        + "<extra></extra>"
    )

    buttons = []

    all_trace = create_temp_sunburst_age_house(df)
    custom_template = (
        "<b>📍 %{label}</b><br>"
        + "🏠 Nombre de ventes: %{customdata[1]:,}<br>"
        + "💰 Prix moyen: $%{customdata[0]:,.0f}<br>"
        + "📊 Part du total: %{percentParent:.1%}<br>"
        + "<extra></extra>"
    )

    buttons.append(
        dict(
            label="Tous les revenus",
            method="restyle",
            args=[
                {
                    "labels": [all_trace.labels],
                    "parents": [all_trace.parents],
                    "values": [all_trace.values],
                    "ids": [all_trace.ids],
                    "marker.colors": [all_trace.marker.colors],
                    "customdata": [all_trace.customdata],
                    "hovertemplate": custom_template,
                }
            ],
        )
    )

    for r_label in labels_rev:
        sub_df = df[df["revenu_label"] == r_label]

        if len(sub_df) > 0:
            print(f"  Filtre {r_label}: {len(sub_df)} lignes")

            filtered_trace = create_temp_sunburst_age_house(sub_df)

            buttons.append(
                dict(
                    label=r_label,
                    method="restyle",
                    args=[
                        {
                            "labels": [filtered_trace.labels],
                            "parents": [filtered_trace.parents],
                            "values": [filtered_trace.values],
                            "ids": [filtered_trace.ids],
                            "marker.colors": [filtered_trace.marker.colors],
                            "customdata": [filtered_trace.customdata],
                            "hovertemplate": custom_template,
                        }
                    ],
                )
            )

    fig.update_layout(
        title={
            "text": "Hiérarchie : Emplacement et âge des biens<br><span style='font-size:12px; color:gray;'>Triable par tranche de revenu</span>",
            "x": 0.05,
            "xanchor": "left",
            "font": {"size": 16},
        },
        updatemenus=[
            dict(
                buttons=buttons,
                direction="down",
                showactive=True,
                x=1.15,
                xanchor="right",
                y=1.15,
                yanchor="top",
                bgcolor="white",
                bordercolor="#CCCCCC",
                borderwidth=1,
            )
        ],
        height=700,
        margin=dict(t=100),
        coloraxis_colorbar=dict(title="Prix moyen ($)", tickformat="$,.0f"),
    )

    return fig.to_html(include_plotlyjs="cdn")


def create_map(df):
    """The function creat a streetmap with colorsheat indicating the median value of each houses"""
    fig_map = px.scatter_map(
        df,
        lat="latitude",
        lon="longitude",
        color="median_house_value",
        size="median_house_value",
        color_continuous_scale="Viridis",
        size_max=12,
        zoom=5,
        map_style="carto-positron",
    )
    fig_map.update_layout(height=600, margin={"r": 10, "t": 10, "l": 0, "b": 0})
    return fig_map.to_html()


def histogramme_age_proximite(df):

    bins = [0, 10, 20, 30, 40, 50, 100]
    labels = ["1-10 ans", "11-20 ans", "21-30 ans", "31-40 ans", "41-50 ans", "50+"]
    df["tranche_age"] = pd.cut(df["housing_median_age"], bins=bins, labels=labels)

    df_counts = (
        df.groupby(["tranche_age", "ocean_proximity"])
        .size()
        .reset_index(name="nombre_maisons")
    )

    fig_bar = px.bar(
        df_counts,
        x="tranche_age",
        y="nombre_maisons",
        color="ocean_proximity",
        title="Répartition de l'âge des maisons par proximité océan",
        color_discrete_sequence=px.colors.sequential.GnBu_r,
        barmode="stack",
        pattern_shape="ocean_proximity",
    )

    fig_bar.update_layout(
        height=600,
        xaxis_title="Tranches d'âge",
        yaxis_title="Nombre de maisons",
        legend_title="Proximité",
        template="plotly_white",
    )

    return fig_bar.to_html()

    df = df.copy().dropna(subset=["ocean_proximity", "total_rooms", "median_income"])

    bins_rooms = [0, 500, 1000, 2000, 5000, 1000000]
    labels_rooms = [
        "Très petit:0-500",
        "Petit:501-1k",
        "Moyen:1k-2k",
        "Grand:2k-5k",
        "Très grand:5k+",
    ]
    df["tranche_pieces"] = pd.cut(
        df["total_rooms"], bins=bins_rooms, labels=labels_rooms
    ).astype(str)

    bin_rev = [0, 1.5, 3, 4.5, 6, 7.5, 10, 100]
    labels_rev = [
        "0-15k$",
        "15-30k$",
        "30-45k$",
        "45-60k$",
        "60-75k$",
        "75-100k$",
        "100k$+",
    ]
    df["revenu_label"] = pd.cut(
        df["median_income"], bins=bin_rev, labels=labels_rev
    ).astype(str)

    df["nb_ventes"] = 1

    # Fonction pour créer un dataframe agrégé
    def get_aggregated_data(df_filtered):
        agg_df = df_filtered.groupby(
            ["ocean_proximity", "tranche_pieces"], as_index=False
        )["nb_ventes"].sum()
        return agg_df

    # Créer le graphique initial avec TOUTES les données
    agg_initial = get_aggregated_data(df)
    fig = px.sunburst(
        agg_initial,
        path=["ocean_proximity", "tranche_pieces"],
        values="nb_ventes",
        title="Hiérarchie : Emplacement et Nombre de pièces",
        color="nb_ventes",
        color_continuous_scale="Viridis",
    )

    # Créer les boutons avec données agrégées
    buttons = [
        dict(
            label="Tous les revenus",
            method="restyle",
            args=[
                {
                    "labels": [
                        agg_initial["tranche_pieces"].tolist()
                        + agg_initial["ocean_proximity"].unique().tolist()
                    ],
                    "parents": [
                        [""] * len(agg_initial["ocean_proximity"].unique())
                        + agg_initial["ocean_proximity"].tolist()
                    ],
                    "values": [
                        [
                            agg_initial.groupby("ocean_proximity")["nb_ventes"]
                            .sum()
                            .tolist()
                        ]
                        + agg_initial["nb_ventes"].tolist()
                    ],
                }
            ],
        )
    ]

    for r_label in labels_rev:
        sub_df = df[df["revenu_label"] == r_label]
        if not sub_df.empty:
            agg_sub = get_aggregated_data(sub_df)
            buttons.append(
                dict(
                    label=r_label,
                    method="update",
                    args=[
                        {
                            "labels": [
                                agg_sub["tranche_pieces"].tolist()
                                + agg_sub["ocean_proximity"].unique().tolist()
                            ],
                            "parents": [
                                [""] * len(agg_sub["ocean_proximity"].unique())
                                + agg_sub["ocean_proximity"].tolist()
                            ],
                            "values": [
                                [
                                    agg_sub.groupby("ocean_proximity")["nb_ventes"]
                                    .sum()
                                    .tolist()
                                ]
                                + agg_sub["nb_ventes"].tolist()
                            ],
                        },
                        {"title": f"Revenu : {r_label}"},
                    ],
                )
            )

    fig.update_layout(
        updatemenus=[dict(buttons=buttons, x=0, y=1.15, xanchor="left", yanchor="top")],
        height=650,
    )

    return fig.to_html()


def create_table_hybride(df):

    df_synthese = (
        df.groupby("ocean_proximity")
        .agg(
            {
                "housing_median_age": "mean",
                "total_rooms": "mean",
                "median_house_value": "mean",
            }
        )
        .reset_index()
        .round(1)
    )

    cols_detail = [
        "longitude",
        "latitude",
        "housing_median_age",
        "total_rooms",
        "median_house_value",
    ]
    categories = df["ocean_proximity"].unique().tolist()

    fig = go.Figure()

    fig.add_trace(
        go.Table(
            header=dict(
                values=[
                    "<b>SECTEUR</b>",
                    "<b>Moy. Âge</b>",
                    "<b>Moy. Pièces</b>",
                    "<b>Prix Moyen ($)</b>",
                ],
                fill_color="#3e0879",
                font=dict(color="white", size=13),
            ),
            cells=dict(
                values=[
                    df_synthese["ocean_proximity"],
                    df_synthese["housing_median_age"],
                    df_synthese["total_rooms"],
                    df_synthese["median_house_value"],
                ],
                fill_color="#e8daef",
                align="center",
                height=30,
            ),
            visible=True,
        )
    )

    for cat in categories:

        df_filtered = df[df["ocean_proximity"] == cat][cols_detail].head(50)

        fig.add_trace(
            go.Table(
                header=dict(
                    values=["Longitude", "Latitude", "Âge", "Pièces", "Valeur ($)"],
                    fill_color="#2c3e50",
                    font=dict(color="white", size=12),
                ),
                cells=dict(
                    values=[df_filtered[c] for c in cols_detail],
                    fill_color="#fdfefe",
                    align="left",
                    height=25,
                ),
                visible=False,
            )
        )

    dropdown_buttons = []

    vis_all = [False] * (len(categories) + 1)
    vis_all[0] = True
    dropdown_buttons.append(
        dict(
            label="📊 Synthèse (Moyennes)",
            method="update",
            args=[{"visible": vis_all}, {"title": "Synthèse par Secteur (Moyennes)"}],
        )
    )

    for i, cat in enumerate(categories):
        vis_cat = [False] * (len(categories) + 1)
        vis_cat[i + 1] = True
        dropdown_buttons.append(
            dict(
                label=f"🏠 Détail : {cat}",
                method="update",
                args=[{"visible": vis_cat}, {"title": f"Détail des maisons : {cat}"}],
            )
        )

    fig.update_layout(
        updatemenus=[
            dict(
                buttons=dropdown_buttons,
                direction="down",
                showactive=True,
                x=0.0,
                y=1.25,
                xanchor="left",
                yanchor="top",
            )
        ],
        margin=dict(t=120, l=10, r=10, b=10),
        height=600,
        title_text="Analyse Immobilière : Synthèse vs Détails Géographiques",
        title_x=0.5,
    )

    return fig.to_html()


def prepare_sunburst_data_nb_room(df_filtered):
    """Agrège et prépare les données pour le sunburst nb de piece"""
    agg = df_filtered.groupby(
        ["ocean_proximity", "tranche_pieces"], as_index=False, observed=True
    ).agg({"nb_ventes": "sum", "median_house_value": "mean"})
    agg["prix_moyen"] = agg["median_house_value"].round(0)

    return agg


def create_temp_sunburst_nb_room(df_filtered):
    """Crée un sunburst temporaire et retourne ses données"""
    filtered_data = prepare_sunburst_data_nb_room(df_filtered)

    temp_fig = px.sunburst(
        filtered_data,
        path=["ocean_proximity", "tranche_pieces"],
        values="nb_ventes",
        color="prix_moyen",
        color_continuous_scale="Viridis",
        custom_data=["prix_moyen", "nb_ventes"],
    )

    temp_fig.update_traces(
        hovertemplate="<b>%{label}</b><br>"
        + "Nombre de ventes: %{customdata[1]:,}<br>"
        + "Prix moyen: $%{customdata[0]:,.0f}<br>"
        + "<extra></extra>"
    )
    return temp_fig.data[0]


def camenber_nb_room(df):

    df = df.copy().dropna(subset=["ocean_proximity", "total_rooms", "median_income"])

    bins_rooms = [0, 500, 1000, 2000, 5000, 1000000]
    labels_rooms = [
        "très petit: 0-500",
        "Petit: 501-1k",
        "Moyen: 1k-2k",
        "Grand: 2k-5k",
        "Très grand: 5k+",
    ]
    df["tranche_pieces"] = pd.cut(
        df["total_rooms"], bins=bins_rooms, labels=labels_rooms
    ).astype(str)

    bin_rev = [0, 1.5, 3, 4.5, 6, 7.5, 10, 100]
    labels_rev = [
        "0-15k$",
        "15-30k$",
        "30-45k$",
        "45-60k$",
        "60-75k$",
        "75-100k$",
        "100k$+",
    ]
    df["revenu_label"] = pd.cut(
        df["median_income"], bins=bin_rev, labels=labels_rev
    ).astype(str)

    df["nb_ventes"] = 1

    initial_data = prepare_sunburst_data_nb_room(df)
    custom_template = (
        "<b>📍 %{label}</b><br>"
        + "🏠 Nombre de ventes: %{customdata[1]:,}<br>"
        + "💰 Prix moyen: $%{customdata[0]:,.0f}<br>"
        + "📊 Part du total: %{percentParent:.1%}<br>"
        + "<extra></extra>"
    )

    fig = px.sunburst(
        initial_data,
        path=["ocean_proximity", "tranche_pieces"],
        values="nb_ventes",
        color="prix_moyen",
        color_continuous_scale="Viridis",
        custom_data=["prix_moyen", "nb_ventes"],
    )

    buttons = []

    all_trace = create_temp_sunburst_nb_room(df)

    buttons.append(
        dict(
            label="Tous les revenus",
            method="restyle",
            args=[
                {
                    "labels": [all_trace.labels],
                    "parents": [all_trace.parents],
                    "values": [all_trace.values],
                    "ids": [all_trace.ids],
                    "marker.colors": [all_trace.marker.colors],
                    "customdata": [all_trace.customdata],
                    "hovertemplate": custom_template,
                }
            ],
        )
    )

    for r_label in labels_rev:
        sub_df = df[df["revenu_label"] == r_label]

        if len(sub_df) > 0:
            print(f"  Filtre {r_label}: {len(sub_df)} lignes")

            filtered_trace = create_temp_sunburst_nb_room(sub_df)

            buttons.append(
                dict(
                    label=r_label,
                    method="restyle",
                    args=[
                        {
                            "labels": [filtered_trace.labels],
                            "parents": [filtered_trace.parents],
                            "values": [filtered_trace.values],
                            "ids": [filtered_trace.ids],
                            "marker.colors": [filtered_trace.marker.colors],
                            "customdata": [filtered_trace.customdata],
                            "hovertemplate": custom_template,
                        }
                    ],
                )
            )

    # Layout
    fig.update_layout(
        title={
            "text": "Hiérarchie : Emplacement et Nombre de pièces<br><span style='font-size:12px; color:gray;'>Triable par tranche de revenu</span>",
            "x": 0.5,
            "xanchor": "left",
            "font": {"size": 16},
        },
        updatemenus=[
            dict(
                buttons=buttons,
                direction="down",
                showactive=True,
                x=0.98,
                xanchor="left",
                y=1.15,
                yanchor="top",
                bgcolor="white",
                bordercolor="#CCCCCC",
                borderwidth=1,
            )
        ],
        height=700,
        margin=dict(t=120),
        coloraxis_colorbar=dict(title="Prix moyen ($)", tickformat="$,.0f"),
    )

    print("✅ Figure créée avec succès")
    return fig.to_html(include_plotlyjs="cdn")
