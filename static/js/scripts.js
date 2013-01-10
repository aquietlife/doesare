$(document).ready(function(){
	var imageNumber = Math.round(Math.random()*7);
		
	$("html").css("background", "url(/static/images/bg/"+ imageNumber +".jpg) no-repeat center center fixed");

});
