# Malaria Cell Detection — Phase 2: reproduction of Marques et al. (2022)
# Plain-script version of Phase2_Baseline_Reproduction_Marques2022.ipynb.
# Run on any cloud GPU terminal:   pip install tensorflow scikit-learn pandas matplotlib kagglehub
#                                   python phase2_baseline_marques2022.py
# In VS Code, the "# %%" markers also let you run it cell-by-cell (Python Interactive).
import matplotlib
try:
    get_ipython  # noqa: F821  (running interactively)
except NameError:
    matplotlib.use("Agg")      # plain script: save figures to files instead of opening windows
    def display(obj):          # notebook-style display() fallback
        print(obj.to_string() if hasattr(obj, "to_string") else obj)


# %% [markdown]
# # Automated Malaria Cell Detection — Phase 2, Milestone 2
# ## Reproducing the base paper: Marques *et al.* (2022), EfficientNet-B0 with stratified k-fold and ensembling
# 
# **Team:** Pugazhendhi J (230066) · J Amathziah (230139) · C Murali Madhav (230115) · Ravi Yadav (230131)
# **Base paper:** G. Marques, A. Ferreras, I. de la Torre-Díez, "An ensemble-based approach for automated medical diagnosis of malaria using EfficientNet," *Multimedia Tools and Applications*, 81, 28061–28078, 2022.
# 
# ### What this notebook does
# 1. Loads the **NIH Malaria Cell Images Dataset** (27,558 single-cell images, parasitized vs. uninfected).
# 2. Rebuilds the base paper's recipe: **ImageNet-pretrained EfficientNet-B0**, **Adam (lr = 1e-4)**, **ReduceLROnPlateau (patience 6, down to 1e-6)**, **stratified 10-fold cross-validation**, and an **ensemble that averages the fold models**.
# 3. Reports the same metrics as the paper (accuracy, precision, recall, F1, ROC-AUC) plus specificity and MCC, and puts them **next to the paper's numbers**.
# 4. Sets up the code for our Phase 2 hypotheses (patient/slide-level split, YUV stain normalisation). These experiments are **switched off by default**. We run them in the next milestone.
# 
# ### Targets from the paper
# | Metric | Marques et al. (2022) |
# |---|---|
# | Mean single-fold accuracy | **97.70 %** |
# | 10-model ensemble accuracy | **98.29 %** |
# | Ensemble recall (sensitivity) | 98.82 % |
# | Ensemble precision | 97.74 % |
# | Ensemble F1 | 98.28 % |
# | Ensemble ROC-AUC | 99.76 % |
# 
# ### How to run it
# * **Kaggle (recommended):** New Notebook → *File → Import Notebook* → upload this file. Then *Add Input* → search **"cell-images-for-detecting-malaria"** (by *iarunava*) → add it. *Settings → Accelerator → GPU T4 ×2 (or P100)*. Click **Run All**.
# * **VS Code + free Colab GPU:** install the official **Google Colab** extension in VS Code → open this `.ipynb` → *Select Kernel → Colab → New Colab Server → GPU (T4)* → sign in with Google → **Run All**. Files are saved on the Colab machine (not your laptop); download `phase2_results.zip` at the end.
# * **Google Colab (browser):** *Runtime → Change runtime type → T4 GPU*. Run All. The dataset downloads automatically (from the NIH, or from Kaggle through `kagglehub`).
# * **Runtime:** about 6–9 min per fold on a T4. The default `FOLDS_TO_RUN = 3` takes about 25–30 min. Set it to `10` for the full paper protocol (about 1.5 h).

# %% [markdown]
# ## 1 · Setup and configuration

# %%
import os, re, glob, json, time, random, math, shutil, subprocess, warnings
warnings.filterwarnings("ignore")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import tensorflow as tf
from sklearn.model_selection import StratifiedKFold, StratifiedGroupKFold, train_test_split
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
                             roc_auc_score, matthews_corrcoef, confusion_matrix, roc_curve)

print("TensorFlow:", tf.__version__)
print("GPUs:", tf.config.list_physical_devices("GPU"))

# %%
# ---------------- CONFIG (edit here) ----------------
CFG = dict(
    SEED            = 42,
    IMG_SIZE        = 224,     # EfficientNet-B0's native input size
    BATCH_SIZE      = 64,
    EPOCHS          = 15,      # max epochs per fold (early stopping usually ends sooner)
    LR              = 1e-4,    # paper: Adam, initial lr 1e-4
    MIN_LR          = 1e-6,    # paper: ReduceLROnPlateau decays down to 1e-6
    PLATEAU_PATIENCE= 6,       # paper: patience of 6 epochs
    PLATEAU_FACTOR  = 0.1,
    EARLY_STOP_PATIENCE = 5,   # our addition, to fit a free GPU budget (restores best weights)
    N_FOLDS         = 10,      # paper: stratified 10-fold CV
    FOLDS_TO_RUN    = 3,       # set to 10 for the full protocol (≈1.5 h on a T4)
    TEST_FRACTION   = 0.10,    # untouched hold-out set, used to evaluate the ensemble
    DROPOUT         = 0.2,
    AUGMENT         = True,    # light, label-preserving flips/rotations
    MIXED_PRECISION = True,
    SAVE_MODELS     = True,
    # ---- Phase 2 hypothesis experiments (off for Milestone 2) ----
    RUN_A1_SLIDE_SPLIT = False,   # H1: same model, leakage-free slide/patient-grouped split
    RUN_A2_YUV_SLIDE   = False,   # H2: + YUV histogram-equalisation stain normalisation
    RUN_A3_YUV_IMAGE   = False,   # control: YUV on the paper's image-level split
)

# Offline code test only (we used this to check the pipeline on dummy images). Leave it off.
SMOKE_TEST = os.environ.get("MALARIA_SMOKE_TEST") == "1"
if SMOKE_TEST:
    CFG.update(IMG_SIZE=64, BATCH_SIZE=16, EPOCHS=2, N_FOLDS=3, FOLDS_TO_RUN=2,
               MIXED_PRECISION=False, RUN_A1_SLIDE_SPLIT=True, RUN_A2_YUV_SLIDE=True, RUN_A3_YUV_IMAGE=True)

def set_seed(s):
    random.seed(s); np.random.seed(s); tf.random.set_seed(s)
    os.environ["PYTHONHASHSEED"] = str(s)
set_seed(CFG["SEED"])

OUT_DIR = "/kaggle/working/outputs" if os.path.isdir("/kaggle/working") else "outputs"
os.makedirs(OUT_DIR, exist_ok=True)

gpus = tf.config.list_physical_devices("GPU")
for g in gpus:
    try: tf.config.experimental.set_memory_growth(g, True)
    except Exception: pass
if CFG["MIXED_PRECISION"] and gpus:
    tf.keras.mixed_precision.set_global_policy("mixed_float16")
STRATEGY = tf.distribute.MirroredStrategy() if len(gpus) > 1 else tf.distribute.get_strategy()
GLOBAL_BATCH = CFG["BATCH_SIZE"] * STRATEGY.num_replicas_in_sync
print("Replicas:", STRATEGY.num_replicas_in_sync, "| global batch:", GLOBAL_BATCH, "| outputs →", OUT_DIR)

# %% [markdown]
# ## 2 · Get the dataset
# The code looks for the dataset in this order:
# 1. A Kaggle input folder (`/kaggle/input/...`).
# 2. A local `cell_images/` folder.
# 3. A download through `kagglehub`.
# 4. A direct download from the NIH (`cell_images.zip`, about 350 MB).

# %%
def find_root(base):
    # Return a folder that has 'Parasitized' and 'Uninfected' subfolders, if one exists under base.
    for dirpath, dirnames, _ in os.walk(base):
        if "Parasitized" in dirnames and "Uninfected" in dirnames:
            return dirpath
    return None

def make_dummy_dataset(root, n_per_class=60):
    # SMOKE_TEST only: random images that copy the NIH file-naming pattern.
    import PIL.Image as Image
    rng = np.random.default_rng(0)
    for cls in ["Parasitized", "Uninfected"]:
        os.makedirs(f"{root}/{cls}", exist_ok=True)
        for i in range(n_per_class):
            slide = rng.integers(1, 13)
            name = (f"C{slide}P{slide+60}thinF_IMG_2015_{i}_cell_{i}.png" if cls == "Parasitized"
                    else f"C{slide}NThinF_IMG_2015_{i}_cell_{i}.png")
            arr = rng.integers(0, 255, (rng.integers(100, 150), rng.integers(100, 150), 3), dtype=np.uint8)
            if cls == "Parasitized": arr[40:60, 40:60] = [90, 20, 120]   # a fake "parasite" blob
            Image.fromarray(arr).save(f"{root}/{cls}/{name}")
    return root

DATA_ROOT = None
if SMOKE_TEST:
    DATA_ROOT = make_dummy_dataset("dummy_cell_images")
for cand in ["/kaggle/input", "cell_images", "/content/cell_images"]:
    if DATA_ROOT is None and os.path.isdir(cand):
        DATA_ROOT = find_root(cand)
if DATA_ROOT is None:
    try:
        import kagglehub
        DATA_ROOT = find_root(kagglehub.dataset_download("iarunava/cell-images-for-detecting-malaria"))
    except Exception as e:
        print("kagglehub not available / failed:", e)
if DATA_ROOT is None:
    url = "https://data.lhncbc.nlm.nih.gov/public/Malaria/cell_images.zip"
    print("Downloading from NIH:", url)
    import urllib.request, zipfile
    if not os.path.exists("cell_images.zip"):
        urllib.request.urlretrieve(url, "cell_images.zip")
    with zipfile.ZipFile("cell_images.zip") as z:
        z.extractall(".")
    DATA_ROOT = find_root(".")
assert DATA_ROOT, "Dataset not found — add the Kaggle input 'cell-images-for-detecting-malaria'."
print("Dataset root:", DATA_ROOT)

# %% [markdown]
# ### Build the image index
# Each file name carries a slide/patient code, for example `C33P1thinF_IMG_..._cell_179.png`. We pull out the `C<number>` part as a **slide ID**. Milestone 2 does not use it, because the base paper splits at the image level. It is what our hypothesis H1 needs: a split where no slide appears in both training and testing.
# 
# The Kaggle copy of the dataset contains a duplicated nested folder and some `Thumbs.db` files. We keep only unique `.png` files.

# %%
rows = []
for label_name, y in [("Parasitized", 1), ("Uninfected", 0)]:
    for p in glob.glob(os.path.join(DATA_ROOT, label_name, "**", "*.png"), recursive=True):
        rows.append((p, os.path.basename(p), label_name, y))
df = pd.DataFrame(rows, columns=["path", "fname", "class", "label"])
df = df.drop_duplicates(subset=["class", "fname"]).reset_index(drop=True)

def slide_id(fname):
    m = re.match(r"^(C\d+)", fname)
    return m.group(1) if m else fname.split("_")[0]
df["slide"] = df["fname"].map(slide_id)

print(f"Total images: {len(df):,}  (paper / NIH: 27,558)")
print(df["class"].value_counts().to_string())
print(f"Distinct slide IDs: {df['slide'].nunique()}")

# %%
# A look at the data: top row parasitized, bottom row uninfected
fig, axes = plt.subplots(2, 8, figsize=(16, 4.4))
for r, cls in enumerate(["Parasitized", "Uninfected"]):
    sample = df[df["class"] == cls].sample(8, random_state=CFG["SEED"])
    for c, p in enumerate(sample["path"]):
        axes[r, c].imshow(plt.imread(p)); axes[r, c].axis("off")
    axes[r, 0].set_title(cls, loc="left", fontsize=12, fontweight="bold")
plt.tight_layout(); plt.savefig(f"{OUT_DIR}/samples.png", dpi=120); plt.show()

sizes = np.array([plt.imread(p).shape[:2] for p in df.sample(min(300, len(df)), random_state=0)["path"]])
print("Raw crop height/width (sample): min", sizes.min(0), "max", sizes.max(0), "→ resized to", CFG["IMG_SIZE"])

# %% [markdown]
# ## 3 · Input pipeline
# * Read the PNG → **resize to 224×224** → pixel values stay in 0–255. Keras' EfficientNet does its own rescaling and normalisation inside the model.
# * **Augmentation** (training only): random horizontal/vertical flips and 90° rotations. A blood cell has no "up", so these never change the label. The paper used the Albumentations library but doesn't list the exact transforms, so this is our closest faithful choice.
# * `preprocess="yuv"` turns on the **YUV histogram-equalisation** stain normalisation from Umer *et al.* [4]. That's hypothesis H2, and it stays off for the baseline.

# %%
AUTOTUNE = tf.data.AUTOTUNE

def tf_yuv_hist_eq(img_uint8):
    # RGB → YUV, histogram-equalise the brightness (Y) channel, → RGB. Same as OpenCV's equalizeHist on Y.
    x = tf.cast(img_uint8, tf.float32) / 255.0
    yuv = tf.image.rgb_to_yuv(x)
    y = yuv[..., 0]
    y8 = tf.cast(tf.clip_by_value(tf.round(y * 255.0), 0, 255), tf.int32)
    hist = tf.math.bincount(tf.reshape(y8, [-1]), minlength=256, maxlength=256)
    cdf = tf.cumsum(hist)
    cdf_min = tf.reduce_min(tf.boolean_mask(cdf, cdf > 0))
    n = tf.size(y8)
    denom = tf.maximum(n - cdf_min, 1)
    lut = tf.cast(tf.round(tf.cast(cdf - cdf_min, tf.float32) * 255.0 / tf.cast(denom, tf.float32)), tf.float32)
    lut = tf.clip_by_value(lut, 0, 255)
    y_eq = tf.gather(lut, y8) / 255.0
    yuv = tf.stack([y_eq, yuv[..., 1], yuv[..., 2]], axis=-1)
    rgb = tf.clip_by_value(tf.image.yuv_to_rgb(yuv), 0.0, 1.0)
    return tf.cast(tf.round(rgb * 255.0), tf.uint8)

def load_image(path, preprocess="none"):
    img = tf.io.decode_png(tf.io.read_file(path), channels=3)
    if preprocess == "yuv":
        img = tf_yuv_hist_eq(img)
    img = tf.image.resize(img, [CFG["IMG_SIZE"], CFG["IMG_SIZE"]], antialias=True)
    return img  # float32, 0–255

def augment(img):
    img = tf.image.random_flip_left_right(img)
    img = tf.image.random_flip_up_down(img)
    k = tf.random.uniform([], 0, 4, dtype=tf.int32)
    return tf.image.rot90(img, k)

def make_ds(paths, labels, training, preprocess="none"):
    ds = tf.data.Dataset.from_tensor_slices((paths, labels.astype("float32")))
    if training:
        ds = ds.shuffle(len(paths), seed=CFG["SEED"], reshuffle_each_iteration=True)
    ds = ds.map(lambda p, y: (load_image(p, preprocess), y), num_parallel_calls=AUTOTUNE)
    if training and CFG["AUGMENT"]:
        ds = ds.map(lambda x, y: (augment(x), y), num_parallel_calls=AUTOTUNE)
    return ds.batch(GLOBAL_BATCH).prefetch(AUTOTUNE)

# %%
# Visual check of the H2 preprocessing (not used by the baseline)
demo = df.groupby("class").sample(3, random_state=1)
fig, axes = plt.subplots(2, 6, figsize=(15, 5.2))
for i, p in enumerate(demo["path"]):
    raw = tf.io.decode_png(tf.io.read_file(p), channels=3)
    axes[0, i].imshow(raw.numpy()); axes[0, i].set_title(demo.iloc[i]["class"], fontsize=9); axes[0, i].axis("off")
    axes[1, i].imshow(tf_yuv_hist_eq(raw).numpy()); axes[1, i].axis("off")
axes[0, 0].set_ylabel("raw"); axes[1, 0].set_ylabel("YUV + hist-eq")
fig.suptitle("Top: raw RGB    Bottom: YUV histogram-equalised (hypothesis H2 input)", fontsize=12)
plt.tight_layout(); plt.savefig(f"{OUT_DIR}/yuv_preview.png", dpi=120); plt.show()

# %% [markdown]
# ## 4 · Model: EfficientNet-B0 (ImageNet-pretrained)
# EfficientNet-B0 backbone (about 4 M parameters without its classifier) → global average pooling → dropout → **one sigmoid output** (probability that the cell is parasitized). We fine-tune the whole network with Adam at a learning rate of 1e-4 and binary cross-entropy loss, as the paper does.

# %%
WEIGHTS = None if SMOKE_TEST else "imagenet"   # offline test cannot download ImageNet weights

def build_model():
    with STRATEGY.scope():
        inp = tf.keras.Input((CFG["IMG_SIZE"], CFG["IMG_SIZE"], 3))
        base = tf.keras.applications.EfficientNetB0(include_top=False, weights=WEIGHTS, input_tensor=inp)
        x = tf.keras.layers.GlobalAveragePooling2D()(base.output)
        x = tf.keras.layers.Dropout(CFG["DROPOUT"])(x)
        out = tf.keras.layers.Dense(1, activation="sigmoid", dtype="float32")(x)
        model = tf.keras.Model(inp, out, name="effnetb0_malaria")
        model.compile(optimizer=tf.keras.optimizers.Adam(CFG["LR"]),
                      loss="binary_crossentropy",
                      metrics=["accuracy", tf.keras.metrics.AUC(name="auc")])
    return model

m = build_model()
print(f"Trainable parameters: {m.count_params():,}")
del m; tf.keras.backend.clear_session()

# %% [markdown]
# ## 5 · Evaluation helpers

# %%
def metrics_from_probs(y_true, prob, thr=0.5):
    y_pred = (prob >= thr).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    return dict(
        accuracy    = accuracy_score(y_true, y_pred) * 100,
        precision   = precision_score(y_true, y_pred, zero_division=0) * 100,
        recall      = recall_score(y_true, y_pred, zero_division=0) * 100,     # sensitivity
        specificity = tn / max(tn + fp, 1) * 100,
        f1          = f1_score(y_true, y_pred, zero_division=0) * 100,
        auc         = roc_auc_score(y_true, prob) * 100 if len(np.unique(y_true)) > 1 else float("nan"),
        mcc         = matthews_corrcoef(y_true, y_pred) * 100,
        TP=int(tp), TN=int(tn), FP=int(fp), FN=int(fn),
    )

def predict(model, ds):
    return model.predict(ds, verbose=0).ravel().astype("float64")

# %% [markdown]
# ## 6 · Experiment runner
# A single function covers the baseline and both hypothesis experiments:
# * `split="image"`: the paper's protocol. A stratified hold-out test set (10 %), then **stratified 10-fold CV** on the remaining 90 %.
# * `split="slide"`: the leakage-free version (H1). Test set and folds are built with **StratifiedGroupKFold** on the slide ID, so no slide is ever in both training and testing.
# 
# For each fold we train, score the fold's own validation part (the paper's "per-fold accuracy"), and score the **hold-out test set**. The **ensemble** averages the test-set probabilities of all trained fold models.

# %%
def make_splits(df, split):
    y, groups = df["label"].values, df["slide"].values
    idx = np.arange(len(df))
    if split == "image":
        pool_idx, test_idx = train_test_split(idx, test_size=CFG["TEST_FRACTION"], stratify=y, random_state=CFG["SEED"])
        kf = StratifiedKFold(CFG["N_FOLDS"], shuffle=True, random_state=CFG["SEED"])
        folds = [(pool_idx[a], pool_idx[b]) for a, b in kf.split(pool_idx, y[pool_idx])]
    elif split == "slide":
        n_test_splits = max(2, round(1 / CFG["TEST_FRACTION"]))
        outer = StratifiedGroupKFold(n_test_splits, shuffle=True, random_state=CFG["SEED"])
        pool_idx, test_idx = next(outer.split(idx, y, groups))
        kf = StratifiedGroupKFold(CFG["N_FOLDS"], shuffle=True, random_state=CFG["SEED"])
        folds = [(pool_idx[a], pool_idx[b]) for a, b in kf.split(pool_idx, y[pool_idx], groups[pool_idx])]
        assert not set(groups[test_idx]) & set(groups[pool_idx]), "slide leakage between test and train!"
    else:
        raise ValueError(split)
    return test_idx, folds

def run_experiment(name, split="image", preprocess="none"):
    print(f"\n{'='*70}\n{name}  |  split={split}  preprocess={preprocess}\n{'='*70}")
    test_idx, folds = make_splits(df, split)
    test_ds = make_ds(df.path.values[test_idx], df.label.values[test_idx], False, preprocess)
    y_test = df.label.values[test_idx]
    print(f"hold-out test: {len(test_idx):,} images | pool split into {CFG['N_FOLDS']} folds | running {CFG['FOLDS_TO_RUN']}")
    fold_rows, test_rows, test_probs, histories = [], [], [], []
    for k, (tr, va) in enumerate(folds[:CFG["FOLDS_TO_RUN"]]):
        set_seed(CFG["SEED"] + k)
        tf.keras.backend.clear_session()
        model = build_model()
        tr_ds = make_ds(df.path.values[tr], df.label.values[tr], True, preprocess)
        va_ds = make_ds(df.path.values[va], df.label.values[va], False, preprocess)
        cbs = [
            tf.keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=CFG["PLATEAU_FACTOR"],
                                                 patience=CFG["PLATEAU_PATIENCE"], min_lr=CFG["MIN_LR"], verbose=1),
            tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=CFG["EARLY_STOP_PATIENCE"],
                                             restore_best_weights=True, verbose=1),
        ]
        t0 = time.time()
        h = model.fit(tr_ds, validation_data=va_ds, epochs=CFG["EPOCHS"], callbacks=cbs, verbose=2)
        mins = (time.time() - t0) / 60
        histories.append(h.history)
        va_m = metrics_from_probs(df.label.values[va], predict(model, va_ds))
        p_test = predict(model, test_ds); test_probs.append(p_test)
        te_m = metrics_from_probs(y_test, p_test)
        fold_rows.append(dict(fold=k + 1, epochs=len(h.history["loss"]), minutes=round(mins, 1), **va_m))
        test_rows.append(dict(fold=k + 1, **te_m))
        print(f"Fold {k+1}: val acc {va_m['accuracy']:.2f}% | test acc {te_m['accuracy']:.2f}% | {mins:.1f} min")
        if CFG["SAVE_MODELS"]:
            model.save(f"{OUT_DIR}/{name}_fold{k+1}.keras")
        del model
    ens_prob = np.mean(test_probs, axis=0)
    res = dict(name=name, split=split, preprocess=preprocess,
               folds=pd.DataFrame(fold_rows), test_per_model=pd.DataFrame(test_rows),
               ensemble=metrics_from_probs(y_test, ens_prob), y_test=y_test,
               test_probs=test_probs, ens_prob=ens_prob, histories=histories)
    res["folds"].to_csv(f"{OUT_DIR}/{name}_per_fold_val.csv", index=False)
    res["test_per_model"].to_csv(f"{OUT_DIR}/{name}_per_model_test.csv", index=False)
    return res

# %% [markdown]
# ## 7 · Run the baseline (Milestone 2)

# %%
RESULTS = {}
RESULTS["A0_baseline"] = run_experiment("A0_baseline", split="image", preprocess="none")

# %% [markdown]
# ## 8 · Results: the reproduced baseline vs. the paper

# %%
PAPER = dict(mean_fold_accuracy=97.70, accuracy=98.29, recall=98.82, precision=97.74, f1=98.28, auc=99.76)
COLS = ["accuracy", "precision", "recall", "specificity", "f1", "auc", "mcc"]

def summarise(res):
    f = res["folds"]
    print(f"Per-fold validation metrics ({len(f)} of {CFG['N_FOLDS']} folds):")
    display(f[["fold", "epochs", "minutes"] + COLS].round(2))
    mean, std = f[COLS].mean(), f[COLS].std(ddof=1) if len(f) > 1 else f[COLS].std() * 0
    print("Mean ± SD over folds:")
    display(pd.DataFrame({"mean": mean, "sd": std}).T.round(2))
    print("Each fold model on the hold-out test set:")
    display(res["test_per_model"][["fold"] + COLS].round(2))
    print(f"ENSEMBLE of {len(f)} fold models on the hold-out test set:")
    display(pd.DataFrame([res["ensemble"]]).round(2))
    return mean, std

mean, std = summarise(RESULTS["A0_baseline"])
ens = RESULTS["A0_baseline"]["ensemble"]

comparison = pd.DataFrame([
    ("Mean single-fold accuracy", PAPER["mean_fold_accuracy"], mean["accuracy"]),
    ("Ensemble accuracy",          PAPER["accuracy"],  ens["accuracy"]),
    ("Ensemble recall",            PAPER["recall"],    ens["recall"]),
    ("Ensemble precision",         PAPER["precision"], ens["precision"]),
    ("Ensemble F1",                PAPER["f1"],        ens["f1"]),
    ("Ensemble ROC-AUC",           PAPER["auc"],       ens["auc"]),
], columns=["Metric", "Paper (%)", "Ours (%)"])
comparison["Δ (ours − paper)"] = comparison["Ours (%)"] - comparison["Paper (%)"]
comparison.to_csv(f"{OUT_DIR}/A0_vs_paper.csv", index=False)
display(comparison.round(2))

# %%
res = RESULTS["A0_baseline"]
fig, axes = plt.subplots(1, 3, figsize=(17, 4.6))

# (a) training curves
for k, h in enumerate(res["histories"]):
    axes[0].plot(h["accuracy"], ls="--", alpha=.7, label=f"fold {k+1} train")
    axes[0].plot(h["val_accuracy"], alpha=.9, label=f"fold {k+1} val")
axes[0].set_title("Accuracy per epoch"); axes[0].set_xlabel("epoch"); axes[0].legend(fontsize=7, ncol=2)

# (b) ensemble confusion matrix
cm = confusion_matrix(res["y_test"], (res["ens_prob"] >= .5).astype(int), labels=[0, 1])
axes[1].imshow(cm, cmap="Blues")
for (i, j), v in np.ndenumerate(cm):
    axes[1].text(j, i, f"{v:,}", ha="center", va="center", fontsize=14,
                 color="white" if v > cm.max() / 2 else "black")
axes[1].set_xticks([0, 1], ["Uninfected", "Parasitized"]); axes[1].set_yticks([0, 1], ["Uninfected", "Parasitized"])
axes[1].set_xlabel("Predicted"); axes[1].set_ylabel("True"); axes[1].set_title("Ensemble confusion matrix (test)")

# (c) ROC curves
for k, p in enumerate(res["test_probs"]):
    fpr, tpr, _ = roc_curve(res["y_test"], p); axes[2].plot(fpr, tpr, alpha=.5, label=f"fold {k+1}")
fpr, tpr, _ = roc_curve(res["y_test"], res["ens_prob"])
axes[2].plot(fpr, tpr, lw=2.5, color="black", label=f"ensemble (AUC {res['ensemble']['auc']:.2f}%)")
axes[2].plot([0, 1], [0, 1], ls=":", color="grey"); axes[2].set_xlim(0, .3); axes[2].set_ylim(.7, 1.01)
axes[2].set_title("ROC (test, zoomed)"); axes[2].set_xlabel("FPR"); axes[2].set_ylabel("TPR"); axes[2].legend(fontsize=8)
plt.tight_layout(); plt.savefig(f"{OUT_DIR}/A0_curves_cm_roc.png", dpi=140); plt.show()

# (d) paper vs ours bar chart
fig, ax = plt.subplots(figsize=(10, 4))
xs = np.arange(len(comparison)); w = .38
ax.bar(xs - w/2, comparison["Paper (%)"], w, label="Marques et al. (2022)", color="#9FC0C9")
ax.bar(xs + w/2, comparison["Ours (%)"], w, label="Our reproduction", color="#137C8E")
for x, v in zip(xs + w/2, comparison["Ours (%)"]): ax.text(x, v + .05, f"{v:.2f}", ha="center", fontsize=8)
ax.set_xticks(xs, comparison["Metric"], rotation=15, fontsize=9)
ax.set_ylim(min(94, comparison[["Paper (%)", "Ours (%)"]].min().min() - 1), 100.3)
ax.set_ylabel("%"); ax.legend(); ax.set_title("Baseline reproduction vs. reported results (axis starts above 0)")
plt.tight_layout(); plt.savefig(f"{OUT_DIR}/A0_vs_paper.png", dpi=140); plt.show()

# %% [markdown]
# ### How to read the comparison
# * **Within about ±1 percentage point of the paper** counts as a successful reproduction. The paper doesn't publish everything: the exact augmentations, the classifier-head details, the batch size and the epoch count are missing, so small gaps are expected.
# * With `FOLDS_TO_RUN < 10`, the ensemble has fewer members than the paper's 10. That usually costs a fraction of a point of ensemble accuracy. The *mean single-fold accuracy* is the fairest one-to-one comparison.
# * **Known deviations from the paper** (put these in the report):
#   1. Early stopping (patience 5, best weights restored) and a 15-epoch cap, to fit a free GPU budget.
#   2. Flip/rotate augmentation in place of the paper's unspecified Albumentations pipeline.
#   3. The ensemble is scored on a 10 % stratified hold-out set that no fold model ever trained on.
#   4. Folds actually run: `CFG['FOLDS_TO_RUN']` out of 10.

# %% [markdown]
# ## 9 · (Next milestone) Hypothesis experiments
# Both are switched off for Milestone 2. Set the flags in the config to `True` to run them later. Each experiment changes **one thing** relative to the experiment it is compared with:
# 
# | ID | Split | Preprocessing | Tests |
# |---|---|---|---|
# | A0 | image-level (paper) | none | baseline (above) |
# | A1 | **slide-grouped** | none | **H1**: does accuracy drop once leakage is removed? |
# | A2 | slide-grouped | **YUV + hist-eq** | **H2**: does stain normalisation recover cross-slide generalisation? (compare with A1) |
# | A3 | image-level | YUV + hist-eq | control: is the gain specific to unseen slides? (compare with A0) |

# %%
if CFG["RUN_A1_SLIDE_SPLIT"]:
    RESULTS["A1_slide_split"] = run_experiment("A1_slide_split", split="slide", preprocess="none")
if CFG["RUN_A2_YUV_SLIDE"]:
    RESULTS["A2_yuv_slide"] = run_experiment("A2_yuv_slide", split="slide", preprocess="yuv")
if CFG["RUN_A3_YUV_IMAGE"]:
    RESULTS["A3_yuv_image"] = run_experiment("A3_yuv_image", split="image", preprocess="yuv")

if len(RESULTS) > 1:
    tab = []
    for name, r in RESULTS.items():
        f = r["folds"]
        tab.append(dict(experiment=name, split=r["split"], preprocess=r["preprocess"],
                        fold_acc_mean=f["accuracy"].mean(), fold_acc_sd=f["accuracy"].std(ddof=1),
                        fold_recall_mean=f["recall"].mean(), fold_mcc_mean=f["mcc"].mean(),
                        ens_test_acc=r["ensemble"]["accuracy"], ens_test_mcc=r["ensemble"]["mcc"]))
    ablation = pd.DataFrame(tab).round(2); ablation.to_csv(f"{OUT_DIR}/ablation.csv", index=False)
    display(ablation)
else:
    print("Hypothesis experiments are off (Milestone 2 = baseline only).")

# %% [markdown]
# ## 10 · Save a summary (paste these numbers into the slides and report)

# %%
r = RESULTS["A0_baseline"]
summary = dict(config=CFG, n_images=int(len(df)), n_slides=int(df.slide.nunique()),
               folds_run=int(len(r["folds"])),
               mean_fold=r["folds"][COLS].mean().round(2).to_dict(),
               sd_fold=(r["folds"][COLS].std(ddof=1) if len(r["folds"]) > 1 else r["folds"][COLS].std()*0).round(2).to_dict(),
               ensemble={k: (round(v, 2) if isinstance(v, float) else v) for k, v in r["ensemble"].items()},
               paper=PAPER)
with open(f"{OUT_DIR}/A0_summary.json", "w") as fh:
    json.dump(summary, fh, indent=2, default=str)

print("SLIDE TABLE (copy into the 'Reproduction results' slide)")
print(f"| Metric | Paper | Ours |")
print(f"| Mean single-fold accuracy | 97.70 | {summary['mean_fold']['accuracy']:.2f} ± {summary['sd_fold']['accuracy']:.2f} |")
for k, lab in [("accuracy", "Ensemble accuracy"), ("recall", "Recall"), ("precision", "Precision"), ("f1", "F1"), ("auc", "ROC-AUC")]:
    print(f"| {lab} | {PAPER[k]:.2f} | {summary['ensemble'][k]:.2f} |")
print(f"| MCC (not reported in paper) | — | {summary['ensemble']['mcc']:.2f} |")
print(f"\nFolds run: {summary['folds_run']} of {CFG['N_FOLDS']}  ·  outputs in {OUT_DIR}/")

# Bundle the results (CSVs, plots, JSON; not the model files) into one zip to download
import zipfile
with zipfile.ZipFile("phase2_results.zip", "w") as z:
    for f in os.listdir(OUT_DIR):
        if not f.endswith(".keras"):
            z.write(os.path.join(OUT_DIR, f), f)
print("Results bundle:", os.path.abspath("phase2_results.zip"))

# %% [markdown]
# ## 11 · Conclusion (fill in after running)
# * **Reproduction:** our EfficientNet-B0 reached a mean single-fold accuracy of **__ %** (paper: 97.70 %) and an ensemble accuracy of **__ %** (paper: 98.29 %) on the NIH dataset. That is within **__ pp** of the reported results, so this is our **Phase 2 baseline**.
# * **Why it matters for our hypothesis:** the paper (like this reproduction) splits **images** at random, so cells from the same slide can land in both training and testing. Our hypotheses test what happens once that leakage is removed (H1), and whether YUV stain normalisation closes the gap (H2).
