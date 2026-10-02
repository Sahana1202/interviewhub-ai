(() => {
  const inspectPage = () => {
    const forms = [...document.forms];
    const passwordFields = document.querySelectorAll('input[type="password"]').length;
    const externalFormAction = forms.some((form) => {
      if (!form.action) return false;
      try { return new URL(form.action, location.href).hostname !== location.hostname; } catch { return false; }
    });
    return { title: document.title, passwordFields, forms: forms.length, externalFormAction };
  };

  chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
    if (message.type === "PAGE_INSPECTION") sendResponse(inspectPage());
  });
})();
