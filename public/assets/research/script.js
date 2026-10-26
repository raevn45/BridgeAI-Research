// =========================
// BridgeAI OS
// script.js
// COMPLETE REPLACEMENT (FIXED)
// =========================

document.addEventListener("DOMContentLoaded", () => {
    // -------------------------
    // Smooth Cursor
    // -------------------------

    const cursor = document.getElementById("cursor");

    let mouseX = window.innerWidth / 2;
    let mouseY = window.innerHeight / 2;

    let currentX = mouseX;
    let currentY = mouseY;

    document.addEventListener("mousemove", (e) => {
        mouseX = e.clientX;
        mouseY = e.clientY;
    });

    if (cursor) {
        animateCursor();
    }

    function animateCursor() {
        currentX += (mouseX - currentX) * 0.22;
        currentY += (mouseY - currentY) * 0.22;

        cursor.style.left = currentX + "px";
        cursor.style.top = currentY + "px";

        requestAnimationFrame(animateCursor);
    }

    // -------------------------
    // Upload Card
    // -------------------------

    const upload = document.getElementById("upload");
    const uploadBox = document.querySelector(".upload-box");

    if (upload) {
        upload.addEventListener("change", () => {
            if (upload.files.length > 0) {
                uploadBox.innerHTML = `
                    <div class="upload-icon">
                        ✓
                    </div>
                    <div>
                        <h3>${upload.files[0].name}</h3>
                        <p>Ready for analysis</p>
                    </div>
                `;
            }
        });
    }

    // -------------------------
    // Analyze Button & Form Submission Fix
    // -------------------------

    const button = document.getElementById("analyzeButton");
    const form = button ? button.closest("form") : null;

    if (button && form) {
        form.addEventListener("submit", (e) => {
            // Only change state if it hasn't already been submitted
            if (button.disabled) {
                e.preventDefault();
                return;
            }

            button.disabled = true;
            button.innerHTML = `
                <span>
                Initializing AI...
                </span>
            `;

            // Allow the native HTML form submit to continue to Flask
        });
    }

    // -------------------------
    // Typing Animation
    // -------------------------

    const output = document.getElementById("typing-output");

    if (output) {
        output.style.opacity = "0";
        output.style.transition = "opacity 0.6s ease";
        requestAnimationFrame(() => {
            output.style.opacity = "1";
        });
    }

    // -------------------------
    // Floating Glass Effect
    // -------------------------

    document.querySelectorAll(".glass").forEach((card) => {
        card.addEventListener("mousemove", (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            const rotateY = (x / rect.width - 0.5) * 8;
            const rotateX = (y / rect.height - 0.5) * -8;

            card.style.transform = `
                perspective(1200px)
                rotateX(${rotateX}deg)
                rotateY(${rotateY}deg)
                translateY(-6px)
            `;
        });

        card.addEventListener("mouseleave", () => {
            card.style.transform = "";
        });
    });

    // -------------------------
    // Orb Pulse
    // -------------------------

    const orb = document.querySelector(".logo-orb");

    if (orb) {
        setInterval(() => {
            orb.animate(
                [
                    { transform: "scale(1)" },
                    { transform: "scale(1.3)" },
                    { transform: "scale(1)" },
                ],
                {
                    duration: 1800,
                },
            );
        }, 2500);
    }

    // -------------------------
    // Status Animation
    // -------------------------

    const status = document.querySelector(".status p");

    if (status) {
        const messages = [
            "Ready",
            "Standing By",
            "Listening",
            "Bridge Connected",
        ];
        let index = 0;
        setInterval(() => {
            index = (index + 1) % messages.length;
            status.textContent = messages[index];
        }, 4000);
    }
});
