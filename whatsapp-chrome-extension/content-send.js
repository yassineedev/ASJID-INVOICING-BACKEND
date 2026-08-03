// content-send.js

(async function () {
  const REPORT = (result) => chrome.runtime.sendMessage({ type: "sendResult", result });

  function waitFor(conditionFn, { timeout = 15000, interval = 400 } = {}) {
    return new Promise((resolve, reject) => {
      const start = Date.now();
      const timer = setInterval(() => {
        let value;
        try {
          value = conditionFn();
        } catch (_) {
          value = null;
        }
        if (value) {
          clearInterval(timer);
          resolve(value);
        } else if (Date.now() - start > timeout) {
          clearInterval(timer);
          reject(new Error("waitFor timeout"));
        }
      }, interval);
    });
  }

  function findChatBox() {
    return (
      document.querySelector('div[contenteditable="true"][data-tab="10"]') ||
      document.querySelector('footer div[contenteditable="true"]') ||
      document.querySelector('div[contenteditable="true"][data-tab="1"]') ||
      null
    );
  }

  function pageSaysInvalidNumber() {
    const text = document.body.innerText || "";
    return (
      text.includes("Phone number shared via url is invalid") ||
      text.includes("le numéro de téléphone") ||
      text.includes("invalid phone number")
    );
  }

  function dataURLtoFile(dataurl, filename) {
    const arr = dataurl.split(",");
    const mime = arr[0].match(/:(.*?);/)[1];
    const bstr = atob(arr[1]);
    let n = bstr.length;
    const u8arr = new Uint8Array(n);
    while (n--) {
      u8arr[n] = bstr.charCodeAt(n);
    }
    return new File([u8arr], filename, { type: mime });
  }

  function findImageFileInput() {
    const candidates = document.querySelectorAll('input[type="file"]');
    for (const input of candidates) {
      const accept = (input.getAttribute("accept") || "").toLowerCase();
      if (accept.includes("image") || accept.includes("application")) return input;
    }
    return candidates[0] || null;
  }

  function attachImageViaFileInput(fileInput, file) {
    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(file);
    
    const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
      window.HTMLInputElement.prototype,
      "files"
    ).set;
    nativeInputValueSetter.call(fileInput, dataTransfer.files);

    fileInput.dispatchEvent(new Event("change", { bubbles: true }));
    fileInput.dispatchEvent(new Event("input", { bubbles: true }));
  }

  function isVisible(el) {
    if (!el) return false;
    const rect = el.getBoundingClientRect();
    return el.offsetParent !== null && rect.width > 0 && rect.height > 0;
  }

  function findSendButton() {
    // Gather all potential send buttons on the page (both chat footer and modal footer)
    const candidates = [
      ...document.querySelectorAll('[data-testid="send"]'),
      ...document.querySelectorAll('span[data-icon="send"]'),
      ...document.querySelectorAll('div[aria-label="Send"]'),
      ...document.querySelectorAll('button[aria-label="Send"]'),
      ...document.querySelectorAll('div[aria-label="Envoyer"]'),
    ];

    const valid = candidates.filter((el) => isVisible(el));
    if (valid.length === 0) return null;

    // If multiple buttons exist, sort by vertical position (modal send button is always lower/further down on the screen)
    valid.sort((a, b) => b.getBoundingClientRect().top - a.getBoundingClientRect().top);
    return valid[0].closest("button") || valid[0].closest('div[role="button"]') || valid[0];
  }

  function fireClick(el) {
    el.scrollIntoView({ behavior: "smooth", block: "center" });
    el.click();
    const rect = el.getBoundingClientRect();
    if (rect.width > 0 && rect.height > 0) {
      const x = rect.left + rect.width / 2;
      const y = rect.top + rect.height / 2;
      const opts = { bubbles: true, cancelable: true, view: window, clientX: x, clientY: y, button: 0 };
      el.dispatchEvent(new MouseEvent("mousedown", opts));
      el.dispatchEvent(new MouseEvent("mouseup", opts));
      el.dispatchEvent(new MouseEvent("click", opts));
    }
  }

  try {
    const outcome = await Promise.race([
      waitFor(findChatBox, { timeout: 25000 }).then(() => "chat_ready"),
      waitFor(() => (pageSaysInvalidNumber() ? true : null), { timeout: 25000 }).then(() => "invalid_number"),
    ]).catch(() => "timeout");

    if (outcome === "invalid_number") {
      await REPORT({ status: "skipped", reason: "number_not_on_whatsapp" });
      return;
    }

    if (outcome === "timeout") {
      await REPORT({ status: "error", reason: "chat_did_not_load_in_time" });
      return;
    }

    const chatBox = findChatBox();
    if (!chatBox) {
      await REPORT({ status: "error", reason: "chat_box_not_found" });
      return;
    }

    let imageAttached = false;

    // Attach image if provided
    if (window.__invoiceImage && window.__invoiceImage.base64 && window.__invoiceImage.name) {
      try {
        const file = dataURLtoFile(window.__invoiceImage.base64, window.__invoiceImage.name);
        chatBox.focus();

        const fileInput = findImageFileInput();
        if (fileInput) {
          attachImageViaFileInput(fileInput, file);
          imageAttached = true;
        }

        // Give WhatsApp Web 1.5 seconds to open the media preview modal smoothly
        await new Promise((r) => setTimeout(r, 1500));

        // Optional: Fill caption if message text exists
        if (window.__invoiceMessage) {
          const captionBox =
            document.querySelector('div[data-testid="media-caption-input"]') ||
            document.querySelector('div[aria-label="Add a caption"]') ||
            document.querySelector('div[contenteditable="true"][data-tab="undefined"]');
          if (captionBox) {
            captionBox.focus();
            document.execCommand("selectAll", false, null);
            document.execCommand("delete", false, null);
            document.execCommand("insertText", false, window.__invoiceMessage);
          }
        }
      } catch (err) {
        console.error("Image attachment error:", err);
      }
    } else if (window.__invoiceMessage) {
      chatBox.focus();
      document.execCommand("insertText", false, window.__invoiceMessage);
      await new Promise((r) => setTimeout(r, 500));
    }

    // Find and click the send button
    let sendBtn = null;
    try {
      sendBtn = await waitFor(findSendButton, { timeout: 8000, interval: 300 });
    } catch (_) {
      sendBtn = null;
    }

    if (!sendBtn) {
      await REPORT({ status: "error", reason: "send_button_not_found" });
      return;
    }

    fireClick(sendBtn);

    // Wait briefly to ensure the message is sent out and the chat screen settles
    await new Promise((r) => setTimeout(r, 2000));

    await REPORT({
      status: "sent",
      imageAttached,
      sentAt: new Date().toISOString(),
    });
  } catch (err) {
    await REPORT({ status: "error", reason: String(err) });
  }
})();