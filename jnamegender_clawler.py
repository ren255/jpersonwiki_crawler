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
# !pip install namedivider-python python-romkan-ng names-dataset

import pandas as pd
import numpy as np
import romkan
import os
from namedivider import BasicNameDivider
from time import time
from typing import List, Tuple, Dict, Callable
import math
import matplotlib.pyplot as plt
import importlib

# %%
import re
import csv

def parse_enamdict(input_path, output_path):
    rows = []
    
    with open(input_path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            # Extract kanji, hiragana, sex, romaji
            match = re.match(r'^(.+?)\s*\[(.+?)\]\s*/\(([mf])\)\s*(.+?)/', line)
            if not match:
                continue
            
            kanji, hiragana, sex, romaji = match.groups()
            rows.append({
                'sex': sex,
                'kanji': kanji,
                'hiragana': hiragana,
                'romaji': romaji.strip()
            })
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['sex', 'kanji', 'hiragana', 'romaji'])
        writer.writeheader()
        writer.writerows(rows)

def parse_name_origin_to_flat_csv(sex, input_path, output_path):
    rows = []
    
    with open(input_path, encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split(',')
            if len(parts) < 3:
                continue
            hiragana, romaji, *kanjis = parts
            for kanji in kanjis:
                rows.append({'kanji': kanji, 'hiragana': hiragana, 'romaji': romaji, 'sex': sex})
    
    pd.DataFrame(rows).to_csv(output_path, index=False)



# %%
# https://github.com/rgamici/japanese-names
# !curl --create-dirs -o ./intermidiate/enumdict_male.txt "https://raw.githubusercontent.com/rgamici/japanese-names/refs/heads/master/male"
# !curl --create-dirs -o ./intermidiate/enumdict_female.txt "https://raw.githubusercontent.com/rgamici/japanese-names/refs/heads/master/female"
# !sync

parse_enamdict("./intermidiate/enumdict_male.txt","./intermidiate/enumdict_male.csv")
parse_enamdict("./intermidiate/enumdict_female.txt","./intermidiate/enumdict_female.csv")
# !sync

enamdict_male = pd.read_csv("./intermidiate/enumdict_male.csv")
enamdict_female = pd.read_csv("./intermidiate/enumdict_female.csv")
enamdict = pd.concat([enamdict_male, enamdict_female])

# https://github.com/shuheilocale/japanese-personal-name-dataset
# !curl --create-dirs -o ./intermidiate/name_origin_male.txt "https://raw.githubusercontent.com/shuheilocale/japanese-personal-name-dataset/refs/heads/main/japanese_personal_name_dataset/dataset/first_name_man_org.csv"
# !curl --create-dirs -o ./intermidiate/name_origin_female.txt "https://raw.githubusercontent.com/shuheilocale/japanese-personal-name-dataset/refs/heads/main/japanese_personal_name_dataset/dataset/first_name_woman_org.csv"
# !sync

parse_name_origin_to_flat_csv("male","./intermidiate/name_origin_male.txt","./intermidiate/name_origin_male.csv")
parse_name_origin_to_flat_csv("female","./intermidiate/name_origin_female.txt","./intermidiate/name_origin_female.csv")
# !sync

name_origin_male = pd.read_csv("./intermidiate/name_origin_male.csv")
name_origin_female = pd.read_csv("./intermidiate/name_origin_female.csv")
name_origin = pd.concat([name_origin_male, name_origin_female])

splits = {'train': 'gendec-train.csv', 'validation': 'gendec-dev.csv', 'test': 'gendec-test.csv'}
gendec = pd.concat([
    pd.read_csv("hf://datasets/tarudesu/gendec-dataset/" + path)
    for path in splits.values()
])

wiki = pd.read_csv("/kaggle/input/datasets/rentoda/japanese-names-with-gender/data.csv")
facebook = pd.read_csv(
    "/kaggle/input/datasets/rentoda/facebook-533m-user-leak/name_dataset/data/JP.csv",
    header=None,
    names=['first', 'last', 'gender', 'country']
)


enamdict.columns = ["sex", "kanji", "hiragana", "romaji"]
wiki.columns = ['sex', 'kanji', 'hiragana', 'pageid', 'birth_year', 'blood_type',
       'height', 'weight', 'occupation', 'education', 'birth_place',
       'birth_date', 'nationality']
name_origin.columns = ["kanji", "hiragana", "romaji", "sex"]
gendec.columns = ['Gender', 'Kanji', 'Higarana', 'Romaji']
facebook.columns = ["first_name", "last_name", "sex", "country"]


# %%
def preprocess_gendec(df: pd.DataFrame) -> pd.DataFrame:
    basic_divider = BasicNameDivider()
    divided = df["Kanji"].apply(lambda x: basic_divider.divide_name(x))
    romaji_parts = df["Romaji"].str.split()
    df["family_kanji"] = divided.apply(lambda x: x.family)
    df["given_kanji"] = divided.apply(lambda x: x.given)
    full_hira = df["Romaji"].apply(romkan.to_hiragana).str.split()
    df["family_hiragana"] = full_hira.str[0]
    df["given_hiragana"] = full_hira.str[1]
    df["sex"] = df["Gender"].str.lower()
    return df[["sex", "given_kanji", "given_hiragana", "family_kanji", "family_hiragana"]]

def preprocess_facebook(df: pd.DataFrame) -> pd.DataFrame:
    """日本語が含まれない名前はすべて排除"""
    df = df.copy()
    df.loc[df["sex"] == "M", "sex"] = "male"
    df.loc[df["sex"] == "F", "sex"] = "female"
    df = df.dropna(subset=["first_name", "sex"])

    def to_hira_or_none(name):
        if not isinstance(name, str):
            return None, None
        h = romkan.to_hiragana(name)
        if re.search(r"[a-zA-Z]", h):
            return None, name if re.fullmatch(r"[一-龯]+", name) else None
        if re.fullmatch(r"[ぁ-んー]+", h):
            return h, None
        return None, h if re.fullmatch(r"[一-龯]+", h) else None

    given = df["first_name"].apply(to_hira_or_none)
    df["given_hiragana"] = given.apply(lambda x: x[0])
    df["given_kanji"] = given.apply(lambda x: x[1])

    family = df["last_name"].apply(to_hira_or_none)
    df["family_hiragana"] = family.apply(lambda x: x[0])
    df["family_kanji"] = family.apply(lambda x: x[1])

    return df[["sex", "given_kanji", "given_hiragana", "family_kanji", "family_hiragana"]]

def preprocess_wiki(df: pd.DataFrame) -> pd.DataFrame:
    basic_divider = BasicNameDivider()
    divided = df["kanji"].apply(lambda x: basic_divider.divide_name(str(x)))
    hira_parts = df["hiragana"].str.split()
    df["family_kanji"] = divided.apply(lambda x: x.family)
    df["given_kanji"] = divided.apply(lambda x: x.given)
    df["family_hiragana"] = hira_parts.str[0]
    df["given_hiragana"] = hira_parts.str[1]
    return df[["sex", "given_kanji", "given_hiragana", "family_kanji", "family_hiragana", "birth_year"]]

wiki["birth_year"] = pd.to_numeric(wiki["birth_year"], errors="coerce").astype("Int64")
facebook = preprocess_facebook(facebook)
gendec = preprocess_gendec(gendec)
wiki = preprocess_wiki(wiki)

# given nameのみのデータセット
enamdict_out = enamdict.rename(columns={"kanji": "given_kanji", "hiragana": "given_hiragana"})[["sex", "given_kanji", "given_hiragana"]]
name_origin_out = name_origin.rename(columns={"kanji": "given_kanji", "hiragana": "given_hiragana"})[["sex", "given_kanji", "given_hiragana"]]

enamdict_out["sex"] = enamdict_out["sex"].replace({"m": "male", "f": "female"})

wiki["dataset"] = "wiki"
facebook["dataset"] = "facebook"
gendec["dataset"] = "gendec"
enamdict_out["dataset"] = "enamdict"
name_origin_out["dataset"] = "name_origin"

dataset = pd.concat([wiki, facebook, gendec, enamdict_out, name_origin_out], ignore_index=True)
dataset = dataset[["dataset", "sex", "given_kanji", "given_hiragana", "family_kanji", "family_hiragana", "birth_year"]]
dataset.to_csv("dataset.csv", index=False)

os.makedirs("./data", exist_ok=True)
wiki.to_csv("./data/wiki.csv", index=False)
facebook.to_csv("./data/facebook.csv", index=False)
gendec.to_csv("./data/gendec.csv", index=False)
enamdict_out.to_csv("./data/enamdict.csv", index=False)
name_origin_out.to_csv("./data/name_origin.csv", index=False)
# !sync

# %%
for name, df in [("enamdict", enamdict), ("wiki", wiki), ("name_origin", name_origin), ("gendec", gendec), ("facebook", facebook)]:
    print(name)
    print(df.head())

# %%
from names_dataset import NameDataset, NameWrapper

nd = NameDataset()

def get_name_stats(name):
    result = nd.search(name)
    if not result or not result.get('first_name'):
        return None
    fn = result['first_name']
    gender = fn.get('gender', {})
    ranks = fn.get('rank', {})
    return {
        'male': gender.get('Male', None),
        'rank': ranks.get('Japan', None)
    }

# collect unique names from both columns
hiragana_names = dataset["given_hiragana"].dropna().unique()
kanji_names = dataset["given_kanji"].dropna().unique()
all_names = set(hiragana_names) | set(kanji_names)
print(f"processing {len(all_names)} names")

rows = []
hit_count = 0
for name in all_names:
    stats = get_name_stats(name)
    if stats is None:
        continue
    hit_count += 1
    is_hiragana = name in set(hiragana_names)
    is_kanji = name in set(kanji_names)
    rows.append({
        "given_hiragana": name if is_hiragana else None,
        "given_kanji": name if is_kanji else None,
        "male_percentage": stats["male"],
        "rank": stats["rank"]
    })

name_stats = pd.DataFrame(rows)
name_stats = name_stats.dropna(subset=["rank", "male_percentage"])
name_stats.to_csv("./data/name_stats.csv", index=False)
# !sync

print(f"hit rate: {hit_count}/{len(all_names)} ({hit_count/len(all_names)*100:.1f}%)")
