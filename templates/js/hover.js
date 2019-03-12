var index = cb_data.index['1d'].indices
if (index.length == 1) {
    var id = document.getElementById(source.data['labels'][index]);
    id.style.backgroundColor = 'red';
}
else {
    for (var i = 0; i < source.data['labels'].length; i++) {
        var id = document.getElementById(source.data['labels'][i]);
        id.style.backgroundColor = '';
    }
}