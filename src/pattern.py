import numpy as np
import matplotlib.pyplot as plt
import io
from matplotlib.patches import Rectangle
from shapely.geometry import Polygon, LineString
from shapely.ops import split
from scipy.interpolate import PchipInterpolator

class TiePatternGenerator:
    def __init__(self,
                 length_cm=148,
                 wide_width_cm=8.0,
                 narrow_width_cm=4.0,
                 neck_width_cm=2.5,
                 folds=7,
                 ratios=(50, 25, 25)):

        self.length = length_cm
        self.w_wide = wide_width_cm
        self.w_narrow = narrow_width_cm
        self.w_neck = neck_width_cm
        self.folds = folds
        self.ratios = np.array(ratios) / 100.0
        self.width_scale = (self.folds + 1) / 2.0

    def get_width_profile(self, num_points=1000):
        # Y positions
        y_points = [
            0,
            self.w_wide / 2.0,
            self.length * 0.35,
            self.length * 0.70,
            self.length - (self.w_narrow / 2.0),
            self.length
        ]
        # Widths
        w_points = [0, self.w_wide, self.w_neck, self.w_neck, self.w_narrow, 0]

        interpolator = PchipInterpolator(y_points, w_points)
        y_vals = np.linspace(0, self.length, num_points)
        w_vals = interpolator(y_vals)

        # Enforce linear tips
        y_wide_max = self.w_wide / 2.0
        mask_wide = y_vals < y_wide_max
        w_vals[mask_wide] = y_vals[mask_wide] * 2

        y_narrow_max = self.length - (self.w_narrow / 2.0)
        mask_narrow = y_vals > y_narrow_max
        w_vals[mask_narrow] = (self.length - y_vals[mask_narrow]) * 2

        w_vals = np.clip(w_vals, 0, None)
        return y_vals, w_vals

    def generate_polygon(self):
        y_vals, w_vals_finished = self.get_width_profile()
        w_vals_pattern = w_vals_finished * self.width_scale

        right_coords = list(zip(w_vals_pattern / 2, y_vals))
        left_coords = list(zip(-w_vals_pattern / 2, y_vals))
        full_coords = right_coords + left_coords[::-1]

        return Polygon(full_coords).buffer(0)

    def cut_pieces(self, poly):
        l1 = self.length * self.ratios[0]
        l2 = self.length * (self.ratios[0] + self.ratios[1])

        # Wide Cut Lines (ensuring they cross the poly)
        cut_line_1 = LineString([(-200, -200 + l1), (200, 200 + l1)])
        cut_line_2 = LineString([(-200, -200 + l2), (200, 200 + l2)])

        # Split 1
        split_1 = split(poly, cut_line_1)
        pieces_1 = sorted(list(split_1.geoms), key=lambda g: g.bounds[1])
        if len(pieces_1) < 2: raise ValueError("Cut 1 Failed")

        wide_piece = pieces_1[0]
        remainder = pieces_1[1]

        # Split 2
        split_2 = split(remainder, cut_line_2)
        pieces_2 = sorted(list(split_2.geoms), key=lambda g: g.bounds[1])
        if len(pieces_2) < 2:
            remainder = remainder.buffer(0)
            split_2 = split(remainder, cut_line_2)
            pieces_2 = sorted(list(split_2.geoms), key=lambda g: g.bounds[1])
            if len(pieces_2) < 2: raise ValueError("Cut 2 Failed")

        return [wide_piece, pieces_2[0], pieces_2[1]]

    def _draw_pieces_on_ax(self, ax, pieces, gap=5.0, simple_mode=False, start_index=0):
        """Helper to draw pieces on a given axis"""
        y_offset = 0
        labels = ['Wide Blade', 'Neck Piece', 'Narrow Blade']
        colors = ['#FFD700', '#87CEEB', '#FF69B4']

        total_min_x, total_max_x = 0, 0
        total_max_y = 0

        for i, piece in enumerate(pieces):
            real_index = i + start_index
            minx, miny, maxx, maxy = piece.bounds
            x, y = piece.exterior.xy
            y_shifted = [yi - miny + y_offset for yi in y] # Normalize Y to 0 then offset

            # Draw Outline
            fc = 'none' if simple_mode else colors[real_index]
            ec = 'black'
            lw = 1.0 if simple_mode else 1.0

            ax.fill(x, y_shifted, alpha=0.5 if not simple_mode else 1, fc=fc, ec=ec, linewidth=lw)

            # Calculate shift for fold lines
            shift_val = -miny + y_offset

            # Draw Fold Lines
            sample_ys = np.linspace(miny, maxy, 40)
            y_prof, w_prof = self.get_width_profile()
            w_interp = PchipInterpolator(y_prof, w_prof)

            l_fold, r_fold, ys_fold = [], [], []
            for yi in sample_ys:
                if 0 <= yi <= self.length:
                    w = w_interp(yi)
                    l_fold.append(-w/2)
                    r_fold.append(w/2)
                    ys_fold.append(yi + shift_val)

            ax.plot(l_fold, ys_fold, 'k--', linewidth=0.5, alpha=0.7)
            ax.plot(r_fold, ys_fold, 'k--', linewidth=0.5, alpha=0.7)

            # Label
            label_y = (maxy - miny)/2 + y_offset
            ax.text(0, label_y, labels[real_index], ha='center', fontsize=10)

            # Track bounds
            total_min_x = min(total_min_x, minx)
            total_max_x = max(total_max_x, maxx)

            # Move next piece up
            height = maxy - miny
            y_offset += height + gap
            total_max_y = y_offset

        return total_min_x, total_max_x, total_max_y

    def plot_pattern(self):
        """Returns figure for visualization"""
        poly = self.generate_polygon()
        pieces = self.cut_pieces(poly)

        fig, ax = plt.subplots(figsize=(8, 12))
        self._draw_pieces_on_ax(ax, pieces)
        ax.set_aspect('equal')
        ax.grid(True, linestyle=':')
        ax.set_title(f"Pattern Preview ({self.folds}-Fold)")
        return fig

    def export_pdf(self):
        """Exports 1:1 scale PDF with calibration square as bytes, one piece per page"""
        from matplotlib.backends.backend_pdf import PdfPages
        poly = self.generate_polygon()
        pieces = self.cut_pieces(poly)

        buf = io.BytesIO()
        with PdfPages(buf) as pdf:
            for i, piece in enumerate(pieces):
                # Calculate dimensions for this piece
                minx, miny, maxx, maxy = piece.bounds
                w = maxx - minx
                h = maxy - miny

                # Margins (cm)
                margin = 3.0
                canvas_w_cm = w + (margin * 2) + 15 # Extra space for calibration square
                canvas_h_cm = h + (margin * 2)

                # Convert to inches for Matplotlib (1 inch = 2.54 cm)
                fig_w_in = canvas_w_cm / 2.54
                fig_h_in = canvas_h_cm / 2.54

                # Create Figure with EXACT dimensions
                fig, ax = plt.subplots(figsize=(fig_w_in, fig_h_in))

                # Draw single piece
                # We pass [piece] so it draws just one, but we pass start_index=i so it gets the right label/color
                min_x, max_x, max_y = self._draw_pieces_on_ax(ax, [piece], gap=0.0, simple_mode=True, start_index=i)

                # Add Calibration Square (10cm x 10cm)
                # Place it to the right of the piece
                rect_x = max_x + 5.0
                rect_y = 5.0
                ax.add_patch(Rectangle((rect_x, rect_y), 10, 10, fill=False, edgecolor='red', linewidth=2))
                ax.text(rect_x + 5, rect_y + 5, "10cm x 10cm\nCHECK SCALE",
                        color='red', ha='center', va='center', fontweight='bold')

                # Set Limits to match the canvas size exactly
                ax.set_xlim(min_x - margin, min_x + canvas_w_cm - margin)
                ax.set_ylim(-margin, canvas_h_cm - margin)

                # Turn off axis for clean print
                ax.axis('off')
                ax.set_aspect('equal')

                # Save page
                pdf.savefig(fig, dpi=72, bbox_inches='tight', pad_inches=0)
                plt.close(fig)

        buf.seek(0)
        return buf.getvalue()

# --- EXECUTION ---
generator = TiePatternGenerator(
    length_cm=148,
    wide_width_cm=8.5,
    narrow_width_cm=4.0,
    neck_width_cm=2.2,
    folds=7,
    ratios=(50, 30, 20)
)

# 1. Show preview
# generator.plot_pattern()

# 2. Export to PDF
# pdf_bytes = generator.export_pdf()
# with open("my_7fold_tie_pattern.pdf", "wb") as f:
#     f.write(pdf_bytes)