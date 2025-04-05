const form = document.getElementById("login");
const emailInput = document.getElementById("username");
const passwordInput = document.getElementById("password");

form.addEventListener("submit", function (e) {
    e.preventDefault();

    const username = emailInput.value;
    const password = passwordInput.value;

    fetch("/auth", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ 'username' : username, 'password' :password }),
        credentials: "include"
    })
    .then(res => res.json())
    .then(response => {
        alert(response.message || "Login successful!");
        form.reset();
        window.location.href = "/dashboard"; 
    })
    .catch(error => {
        console.error("Login error:", error);
        alert("An error occurred during login.");
    });
});
