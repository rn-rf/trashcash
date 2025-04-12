const form = document.getElementById("signup");
const emailInput = document.getElementById("username");
const passwordInput = document.getElementById("password");
const input = document.getElementById("remember-me");

form.addEventListener("submit", function (e) {
    e.preventDefault();

    const username = emailInput.value;
    const password = passwordInput.value;
    const iscollector = input.checked;

    fetch("/save", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ username, password, iscollector })
    })
    .then(res => res.json())
    .then(response => {
        alert(response.message || "Signup successful!");
        form.reset();
        window.location.href = "/login"; 
    })
    .catch(error => {
        console.error("Signup error:", error);
        alert("An error occurred during signup.");
    });
});
