# Figure contracts before plotting

Backend: Python, established in this project. No image generation or simulated observations.
Export: editable PDF/SVG, 600 dpi PNG/TIFF; 180 mm width; minimum glyph 7.5 pt. Statistical units and scope stated in captions. All plotted values come from frozen CSV.

Figure 1 question: Does zone-wise energy matching preserve the same pattern of decision disagreement across synthetic mappings and feeders?
Claim: At the main threshold, disagreement persists across all 33-bus mappings but disappears in part of the 69-bus mapping set.
Panel a: primary-feeder persistence and spread across all 20 mappings, BG versus BZ.
Panel b: boundary case on the second test feeder, including zero disagreements.
Archetype: quantitative grid, two equal rectangles, common y scale. No mapping is selected or averaged away; 80 rows in the specified BG/BZ subset are retained. Mapping 0 is not pooled with alternatives. No error bars because mappings are controlled scenarios, not empirical replicates. No connecting lines because IDs have no temporal meaning.

Figure S1 question: How do the original and matched inputs compare under fixed mapping 0?
Claim: Energy matching changes paired disagreement without necessarily eliminating it in the fixed scenario.
Archetype: single quantitative panel. Six markers, all 4344-hour paired contrasts. Horizontal ranges are the existing 2.5th–97.5th percentiles of 2000 paired 7-day moving-block resamples. These are conditional temporal ranges, not annual or population intervals. No new resampling or power flow is performed.

QA: invoke rendered alignment gate before export (single-panel N/A); run source preflight, PDF glyph floor and PDF collision audit; inspect full figures and both Figure 1 panels. Keep QA overlays separate from deliverables.
