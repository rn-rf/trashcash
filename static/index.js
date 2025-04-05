const form = document.getElementById("signup");
const emailInput = document.getElementById("username");
const passwordInput = document.getElementById("password");

form.addEventListener("submit", function (e) {
    e.preventDefault();

    const username = emailInput.value;
    const password = passwordInput.value;

    fetch("/save", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ 'username' : username, 'password' :password })
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
