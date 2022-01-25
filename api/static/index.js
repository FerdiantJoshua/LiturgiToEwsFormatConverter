const quillDOMId = ".ql-editor";

function handleFileSelect (e) {
    var files = e.target.files;
    if (files.length < 1) {
        alert('select a file...');
        return;
    }
    var file = files[0];
    var reader = new FileReader();
    reader.onload = onFileLoaded;
    reader.readAsText(file);
}
function onFileLoaded (e) {
    $(quillDOMId)[0].innerHTML = e.target.result;
}

function handleAjaxError(jqXHR, textStatus, errorThrown) {
    console.log("textStatus", textStatus, "; errorThrown: ", errorThrown, "; jqXHR: ", jqXHR);
    const errorStatus = jqXHR.status;
    errorThrown = errorThrown == "timeout" ? "Timeout error" : errorStatus + " - " + errorThrown
    $("#error-detail").html(errorThrown);
    $(".disappearing-alert").removeClass("d-none");
    setTimeout(() => {
        $(".disappearing-alert").addClass("d-none");
    }, 5000);
}

$.ajaxSetup({ cache: false });
$(document).ready(function () {
    var quill = new Quill('#editor', {
        modules: {
            // toolbar: toolbarOptions
            toolbar: "#toolbar",
            keyboard: {
                bindings: {
                  'list autofill': {
                    prefix: /^\s*()$/
                  }
                }
            }
        },
        placeholder: 'Edit your liturgi here...',
        theme: 'snow'
    });
    quill.keyboard.addBinding({
        key: 'S',
        ctrlKey: true,
        handler: function(range, context) {
            $("#btn-editor-download").click();
        }
    });
    quill.keyboard.addBinding({
        key: 'O',
        ctrlKey: true,
        handler: function(range, context) {
            $("#btn-editor-upload").click();
        }
    });
    quill.root.setAttribute('spellcheck', false)
    const quillDOM = $(quillDOMId);

    const formConvert = $("#form_convert");
    const txtResult = $("#txt-result");
    const checkboxIsFormatted = $("#checkbox-is-formatted");

    const spinner = $("#spinner");

    $("#btn-convert").click(function (e) {
        if (!formConvert[0].reportValidity()) {
            return;
        }

        spinner.removeClass("d-none");
        const payload = new FormData(formConvert[0]);
        $.ajax({
            type: "POST",
            url: "/convert",
            data: payload,
            timeout: 30000,
            enctype: "multipart/form-data",
            processData: false,
            contentType: false,
            success: function (data) {
                quill.setText(data.result);
            },
            error: handleAjaxError
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
            timeout: 7000,
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            success: function (data) {
                quillDOM[0].innerHTML = data.result;
                checkboxIsFormatted.prop("checked", true);
            },
            error: handleAjaxError
        }).always(function () {
            spinner.addClass('d-none');
        })
    });

    $("#btn-postprocess").click(function () {
        txtResult.text("");
        spinner.removeClass('d-none');
        isFormatted = checkboxIsFormatted.is(":checked");
        text = !isFormatted ? quill.getText() : quillDOM[0].innerHTML;
        const payload = { "text": text, "is_formatted": isFormatted };
        $.ajax({
            type: "POST",
            url: "/postprocess",
            data: JSON.stringify(payload),
            timeout: 7000,
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            success: function (data) {
                txtResult.text(data.result);
            },
            error: handleAjaxError
        }).always(function () {
            spinner.addClass('d-none');
        })
    });

    // COPY BUTTONS
    $("#btn-copy-editor").click(function () {
        navigator.clipboard.writeText(quill.getText());
    });
    $("#btn-copy-postprocess-result").click(function () {
        navigator.clipboard.writeText(txtResult.val());
    });

    // DOWNLOAD & UPLOAD TOOLBAR BUTTONS
    const inputEditorDownload = $("#input-editor-download");
    const inputEditorUpload = $("#input-editor-upload");

    const downloadDataPrefix = "data:application/xml;charset=utf-8,"
    $("#btn-editor-download").click(function () {
        inputEditorDownload.attr("href", downloadDataPrefix + quillDOM[0].innerHTML);
        inputEditorDownload[0].click();
    });
    $("#btn-editor-upload").click(function () {
        checkboxIsFormatted.prop("checked", true);
        inputEditorUpload.click();
    });
    inputEditorUpload.change(handleFileSelect);
});
