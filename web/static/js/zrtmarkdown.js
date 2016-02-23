function htmlDecode(value){
  return $('<div/>').html(value).text();
}
function tomarkdown(){
    var converter = new showdown.Converter();
    this.innerHTML=converter.makeHtml(htmlDecode(this.innerHTML))
}
$(function (){
    $('.markdown').map(tomarkdown);
});
