Not included in this commit — these are large binary/vendor assets, not source you'd
review or diff. `offscreen.js` expects this directory to contain:

- `tesseract.min.js` (Tesseract.js UMD build, loaded by `offscreen.html`)
- `worker.min.js`
- `tesseract-core-simd-lstm.js` (or `.wasm.js` depending on your `tesseract.js-core`
  version — if OCR fails to initialize, check the actual filename shipped in your
  `node_modules/tesseract.js-core/` and update `corePath` in `offscreen.js` to match)
- `eng.traineddata.gz`

Copy them from your local `ten-talons-ext` vendor bundle (or from
`node_modules/tesseract.js/dist/` + `node_modules/tesseract.js-core/` +
`node_modules/@tesseract.js-data/eng/`) before loading this extension unpacked.
