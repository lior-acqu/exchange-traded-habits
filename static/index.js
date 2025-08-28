function changeDescription() {
  var interval = document.getElementById("interval").value;
  var identity = document.getElementById("identity").value;
  var time = document.getElementById("time").value;

  // change to X if no value
  if (interval == "") interval = "X";
  if (time == "") time = "X";
  if (identity == "") identity = "X";

  // change the text
  document.querySelector(".habit-statement").innerHTML =
    "Every " +
    interval +
    " day/s, I'll complete this habit when " +
    time +
    " to become " +
    identity +
    ".";
}
