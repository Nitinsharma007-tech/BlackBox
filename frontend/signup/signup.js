// ============================================================
// NOVASHIELDS REGISTRATION WIZARD
// ============================================================

const state = {
    step: 1,
    phone: "",
    otp: "",
    otpVerified: false,
    contacts: []
};

const form = document.getElementById("signupForm");
const errorBox = document.getElementById("errorBox");
const steps = [...document.querySelectorAll(".step")];
const stepLabel = document.getElementById("stepLabel");

const labels = {
    1: "Mobile verification",
    2: "OTP verification",
    3: "Personal details",
    4: "Emergency contacts",
    5: "Black Box activation"
};

function showError(message) {
    errorBox.textContent = message || "Something went wrong.";
    errorBox.classList.add("show");
}

function clearError() {
    errorBox.textContent = "";
    errorBox.classList.remove("show");
}

function setStep(step) {
    state.step = step;
    steps.forEach(s => s.classList.toggle("active", Number(s.dataset.step) === step));

    document.querySelectorAll(".step-dot").forEach(dot => {
        const n = Number(dot.dataset.dot);
        dot.classList.toggle("active", n === step);
        dot.classList.toggle("done", n < step);
    });

    document.querySelectorAll(".step-line").forEach(line => {
        line.classList.toggle("done", Number(line.dataset.line) < step);
    });

    stepLabel.textContent = labels[step];
    clearError();
    window.scrollTo({top: 0, behavior: "smooth"});
}

function phoneIsValid(phone) {
    return /^[6-9]\d{9}$/.test(phone);
}

function renderContacts() {
    const container = document.getElementById("contactsContainer");
    container.innerHTML = "";

    if (!state.contacts.length) {
        addContact();
        return;
    }

    state.contacts.forEach((contact, index) => {
        const card = document.createElement("div");
        card.className = "contact-card";
        card.innerHTML = `
            <div class="flex items-center justify-between mb-3">
                <div class="font-bold text-sm">
                    Emergency Contact ${index + 1}
                    ${index === 0 ? '<span class="text-primary text-xs ml-1">PRIMARY</span>' : ""}
                </div>
                ${index > 0 ? `<button type="button" class="remove-contact text-xs font-bold text-rose-600" data-index="${index}">Remove</button>` : ""}
            </div>
            <div class="grid sm:grid-cols-3 gap-3">
                <input class="input-field px-3 py-2 rounded-lg contact-name" data-index="${index}" placeholder="Name" value="${contact.name || ""}" ${index === 0 ? "required" : ""}>
                <input class="input-field px-3 py-2 rounded-lg contact-relation" data-index="${index}" placeholder="Relationship" value="${contact.relationship || ""}" ${index === 0 ? "required" : ""}>
                <input class="input-field px-3 py-2 rounded-lg contact-phone" data-index="${index}" placeholder="Phone" inputmode="numeric" maxlength="10" value="${contact.phone || ""}" ${index === 0 ? "required" : ""}>
            </div>
        `;
        container.appendChild(card);
    });

    container.querySelectorAll(".remove-contact").forEach(btn => {
        btn.addEventListener("click", () => {
            state.contacts.splice(Number(btn.dataset.index), 1);
            renderContacts();
        });
    });

    container.querySelectorAll(".contact-name").forEach(input => {
        input.addEventListener("input", e => state.contacts[Number(e.target.dataset.index)].name = e.target.value);
    });
    container.querySelectorAll(".contact-relation").forEach(input => {
        input.addEventListener("input", e => state.contacts[Number(e.target.dataset.index)].relationship = e.target.value);
    });
    container.querySelectorAll(".contact-phone").forEach(input => {
        input.addEventListener("input", e => state.contacts[Number(e.target.dataset.index)].phone = e.target.value.replace(/\D/g, "").slice(0, 10));
    });
}

function addContact() {
    if (state.contacts.length >= 5) {
        showError("You can add a maximum of 5 emergency contacts.");
        return;
    }
    state.contacts.push({name: "", relationship: "", phone: ""});
    renderContacts();
}

document.getElementById("sendOtpBtn").addEventListener("click", async () => {
    clearError();
    const phone = document.getElementById("phone").value.trim();

    if (!phoneIsValid(phone)) {
        showError("Enter a valid 10-digit Indian mobile number.");
        return;
    }

    state.phone = phone;
    const btn = document.getElementById("sendOtpBtn");
    btn.disabled = true;
    btn.textContent = "Sending OTP...";

    try {
        if (typeof NovaAPI.requestSignupOtp !== "function") {
            throw new Error("Registration OTP API is not available in the current backend yet.");
        }
        await NovaAPI.requestSignupOtp(phone);
        setStep(2);
    } catch (err) {
        showError(err.message || "Unable to send OTP.");
    } finally {
        btn.disabled = false;
        btn.textContent = "Send OTP";
    }
});

document.getElementById("resendOtpBtn").addEventListener("click", () => {
    document.getElementById("sendOtpBtn").click();
});

document.getElementById("verifyOtpBtn").addEventListener("click", async () => {
    clearError();
    const otp = document.getElementById("otp").value.trim();

    if (!/^\d{6}$/.test(otp)) {
        showError("Enter the 6-digit OTP.");
        return;
    }

    state.otp = otp;
    const btn = document.getElementById("verifyOtpBtn");
    btn.disabled = true;
    btn.textContent = "Verifying...";

    try {
        if (typeof NovaAPI.verifySignupOtp !== "function") {
            throw new Error("OTP verification API is not available in the current backend yet.");
        }
        await NovaAPI.verifySignupOtp(state.phone, otp);
        state.otpVerified = true;
        setStep(3);
    } catch (err) {
        showError(err.message || "Invalid OTP.");
    } finally {
        btn.disabled = false;
        btn.textContent = "Verify & Continue";
    }
});

document.getElementById("detailsNextBtn").addEventListener("click", () => {
    clearError();

    const requiredIds = ["fullName", "dob", "bloodGroup", "email", "address"];
    for (const id of requiredIds) {
        if (!document.getElementById(id).value.trim()) {
            showError("Please complete all personal details.");
            return;
        }
    }

    setStep(4);
    if (!state.contacts.length) renderContacts();
});

document.getElementById("addContactBtn").addEventListener("click", addContact);

document.getElementById("contactsNextBtn").addEventListener("click", () => {
    clearError();
    if (!state.contacts.length) {
        showError("Add at least one emergency contact.");
        return;
    }

    const primary = state.contacts[0];
    if (!primary.name || !primary.relationship || !phoneIsValid(primary.phone)) {
        showError("Complete the primary emergency contact with a valid 10-digit phone number.");
        return;
    }

    setStep(5);
});

form.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearError();

    if (!state.otpVerified) {
        showError("Please verify your mobile number first.");
        return;
    }

    const registerBtn = document.getElementById("registerBtn");
    registerBtn.disabled = true;
    registerBtn.textContent = "Creating accounts...";

    const payload = {
        phone: state.phone,
        otp: state.otp,
        name: document.getElementById("fullName").value.trim(),
        dob: document.getElementById("dob").value,
        blood_group: document.getElementById("bloodGroup").value,
        email: document.getElementById("email").value.trim(),
        address: document.getElementById("address").value.trim(),
        device_id: document.getElementById("deviceId").value.trim().toUpperCase(),
        emergency_contacts: state.contacts.filter(c => c.name || c.relationship || c.phone)
    };

    try {
        if (typeof NovaAPI.registerCustomer !== "function") {
            throw new Error("Customer registration API is not available in the current backend yet.");
        }

        const result = await NovaAPI.registerCustomer(payload);

        document.getElementById("signupForm").classList.add("hidden");
        document.querySelector(".step-dot[data-dot='5']").classList.add("done");

        const credentials = result.credentials || {};
        document.getElementById("credentialsBox").innerHTML = `
            <div class="contact-card">
                <div class="text-xs font-bold tracking-widest text-slate-500 mb-2">RIDER ACCOUNT</div>
                <div class="text-sm">Username</div>
                <div class="font-bold text-primary">${credentials.rider_username || "Generated by backend"}</div>
                <div class="text-sm mt-2">Temporary Password</div>
                <div class="font-bold">${credentials.rider_password || "Generated by backend"}</div>
            </div>
            <div class="contact-card">
                <div class="text-xs font-bold tracking-widest text-slate-500 mb-2">GUARDIAN ACCOUNT</div>
                <div class="text-sm">Username</div>
                <div class="font-bold text-primary">${credentials.guardian_username || "Generated by backend"}</div>
                <div class="text-sm mt-2">Temporary Password</div>
                <div class="font-bold">${credentials.guardian_password || "Generated by backend"}</div>
            </div>
            <div class="p-3 rounded-lg bg-amber-50 border border-amber-200 text-amber-800 text-xs">
                Save these credentials securely. In production, temporary passwords should be changed after first login.
            </div>
        `;

        document.getElementById("successBox").classList.remove("hidden");
        clearError();
    } catch (err) {
        showError(err.message || "Unable to complete registration.");
    } finally {
        registerBtn.disabled = false;
        registerBtn.textContent = "Complete Registration";
    }
});

renderContacts();
