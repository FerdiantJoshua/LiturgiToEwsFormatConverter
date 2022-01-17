$.ajaxSetup({ cache: false });
$(document).ready(function () {
    const formConvert = $("#form_convert");
    const txtInput = $("#txt-input");
    const txtResult = $("#txt-result");

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
            // We need these 3 lines to support most browsers
            txtInput.text(data.result);
            txtInput.html(data.result);
            txtInput.val(data.result);
        }).fail(function (error) {
            console.log(error)
        }).always(function () {
            spinner.addClass('d-none');
        })
    });

    $("#btn-postprocess").click(function () {
        spinner.removeClass('d-none');
        const payload = { "text": txtInput.val() };
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

    $("#btn-copy-txt-input").click(function () {
        navigator.clipboard.writeText(txtInput.val());
    });

    $("#btn-copy-postprocess-result").click(function () {
        navigator.clipboard.writeText(txtResult.val());
    });
});
