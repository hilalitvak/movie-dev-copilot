const runBtn = document.getElementById("runBtn");
const promptInput = document.getElementById("promptInput");
const responseBox = document.getElementById("responseBox");
const stepsBox = document.getElementById("stepsBox");

runBtn.addEventListener("click", async () => {
    const prompt = promptInput.value.trim();
    if (!prompt) {
        alert("Please enter a prompt.");
        return;
    }

    responseBox.textContent = "Loading...";
    stepsBox.textContent = "";

    try {
        const res = await fetch("/api/execute", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ prompt })
        });

        const data = await res.json();

        if (data.status !== "ok") {
            responseBox.textContent = "Error: " + data.error;
            return;
        }

        responseBox.textContent = data.response;

        if (data.steps) {
            stepsBox.textContent = JSON.stringify(data.steps, null, 2);
        }

    } catch (err) {
        responseBox.textContent = "Server error.";
        console.error(err);
    }
});
