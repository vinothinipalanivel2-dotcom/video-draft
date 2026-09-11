import os
import openpyxl

orig_path = r"C:\Users\Vino\Downloads\Track_03_draft_video_generation_routing_Submission_Evaluation_and_Batch_Moderation_Workbook.xlsx"
comp_path = r"C:\Users\Vino\.gemini\antigravity\scratch\draft-video-routing\submission\IncuBrix_PS03_Submission_Evaluation_Batch_Moderation_Workbook_COMPLETED.xlsx"

print("Checking files existence and sizes:")
print(f"Original: {os.path.getsize(orig_path)} bytes")
print(f"Completed: {os.path.getsize(comp_path)} bytes")

wb_orig = openpyxl.load_workbook(orig_path, data_only=False)
wb_comp = openpyxl.load_workbook(comp_path, data_only=False)

assert wb_orig.sheetnames == wb_comp.sheetnames, "Sheet names mismatch!"
print(f"Worksheets ({len(wb_comp.sheetnames)}): {wb_comp.sheetnames}")

# Verify evaluator sheets are untouched
for sname in ["04_TRACK_CRITERIA", "05_REVIEW_RESULT", "06_LIVE_VALIDATION", "07_BATCH_MODERATION"]:
    ws_o = wb_orig[sname]
    ws_c = wb_comp[sname]
    mismatches = []
    for r in range(1, max(ws_o.max_row, ws_c.max_row) + 1):
        for c in range(1, max(ws_o.max_column, ws_c.max_column) + 1):
            vo = ws_o.cell(r, c).value
            vc = ws_c.cell(r, c).value
            if vo != vc:
                coord = f"{openpyxl.utils.get_column_letter(c)}{r}"
                mismatches.append((coord, vo, vc))
    print(f"Sheet {sname} evaluator integrity check: {len(mismatches)} differences")
    assert len(mismatches) == 0, f"Evaluator sheet {sname} was modified! {mismatches}"

# Verify candidate fields populated
ws0 = wb_comp["00_START"]
print("\n--- 00_START Inspection ---")
print("Candidate Name (B6):", ws0["B6"].value)
print("Candidate Email (F6):", ws0["F6"].value)
print("Submission Date (B7):", ws0["B7"].value)
print("Repo URL (F7):", ws0["F7"].value)
print("CPU Specs (B8):", ws0["B8"].value)
print("RAM (F8):", ws0["F8"].value)
print("OS (B9):", ws0["B9"].value)
print("Runtime (F9):", ws0["F9"].value)
print("Free compute used (B10):", ws0["B10"].value)
print("Provider/runtime (F10):", ws0["F10"].value)
print("Checklist items F23:F30:", [ws0[f"F{r}"].value for r in range(23, 31)])
print("Declaration signature (B34):", ws0["B34"].value)

ws1 = wb_comp["01_DELIVERABLES"]
print("\n--- 01_DELIVERABLES Inspection ---")
print("Deliverables C5:C13 status:", [ws1[f"C{r}"].value for r in range(5, 14)])
print("Reproduction commands populated:", all(ws1[f"B{r}"].value is not None for r in range(16, 23)))
print("Submission notes length:", len(str(ws1["A25"].value)))

ws2 = wb_comp["02_COMPONENTS"]
print("\n--- 02_COMPONENTS Inspection ---")
components_count = sum(1 for r in range(5, 25) if ws2[f"A{r}"].value is not None)
print("Components populated:", components_count)
for r in range(5, 5 + components_count):
    print(f"  Row {r:2d}: {ws2[f'A{r}'].value} | {ws2[f'B{r}'].value} | {ws2[f'C{r}'].value} | {ws2[f'E{r}'].value} | {ws2[f'G{r}'].value} | {ws2[f'H{r}'].value}")

ws3 = wb_comp["03_TEST_EVIDENCE"]
print("\n--- 03_TEST_EVIDENCE Inspection ---")
tests_count = sum(1 for r in range(7, 27) if ws3[f"A{r}"].value is not None)
print("Tests populated:", tests_count)
for r in range(7, 7 + tests_count):
    print(f"  Row {r:2d}: {ws3[f'A{r}'].value} | Level={ws3[f'B{r}'].value} | Route={ws3[f'G{r}'].value} | Pass={ws3[f'H{r}'].value} | Runtime={ws3[f'M{r}'].value}s | RAM={ws3[f'N{r}'].value}MB")

# Check formula integrity in 05 and 07
formulas_05 = [ws_c.cell(r, c).value for r in range(1, wb_comp["05_REVIEW_RESULT"].max_row+1) for c in range(1, wb_comp["05_REVIEW_RESULT"].max_column+1) if isinstance(ws_c.cell(r, c).value, str) and ws_c.cell(r, c).value.startswith("=")]
formulas_07 = [ws_c.cell(r, c).value for r in range(1, wb_comp["07_BATCH_MODERATION"].max_row+1) for c in range(1, wb_comp["07_BATCH_MODERATION"].max_column+1) if isinstance(ws_c.cell(r, c).value, str) and ws_c.cell(r, c).value.startswith("=")]
print(f"\nFormulas in 05_REVIEW_RESULT: {len(formulas_05)} formulas intact")
print(f"Formulas in 07_BATCH_MODERATION: {len(formulas_07)} formulas intact")

print("\nALL VERIFICATIONS PASSED PERFECTLY!")
