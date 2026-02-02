document.addEventListener('keydown', (event) => {
  var keyValue = event.key;
  var codeValue = event.code;
  var activeElement = document.activeElement;
  if (!(activeElement.tagName == 'INPUT' && activeElement.type == 'text')) {
    if ((keyValue === 'ArrowLeft' || keyValue === 'P' || keyValue === 'p') && window.previous_media) {
      window.location = window.previous_media;
    }
    else if ((keyValue === 'ArrowRight' || keyValue === 'N' || keyValue === 'n') && window.next_media) {
      window.location = window.next_media;
    }
    else if (keyValue === 'Delete' || keyValue === 'Backspace') {
      window.location.href = window.delete_url;
    }
    else {
      console.log(keyValue, codeValue)
    }
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

function handleTagSingleSelected(selectBox, tagGroupId) {
  var tagId = selectBox.options[selectBox.selectedIndex].value;
  if (isSearchMode) {
    if (parseInt(tagId, 10) > 0) {
      selectBox.name = "tag_" + tagId;
    }
  } else {
    handleTagSelected(true, tagId, tagGroupId);
  }
}

function handleTagClicked(checkbox, tagId, tagGroupId) {
  handleTagSelected(checkbox.checked, tagId, tagGroupId);
}

function handleTagSelected(selected, tagId, tagGroupId) {
  if (isSearchMode) return;
  socket.emit('set_tag', {
    db_id: dbId,
    tag_id: tagId,
    value: selected,
    tag_group_id: tagGroupId,
  });
}

function handleTagGroupCarry(checkbox, tagGroupId) {
  if (isSearchMode) return;
  socket.emit('set_tag_group_carry', {
    value: checkbox.checked,
    tag_group_id: tagGroupId,
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