document.addEventListener('keydown', (event) => {
  var keyValue = event.key;
  var codeValue = event.code;
  if (keyValue === 'ArrowLeft' && window.previous_media) {
    window.location = window.previous_media;
  }
  else if (keyValue === 'ArrowRight' && window.next_media) {
    window.location = window.next_media;
  }
  else {
    console.log("keyValue: " + keyValue);
    console.log("codeValue: " + codeValue);
  }
}, false);