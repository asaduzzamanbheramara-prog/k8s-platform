const API = "https://api.shopnoltd.dpdns.org";
const KEY = "my-super-secret-key";

async function load() {
    const res = await fetch(API + "/domains", {
        headers: {
            "x-api-key": KEY
        }
    });

    const data = await res.json();
    document.getElementById("output").innerText =
        JSON.stringify(data, null, 2);
}

async function addDomain() {
    const name = document.getElementById("name").value;
    const host = document.getElementById("host").value;

    const res = await fetch(API + "/domain", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "x-api-key": KEY
        },
        body: JSON.stringify({
            name,
            host,
            service: "auto",
            namespace: "default",
            port: 80
        })
    });

    if (res.ok) {
        alert("Domain added successfully");
        load();
    } else {
        const err = await res.json();
        alert("Error: " + JSON.stringify(err));
    }
}

load();
