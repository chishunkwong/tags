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

function handleSetAssetBoolean(checkbox, attribute) {
  if (isSearchMode) return;
  socket.emit('set_asset_boolean', {
    db_id: dbId,
    attribute,
    value: checkbox.checked
  });
}

function handleTagClicked(checkbox, isMultiselect, tagId, tagGroupId) {
  if (isSearchMode) return;
  socket.emit('set_tag', {
    db_id: dbId,
    tag_id: tagId,
    value: checkbox.checked,
    tag_group_id: tagGroupId,
    is_multiselect: isMultiselect
  });
}

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
    const checkbox = document.getElementById('tag_' + checkedTag);
    makeSelectedVisible(checkbox);
  }
});