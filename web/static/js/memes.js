$(function() {
	$('*').contents().filter((_, node) => node.nodeType === 3).each((_, node) => node.nodeValue = node.nodeValue.replace(/a/gi, '🅰️').replace(/b/gi, '🅱️').replace(/o/gi, '🅾️').replace(/p/gi, '🅿️'));
});
