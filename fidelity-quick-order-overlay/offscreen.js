// Offscreen document: runs Tesseract.js OCR entirely locally, in a page governed
// by this extension's own CSP — not the host page's (Fidelity's CSP would otherwise
// be free to block the Worker/WASM Tesseract needs).
//
// Everything Tesseract needs (worker script, wasm core, English language data) is
// bundled under vendor/tesseract/ and loaded via chrome-extension:// URLs. No
// network request ever leaves the machine for OCR.

let workerPromise = null;

function getWorker() {
  if (!workerPromise) {
    workerPromise = Tesseract.createWorker("eng", 1, {
      workerPath: chrome.runtime.getURL("vendor/tesseract/worker.min.js"),
      corePath: chrome.runtime.getURL("vendor/tesseract/tesseract-core-simd-lstm.js"),
      langPath: chrome.runtime.getURL("vendor/tesseract/"),
      workerBlobURL: false, // blob-wrapped importScripts() can't reach chrome-extension:// URLs; load the worker script directly instead
      gzip: true,
      logger: () => {},
    }).catch((e) => {
      workerPromise = null; // let the next request retry instead of staying broken
      throw e;
    });
  }
  return workerPromise;
}

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg?.target !== "offscreen" || msg?.type !== "ocr") return false;
  (async () => {
    try {
      const worker = await getWorker();
      const { data } = await worker.recognize(msg.imageDataUrl);
      sendResponse({ ok: true, text: data.text || "" });
    } catch (e) {
      sendResponse({ ok: false, error: e?.message || String(e) });
    }
  })();
  return true; // async response
});
