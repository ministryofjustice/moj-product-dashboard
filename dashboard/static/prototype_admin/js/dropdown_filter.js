let listVisible = false;
let listFilter = document.getElementById("changelist-filter");
console.log(listFilter);

function shrink(element) {
  element.setAttribute("style", "height:54px");
  element.style.overflow = "hidden";
}

function expand(element) {
  element.setAttribute("style", "height:auto");
  element.style.overflow = "visible";
}


function dropDownClick() {
  if (listVisible) {
    shrink(listFilter);
    listVisible = false;
  } else if (!listVisible) {
    expand(listFilter);
    listVisible = true;
  }
}

if (listFilter != null) {

  filterHeading = listFilter.getElementsByTagName("h2")[0];
  headingText = filterHeading.innerHTML;
  headingText = headingText + "<a id='dropdown_button'><img src='staticfiles/prototype_admin/img/down_arrow.png' /></a>";
  filterHeading.innerHTML = headingText;
  dropDownButton = document.getElementById("dropdown_button");
  dropDownButton.onclick = dropDownClick;
  shrink(listFilter);
  console.log(listFilter);

}
