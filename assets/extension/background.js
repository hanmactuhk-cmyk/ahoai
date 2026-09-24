const BRIDGE = "http://127.0.0.1:18923";

chrome.runtime.onInstalled.addListener(() => {
  console.log("Hn38videoAItool Bridge installed");
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (!message || message.type !== "health") return;
  fetch(`${BRIDGE}/health`)
    .then(r => r.json())
    .then(sendResponse)
    .catch(e => sendResponse({ok:false, error:String(e)}));
  return true;
});
