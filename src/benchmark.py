import os
import sys
import time
import hashlib
import csv
import statistics

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    print("WARN: psutil nie je nainstalovany, meranie pamate nebude dostupne")

sys.path.insert(0, os.path.dirname(__file__))
import huffman
import lzw
import rle
import hybrid

NUM_REPEATS = 15
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "results")

ALGORITHMS = {
    "Huffman": (huffman.compress, huffman.decompress),
    "LZW": (lzw.compress, lzw.decompress),
    "RLE": (rle.compress, rle.decompress),
    "RLE+Huffman": (hybrid.compress_rle_huffman, hybrid.decompress_rle_huffman),
    "LZW+Huffman": (hybrid.compress_lzw_huffman, hybrid.decompress_lzw_huffman),
}

DATA_CATEGORIES = {
    "Canterbury Corpus": "Canterbury Corpus",
    "The Standard Calgary Corpus": "Calgary Corpus (Standard)",
    "The Large Calgary Corpus": "Calgary Corpus (Large)",
}


def get_memory_mb():
    if HAS_PSUTIL:
        return psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
    return 0.0


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def measure(compress_fn, decompress_fn, data, repeats=NUM_REPEATS):
    original_size = len(data)
    original_hash = sha256(data)

    comp_times = []
    decomp_times = []
    comp_mem = []
    decomp_mem = []
    compressed_size = 0
    integrity_ok = True

    for _ in range(repeats):
        mem_before = get_memory_mb()
        t0 = time.perf_counter()
        compressed = compress_fn(data)
        t1 = time.perf_counter()
        mem_after = get_memory_mb()

        comp_times.append(t1 - t0)
        comp_mem.append(max(0, mem_after - mem_before))
        compressed_size = len(compressed)

        mem_before = get_memory_mb()
        t0 = time.perf_counter()
        decompressed = decompress_fn(compressed)
        t1 = time.perf_counter()
        mem_after = get_memory_mb()

        decomp_times.append(t1 - t0)
        decomp_mem.append(max(0, mem_after - mem_before))

        if sha256(decompressed) != original_hash:
            integrity_ok = False

    avg_comp = statistics.mean(comp_times)
    avg_decomp = statistics.mean(decomp_times)

    ratio = ((original_size - compressed_size) / original_size * 100) if original_size > 0 else 0
    comp_speed = (original_size / (1024 * 1024)) / avg_comp if avg_comp > 0 else 0
    decomp_speed = (original_size / (1024 * 1024)) / avg_decomp if avg_decomp > 0 else 0

    return {
        "original_size": original_size,
        "compressed_size": compressed_size,
        "compression_ratio": round(ratio, 2),
        "avg_compress_time": round(avg_comp, 6),
        "avg_decompress_time": round(avg_decomp, 6),
        "std_compress_time": round(statistics.stdev(comp_times), 6) if len(comp_times) > 1 else 0,
        "std_decompress_time": round(statistics.stdev(decomp_times), 6) if len(decomp_times) > 1 else 0,
        "compress_speed_mbps": round(comp_speed, 2),
        "decompress_speed_mbps": round(decomp_speed, 2),
        "max_compress_memory_mb": round(max(comp_mem), 2),
        "max_decompress_memory_mb": round(max(decomp_mem), 2),
        "integrity": integrity_ok,
    }


def collect_test_files():
    files = {}
    for category in DATA_CATEGORIES:
        cat_dir = os.path.join(DATA_DIR, category)
        if not os.path.isdir(cat_dir):
            continue
        files[category] = []
        for fname in sorted(os.listdir(cat_dir)):
            fpath = os.path.join(cat_dir, fname)
            if os.path.isfile(fpath):
                files[category].append((fname, fpath))
    return files


def run_benchmarks():
    os.makedirs(RESULTS_DIR, exist_ok=True)

    test_files = collect_test_files()
    all_results = []

    print("=" * 80)
    print("BENCHMARK KOMPRESNYCH ALGORITMOV")
    print("=" * 80)
    print(f"Pocet opakovani: {NUM_REPEATS}\n")

    for category, cat_label in DATA_CATEGORIES.items():
        if category not in test_files or not test_files[category]:
            print(f"[SKIP] {cat_label}: ziadne subory")
            continue

        print(f"\n--- {cat_label} ---")

        for fname, fpath in test_files[category]:
            with open(fpath, "rb") as f:
                data = f.read()

            print(f"\n  {fname} ({len(data) / 1024:.1f} KB)")

            for algo_name, (comp_fn, decomp_fn) in ALGORITHMS.items():
                try:
                    metrics = measure(comp_fn, decomp_fn, data)
                    status = "OK" if metrics["integrity"] else "FAIL"
                    print(
                        f"    {algo_name:10s} | "
                        f"Pomer: {metrics['compression_ratio']:6.1f}% | "
                        f"Komp: {metrics['avg_compress_time']*1000:8.2f}ms | "
                        f"Dek: {metrics['avg_decompress_time']*1000:8.2f}ms | "
                        f"Integrita: {status}"
                    )
                    all_results.append({
                        "category": category,
                        "category_label": cat_label,
                        "file": fname,
                        "algorithm": algo_name,
                        **metrics,
                    })
                except Exception as e:
                    print(f"    {algo_name:10s} | CHYBA: {e}")
                    all_results.append({
                        "category": category,
                        "category_label": cat_label,
                        "file": fname,
                        "algorithm": algo_name,
                        "error": str(e),
                    })

    return all_results


def export_csv(results, filepath):
    if not results:
        return

    fieldnames = [
        "category", "category_label", "file", "algorithm",
        "original_size", "compressed_size", "compression_ratio",
        "avg_compress_time", "avg_decompress_time",
        "std_compress_time", "std_decompress_time",
        "compress_speed_mbps", "decompress_speed_mbps",
        "max_compress_memory_mb", "max_decompress_memory_mb",
        "integrity",
    ]

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in results:
            writer.writerow(row)

    print(f"\nVysledky exportovane do: {filepath}")


def print_summary(results):
    print("\n" + "=" * 80)
    print("SUMARNE VYSLEDKY")
    print("=" * 80)

    summary = {}
    for r in results:
        if "error" in r:
            continue
        key = (r["algorithm"], r["category"])
        if key not in summary:
            summary[key] = {"ratios": [], "comp": [], "decomp": []}
        summary[key]["ratios"].append(r["compression_ratio"])
        summary[key]["comp"].append(r["avg_compress_time"] * 1000)
        summary[key]["decomp"].append(r["avg_decompress_time"] * 1000)

    print(f"\n{'Algoritmus':<12} {'Kategoria':<15} {'Pomer(%)':<12} {'Komp(ms)':<12} {'Dek(ms)':<12}")
    print("-" * 63)
    for (algo, cat), d in sorted(summary.items()):
        print(f"{algo:<12} {cat:<15} {statistics.mean(d['ratios']):>8.1f}    {statistics.mean(d['comp']):>8.2f}    {statistics.mean(d['decomp']):>8.2f}")

    print(f"\n{'Algoritmus':<12} {'Celk. pomer(%)':<18} {'Celk. komp(ms)':<18} {'Celk. dek(ms)':<18}")
    print("-" * 66)

    by_algo = {}
    for r in results:
        if "error" in r:
            continue
        algo = r["algorithm"]
        by_algo.setdefault(algo, {"ratios": [], "comp": [], "decomp": []})
        by_algo[algo]["ratios"].append(r["compression_ratio"])
        by_algo[algo]["comp"].append(r["avg_compress_time"] * 1000)
        by_algo[algo]["decomp"].append(r["avg_decompress_time"] * 1000)

    for algo, d in sorted(by_algo.items()):
        print(f"{algo:<12} {statistics.mean(d['ratios']):>10.1f}        {statistics.mean(d['comp']):>10.2f}        {statistics.mean(d['decomp']):>10.2f}")

    failed = [r for r in results if r.get("integrity") is False]
    if failed:
        print(f"\n!! VAROVANIE: {len(failed)} testov zlyhalo pri overeni integrity !!")
        for r in failed:
            print(f"   - {r['algorithm']} na {r['file']}")
    else:
        print(f"\nVsetky testy integrity uspesne (SHA-256 zhoda)")


def main():
    results = run_benchmarks()
    export_csv(results, os.path.join(RESULTS_DIR, "benchmark_results.csv"))
    print_summary(results)
    return results


if __name__ == "__main__":
    main()
