from __future__ import annotations

import json
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

from bench import DEFAULT_BENCH_FILE, DEFAULT_DATA_DIR, run_all_chunkers, run_benchmark


CHUNKER_CHOICES = ["all", "fixed_size", "sentence", "recursive", "semantic", "agentic", "parent_child"]
EMBEDDER_CHOICES = ["auto", "mock", "local", "openai"]


class BenchmarkDemoApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("K4 Ecommerce Benchmark Demo")
        self.geometry("1200x780")
        self.minsize(1000, 700)

        self._result_queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self._worker: threading.Thread | None = None

        self.data_dir_var = tk.StringVar(value=str(DEFAULT_DATA_DIR))
        self.benchmark_file_var = tk.StringVar(value=str(DEFAULT_BENCH_FILE))
        self.chunker_var = tk.StringVar(value="all")
        self.embedder_var = tk.StringVar(value="auto")
        self.chunk_size_var = tk.IntVar(value=400)
        self.top_k_var = tk.IntVar(value=1)
        self.status_var = tk.StringVar(value="Ready")

        self._build_ui()
        self.after(100, self._poll_result_queue)

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=16)
        root.pack(fill="both", expand=True)

        header = ttk.Frame(root)
        header.pack(fill="x")
        ttk.Label(header, text="K4 Ecommerce Benchmark Demo", font=("Segoe UI", 18, "bold")).pack(anchor="w")
        ttk.Label(
            header,
            text="Run chunking + embedding benchmark and inspect retrieved chunks with agent answers.",
        ).pack(anchor="w", pady=(4, 12))

        controls = ttk.LabelFrame(root, text="Controls", padding=12)
        controls.pack(fill="x")

        controls.columnconfigure(1, weight=1)
        controls.columnconfigure(3, weight=1)

        ttk.Label(controls, text="Data dir").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(controls, textvariable=self.data_dir_var).grid(row=0, column=1, sticky="ew", pady=4)
        ttk.Button(controls, text="Browse", command=self._browse_data_dir).grid(row=0, column=2, padx=(8, 0), pady=4)

        ttk.Label(controls, text="Benchmark file").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(controls, textvariable=self.benchmark_file_var).grid(row=1, column=1, sticky="ew", pady=4)
        ttk.Button(controls, text="Browse", command=self._browse_benchmark_file).grid(row=1, column=2, padx=(8, 0), pady=4)

        ttk.Label(controls, text="Chunker").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Combobox(controls, textvariable=self.chunker_var, values=CHUNKER_CHOICES, state="readonly").grid(
            row=2, column=1, sticky="ew", pady=4
        )

        ttk.Label(controls, text="Embedder").grid(row=2, column=2, sticky="w", padx=(16, 8), pady=4)
        ttk.Combobox(controls, textvariable=self.embedder_var, values=EMBEDDER_CHOICES, state="readonly").grid(
            row=2, column=3, sticky="ew", pady=4
        )

        ttk.Label(controls, text="Chunk size").grid(row=3, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Spinbox(controls, from_=50, to=2000, increment=50, textvariable=self.chunk_size_var, width=12).grid(
            row=3, column=1, sticky="w", pady=4
        )

        ttk.Label(controls, text="Top-k").grid(row=3, column=2, sticky="w", padx=(16, 8), pady=4)
        ttk.Spinbox(controls, from_=1, to=10, increment=1, textvariable=self.top_k_var, width=12).grid(
            row=3, column=3, sticky="w", pady=4
        )

        button_bar = ttk.Frame(root)
        button_bar.pack(fill="x", pady=(12, 8))
        self.run_button = ttk.Button(button_bar, text="Run Benchmark", command=self._run)
        self.run_button.pack(side="left")
        ttk.Button(button_bar, text="Clear Output", command=self._clear_output).pack(side="left", padx=8)
        ttk.Label(button_bar, textvariable=self.status_var).pack(side="right")

        main = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main, padding=(0, 0, 8, 0))
        right = ttk.Frame(main, padding=(8, 0, 0, 0))
        main.add(left, weight=2)
        main.add(right, weight=3)

        ttk.Label(left, text="Benchmark Summary", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        self.summary_text = tk.Text(left, wrap="word", height=30)
        self.summary_text.pack(fill="both", expand=True, pady=(6, 0))

        ttk.Label(right, text="Detailed Output", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        self.output_text = tk.Text(right, wrap="word")
        self.output_text.pack(fill="both", expand=True, pady=(6, 0))

        self._append_summary("Choose the benchmark settings and click Run Benchmark.")

    def _browse_data_dir(self) -> None:
        selected = filedialog.askdirectory(initialdir=self.data_dir_var.get() or str(DEFAULT_DATA_DIR))
        if selected:
            self.data_dir_var.set(selected)

    def _browse_benchmark_file(self) -> None:
        selected = filedialog.askopenfilename(
            initialdir=str(DEFAULT_BENCH_FILE.parent),
            initialfile=DEFAULT_BENCH_FILE.name,
            filetypes=[("JSON files", "*.json"), ("All files", "*")],
        )
        if selected:
            self.benchmark_file_var.set(selected)

    def _clear_output(self) -> None:
        self.summary_text.delete("1.0", tk.END)
        self.output_text.delete("1.0", tk.END)
        self.status_var.set("Cleared")

    def _run(self) -> None:
        if self._worker and self._worker.is_alive():
            messagebox.showinfo("Benchmark running", "A benchmark run is already in progress.")
            return

        data_dir = Path(self.data_dir_var.get())
        benchmark_file = Path(self.benchmark_file_var.get())

        if not data_dir.exists():
            messagebox.showerror("Invalid data dir", f"Data directory not found: {data_dir}")
            return
        if not benchmark_file.exists():
            messagebox.showerror("Invalid benchmark file", f"Benchmark file not found: {benchmark_file}")
            return

        self.run_button.configure(state="disabled")
        self.status_var.set("Running benchmark...")
        self._append_summary(f"Running {self.chunker_var.get()} with {self.embedder_var.get()} embeddings...")

        payload = {
            "data_dir": data_dir,
            "benchmark_file": benchmark_file,
            "chunker": self.chunker_var.get(),
            "embedder": self.embedder_var.get(),
            "chunk_size": int(self.chunk_size_var.get()),
            "top_k": int(self.top_k_var.get()),
        }

        self._worker = threading.Thread(target=self._worker_run, args=(payload,), daemon=True)
        self._worker.start()

    def _worker_run(self, payload: dict) -> None:
        try:
            if payload["chunker"] == "all":
                report = run_all_chunkers(
                    data_dir=payload["data_dir"],
                    benchmark_file=payload["benchmark_file"],
                    chunk_size=payload["chunk_size"],
                    top_k=payload["top_k"],
                    embedder_name=payload["embedder"],
                )
            else:
                report = run_benchmark(
                    data_dir=payload["data_dir"],
                    benchmark_file=payload["benchmark_file"],
                    chunker_name=payload["chunker"],
                    chunk_size=payload["chunk_size"],
                    top_k=payload["top_k"],
                    embedder_name=payload["embedder"],
                )
            self._result_queue.put(("ok", report))
        except Exception as exc:  # noqa: BLE001
            self._result_queue.put(("error", exc))

    def _poll_result_queue(self) -> None:
        try:
            status, payload = self._result_queue.get_nowait()
        except queue.Empty:
            self.after(150, self._poll_result_queue)
            return

        self.run_button.configure(state="normal")
        if status == "error":
            self.status_var.set("Failed")
            messagebox.showerror("Benchmark failed", str(payload))
            self.after(150, self._poll_result_queue)
            return

        report = payload
        self.status_var.set("Done")
        self._render_report(report)
        self.after(150, self._poll_result_queue)

    def _render_report(self, report: dict) -> None:
        self.summary_text.delete("1.0", tk.END)
        self.output_text.delete("1.0", tk.END)

        self._append_summary(
            "Dataset: {dataset}\nChunker: {chunker}\nEmbedder: {embedder}\nChunk size: {chunk_size}\nTop-k: {top_k}\nCollection size: {collection_size}\nChunk count: {chunk_count}".format(
                dataset=report.get("dataset"),
                chunker=report.get("chunker", "all"),
                embedder=report.get("embedder", "auto"),
                chunk_size=report.get("chunk_size"),
                top_k=report.get("top_k"),
                collection_size=report.get("collection_size", report.get("chunk_count", 0)),
                chunk_count=report.get("chunk_count", report.get("collection_size", 0)),
            )
        )

        self.output_text.insert(tk.END, json.dumps(report, ensure_ascii=False, indent=2))

        if "runs" in report:
            self._append_summary("\nPer-strategy chunk counts:")
            for run in report["runs"]:
                self._append_summary(f"- {run.get('chunker')}: {run.get('chunk_count', run.get('collection_size', 0))} chunks")
        else:
            results = report.get("results", [])
            self._append_summary(f"\nAnswered queries: {len(results)}")
            if results:
                first = results[0]
                self._append_summary(
                    f"First answer:\n{first.get('agent_answer', '')}\n\nTop retrieved doc: {first.get('retrieved', [{}])[0].get('doc_id', 'n/a')}"
                )

    def _append_summary(self, text: str) -> None:
        self.summary_text.insert(tk.END, text + "\n")
        self.summary_text.see(tk.END)


def main() -> int:
    app = BenchmarkDemoApp()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())