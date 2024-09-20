chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "getAuthToken") {
      chrome.identity.getAuthToken({ interactive: true }, function(token) {
        sendResponse({token: token});
      });
      return true;  
    }
  });