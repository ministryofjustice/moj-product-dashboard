var listVisible = false;
var userMenuVisible = false;
var listFilter = document.getElementById("changelist-filter");
var userMenu = document.getElementById("user-menu-options");

function shrink(dropDownElement, height) {
  var heightStyle = "height:" + String(height) + "px";
  dropDownElement.setAttribute("style", heightStyle);
  dropDownElement.style.overflow = "hidden";
}

function expand(dropDownElement) {
  dropDownElement.setAttribute("style", "height:auto");
  dropDownElement.style.overflow = "visible";
}


function filterClick() {
  if (listVisible) {
    shrink(listFilter, 54);
    listVisible = false;

  } else if (!listVisible) {
    expand(listFilter);
    listVisible = true;

  }
}

function userClick() {
  if (userMenuVisible) {
    userMenu.setAttribute("style", "display:none");
    // shrink(userMenu, 24);
    userMenuVisible = false;

  } else if (!userMenuVisible) {
    userMenu.setAttribute("style", "display:inline");
    // expand(userMenu);
    userMenuVisible = true;

  }
}

if (listFilter != null) {

  filterHeading = listFilter.getElementsByTagName("h2")[0];
  headingText = filterHeading.innerHTML;
  headingText = headingText + "<a id='dropdown-button'>show/hide</a>";
  filterHeading.innerHTML = headingText;
  filterDropDownButton = document.getElementById("dropdown-button");
  filterDropDownButton.onclick = filterClick;
  shrink(listFilter, 54);

}

if (userMenu != null) {

  userDropDownButton = document.getElementById("user-menu-button");
  userDropDownButton.onclick = userClick;
  // shrink(userMenu, 24);

}
