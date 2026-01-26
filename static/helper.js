document.addEventListener('keydown', (event) => {
  var keyValue = event.key;
  var codeValue = event.code;
  if (document.activeElement.tagName != 'INPUT'
    && (keyValue === 'ArrowLeft' || keyValue === 'P' || keyValue === 'p')
    && window.previous_media) {
    console.log("focus", document.activeElement.tagName)
    window.location = window.previous_media;
  }
  else if (document.activeElement.tagName != 'INPUT'
    && (keyValue === 'ArrowRight' || keyValue === 'N' || keyValue === 'n')
    && window.next_media) {
    console.log("focus", document.activeElement.tagName)
    window.location = window.next_media;
  }
  else {
    console.log("keyValue: " + keyValue);
    console.log("codeValue: " + codeValue);
  }
}, false);