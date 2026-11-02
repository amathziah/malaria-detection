# Building the Phase 3 deck

`Malaria_Phase3_Final.pptx` is generated from the results, so every number on the slides comes from `results/`:

```bash
python slides/src/make_deck_assets.py                    # circular cell images (needs the NIH data in outputs/data)
cd slides/src && npm install pptxgenjs react react-dom react-icons sharp
NODE_PATH=$PWD/node_modules node build.js ../.. ../Malaria_Phase3_Final.pptx
```

- `build_deck.js`: theme, layouts and helpers.
- `build.js`: the slides up to the hypotheses.
- `results_slides.js`: the result, limitation, conclusion and reference slides, read from `results/ablation/` and `results/phase3b/`.

`build.js` also applies the deck's theme colours with the `apply_theme.js` helper from the PowerPoint skill used to build it.
Without that helper, remove the `applyTheme` lines and the deck keeps Office's default theme colours.
The slides themselves are ordinary PowerPoint and can be edited by hand.
