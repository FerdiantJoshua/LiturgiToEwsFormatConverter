const quillDOMId = ".ql-editor";

// Enable line-height option in toolbar (ref: https://github.com/quilljs/quill/issues/197)
var Parchment = Quill.import('parchment');
var lineHeightConfig = {
    scope: Parchment.Scope.INLINE,
    whitelist: ['0.8', '1.0', '1.2', '3.0']
};
var lineHeightClass = new Parchment.Attributor.Class('lineheight', 'ql-line-height', lineHeightConfig);
var lineHeightStyle = new Parchment.Attributor.Style('lineheight', 'line-height', lineHeightConfig);
Parchment.register(lineHeightClass);
Parchment.register(lineHeightStyle);
// END OF ENABLING line-height option in toolbar

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

let popUpCopiedInfoTimeout = null;
function popUpCopiedInfo() {
    if (popUpCopiedInfoTimeout) {
        clearTimeout(popUpCopiedInfoTimeout);
    }
    $("#copied-text-alert").fadeIn(200);
    popUpCopiedInfoTimeout = setTimeout(() => {
        $("#copied-text-alert").fadeOut(200);
    }, 2500);
}

function handleAjaxError(jqXHR, textStatus, errorThrown) {
    console.log("textStatus", textStatus, "; errorThrown: ", errorThrown, "; jqXHR: ", jqXHR);
    const errorStatus = jqXHR.status;
    let errorMessage = " 503 - Service Unavailable"
    if (errorThrown == "timeout") {
        errorMessage = "Timeout error";
    } else if (errorStatus != 0) {
        errorMessage = errorStatus + " - " + errorThrown
    }
    $("#error-detail").html(errorMessage);
    $("#error-alert").fadeIn(200);
    setTimeout(() => {
        $("#error-alert").fadeOut(200);
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
    quill.on("text-change", function(delta, oldDelta, source) {
        const start = performance.now();
        if (JSON.stringify(contentFromLastSave.ops) == JSON.stringify(quill.getContents().ops)) {
            if (document.title.startsWith("* ")) {
                document.title = document.title.slice(2);
            }
        } else {
            if (!document.title.startsWith("* ")) {
                document.title = "* " + document.title;
            }
        }
        console.log(`Text difference execution time: ${performance.now() - start} ms`, );
    });
    quill.root.setAttribute('spellcheck', false)
    const quillDOM = $(quillDOMId);

    var contentFromLastSave = quill.getContents();

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
        txtResult.val("");
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
                txtResult.val(data.result);
            },
            error: handleAjaxError
        }).always(function () {
            spinner.addClass('d-none');
        })
    });

    // COPY BUTTONS
    $("#btn-copy-editor").click(function () {
        navigator.clipboard.writeText(quill.getText());
        popUpCopiedInfo();
    });
    $("#btn-copy-postprocess-result").click(function () {
        navigator.clipboard.writeText(txtResult.val());
        popUpCopiedInfo();
    });

    // DOWNLOAD & UPLOAD TOOLBAR BUTTONS
    const inputEditorDownload = $("#input-editor-download");
    const inputEditorUpload = $("#input-editor-upload");

    const downloadDataPrefix = "data:application/xml;charset=utf-8,"
    $("#btn-editor-download").click(function () {
        inputEditorDownload.attr("href", downloadDataPrefix + quillDOM[0].innerHTML);
        inputEditorDownload[0].click();

        // For exit confirmation
        contentFromLastSave = quill.getContents();
        if (document.title.startsWith("* ")) {
            document.title = document.title.slice(2);
        }
    });
    $("#btn-editor-upload").click(function () {
        checkboxIsFormatted.prop("checked", true);
        inputEditorUpload.click();
    });
    inputEditorUpload.change(handleFileSelect);

    // Exit confirmation
    function exitConfirmation() {
        if (JSON.stringify(contentFromLastSave.ops) != JSON.stringify(quill.getContents().ops)) {
            console.log("different yeah");
            return "You have unsaved changes. Do you really want to quit?"
        }
        return void(0);
    }
    window.onbeforeunload = exitConfirmation;
});
