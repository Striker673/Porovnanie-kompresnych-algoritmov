import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "results")
CSV_PATH = os.path.join(RESULTS_DIR, "benchmark_results.csv")

COLORS = {
    "Huffman": "#2196F3",
    "LZW": "#4CAF50",
    "RLE": "#FF9800",
    "RLE+Huffman": "#9C27B0",
    "LZW+Huffman": "#E91E63",
}

CATEGORY_LABELS = {
    "Canterbury Corpus": "Canterbury",
    "The Standard Calgary Corpus": "Calgary",
    "images": "Obrazky",
    "large": "Velke (GB)",
}


def load_results():
    return pd.read_csv(CSV_PATH)


def _save(fig, name):
    path = os.path.join(RESULTS_DIR, name)
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Ulozeny: {path}")


def plot_compression_ratio_by_category(df):
    fig, ax = plt.subplots(figsize=(12, 6))

    categories = df["category"].unique()
    algorithms = df["algorithm"].unique()
    x = np.arange(len(categories))
    width = 0.8 / len(algorithms)

    for i, algo in enumerate(algorithms):
        means = [df[(df["algorithm"] == algo) & (df["category"] == cat)]["compression_ratio"].mean()
                 for cat in categories]
        bars = ax.bar(x + i * width, means, width, label=algo, color=COLORS.get(algo, "#999"))
        for bar, val in zip(bars, means):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                    f"{val:.1f}%", ha="center", va="bottom", fontsize=8)

    ax.set_xlabel("Kategoria dat")
    ax.set_ylabel("Kompresny pomer (%)")
    ax.set_title("Priemerny kompresny pomer podla kategorie dat")
    ax.set_xticks(x + width)
    ax.set_xticklabels([CATEGORY_LABELS.get(c, c) for c in categories])
    ax.legend()
    ax.axhline(y=0, color="black", linewidth=0.5, linestyle="--")
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    _save(fig, "compression_ratio_by_category.png")


def plot_compression_ratio_by_file(df):
    fig, ax = plt.subplots(figsize=(16, 8))

    files = df["file"].unique()
    algorithms = df["algorithm"].unique()
    x = np.arange(len(files))
    width = 0.25

    for i, algo in enumerate(algorithms):
        values = []
        for f in files:
            subset = df[(df["algorithm"] == algo) & (df["file"] == f)]
            values.append(subset["compression_ratio"].values[0] if len(subset) > 0 else 0)
        ax.bar(x + i * width, values, width, label=algo, color=COLORS.get(algo, "#999"))

    ax.set_xlabel("Subor")
    ax.set_ylabel("Kompresny pomer (%)")
    ax.set_title("Kompresny pomer pre jednotlive subory")
    ax.set_xticks(x + width)
    ax.set_xticklabels(files, rotation=45, ha="right", fontsize=8)
    ax.legend()
    ax.axhline(y=0, color="black", linewidth=0.5, linestyle="--")
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    _save(fig, "compression_ratio_by_file.png")


def plot_speed_comparison(df):
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    categories = df["category"].unique()
    algorithms = df["algorithm"].unique()
    x = np.arange(len(categories))
    width = 0.25

    for plot_idx, (col, title, ylabel) in enumerate([
        ("avg_compress_time", "Priemerny cas kompresie", "Cas kompresie (ms)"),
        ("avg_decompress_time", "Priemerny cas dekompresie", "Cas dekompresie (ms)"),
    ]):
        for i, algo in enumerate(algorithms):
            means = [df[(df["algorithm"] == algo) & (df["category"] == cat)][col].mean() * 1000
                     for cat in categories]
            axes[plot_idx].bar(x + i * width, means, width, label=algo, color=COLORS.get(algo, "#999"))

        axes[plot_idx].set_xlabel("Kategoria dat")
        axes[plot_idx].set_ylabel(ylabel)
        axes[plot_idx].set_title(title)
        axes[plot_idx].set_xticks(x + width)
        axes[plot_idx].set_xticklabels([CATEGORY_LABELS.get(c, c) for c in categories])
        axes[plot_idx].legend()
        axes[plot_idx].grid(axis="y", alpha=0.3)

    plt.tight_layout()
    _save(fig, "speed_comparison.png")


def plot_overall_summary(df):
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    algorithms = df["algorithm"].unique()
    colors = [COLORS.get(a, "#999") for a in algorithms]

    ratios = [df[df["algorithm"] == a]["compression_ratio"].mean() for a in algorithms]
    bars = axes[0].bar(algorithms, ratios, color=colors)
    axes[0].set_ylabel("Kompresny pomer (%)")
    axes[0].set_title("Celkovy priemerny\nkompresny pomer")
    axes[0].axhline(y=0, color="black", linewidth=0.5, linestyle="--")
    for bar, val in zip(bars, ratios):
        axes[0].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                     f"{val:.1f}%", ha="center", fontsize=10)

    for idx, (col, title) in enumerate([("avg_compress_time", "Priemerny cas\nkompresie"),
                                         ("avg_decompress_time", "Priemerny cas\ndekompresie")], start=1):
        speeds = [df[df["algorithm"] == a][col].mean() * 1000 for a in algorithms]
        bars = axes[idx].bar(algorithms, speeds, color=colors)
        axes[idx].set_ylabel("Cas (ms)")
        axes[idx].set_title(title)
        for bar, val in zip(bars, speeds):
            axes[idx].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                           f"{val:.1f}ms", ha="center", fontsize=10)

    for ax in axes:
        ax.grid(axis="y", alpha=0.3)
        ax.tick_params(axis="x", rotation=20)

    plt.tight_layout()
    _save(fig, "overall_summary.png")


def plot_boxplot_ratios(df):
    fig, ax = plt.subplots(figsize=(10, 6))

    algorithms = df["algorithm"].unique()
    data = [df[df["algorithm"] == a]["compression_ratio"].values for a in algorithms]

    bp = ax.boxplot(data, labels=algorithms, patch_artist=True)
    for patch, algo in zip(bp["boxes"], algorithms):
        patch.set_facecolor(COLORS.get(algo, "#999"))
        patch.set_alpha(0.7)

    ax.set_ylabel("Kompresny pomer (%)")
    ax.set_title("Rozptyl kompresneho pomeru podla algoritmu")
    ax.axhline(y=0, color="black", linewidth=0.5, linestyle="--")
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    _save(fig, "boxplot_compression_ratio.png")


def plot_memory_usage(df):
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    algorithms = df["algorithm"].unique()
    colors = [COLORS.get(a, "#999") for a in algorithms]

    for idx, (col, title) in enumerate([
        ("max_compress_memory_mb", "Priemerna pamatova narocnost\nkompresie"),
        ("max_decompress_memory_mb", "Priemerna pamatova narocnost\ndekompresie"),
    ]):
        mem = [df[df["algorithm"] == a][col].mean() for a in algorithms]
        bars = axes[idx].bar(algorithms, mem, color=colors)
        axes[idx].set_ylabel("Pamat (MB)")
        axes[idx].set_title(title)
        axes[idx].grid(axis="y", alpha=0.3)
        for bar, val in zip(bars, mem):
            axes[idx].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
                           f"{val:.2f}", ha="center", va="bottom", fontsize=9)

    plt.tight_layout()
    _save(fig, "memory_usage.png")


def generate_summary_table(df):
    summary = df.groupby(["algorithm", "category"]).agg({
        "compression_ratio": "mean",
        "avg_compress_time": "mean",
        "avg_decompress_time": "mean",
        "original_size": "sum",
        "compressed_size": "sum",
    }).round(4)
    summary["avg_compress_time_ms"] = summary["avg_compress_time"] * 1000
    summary["avg_decompress_time_ms"] = summary["avg_decompress_time"] * 1000

    path = os.path.join(RESULTS_DIR, "summary_table.csv")
    summary.to_csv(path, encoding="utf-8")
    print(f"Ulozeny: {path}")

    overall = df.groupby("algorithm").agg({
        "compression_ratio": "mean",
        "avg_compress_time": "mean",
        "avg_decompress_time": "mean",
    }).round(4)
    overall["avg_compress_time_ms"] = overall["avg_compress_time"] * 1000
    overall["avg_decompress_time_ms"] = overall["avg_decompress_time"] * 1000

    path2 = os.path.join(RESULTS_DIR, "overall_summary_table.csv")
    overall.to_csv(path2, encoding="utf-8")
    print(f"Ulozeny: {path2}")


def main():
    print("=== Vizualizacia vysledkov ===\n")

    if not os.path.exists(CSV_PATH):
        print(f"Subor {CSV_PATH} neexistuje. Najprv spustite benchmark.py")
        return

    df = load_results()
    print(f"Nacitanych {len(df)} zaznamov\n")

    plot_compression_ratio_by_category(df)
    plot_compression_ratio_by_file(df)
    plot_speed_comparison(df)
    plot_overall_summary(df)
    plot_boxplot_ratios(df)
    plot_memory_usage(df)
    generate_summary_table(df)

    print(f"\nVsetky grafy a tabulky ulozene v: {RESULTS_DIR}")


if __name__ == "__main__":
    main()
