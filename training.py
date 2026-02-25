import pandas as pd
import numpy as np
import json
import joblib
import os
from datetime import datetime
from sklearn.metrics import root_mean_squared_error, r2_score

MODEL_DIR = "model"


def prepare_data(df):
    """cette fonction permet de préparer les données pour quellles puissent être intégrées avec les données précedente
    étape 1 : ne garde que les colonne qui m'interessent
    étape 2 : enlève les donnée contenant des N/A
    etape 3 : remplace les chaie de caractère de la colonne ocean_proximity par des numbres
    etape 4 : créé les 3 nouvelle variable qui sont utilisé par le model"""

    colonnes_attendues = [
        "longitude",
        "latitude",
        "housing_median_age",
        "total_rooms",
        "total_bedrooms",
        "population",
        "households",
        "median_income",
        "ocean_proximity",
        "median_house_value",
    ]
    df = df[colonnes_attendues]
    df = df.dropna()

    df["ocean_proximity"] = df["ocean_proximity"].replace(
        ["ISLAND", "<1H OCEAN", "NEAR BAY", "INLAND", "NEAR OCEAN"],
        ["1", "4", "3", "0", "2"],
    )

    df["rooms_per_household"] = df["total_rooms"] / df["households"]
    df["bedrooms_per_room"] = df["total_bedrooms"] / df["total_rooms"]
    df["population_per_household"] = df["population"] / df["households"]

    return df


def load_model(model_name="model_ramdomforest.joblib"):
    """permet d'importer le modele_ai cela defini dans un fonction pour ne pas avoir à l'ecrire a plusieurs endroit"""
    return joblib.load(os.path.join(MODEL_DIR, model_name))


def train_and_save(df):
    """1/ entraine le model actuel avec les nouvelles données
    2 /entraine avec les donnéancienne et actuelle
    3 / Puis fait les calculs de score comparatif entre le model actuel et le nouveau
    """
    print("▶ Préparation des données...")
    df = prepare_data(df)
    old_df = pd.read_csv("housing_1.csv")
    old_df = prepare_data(old_df)
    combined_df = pd.concat([old_df, df], ignore_index=True)
    X = combined_df.drop(columns=["median_house_value"])
    y = combined_df["median_house_value"]

    print("▶ Évaluation de l'ancien modèle...")
    old_model = load_model()
    old_preds = old_model.predict(X)
    old_rmse = root_mean_squared_error(y, old_preds)
    old_r2 = r2_score(y, old_preds)

    print("▶ Réentraînement en cours...")
    new_model = load_model()
    new_model.fit(X, y)

    print("▶ Évaluation du nouveau modèle...")
    new_preds = new_model.predict(X)
    new_rmse = root_mean_squared_error(y, new_preds)
    new_r2 = r2_score(y, new_preds)

    print("▶ Sauvegarde...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    new_model_name = f"model_ramdomforest_{timestamp}.joblib"
    joblib.dump(new_model, os.path.join(MODEL_DIR, new_model_name))

    metrics = {"r2": round(new_r2 * 100, 1), "nb_transactions": len(combined_df)}
    with open("model/metrics.json", "w") as f:
        json.dump(metrics, f)

    print("✅ Terminé !")

    return {
        "old": {"rmse": round(old_rmse, 2), "r2": round(old_r2, 4)},
        "new": {"rmse": round(new_rmse, 2), "r2": round(new_r2, 4)},
        "new_model_name": new_model_name,
    }


def confirm_new_model(new_model_name):
    """Remplace le modèle principal par le nouveau si l'utilisateur valide."""
    new_path = os.path.join(MODEL_DIR, new_model_name)
    main_path = os.path.join(MODEL_DIR, "model_ramdomforest.joblib")
    joblib.dump(joblib.load(new_path), main_path)
