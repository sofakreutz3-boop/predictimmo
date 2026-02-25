from flask import Flask, render_template, current_app, request, jsonify
import pandas as pd
import os
import json
import plotly.express as px
import plotly.graph_objects as go
from training import train_and_save, confirm_new_model, load_model
from plot import (
    camenber_nb_room,
    create_table_hybride,
    histogramme_age_proximite,
    create_histogramme,
    creat_graph,
    create_map,
    camenber_age_place,
)

app = Flask(__name__)

app.config["dataframe"] = pd.read_csv("housing_1.csv")
modele_ai = load_model()
with open("model/metrics.json", "r") as f:
    metrics = json.load(f)


@app.route("/")
def index():
    df = app.config["dataframe"]

    return render_template(
        "index.html", nb_transactions=metrics["nb_transactions"], r2=metrics["r2"]
    )


@app.route("/training")
def training():

    return render_template("training.html")


@app.route("/training/upload", methods=["POST"])
def upload_and_train():
    file = request.files["dataset"]
    df = pd.read_csv(file)
    results = train_and_save(df)
    return jsonify(results)


@app.route("/training/confirm", methods=["POST"])
def confirm_model():
    data = request.get_json()
    if data["activate"] == "new":
        confirm_new_model(data["model_name"])
    return jsonify({"status": "ok"})


@app.route("/dashbord")
def dashbord():
    df = current_app.config["dataframe"]

    nb_maisons = len(df)
    valeur_moyenne = round(df["median_house_value"].mean())
    age_moyen = round(df["housing_median_age"].mean())
    valeur_max_maiz = round(df["median_house_value"].max())
    valeur_min_maiz = round(df["median_house_value"].min())

    tableau_recap = create_table_hybride(df)
    histogramme = create_histogramme(df)
    map = create_map(df)
    age_per_place = camenber_age_place(df)
    figure_barre = histogramme_age_proximite(df)
    graphique = creat_graph(df)
    nb_room = camenber_nb_room(df)

    return render_template(
        "dashbord.html",
        map=map,
        figure=figure_barre,
        valeur_moyenne=valeur_moyenne,
        nb_maisons=nb_maisons,
        age_moyen_maiz=age_moyen,
        histogramme=histogramme,
        graph=graphique,
        max_maiz=valeur_max_maiz,
        min_maiz=valeur_min_maiz,
        age_per_place=age_per_place,
        nb_room=nb_room,
        tableau_recap=tableau_recap,
    )


@app.route("/prediction", methods=["GET", "POST"])
def prediction():
    prix_final = None

    models = [f for f in os.listdir("model") if f.endswith(".joblib")]

    if request.method == "POST":
        model_name = request.form.get("model_name")
        modele = load_model(model_name)

        longitude_saisi = request.form.get("longitude")
        latitude_saisi = request.form.get("latitude")
        age_saisi = request.form.get("housing_median_age")
        total_rooms_saisi = request.form.get("total_rooms")
        total_bedrooms_saisi = request.form.get("total_bedrooms")
        population_saisi = request.form.get("population")
        households_saisi = request.form.get("households")
        median_income_saisi = request.form.get("median_income")
        proximite_saisi = request.form.get("ocean_proximity")

        rooms = float(total_rooms_saisi)
        bedrooms = float(total_bedrooms_saisi)
        pop = float(population_saisi)
        hh = float(households_saisi)

        rooms_per_hh = rooms / hh if hh != 0 else 0
        bedrooms_per_room = bedrooms / rooms if rooms != 0 else 0
        pop_per_hh = pop / hh if hh != 0 else 0

        guess = pd.DataFrame(
            [
                {
                    "longitude": float(longitude_saisi),
                    "latitude": float(latitude_saisi),
                    "housing_median_age": float(age_saisi),
                    "total_rooms": rooms,
                    "total_bedrooms": bedrooms,
                    "population": pop,
                    "households": hh,
                    "median_income": float(median_income_saisi) / 10000,
                    "ocean_proximity": float(proximite_saisi),
                    "rooms_per_household": rooms_per_hh,
                    "bedrooms_per_room": bedrooms_per_room,
                    "population_per_household": pop_per_hh,
                }
            ]
        )

        prix_final = modele.predict(guess)[0]
        prix_final = round(prix_final, 2)

    return render_template("prediction.html", resultat=prix_final, models=models)
