# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.6
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% _uuid="8f2839f25d086af736a60e9eeb907d3b93b6e0e5" _cell_guid="b1076dfc-b9ad-4769-8c92-a6c4dae69d19"
# !pip install namedivider-python python-romkan-ng

import pandas as pd
import numpy as np
import romkan
import os
import kagglehub
from namedivider import BasicNameDivider
from time import time
from typing import List, Tuple, Dict, Callable
import math
import matplotlib.pyplot as plt
import importlib

IS_KAGGLE = os.path.exists("/kaggle/input")


def get_jpersonwiki_path():
    if IS_KAGGLE:
        return "/kaggle/input/datasets/rentoda/jpersonwiki/jpersonwiki.csv"
    path = kagglehub.dataset_download("rentoda/jpersonwiki")
    return os.path.join(path, "jpersonwiki.csv")


# %%
import re
import csv


def parse_enamdict(input_path, output_path):
    rows = []

    with open(input_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # Extract kanji, hiragana, sex, romaji
            match = re.match(r"^(.+?)\s*\[(.+?)\]\s*/\(([mf])\)\s*(.+?)/", line)
            if not match:
                continue

            kanji, hiragana, sex, romaji = match.groups()
            rows.append(
                {
                    "sex": sex,
                    "kanji": kanji,
                    "hiragana": hiragana,
                    "romaji": romaji.strip(),
                }
            )

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["sex", "kanji", "hiragana", "romaji"])
        writer.writeheader()
        writer.writerows(rows)


def parse_name_origin_to_flat_csv(sex, input_path, output_path):
    rows = []

    with open(input_path, encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split(",")
            if len(parts) < 3:
                continue
            hiragana, romaji, *kanjis = parts
            for kanji in kanjis:
                rows.append(
                    {"kanji": kanji, "hiragana": hiragana, "romaji": romaji, "sex": sex}
                )

    pd.DataFrame(rows).to_csv(output_path, index=False)


# %%
# https://github.com/rgamici/japanese-names
# !curl --create-dirs -o ./intermidiate/enumdict_male.txt "https://raw.githubusercontent.com/rgamici/japanese-names/refs/heads/master/male"
# !curl --create-dirs -o ./intermidiate/enumdict_female.txt "https://raw.githubusercontent.com/rgamici/japanese-names/refs/heads/master/female"
# !sync

parse_enamdict("./intermidiate/enumdict_male.txt", "./intermidiate/enumdict_male.csv")
parse_enamdict(
    "./intermidiate/enumdict_female.txt", "./intermidiate/enumdict_female.csv"
)
# !sync

enamdict_male = pd.read_csv("./intermidiate/enumdict_male.csv")
enamdict_female = pd.read_csv("./intermidiate/enumdict_female.csv")
enamdict = pd.concat([enamdict_male, enamdict_female])

# https://github.com/shuheilocale/japanese-personal-name-dataset
# !curl --create-dirs -o ./intermidiate/name_origin_male.txt "https://raw.githubusercontent.com/shuheilocale/japanese-personal-name-dataset/refs/heads/main/japanese_personal_name_dataset/dataset/first_name_man_org.csv"
# !curl --create-dirs -o ./intermidiate/name_origin_female.txt "https://raw.githubusercontent.com/shuheilocale/japanese-personal-name-dataset/refs/heads/main/japanese_personal_name_dataset/dataset/first_name_woman_org.csv"
# !sync

parse_name_origin_to_flat_csv(
    "M", "./intermidiate/name_origin_male.txt", "./intermidiate/name_origin_male.csv"
)
parse_name_origin_to_flat_csv(
    "F",
    "./intermidiate/name_origin_female.txt",
    "./intermidiate/name_origin_female.csv",
)
# !sync

name_origin_male = pd.read_csv("./intermidiate/name_origin_male.csv")
name_origin_female = pd.read_csv("./intermidiate/name_origin_female.csv")
name_origin = pd.concat([name_origin_male, name_origin_female])

jpersonwiki = pd.read_csv(get_jpersonwiki_path(), low_memory=False)
jpersonwiki = jpersonwiki[jpersonwiki["is_japanese_name"] == True]
jpersonwiki = jpersonwiki[["gender", "kanji", "hiragana", "birth_year"]]
jpersonwiki = jpersonwiki.rename(columns={"gender": "sex"})
jpersonwiki = jpersonwiki[jpersonwiki["sex"].isin(["M", "F"])]

enamdict.columns = ["sex", "kanji", "hiragana", "romaji"]
enamdict["sex"] = enamdict["sex"].str.upper()
name_origin.columns = ["kanji", "hiragana", "romaji", "sex"]


# %%
def preprocess_jpersonwiki(df: pd.DataFrame) -> pd.DataFrame:
    basic_divider = BasicNameDivider()
    divided = df["kanji"].apply(lambda x: basic_divider.divide_name(str(x)))
    hira_parts = df["hiragana"].str.split()
    df["family_kanji"] = divided.apply(lambda x: x.family)
    df["given_kanji"] = divided.apply(lambda x: x.given)
    df["family_hiragana"] = hira_parts.str[0]
    df["given_hiragana"] = hira_parts.str[1]
    return df[
        [
            "sex",
            "given_kanji",
            "given_hiragana",
            "family_kanji",
            "family_hiragana",
            "birth_year",
        ]
    ]


jpersonwiki["birth_year"] = pd.to_numeric(
    jpersonwiki["birth_year"], errors="coerce"
).astype("Int64")
jpersonwiki = preprocess_jpersonwiki(jpersonwiki)

# given nameのみのデータセット
enamdict_out = enamdict.rename(
    columns={"kanji": "given_kanji", "hiragana": "given_hiragana"}
)[["sex", "given_kanji", "given_hiragana"]]
name_origin_out = name_origin.rename(
    columns={"kanji": "given_kanji", "hiragana": "given_hiragana"}
)[["sex", "given_kanji", "given_hiragana"]]

jpersonwiki["dataset"] = "jpersonwiki"
enamdict_out["dataset"] = "enamdict"
name_origin_out["dataset"] = "name_origin"

dataset = pd.concat([jpersonwiki, enamdict_out, name_origin_out], ignore_index=True)
dataset = dataset[
    [
        "dataset",
        "sex",
        "given_kanji",
        "given_hiragana",
        "family_kanji",
        "family_hiragana",
        "birth_year",
    ]
]
os.makedirs("./dataset", exist_ok=True)
dataset.to_csv("./dataset/jnamegender.csv", index=False)
jpersonwiki.to_csv("./dataset/jpersonwiki.csv", index=False)
enamdict_out.to_csv("./dataset/enamdict.csv", index=False)
name_origin_out.to_csv("./dataset/name_origin.csv", index=False)
# !sync

# %%
for name, df in [
    ("enamdict", enamdict),
    ("jpersonwiki", jpersonwiki),
    ("name_origin", name_origin),
]:
    print(name)
    print(df.head())
