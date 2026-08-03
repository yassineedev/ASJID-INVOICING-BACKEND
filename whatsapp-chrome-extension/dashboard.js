let rawQueue = [];
let imagesMap = {};
let lastResults = [];

const jsonInput = document.getElementById("jsonFile");
const folderInput = document.getElementById("imageFolder");
const statsDiv = document.getElementById("stats");
const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");
const progressDiv = document.getElementById("progress");
const downloadBtn = document.getElementById("downloadReportBtn");

jsonInput.addEventListener("change", async (event) => {
  const file = event.target.files[0];
  if (!file) return;

  try {
    const text = await file.text();
    const json = JSON.parse(text);
    rawQueue = Array.isArray(json) ? json : json.queue || [];
    // A fresh JSON almost certainly means a fresh batch of invoices -
    // any images loaded for a previous batch are no longer relevant and
    // could otherwise get matched against the wrong meter numbers if
    // filenames happen to collide between runs.
    imagesMap = {};
    folderInput.value = "";
    updateStatus();
  } catch (e) {
    alert("Failed to parse JSON file.");
  }
});

folderInput.addEventListener("change", async (event) => {
  const files = event.target.files;
  // Reset before repopulating: previously, images from an earlier
  // folder selection stayed in this map forever, so re-selecting a
  // folder (or picking a different one) silently mixed old and new
  // images together instead of replacing them.
  imagesMap = {};
  for (const file of files) {
    const base64 = await readFileAsDataURL(file);
    imagesMap[file.name] = base64;
  }
  updateStatus();
});

function readFileAsDataURL(file) {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = (e) => resolve(e.target.result);
    reader.readAsDataURL(file);
  });
}

function getInvoiceFilename(item) {
  // Use the filename the Python app already gives us directly, instead
  // of trying to parse it back out of invoicePath. invoicePath is built
  // with the OS's own path separator (backslashes on Windows), so
  // splitting on '/' silently failed to match any image on Windows.
  return item.invoiceFile || "";
}

function updateStatus() {
  const matchedCount = rawQueue.filter((item) => imagesMap[getInvoiceFilename(item)]).length;

  const noPhoneCount = rawQueue.filter((item) => !item.whatsappNumber).length;

  statsDiv.innerHTML = `
        <b>JSON Records Loaded:</b> ${rawQueue.length}<br>
        <b>Images Loaded in Folder:</b> ${Object.keys(imagesMap).length}<br>
        <b>Successfully Matched Images:</b> ${matchedCount} / ${rawQueue.length}<br>
        <b>Entries Without a Phone Number:</b> ${noPhoneCount} (will be skipped and listed in the report)
    `;

  startBtn.disabled = !(rawQueue.length > 0 && Object.keys(imagesMap).length > 0);
}

startBtn.addEventListener("click", async () => {
  const finalQueue = rawQueue.map((item) => {
    const filename = getInvoiceFilename(item);
    return {
      ...item,
      imageBase64: imagesMap[filename] || null,
      imageName: filename || null,
    };
  });

  startBtn.disabled = true;
  stopBtn.disabled = false;
  downloadBtn.disabled = true;
  lastResults = [];
  progressDiv.style.display = "block";
  progressDiv.innerHTML = "Starting...";

  const response = await chrome.runtime.sendMessage({ type: "startQueue", queue: finalQueue });
  if (!response || !response.ok) {
    alert(response && response.error ? response.error : "Could not start the queue.");
    startBtn.disabled = false;
    stopBtn.disabled = true;
  }
});

stopBtn.addEventListener("click", async () => {
  stopBtn.disabled = true;
  await chrome.runtime.sendMessage({ type: "stopQueue" });
  progressDiv.innerHTML += "<br><b>Stopping after the current contact...</b>";
});

chrome.runtime.onMessage.addListener((message) => {
  if (message.type === "itemStarted") {
    progressDiv.innerHTML = `Sending ${message.index + 1} / ${message.total}: <b>${
      message.item.fullName || ""
    }</b> (${message.item.whatsappNumber || "no number"})...`;
  }

  if (message.type === "itemFinished") {
    lastResults.push(message.result);
    const statusLabel =
      message.result.status === "sent"
        ? "\u2705 Sent"
        : message.result.status === "skipped"
        ? `\u26a0\ufe0f Skipped (${message.result.reason})`
        : `\u274c Error (${message.result.reason})`;
    progressDiv.innerHTML = `${message.index + 1} / ${message.total} - ${
      message.result.fullName || ""
    }: ${statusLabel}`;
  }

  if (message.type === "queueDone") {
    lastResults = message.results;
    const sentCount = lastResults.filter((r) => r.status === "sent").length;
    const skippedCount = lastResults.filter((r) => r.status === "skipped").length;
    const errorCount = lastResults.filter((r) => r.status === "error").length;
    progressDiv.innerHTML = `
            <b>Finished.</b><br>
            Sent: ${sentCount} &nbsp; | &nbsp; Skipped (no WhatsApp / no phone): ${skippedCount} &nbsp; | &nbsp; Errors: ${errorCount}
        `;
    startBtn.disabled = false;
    stopBtn.disabled = true;
    downloadBtn.disabled = lastResults.length === 0;
  }

  if (message.type === "queueStopped") {
    progressDiv.innerHTML += `<br>Stopped after ${message.processed} / ${message.total} contacts.`;
    startBtn.disabled = false;
    stopBtn.disabled = true;
    downloadBtn.disabled = lastResults.length === 0;
  }

  if (message.type === "queueError") {
    progressDiv.innerHTML += `<br><b>Queue error:</b> ${message.error}`;
    startBtn.disabled = false;
    stopBtn.disabled = true;
  }
});

downloadBtn.addEventListener("click", () => {
  // So staff always have a record of exactly who did NOT get an
  // invoice via WhatsApp (wrong/missing number, not on WhatsApp, or a
  // send error) and can follow up with those people some other way.
  const blob = new Blob([JSON.stringify({ results: lastResults }, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `whatsapp_send_report_${new Date().toISOString().slice(0, 10)}.json`;
  a.click();
  URL.revokeObjectURL(url);
});