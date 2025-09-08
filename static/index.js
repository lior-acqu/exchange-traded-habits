/* AI DISCLAIMER: I HAVE USED CHATGPT AS AN ASSISTANT DURING MY CODING PROCESS. IT HAS HELPED ME CREATE SOME OF THE SYNTAX AND LOGIC IN THIS DOCUMENT'S FUNCTIONS, WHEREAS THE STRUCTURE AND MOST OF THE CODE IS HAND-WRITTEN. 0% OF THIS DOCUMENT IS WRITTEN BY AI. */

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

