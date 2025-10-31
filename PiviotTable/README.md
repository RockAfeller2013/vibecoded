Build a single-file front-end project: an `index.html` that uses only client-side JavaScript and front-end libraries. Do not use any server-side code.

Requirements:
1. Layout and frameworks
   - Include Bootstrap via CDN for layout and responsiveness.
   - Include a Google Material Design library (Material Icons and Material Components or Materialize) via CDN.
   - Page must render correctly on a typical 14-inch laptop screen. Default font-size should be appropriate for that display.
   - Provide zoom in/out controls to scale the table view.

2. Data input
   - Load `input.csv` from the same folder using client-side file input or drag-and-drop.
   - Expected CSV columns: `DATE`, `DESCRIPTION`, `AMOUNT`, `CATEGORY`.
   - DATE format: ISO or common formats (DD/MM/YYYY). Parse robustly.

3. Pivot table behavior
   - Build an interactive pivot table entirely in JavaScript. You may use client-side JS libraries (e.g., PapaParse for CSV parsing and a pivot table library) but keep everything client-only.
   - Rows: Months consolidated from dates. Show months in calendar order from JAN to DEC. Each row represents one month (Jan, Feb, ... Dec).
   - Columns: Distinct `CATEGORY` values from the CSV. Each column shows the total amount for that category for the month row.
   - Cells: For each month and category display the sum of `AMOUNT`.
   - Totals:
     - Row-level totals (per month) must appear in a "Grand Total" column to the right.
     - Column-level totals (per category) must appear in a "Grand Total" row at the bottom.
     - Display a final overall total (bottom-right cell).
   - Sorting and filtering: Allow sorting by month and toggling categories on/off.
   - Support horizontal and vertical scrolling. The table must remain usable when many categories or months are shown.

4. UI and UX
   - Use Bootstrap components and Material visual style.
   - Keep the pivot table readable at default zoom on a 14" laptop.
   - Provide controls: file input, zoom in, zoom out, reset zoom, toggle columns (categories), export current pivot to CSV.
   - Make the header sticky when scrolling vertically. Make the leftmost column (months) sticky when scrolling horizontally.

5. Accessibility and performance
   - Ensure keyboard focus on interactive controls.
   - Handle large CSVs gracefully without freezing the UI (use requestAnimationFrame or chunk parsing if needed).
   - Validate numeric values for `AMOUNT` and ignore malformed rows with a warning.

6. Deliverable
   - One `index.html` file that includes all HTML, CSS, and JavaScript.
   - The page must function offline if the CDNs are reachable on first load (no server required).
   - Include brief inline comments only where necessary.
   - Include a sample `input.csv` snippet in a comment or a downloadable example.

Example CSV:
DATE,DESCRIPTION,AMOUNT,CATEGORY
02/01/2025,MOBILE COMPANY,$103.00,MOBILE
03/01/2025,FOOD PLACE,$46.64,FOOD
03/01/2025,ENERGY USAGE,$203.56,ENERGY


Acceptance criteria:
- Loading the example CSV populates months Jan–Dec.
- Categories become columns.
- Toggle Option for Month and Categories
- Option to Swap Row to Colums
- Remove File open, keep drag and drop only
- Monthly sums and grand totals match CSV amounts.
- Sticky headers and sticky month column work while scrolling.
- Zoom and export work.
- Add a Sort order for each Accending and Descending for each Row, just click ascending click again descending
