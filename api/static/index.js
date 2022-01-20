$.ajaxSetup({ cache: false });
$(document).ready(function () {
    var quill = new Quill('#editor', {
        modules: {
            // toolbar: toolbarOptions
            toolbar: "#toolbar"
        },
        placeholder: 'Edit your liturgi here...',
        theme: 'snow'
    });
    quill.root.setAttribute('spellcheck', false)
    const quillDOM = $(".ql-editor")

    const formConvert = $("#form_convert");
    const txtResult = $("#txt-result");
    const checkboxIsFormatted = $("#checkbox-is-formatted");

    const spinner = $("#spinner");

    $("#btn-convert").click(function (e) {
        if (!formConvert[0].reportValidity()) {
            return;
        }

        spinner.removeClass('d-none');
        const payload = new FormData(formConvert[0]);
        $.ajax({
            type: "POST",
            url: "/convert",
            data: payload,
            enctype: "multipart/form-data",
            processData: false,
            contentType: false
        }).done(function (data) {
            quill.setText(data.result)
        }).fail(function (error) {
            console.log(error)
        }).always(function () {
            spinner.addClass('d-none');
        })
    });

    $("#auto-format-header").click(function () {
        spinner.removeClass('d-none');
        const payload = { "text": quill.getText() };
        $.ajax({
            type: "POST",
            url: "/format-text",
            data: JSON.stringify(payload),
            contentType: "application/json; charset=utf-8",
            dataType: "json"
        }).done(function (data) {
            quillDOM[0].innerHTML = data.result;
            checkboxIsFormatted.prop("checked", true);
        }).fail(function (error) {
            console.log(error)
        }).always(function () {
            spinner.addClass('d-none');
        })
    });

    $("#btn-postprocess").click(function () {
        spinner.removeClass('d-none');
        isFormatted = checkboxIsFormatted.is(":checked");
        text = !isFormatted ? quill.getText() : quillDOM[0].innerHTML;
        const payload = { "text": text, "is_formatted": isFormatted };
        $.ajax({
            type: "POST",
            url: "/postprocess",
            data: JSON.stringify(payload),
            contentType: "application/json; charset=utf-8",
            dataType: "json"
        }).done(function (data) {
            // We need these 3 lines to support most browsers
            txtResult.text(data.result);
            txtResult.html(data.result);
            txtResult.val(data.result);
        }).fail(function (error) {
            console.log(error)
        }).always(function () {
            spinner.addClass('d-none');
        })
    });

    $("#btn-copy-editor").click(function () {
        navigator.clipboard.writeText(quill.getText());
    });

    $("#btn-copy-postprocess-result").click(function () {
        navigator.clipboard.writeText(txtResult.val());
    });
});
