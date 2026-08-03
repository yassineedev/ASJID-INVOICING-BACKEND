// background.js

let isRunning = false;
let shouldStop = false;
const pendingResultResolvers = new Map();

chrome.action.onClicked.addListener(() => {
  chrome.tabs.create({ url: chrome.runtime.getURL("dashboard.html") });
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "startQueue") {
    if (isRunning) {
      sendResponse({ ok: false, error: "A queue is already running." });
      return;
    }
    isRunning = true;
    shouldStop = false;
    runQueue(message.queue).catch((err) => {
      console.error("Queue run failed:", err);
      broadcastProgress({ type: "queueError", error: String(err) });
    });
    sendResponse({ ok: true });
    return;
  }

  if (message.type === "stopQueue") {
    shouldStop = true;
    sendResponse({ ok: true });
    return;
  }

  if (message.type === "sendResult" && sender.tab) {
    const resolver = pendingResultResolvers.get(sender.tab.id);
    if (resolver) {
      resolver(message.result);
      pendingResultResolvers.delete(sender.tab.id);
    }
    sendResponse({ ok: true });
    return;
  }
});

function broadcastProgress(payload) {
  chrome.runtime.sendMessage(payload).catch(() => {});
}

async function waitForTabComplete(tabId, timeoutMs = 25000) {
  // Check current status first in case it already completed loading
  const initialTab = await chrome.tabs.get(tabId);
  if (initialTab && initialTab.status === "complete") {
    return;
  }

  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      chrome.tabs.onUpdated.removeListener(listener);
      reject(new Error("Tab load timed out"));
    }, timeoutMs);

    function listener(updatedTabId, changeInfo) {
      if (updatedTabId === tabId && changeInfo.status === "complete") {
        clearTimeout(timer);
        chrome.tabs.onUpdated.removeListener(listener);
        resolve();
      }
    }
    chrome.tabs.onUpdated.addListener(listener);
  });
}

function waitForSendResult(tabId, timeoutMs = 40000) {
  return new Promise((resolve) => {
    const timer = setTimeout(() => {
      pendingResultResolvers.delete(tabId);
      resolve({ status: "error", reason: "timeout_waiting_for_content_script" });
    }, timeoutMs);

    pendingResultResolvers.set(tabId, (result) => {
      clearTimeout(timer);
      resolve(result);
    });
  });
}

async function runQueue(queue) {
  const results = [];

  for (let i = 0; i < queue.length; i++) {
    if (shouldStop) {
      broadcastProgress({ type: "queueStopped", processed: i, total: queue.length });
      break;
    }

    const item = queue[i];
    broadcastProgress({
      type: "itemStarted",
      index: i,
      total: queue.length,
      item,
    });

    if (!item.whatsappNumber) {
      const result = { ...item, status: "skipped", reason: "missing_phone_number" };
      results.push(result);
      broadcastProgress({ type: "itemFinished", index: i, total: queue.length, result });
      continue;
    }

    const digits = item.whatsappNumber.replace(/\D/g, "");
    const url = `https://web.whatsapp.com/send?phone=${digits}`;

    let tab;
    try {
      tab = await chrome.tabs.create({ url, active: true });
      await waitForTabComplete(tab.id);
      await new Promise((r) => setTimeout(r, 2000)); // Allow SPA to render chat UI

      await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: (base64, name, message) => {
          window.__invoiceImage = base64 && name ? { base64, name } : null;
          window.__invoiceMessage = message || "";
        },
        args: [item.imageBase64 || null, item.imageName || null, item.message || ""],
      });

      await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        files: ["content-send.js"],
      });

      const sendResult = await waitForSendResult(tab.id);
      const result = { ...item, ...sendResult };
      results.push(result);
      broadcastProgress({ type: "itemFinished", index: i, total: queue.length, result });
    } catch (err) {
      const result = { ...item, status: "error", reason: String(err) };
      results.push(result);
      broadcastProgress({ type: "itemFinished", index: i, total: queue.length, result });
    } finally {
      if (tab) {
        try {
          await chrome.tabs.remove(tab.id);
        } catch (_) {}
      }
    }

    if (i < queue.length - 1 && !shouldStop) {
      await new Promise((r) => setTimeout(r, 3000));
    }
  }

  isRunning = false;
  broadcastProgress({ type: "queueDone", results });
}