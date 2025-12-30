# 👔 Custom Tie Pattern Generator

A Python-based tool to design and generate custom tie patterns (specifically 7-fold ties) and export them as production-ready PDFs.

See it deployed here [ties-marcopist.streamlit.app](http://ties-marcopist.streamlit.app)

## Features

- **Customizable Dimensions**: Adjust length, wide blade width, narrow blade width, and neck width.
- **Fold Options**: Support for 3, 5, and 7-fold tie constructions.
- **Dynamic Preview**: Visualize the pattern shape and cut pieces in real-time.
- **PDF Export**: Generate a 1:1 scale PDF with calibration squares, split across multiple pages for easy printing.
- **Cut Ratios**: Fine-tune where the tie is spliced into 3 pieces to fit your fabric.

## Prerequisites

This project uses [uv](https://github.com/astral-sh/uv) for fast Python package management.

## Installation

1.  Clone the repository:
    ```bash
    git clone <repository-url>
    cd tie-pattern
    ```

2.  Install dependencies using `uv`:
    ```bash
    uv sync
    ```

## Usage

Run the Streamlit application:

```bash
uv run streamlit run src/ui.py
```

This will open the application in your default web browser (usually at `http://localhost:8501`).

## Project Structure

- `src/pattern.py`: Core logic for geometry generation, folding calculations, and PDF export.
- `src/ui.py`: Streamlit user interface.
- `pyproject.toml`: Project dependencies and configuration.

## PDF Export Details

The exported PDF is designed for printing on standard paper (A4/Letter).
- **Scale**: 1:1 (Real world size).
- **Calibration**: Each page includes a 10cm x 10cm red square. **Always measure this square after printing** to ensure your printer scaling is correct (set "Scale" to "100%" or "Do Not Scale" in print settings).
- **Assembly**: The pattern is split into 3 pieces (Wide Blade, Neck Piece, Narrow Blade).
