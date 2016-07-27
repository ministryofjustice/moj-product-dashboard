let listVisible = false;
let listFilter = document.getElementById("changelist-filter");


function shrink(listFilterElement) {
  listFilterElement.setAttribute("style", "height:54px");
  listFilterElement.style.overflow = "hidden";
  // visibilityButton.innerHTML = 'show';
  listVisible = false;
}

function expand(listFilterElement) {
  listFilterElement.setAttribute("style", "height:auto");
  listFilterElement.style.overflow = "visible";
  // visibilityButton.innerHTML = 'hide';
  listVisible = true;
}


function dropDownClick() {
  if (listVisible) {
    shrink(listFilter);

  } else if (!listVisible) {
    expand(listFilter);

  }
}

if (listFilter != null) {

  filterHeading = listFilter.getElementsByTagName("h2")[0];
  headingText = filterHeading.innerHTML;
  headingText = headingText + "<a id='dropdown_button'>X</a>";
  filterHeading.innerHTML = headingText;
  dropDownButton = document.getElementById("dropdown_button");
  dropDownButton.onclick = dropDownClick;
  shrink(listFilter);

}
