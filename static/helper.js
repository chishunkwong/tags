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
}, false);

function makeSelectedVisible(checkboxElement) {
  if (checkboxElement && checkboxElement.checked) {
    checkboxElement.scrollIntoView({
      behavior: 'smooth', // Optional: provides a smooth scrolling animation
      block: 'nearest'    // Scrolls to the nearest edge of the container
    });
    return true;
  }
  return false;
}

document.addEventListener('DOMContentLoaded', function() {
  for (const checkedTag of checkedTagIds) {
    const checkbox = document.getElementById(checkedTag);
    makeSelectedVisible(checkbox);
  }
});