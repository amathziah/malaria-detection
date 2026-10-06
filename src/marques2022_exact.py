"""Exact replication of Marques et al. (2022), EfficientNet-B0 + 10-fold ensemble on the NIH malaria cells.

G. Marques, A. Ferreras, I. de la Torre-Díez, "An ensemble-based approach for automated medical
diagnosis of malaria using EfficientNet", Multimedia Tools and Applications 81, 28061-28078 (2022).

The recipe comes from the paper's own executed code (Springer supplementary file MOESM1, notebook
"efn0_malaria_binary", 30 Jan 2021), not only from the paper text. Section numbers below refer to it.

What is changed for speed only (the maths stays the same):
  * images are decoded and resized once, with the same cv2 calls as ImageDataAugmentor, into a uint8 cache;
  * the paper's albumentations pipeline runs in worker processes, seeded per batch, so batches do not
    depend on the number of workers;
  * batches reach the GPU as uint8 and are divided by 255 inside the model (= rescale=1/255);
  * the training step can be compiled with XLA.

TensorFlow is imported inside functions only, so the augmentation workers stay light.
"""
import hashlib
import itertools
import json
import math
import multiprocessing as mp
import os
import random
import re
import time
from collections import deque

import cv2
import numpy as np
import pandas as pd

TIPOS = ["Parasitized", "Uninfected"]  # os.listdir order in the paper; softmax unit 0 = parasitized

# Section 1.1.2 (parameters), 2.2 (model, callbacks, loss), 2.4 (training) of the paper's code
PAPER = dict(
    SEED=1234,             # SEED
    KFOLD=10,              # KFOLD
    KFOLD_SEED=50,         # StratifiedKFold(KFOLD, shuffle=True, random_state=50)
    EPOCHS=33,             # EPOCHS (no early stopping)
    BATCH_SIZE=16,         # BATCH_SIZE
    IMG_SIZE=224,          # EfficientNetB0 input
    LR=1e-4,               # Adam(0.0001)
    LR_FACTOR=0.5,         # ReduceLROnPlateau(factor=0.5, ...)
    PATIENCE=6,            # PATIENCE
    MIN_LR=1e-6,           # min_lr=0.000001
    LABEL_SMOOTHING=0.1,   # custom_loss
    VAL_FRACTION=0.2,      # train_test_split(df_total, test_size=0.2)
    WEIGHTS="noisy-student",
    DENSE=(128, 64, 32),
    DROPOUT=0.3,
)
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".gif")
NIH_URL = "https://data.lhncbc.nlm.nih.gov/public/Malaria/cell_images.zip"


# ----------------------------------------------------------------------------- data and splits
def build_index(entries, root=None):
    """Table of (file, label) like the paper's df_total, sorted so the split never depends on os.listdir order.

    `cache_idx` is each image's row in the image cache. With `root`, `path` points at root/<label>/<file>
    (NIH layout) or root/<file>.
    """
    df = pd.DataFrame(list(entries), columns=["file", "label"])
    df = df[df["file"].str.lower().str.endswith(IMAGE_EXTENSIONS)]  # the paper deletes Thumbs.db etc.
    df = df.sort_values(["label", "file"]).reset_index(drop=True)
    df["cache_idx"] = np.arange(len(df))
    if root is not None:
        nested = [os.path.join(root, l, f) for f, l in zip(df["file"], df["label"])]
        df["path"] = [p if os.path.exists(p) else os.path.join(root, f) for p, f in zip(nested, df["file"])]
    return df


def index_dataset(root):
    """Index a folder with Parasitized/ and Uninfected/ subfolders (the NIH cell_images layout)."""
    return build_index([(f, label) for label in TIPOS for f in os.listdir(os.path.join(root, label))], root)


def find_or_download(data_dir):
    """Return the cell_images folder, downloading the NIH zip (353 MB) into data_dir if needed."""
    for cand in [data_dir, os.path.join(data_dir, "cell_images")]:
        if all(os.path.isdir(os.path.join(cand, t)) for t in TIPOS):
            return cand
    import urllib.request
    import zipfile
    os.makedirs(data_dir, exist_ok=True)
    zpath = os.path.join(data_dir, "cell_images.zip")
    if not os.path.exists(zpath):
        urllib.request.urlretrieve(NIH_URL, zpath + ".part")
        os.replace(zpath + ".part", zpath)
    with zipfile.ZipFile(zpath) as z:
        z.extractall(data_dir)
    return os.path.join(data_dir, "cell_images")


def paper_split(df, seed=PAPER["SEED"]):
    """80 % learning set for the 10-fold CV, 20 % untouched hold-out set (the paper calls it "validation").

    The paper's call is train_test_split(df_total, test_size=0.2): not stratified, no random_state.
    We keep it unstratified and fix random_state so every machine gets the same split.
    """
    from sklearn.model_selection import train_test_split
    learn, val = train_test_split(df, test_size=PAPER["VAL_FRACTION"], random_state=seed)
    return learn.reset_index(drop=True), val.reset_index(drop=True)


def paper_folds(learn, n_splits=PAPER["KFOLD"], seed=PAPER["KFOLD_SEED"]):
    """(train positions, test positions) for each fold, exactly as the paper's StratifiedKFold loop."""
    from sklearn.model_selection import StratifiedKFold
    kf = StratifiedKFold(n_splits, shuffle=True, random_state=seed)
    return list(kf.split(learn, learn["label"]))


def split_fingerprint(learn, val, folds=None):
    """Short hash of the split, so results from different machines can be checked to share it."""
    h = hashlib.sha1("\n".join(val["file"]).encode() + b"|" + "\n".join(learn["file"]).encode())
    for _, te in folds or []:
        h.update(np.asarray(te, np.int64).tobytes())
    return h.hexdigest()[:16]


def one_hot(labels):
    """pd.get_dummies(label) in TIPOS order, as float32."""
    labels = np.asarray(labels)
    return np.stack([labels == t for t in TIPOS], 1).astype(np.float32)


# ----------------------------------------------------------------------------- images and augmentation
def build_paper_augmentation():
    """Section 2.3 of the paper's code, verbatim (albumentations 0.5.2 + imgaug 0.4.0)."""
    from albumentations import (CLAHE, Blur, Compose, Flip, GaussNoise, GridDistortion,
                                IAAAdditiveGaussianNoise, IAAEmboss, IAAPiecewiseAffine, IAASharpen,
                                MedianBlur, MotionBlur, OneOf, OpticalDistortion, RandomBrightness,
                                RandomContrast, RandomRotate90, ShiftScaleRotate, Transpose)
    return Compose([RandomRotate90(),
                    Flip(),
                    Transpose(),
                    OneOf([IAAAdditiveGaussianNoise(),
                           GaussNoise(), ], p=0.2),
                    OneOf([MotionBlur(p=.2),
                           MedianBlur(blur_limit=3, p=.1),
                           Blur(blur_limit=3, p=.1), ], p=0.3),
                    ShiftScaleRotate(shift_limit=0.0625,
                                     scale_limit=0.2,
                                     rotate_limit=45, p=.2),
                    OneOf([OpticalDistortion(p=0.3),
                           GridDistortion(p=.1),
                           IAAPiecewiseAffine(p=0.3), ], p=0.3),
                    OneOf([CLAHE(clip_limit=2),
                           IAASharpen(),
                           IAAEmboss(),
                           RandomContrast(),
                           RandomBrightness(), ], p=0.3),
                    ], p=1)


def load_resized(path, size=PAPER["IMG_SIZE"]):
    """ImageDataAugmentor.utils.load_img(color_mode='rgb', target_size=(size, size)): cv2, nearest neighbour."""
    img = cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2RGB)
    if img.shape[0:2] != (size, size):
        img = cv2.resize(img, dsize=(size, size), interpolation=cv2.INTER_NEAREST)
    return img


def _decode_into(args):
    cache_path, start, paths = args
    cv2.setNumThreads(1)
    cache = np.load(cache_path, mmap_mode="r+")
    for k, p in enumerate(paths):
        cache[start + k] = load_resized(p, cache.shape[1])
    cache.flush()
    return len(paths)


def build_image_cache(paths, cache_path, workers=None, size=PAPER["IMG_SIZE"]):
    """Decode + resize every image once into a uint8 .npy (27,558 x 224 x 224 x 3 = 4.1 GB for NIH)."""
    np.lib.format.open_memmap(cache_path, mode="w+", dtype=np.uint8, shape=(len(paths), size, size, 3)).flush()
    chunks = [(cache_path, s, list(paths[s:s + 256])) for s in range(0, len(paths), 256)]
    if workers == 0:
        for c in chunks:
            _decode_into(c)
    else:
        with _spawn_pool(workers or available_cpus()) as pool:
            pool.map(_decode_into, chunks)
    return cache_path


def _load_worker_state(cache_path):
    cv2.setNumThreads(1)
    return {"cache": np.load(cache_path, mmap_mode="r"), "aug": build_paper_augmentation()}


_WORKER = {}
# One BLAS/OpenMP thread per worker: otherwise every worker starts a pool sized for the whole host
_SINGLE_THREAD_ENV = {"OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"}


def _worker_env():
    return {k: os.environ.get(k) for k in _SINGLE_THREAD_ENV}


def _spawn_pool(workers, initializer=None, initargs=()):
    """A spawn-context pool whose workers start with _SINGLE_THREAD_ENV (the parent's env is restored)."""
    saved = {k: os.environ.get(k) for k in _SINGLE_THREAD_ENV}
    os.environ.update(_SINGLE_THREAD_ENV)
    try:
        return mp.get_context("spawn").Pool(workers, initializer, initargs)
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def _init_worker(cache_path):
    _WORKER.update(_load_worker_state(cache_path))


def _make_batch(task, state=None):
    """Build one batch. With augmentation, every RNG the paper's pipeline touches is seeded from `seed`."""
    rows, seed, augment = task
    state = state or _WORKER
    cache = state["cache"]
    if not augment:
        return np.asarray(cache[rows])
    import imgaug
    random.seed(seed)
    np.random.seed(seed % 2 ** 32)
    imgaug.random.seed(seed % 2 ** 32)
    out = np.empty((len(rows),) + cache.shape[1:], np.uint8)
    for j, r in enumerate(rows):
        out[j] = state["aug"](image=np.array(cache[r]))["image"]
    return out


class _Ready:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value


class AugmentPool:
    """Processes that build batches from the image cache. workers=0 builds them in this process."""

    def __init__(self, workers, cache_path):
        self.workers, self.cache_path = workers, cache_path
        self._pool = self._state = None

    def __enter__(self):
        if self.workers:
            self._pool = _spawn_pool(self.workers, _init_worker, (self.cache_path,))
        else:
            self._state = _load_worker_state(self.cache_path)
        return self

    def __exit__(self, *exc):
        if self._pool is not None:
            self._pool.terminate()
            self._pool.join()

    def submit(self, task):
        if self._pool is not None:
            return self._pool.apply_async(_make_batch, (task,))
        return _Ready(_make_batch(task, self._state))


def available_cpus(cgroup_file="/sys/fs/cgroup/cpu.max", cgroup_v1_dir="/sys/fs/cgroup/cpu"):
    """CPUs this process may really use. In a container os.cpu_count() shows the whole host:
    a "16 vCPU" RunPod pod sees 32-64 CPUs but its cgroup quota allows 13.6 (cgroup v2 or v1)."""
    n = len(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else os.cpu_count()
    quota = period = None
    try:
        with open(cgroup_file) as fh:  # cgroup v2: "<quota> <period>" or "max <period>"
            q, p = fh.read().split()[:2]
        if q != "max":
            quota, period = int(q), int(p)
    except (OSError, ValueError):
        try:  # cgroup v1: quota is -1 when unlimited
            with open(os.path.join(cgroup_v1_dir, "cpu.cfs_quota_us")) as fq, \
                    open(os.path.join(cgroup_v1_dir, "cpu.cfs_period_us")) as fp:
                q, p = int(fq.read()), int(fp.read())
            if q > 0:
                quota, period = q, p
        except (OSError, ValueError):
            pass
    if quota:
        n = min(n, int(quota / period))
    return max(1, n)


def steps_per_epoch(n, batch_size):
    """The paper trains 1240 steps per epoch (19,841 / 16): full batches only."""
    return n // batch_size


def _batch_seed(seed_key, epoch, b):
    return int(np.random.SeedSequence([*seed_key, epoch, b]).generate_state(1, np.uint64)[0])


def iterate_batches(pool, rows, batch_size, *, augment, shuffle, drop_remainder, seed_key, epoch, prefetch=None):
    """Yield (positions into `rows`, uint8 images) batch by batch, in order, with up to `prefetch` batches in flight.

    Like ImageDataAugmentor's iterator: a new shuffle every epoch and (with augment) a new random
    augmentation of every image, here seeded by (seed_key, epoch, batch number).
    """
    rows = np.asarray(rows)
    order = np.random.default_rng([*seed_key, epoch]).permutation(len(rows)) if shuffle else np.arange(len(rows))
    n_batches = steps_per_epoch(len(rows), batch_size) if drop_remainder else math.ceil(len(rows) / batch_size)
    tasks = ((order[b * batch_size:(b + 1) * batch_size], b) for b in range(n_batches))
    pending = deque()

    def submit(pos, b):
        pending.append((pos, pool.submit((rows[pos], _batch_seed(seed_key, epoch, b), augment))))

    for pos, b in itertools.islice(tasks, prefetch or max(2, 4 * pool.workers)):
        submit(pos, b)
    while pending:
        pos, result = pending.popleft()
        nxt = next(tasks, None)
        if nxt is not None:
            submit(*nxt)
        yield pos, result.get()


class BatchStream:
    """One call = one pass over `rows` (an epoch); feeds tf.data.Dataset.from_generator."""

    def __init__(self, pool, rows, labels, batch_size, *, augment, shuffle, drop_remainder, seed_key):
        self.pool, self.rows, self.labels, self.batch_size = pool, np.asarray(rows), labels, batch_size
        self.kw = dict(augment=augment, shuffle=shuffle, drop_remainder=drop_remainder, seed_key=seed_key)
        self.epoch = 0

    def __len__(self):
        n = len(self.rows)
        return steps_per_epoch(n, self.batch_size) if self.kw["drop_remainder"] else math.ceil(n / self.batch_size)

    def __call__(self):
        epoch, self.epoch = self.epoch, self.epoch + 1
        for pos, x in iterate_batches(self.pool, self.rows, self.batch_size, epoch=epoch, **self.kw):
            yield x, self.labels[pos]


def as_dataset(stream, size=PAPER["IMG_SIZE"]):
    import tensorflow as tf
    ds = tf.data.Dataset.from_generator(stream, output_signature=(
        tf.TensorSpec((None, size, size, 3), tf.uint8), tf.TensorSpec((None, len(TIPOS)), tf.float32)))
    # Known length: Keras then starts a fresh pass (new shuffle + augmentations) every epoch
    return ds.apply(tf.data.experimental.assert_cardinality(len(stream))).prefetch(tf.data.AUTOTUNE)


# ----------------------------------------------------------------------------- model
def build_model(weights=PAPER["WEIGHTS"], size=PAPER["IMG_SIZE"]):
    """Section 2.2 create_model(): EfficientNetB0 (qubvel efficientnet 1.1.1, all layers trainable) + dense head.

    Input is uint8; the first layer divides by 255 (the paper's ImageDataAugmentor(rescale=1/255)).
    """
    import tensorflow as tf
    from efficientnet import model as efn  # efficientnet.tfkeras would inject TF's legacy internal Keras on TF 2.15
    from tensorflow.keras import layers

    keras_modules = dict(backend=tf.keras.backend, layers=tf.keras.layers, models=tf.keras.models, utils=tf.keras.utils)
    # Built on its own and then called: its input_tensor path hard-codes TF's legacy is_keras_tensor
    base = efn.EfficientNetB0(weights=weights, include_top=False, input_shape=(size, size, 3), **keras_modules)
    inp = layers.Input((size, size, 3), dtype="uint8", name="image_uint8")
    x = layers.Rescaling(1 / 255, name="rescale_1_255")(inp)
    x = layers.GlobalAveragePooling2D()(base(x))
    for units in PAPER["DENSE"]:
        x = layers.Dense(units, activation="relu")(x)
        x = layers.Dropout(PAPER["DROPOUT"])(x)
    out = layers.Dense(len(TIPOS), activation="softmax")(x)
    return tf.keras.Model(inputs=inp, outputs=out, name="efficientnetb0_marques2022")


def paper_loss(y_true, y_pred):
    """Section 2.2 custom_loss: categorical cross-entropy with label smoothing 0.1."""
    import tensorflow as tf
    return tf.keras.losses.categorical_crossentropy(y_true, y_pred, label_smoothing=PAPER["LABEL_SMOOTHING"])


def compile_paper_model(model, xla=True, steps_per_execution=1):
    """Adam(1e-4) (the TF 2.3 optimizer, which is tf.keras.optimizers.legacy.Adam in TF 2.15) + accuracy."""
    import tensorflow as tf
    model.compile(optimizer=tf.keras.optimizers.legacy.Adam(PAPER["LR"]), loss=paper_loss,
                  metrics=["accuracy"], steps_per_execution=steps_per_execution)
    model._paper_xla = bool(xla)
    return model


def paper_callbacks(weights_path):
    """Section 2.2 create_callbacks(): halve the LR on a val_loss plateau; keep the best val_loss weights."""
    import tensorflow as tf
    return [tf.keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=PAPER["LR_FACTOR"],
                                                 patience=PAPER["PATIENCE"], min_lr=PAPER["MIN_LR"]),
            tf.keras.callbacks.ModelCheckpoint(weights_path, save_best_only=True, monitor="val_loss",
                                               mode="min", save_freq="epoch", save_weights_only=True)]


def _xla_for_training_only():
    """XLA-compile the train step only. Keras reads model._jit_compile when it traces each step function,
    so evaluation and prediction (which see partial batches) stay uncompiled and never recompile."""
    import tensorflow as tf

    class XlaForTrainingOnly(tf.keras.callbacks.Callback):
        def on_train_begin(self, logs=None):
            self.model._jit_compile = True

        def on_test_begin(self, logs=None):
            self.model._jit_compile = False

        def on_test_end(self, logs=None):
            self.model._jit_compile = True

        def on_train_end(self, logs=None):
            self.model._jit_compile = False

    return XlaForTrainingOnly()


def _epoch_timer():
    import tensorflow as tf

    class EpochTimer(tf.keras.callbacks.Callback):
        def on_train_begin(self, logs=None):
            self.seconds = []

        def on_epoch_begin(self, epoch, logs=None):
            self._t = time.time()

        def on_epoch_end(self, epoch, logs=None):
            self.seconds.append(time.time() - self._t)
            logs["epoch_seconds"] = self.seconds[-1]

    return EpochTimer()


# ----------------------------------------------------------------------------- metrics
def classification_summary(y_true, y_pred, probs=None):
    """What the paper prints with sklearn's classification_report: per class, macro and weighted averages.

    Tables 3/4 are the per-class rows, Tables 5/6 the weighted average. The ROC AUC is the same
    for both classes of a 2-unit softmax.
    """
    from sklearn.metrics import (accuracy_score, confusion_matrix, matthews_corrcoef,
                                 precision_recall_fscore_support, roc_auc_score)
    y_true, y_pred = np.asarray(y_true, int), np.asarray(y_pred, int)
    p, r, f, s = precision_recall_fscore_support(y_true, y_pred, labels=[0, 1], zero_division=0)
    out = {"n": int(len(y_true)), "accuracy": float(accuracy_score(y_true, y_pred))}
    for k, name in enumerate(TIPOS):
        out[name] = {"precision": float(p[k]), "recall": float(r[k]), "f1": float(f[k]), "support": int(s[k])}
    for avg in ("macro", "weighted"):
        pa, ra, fa, _ = precision_recall_fscore_support(y_true, y_pred, labels=[0, 1], average=avg, zero_division=0)
        out[avg] = {"precision": float(pa), "recall": float(ra), "f1": float(fa)}
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])  # rows: true class, columns: predicted, TIPOS order
    out["confusion"] = cm.tolist()
    out["mcc"] = float(matthews_corrcoef(y_true, y_pred))
    if probs is not None:
        out["auc"] = float(roc_auc_score(y_true == 0, np.asarray(probs)[:, 0]))
    return out


def ensemble_probs(fold_probs):
    """Section 2.4: the ensemble averages the 10 models' softmax outputs."""
    return np.mean(np.stack(fold_probs), axis=0)


# ----------------------------------------------------------------------------- one fold
EVAL_SETS = {  # name: (which rows, augmented like the paper's generators?, seed stream)
    "test_aug": ("test", True, 2),     # paper: test_generator came from the augmenting data_gen
    "test_clean": ("test", False, 4),
    "val_aug": ("val", True, 3),       # paper: val_generator too
    "val_clean": ("val", False, 5),
}


def _jsonable(o):
    if isinstance(o, dict):
        return {k: _jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_jsonable(v) for v in o]
    if isinstance(o, np.generic):
        return o.item()
    return o


def train_fold(fold, *, learn, val, folds, pool, out_dir, weights=PAPER["WEIGHTS"], xla=True,
               epochs=PAPER["EPOCHS"], batch_size=PAPER["BATCH_SIZE"], steps_per_execution=1,
               max_steps_per_epoch=None, verbose=2):
    """Train one fold like the paper's section 2.4 loop and evaluate it on its test part and on the hold-out set.

    Saves fold_<k>/fold_<k>_best.h5 (best val_loss weights), fold_<k>_predictions.npz and fold_<k>.json.
    """
    import tensorflow as tf
    tr, te = folds[fold]
    df_train, df_test = learn.iloc[tr], learn.iloc[te]
    fold_dir = os.path.join(out_dir, f"fold_{fold}")
    os.makedirs(fold_dir, exist_ok=True)

    tf.keras.backend.clear_session()
    seed = PAPER["SEED"] + fold
    random.seed(seed)
    np.random.seed(seed)
    tf.random.set_seed(seed)
    model = compile_paper_model(build_model(weights), xla=xla, steps_per_execution=steps_per_execution)

    key = (PAPER["SEED"], fold)
    y = {"train": one_hot(df_train["label"]), "test": one_hot(df_test["label"]), "val": one_hot(val["label"])}
    rows = {"train": df_train["cache_idx"].values, "test": df_test["cache_idx"].values, "val": val["cache_idx"].values}
    train_stream = BatchStream(pool, rows["train"], y["train"], batch_size, augment=True, shuffle=True,
                               drop_remainder=True, seed_key=key + (0,))
    # Validation during training = the fold's test part, through the same augmenting generator (paper)
    val_stream = BatchStream(pool, rows["test"], y["test"], batch_size, augment=True, shuffle=False,
                             drop_remainder=False, seed_key=key + (1,))
    steps = len(train_stream) if max_steps_per_epoch is None else min(len(train_stream), max_steps_per_epoch)
    train_ds = as_dataset(train_stream)
    if steps != len(train_stream):  # smoke runs only
        train_ds = train_ds.take(steps).apply(tf.data.experimental.assert_cardinality(steps))

    weights_path = os.path.join(fold_dir, f"fold_{fold}_best.h5")
    timer = _epoch_timer()
    callbacks = paper_callbacks(weights_path) + [timer] + ([_xla_for_training_only()] if xla else [])
    t0 = time.time()
    hist = model.fit(train_ds, epochs=epochs, steps_per_epoch=steps, validation_data=as_dataset(val_stream),
                     validation_steps=len(val_stream), callbacks=callbacks, verbose=verbose)
    train_seconds = time.time() - t0
    history = {k: [float(v) for v in vals] for k, vals in hist.history.items()}
    best_epoch = int(np.argmin(history["val_loss"])) + 1

    model.load_weights(weights_path)  # paper: model.load_weights('model_{fold}.hdf5')
    probs, metrics, t1 = {}, {}, time.time()
    for name, (part, augment, stream_id) in EVAL_SETS.items():
        s = BatchStream(pool, rows[part], y[part], batch_size, augment=augment, shuffle=False,
                        drop_remainder=False, seed_key=key + (stream_id,))
        probs[name] = model.predict(as_dataset(s), steps=len(s), verbose=0).astype(np.float64)
        metrics[name] = classification_summary(y[part].argmax(1), probs[name].argmax(1), probs[name])
    eval_seconds = time.time() - t1

    gpus = tf.config.list_physical_devices("GPU")
    record = dict(fold=fold, best_epoch=best_epoch, epochs=len(history["loss"]), steps_per_epoch=steps,
                  batch_size=batch_size, train_seconds=train_seconds, eval_seconds=eval_seconds,
                  epoch_seconds=timer.seconds, history=history, metrics=metrics,
                  n_train=len(df_train), n_test=len(df_test), n_val=len(val),
                  split_fingerprint=split_fingerprint(learn, val, folds), xla=bool(xla),
                  steps_per_execution=steps_per_execution, weights=weights,
                  tensorflow=tf.__version__,
                  gpu=[tf.config.experimental.get_device_details(g).get("device_name") for g in gpus])
    save_fold_outputs(out_dir, record, probs, test_files=df_test["file"].values, val_files=val["file"].values,
                      test_true=y["test"].argmax(1), val_true=y["val"].argmax(1))
    del model
    return dict(record, probs=probs, weights_path=weights_path)


def save_fold_outputs(out_dir, record, probs, *, test_files, val_files, test_true, val_true):
    """fold_<k>/fold_<k>.json (history, timings, metrics) + fold_<k>_predictions.npz (softmax outputs)."""
    fold_dir = os.path.join(out_dir, f"fold_{record['fold']}")
    os.makedirs(fold_dir, exist_ok=True)
    np.savez_compressed(os.path.join(fold_dir, f"fold_{record['fold']}_predictions.npz"),  # str, not object: no pickle
                        test_files=np.asarray(test_files, dtype=str), val_files=np.asarray(val_files, dtype=str),
                        test_true=np.asarray(test_true), val_true=np.asarray(val_true), **probs)
    with open(os.path.join(fold_dir, f"fold_{record['fold']}.json"), "w") as fh:
        json.dump(_jsonable(record), fh, indent=1)


# ----------------------------------------------------------------------------- all folds -> paper tables
# From the paper and its executed code (MOESM1). Each list is folds 0-9.
PAPER_RESULTS = dict(
    # Table 5: each fold model on its own CV test part (accuracy)
    cv_accuracy=[0.974603, 0.977324, 0.976871, 0.974603, 0.973243, 0.974150, 0.976407, 0.983666, 0.970508, 0.975045],
    # Each fold model on the 5,512-image hold-out set: accuracy printed by the code. (Table 6's "accuracy"
    # column is (precision + recall) / 2 of these reports; its mean is 97.70 instead of 97.69.)
    holdout_accuracy=[0.977141, 0.978774, 0.973875, 0.978229, 0.979499, 0.973331, 0.977866, 0.978229, 0.976415,
                      0.975508],
    holdout_auc=[0.996143, 0.997121, 0.996094, 0.996904, 0.996379, 0.996098, 0.996798, 0.996274, 0.996893, 0.996243],
    # Ensemble on the hold-out set, from the printed report (2744 parasitized: 62 missed; 2768 uninfected: 32 flagged).
    # The paper's text swaps the parasitized precision and recall ("recall 98.82 %, precision 97.74 %").
    ensemble=dict(accuracy=0.982946, recall=0.977405, precision=0.988209, f1=0.982778, specificity=0.988439,
                  auc=0.9976),
)


def _pct(x):
    return round(100 * float(x), 2)


def _binary(m):
    """Parasitized = positive class, in %, the way results/A0_baseline reports it."""
    (tp, fn), (fp, tn) = m["confusion"]
    return dict(accuracy=100 * m["accuracy"], precision=100 * m["Parasitized"]["precision"],
                recall=100 * m["Parasitized"]["recall"], specificity=100 * m["Uninfected"]["recall"],
                f1=100 * m["Parasitized"]["f1"], auc=100 * m.get("auc", float("nan")), mcc=100 * m["mcc"],
                TP=int(tp), TN=int(tn), FP=int(fp), FN=int(fn))


def load_fold(fold_dir):
    k = int(os.path.basename(os.path.normpath(fold_dir)).split("_")[-1])
    with open(os.path.join(fold_dir, f"fold_{k}.json")) as fh:
        record = json.load(fh)
    with np.load(os.path.join(fold_dir, f"fold_{k}_predictions.npz"), allow_pickle=False) as z:
        record["npz"] = {key: z[key] for key in z.files}
    return record


def aggregate(folds_dir, n_folds=PAPER["KFOLD"]):
    """Rebuild the paper's per-fold tables and the 10-model ensemble from the saved fold outputs.

    Two views: "paper" = predictions on augmented images, as the paper's code produced them;
    "clean" = the same models on un-augmented images.
    """
    records = [load_fold(os.path.join(folds_dir, f"fold_{k}")) for k in range(n_folds)]
    if len({r["split_fingerprint"] for r in records}) != 1:
        raise ValueError("folds were trained on different splits: " + str([r["split_fingerprint"] for r in records]))
    val_files = records[0]["npz"]["val_files"]
    if not all(np.array_equal(r["npz"]["val_files"], val_files) for r in records):
        raise ValueError("folds disagree on the hold-out set")
    val_true = records[0]["npz"]["val_true"]

    per_fold, ensemble, ens_probs = {}, {}, {}
    for proto, suffix in [("paper", "aug"), ("clean", "clean")]:
        rows = []
        for r in records:
            cv, ho = r["metrics"][f"test_{suffix}"], r["metrics"][f"val_{suffix}"]
            rows.append(dict(fold=r["fold"], epochs=r["epochs"], best_epoch=r["best_epoch"],
                             minutes=round(r["train_seconds"] / 60, 1), gpu=(r.get("gpu") or ["?"])[0],
                             **{f"cv_{k}": v for k, v in _binary(cv).items()},
                             cv_weighted_precision=100 * cv["weighted"]["precision"],
                             cv_weighted_recall=100 * cv["weighted"]["recall"], cv_weighted_f1=100 * cv["weighted"]["f1"],
                             cv_uninfected_precision=100 * cv["Uninfected"]["precision"],
                             cv_uninfected_f1=100 * cv["Uninfected"]["f1"],
                             **{f"holdout_{k}": v for k, v in _binary(ho).items()},
                             holdout_weighted_precision=100 * ho["weighted"]["precision"],
                             holdout_weighted_f1=100 * ho["weighted"]["f1"]))
        per_fold[proto] = pd.DataFrame(rows)
        ens_probs[proto] = ensemble_probs([r["npz"][f"val_{suffix}"] for r in records])
        ensemble[proto] = classification_summary(val_true, ens_probs[proto].argmax(1), ens_probs[proto])

    pr = PAPER_RESULTS
    rows = [("Mean CV-fold accuracy (Table 5)", np.mean(pr["cv_accuracy"]), "cv_accuracy"),
            ("Mean single-model hold-out accuracy (Table 6)", np.mean(pr["holdout_accuracy"]), "holdout_accuracy"),
            ("Mean single-model hold-out ROC-AUC (Table 6)", np.mean(pr["holdout_auc"]), "holdout_auc")]
    comparison = [dict(Metric=name, Paper=_pct(p), **{f"Ours ({proto})": round(per_fold[proto][col].mean(), 2)
                                                       for proto in per_fold}) for name, p, col in rows]
    for name, key in [("Ensemble accuracy", "accuracy"), ("Ensemble recall (parasitized)", "recall"),
                      ("Ensemble precision (parasitized)", "precision"), ("Ensemble F1 (parasitized)", "f1"),
                      ("Ensemble specificity (uninfected recall)", "specificity"), ("Ensemble ROC-AUC", "auc")]:
        comparison.append(dict(Metric=name, Paper=_pct(pr["ensemble"][key]),
                               **{f"Ours ({proto})": round(_binary(ensemble[proto])[key], 2) for proto in ensemble}))
    comparison = pd.DataFrame(comparison)
    comparison["Δ paper protocol (pp)"] = (comparison["Ours (paper)"] - comparison["Paper"]).round(2)

    all_files = set(val_files.tolist()).union(*[r["npz"]["test_files"].tolist() for r in records])
    return dict(records=records, per_fold=per_fold, ensemble=ensemble, ens_probs=ens_probs, val_true=val_true,
                comparison=comparison, n_folds=n_folds, n_images=len(all_files),
                n_slides=len({re.match(r"^(C\d+)", f).group(1) if re.match(r"^(C\d+)", f) else f.split("_")[0]
                              for f in all_files}),
                split_fingerprint=records[0]["split_fingerprint"])


def write_results(agg, out_dir, prefix="A0_10fold"):
    """CSV/JSON files in the layout of results/A0_baseline, so src/check_results.py can read them."""
    os.makedirs(out_dir, exist_ok=True)
    cols = ["accuracy", "precision", "recall", "specificity", "f1", "auc", "mcc"]
    paths = []
    for proto, df in agg["per_fold"].items():
        name = f"{prefix}_per_fold_val.csv" if proto == "paper" else f"{prefix}_per_fold_val_clean.csv"
        cv = df[["fold", "epochs", "best_epoch", "minutes", "gpu"] + [f"cv_{c}" for c in cols]].rename(
            columns=lambda c: c[3:] if c.startswith("cv_") else c)
        cv.to_csv(os.path.join(out_dir, name), index=False)
        name = f"{prefix}_per_model_test.csv" if proto == "paper" else f"{prefix}_per_model_test_clean.csv"
        ho = df[["fold"] + [f"holdout_{c}" for c in cols]].rename(columns=lambda c: c.replace("holdout_", ""))
        ho.to_csv(os.path.join(out_dir, name), index=False)
    agg["comparison"].to_csv(os.path.join(out_dir, f"{prefix}_vs_paper.csv"), index=False)

    paper_df = agg["per_fold"]["paper"]
    cv_cols = [f"cv_{c}" for c in cols]
    summary = dict(
        experiment=prefix, split="image (paper: 20 % hold-out + stratified 10-fold)",
        preprocess="none (paper's albumentations augmentation)",
        config=dict(N_FOLDS=agg["n_folds"], **{k: v for k, v in PAPER.items()}),
        n_images=agg["n_images"], n_slides=agg["n_slides"], folds_run=len(agg["records"]),
        split_fingerprint=agg["split_fingerprint"],
        mean_fold={c: round(paper_df[f"cv_{c}"].mean(), 2) for c in cols},
        sd_fold={c: round(paper_df[f"cv_{c}"].std(ddof=1) if len(paper_df) > 1 else 0.0, 2) for c in cols},
        holdout_mean={c: round(paper_df[f"holdout_{c}"].mean(), 2) for c in cols},
        ensemble={k: (round(v, 2) if isinstance(v, float) else v) for k, v in _binary(agg["ensemble"]["paper"]).items()},
        ensemble_clean={k: (round(v, 2) if isinstance(v, float) else v)
                        for k, v in _binary(agg["ensemble"]["clean"]).items()},
        mean_fold_clean={c: round(agg["per_fold"]["clean"][f"cv_{c}"].mean(), 2) for c in cols},
        paper=dict(mean_fold_accuracy=_pct(np.mean(PAPER_RESULTS["cv_accuracy"])),
                   holdout_mean_accuracy=_pct(np.mean(PAPER_RESULTS["holdout_accuracy"])),
                   **{k: _pct(v) for k, v in PAPER_RESULTS["ensemble"].items() if k != "specificity"},
                   specificity=_pct(PAPER_RESULTS["ensemble"]["specificity"])),
        minutes_per_fold=paper_df["minutes"].tolist(), gpus=paper_df["gpu"].tolist(),
        notes="paper protocol = evaluation on augmented images, as in the paper's code; *_clean = un-augmented",
    )
    with open(os.path.join(out_dir, f"{prefix}_summary.json"), "w") as fh:
        json.dump(_jsonable(summary), fh, indent=2, default=str)
    return summary
