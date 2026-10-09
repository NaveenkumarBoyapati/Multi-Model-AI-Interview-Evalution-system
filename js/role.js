const cards = document.querySelectorAll(".role-card");
const button = document.getElementById("continueBtn");

let selectedRole = "";

cards.forEach(card => {

    card.addEventListener("click", () => {

        cards.forEach(c => c.classList.remove("selected"));

        card.classList.add("selected");

        selectedRole = card.dataset.role;

        button.disabled = false;

    });

});

button.addEventListener("click", () => {

    localStorage.setItem("selectedRole", selectedRole);

    window.location.href = "instructions.html";

});