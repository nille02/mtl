if (window.location.host !== "translate.google.com"){
	var togoogle = document.getElementById('togoogle');
	togoogle.href = "http://translate.google.com/translate?js=n&sl=ja&tl=en&u=" + window.location;
	togoogle.style.display = "";
}