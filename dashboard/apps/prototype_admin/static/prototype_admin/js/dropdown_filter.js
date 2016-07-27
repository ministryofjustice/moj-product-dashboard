function dropDownClick() {

}

function shrink(element) {
  
}

listFilter = document.getElementById("changelist-filter");

if (listFilter != null) {

  filterHeading = listFilter.getElementsByTagName("h2")[0];
  headingText = filterHeading.innerHTML;
  headingText = headingText + "<a id='dropdown_button'> X </a>";
  filterHeading.innerHTML = headingText;
  dropDownButton = document.getElementById("dropdown_button");
  dropDownButton.onclick = dropDownClick;

}
