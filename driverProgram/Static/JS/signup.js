document.addEventListener("DOMContentLoaded", function () {
    const passwordField = document.getElementById("password");
    const confirmPasswordField = document.getElementById("confirm_password");
    const submitButton = document.getElementById("submit-button");

    // Enable submit button only if passwords match
    alert("Test");
    function validatePassword() {
        alert("Test");
        if (passwordField.value === confirmPasswordField.value && passwordField.value != "") {
            alert("Submit = " && submitButton.disabled);
            submitButton.disabled = false;
            alert("Submit = " && submitButton.disabled);
        } else {
            alert("Submit = " && submitButton.disabled);
            submitButton.disabled = true;
            alert("Submit = " && submitButton.disabled);
        }
    }

    passwordField.addEventListener("input", validatePassword);
    confirmPasswordField.addEventListener("input", validatePassword);
});
